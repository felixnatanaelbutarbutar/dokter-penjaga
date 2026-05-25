"""
eval/test_ingestion.py — Dokter Penjaga
Unit tests for the data ingestion pipeline (Fase 1 — tasks.md §1.3)

Covers:
  - DATA-01/DATA-02: documents without required metadata must be rejected
  - DATA-05: documents from non-whitelisted sources must be rejected
  - chunk_text: edge cases
  - DocumentMetadata.validate(): all branches
"""

from __future__ import annotations

import json
import pickle
import tempfile
from dataclasses import asdict
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Adjust sys.path so we can import from project root ────────
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.ingest import (
    ALLOWED_SOURCES,
    DocumentChunk,
    DocumentMetadata,
    IngestionStats,
    build_bm25_index,
    chunk_text,
    discover_documents,
    load_json_doc,
    process_document,
    save_bm25_index,
)


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def valid_meta_dict() -> dict:
    return {
        "title": "Management of Hypertension in Adults",
        "year": 2023,
        "source": "pubmed",
        "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        "doi": "10.1001/jama.2023.1234",
        "authors": ["Smith J", "Doe A"],
        "abstract": "Background: Hypertension is a leading risk factor...",
        "full_text": "Introduction\n\nHypertension (high blood pressure) affects "
                     "1.3 billion people globally. This review covers evidence-based "
                     "management strategies from 2018 to 2023.\n\nMethods\n\nWe conducted "
                     "a systematic review of randomized controlled trials...",
    }


@pytest.fixture
def valid_json_doc(tmp_path: Path, valid_meta_dict: dict) -> Path:
    p = tmp_path / "hypertension_2023.json"
    p.write_text(json.dumps(valid_meta_dict), encoding="utf-8")
    return p


@pytest.fixture
def valid_txt_with_sidecar(tmp_path: Path, valid_meta_dict: dict) -> Path:
    txt = tmp_path / "who_guideline_2024.txt"
    txt.write_text("WHO clinical guidance on diabetes management 2024.", encoding="utf-8")
    sidecar = tmp_path / "who_guideline_2024.meta.json"
    sidecar_data = {k: v for k, v in valid_meta_dict.items() if k != "full_text"}
    sidecar_data.update({"source": "who", "year": 2024})
    sidecar.write_text(json.dumps(sidecar_data), encoding="utf-8")
    return txt


# ═══════════════════════════════════════════════════════════════
# DocumentMetadata Validation Tests
# ═══════════════════════════════════════════════════════════════

class TestDocumentMetadataValidation:

    def test_valid_metadata_passes(self):
        """Happy path: all required fields present and valid."""
        meta = DocumentMetadata(title="Test", year=2022, source="pubmed", url="http://x.com")
        meta.validate()  # should not raise

    def test_missing_year_raises(self):
        """DATA-02: document without year MUST be rejected."""
        meta = DocumentMetadata(title="Test Doc", year=0, source="pubmed")
        with pytest.raises(ValueError, match="year"):
            meta.validate()

    def test_year_none_equivalent_zero(self):
        """DATA-02: year=0 treated as missing year."""
        meta = DocumentMetadata(title="Test", year=0, source="pubmed")
        with pytest.raises(ValueError, match="year"):
            meta.validate()

    def test_missing_title_raises(self):
        """DATA-01: document without title must be rejected."""
        meta = DocumentMetadata(title="", year=2022, source="pubmed")
        with pytest.raises(ValueError, match="title"):
            meta.validate()

    def test_whitespace_only_title_raises(self):
        """DATA-01: whitespace-only title treated as missing."""
        meta = DocumentMetadata(title="   ", year=2022, source="pubmed")
        with pytest.raises(ValueError, match="title"):
            meta.validate()

    def test_missing_source_raises(self):
        """DATA-01: document without source must be rejected."""
        meta = DocumentMetadata(title="Test", year=2022, source="")
        with pytest.raises(ValueError, match="source"):
            meta.validate()

    def test_unknown_source_raises(self):
        """DATA-05: source not in ALLOWED_SOURCES must be rejected."""
        meta = DocumentMetadata(title="Test", year=2022, source="springer")
        with pytest.raises(ValueError, match="source"):
            meta.validate()

    @pytest.mark.parametrize("source", list(ALLOWED_SOURCES))
    def test_all_allowed_sources_pass(self, source: str):
        """DATA-05: all whitelisted sources should pass validation."""
        meta = DocumentMetadata(title="Test", year=2022, source=source)
        meta.validate()  # no raise

    def test_year_out_of_range_raises(self):
        """Year must be in plausible range [1900, 2100]."""
        meta = DocumentMetadata(title="Test", year=1800, source="pubmed")
        with pytest.raises(ValueError, match="range"):
            meta.validate()

    def test_multiple_errors_reported_together(self):
        """All validation errors surfaced at once."""
        meta = DocumentMetadata(title="", year=0, source="unknown_source_xyz")
        with pytest.raises(ValueError) as exc_info:
            meta.validate()
        msg = str(exc_info.value)
        assert "title" in msg
        assert "year" in msg
        assert "source" in msg


# ═══════════════════════════════════════════════════════════════
# Document Loading Tests
# ═══════════════════════════════════════════════════════════════

class TestDocumentLoading:

    def test_load_valid_json_doc(self, valid_json_doc: Path):
        text, meta = load_json_doc(valid_json_doc)
        assert isinstance(text, str) and len(text) > 0
        assert meta["year"] == 2023
        assert meta["source"] == "pubmed"

    def test_load_json_doc_missing_text_raises(self, tmp_path: Path):
        p = tmp_path / "empty.json"
        p.write_text(json.dumps({"title": "X", "year": 2020, "source": "pubmed"}))
        with pytest.raises(ValueError, match="full_text"):
            load_json_doc(p)

    def test_txt_without_sidecar_rejected(self, tmp_path: Path):
        txt = tmp_path / "orphan.txt"
        txt.write_text("Some medical text.")
        from data.ingest import load_document
        with pytest.raises(FileNotFoundError, match="sidecar"):
            load_document(txt)


# ═══════════════════════════════════════════════════════════════
# process_document Integration Tests (DATA-02 compliance)
# ═══════════════════════════════════════════════════════════════

class TestProcessDocument:

    def test_valid_json_document_produces_chunks(self, valid_json_doc: Path):
        stats = IngestionStats()
        chunks = process_document(valid_json_doc, chunk_size=256, chunk_overlap=32, stats=stats)
        assert chunks is not None and len(chunks) > 0
        assert stats.processed_documents == 1
        assert stats.total_chunks == len(chunks)
        assert stats.rejected_missing_metadata == 0

    def test_document_without_year_is_rejected(self, tmp_path: Path):
        """DATA-02: missing year → rejected, not indexed."""
        doc = tmp_path / "no_year.json"
        doc.write_text(json.dumps({
            "title": "Test Doc",
            "year": 0,          # ← missing / zero
            "source": "pubmed",
            "full_text": "Some medical content here.",
        }))
        stats = IngestionStats()
        result = process_document(doc, chunk_size=256, chunk_overlap=32, stats=stats)
        assert result is None, "Document without year must be rejected"
        assert stats.rejected_missing_metadata == 1
        assert stats.processed_documents == 0

    def test_document_without_title_is_rejected(self, tmp_path: Path):
        doc = tmp_path / "no_title.json"
        doc.write_text(json.dumps({
            "title": "",
            "year": 2022,
            "source": "pubmed",
            "full_text": "Some content.",
        }))
        stats = IngestionStats()
        result = process_document(doc, chunk_size=256, chunk_overlap=32, stats=stats)
        assert result is None
        assert stats.processed_documents == 0

    def test_document_with_invalid_source_is_rejected(self, tmp_path: Path):
        """DATA-05: non-whitelisted source → rejected."""
        doc = tmp_path / "bad_source.json"
        doc.write_text(json.dumps({
            "title": "Random Blog Post",
            "year": 2022,
            "source": "random_blog",
            "full_text": "Some content.",
        }))
        stats = IngestionStats()
        result = process_document(doc, chunk_size=256, chunk_overlap=32, stats=stats)
        assert result is None
        assert stats.rejected_invalid_source == 1

    def test_chunk_ids_are_unique(self, valid_json_doc: Path):
        stats = IngestionStats()
        chunks = process_document(valid_json_doc, chunk_size=100, chunk_overlap=20, stats=stats)
        assert chunks is not None
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "Each chunk must have a unique ID"

    def test_chunks_preserve_metadata(self, valid_json_doc: Path):
        stats = IngestionStats()
        chunks = process_document(valid_json_doc, chunk_size=100, chunk_overlap=20, stats=stats)
        assert chunks
        for chunk in chunks:
            assert chunk.metadata.year == 2023
            assert chunk.metadata.source == "pubmed"
            assert chunk.metadata.title != ""


# ═══════════════════════════════════════════════════════════════
# Chunking Tests
# ═══════════════════════════════════════════════════════════════

class TestChunkText:

    def test_empty_text_returns_empty_list(self):
        assert chunk_text("") == []

    def test_whitespace_only_returns_empty_list(self):
        assert chunk_text("   \n\n\t  ") == []

    def test_short_text_single_chunk(self):
        text = "Short medical note."
        result = chunk_text(text, chunk_size=512, chunk_overlap=64)
        assert len(result) == 1
        assert "Short medical note." in result[0]

    def test_long_text_multiple_chunks(self):
        # ~2000 token text → should produce multiple chunks at size=200
        paragraph = "This is a test medical paragraph about hypertension management. " * 20
        text = "\n\n".join([paragraph] * 5)
        result = chunk_text(text, chunk_size=200, chunk_overlap=30)
        assert len(result) > 1

    def test_chunks_cover_all_content(self):
        """Union of all chunk content should cover original meaningful tokens."""
        sentences = [f"Sentence number {i} about medical topic X." for i in range(50)]
        text = " ".join(sentences)
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=20)
        combined = " ".join(chunks)
        # All original sentences should appear somewhere
        for s in sentences:
            assert s in combined, f"Missing sentence: {s}"

    def test_no_empty_chunks(self):
        text = "Para one.\n\nPara two.\n\nPara three."
        for chunk in chunk_text(text, chunk_size=10, chunk_overlap=2):
            assert chunk.strip() != ""


# ═══════════════════════════════════════════════════════════════
# BM25 Index Tests
# ═══════════════════════════════════════════════════════════════

class TestBM25Index:

    def _make_chunks(self, texts: list[str]) -> list[DocumentChunk]:
        return [
            DocumentChunk(
                chunk_id=f"chunk-{i}",
                doc_id="doc-0",
                text=t,
                chunk_index=i,
                metadata=DocumentMetadata(title="Test", year=2022, source="pubmed"),
            )
            for i, t in enumerate(texts)
        ]

    def test_build_returns_bm25_instance(self):
        from rank_bm25 import BM25Okapi
        chunks = self._make_chunks(["diabetes treatment 2022", "hypertension blood pressure"])
        bm25, returned_chunks = build_bm25_index(chunks)
        assert isinstance(bm25, BM25Okapi)
        assert len(returned_chunks) == 2

    def test_bm25_ranks_relevant_doc_higher(self):
        texts = [
            "Diabetes mellitus type 2 management with metformin",
            "Hypertension treatment with ACE inhibitors",
            "Pregnancy complications and prenatal care",
        ]
        chunks = self._make_chunks(texts)
        bm25, _ = build_bm25_index(chunks)
        scores = bm25.get_scores(["diabetes", "metformin"])
        # Document 0 should rank highest
        assert scores[0] == max(scores), "Diabetes doc should rank highest for diabetes query"

    def test_bm25_save_and_load(self, tmp_path: Path):
        chunks = self._make_chunks(["aspirin pain relief", "ibuprofen anti-inflammatory"])
        bm25, _ = build_bm25_index(chunks)
        index_path = tmp_path / "test_bm25.pkl"
        save_bm25_index(bm25, chunks, index_path)
        assert index_path.exists()
        with open(index_path, "rb") as f:
            payload = pickle.load(f)
        assert "bm25" in payload
        assert "chunks_meta" in payload
        assert len(payload["chunks_meta"]) == 2


# ═══════════════════════════════════════════════════════════════
# Document Discovery Tests
# ═══════════════════════════════════════════════════════════════

class TestDiscoverDocuments:

    def test_discovers_supported_files(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("text")
        (tmp_path / "b.json").write_text("{}")
        (tmp_path / "c.pdf").write_bytes(b"%PDF")
        (tmp_path / "d.meta.json").write_text("{}")  # sidecar — should be excluded
        (tmp_path / "e.csv").write_text("col1,col2")  # unsupported

        found = discover_documents(tmp_path)
        names = {p.name for p in found}
        assert "a.txt" in names
        assert "b.json" in names
        assert "c.pdf" in names
        assert "d.meta.json" not in names  # sidecar excluded
        assert "e.csv" not in names        # unsupported excluded

    def test_returns_empty_for_empty_dir(self, tmp_path: Path):
        assert discover_documents(tmp_path) == []

    def test_recurses_into_subdirectories(self, tmp_path: Path):
        sub = tmp_path / "pubmed" / "2023"
        sub.mkdir(parents=True)
        (sub / "article.json").write_text("{}")
        found = discover_documents(tmp_path)
        assert any(p.name == "article.json" for p in found)
