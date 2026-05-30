param(
    [Alias("Input")]
    [string]$InputPath = "exports\library\library-items.json",
    [int]$Days,
    [string]$FromDate,
    [string]$ToDate,
    [string]$OutputDir = "audits\library-export",
    [switch]$DryRun,
    [string[]]$Tag,
    [string[]]$Source,
    [int]$MinPriorityScore = 0
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

$resolvedInput = $InputPath
if (-not (Test-Path $resolvedInput)) {
    if ($Days -gt 0 -or $FromDate -or $ToDate) {
        $resolvedInput = "data"
    } else {
        throw "Input does not exist: $InputPath. Pass -Days or -FromDate/-ToDate to audit data/*.json directly."
    }
}

if ($Days -gt 0) {
    $today = Get-Date
    $from = $today.Date.AddDays(-1 * ($Days - 1))
    $FromDate = $from.ToString("yyyy-MM-dd")
    $ToDate = $today.ToString("yyyy-MM-dd")
}

$pythonArgs = @(
    "-m", "lattice_digest.audit_library_export",
    "--input", $resolvedInput,
    "--output-dir", $OutputDir,
    "--format", "all",
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
foreach ($tagValue in ($Tag | Where-Object { $_ })) {
    $pythonArgs += @("--tag", $tagValue)
}
foreach ($sourceValue in ($Source | Where-Object { $_ })) {
    $pythonArgs += @("--source", $sourceValue)
}

Write-Host "Lattice Crypto Daily Digest - Library Export Audit"
Write-Host ("Project root: {0}" -f $ProjectRoot)
Write-Host ("Input: {0}" -f $resolvedInput)
Write-Host ("Output dir: {0}" -f (Join-Path $ProjectRoot $OutputDir))
Write-Host ("Python command: python {0}" -f ($pythonArgs -join " "))

& python @pythonArgs
exit $LASTEXITCODE
