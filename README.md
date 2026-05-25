# Dokter Penjaga
> Emergency-Aware Medical RAG Agent | Kompetisi INaAI 2026  
> Track: AI Engineer · Domain 3: Medical AI / Health NLP  
> Author: Felix Natanael Butarbutar

---

## Prinsip Utama

> **"Selamatkan nyawa dulu, jawab kemudian."**

Sistem ini mendeteksi kondisi darurat **sebelum** memanggil LLM, meredaksi PII, dan memblokir jailbreak — semua secara deterministik.

---

## Arsitektur

```
Input → [PII Redact] → [Triage Gate] → [Guardrail In] →
        [Hybrid Retrieval] → [Conflict Check] → [LLM] →
        [Guardrail Out] → [Audit Log] → Response
```

Lihat [architecture.md](architecture.md) untuk detail lengkap.

---

## Quickstart

### 1. Clone & Setup

```bash
git clone <repo-url>
cd dokter-penjaga

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
python -m spacy download id_core_news_lg
python -m spacy download en_core_web_lg
```

### 2. Konfigurasi Environment

```bash
copy .env.example .env
# Edit .env dan isi ANTHROPIC_API_KEY dan variabel lainnya
```

### 3. Jalankan Qdrant (Docker)

```bash
docker-compose up -d qdrant
# Tunggu health check OK:
# curl http://localhost:6333/healthz
```

### 4. Ingest Dokumen

```bash
# Dry-run (validasi tanpa upload):
python -m data.ingest --dry-run

# Ingest penuh:
python -m data.ingest

# Dengan custom docs dir:
python -m data.ingest --docs-dir path/to/documents
```

### 5. Jalankan API

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Jalankan Tests

```bash
pytest eval/ -v
pytest eval/test_ingestion.py -v   # unit tests saja (no Qdrant needed)
```

---

## Format Dokumen

Setiap dokumen harus berformat JSON dengan field wajib:

```json
{
  "title": "...",         ← WAJIB
  "year": 2023,           ← WAJIB (DATA-02)
  "source": "pubmed",     ← WAJIB, harus "pubmed" atau "who" (DATA-05)
  "url": "https://...",
  "doi": "10.xxxx/...",
  "authors": ["..."],
  "abstract": "...",
  "full_text": "..."      ← Teks utama untuk diindeks
}
```

> ⚠️ Dokumen tanpa `year`, `title`, atau `source` akan **ditolak otomatis** saat ingestion.

---

## Environment Variables Penting

| Variable | Deskripsi | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | API key Claude | *wajib diisi* |
| `ALPHA_HYBRID` | Bobot semantic dalam hybrid search (α) | `0.6` |
| `LAMBDA_TEMPORAL` | Bobot temporal boost (λ) | `0.1` |
| `QDRANT_HOST` | Host Qdrant | `localhost` |
| `QDRANT_PORT` | Port Qdrant | `6333` |

Lihat [.env.example](.env.example) untuk daftar lengkap.

---

## Target Metrics

| Metric | Target |
|---|---|
| Retrieval Recall@5 | ≥ 0.80 |
| Factual Accuracy (LLM-as-judge) | ≥ 0.75 |
| Triage Detection F1 | ≥ 0.90 |
| PII Redaction Rate | 100% |
| Guardrail Block Rate | ≥ 0.95 |

---

## Open-Source Acknowledgments

- [Qdrant](https://qdrant.tech/) — Vector database
- [rank-bm25](https://github.com/dorianbrown/rank_bm25) — BM25 implementation
- [Microsoft Presidio](https://microsoft.github.io/presidio/) — PII redaction
- [sentence-transformers](https://www.sbert.net/) — Multilingual embeddings
- [FastAPI](https://fastapi.tiangolo.com/) — API framework
