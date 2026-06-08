@echo off
setlocal EnableExtensions

cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
if errorlevel 1 (
  echo Failed to enter project directory.
  exit /b 1
)

if not exist ".pytest_tmp" mkdir ".pytest_tmp"
set "TEMP=%CD%\.pytest_tmp"
set "TMP=%CD%\.pytest_tmp"

python scripts\compare_reliability_baseline.py
