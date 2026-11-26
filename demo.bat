@echo off
REM One-click Introspect demo (Windows). Uses .venv if present.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\start_demo.py %*
) else (
  python scripts\start_demo.py %*
)
if errorlevel 1 pause
