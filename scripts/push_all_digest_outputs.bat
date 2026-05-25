@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo Lattice Crypto Daily Digest - Push Local Outputs
echo.

cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
if errorlevel 1 (
  echo Failed to enter project directory.
  pause
  exit /b 1
)

echo Checking GitHub connectivity...
git ls-remote https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git >nul 2>&1
if errorlevel 1 (
  echo GitHub connection failed. Please check Clash / Git proxy / GitHub login status.
  echo You can inspect proxy settings with:
  echo git config --global --get http.proxy
  echo git config --global --get https.proxy
  echo Previously working proxy: http://127.0.0.1:7897
  pause
  exit /b 1
)

for /f "delims=" %%B in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%B"
if /I not "%CURRENT_BRANCH%"=="main" (
  echo Current branch is not main: %CURRENT_BRANCH%
  pause
  exit /b 1
)

echo Checking working tree before pull...
set "STATUS_FILE=%TEMP%\lattice_digest_push_status_%RANDOM%.tmp"
git status --porcelain --untracked-files=all > "%STATUS_FILE%"
if errorlevel 1 (
  echo Failed to inspect git status.
  if exist "%STATUS_FILE%" del "%STATUS_FILE%" >nul 2>&1
  pause
  exit /b 1
)

set "HAS_BLOCKED_CHANGES=0"
for /f "usebackq delims=" %%L in ("%STATUS_FILE%") do (
  set "STATUS_LINE=%%L"
  set "STATUS_PATH=!STATUS_LINE:~3!"
  call :IsAllowedDigestOutput "!STATUS_PATH!"
  if errorlevel 1 (
    echo Non-digest change detected: !STATUS_PATH!
    set "HAS_BLOCKED_CHANGES=1"
  )
)
del "%STATUS_FILE%" >nul 2>&1

if "%HAS_BLOCKED_CHANGES%"=="1" (
  echo Please review non-digest changes manually before using this script.
  pause
  exit /b 1
)

echo Pulling latest origin/main...
git pull --rebase origin main
if errorlevel 1 (
  echo git pull failed. Please resolve the issue manually.
  pause
  exit /b 1
)

echo Staging local digest outputs...
git add digests data papers.db
if errorlevel 1 (
  echo git add failed.
  pause
  exit /b 1
)

git diff --cached --quiet
set "DIFF_EXIT=%ERRORLEVEL%"
if "%DIFF_EXIT%"=="0" (
  echo No local digest outputs to commit.
  pause
  exit /b 0
)
if not "%DIFF_EXIT%"=="1" (
  echo Failed to inspect staged changes.
  pause
  exit /b 1
)

git commit -m "daily lattice digest outputs"
if errorlevel 1 (
  echo git commit failed.
  pause
  exit /b 1
)

git push origin main
if errorlevel 1 (
  echo git push failed. Please check GitHub network, Clash proxy, and authentication status.
  pause
  exit /b 1
)

echo Pushed local digest outputs to GitHub.
pause
exit /b 0

:IsAllowedDigestOutput
set "CHECK_PATH=%~1"
if /I "%CHECK_PATH%"=="papers.db" exit /b 0
if /I "%CHECK_PATH:~0,8%"=="digests/" exit /b 0
if /I "%CHECK_PATH:~0,8%"=="digests\" exit /b 0
if /I "%CHECK_PATH:~0,5%"=="data/" exit /b 0
if /I "%CHECK_PATH:~0,5%"=="data\" exit /b 0
exit /b 1
