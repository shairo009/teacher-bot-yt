@echo off
REM Teacher Bot YT - Correct Python launcher
REM Use this instead of "python main.py" to avoid venv conflicts

set PYTHON=C:\Users\1001s\AppData\Local\Programs\Python\Python312\python.exe

echo.
echo [Teacher Bot YT] Starting...
echo [Python] %PYTHON%
echo.

%PYTHON% main.py %*
