param(
    [int]$Days,
    [string]$FromDate,
    [string]$ToDate,
    [string]$Format = "all",
    [string]$OutputDir = "exports\library",
    [switch]$DryRun,
    [string[]]$Tag,
    [string[]]$Source,
    [int]$MinPriorityScore = 0,
    [string[]]$PriorityLabel,
    [int]$Limit
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

if ($Days -gt 0) {
    $today = Get-Date
    $from = $today.Date.AddDays(-1 * ($Days - 1))
    $FromDate = $from.ToString("yyyy-MM-dd")
    $ToDate = $today.ToString("yyyy-MM-dd")
}

$pythonArgs = @(
    "-m", "lattice_digest.export_library",
    "--input", "data",
    "--output-dir", $OutputDir,
    "--format", $Format,
    "--min-priority-score", "$MinPriorityScore"
)

if ($FromDate) {
    $pythonArgs += @("--from-date", $FromDate)
}
if ($ToDate) {
    $pythonArgs += @("--to-date", $ToDate)
}
if ($DryRun) {
    $pythonArgs += "--dry-run"
}
if ($Limit -gt 0) {
    $pythonArgs += @("--limit", "$Limit")
}
foreach ($label in ($PriorityLabel | Where-Object { $_ })) {
    $pythonArgs += @("--priority-label", $label)
}
foreach ($tagValue in ($Tag | Where-Object { $_ })) {
    $pythonArgs += @("--tag", $tagValue)
}
foreach ($sourceValue in ($Source | Where-Object { $_ })) {
    $pythonArgs += @("--source", $sourceValue)
}

Write-Host "Lattice Crypto Daily Digest - Library Export"
Write-Host ("Project root: {0}" -f $ProjectRoot)
Write-Host ("Output dir: {0}" -f (Join-Path $ProjectRoot $OutputDir))
Write-Host ("Python command: python {0}" -f ($pythonArgs -join " "))

& python @pythonArgs
exit $LASTEXITCODE
