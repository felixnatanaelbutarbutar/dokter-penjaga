# Rangkuman Fase 2: API & Privacy Layer
**Proyek: Dokter Penjaga (Medical AI Assistant)**

Pada Fase 2, kami membangun infrastruktur antarmuka sistem (API) dan mengimplementasikan lapisan keamanan data (Privacy Layer) yang ketat. Fokus utama fase ini adalah untuk memastikan seluruh data yang masuk ke sistem terlindungi dan setiap kejadian sistem tercatat dengan aman.

Berikut adalah detail teknis yang telah dikerjakan untuk dijelaskan kepada juri:

## 1. PII Redaction (Privacy Layer)
*   **Compliance (PII-01, PII-02):** Sesuai dengan aturan kompetisi, kami wajib memastikan tidak ada data Personally Identifiable Information (PII) yang bocor ke log maupun ke pemrosesan LLM.
*   **Implementasi:** Menggunakan **Microsoft Presidio** dipadukan dengan **spaCy** model NLP (Natural Language Processing).
*   **Custom Recognizer (Konteks Indonesia):** Karena Presidio aslinya didesain untuk teks bahasa Inggris, kami menambahkan *custom pattern recognizer* menggunakan Regex untuk mendeteksi data spesifik Indonesia:
    *   **Nomor Induk Kependudukan (NIK):** Regex 16-digit.
    *   **Nomor Telepon Indonesia:** Regex awalan `+62`, `08`, `628`.
*   **False Positive Filtering:** Model NLP sering salah mendeteksi kata ganti umum (seperti "Saya", "Aku", "Kami") sebagai nama orang (PERSON). Kami menambahkan modul *filter allow-list* sehingga kata-kata umum dalam bahasa Indonesia tidak terblokir.
*   **Hasil Pengujian:** Redaction rate mencapai **100%**. Pengujian otomatis membuktikan bahwa input berisi NIK, Nama, dan Lokasi berhasil disensor (diganti dengan token seperti `[REDACTED]`), sementara input medis biasa tetap aman.

## 2. Sistem Log Audit (Audit Logger)
*   **Compliance (OPS-01, PII-03):** Semua keputusan krusial dalam sistem (Triage, PII, Guardrails) harus dicatat secara deterministik tanpa membocorkan data pribadi mentah pengguna.
*   **Implementasi:** Menggunakan *library* `structlog` untuk menghasilkan JSON structured logging. 
*   **Fitur:** Setiap *incoming request* hanya akan mencatat *query* pengguna yang **telah melalui proses PII Redaction**. Format JSON memastikan bahwa file log dapat dengan mudah diproses oleh sistem SIEM (Security Information and Event Management) di masa mendatang jika aplikasi di-deploy di level enterprise.

## 3. Infrastruktur Web Server (FastAPI)
*   **Framework:** Dibangun di atas **FastAPI**, framework modern dan sangat cepat berbasis Python asinkron.
*   **Endpoint Utama:**
    *   `GET /health`: Untuk *healthcheck* / pemantauan *uptime* sistem. Memastikan *load balancer* tahu kapan sistem siap menerima trafik.
    *   `POST /ask`: Endpoint interaksi utama (entrypoint).
*   **Alur Data (Data Flow):** Request masuk melalui *AskRequest* (Pydantic Schema) → Masuk ke modul *PII Redactor* → Dicatat di *Audit Log* → Dikembalikan sebagai *AskResponse* yang aman. (Pada Fase selanjutnya, LLM dan Triage akan di-embed di alur ini).
*   **Validasi:** Menggunakan Pydantic untuk memvalidasi tipe data yang masuk dan keluar, menjaga API tetap aman dari injeksi *payload* berbahaya secara arsitektur.

---
**Status Fase 2:** SELESAI (100%)
**Siap Lanjut ke Fase 3:** Pembuatan Sistem Triage (Deteksi Gawat Darurat) & Guardrails.
