@echo off
echo ===================================================================
echo     Stopping CryptoTrace Services...
echo ===================================================================

taskkill /f /im uvicorn.exe 2>nul
taskkill /f /im node.exe 2>nul

echo All CryptoTrace services have been stopped.
timeout /t 2 /nobreak >nul
