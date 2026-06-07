@echo off
setlocal EnableExtensions

echo Lattice Crypto Daily Digest - Weekly Handoff
echo Manual-only helper. This script does not commit, push, schedule, or write PhD_Application.
echo.

cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
if errorlevel 1 (
  echo Failed to enter project directory.
  exit /b 1
)

if not exist ".pytest_tmp" mkdir ".pytest_tmp"
set "TEMP=%CD%\.pytest_tmp"
set "TMP=%CD%\.pytest_tmp"

python --version
if errorlevel 1 (
  echo Python version check failed.
  exit /b 1
)

python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"
if errorlevel 1 (
  echo Environment import check failed.
  exit /b 1
)

python -m lattice_digest.weekly_handoff --latest
if errorlevel 1 (
  echo Weekly handoff generation failed.
  exit /b 1
)

echo Weekly handoff generation completed.
exit /b 0
