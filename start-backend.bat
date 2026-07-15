@echo off
cd /d "%~dp0backend"
echo Starting Video Downloader Backend...
echo.
echo Backend will be available at: http://127.0.0.1:8000
echo API docs at: http://127.0.0.1:8000/docs
echo.
python run.py
pause