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

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Name,

        [Parameter(Mandatory=$true)]
        [scriptblock]$Command
    )

    Write-Host "==> $Name"
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

Write-Host "==> Project root: $ProjectRoot"

Write-Host "==> Preflight write checks"
Test-DirectoryWritable $ProjectRoot
Test-DirectoryWritable (Join-Path $ProjectRoot "data")
Test-DirectoryWritable (Join-Path $ProjectRoot "digests")
Test-DirectoryWritable (Join-Path $ProjectRoot ".git")

Invoke-CheckedCommand "Checking git remote" {
    git remote -v
}

Invoke-CheckedCommand "Pulling latest origin/main" {
    git pull --rebase --autostash origin main
}

Invoke-CheckedCommand "Generating daily lattice crypto digest" {
    python -m lattice_digest.run --since 36h --output markdown,json --send none
}

Invoke-CheckedCommand "Running tests" {
    python -m pytest
}

Invoke-CheckedCommand "Staging generated outputs only" {
    git add digests data papers.db
}

Write-Host "==> Checking staged changes"
git diff --cached --quiet
$DiffExitCode = $LASTEXITCODE

if ($DiffExitCode -eq 0) {
    Write-Host "no changes to commit"
    exit 0
}

if ($DiffExitCode -ne 1) {
    throw "git diff --cached --quiet failed with exit code $DiffExitCode"
}

$Today = Get-Date -Format "yyyy-MM-dd"
$CommitMessage = "daily lattice digest: $Today"

Invoke-CheckedCommand "Committing: $CommitMessage" {
    git commit -m $CommitMessage
}

Invoke-CheckedCommand "Pushing to GitHub" {
    git push origin main
}

Write-Host "pushed daily digest to GitHub"
