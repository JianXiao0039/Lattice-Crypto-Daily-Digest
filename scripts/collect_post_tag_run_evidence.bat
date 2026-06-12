@echo off
setlocal
cd /d "%~dp0.."
python scripts\collect_post_tag_run_evidence.py
exit /b %errorlevel%
