# Technical Report: Dokter Penjaga
> **INaAI Hackathon 2026 Final Deliverable**  
> **Track:** AI Engineer · **Domain 3:** Medical AI / Health NLP  
> **Author:** Felix Natanael Butarbutar  

Dokumen ini berfungsi ganda sebagai *README* repositori dan *Technical Report* resmi untuk submission akhir kompetisi INaAI 2026. *Report* ini didesain ringkas, komprehensif, dan siap dikonversi menjadi format LaTeX/PDF.

---

## 1. System Design (Arsitektur)

**Dokter Penjaga** dibangun di atas kerangka pikir *Defense-in-Depth* dan prinsip medis dasar: *"Selamatkan nyawa dulu, jawab kemudian."* Arsitektur sistem kami tidak semata-mata mengandalkan LLM, melainkan dilindungi oleh *Layered Pipelines* deterministik.

**Alur Pemrosesan RAG Medis:**
1. **PII Redaction (Data Privacy):** Kueri input pengguna segera melewati komponen `core/pii.py`. Menggunakan Microsoft Presidio, seluruh identitas (Nama, NIK, dsb) secara otomatis digantikan dengan token anonim (contoh: `<PERSON>`) sebelum direkam atau dikirim ke LLM.
2. **Deterministik Triage Bypass:** Sebelum AI membaca kueri, pengklasifikasi *triage* kami memindai kata kunci yang mengancam nyawa (contoh: "sesak napas", "nyeri dada hebat"). Jika terdeteksi, sistem langsung membatalkan proses RAG secara otonom dalam < 0.1 detik dan mengarahkan pengguna untuk menelepon 119.
3. **Input Guardrail:** Penyaring leksikal dan regex memblokir segala bentuk *Prompt Injection* dan permintaan dosis/racun ilegal sebelum membuang *resource* ke eksternal LLM.
4. **Hybrid Retrieval + Temporal Filter:** Menggabungkan Vector/Dense Search (Qdrant) dan Sparse Search (BM25) dengan pembobotan dinamis untuk memastikan pencarian kontekstual maupun kecocokan spesifik nama obat berhasil ditangkap. Dokumen usang disaring/dikurangi bobotnya melalui *Temporal Boost*.
5. **LLM Generation & Output Guardrail:** Claude mensintesis jawaban berbasis konteks. *Output* yang keluar divalidasi kembali untuk memastikan tidak ada saran dosis absolut tanpa konsultasi klinis.

## 2. Data

Sistem kami mengasimilasi data medis yang difokuskan pada format pedoman klinis:
- **Klinis & Pedoman (Prototype):** Untuk keperluan MVP (*Minimum Viable Product*) Hackathon ini, *knowledge base* yang kami gunakan adalah **data sintetis (*dummy data*)** berformat JSON yang kami buat sedemikian rupa agar meniru struktur, gaya bahasa, dan kedalaman medis dari pedoman *World Health Organization* (WHO) dan literatur jurnal *PubMed*.
- **Pemrosesan Metadata:** Data dimasukkan melalui *Ingestion Pipeline* khusus kami. Segala dokumen yang masuk WAJIB memiliki metadata `year`, `title`, dan `source` (wajib diisi 'who' atau 'pubmed'). Dokumen tanpa atribut tahun yang jelas akan **ditolak secara otomatis** (Hard Check) guna mencegah sistem mengacu pada praktik medis kedaluwarsa.
- **Chunking Strategy:** Teks dokumen dipecah (*chunked*) berbasis paragraf dengan irisan tumpang-tindih (*overlap*) sejauh 64 token untuk mempertahankan keutuhan konteks antar sub-kalimat.

## 3. Model

Sistem ini didayagai oleh tiga model terintegrasi yang bekerja dalam harmoni:
- **Embedding Model (paraphrase-multilingual-mpnet-base-v2):** Digunakan untuk menterjemahkan teks *knowledge base* maupun kueri Indonesia-Inggris menjadi representasi ruang vektor. Model ML ini dipilih karena kemampuannya mempertahankan relasi semantik dalam kondisi pertukaran bahasa (*code-switching*).
- **Inference LLM (Anthropic Claude 3.5 Sonnet):** Bertindak sebagai otak sintesis sentral. Sonnet dipilih karena menyeimbangkan kecerdasan pemahaman, keandalan instruksi sistem, serta biaya tokenisasi yang jauh lebih ekonomis untuk kueri RS skala besar dibanding Opus.
- **NER NLP Model (spaCy & Microsoft Presidio):** Model lokal yang dijalankan khusus untuk deteksi Entitas Bernama (PII/Privacy Handling).

## 4. Evaluation (Metrik & Kinerja)

Kami mendirikan *framework* pengujian terotomatisasi ketat yang memvalidasi setiap komponen RAG:
* **Factual Accuracy (100%):** Diuji menggunakan algoritma *LLM-as-Judge*. Hakim dikondisikan tanpa basis pengetahuan luarnya sendiri untuk memeriksa *Hallucination Rate*. Target proyek: ≥ 0.75 | Hasil Eksekusi: **1.00**
* **Retrieval Recall@5 (100%):** Memastikan pedoman medis terkait masuk ke 5 kandidat dokumen teratas. Target proyek: ≥ 0.80 | Hasil Eksekusi: **1.00**
* **Triage Detection F1-Score (100%):** Menggunakan *dataset* sintetis gawat darurat, model klasifikasi deterministik kami berhasil menolak 100% kasus ancaman nyawa tanpa *False Negative*.

## 5. AI Usage Log
Seluruh proses pembangunan (desain, pengkodean, pembuatan kasus uji *adversarial*, dokumentasi evaluasi) dilakukan melalui integrasi produktif 90% AI (*Antigravity IDE Asisstant*, *Claude*, *Gemini*) dan 10% Manusia (Arahan Arsitektur & Filosofi Sistem). Silakan merujuk pada dokumen terpisah `AI_USAGE_LOG.md` di dalam repositori untuk melihat detail deklarasi lengkap.

## 6. Limitations (Batasan Sistem Saat Ini)
Kelemahan atau batasan yang kami sadari dan bisa diperbaiki ke depannya:
1. **Model BM25 Statis:** Walaupun *Hybrid Search* kami ampuh, tokenisasi *keyword* untuk BM25 masih menggunakan fungsi pemisah jarak (*whitespace*) dasar. Ke depannya diperlukan *Tokenizer NLP Indonesia* resmi agar pengenalan akar kata (Sastrawi) berjalan optimal.
2. **Absensi Analitik Visual Logging:** Meski Audit Logger sudah menyimpan kejadian kritis (misal blokir *injection*) dalam format JSON terstruktur dengan efisien, sistem ini belum memiliki Dasbor (Kibana/Grafana) agar *Admin* Rumah Sakit dapat menginspeksi metrik serangan secara grafik langsung.

---

## 🚀 Panduan Eksekusi Juri (Local Deploy)

Skrip *endpoint* dibangun menggunakan kerangka **FastAPI**. Aplikasi ini berjalan secara lokal.

**1. Persiapan Dependensi & Environment**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download id_core_news_lg
python -m spacy download en_core_web_lg
```
*(Jangan lupa mengisi `ANTHROPIC_API_KEY` dan konfigurasi Qdrant di dalam file `.env` berdasarkan `env.example`)*

**2. Jalankan Inference Endpoint Utama**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**3. Akses**
- **Web UI Chatbot:** Buka `http://localhost:8000/` di browser Anda.
- **REST API Endpoint:** Buka `http://localhost:8000/docs` (Swagger UI) untuk melakukan *Hit Endpoint* `/api/chat/ask`.

**4. Validasi Metrik Evaluasi**
Cukup jalankan dua skrip ini di terminal untuk melihat kebenaran angka evaluasi kami (Buktikan secara Reproducible!):
```bash
python scripts/run_triage_eval.py
python scripts/run_factual_eval.py
```
