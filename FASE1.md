# Rangkuman Fase 1: Setup & Ingestion Pipeline
**Proyek: Dokter Penjaga (Medical AI Assistant)**

Fase 1 berfokus pada pembangunan fondasi utama sistem, yaitu penyiapan environment, database vektor, dan *pipeline* untuk memasukkan dokumen-dokumen medis ke dalam *knowledge base* (basis pengetahuan) agar nantinya bisa dicari oleh AI (RAG - Retrieval-Augmented Generation).

Berikut adalah detail teknis yang telah dikerjakan untuk dijelaskan kepada juri:

## 1. Environment & Architecture Setup
*   **Isolasi Environment:** Menggunakan Virtual Environment (`.venv`) Python untuk memastikan *dependency* (library yang digunakan) terisolasi dengan baik.
*   **Dependency Management:** Menginstal *library* utama sesuai kebutuhan *compliance* proyek:
    *   `qdrant-client`: Untuk koneksi ke database vektor Qdrant.
    *   `sentence-transformers`: Untuk mengubah teks menjadi vektor (*embedding*).
    *   `rank-bm25`: Untuk *keyword search* lokal yang dikombinasikan dengan *vector search* (Hybrid Search).
    *   `pytest`: Untuk pengujian unit (*unit testing*).
*   **Konfigurasi Keamanan:** Mengamankan kredensial (seperti API Keys Anthropic dan Qdrant Cloud) menggunakan file `.env` yang tidak dimasukkan ke dalam version control (`.gitignore`). Skema konfigurasi divalidasi menggunakan Pydantic.

## 2. Vector Database (Qdrant Cloud)
*   **Cloud Deployment:** Berhasil menghubungkan aplikasi dengan *cluster* Qdrant Cloud yang sudah disediakan.
*   **Pembuatan Koleksi:** Membuat koleksi bernama `medical_docs` dengan konfigurasi *Cosine Similarity* dan dimensi vektor **768** (disesuaikan dengan model *embedding* yang dipilih).

## 3. Peningkatan Model Embedding (Semantic Search)
*   **Model Terpilih:** Menggunakan model `paraphrase-multilingual-mpnet-base-v2` (768 dimensi, ukuran ~440MB).
*   **Alasan Pemilihan:** Model ini sangat handal untuk bahasa Indonesia dan Inggris, dan memiliki kualitas pemahaman semantik yang jauh lebih tinggi dibanding model yang lebih kecil.
*   **Optimasi Infrastruktur:** Untuk mengatasi masalah koneksi/timeout saat mengunduh dari HuggingFace (isu CDN Xet Storage), kami membuat *script* khusus (`scripts/download_model.py`) untuk mengunduh model secara utuh dan menyimpannya di penyimpanan lokal (`models/`). Pipeline ingestion sekarang langsung membaca dari disk lokal, sehingga jauh lebih cepat dan stabil.

## 4. Pipeline Ingestion Dokumen (Data-02 & Data-05 Compliance)
*   **Format Dokumen Tersusun:** Kami menyusun dokumen demo dalam format JSON. Mengapa JSON dan bukan `.txt` biasa? Karena sistem memiliki aturan ketat (*compliance*):
    *   **DATA-02:** Dokumen wajib memiliki metadata `year` (tahun).
    *   **DATA-05:** Sumber (`source`) wajib berasal dari sumber terpercaya, yaitu `who` atau `pubmed`.
    Dengan JSON, kita bisa menyematkan teks kustom (*full_text*) bersama dengan metadata yang valid agar sistem menerimanya.
*   **Dokumen Demo Berkualitas Tinggi:** Kami membuat konten dokumen "buatan sendiri" yang berisi sari pati pedoman resmi WHO agar sangat relevan untuk demo kompetisi. Dokumen tersebut mencakup:
    1.  Penanganan Hipertensi (2021)
    2.  Panduan Tuberkulosis (2022)
    3.  Klasifikasi Diabetes (2019)
    4.  Manajemen Demam/Paracetamol (2023) - *Untuk demo limitasi dosis (guardrail)*.
    5.  Perawatan Diri Kesehatan Mental (2022) - *Untuk demo deteksi krisis (triage)*.
*   **Proses Ingestion:** 
    1.  **Validasi:** Memastikan metadata lengkap dan valid.
    2.  **Chunking:** Memotong teks panjang menjadi bagian-bagian kecil (512 token) agar pencarian lebih akurat.
    3.  **Embedding:** Mengubah teks menjadi vektor (768 dimensi).
    4.  **Upsert:** Memasukkan vektor dan metadata ke Qdrant Cloud.
    5.  **BM25 Indexing:** Menyimpan indeks pencarian kata kunci lokal (`data/bm25_index.pkl`) untuk mendukung *Hybrid Search* nanti di Fase 2.
*   **Hasil:** 8 dokumen berhasil divalidasi, diubah menjadi 20 *chunks*, dan berhasil di-upload ke Qdrant tanpa error (100% Success).

## 5. Unit Testing
*   **Validasi Keamanan Data:** Telah dibuat 22 *unit tests* (`tests/test_ingest.py`) yang semuanya **LULUS (22/22 PASSED)**.
*   *Test* ini membuktikan kepada juri bahwa aturan ketat proyek (seperti menolak dokumen tanpa tahun atau dari sumber yang tidak valid) benar-benar diimplementasikan dan berjalan dengan baik di level kode.

---
**Status Fase 1:** SELESAI (100%)
**Siap Lanjut ke Fase 2:** Pembuatan API, RAG, Privacy Layer (Redaction), dan Audit Log.
