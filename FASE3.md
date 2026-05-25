# Rangkuman Fase 3: Triage & Guardrails
**Proyek: Dokter Penjaga (Medical AI Assistant)**

Fase 3 berfokus pada **Pertahanan dan Keselamatan (*Safety & Defense*)**. Filosofi sistem ini adalah: *"Selamatkan nyawa dulu, jawab kemudian."*

Berikut adalah komponen yang dibangun pada Fase 3:

## 1. Input Guardrails (Anti-Jailbreak)
Kami membangun tameng pertama untuk melawan serangan *Prompt Injection* (upaya peretasan untuk mencuci otak AI).
- Sistem mencocokkan input dengan `guardrail_patterns.yaml` yang berisi pola-pola seperti *"ignore previous instructions"*, *"abaikan semua aturan"*, dan permintaan berbahaya ekstrem seperti *"dosis mematikan"*.
- Jika terdeteksi, AI tidak akan memproses kalimat tersebut dan langsung mengembalikan pesan penolakan yang sopan namun tegas.

## 2. Emergency Triage Classifier
Sebelum RAG/LLM bekerja, sistem wajib mengenali apakah keluhan pasien mengancam nyawa (contoh: serangan jantung, henti napas, pingsan).
- Kami menggunakan pendekatan **Rule-based Deterministik** (menggunakan YAML `triage_keywords.yaml`) untuk mendeteksi kata kunci gawat darurat.
- Jika darurat terdeteksi, sistem mem-bypass seluruh proses AI dan langsung memunculkan peringatan keras: **"⚠️ INI KONDISI DARURAT. Segera hubungi 119 atau bawa ke IGD terdekat sekarang."**
- Deteksi ini dilakukan secara deterministik karena nyawa tidak boleh bergantung pada halusinasi probabilistik AI.

Semua penolakan akibat *Guardrail* maupun deteksi *Triage* direkam secara rapi ke dalam **Audit Logger** untuk keperluan evaluasi medis.
