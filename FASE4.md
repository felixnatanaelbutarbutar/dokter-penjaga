# Rangkuman Fase 4: Hybrid Retrieval & LLM Integration
**Proyek: Dokter Penjaga (Medical AI Assistant)**

Fase 4 adalah **jantung dari kecerdasan sistem RAG (Retrieval-Augmented Generation)** ini. Pada fase ini, sistem mulai mampu menarik informasi relevan dari database dan memprosesnya secara cerdas menggunakan Model Bahasa Besar (LLM).

Berikut adalah hal-hal penting yang telah berhasil dibangun pada Fase 4:

## 1. Hybrid Search Engine (Pencarian Ganda)
Untuk menghindari halusinasi medis (di mana AI mengarang informasi yang salah), kami tidak hanya mengandalkan *Vector Search* biasa. Kami membangun **Hybrid Retrieval**:
- **Semantic Search (Qdrant):** Mencari dokumen berdasarkan *kemiripan makna* kalimat.
- **Keyword Search (BM25):** Mencari berdasarkan *kecocokan kata kunci eksak*. Ini sangat penting di dunia medis agar nama obat (misal: "Paracetamol") dan dosis tidak tertukar atau salah tafsir.
- Sistem akan menggabungkan skor dari keduanya dengan pembobotan $\alpha$ (Alpha) untuk menghasilkan daftar dokumen yang paling akurat.

## 2. Temporal Re-Ranking & Deteksi Konflik
Ilmu medis selalu diperbarui. Panduan tahun 2018 mungkin sudah direvisi pada tahun 2024.
- **Temporal Boost:** Dokumen pedoman terbaru akan mendapatkan "bonus skor" ($\lambda$) sehingga diprioritaskan muncul paling atas.
- **Conflict Detection:** Jika mesin menemukan dua dokumen pedoman yang berbeda tahun (jarak >3 tahun) namun sama-sama relevan, sistem akan membunyikan alarm (*Conflict Flag*). AI diwajibkan untuk menyebutkan **kedua** dokumen tersebut beserta tahunnya, sehingga pengguna mendapatkan informasi yang utuh dan berimbang.

## 3. Integrasi Anthropic API & Guardrails Output
Sistem dihubungkan ke LLM *Anthropic Claude* melalui API. Kami menyuntikkan *System Prompt* yang sangat ketat:
- **Kewajiban Mengutip:** AI harus menyertakan nama pedoman dan tahun referensi di setiap jawabannya.
- **Peringatan Dosis:** AI dilarang memberikan dosis mutlak tanpa perintah dari dokumen.
- **Low Confidence Alert:** Jika skor kecocokan dokumen (retrieval) terlalu rendah (di bawah 0.5), AI akan memberikan peringatan kepada pengguna bahwa informasi yang dimiliki belum tentu akurat, dan sangat menyarankan untuk berkonsultasi ke dokter nyata.

## 4. End-to-End Pipeline Terintegrasi
Kami menggabungkan seluruh komponen keamanan yang sudah dibuat di Fase 2 dan 3, sehingga kini alur utamanya adalah:
1. Pesan Pengguna masuk $\rightarrow$ **PII Redaction** (Sensor data diri).
2. Teks disensor $\rightarrow$ **Input Guardrail** (Tolak jika prompt injeksi/jailbreak).
3. Aman dari injeksi $\rightarrow$ **Emergency Triage** (Cek apakah darurat).
4. Tidak darurat $\rightarrow$ **Hybrid Retrieval** (Tarik dokumen medis relevan).
5. Dokumen siap $\rightarrow$ **Anthropic LLM** (Rakit jawaban & berikan kutipan).

Semua langkah ini berhasil di-uji (End-to-End Test) dengan lancar! 🚀
