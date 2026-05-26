# AI Usage Log (Catatan Penggunaan AI)

Sesuai dengan regulasi INaAI 2026, dokumen ini secara transparan mendeklarasikan pemanfaatan kecerdasan buatan (AI) selama pengembangan proyek **Dokter Penjaga**.

## 1. Model AI yang Digunakan
* **Antigravity IDE (Gemini-based Agent):** Digunakan sebagai Asisten Pemrograman Utama (*Autonomous Pair Programmer*). Berperan aktif merancang arsitektur, *coding* infrastruktur backend (FastAPI), *debugging* error, menyusun *unit test*, serta membangun *eval framework* yang komprehensif dari awal hingga akhir.
* **Anthropic Claude (Sonnet 3.5 & Sonnet 4):** Model inti LLM yang digunakan untuk men- *generate* respons medis pada saat *runtime* (sistem RAG). Claude juga difungsikan ganda secara mandiri sebagai Hakim Evaluasi Otomatis (*LLM-as-Judge*) untuk menguji akurasi faktual.
* **paraphrase-multilingual-mpnet-base-v2 (Sentence Transformers):** Model *Machine Learning* yang memproses pembuatan vektor (*embeddings*) multi-bahasa untuk *Semantic Search* di database Qdrant.
* **Microsoft Presidio & spaCy:** Pustaka kecerdasan buatan untuk *Natural Language Processing* (NLP) lokal yang secara khusus difungsikan mengenali *Named-Entity Recognition* (NER) demi meredaksi data privasi pasien (PII).

## 2. Proporsi & Kontribusi AI vs Manusia
* **Desain Arsitektur & Ideasi Konsep:** 60% Manusia, 40% AI. (Manusia mendefinisikan *Defense-in-Depth* dan *Triage* darurat, AI menyusun abstraksinya).
* **Pembuatan Kode Dasar & Logika Bisnis:** 95% AI, 5% Manusia. (AI mengimplementasikan struktur kode, dependensi, fungsi asinkronus, hingga antarmuka Glassmorphism HTML/JS).
* **Evaluasi & Pengujian (*Red Teaming*):** 100% AI. Dataset sintetis, evaluasi Triage, evaluasi Retrieval, hingga Factual Accuracy sepenuhnya dibangkitkan dan diuji secara skriptural oleh AI.

## 3. Proses & Prompts Utama
Selama proses pengembangan, *prompt* diarahkan bukan hanya sekadar untuk "membuat chatbot", melainkan secara spesifik untuk membangun agen medis bertingkat keamanan tinggi. Contoh *prompt* fundamental yang membimbing AI:
> *"Bangun AI assistant untuk domain kesehatan dengan RAG. Harus memiliki guardrails untuk medical content, PII handling yang proper menggunakan Microsoft Presidio, dan sistem Deterministik Triage yang dapat mem-bypass LLM ketika pengguna menyebutkan kondisi mengancam nyawa (seperti sesak napas)."*

## 4. Deklarasi Integritas
Kami mendeklarasikan bahwa meskipun kode Mayoritas dihasilkan oleh AI, hasil akhir telah ditinjau (*reviewed*) untuk memastikan **tidak ada halusinasi medis terprogram**, fungsionalitas aman, dan kode tidak mengandung kerentanan berbahaya (*malicious scripts*). Sistem sengaja difilosofikan dengan prinsip *"Primum non nocere"* (First, do no harm) di mana fitur Triage Darurat menolak mengandalkan AI jika pasien terancam bahaya.
