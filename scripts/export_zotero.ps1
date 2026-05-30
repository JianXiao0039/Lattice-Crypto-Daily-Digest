param(
    [int]$Days,
    [string]$FromDate,
    [string]$ToDate,
    [string]$InputDir = "data",
    [string]$OutputDir = "exports\zotero",
    [string]$Formats = "all",
    [int]$MinPriorityScore = 0,
    [switch]$IncludeProvisional,
    [switch]$DryRun,
    [switch]$FailOnEmpty
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

$pythonArgs = @(
    "-m", "lattice_digest.zotero_compat",
    "--input-dir", $InputDir,
    "--output-dir", $OutputDir,
    "--formats", $Formats,
    "--min-priority-score", "$MinPriorityScore"
)

if ($Days -gt 0) {
    $pythonArgs += @("--days", "$Days")
}
if ($FromDate) {
    $pythonArgs += @("--from-date", $FromDate)
}
if ($ToDate) {
    $pythonArgs += @("--to-date", $ToDate)
}
if ($IncludeProvisional) {
    $pythonArgs += "--include-provisional"
}
if ($DryRun) {
    $pythonArgs += "--dry-run"
}
if ($FailOnEmpty) {
    $pythonArgs += "--fail-on-empty"
}

Write-Host "Lattice Crypto Daily Digest - Zotero Compatibility Export"
Write-Host ("Project root: {0}" -f $ProjectRoot)
Write-Host ("Input dir: {0}" -f (Join-Path $ProjectRoot $InputDir))
Write-Host ("Output dir: {0}" -f (Join-Path $ProjectRoot $OutputDir))
Write-Host ("Python command: python {0}" -f ($pythonArgs -join " "))

& python @pythonArgs
exit $LASTEXITCODE
