# tasks.md — Dokter Penjaga

> Roadmap pelaksanaan Fase 2 (Window 21,5 Jam)  
> Kompetisi INaAI 2026 · Track: AI Engineer · Domain 3: Medical AI

---

## Status Legend

| Simbol | Arti |
|---|---|
| `[ ]` | Belum dikerjakan |
| `[~]` | Sedang dikerjakan |
| `[x]` | Selesai |
| 🔴 **Must Have** | Wajib diselesaikan |
| 🟡 **Nice to Have** | Dikerjakan jika waktu cukup |
| 🟢 **Extraordinary** | Bonus poin kompetisi |

---

## Fase 1 — Setup & Ingestion (Jam 01–04) 🔴 Must Have

### 1.1 Environment Setup
- [x] Buat struktur direktori proyek
- [x] Setup virtual environment Python
- [x] Install dependencies: `qdrant-client`, `rank-bm25`, `presidio-analyzer`, `presidio-anonymizer`, `fastapi`, `anthropic`, `uvicorn`
- [x] Konfigurasi environment variables (`.env` file + `.env.example`)
- [x] Setup `.gitignore` (pastikan `.env` tidak ter-commit)

### 1.2 Qdrant Setup
- [x] Jalankan Qdrant instance (Qdrant Cloud)
- [x] Buat koleksi `medical_docs` dengan konfigurasi vector dimension yang sesuai (dim=384, Cosine)
- [x] Verifikasi koneksi Qdrant berjalan

### 1.3 Data Ingestion
- [x] Download/siapkan dokumen PubMed Open Access (2018–2025)
- [x] Download/siapkan panduan klinis WHO
- [x] Validasi setiap dokumen memiliki metadata: `year`, `source`, `title`, `url`
- [x] Buat script ingestion: chunking → embedding → upsert ke Qdrant
- [x] Buat index BM25 dari corpus yang sama
- [x] Verifikasi jumlah dokumen yang berhasil diindeks (3 docs, 4 chunks)
- [x] Tulis unit test: dokumen tanpa metadata `year` harus ditolak oleh ingestion script

---

## Fase 2 — API & Privacy Layer (Jam 05–09) 🔴 Must Have

### 2.1 FastAPI Endpoint
- [x] Buat endpoint `POST /ask` sebagai entry point utama
- [x] Buat endpoint `GET /health` untuk health check
- [x] Setup request/response schema dengan Pydantic
- [x] Setup error handler global

### 2.2 PII Redaction (Microsoft Presidio)
- [x] Install dan konfigurasi Presidio untuk Bahasa Indonesia (`id`)
- [x] Implementasi fungsi `redact_pii(text: str) -> str`
- [x] Daftarkan entitas yang disensor: `PERSON`, `LOCATION`, `ID_NUMBER`, `PHONE_NUMBER`, `EMAIL_ADDRESS`
- [x] Integrasi Presidio sebagai layer pertama di pipeline (sebelum log & LLM)
- [x] Tulis unit test:
  - [x] Input mengandung NIK → harus tersensor
  - [x] Input mengandung nama → harus tersensor
  - [x] Input mengandung nomor HP → harus tersensor
- [x] Verifikasi PII Redaction Rate mencapai 100% pada test set

### 2.3 Audit Logger
- [x] Buat modul `audit_logger.py`
- [x] Log setiap event: `triage_trigger`, `pii_redacted`, `guardrail_block`, `retrieval_scores`, `response_sent`
- [x] Pastikan log tidak menyimpan PII asli (hanya versi tersensor)
- [x] Format log: JSON structured logging dengan timestamp

---

## Fase 3 — Triage & Guardrails (Jam 10–13) 🔴 Must Have

### 3.1 Emergency Triage Classifier
- [x] Buat file konfigurasi `triage_keywords.yaml` (bukan hardcoded)
- [x] Isi keyword awal: serangan jantung, overdosis, tidak bernapas, pingsan, stroke, perdarahan hebat, kejang, tersedak, dll.
- [x] Implementasi fungsi `is_emergency(text: str) -> bool`
- [x] Implementasi respons darurat: teks tetap + arahan **hubungi 119**
- [x] Integrasi triage sebagai gate kedua di pipeline (setelah PII redaction)
- [x] Tulis unit test:
  - [x] "Saya merasakan nyeri dada dan sesak napas" → `True`
  - [x] "Apa obat untuk demam ringan?" → `False`
  - [x] Verifikasi Triage Detection F1 ≥ 0,90 pada eval dataset

### 3.2 Input Guardrail
- [x] Buat daftar pattern prompt injection & jailbreak (`guardrail_patterns.yaml`)
- [x] Implementasi fungsi `validate_input(text: str) -> GuardrailResult`
- [x] Setiap block dicatat dengan label `BLOCKED_INJECTION` di audit log
- [x] Tulis unit test dengan sample dari 150 prompt sintetis

### 3.3 Output Guardrail
- [x] Implementasi fungsi `validate_output(response: str) -> GuardrailResult`
- [x] Blokir respons yang mengandung: dosis obat spesifik tanpa arahan dokter, instruksi berbahaya
- [x] Tulis unit test untuk contoh output berbahaya

---

## Fase 4 — Hybrid Retrieval & Temporal Filter (Jam 14–17) 🟡 Nice to Have

### 4.1 Hybrid Search Engine
- [x] Implementasi `semantic_search(query: str, top_k: int) -> List[Document]` via Qdrant
- [x] Implementasi `bm25_search(query: str, top_k: int) -> List[Document]`
- [x] Implementasi fungsi `hybrid_search(query, alpha, lambda_temporal)`:
  ```
  score_final = α · score_semantic + (1−α) · score_BM25 + λ · f(year)
  ```
- [x] Ekspose nilai `alpha` dan `lambda_temporal` sebagai environment variable
- [x] Tulis unit test: query nama obat spesifik harus memiliki BM25 score tinggi

### 4.2 Temporal Re-ranking
- [x] Implementasi fungsi `temporal_boost(year: int) -> float`
- [x] Dokumen tahun terbaru mendapat bobot lebih tinggi
- [x] Verifikasi retrieval Recall@5 ≥ 0,80

### 4.3 Conflict Detection
- [x] Implementasi deteksi perbedaan informasi antar dokumen (threshold berbasis semantic similarity)
- [x] Jika konflik terdeteksi → format respons menampilkan dua versi dengan label tahun eksplisit
- [x] Tulis unit test: dua dokumen berbeda tahun dengan klaim berbeda harus memicu conflict view

### 4.4 LLM Integration
- [x] Integrasikan Anthropic API untuk generasi jawaban
- [x] Susun system prompt yang mewajibkan: sertakan sumber referensi, nyatakan ketidakpastian jika confidence rendah
- [x] Implementasi confidence degradation: jika retrieval score rendah → modifikasi prompt agar LLM tidak menjawab terlalu yakin

---

## Fase 5 — Adversarial Testing (Jam 18–20) 🟢 Extraordinary

### 5.1 Eval Dataset
- [x] Siapkan 150 prompt sintetis (sudah diverifikasi manual):
  - [x] 50 prompt: permintaan saran overdosis / self-harm
  - [x] 50 prompt: prompt injection & jailbreak
  - [x] 50 prompt: pencurian data / manipulasi sistem
- [x] Buat script `run_eval.py` untuk menjalankan semua prompt secara otomatis

### 5.2 Running Eval
- [x] Jalankan 150 skenario terhadap sistem
- [x] Catat: berapa yang berhasil diblokir, berapa yang lolos
- [x] Hitung Guardrail Block Rate → target ≥ 0,95
- [x] Simpan hasil dalam file `eval_results.json`

### 5.3 LLM-as-Judge (Factual Accuracy)
- [x] Buat script evaluasi dengan LLM-as-judge
- [x] Uji pada subset pertanyaan medis faktual
- [x] Hitung Factual Accuracy → target ≥ 0,75
- [x] Simpan hasil dalam file `factual_accuracy_results.json`

### 5.4 Retrieval Eval
- [x] Buat ground truth dataset untuk retrieval (query → dokumen relevan yang diharapkan)
- [x] Hitung Recall@5 → target ≥ 0,80
- [x] Simpan hasil dalam file `retrieval_eval_results.json`

---

## Fase 6 — Finalisasi & Dokumentasi (Jam 21–21.5) 🔴 Must Have

- [x] Tulis laporan teknis singkat (`technical_report.md`)
- [x] Perbarui `AI_USAGE_LOG.md` sesuai ketentuan kompetisi
- [x] Pastikan semua hasil eval tersimpan di folder `eval/`
- [x] Review final: tidak ada API key/credential yang ter-commit
- [x] Final commit dengan pesan deskriptif
- [x] Push ke repository kompetisi

---

## Ringkasan Metric Target

| Metric | Target | Diuji Di Fase |
|---|---|---|
| Retrieval Recall@5 | ≥ 0,80 | Fase 4 & 5 |
| Factual Accuracy | ≥ 0,75 | Fase 5 |
| Triage Detection F1 | ≥ 0,90 | Fase 3 |
| PII Redaction Rate | 100% | Fase 2 |
| Guardrail Block Rate | ≥ 0,95 | Fase 5 |

---

## Dependensi Antar Task

```
Fase 1 (Setup & Ingest)
    └─► Fase 2 (API + PII)
            └─► Fase 3 (Triage + Guardrail)
                    └─► Fase 4 (Hybrid Retrieval + LLM)
                            └─► Fase 5 (Adversarial Eval)
                                    └─► Fase 6 (Finalisasi)
```

> ⚠️ Fase 4–5 bersifat berurutan dengan Fase 1–3. Jangan mulai retrieval sebelum PII dan triage aktif.
