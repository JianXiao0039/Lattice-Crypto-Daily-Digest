$ErrorActionPreference = "Stop"

$ProjectRoot = "D:\Code\CodexProjects\lattice-crypto-daily-digest"
Set-Location $ProjectRoot

Write-Host "Lattice Crypto Daily Digest - Daily Reliability Dashboard"
Write-Host "Manual-only helper. This script does not commit, push, schedule, or write PhD_Application or ResearchArtifacts."

$PytestTmp = Join-Path $ProjectRoot ".pytest_tmp"
New-Item -ItemType Directory -Force $PytestTmp | Out-Null
$env:TEMP = $PytestTmp
$env:TMP = $PytestTmp

python --version
if ($LASTEXITCODE -ne 0) {
    throw "Python version check failed."
}

python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"
if ($LASTEXITCODE -ne 0) {
    throw "Environment import check failed."
}

python -m lattice_digest.workflow doctor
if ($LASTEXITCODE -ne 0) {
    throw "Workflow doctor failed."
}

python scripts\daily_reliability_dashboard.py
if ($LASTEXITCODE -ne 0) {
    throw "Reliability dashboard generation failed."
}

git status -sb
if ($LASTEXITCODE -ne 0) {
    throw "git status failed."
}

Write-Host "Daily reliability dashboard completed."
