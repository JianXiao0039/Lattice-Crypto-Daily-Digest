param(
    [string]$FromDate,
    [string]$ToDate,
    [int]$MinPaperPriority = 50,
    [int]$MinIdeaScore = 0,
    [string]$InputPath = "data",
    [string]$OutputDir = "exports\ideas",
    [string]$ObsidianDir = "exports\obsidian\ideas",
    [string]$Tracks,
    [int]$Limit = 0,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location -LiteralPath $RepoRoot

$args = @(
    "-m", "lattice_digest.ideas",
    "--input", $InputPath,
    "--output-dir", $OutputDir,
    "--obsidian-dir", $ObsidianDir,
    "--min-paper-priority", "$MinPaperPriority",
    "--min-idea-score", "$MinIdeaScore"
)

if ($FromDate) {
    $args += @("--from-date", $FromDate)
}
if ($ToDate) {
    $args += @("--to-date", $ToDate)
}
if ($Tracks) {
    $args += @("--tracks", $Tracks)
}
if ($Limit -gt 0) {
    $args += @("--limit", "$Limit")
}
if ($DryRun) {
    $args += "--dry-run"
}

& python @args
if ($LASTEXITCODE -ne 0) {
    Write-Host "Idea bank generation failed."
    exit $LASTEXITCODE
}
