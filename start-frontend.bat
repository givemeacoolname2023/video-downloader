@echo off
cd /d "%~dp0frontend"
echo Starting Video Downloader Frontend...
echo.
echo Frontend will be available at: http://localhost:5173
echo.
call npm run dev
pause