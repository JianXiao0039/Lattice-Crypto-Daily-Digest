@echo off
setlocal
cd /d "%~dp0.."
python scripts\audit_seven_day_source_reliability.py
exit /b %errorlevel%
