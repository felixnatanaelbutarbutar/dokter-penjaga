# Catatan Penggunaan AI dalam Pengembangan (AI Usage Log)

Sesuai dengan regulasi INaAI 2026, dokumen ini menjelaskan pemanfaatan kecerdasan buatan (AI) selama pengembangan proyek **Dokter Penjaga**.

## Model AI yang Digunakan
- **Antigravity IDE (Gemini-based Agent):** Digunakan sebagai Asisten Pemrograman (*Pair Programmer*) otonom. AI secara aktif membantu arsitektur, *coding*, deteksi *bugs*, pembuatan *unit test*, serta penyusunan evaluasi *Adversarial* secara menyeluruh di 6 fase.
- **Anthropic Claude (Sonnet 3.5 & Sonnet 4):** Digunakan sebagai otak *Retrieval-Augmented Generation (RAG)* pada saat *runtime* (membangkitkan jawaban medis) dan bertindak sebagai Hakim Faktual (*LLM-as-Judge*) pada saat uji kualitas.
- **paraphrase-multilingual-mpnet-base-v2 (Sentence Transformers):** Model ML yang digunakan untuk membuat vektor/embeddings dokumen *knowledge base* dan *query* pencarian.
- **spaCy & Microsoft Presidio:** Model NLP spesifik yang digunakan khusus untuk melakukan pendeteksian nama entitas bernama (NER) untuk kebutuhan penyensoran data diri pengguna (PII Redaction).

## Proporsi & Kontribusi
- **Pembuatan Kode Dasar (Boilerplate):** 90% AI (Antigravity), 10% Manusia (Desain Arsitektur)
- **Logika Bisnis & Fitur Keselamatan (Guardrails/Triage):** 80% AI, 20% Manusia (Instruksi Prompting & Arah Filosofis)
- **Evaluasi & Pengujian (Red Teaming):** 100% dibuat secara sintetis oleh AI (Prompt Evaluasi) dan dieksekusi oleh skrip otomatis.

## Deklarasi
Kami menyetujui bahwa kode sumber yang dihasilkan menggunakan AI telah ditinjau kembali dari segi etika medis, fungsionalitas, dan keamanan (tidak mengandung skrip perusak, *backdoors*, atau logika tersembunyi yang mendiskriminasi pengguna). Sistem dirancang dengan filosofi kehati-hatian (*safety-first*).
