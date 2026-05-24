$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

function Test-DirectoryWritable {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        throw "Required path does not exist: $Path"
    }

    $testFile = Join-Path $Path "__codex_write_test.tmp"

    try {
        "probe" | Set-Content -Encoding UTF8 $testFile
        Remove-Item $testFile -Force
        Write-Host "Writable: $Path"
    }
    catch {
        throw "Path is not writable: $Path. Error: $($_.Exception.Message)"
    }
}

Write-Host "==> Project root: $ProjectRoot"

Write-Host "==> Preflight write checks"
Test-DirectoryWritable $ProjectRoot
Test-DirectoryWritable (Join-Path $ProjectRoot "data")
Test-DirectoryWritable (Join-Path $ProjectRoot "digests")
Test-DirectoryWritable (Join-Path $ProjectRoot ".git")

Write-Host "==> Checking git remote"
git remote -v
if ($LASTEXITCODE -ne 0) {
    throw "git remote failed"
}

Write-Host "==> Pulling latest origin/main"
git pull --rebase --autostash origin main
if ($LASTEXITCODE -ne 0) {
    throw "git pull failed. If error mentions .git/FETCH_HEAD Permission denied, fix local .git permissions or Codex sandbox write access."
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
