$ErrorActionPreference = "Stop"

$ProjectRoot = "D:\Code\CodexProjects\lattice-crypto-daily-digest"
Set-Location $ProjectRoot

Write-Host "Lattice Crypto Daily Digest - Daily Quality Probe"
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

python scripts\probe_source_connectivity.py
if ($LASTEXITCODE -ne 0) {
    throw "Source connectivity probe failed."
}

@'
import json
from pathlib import Path

data_dir = Path("data")
paths = sorted(data_dir.glob("*.json"))
if not paths:
    print("No daily JSON artifacts found.")
    raise SystemExit(0)
latest = paths[-1]
payload = json.loads(latest.read_text(encoding="utf-8"))
records = payload.get("records") or []
source_health = payload.get("source_health") or []
red_count = sum(1 for item in source_health if (item.get("health_status") or item.get("status")) == "red")
retryable_error_count = sum(1 for item in source_health if item.get("retryable"))
all_red = bool(source_health) and red_count == len(source_health)
print(f"latest_daily_json={latest}")
print(f"digest_record_count={len(records)}")
print(f"source_red_count={red_count}")
print(f"retryable_error_count={retryable_error_count}")
print(f"source_starved={len(records) == 0 and all_red}")
'@ | python -
if ($LASTEXITCODE -ne 0) {
    throw "Daily quality summary failed."
}

git status -sb
if ($LASTEXITCODE -ne 0) {
    throw "git status failed."
}

Write-Host "Daily quality probe completed."
