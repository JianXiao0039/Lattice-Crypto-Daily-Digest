@echo off
setlocal EnableExtensions

echo Lattice Crypto Daily Digest - Project Tests
echo This helper is manual-only and does not commit, push, or schedule anything.
echo.

cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
if errorlevel 1 (
  echo Failed to enter project directory.
  pause
  exit /b 1
)

if not exist ".pytest_tmp" mkdir ".pytest_tmp"
set "TEMP=%CD%\.pytest_tmp"
set "TMP=%CD%\.pytest_tmp"

python -m pytest tests --basetemp=.pytest_tmp
if errorlevel 1 (
  echo Project tests failed.
  pause
  exit /b 1
)

echo Project tests passed.
pause
exit /b 0
