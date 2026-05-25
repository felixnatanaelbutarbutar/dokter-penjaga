"""
data/ingest.py — Dokter Penjaga
Document Ingestion Pipeline: Load → Validate → Chunk → Embed → Upsert to Qdrant + BM25

Compliance:
  - DATA-01 / DATA-02: Rejects any document missing year/source/title metadata.
  - DATA-03: α and λ read from env (config.py), never hardcoded.
  - DATA-05: Only PubMed Open Access and WHO clinical guidelines accepted.
  - OPS-03: No credentials hardcoded.

Usage:
    python -m data.ingest --docs-dir data/documents --batch-size 32
    python -m data.ingest --docs-dir data/documents --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import pickle
import re
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Generator

import yaml
from tqdm import tqdm

# ── Setup logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("dokter_penjaga.ingest")

# ── Lazy imports (heavy deps) ─────────────────────────────────
_embedder = None
_qdrant_client = None


# ═══════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════

ALLOWED_SOURCES = {"pubmed", "who"}  # DATA-05: only these sources


@dataclass
class DocumentMetadata:
    """Required metadata for every document (DATA-01, DATA-02)."""

    title: str
    year: int
    source: str          # "pubmed" | "who"
    url: str = ""
    doi: str = ""
    authors: list[str] = field(default_factory=list)
    abstract: str = ""

    def validate(self) -> None:
        """Raise ValueError if metadata is invalid (DATA-02)."""
        errors: list[str] = []

        if not self.title or not self.title.strip():
            errors.append("'title' is required and cannot be empty")

        if not self.year:
            errors.append("'year' is required (DATA-02: documents without year MUST be rejected)")
        elif not (1900 <= self.year <= 2100):
            errors.append(f"'year' value {self.year} is out of plausible range [1900, 2100]")

        if not self.source or not self.source.strip():
            errors.append("'source' is required and cannot be empty")
        elif self.source.lower() not in ALLOWED_SOURCES:
            errors.append(
                f"'source' must be one of {ALLOWED_SOURCES} (DATA-05). "
                f"Got: '{self.source}'. Non-listed sources require manual review."
            )

        if errors:
            raise ValueError(
                f"Document metadata validation failed:\n  "
                + "\n  ".join(f"• {e}" for e in errors)
            )


@dataclass
class DocumentChunk:
    """A chunk of text with its provenance metadata."""

    chunk_id: str
    doc_id: str
    text: str
    chunk_index: int
    metadata: DocumentMetadata
    embedding: list[float] = field(default_factory=list)

    @property
    def text_hash(self) -> str:
        return hashlib.sha256(self.text.encode()).hexdigest()[:16]


@dataclass
class IngestionStats:
    """Counters for a single ingestion run."""

    total_files: int = 0
    rejected_missing_metadata: int = 0
    rejected_invalid_source: int = 0
    processed_documents: int = 0
    total_chunks: int = 0
    upserted_to_qdrant: int = 0
    errors: list[str] = field(default_factory=list)

    def report(self) -> str:
        lines = [
            "=" * 60,
            "  Ingestion Summary",
            "=" * 60,
            f"  Files found        : {self.total_files}",
            f"  Rejected (metadata): {self.rejected_missing_metadata}",
            f"  Rejected (source)  : {self.rejected_invalid_source}",
            f"  Documents OK       : {self.processed_documents}",
            f"  Chunks created     : {self.total_chunks}",
            f"  Upserted to Qdrant : {self.upserted_to_qdrant}",
            f"  Errors             : {len(self.errors)}",
        ]
        if self.errors:
            lines.append("\n  Errors detail:")
            for err in self.errors[:10]:
                lines.append(f"    • {err}")
        lines.append("=" * 60)
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# Document Loaders
# ═══════════════════════════════════════════════════════════════

def load_txt(path: Path) -> str:
    """Load plain text file."""
    return path.read_text(encoding="utf-8", errors="replace")


def load_pdf(path: Path) -> str:
    """Load PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n\n".join(pages)
    except ImportError:
        raise ImportError("pypdf is required: pip install pypdf")
    except Exception as exc:
        raise RuntimeError(f"Failed to parse PDF '{path}': {exc}") from exc


def load_json_doc(path: Path) -> tuple[str, dict]:
    """
    Load structured JSON document.
    Expected format:
    {
        "title": "...",
        "year": 2024,
        "source": "pubmed",
        "url": "https://...",
        "doi": "10.xxxx/...",
        "authors": ["..."],
        "abstract": "...",
        "full_text": "..."
    }
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    text = data.get("full_text") or data.get("abstract") or ""
    if not text:
        raise ValueError(f"JSON doc '{path}' has no 'full_text' or 'abstract'")
    return text, data


LOADER_MAP: dict[str, callable] = {
    ".txt": load_txt,
    ".md": load_txt,
    ".pdf": load_pdf,
}


def load_document(path: Path) -> tuple[str, dict]:
    """
    Load a document file and return (text, raw_metadata_dict).
    For JSON files the metadata is embedded.
    For PDF/TXT files, a companion .meta.json sidecar is required.
    """
    if path.suffix.lower() == ".json":
        return load_json_doc(path)

    loader = LOADER_MAP.get(path.suffix.lower())
    if loader is None:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    text = loader(path)

    # Look for companion sidecar: document.pdf → document.meta.json
    sidecar = path.with_suffix(".meta.json")
    if not sidecar.exists():
        raise FileNotFoundError(
            f"Metadata sidecar not found for '{path.name}'. "
            f"Create '{sidecar.name}' with: title, year, source, url."
        )
    meta_dict = json.loads(sidecar.read_text(encoding="utf-8"))
    return text, meta_dict


# ═══════════════════════════════════════════════════════════════
# Text Chunker
# ═══════════════════════════════════════════════════════════════

def _estimate_tokens(text: str) -> int:
    """Fast token count estimate (4 chars ≈ 1 token)."""
    return max(1, len(text) // 4)


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[str]:
    """
    Split text into overlapping chunks by paragraph boundaries.
    Falls back to character splitting if paragraphs are too large.

    Args:
        text: Input text to chunk.
        chunk_size: Target chunk size in tokens.
        chunk_overlap: Token overlap between consecutive chunks.

    Returns:
        List of text chunks.
    """
    text = text.strip()
    if not text:
        return []

    # Split into paragraphs first
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    chunks: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = _estimate_tokens(para)

        if para_tokens > chunk_size:
            # Flush current buffer first
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = []
                current_tokens = 0
            # Force-split long paragraph by sentences
            sentences = re.split(r"(?<=[.!?])\s+", para)
            sub_buf: list[str] = []
            sub_tok = 0
            for sent in sentences:
                st = _estimate_tokens(sent)
                if sub_tok + st > chunk_size and sub_buf:
                    chunks.append(" ".join(sub_buf))
                    # Keep overlap
                    overlap_sents = sub_buf[max(0, len(sub_buf) - 2):]
                    sub_buf = overlap_sents
                    sub_tok = sum(_estimate_tokens(s) for s in sub_buf)
                sub_buf.append(sent)
                sub_tok += st
            if sub_buf:
                chunks.append(" ".join(sub_buf))
            continue

        if current_tokens + para_tokens > chunk_size and current_parts:
            chunks.append("\n\n".join(current_parts))
            # Overlap: keep last paragraph(s) within overlap budget
            overlap: list[str] = []
            overlap_tok = 0
            for p in reversed(current_parts):
                t = _estimate_tokens(p)
                if overlap_tok + t <= chunk_overlap:
                    overlap.insert(0, p)
                    overlap_tok += t
                else:
                    break
            current_parts = overlap
            current_tokens = overlap_tok

        current_parts.append(para)
        current_tokens += para_tokens

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return [c for c in chunks if c.strip()]


# ═══════════════════════════════════════════════════════════════
# Embedder (lazy init)
# ═══════════════════════════════════════════════════════════════

def get_embedder(model_name: str):
    """Lazy-load the SentenceTransformer embedder."""
    global _embedder
    if _embedder is None:
        logger.info(f"Loading embedding model: {model_name}")
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(model_name)
        logger.info("Embedding model loaded.")
    return _embedder


def embed_chunks(
    chunks: list[DocumentChunk],
    model_name: str,
    batch_size: int = 32,
    show_progress: bool = True,
) -> list[DocumentChunk]:
    """
    Embed chunk texts in batches and store vectors in-place.

    Returns the same list with .embedding populated.
    """
    embedder = get_embedder(model_name)
    texts = [c.text for c in chunks]
    logger.info(f"Embedding {len(texts)} chunks in batches of {batch_size}…")

    all_embeddings = embedder.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=True,   # cosine-ready
    )

    for chunk, emb in zip(chunks, all_embeddings):
        chunk.embedding = emb.tolist()

    return chunks


# ═══════════════════════════════════════════════════════════════
# Qdrant
# ═══════════════════════════════════════════════════════════════

def get_qdrant_client(host: str, port: int | None, api_key: str | None = None):
    """Lazy-initialize and return a QdrantClient.

    Supports both:
    - Local: host='localhost', port=6333
    - Cloud: host='https://xxx.cloud.qdrant.io', port=None or port=443
    """
    global _qdrant_client
    if _qdrant_client is None:
        from qdrant_client import QdrantClient

        # Strip any trailing whitespace / CRLF from Windows .env files
        host = host.strip()
        if host.startswith("http://") or host.startswith("https://"):
            kwargs: dict[str, Any] = {"url": host, "timeout": 30}
            if api_key:
                kwargs["api_key"] = api_key
            _qdrant_client = QdrantClient(**kwargs)
            logger.info(f"Connected to Qdrant Cloud at {host}")
        else:
            kwargs = {"host": host, "port": port or 6333, "timeout": 30}
            if api_key:
                kwargs["api_key"] = api_key
            _qdrant_client = QdrantClient(**kwargs)
            logger.info(f"Connected to Qdrant at {host}:{port}")
    return _qdrant_client


def ensure_qdrant_collection(
    client,
    collection_name: str,
    vector_dim: int,
) -> None:
    """
    Create the Qdrant collection if it doesn't exist.
    Uses Cosine distance (embeddings are L2-normalized).
    """
    from qdrant_client.models import (
        Distance,
        VectorParams,
        HnswConfigDiff,
    )

    existing = {c.name for c in client.get_collections().collections}
    if collection_name in existing:
        logger.info(f"Collection '{collection_name}' already exists — skipping creation.")
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_dim,
            distance=Distance.COSINE,
        ),
        hnsw_config=HnswConfigDiff(
            m=16,
            ef_construct=200,
        ),
    )
    logger.info(f"Created Qdrant collection '{collection_name}' (dim={vector_dim}, Cosine).")


def upsert_chunks_to_qdrant(
    client,
    collection_name: str,
    chunks: list[DocumentChunk],
    batch_size: int = 64,
) -> int:
    """
    Upsert embedded chunks to Qdrant.

    Returns number of points successfully upserted.
    """
    from qdrant_client.models import PointStruct

    total_upserted = 0
    for i in tqdm(range(0, len(chunks), batch_size), desc="Upserting to Qdrant"):
        batch = chunks[i : i + batch_size]
        points = [
            PointStruct(
                id=chunk.chunk_id,
                vector=chunk.embedding,
                payload={
                    "doc_id": chunk.doc_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "text_hash": chunk.text_hash,
                    # Metadata fields (DATA-01 — all present, validated)
                    "title": chunk.metadata.title,
                    "year": chunk.metadata.year,
                    "source": chunk.metadata.source,
                    "url": chunk.metadata.url,
                    "doi": chunk.metadata.doi,
                    "authors": chunk.metadata.authors,
                },
            )
            for chunk in batch
        ]
        client.upsert(collection_name=collection_name, points=points)
        total_upserted += len(points)

    return total_upserted


# ═══════════════════════════════════════════════════════════════
# BM25 Index
# ═══════════════════════════════════════════════════════════════

def _simple_tokenize(text: str) -> list[str]:
    """
    Basic whitespace + punctuation tokenizer.
    Replace with a proper Indonesian tokenizer if available.
    """
    text = text.lower()
    # Remove punctuation except hyphens inside words
    text = re.sub(r"[^\w\s-]", " ", text)
    tokens = text.split()
    return [t for t in tokens if len(t) > 1]


def build_bm25_index(chunks: list[DocumentChunk]) -> tuple[Any, list[DocumentChunk]]:
    """
    Build a BM25 index over the chunk corpus.

    Returns (BM25Okapi, chunks) — the chunks list is kept for retrieval mapping.
    """
    from rank_bm25 import BM25Okapi

    logger.info(f"Building BM25 index over {len(chunks)} chunks…")
    tokenized = [_simple_tokenize(c.text) for c in chunks]
    bm25 = BM25Okapi(tokenized)
    logger.info("BM25 index built.")
    return bm25, chunks


def save_bm25_index(bm25, chunks: list[DocumentChunk], index_path: Path) -> None:
    """Persist BM25 index + chunk metadata to disk."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "bm25": bm25,
        "chunks_meta": [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "text": c.text,
                "chunk_index": c.chunk_index,
                "metadata": asdict(c.metadata),
            }
            for c in chunks
        ],
    }
    with open(index_path, "wb") as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
    logger.info(f"BM25 index saved to: {index_path}")


# ═══════════════════════════════════════════════════════════════
# Document Discovery
# ═══════════════════════════════════════════════════════════════

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".json", ".md"}


def discover_documents(docs_dir: Path) -> list[Path]:
    """
    Recursively discover all supported document files.
    Skips .meta.json sidecar files.
    """
    paths: list[Path] = []
    for ext in SUPPORTED_EXTENSIONS:
        for p in docs_dir.rglob(f"*{ext}"):
            if p.name.endswith(".meta.json"):
                continue  # skip sidecars
            paths.append(p)
    return sorted(paths)


# ═══════════════════════════════════════════════════════════════
# Core Ingestion Pipeline
# ═══════════════════════════════════════════════════════════════

def process_document(
    doc_path: Path,
    chunk_size: int,
    chunk_overlap: int,
    stats: IngestionStats,
) -> list[DocumentChunk] | None:
    """
    Load, validate, and chunk a single document.

    Returns list of DocumentChunk on success, None on rejection.
    Increments stats counters in-place.
    """
    stats.total_files += 1
    doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(doc_path)))

    try:
        text, raw_meta = load_document(doc_path)
    except FileNotFoundError as exc:
        logger.warning(f"[SKIP] Missing metadata sidecar: {exc}")
        stats.rejected_missing_metadata += 1
        stats.errors.append(f"{doc_path.name}: {exc}")
        return None
    except Exception as exc:
        logger.error(f"[ERROR] Load failed for '{doc_path.name}': {exc}")
        stats.errors.append(f"{doc_path.name}: {exc}")
        return None

    # ── Build & validate metadata (DATA-01, DATA-02) ──────────
    try:
        meta = DocumentMetadata(
            title=raw_meta.get("title", "").strip(),
            year=int(raw_meta.get("year", 0)),
            source=str(raw_meta.get("source", "")).lower().strip(),
            url=raw_meta.get("url", ""),
            doi=raw_meta.get("doi", ""),
            authors=raw_meta.get("authors", []),
            abstract=raw_meta.get("abstract", ""),
        )
        meta.validate()
    except ValueError as exc:
        logger.warning(f"[REJECT] '{doc_path.name}': {exc}")
        if "year" in str(exc).lower():
            stats.rejected_missing_metadata += 1
        else:
            stats.rejected_invalid_source += 1
        stats.errors.append(f"{doc_path.name}: {exc}")
        return None

    # ── Chunk text ────────────────────────────────────────────
    text_chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not text_chunks:
        logger.warning(f"[SKIP] '{doc_path.name}' produced 0 chunks after chunking.")
        return None

    chunks = [
        DocumentChunk(
            chunk_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}::{i}")),
            doc_id=doc_id,
            text=chunk_text_str,
            chunk_index=i,
            metadata=meta,
        )
        for i, chunk_text_str in enumerate(text_chunks)
    ]

    stats.processed_documents += 1
    stats.total_chunks += len(chunks)

    logger.info(
        f"[OK] '{doc_path.name}' -> {len(chunks)} chunks "
        f"(year={meta.year}, source={meta.source})"
    )
    return chunks


def run_ingestion(
    docs_dir: Path,
    chunk_size: int,
    chunk_overlap: int,
    embedding_model: str,
    embed_batch_size: int,
    qdrant_host: str,
    qdrant_port: int,
    qdrant_collection: str,
    qdrant_api_key: str | None,
    vector_dim: int,
    bm25_index_path: Path,
    dry_run: bool = False,
) -> IngestionStats:
    """
    Full ingestion pipeline:
      1. Discover documents
      2. Load + validate + chunk
      3. Embed
      4. Upsert to Qdrant
      5. Build & save BM25 index

    Args:
        dry_run: If True, skip embedding/upload steps (validation only).
    """
    stats = IngestionStats()

    if not docs_dir.exists():
        logger.error(f"Documents directory not found: {docs_dir}")
        sys.exit(1)

    # ── 1. Discover ──────────────────────────────────────────────
    doc_paths = discover_documents(docs_dir)
    if not doc_paths:
        logger.warning(f"No supported documents found in: {docs_dir}")
        return stats
    logger.info(f"Discovered {len(doc_paths)} document file(s) in '{docs_dir}'")

    # ── 2. Load + Validate + Chunk ───────────────────────────────
    all_chunks: list[DocumentChunk] = []
    for path in tqdm(doc_paths, desc="Loading & chunking"):
        result = process_document(path, chunk_size, chunk_overlap, stats)
        if result:
            all_chunks.extend(result)

    logger.info(
        f"Validation complete: {stats.processed_documents} docs OK, "
        f"{stats.rejected_missing_metadata} rejected (no year/title), "
        f"{stats.rejected_invalid_source} rejected (bad source). "
        f"Total chunks: {len(all_chunks)}"
    )

    if not all_chunks:
        logger.error("No valid chunks to index. Aborting.")
        print(stats.report())
        return stats

    if dry_run:
        logger.info("[DRY RUN] Skipping embedding and upload steps.")
        print(stats.report())
        return stats

    # ── 3. Embed ──────────────────────────────────────────────────
    all_chunks = embed_chunks(
        all_chunks,
        model_name=embedding_model,
        batch_size=embed_batch_size,
    )

    # ── 4. Upsert to Qdrant ───────────────────────────────────────
    qdrant = get_qdrant_client(qdrant_host, qdrant_port, qdrant_api_key)
    ensure_qdrant_collection(qdrant, qdrant_collection, vector_dim)
    stats.upserted_to_qdrant = upsert_chunks_to_qdrant(
        qdrant, qdrant_collection, all_chunks
    )

    # ── 5. Build & Save BM25 Index ────────────────────────────────
    bm25_model, indexed_chunks = build_bm25_index(all_chunks)
    save_bm25_index(bm25_model, indexed_chunks, bm25_index_path)

    print(stats.report())
    return stats


# ═══════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="dokter-penjaga-ingest",
        description="Ingest medical documents into Qdrant + BM25 index.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=None,
        help="Directory containing medical documents. Overrides DOCUMENTS_DIR env var.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Embedding batch size.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate documents only; skip embedding and upload.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load settings from env (OPS-03 — no hardcoded credentials)
    from config import get_settings
    cfg = get_settings()

    docs_dir = args.docs_dir or cfg.documents_dir_obj

    logger.info("=" * 60)
    logger.info("  Dokter Penjaga --- Document Ingestion Pipeline")
    logger.info("=" * 60)
    logger.info(f"  Documents dir    : {docs_dir}")
    logger.info(f"  Qdrant           : {cfg.qdrant_host}:{cfg.qdrant_port}")
    logger.info(f"  Collection       : {cfg.qdrant_collection}")
    logger.info(f"  Embedding model  : {cfg.embedding_model}")
    logger.info(f"  Chunk size       : {cfg.chunk_size} tokens")
    logger.info(f"  Chunk overlap    : {cfg.chunk_overlap} tokens")
    logger.info(f"  BM25 index path  : {cfg.bm25_index_path}")
    logger.info(f"  Dry run          : {args.dry_run}")
    logger.info("=" * 60)

    start = time.perf_counter()
    run_ingestion(
        docs_dir=docs_dir,
        chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
        embedding_model=cfg.embedding_model,
        embed_batch_size=args.batch_size,
        qdrant_host=cfg.qdrant_host,
        qdrant_port=cfg.qdrant_port,
        qdrant_collection=cfg.qdrant_collection,
        qdrant_api_key=cfg.qdrant_api_key,
        vector_dim=cfg.embedding_dim,
        bm25_index_path=cfg.bm25_index_path_obj,
        dry_run=args.dry_run,
    )
    elapsed = time.perf_counter() - start
    logger.info(f"Ingestion finished in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
