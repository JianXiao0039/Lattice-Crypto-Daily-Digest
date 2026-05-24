@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0run_daily_digest_and_push.ps1"
exit /b %ERRORLEVEL%
