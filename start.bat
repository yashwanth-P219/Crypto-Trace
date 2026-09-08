@echo off
title CryptoTrace Forensic Defense Suite Launcher
color 0A

echo ===================================================================
echo     CryptoTrace - Blockchain Fraud Analytics & Attribution
echo ===================================================================
echo.

if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in backend\venv!
    pause
    exit /b 1
)

echo [1/3] Launching FastAPI Backend (Connected to Supabase)...
start "CryptoTrace Backend (Port 8000)" cmd /k "cd backend && venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/3] Waiting for Backend to be ready...
timeout /t 4 /nobreak >nul

echo [3/3] Launching React Vite Frontend (Port 5173)...
start "CryptoTrace Frontend (Port 5173)" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ===================================================================
echo   SYSTEM IS READY!
echo   Frontend: http://localhost:5173
echo   API Docs: http://127.0.0.1:8000/docs
echo ===================================================================
echo.

start http://localhost:5173
