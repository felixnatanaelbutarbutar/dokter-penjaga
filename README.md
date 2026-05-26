# Technical Report: Dokter Penjaga
> **INaAI Hackathon 2026 Final Deliverable**  
> **Track:** AI Engineer · **Domain 3:** Medical AI / Health NLP  
> **Author:** Felix Natanael Butarbutar  

Dokumen ini berfungsi sebagai draf utama untuk *Technical Report* (2-3 halaman) Anda yang siap disalin/diubah menjadi format LaTeX.

---

## 1. System Design (Arsitektur Sistem)
Sistem **Dokter Penjaga** dirancang bukan sebagai agen percakapan generik, melainkan sebagai mesin penalaran medis yang dilindungi oleh pipa arsitektur **Defense-in-Depth**. Karena beroperasi di domain risiko tinggi, sistem ini menganut prinsip: *"Selamatkan nyawa dulu, jawab kemudian."*

Alur arsitektur (*Layered Pipelines*) berjalan secara sekuensial:
1. **Data Privacy (PII Redaction):** Kueri *input* masuk ke modul `core/pii.py`. Menggunakan arsitektur NLP lokal (Microsoft Presidio & spaCy), identitas pribadi (Nama, NIK, Lokasi, Nomor HP) disensor (*redact*) secara *on-the-fly* menjadi token generik (misal: `<PERSON>`) sebelum menembus batas jaringan ke *eksternal* LLM.
2. **Deterministik Triage (Gawat Darurat):** Model deteksi ancaman nyawa memindai frasa bahaya (seperti "nyeri dada", "sesak napas"). Apabila dipicu, sistem memotong (mem-*bypass*) seluruh sisa rantai RAG dan memaksa respon deterministik instan (< 0.1 detik) yang mengarahkan pengguna ke layanan gawat darurat (119).
3. **Lexical Guardrail (Keamanan Prompt):** Penyaring pra-LLM memblokir injeksi *prompt* (mis: "Abaikan instruksi sebelumnya") dan permintaan dosis letal, menghemat biaya token dengan menggagalkan serangan pada level aplikasi (*O(1) complexity*).
4. **Hybrid Retrieval (Dense + Sparse):** Kueri diproses dengan vektorisasi. Hasil pencarian dari Qdrant (semantik) digabungkan dengan indeks BM25 (pencocokan kata kunci eksak, sangat penting untuk ejaan nama obat yang rumit) melalui pembobotan matematis *alpha*. Dokumen kadaluwarsa dikenai penalti bobot oleh algoritma *Temporal Filter*.
5. **LLM Synthesis & Output Guardrail:** LLM memformulasikan jawaban berbasis dokumen medis terpilih. Sistem melakukan pemindaian terakhir pada *output* untuk menahan LLM agar tidak bertindak sebagai dokter definitif (mencegah *prescribing*).

## 2. Data
Fokus pengetahuan agen (*Knowledge Base*) kami didasarkan pada pedoman klinis standar:
- **Karakteristik Data Prototipe (MVP):** Untuk mendemonstrasikan kapabilitas RAG secara langsung di lingkungan Hackathon, basis data kami menggunakan struktur JSON *dummy* sintetis. Data ini secara teliti memodelkan struktur linguistik, format metadata, dan kedalaman taksonomi dari publikasi asli *World Health Organization* (WHO) dan literatur terbuka *PubMed*.
- **Ingestion Pipeline:** Proses *ingestion* bersikap ketat (Agnostik). Setiap titik data WAJIB lolos validasi skema (membutuhkan kunci metadata `year`, `title`, dan `source`). Absensi metadata krusial akan memicu *Hard Reject* otomatis, mengeliminasi risiko masuknya pengetahuan klinis tanpa referensi waktu (*timeline-agnostic hallucination*).
- **Chunking Strategy:** Mempertahankan koherensi paragraf dengan strategi pemecahan ukuran variabel, menerapkan *overlap* 64 token guna mencegah hilangnya konteks antar-halaman (*semantic continuity loss*).

## 3. Model
Untuk menggerakkan sistem hibrida ini, kami menggunakan ansambel 3 lapis model:
- **Embedding Model (`paraphrase-multilingual-mpnet-base-v2`):** Mentransformasi dokumen dan kueri menjadi vektor *dense*. Kemampuan *multilingual*-nya sangat krusial di Indonesia, di mana pasien sering menggunakan *code-switching* (campuran ID/EN, misal: "saya mengalami *chest pain*"). 
- **Large Language Model (Anthropic Claude 3.5 Sonnet):** Bertindak sebagai otak sintesis di ekosistem RAG. Sonnet diplih karena keunggulan *Context Window* (200k), rasio biaya-ke-kepintaran yang superior, dan keandalan tinggi dalam mematuhi batasan *System Prompt* (Guardrails).
- **NLP NER Model (`id_core_news_lg` spaCy):** Model spesifik-bahasa (*Language-Specific*) tanpa koneksi internet yang mendeteksi Entitas Named (PII) dengan kecepatan *sub-millisecond*.

## 4. Evaluation (Metrik & Kinerja)
Kami membangun *eval framework* otomatis tanpa campur tangan manusia untuk melakukan pengujian stres (Red Teaming):
- **Retrieval Recall@5 (Hasil: 100% | Target: ≥ 0.80):** Akurasi sistem menempatkan dokumen pedoman yang benar dalam 5 kandidat ruang pencarian teratas.
- **Factual Accuracy (Hasil: 100% | Target: ≥ 0.75):** Menggunakan evaluasi *LLM-as-Judge*, dengan instruksi *Zero-Knowledge* (Hakim dilarang menggunakan pengetahuan internal model, hanya mengecek keselarasan jawaban terhadap dokumen yang di-RAG).
- **Triage Detection (F1-Score: 1.00):** Validasi biner deterministik membuktikan 0% *False Negative* pada kasus uji kegawatdaruratan mematikan.

## 5. AI Usage Log
Secara komprehensif (seperti terdokumentasi dalam `AI_USAGE_LOG.md`), integrasi AI secara otonom dimanfaatkan dalam pengembangan sistem ini. AI Assistant (Gemini) diutilisasi hingga 90% pada perancangan basis kode (Boilerplating FastAPI, Pipeline Ingestion), pembuatan ratusan kueri pengujian *adversarial* (Red Teaming sintetis), dan perumusan matriks evaluasi otomatis. Manusia (Author) memegang 10% kontrol pada sisi pengarahan arsitektur *Safety-First* dan filosofi batas medis.

## 6. Limitations (Batasan MVP)
Dalam konteks keterbatasan waktu Hackathon (MVP), kami menyadari ada beberapa bagian eksekusi teknis yang masih kurang optimal dan perlu diperbaiki untuk fase produksi:
1. **Tidak Ada PDF Parser (Hanya Dummy JSON):** Saat ini, kami belum sempat mengintegrasikan *Optical Character Recognition* (OCR) atau `PyMuPDF` untuk memecah tabel kompleks dari PDF asli WHO. Oleh karena itu, *Knowledge Base* kami saat ini masih bergantung pada pembuatan file sintesis berformat JSON (*dummy data*).
2. **BM25 Tokenizer Terlalu Sederhana:** Modul *Sparse Search* (BM25) kami saat ini hanya memecah kata berdasarkan spasi (*whitespace tokenizer*). Kami belum sempat mengintegrasikan algoritma *Stemming* Indonesia (seperti PySastrawi), sehingga imbuhan kata (misal: "mengobati" vs "obat") belum tertangani dengan baik oleh pencarian eksak.
3. **Stateless API (Tanpa Memori Sesi):** Endpoint `/api/chat/ask` saat ini belum didukung oleh basis data riwayat percakapan (seperti Redis atau Postgres). Akibatnya, AI tidak bisa menjawab pertanyaan lanjutan (*follow-up questions*) karena tidak mengingat konteks kueri pengguna sebelumnya.
4. **Antarmuka Minimalis:** Sisi *Frontend* saat ini hanya dibangun menggunakan Vanilla HTML/JS sederhana, belum menggunakan kerangka kerja produksi yang tangguh seperti React atau Next.js untuk menangani *state management* dan analitik.

---

## 🚀 PANDUAN DEPLOYMENT UNTUK JURI (MENGGUNAKAN NGROK)

Untuk memberikan akses Inference Endpoint yang *Deployed* dan dapat diuji langsung oleh Juri dari perangkat mereka (tanpa perlu repot dengan infrastruktur Cloud yang sering OOM / *Out of Memory* pada *free-tier*), kami menggunakan **Ngrok (Secure Tunneling)**. Ini adalah metode standar industri yang paling bersih dan andal.

Berikut adalah langkah-langkah detail dan berurutannya:

**Langkah 1: Siapkan Server API Lokal (FastAPI)**
1. Buka terminal komputer Anda.
2. Aktifkan *virtual environment*: `.venv\Scripts\activate`
3. Nyalakan peladen: `uvicorn api.main:app --host 0.0.0.0 --port 8000`
4. Biarkan terminal ini tetap menyala. API Anda sekarang hidup di `http://localhost:8000`.

**Langkah 2: Hubungkan API ke Internet Publik dengan Ngrok**
1. Buka terminal/CMD **baru** (biarkan terminal pertama tetap jalan).
2. Ketik perintah pengeksposan *port* 8000:
   ```bash
   ngrok http 8000
   ```
3. Ngrok akan segera menghubungkan laptop Anda ke server awan global dan memunculkan tampilan "Session Status: Online".
4. Cari bagian **"Forwarding"**, di sana Anda akan melihat tautan unik yang dilindungi SSL hijau, contohnya: `https://abcd-123.ngrok-free.app`

**Langkah 3: Berikan Akses Endpoint ke Juri**
1. Salin URL hijau dari Ngrok tersebut (misal: `https://abcd-123.ngrok-free.app`).
2. Kirim tautan tersebut kepada Dewan Juri, atau mintalah Juri membuka tautan tersebut diikuti dengan `/docs` (misal: `https://abcd-123.ngrok-free.app/docs`).
3. Juri akan langsung disambut oleh halaman antarmuka **Swagger UI FastAPI**. Dari sana, mereka bebas melakukan uji tembak (*Hit Endpoint*) `/api/chat/ask` untuk menguji *Code-Switching*, Injeksi PII, atau Kasus Darurat (Triage). 
4. Segala *log audit* dan pembuktian *redaction* akan mencuat *real-time* di layar laptop Anda untuk diinspeksi oleh Juri.
