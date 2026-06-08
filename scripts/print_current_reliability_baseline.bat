@echo off
setlocal EnableExtensions

cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
if errorlevel 1 (
  echo Failed to enter project directory.
  exit /b 1
)

python scripts\print_current_reliability_baseline.py
exit /b %ERRORLEVEL%
