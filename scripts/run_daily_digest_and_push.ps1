$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $ProjectRoot

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command,
        [string]$FailureHint = ""
    )

    Write-Host "==> $Description"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        if ($FailureHint) {
            Write-Host $FailureHint
        }
        throw "$Description failed with exit code $LASTEXITCODE"
    }
}

Invoke-Checked "git remote -v" {
    git remote -v
}

Invoke-Checked "git pull --rebase --autostash origin main" {
    git pull --rebase --autostash origin main
}

Invoke-Checked "generate daily lattice digest" {
    python -m lattice_digest.run --since 36h --output markdown,json --send none
}

Invoke-Checked "run pytest" {
    python -m pytest
}

Invoke-Checked "stage digest artifacts" {
    git add digests data papers.db
}

git diff --cached --quiet
$DiffExitCode = $LASTEXITCODE
if ($DiffExitCode -eq 0) {
    Write-Host "no changes to commit"
    exit 0
}
if ($DiffExitCode -ne 1) {
    throw "git diff --cached --quiet failed with exit code $DiffExitCode"
}

$DigestDate = Get-Date -Format "yyyy-MM-dd"
$CommitMessage = "daily lattice digest: $DigestDate"

Invoke-Checked "git commit" {
    git commit -m $CommitMessage
}

try {
    Invoke-Checked "git push origin main" {
        git push origin main
    }
}
catch {
    Write-Host "git push failed. Please check GitHub network, Clash proxy, and authentication status."
    Write-Host "Try: git ls-remote https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git"
    Write-Host "Then retry: git push"
    throw
}

Write-Host "pushed daily digest to GitHub"
