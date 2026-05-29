param(
    [string]$IdeaBank = "exports\ideas\idea-bank.json",
    [string]$OutputDir = "exports\paper_plans",
    [string]$ObsidianDir = "exports\obsidian\paper_plans",
    [int]$Top = 5,
    [int]$MinIdeaScore = 70,
    [string[]]$Tracks,
    [string[]]$Maturity,
    [int]$Limit = 0,
    [string]$SingleIdeaId,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location -LiteralPath $RepoRoot

$args = @(
    "-m", "lattice_digest.paper_plans",
    "--idea-bank", $IdeaBank,
    "--output-dir", $OutputDir,
    "--obsidian-dir", $ObsidianDir,
    "--top", "$Top",
    "--min-idea-score", "$MinIdeaScore"
)

if ($Tracks -and $Tracks.Count -gt 0) {
    $args += @("--tracks", ($Tracks -join ","))
}
if ($Maturity -and $Maturity.Count -gt 0) {
    $args += @("--maturity", ($Maturity -join ","))
}
if ($Limit -gt 0) {
    $args += @("--limit", "$Limit")
}
if ($SingleIdeaId) {
    $args += @("--single-idea-id", $SingleIdeaId)
}
if ($DryRun) {
    $args += "--dry-run"
}
if ($Force) {
    $args += "--force"
}

& python @args
if ($LASTEXITCODE -ne 0) {
    Write-Host "Paper plan generation failed."
    exit $LASTEXITCODE
}
