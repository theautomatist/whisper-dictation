@echo off
title Local Dictation (Whisper large-v3)
echo Starting local dictation... (model loads in ~7 seconds)
echo.
"%~dp0venv\Scripts\python.exe" "%~dp0dictate.py"
echo.
echo Dictation ended.
pause
