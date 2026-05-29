param(
    [Parameter(Mandatory = $true)]
    [string]$Plan,
    [string]$OutputDir = "research_artifacts",
    [switch]$DryRun,
    [switch]$Force,
    [string]$TrackOverride,
    [string]$Slug,
    [string]$PlanId
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location -LiteralPath $RepoRoot

$args = @(
    "-m", "lattice_digest.artifact_scaffold",
    "--plan", $Plan,
    "--output-dir", $OutputDir
)

if ($DryRun) {
    $args += "--dry-run"
}
if ($Force) {
    $args += "--force"
}
if ($TrackOverride) {
    $args += @("--track-override", $TrackOverride)
}
if ($Slug) {
    $args += @("--slug", $Slug)
}
if ($PlanId) {
    $args += @("--plan-id", $PlanId)
}

& python @args
if ($LASTEXITCODE -ne 0) {
    Write-Host "Research artifact scaffold generation failed."
    exit $LASTEXITCODE
}
