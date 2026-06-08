@echo off
setlocal EnableExtensions

cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
if errorlevel 1 (
  echo Failed to enter project directory.
  exit /b 1
)

powershell.exe -ExecutionPolicy Bypass -File scripts\daily_reliability_dashboard.ps1
exit /b %ERRORLEVEL%
