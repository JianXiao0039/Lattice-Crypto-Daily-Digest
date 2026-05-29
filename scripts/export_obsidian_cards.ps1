param(
    [string]$Date,
    [int]$MinPriority = 70,
    [string]$OutputDir = "exports\obsidian\papers",
    [string]$Labels,
    [int]$Limit = 0,
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location -LiteralPath $RepoRoot

if (-not $Date) {
    $Date = (Get-Date).ToString("yyyy-MM-dd")
}

$InputJson = Join-Path $RepoRoot "data\$Date.json"
if (-not (Test-Path -LiteralPath $InputJson)) {
    Write-Host "Digest JSON not found: $InputJson"
    exit 1
}

$args = @(
    "-m", "lattice_digest.obsidian",
    "--input", $InputJson,
    "--output-dir", $OutputDir,
    "--min-priority", "$MinPriority"
)

if ($Labels) {
    $args += @("--labels", $Labels)
}
if ($Limit -gt 0) {
    $args += @("--limit", "$Limit")
}
if ($Force) {
    $args += "--force"
}
if ($DryRun) {
    $args += "--dry-run"
}

& python @args
if ($LASTEXITCODE -ne 0) {
    Write-Host "Obsidian card export failed."
    exit $LASTEXITCODE
}
