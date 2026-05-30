param(
    [int]$Days = 7,
    [string]$FromDate,
    [string]$ToDate,
    [string]$InputDir = "data",
    [string]$OutputDir = "exports\zotero",
    [int]$MinPriorityScore = 0,
    [switch]$IncludeProvisional,
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
    "--formats", "zotero-json,csl-json,bibtex,ris,collections,report",
    "--min-priority-score", "$MinPriorityScore",
    "--dry-run"
)

if ($FromDate) {
    $pythonArgs += @("--from-date", $FromDate)
} elseif ($ToDate) {
    $pythonArgs += @("--to-date", $ToDate)
} elseif ($Days -gt 0) {
    $pythonArgs += @("--days", "$Days")
}

if ($FromDate -and $ToDate) {
    $pythonArgs += @("--to-date", $ToDate)
}
if ($IncludeProvisional) {
    $pythonArgs += "--include-provisional"
}
if ($FailOnEmpty) {
    $pythonArgs += "--fail-on-empty"
}

Write-Host "Lattice Crypto Daily Digest - Zotero Manual Import QA"
Write-Host ("Project root: {0}" -f $ProjectRoot)
Write-Host "QA mode: dry-run only; no files are written."
Write-Host "Formats checked: Zotero JSON, CSL-JSON, BibTeX, RIS, collections, report"
Write-Host ("Python command: python {0}" -f ($pythonArgs -join " "))

& python @pythonArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Manual import QA checklist:"
Write-Host "- If records > 0, run scripts\export_zotero.ps1 without -DryRun to generate files."
Write-Host "- Prefer CSL-JSON first, then BibTeX, then RIS."
Write-Host "- In Zotero, verify title/authors/year/url/abstract/tags/notes after import."
Write-Host "- Confirm LC/* tags are useful and not too noisy."
exit 0
