@echo off
chcp 65001 > nul 2>&1
if exist "%~dp0..\.venv\Scripts\python.exe" (
    "%~dp0..\.venv\Scripts\python.exe" "%~dp0..\metis.py" %*
) else (
    python "%~dp0..\metis.py" %*
)
