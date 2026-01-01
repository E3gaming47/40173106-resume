@echo off
REM Startup script for Windows

echo Starting Resume Backend API...
echo Installing dependencies...
pip install -r requirements.txt

echo Starting server on http://0.0.0.0:8000
echo API Documentation: http://localhost:8000/docs
python main.py

pause

