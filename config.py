"""
config.py — Dokter Penjaga
Centralized settings loaded from environment variables.

All scoring weights (α, λ) come from env vars — never hardcoded (DATA-03, OPS-03).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from .env / environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,   # treat empty strings in .env as unset (None)
    )

    # ── LLM ──────────────────────────────────────────────────────
    anthropic_api_key: str = Field(..., description="Anthropic Claude API key")
    llm_model: str = Field("claude-sonnet-4-20250514", description="Claude model name")
    llm_max_tokens: int = Field(1024, ge=256, le=4096)

    # ── Qdrant ────────────────────────────────────────────────────
    qdrant_host: str = Field("localhost")
    qdrant_port: int | None = Field(None)
    qdrant_grpc_port: int | None = Field(None)
    qdrant_collection: str = Field("medical_docs")
    qdrant_api_key: str | None = Field(None)

    # ── Embedding ──────────────────────────────────────────────────
    embedding_model: str = Field(
        "models/paraphrase-multilingual-mpnet-base-v2"
    )
    embedding_dim: int = Field(768, ge=64, le=4096)

    # ── Hybrid Retrieval Scoring (DATA-03) ────────────────────────
    alpha_hybrid: float = Field(
        0.6,
        ge=0.0,
        le=1.0,
        description="α: weight for semantic score in hybrid formula",
    )
    lambda_temporal: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="λ: temporal boost weight in hybrid formula",
    )
    top_k: int = Field(5, ge=1, le=50, description="Number of docs to retrieve")
    retrieval_confidence_threshold: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Below this score the system warns user about low confidence",
    )

    # ── Temporal Scoring ─────────────────────────────────────────
    year_min: int = Field(2018, ge=1900, le=2100)
    year_max: int = Field(2025, ge=1900, le=2100)
    conflict_year_gap: int = Field(
        3, ge=1, description="Year difference threshold to flag temporal conflict"
    )

    # ── Triage & Emergency ────────────────────────────────────────
    triage_keyword_config_path: str = Field("config/triage_keywords.yaml")
    emergency_number: str = Field("119")

    # ── Guardrails ────────────────────────────────────────────────
    guardrail_patterns_config_path: str = Field("config/guardrail_patterns.yaml")

    # ── PII Redaction ─────────────────────────────────────────────
    presidio_language: str = Field("id")
    # spaCy NLP model for Presidio NER
    # xx_ent_wiki_sm = multilingual (supports Indonesian), officially available for spaCy 3.8
    # id_core_news_lg is NOT available for spaCy 3.8 — do not use
    spacy_model: str = Field("xx_ent_wiki_sm", description="Primary spaCy model (multilingual)")
    spacy_en_model: str = Field("en_core_web_sm", description="English spaCy model for English PII")

    # ── Audit Logger ─────────────────────────────────────────────
    audit_log_path: str = Field("logs/audit.jsonl")

    # ── BM25 ──────────────────────────────────────────────────────
    bm25_index_path: str = Field("data/bm25_index.pkl")

    # ── API Server ────────────────────────────────────────────────
    api_host: str = Field("0.0.0.0")
    api_port: int = Field(8000, ge=1, le=65535)
    debug: bool = Field(False)

    # ── Data Ingestion ────────────────────────────────────────────
    documents_dir: str = Field("data/documents")
    chunk_size: int = Field(512, ge=64, le=2048)
    chunk_overlap: int = Field(64, ge=0, le=512)

    # ── Derived paths (convenience) ───────────────────────────────
    @property
    def audit_log_path_obj(self) -> Path:
        return Path(self.audit_log_path)

    @property
    def bm25_index_path_obj(self) -> Path:
        return Path(self.bm25_index_path)

    @property
    def documents_dir_obj(self) -> Path:
        return Path(self.documents_dir)

    @field_validator("year_max")
    @classmethod
    def year_max_gte_year_min(cls, v: int, info) -> int:
        year_min = info.data.get("year_min", 2018)
        if v < year_min:
            raise ValueError(f"year_max ({v}) must be >= year_min ({year_min})")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton (loaded once at startup)."""
    return Settings()
