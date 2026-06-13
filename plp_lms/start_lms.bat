@echo off
cd /d "C:\Users\drnaf\OneDrive\Desktop\CESUS\Mateen Project\PLP Learning management system\plp_lms"
echo Starting PLP LMS...
start "" http://127.0.0.1:8000
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
