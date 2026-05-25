"""
tests/test_ingest.py — Unit tests untuk Fase 1 (Data Ingestion)

Compliance:
  - DATA-02: Dokumen tanpa metadata 'year' HARUS ditolak
  - DATA-05: Hanya 'pubmed' dan 'who' sebagai source yang valid
"""

import pytest
from data.ingest import (
    DocumentMetadata,
    chunk_text,
    IngestionStats,
    process_document,
    _simple_tokenize,
)
from pathlib import Path
import json
import tempfile
import os


# ═══════════════════════════════════════════════════════════════
# 1. DocumentMetadata Validation (DATA-02)
# ═══════════════════════════════════════════════════════════════

class TestDocumentMetadataValidation:
    """Verifikasi bahwa metadata validation bekerja sesuai spec DATA-02."""

    def test_valid_metadata_passes(self):
        """Metadata lengkap dan valid harus lolos tanpa error."""
        meta = DocumentMetadata(
            title="WHO Hypertension Guidelines 2023",
            year=2023,
            source="who",
            url="https://who.int/guidelines/hypertension",
        )
        meta.validate()  # harus tidak raise

    def test_missing_year_raises_error(self):
        """Dokumen tanpa 'year' HARUS ditolak (DATA-02)."""
        meta = DocumentMetadata(title="Test Doc", year=0, source="pubmed")
        with pytest.raises(ValueError, match="year"):
            meta.validate()

    def test_year_none_via_zero_raises_error(self):
        """year=0 dianggap missing (DATA-02)."""
        meta = DocumentMetadata(title="Test Doc", year=0, source="who")
        with pytest.raises(ValueError):
            meta.validate()

    def test_missing_title_raises_error(self):
        """Dokumen tanpa 'title' harus ditolak."""
        meta = DocumentMetadata(title="", year=2023, source="pubmed")
        with pytest.raises(ValueError, match="title"):
            meta.validate()

    def test_missing_source_raises_error(self):
        """Dokumen tanpa 'source' harus ditolak."""
        meta = DocumentMetadata(title="Test", year=2023, source="")
        with pytest.raises(ValueError, match="source"):
            meta.validate()

    def test_invalid_source_raises_error(self):
        """Source selain 'pubmed' atau 'who' harus ditolak (DATA-05)."""
        meta = DocumentMetadata(title="Test", year=2023, source="arxiv")
        with pytest.raises(ValueError, match="source"):
            meta.validate()

    def test_pubmed_source_valid(self):
        """Source 'pubmed' harus diterima."""
        meta = DocumentMetadata(title="PubMed Paper", year=2022, source="pubmed")
        meta.validate()  # harus tidak raise

    def test_who_source_valid(self):
        """Source 'who' harus diterima."""
        meta = DocumentMetadata(title="WHO Guide", year=2021, source="who")
        meta.validate()  # harus tidak raise

    def test_year_out_of_range_raises_error(self):
        """Year di luar range [1900, 2100] harus ditolak."""
        meta = DocumentMetadata(title="Test", year=1800, source="pubmed")
        with pytest.raises(ValueError, match="year"):
            meta.validate()

    def test_source_case_insensitive(self):
        """validate() menggunakan .lower() — sehingga 'WHO' uppercase tetap VALID."""
        meta = DocumentMetadata(title="Test", year=2023, source="WHO")
        # Tidak boleh raise karena "WHO".lower() == "who" ada di ALLOWED_SOURCES
        meta.validate()  # harus tidak raise


# ═══════════════════════════════════════════════════════════════
# 2. chunk_text
# ═══════════════════════════════════════════════════════════════

class TestChunkText:
    """Verifikasi bahwa chunking berfungsi dengan benar."""

    def test_empty_text_returns_empty_list(self):
        result = chunk_text("", chunk_size=512, chunk_overlap=64)
        assert result == []

    def test_short_text_single_chunk(self):
        text = "Pasien mengalami demam tinggi selama 3 hari."
        result = chunk_text(text, chunk_size=512, chunk_overlap=64)
        assert len(result) == 1
        assert text in result[0]

    def test_long_text_multiple_chunks(self):
        # Buat teks panjang ~2000 kata
        para = "Pasien mengalami gejala yang memerlukan pemeriksaan lebih lanjut. " * 20
        text = "\n\n".join([para] * 5)
        result = chunk_text(text, chunk_size=100, chunk_overlap=10)
        assert len(result) > 1

    def test_no_empty_chunks(self):
        text = "Paragraf pertama.\n\n\n\nParagraf kedua.\n\n\nParagraf ketiga."
        result = chunk_text(text, chunk_size=512, chunk_overlap=64)
        for chunk in result:
            assert chunk.strip() != ""


# ═══════════════════════════════════════════════════════════════
# 3. process_document — Integrasi dengan file sistem
# ═══════════════════════════════════════════════════════════════

class TestProcessDocument:
    """Test process_document dengan file JSON sementara."""

    def _make_json_doc(self, tmp_path: Path, data: dict) -> Path:
        """Buat file JSON dokumen sementara."""
        doc_path = tmp_path / "test_doc.json"
        doc_path.write_text(json.dumps(data), encoding="utf-8")
        return doc_path

    def test_valid_json_doc_accepted(self, tmp_path):
        """Dokumen JSON valid harus diterima dan menghasilkan chunks."""
        data = {
            "title": "Test Medical Paper",
            "year": 2023,
            "source": "pubmed",
            "url": "https://pubmed.ncbi.nlm.nih.gov/test",
            "full_text": "Pasien dengan hipertensi memerlukan pemantauan tekanan darah rutin. " * 10,
        }
        doc_path = self._make_json_doc(tmp_path, data)
        stats = IngestionStats()
        result = process_document(doc_path, chunk_size=512, chunk_overlap=64, stats=stats)
        assert result is not None
        assert len(result) >= 1
        assert stats.processed_documents == 1
        assert stats.rejected_missing_metadata == 0

    def test_doc_without_year_is_rejected(self, tmp_path):
        """Dokumen tanpa 'year' HARUS ditolak — persyaratan DATA-02 utama."""
        data = {
            "title": "Paper Tanpa Tahun",
            "source": "pubmed",
            "url": "https://pubmed.ncbi.nlm.nih.gov/test",
            "full_text": "Konten medis tanpa tahun publikasi.",
        }
        doc_path = self._make_json_doc(tmp_path, data)
        stats = IngestionStats()
        result = process_document(doc_path, chunk_size=512, chunk_overlap=64, stats=stats)
        assert result is None
        assert stats.rejected_missing_metadata == 1

    def test_doc_with_year_zero_is_rejected(self, tmp_path):
        """Dokumen dengan year=0 HARUS ditolak (dianggap tidak ada tahun)."""
        data = {
            "title": "Paper Year Zero",
            "year": 0,
            "source": "pubmed",
            "full_text": "Konten medis.",
        }
        doc_path = self._make_json_doc(tmp_path, data)
        stats = IngestionStats()
        result = process_document(doc_path, chunk_size=512, chunk_overlap=64, stats=stats)
        assert result is None
        assert stats.rejected_missing_metadata == 1

    def test_doc_with_invalid_source_is_rejected(self, tmp_path):
        """Dokumen dengan source tidak valid harus ditolak (DATA-05)."""
        data = {
            "title": "Paper Invalid Source",
            "year": 2023,
            "source": "arxiv",
            "full_text": "Konten dari arxiv.",
        }
        doc_path = self._make_json_doc(tmp_path, data)
        stats = IngestionStats()
        result = process_document(doc_path, chunk_size=512, chunk_overlap=64, stats=stats)
        assert result is None
        assert stats.rejected_invalid_source == 1

    def test_doc_chunk_metadata_preserved(self, tmp_path):
        """Setiap chunk harus mempertahankan metadata dokumen asli."""
        data = {
            "title": "Panduan WHO Diabetes 2022",
            "year": 2022,
            "source": "who",
            "url": "https://who.int/diabetes",
            "full_text": "Manajemen diabetes memerlukan pendekatan multi-disiplin. " * 5,
        }
        doc_path = self._make_json_doc(tmp_path, data)
        stats = IngestionStats()
        result = process_document(doc_path, chunk_size=512, chunk_overlap=64, stats=stats)
        assert result is not None
        for chunk in result:
            assert chunk.metadata.title == "Panduan WHO Diabetes 2022"
            assert chunk.metadata.year == 2022
            assert chunk.metadata.source == "who"


# ═══════════════════════════════════════════════════════════════
# 4. BM25 Tokenizer
# ═══════════════════════════════════════════════════════════════

class TestSimpleTokenize:
    def test_basic_tokenization(self):
        result = _simple_tokenize("Pasien mengalami demam tinggi")
        assert "pasien" in result
        assert "demam" in result
        assert "tinggi" in result

    def test_removes_short_tokens(self):
        result = _simple_tokenize("a b c demam")
        assert "a" not in result
        assert "b" not in result
        assert "demam" in result

    def test_lowercases(self):
        result = _simple_tokenize("DEMAM TINGGI")
        assert "demam" in result
        assert "DEMAM" not in result
