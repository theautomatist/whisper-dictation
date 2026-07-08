@echo off
title Microphone Test
echo Microphone test - recording 6 seconds.
echo Please speak loudly once "SPEAK LOUDLY NOW" appears.
echo.
"%~dp0venv\Scripts\python.exe" "%~dp0mic_test.py"
echo.
pause
