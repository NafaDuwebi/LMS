@echo off
title PLP Learning Management System
cd /d "C:\Users\drnaf\OneDrive\Desktop\CESUS\Mateen Project\PLP Learning management system\plp_lms"
echo Starting PLP LMS...
echo.
echo Open http://127.0.0.1:8000 in your browser after the server starts.
echo.
start "" http://127.0.0.1:8000
python main.py
pause
