# architecture.md — Dokter Penjaga

> Emergency-Aware Medical RAG Agent  
> Kompetisi INaAI 2026 · Track: AI Engineer · Domain 3: Medical AI

---

## Gambaran Umum

Dokter Penjaga adalah sistem RAG (Retrieval-Augmented Generation) berlapis yang dirancang dengan prinsip **safety-first**. Alur utama memastikan kondisi darurat selalu ditangani sebelum sistem masuk ke proses retrieval dan generasi jawaban.

```
User Input
    │
    ▼
┌─────────────────────┐
│  1. PII Redaction   │  ← Microsoft Presidio
│     (Presidio)      │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  2. Triage Check    │  ← Rule-based Classifier (deterministik)
│  (Emergency Gate)   │
└────────┬────────────┘
         │
    [Darurat?]
    /         \
  YES          NO
   │            │
   ▼            ▼
Respons     ┌──────────────────────┐
119 &       │  3. Guardrail Input  │  ← Prompt injection / jailbreak filter
Arahan      │     Validation       │
Segera      └────────┬─────────────┘
                     │
                     ▼
            ┌──────────────────────┐
            │  4. Hybrid Retrieval │  ← Qdrant (vektor) + BM25 (kata kunci)
            │  + Temporal Ranking  │     dengan bobot tahun dokumen
            └────────┬─────────────┘
                     │
                     ▼
            ┌──────────────────────┐
            │  5. Conflict Check   │  ← Deteksi perbedaan antar dokumen
            │  (Multi-year view)   │     → tampilkan kedua versi jika beda
            └────────┬─────────────┘
                     │
                     ▼
            ┌──────────────────────┐
            │  6. LLM Generation   │  ← Claude / model via Anthropic API
            │  (RAG Synthesis)     │
            └────────┬─────────────┘
                     │
                     ▼
            ┌──────────────────────┐
            │  7. Guardrail Output │  ← Validasi respons sebelum dikirim
            │     Validation       │
            └────────┬─────────────┘
                     │
                     ▼
            ┌──────────────────────┐
            │  8. Audit Logger     │  ← Log immutable semua keputusan sistem
            └────────┬─────────────┘
                     │
                     ▼
                User Response
```

---

## Komponen Detail

### 1. PII Redaction Layer
| Atribut | Detail |
|---|---|
| **Library** | Microsoft Presidio |
| **Target PII** | NIK, Nama, Alamat, Nomor HP, Email |
| **Mode** | Anonymize (replace dengan `[REDACTED]`) |
| **Posisi** | Paling pertama — sebelum log dan sebelum ke komponen lain |
| **Metric** | Redaction Rate = 100% |

### 2. Triage / Emergency Gate
| Atribut | Detail |
|---|---|
| **Tipe** | Rule-based classifier (deterministik) |
| **Metode** | Keyword matching + pattern rules |
| **Contoh Trigger** | "serangan jantung", "overdosis", "tidak bernapas", "pingsan" |
| **Output Darurat** | Respons tetap + arahan hubungi **119** |
| **Metric** | Triage Detection F1 ≥ 0,90 |
| **Konfigurasi** | Keyword list di config file, bukan hardcoded |

### 3. Guardrail — Input Validation
| Atribut | Detail |
|---|---|
| **Target** | Prompt injection, jailbreak, permintaan berbahaya |
| **Metode** | Pattern matching + semantic classifier |
| **Log** | Setiap block dicatat dengan label `BLOCKED_INJECTION` |
| **Metric** | Guardrail Block Rate ≥ 0,95 |

### 4. Knowledge Base & Hybrid Retrieval
| Atribut | Detail |
|---|---|
| **Vector DB** | Qdrant |
| **Keyword Search** | BM25 |
| **Sumber Data** | PubMed Open Access (2018–2025), WHO Clinical Guidelines |
| **Metadata wajib** | `year`, `source`, `title`, `url` |
| **Scoring Formula** | `score = α·semantic + (1−α)·BM25 + λ·f(year)` |
| **Metric** | Retrieval Recall@5 ≥ 0,80 |

**Alasan BM25 dipertahankan:** BM25 unggul untuk mencocokkan nama obat dan istilah medis spesifik yang sering tidak tertangkap oleh pencarian semantik saja.

### 5. Conflict Detection (Temporal Transparency)
- Jika dokumen dari tahun berbeda memberikan informasi yang bertentangan → sistem menampilkan **kedua versi** secara eksplisit beserta tahunnya.
- Tidak ada pemilihan diam-diam; transparansi diutamakan.

### 6. LLM Generation
| Atribut | Detail |
|---|---|
| **Model** | Claude (via Anthropic API) |
| **Input** | Query + dokumen hasil retrieval (dengan metadata tahun & sumber) |
| **Output** | Jawaban + referensi sumber wajib disertakan |
| **Confidence** | Jika retrieval lemah, respons wajib menyatakan ketidakpastian |

### 7. Guardrail — Output Validation
- Validasi respons LLM sebelum dikirim ke pengguna.
- Respons yang mengandung instruksi berbahaya, dosis spesifik, atau saran penghentian obat tanpa arahan profesional → **ditolak dan di-log**.

### 8. Audit Logger
- Log immutable untuk semua keputusan: triage trigger, PII redaction, guardrail block, retrieval score.
- Log tidak menyimpan teks PII asli (hanya versi tersensor).

---

## Stack Teknologi

| Komponen | Pilihan | Alasan |
|---|---|---|
| Vector DB | **Qdrant** | Mendukung filter metadata (tahun), mudah dikelola |
| Keyword Search | **BM25** | Akurat untuk nama obat & istilah medis |
| PII Redaction | **Microsoft Presidio** | Siap pakai, akurasi tinggi |
| Emergency Gate | **Rule-based classifier** | 100% deterministik, tidak bergantung pada model |
| LLM | **Claude (Anthropic API)** | Kemampuan reasoning & summarization yang kuat |
| API Framework | **FastAPI** | Performa tinggi, dokumentasi otomatis |

---

## Environment Variables

```env
ANTHROPIC_API_KEY=
QDRANT_HOST=
QDRANT_PORT=
TRIAGE_KEYWORD_CONFIG_PATH=
PRESIDIO_LANGUAGE=id
AUDIT_LOG_PATH=
ALPHA_HYBRID=0.6
LAMBDA_TEMPORAL=0.1
```

---

## Diagram Alur Retrieval Hybrid

```
Query (sudah disensor)
        │
   ┌────┴────┐
   │         │
Qdrant      BM25
(vektor)  (keyword)
   │         │
   └────┬────┘
        │
  Temporal Re-rank
  (bobot tahun dokumen)
        │
  Top-K Documents
  (dengan metadata: title, year, source)
        │
  Conflict Detection
  (beda tahun & info? → tampilkan dua versi)
        │
  Kirim ke LLM
```
