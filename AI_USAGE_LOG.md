# AI Usage Log (Catatan Penggunaan AI)

Sesuai dengan regulasi INaAI 2026, dokumen ini secara transparan mendeklarasikan pemanfaatan kecerdasan buatan (AI) selama pengembangan proyek **Dokter Penjaga**.

---

## 1. Model AI yang Digunakan

| Model | Peran dalam Proyek |
|-------|-------------------|
| **Antigravity IDE (Gemini Agent)** | Asisten Pemrograman Utama — merancang arsitektur, *coding* infrastruktur FastAPI, *debugging*, *unit test*, dan membangun *eval framework* dari awal hingga akhir |
| **Anthropic Claude 3.5 Sonnet** | (1) LLM inti untuk men-*generate* respons medis *runtime*, (2) **LLM-as-Judge** untuk mengevaluasi akurasi faktual jawaban sistem |
| **paraphrase-multilingual-mpnet-base-v2** | Embedding model untuk Dense Vector Search multilingual (ID/EN) di Qdrant |
| **Microsoft Presidio + spaCy** | NLP lokal untuk Named-Entity Recognition (NER) — mendeteksi dan menyensor PII pasien |

---

## 2. Proporsi Kontribusi AI vs Manusia

| Area | AI | Manusia |
|------|-----|---------|
| Desain Arsitektur & Ideasi | 40% | 60% — Manusia mendefinisikan filosofi *Defense-in-Depth*, *Triage* darurat, dan prinsip *Safety-First* |
| Implementasi Kode | 95% | 5% — Manusia memberikan *prompt* terstruktur dan meninjau hasil |
| Evaluasi & Red Teaming | 100% | 0% — Dataset sintetis dan skrip eval sepenuhnya dihasilkan AI |

---

## 3. Prompt Awal yang Mendorong Seluruh Pengembangan

*Prompt* pertama yang ditulis oleh Author kepada Antigravity AI Agent — yang menjadi panduan seluruh 6 fase pengembangan:

> *"Kamu adalah senior AI engineer yang membantu saya membangun sistem "Dokter Penjaga" — sebuah Emergency-Aware Medical RAG Agent untuk kompetisi INaAI 2026.*
>
> *Baca ketiga file berikut sebagai konteks utama:*
> - *rules.md → semua constraint dan aturan wajib*
> - *architecture.md → desain sistem dan pipeline*
> - *tasks.md → breakdown pekerjaan per fase*
>
> *Mulai dari Fase 1 (Jam 01–04): Setup & Ingestion.*
>
> *Tugas pertama:*
> 1. *Buat struktur direktori proyek lengkap*
> 2. *Buat requirements.txt dengan semua dependency yang dibutuhkan*
> 3. *Buat .env.example dengan semua environment variable sesuai architecture.md*
> 4. *Buat script ingestion: load dokumen → chunk → embed → upsert ke Qdrant + build BM25 index*
> 5. *Setiap file harus production-quality, bukan toy code*
>
> *Constraint wajib dari rules.md:*
> - *Dokumen tanpa metadata year/source/title HARUS ditolak (DATA-02)*
> - *α dan λ untuk hybrid scoring harus dari env variable, bukan hardcoded (DATA-03)*
> - *Tidak ada credential hardcoded (OPS-03)*
>
> *Setelah selesai, checklist mana saja di tasks.md Fase 1 yang sudah selesai."*

Prompt ini mencerminkan bahwa Author tidak sekadar meminta AI "membuat chatbot", melainkan memandu AI untuk membangun **sistem rekayasa perangkat lunak terstruktur** yang bersandar pada *constraint* keamanan medis eksplisit dari awal.

---

## 4. Deklarasi Integritas

Meskipun sebagian besar kode dihasilkan oleh AI, seluruh hasil akhir telah ditinjau (*reviewed*) oleh Author untuk memastikan:
- Tidak ada halusinasi medis yang terprogram secara sengaja
- Kode bebas dari kerentanan keamanan (*backdoor*, *malicious script*)
- Sistem mematuhi prinsip *"Primum non nocere"* (First, do no harm) — dibuktikan oleh fitur Triage Darurat yang menolak melibatkan LLM jika nyawa pasien terancam
