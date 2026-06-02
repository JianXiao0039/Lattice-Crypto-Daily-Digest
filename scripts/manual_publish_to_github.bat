@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo Lattice Crypto Daily Digest - Manual GitHub Publish
echo This helper requires manual execution.
echo It does not install any scheduled task.
echo It does not run in the background.
echo It never force pushes.
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

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo This directory is not a git repository.
  pause
  exit /b 1
)

for /f "delims=" %%B in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%B"
echo Current branch: %CURRENT_BRANCH%
if /I not "%CURRENT_BRANCH%"=="main" (
  echo Current branch is not main. Stop before publishing.
  pause
  exit /b 1
)

echo Fetching origin...
git fetch origin
if errorlevel 1 (
  echo git fetch failed.
  pause
  exit /b 1
)

echo Pulling latest origin/main with rebase...
git pull --rebase origin main
if errorlevel 1 (
  echo git pull --rebase failed. Resolve conflicts manually before publishing.
  pause
  exit /b 1
)

echo Running tests...
python -m pytest tests --basetemp=.pytest_tmp
if errorlevel 1 (
  echo pytest failed. Stop before commit.
  pause
  exit /b 1
)

echo Running release hygiene...
python scripts/check_release_hygiene.py
if errorlevel 1 (
  echo release hygiene failed. Stop before commit.
  pause
  exit /b 1
)

echo Checking whitespace...
git diff --check
if errorlevel 1 (
  echo git diff --check failed. Stop before commit.
  pause
  exit /b 1
)

echo Current git status:
git status -sb
if errorlevel 1 (
  echo git status failed.
  pause
  exit /b 1
)

echo Checking staged files...
set "STAGED_FILE=%TEMP%\lattice_digest_staged_%RANDOM%.tmp"
git diff --cached --name-only > "%STAGED_FILE%"
if errorlevel 1 (
  echo Failed to inspect staged files.
  if exist "%STAGED_FILE%" del "%STAGED_FILE%" >nul 2>&1
  pause
  exit /b 1
)

for %%A in ("%STAGED_FILE%") do if %%~zA==0 (
  echo No staged files found. Stage exact reviewed files manually, then rerun this helper.
  del "%STAGED_FILE%" >nul 2>&1
  pause
  exit /b 1
)

set "HAS_FORBIDDEN=0"
for /f "usebackq delims=" %%P in ("%STAGED_FILE%") do (
  call :IsForbiddenArtifact "%%P"
  if not errorlevel 1 (
    echo Forbidden staged artifact: %%P
    set "HAS_FORBIDDEN=1"
  )
)
del "%STAGED_FILE%" >nul 2>&1

if "%HAS_FORBIDDEN%"=="1" (
  echo Remove forbidden staged artifacts before publishing.
  pause
  exit /b 1
)

set "COMMIT_MESSAGE="
set /p COMMIT_MESSAGE=Enter commit message: 
if "%COMMIT_MESSAGE%"=="" (
  echo Empty commit message is not allowed.
  pause
  exit /b 1
)

git commit -m "%COMMIT_MESSAGE%"
if errorlevel 1 (
  echo git commit failed.
  pause
  exit /b 1
)

git push origin main
if errorlevel 1 (
  echo git push failed. Do not force push; inspect the error and retry manually.
  pause
  exit /b 1
)

echo Manual publish complete. GitHub Actions remains the validation gate.
pause
exit /b 0

:IsForbiddenArtifact
set "CHECK_PATH=%~1"
if /I "%CHECK_PATH%"==".env" exit /b 0
if /I "%CHECK_PATH%"=="papers.db" exit /b 0
if /I "%CHECK_PATH%"=="state/reading-queue.json" exit /b 0
if /I "%CHECK_PATH%"=="state\reading-queue.json" exit /b 0
if /I "%CHECK_PATH:~0,8%"=="exports/" exit /b 0
if /I "%CHECK_PATH:~0,8%"=="exports\" exit /b 0
if /I "%CHECK_PATH:~0,7%"=="audits/" exit /b 0
if /I "%CHECK_PATH:~0,7%"=="audits\" exit /b 0
if /I "%CHECK_PATH:~0,12%"==".pytest_tmp/" exit /b 0
if /I "%CHECK_PATH:~0,12%"==".pytest_tmp\" exit /b 0
if /I "%CHECK_PATH:~0,12%"=="__pycache__/" exit /b 0
if /I "%CHECK_PATH:~0,12%"=="__pycache__\" exit /b 0
if /I "%CHECK_PATH:~0,5%"=="data/" exit /b 0
if /I "%CHECK_PATH:~0,5%"=="data\" exit /b 0
if /I "%CHECK_PATH:~0,8%"=="digests/" exit /b 0
if /I "%CHECK_PATH:~0,8%"=="digests\" exit /b 0
exit /b 1
