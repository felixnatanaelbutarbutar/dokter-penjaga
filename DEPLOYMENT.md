# Panduan Deployment: Dokter Penjaga

Dokumen ini berisi langkah-langkah lengkap untuk menjalankan dan mengekspos *endpoint* API **Dokter Penjaga** agar dapat diakses oleh Juri secara publik menggunakan **Ngrok**.

---

## Prasyarat Sebelum Mulai

Pastikan hal-hal berikut sudah terpenuhi:
- [ ] Python 3.10+ sudah terinstall di komputer Anda
- [ ] File `.env` sudah diisi (salin dari `.env.example`, lalu isi `ANTHROPIC_API_KEY`, `QDRANT_API_KEY`, dan pengaturan Qdrant lainnya)
- [ ] Ngrok sudah terinstall dan akun sudah didaftarkan (lihat Langkah 0 di bawah)

---

## Langkah 0 — Daftar dan Setup Ngrok (Cukup Sekali)

Ngrok adalah layanan *secure tunneling* yang membolehkan laptop Anda diakses dari internet. **Gratis** dan tidak butuh kartu kredit.

1. **Daftar akun di** [https://ngrok.com/](https://ngrok.com/) — klik tombol "Sign Up" dan daftar menggunakan akun Google/GitHub Anda.
2. Setelah masuk ke *dashboard* Ngrok, buka menu **"Your Authtoken"** di panel sebelah kiri.
3. Salin *Authtoken* Anda (contoh: `2xxxxxxxxxxx_ABCxxx...`).
4. **Unduh Ngrok** dari halaman [https://ngrok.com/download](https://ngrok.com/download) — pilih versi Windows.
5. Ekstrak file `.zip` tersebut. Anda akan mendapatkan file bernama `ngrok.exe`.
6. Letakkan `ngrok.exe` di dalam folder proyek ini (`c:\INaAI\dokter-penjaga\`) agar mudah diakses.
7. Buka terminal baru di folder proyek dan jalankan perintah registrasi *token* (cukup sekali):
   ```powershell
   .\ngrok.exe config add-authtoken 2xxxxxxxxxxx_ABCxxx...
   ```
   *(Ganti dengan Authtoken milik Anda yang telah disalin dari dashboard)*
8. Jika berhasil, terminal akan mencetak: `Authtoken saved to configuration file`. Ngrok sudah siap digunakan selamanya.

---

## Langkah 1 — Aktifkan Virtual Environment Python

Buka terminal/PowerShell dan jalankan perintah berikut agar Python dapat menemukan dependensi proyek:

```powershell
# Izinkan eksekusi skrip PowerShell (hanya perlu dilakukan sekali per sesi terminal)
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Aktifkan virtual environment
.venv\Scripts\activate
```

Setelah berhasil, bagian kiri terminal Anda akan berubah menjadi `(.venv)`, menandakan lingkungan Python sudah aktif.

---

## Langkah 2 — Jalankan Server API (FastAPI)

Di dalam terminal yang sama (yang sudah aktif `.venv`), jalankan peladen API:

```powershell
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Tunggu hingga terminal mencetak baris ini (tandanya server sudah siap):
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

> **Penting:** Biarkan terminal ini tetap terbuka dan menyala. Jangan ditutup.

---

## Langkah 3 — Ekspos API ke Internet via Ngrok

Buka jendela terminal/PowerShell **baru** (biarkan terminal server API dari Langkah 2 tetap jalan di latar belakang). Jalankan perintah berikut:

```powershell
# Jika ngrok.exe ada di folder proyek
.\ngrok.exe http 8000

# Atau jika ngrok sudah ada di PATH sistem (bisa dipanggil dari mana saja)
ngrok http 8000
```

Dalam beberapa detik, Ngrok akan menampilkan layar seperti ini:
```
Session Status                online
Account                       felixnatanael@xxx.com (Plan: Free)
Forwarding                    https://abcd-1234-efgh.ngrok-free.app -> http://localhost:8000
```

Salin tautan **HTTPS** di bagian `Forwarding` tersebut (contoh: `https://abcd-1234-efgh.ngrok-free.app`). Inilah alamat publik API Anda yang bisa diakses dari mana saja.

---

## Langkah 4 — Berikan Akses ke Juri

Serahkan tautan berikut kepada Dewan Juri:

| Tujuan | Tautan |
|--------|--------|
| Web UI Chatbot | `https://abcd-xxxx.ngrok-free.app/` |
| Swagger API Explorer | `https://abcd-xxxx.ngrok-free.app/docs` |
| Health Check | `https://abcd-xxxx.ngrok-free.app/healthz` |

**Catatan:** Juri mungkin melihat halaman peringatan "You are about to visit..." dari Ngrok. Mereka cukup klik tombol "Visit Site" untuk melanjutkan. Ini adalah fitur keamanan bawaan Ngrok, bukan *error*.

---

## Langkah 5 — Pantau Log Real-Time (Saat Demo)

Kembali ke terminal **pertama** (yang menjalankan `uvicorn`). Saat Juri mengirimkan pertanyaan, Anda dapat memperlihatkan log yang muncul secara *real-time* sebagai bukti:

- **Log PII Redaction** — Menunjukkan bahwa nama/NIK pengguna disensor otomatis
- **Log Triage** — Menunjukkan deteksi kondisi darurat berhasil diidentifikasi
- **Log Guardrail** — Menunjukkan blokir terhadap pertanyaan berbahaya

---

## Troubleshooting Umum

| Masalah | Solusi |
|---------|--------|
| `.venv\Scripts\activate` gagal (SecurityError) | Jalankan `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process` terlebih dahulu di terminal yang sama |
| Port 8000 sudah digunakan | Ganti port: `uvicorn api.main:app --port 8001` dan `ngrok http 8001` |
| Ngrok menampilkan "ERR_NGROK_8012" | Anda sudah menjalankan 1 sesi Ngrok di terminal lain. Tutup terminal itu terlebih dahulu (akun Free Tier hanya boleh 1 sesi aktif bersamaan) |
| API menjawab 500 Internal Server Error | Periksa apakah file `.env` sudah terisi lengkap dengan `ANTHROPIC_API_KEY` yang valid |
