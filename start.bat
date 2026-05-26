@echo off
echo.
echo  ====================================================
echo    DOKTER PENJAGA — STARTUP LAUNCHER
echo  ====================================================
echo.

echo [1/2] Menjalankan API FastAPI...
start "Dokter Penjaga API" cmd /k "Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process 2>nul & .venv\Scripts\activate && uvicorn api.main:app --host 0.0.0.0 --port 8000"

echo Menunggu API siap (3 detik)...
timeout /t 3 /nobreak >nul

echo [2/2] Menghubungkan Ngrok Tunnel...
echo CATATAN: Ganti "STATIC_DOMAIN_ANDA" di baris di bawah ini dengan domain dari dashboard Ngrok Anda!
echo.
start "Ngrok Tunnel" cmd /k ".\ngrok.exe http --url=STATIC_DOMAIN_ANDA 8000"

echo.
echo  ====================================================
echo    SELESAI! Dua jendela terminal terbuka:
echo    - "Dokter Penjaga API" = Server FastAPI
echo    - "Ngrok Tunnel" = URL Publik untuk Juri
echo.
echo    Lihat URL di jendela "Ngrok Tunnel"!
echo  ====================================================
echo.
pause
