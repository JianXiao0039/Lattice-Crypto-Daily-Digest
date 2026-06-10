@echo off
setlocal EnableExtensions

echo Lattice Crypto Daily Digest - Manual Failed Source Recovery
echo Manual-only helper. This script does not commit, push, schedule, or write PhD_Application or ResearchArtifacts.
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
if errorlevel 1 exit /b 1

python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"
if errorlevel 1 (
  echo Environment import check failed.
  exit /b 1
)

python -m lattice_digest.workflow doctor
if errorlevel 1 (
  echo Workflow doctor failed.
  exit /b 1
)

python scripts\probe_source_connectivity.py
if errorlevel 1 (
  echo Source connectivity probe failed.
  exit /b 1
)

python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
if errorlevel 1 (
  echo Manual failed-source recovery run failed.
  exit /b 1
)

scripts\run_weekly_handoff.bat
if errorlevel 1 (
  echo Weekly handoff generation failed.
  exit /b 1
)

echo Manual failed-source recovery completed.
exit /b 0
