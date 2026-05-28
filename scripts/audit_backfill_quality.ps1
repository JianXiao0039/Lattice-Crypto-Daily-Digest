param(
    [string]$Date,
    [string]$FromDate,
    [string]$ToDate
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location -LiteralPath $RepoRoot

function Stop-WithMessage {
    param([string]$Message)
    Write-Host $Message
    exit 1
}

if ($Date) {
    $start = [datetime]::ParseExact($Date, "yyyy-MM-dd", $null)
    $end = $start
} elseif ($FromDate -and $ToDate) {
    $start = [datetime]::ParseExact($FromDate, "yyyy-MM-dd", $null)
    $end = [datetime]::ParseExact($ToDate, "yyyy-MM-dd", $null)
} else {
    Stop-WithMessage "Use either -Date YYYY-MM-DD or -FromDate YYYY-MM-DD -ToDate YYYY-MM-DD."
}

if ($end -lt $start) {
    Stop-WithMessage "ToDate must be greater than or equal to FromDate."
}

$current = $start
while ($current -le $end) {
    $dateText = $current.ToString("yyyy-MM-dd")
    & python -m lattice_digest.audit --date $dateText
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Backfill quality audit failed for $dateText."
    }
    $current = $current.AddDays(1)
}

Write-Host "backfill quality audit complete"
