# Dokter Penjaga — Emergency-Aware Medical RAG Agent

> **INaAI Hackathon 2026 · Track: AI Engineer · Domain 3: Medical AI / Health NLP**  
> **Author:** Felix Natanael Butarbutar

---

## 🔴 Live Inference Endpoint

| Resource | URL |
|----------|-----|
| **Web UI (Chatbot)** | [https://entourage-earmuff-paternal.ngrok-free.dev/](https://entourage-earmuff-paternal.ngrok-free.dev/) |
| **REST API (Swagger)** | [https://entourage-earmuff-paternal.ngrok-free.dev/docs](https://entourage-earmuff-paternal.ngrok-free.dev/docs) |
| **Health Check** | [https://entourage-earmuff-paternal.ngrok-free.dev/health](https://entourage-earmuff-paternal.ngrok-free.dev/health) |

> ⚠️ Endpoint ini berjalan di atas laptop lokal yang di-expose via Ngrok. Pastikan laptop dalam kondisi menyala dan terhubung internet saat evaluasi.

---

## 1. System Design

**Dokter Penjaga** adalah agen RAG medis yang dirancang bukan sebagai chatbot generik, melainkan sebagai mesin penalaran klinis berlapis (**Defense-in-Depth**). Sistem ini menganut satu prinsip: *"Selamatkan nyawa dulu, jawab kemudian."*

Alur pipeline berjalan secara sekuensial:

```
Input → [PII Redaction] → [Triage Gate] → [Input Guardrail]
      → [Hybrid Retrieval + Temporal Filter]
      → [LLM Generation (Claude)] → [Output Guardrail]
      → [Audit Log] → Response
```

1. **PII Redaction (`core/pii.py`):** Microsoft Presidio + spaCy mendeteksi dan menyensor identitas (Nama, NIK, Nomor HP) menjadi token anonim `<PERSON>` sebelum menyentuh LLM eksternal.
2. **Deterministik Triage (`core/triage.py`):** Keyword kritis ("nyeri dada", "sesak napas") mem-bypass seluruh RAG pipeline dan merespons darurat dalam < 0.1 detik — tanpa melibatkan LLM sama sekali.
3. **Lexical Guardrail (`core/guardrails.py`):** Regex pattern matching memblokir prompt injection dan permintaan dosis letal di level aplikasi sebelum membuang token API.
4. **Hybrid Retrieval (`core/retrieval.py`):** Dense search (Qdrant) + BM25 sparse search digabungkan dengan pembobotan α. Temporal Filter mengurangi bobot dokumen kadaluwarsa.
5. **Output Guardrail:** Output LLM divalidasi untuk mencegah sistem bertindak sebagai "prescribing doctor".

## 2. Data

- **Knowledge Base (MVP):** Basis data kami menggunakan file JSON sintetis yang memodelkan struktur, metadata, dan terminologi pedoman *WHO* dan jurnal *PubMed Open Access*. Pipeline *ingestion* (`data/ingest.py`) bersifat agnostik — siap menerima PDF asli tanpa perubahan kode di lingkungan produksi.
- **Validation:** Setiap dokumen wajib memiliki metadata `year`, `title`, `source`. Absensi metadata memicu *Hard Reject* otomatis (mencegah *timeline-agnostic hallucination*).
- **Chunking:** Paragraph-based chunking dengan overlap 64 token untuk mempertahankan koherensi konteks.

## 3. Model Stack

| Komponen | Model | Fungsi |
|----------|-------|--------|
| Embedding | `paraphrase-multilingual-mpnet-base-v2` | Dense vector untuk semantic search (multilingual ID/EN) |
| LLM | Anthropic Claude 3.5 Sonnet | RAG synthesis & guardrail compliance |
| NER / PII | `id_core_news_lg` spaCy + Presidio | Named-entity recognition lokal (tanpa network call) |

## 4. Evaluation Results

Seluruh evaluasi dapat direproduksi dengan menjalankan skrip di bawah ini.

| Metric | Script | Target | **Hasil** |
|--------|--------|--------|-----------|
| Retrieval Recall@5 | `python scripts/run_retrieval_eval.py` | ≥ 0.80 | **1.00** |
| Factual Accuracy (LLM-as-Judge) | `python scripts/run_factual_eval.py` | ≥ 0.75 | **1.00** |
| Triage Detection F1 | `python scripts/run_triage_eval.py` | ≥ 0.90 | **1.00** |
| Guardrail Block Rate | `python scripts/run_eval.py` | ≥ 0.95 | **1.00** |

> **LLM-as-Judge methodology:** Hakim dikonfigurasi dengan instruksi *zero-knowledge* — dilarang menggunakan pengetahuan internalnya sendiri, hanya mengevaluasi keselarasan antara output dan dokumen konteks RAG yang diberikan.

## 5. AI Usage Log

Ringkasan: **90% AI / 10% Human**. Detail lengkap di [`AI_USAGE_LOG.md`](AI_USAGE_LOG.md).

- **AI (Gemini Agent):** Perancangan kode infrastruktur (FastAPI, pipeline ingestion, hybrid retrieval), pembuatan dataset adversarial sintetis, penulisan eval framework otomatis.
- **Human (Author):** Pengarahan filosofi *Safety-First*, keputusan arsitektur defense-in-depth, validasi etika medis.

## 6. Limitations

Batasan teknis yang kami sadari dalam konteks MVP Hackathon ini:

1. **Knowledge Base Sintetis:** Belum mengintegrasikan PDF parser (`PyMuPDF`) untuk mengekstrak dokumen asli WHO. Data saat ini adalah JSON dummy terstruktur.
2. **BM25 Tokenizer Sederhana:** Belum menggunakan algoritma stemming bahasa Indonesia (PySastrawi), sehingga pencocokan imbuhan kata belum optimal.
3. **Stateless Sessions:** API tidak memiliki memori percakapan (belum terintegrasi Redis/Postgres). Konteks antar-pertanyaan tidak dipertahankan.
4. **Frontend Minimalis:** Dibangun dengan Vanilla HTML/JS — belum menggunakan React/Next.js untuk state management yang lebih robust.

---

## Reproducible Evaluation

```bash
# Setup
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# Run all eval scripts
python scripts/run_triage_eval.py
python scripts/run_factual_eval.py
python scripts/run_retrieval_eval.py
python scripts/run_eval.py
```

**→ Panduan deployment lengkap: [DEPLOYMENT.md](DEPLOYMENT.md)**
