param(
    [int]$Days,
    [string]$FromDate,
    [string]$ToDate,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location -LiteralPath $RepoRoot

function Stop-WithMessage {
    param([string]$Message)
    Write-Host $Message
    exit 1
}

function Test-AllowedOutputPath {
    param([string]$PathText)
    $normalized = $PathText -replace "\\", "/"
    return (
        $normalized -like "data/*" -or
        $normalized -like "digests/*" -or
        $normalized -eq "papers.db"
    )
}

function Get-ReportQuality {
    param([string]$DateText)
    $jsonPath = Join-Path $RepoRoot "data\$DateText.json"
    if (-not (Test-Path -LiteralPath $jsonPath)) {
        return $null
    }
    try {
        $payload = Get-Content -LiteralPath $jsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
        return $payload.metadata.quality_status
    } catch {
        return $null
    }
}

function Import-ProxyFromEnvFile {
    $envPath = Join-Path $RepoRoot ".env"
    if (-not (Test-Path -LiteralPath $envPath)) {
        return
    }
    foreach ($line in Get-Content -LiteralPath $envPath -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }
        $parts = $trimmed.Split("=", 2)
        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        if (($key -eq "HTTP_PROXY" -or $key -eq "HTTPS_PROXY" -or $key -eq "http_proxy" -or $key -eq "https_proxy") -and $value) {
            if (-not [Environment]::GetEnvironmentVariable($key, "Process")) {
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
    }
}

Write-Host "Lattice Crypto Daily Digest - Local Authoritative Backfill"

$statusLines = git status --porcelain
foreach ($line in $statusLines) {
    if ($line.Length -lt 4) {
        continue
    }
    $pathText = $line.Substring(3).Trim().Trim('"')
    if (-not (Test-AllowedOutputPath $pathText)) {
        Stop-WithMessage "Uncommitted code changes detected at '$pathText'. Please review or commit/stash code changes before backfill."
    }
}

git fetch origin
git checkout main
git pull --rebase origin main

Import-ProxyFromEnvFile

if ($Days -gt 0) {
    $today = (Get-Date).Date
    $start = $today.AddDays(-1 * ($Days - 1))
    $end = $today
} elseif ($FromDate -and $ToDate) {
    $start = [datetime]::ParseExact($FromDate, "yyyy-MM-dd", $null)
    $end = [datetime]::ParseExact($ToDate, "yyyy-MM-dd", $null)
} else {
    Stop-WithMessage "Use either -Days N or -FromDate YYYY-MM-DD -ToDate YYYY-MM-DD."
}

if ($end -lt $start) {
    Stop-WithMessage "ToDate must be greater than or equal to FromDate."
}

$current = $start
while ($current -le $end) {
    $dateText = $current.ToString("yyyy-MM-dd")
    $quality = Get-ReportQuality $dateText
    if (($quality -eq "authoritative" -or $quality -eq "authoritative_backfill") -and -not $Force) {
        Write-Host "Skipping $dateText because existing report is $quality. Use -Force to overwrite."
        $current = $current.AddDays(1)
        continue
    }

    $args = @(
        "-m", "lattice_digest.run",
        "--target-date", $dateText,
        "--since", "7d",
        "--output", "markdown,json",
        "--send", "none",
        "--collector", "local_codex",
        "--quality-status", "authoritative_backfill",
        "--run-mode", "backfill"
    )
    if ($Force) {
        $args += "--force"
    }
    & python @args
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Backfill failed for $dateText."
    }
    $current = $current.AddDays(1)
}

$pytestTmp = Join-Path $RepoRoot ".pytest_tmp"
if (Test-Path -LiteralPath $pytestTmp) {
    Remove-Item -LiteralPath $pytestTmp -Recurse -Force
}

git add -- data/*.json digests/*.md papers.db
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "git add failed."
}

git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "No backfill changes to commit."
    exit 0
}

$commitMessage = "backfill lattice digest: {0}..{1}" -f $start.ToString("yyyy-MM-dd"), $end.ToString("yyyy-MM-dd")
git commit -m $commitMessage
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "git commit failed."
}

git push origin main
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "git push failed. Please check GitHub network, Clash proxy, and authentication status."
}

Write-Host "pushed authoritative backfill to GitHub"
