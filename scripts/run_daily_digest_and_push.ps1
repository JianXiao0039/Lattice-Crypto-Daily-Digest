$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

Write-Host "==> Project root: $ProjectRoot"

Write-Host "==> Checking git remote"
git remote -v
if ($LASTEXITCODE -ne 0) {
    throw "git remote failed"
}

Write-Host "==> Pulling latest origin/main"
git pull --rebase --autostash origin main
if ($LASTEXITCODE -ne 0) {
    throw "git pull failed. Please check GitHub network/proxy/authentication."
}

Write-Host "==> Generating daily lattice crypto digest"
python -m lattice_digest.run --since 36h --output markdown,json --send none
if ($LASTEXITCODE -ne 0) {
    throw "digest generation failed. Will not commit or push."
}

Write-Host "==> Running tests"
python -m pytest
if ($LASTEXITCODE -ne 0) {
    throw "pytest failed. Will not commit or push."
}

Write-Host "==> Staging generated outputs only"
git add digests data papers.db
if ($LASTEXITCODE -ne 0) {
    throw "git add failed"
}

Write-Host "==> Checking staged changes"
git diff --cached --quiet
$DiffExitCode = $LASTEXITCODE

if ($DiffExitCode -eq 0) {
    Write-Host "no changes to commit"
    exit 0
}

if ($DiffExitCode -ne 1) {
    throw "git diff --cached --quiet failed"
}

$Today = Get-Date -Format "yyyy-MM-dd"
$CommitMessage = "daily lattice digest: $Today"

Write-Host "==> Committing: $CommitMessage"
git commit -m $CommitMessage
if ($LASTEXITCODE -ne 0) {
    throw "git commit failed"
}

Write-Host "==> Pushing to GitHub"
git push origin main
if ($LASTEXITCODE -ne 0) {
    throw "git push failed. Please check GitHub network, Clash proxy, or authentication."
}

Write-Host "pushed daily digest to GitHub"
