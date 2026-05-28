$ErrorActionPreference = "Stop"

$Project = "D:\Code\CodexProjects\lattice-crypto-daily-digest"
Set-Location $Project

$env:HTTP_PROXY = "http://127.0.0.1:7897"
$env:HTTPS_PROXY = "http://127.0.0.1:7897"

$LogDir = Join-Path $Project "logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null

$Time = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$LogFile = Join-Path $LogDir "daily_digest_$Time.log"

Start-Transcript -Path $LogFile -Append

python -m lattice_digest.run --since 7d --output markdown,json --send none
python -m pytest

Stop-Transcript