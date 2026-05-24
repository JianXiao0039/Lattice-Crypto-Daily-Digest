$ErrorActionPreference = "Stop"

$Root = "D:\Code\CodexProjects\lattice-crypto-daily-digest"
$LogDir = Join-Path $Root ".tmp"
$LogFile = Join-Path $LogDir "git_auto_push_watcher.log"
$LockFile = Join-Path $LogDir "git_auto_push.lock"

New-Item -ItemType Directory -Force $LogDir | Out-Null

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $Message"
    Write-Host $line
    Add-Content -Encoding UTF8 -Path $LogFile -Value $line
}

function Invoke-Git {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Step,

        [Parameter(Mandatory=$true)]
        [scriptblock]$Command
    )

    Write-Log "==> $Step"
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE"
    }
}

function Push-DigestChanges {
    Set-Location $Root

    if (Test-Path $LockFile) {
        Write-Log "Lock file exists; skip this round."
        return
    }

    New-Item -ItemType File -Force $LockFile | Out-Null

    try {
        $status = git status --porcelain -- digests data papers.db

        if ([string]::IsNullOrWhiteSpace($status)) {
            Write-Log "No digest/data/papers.db changes."
            return
        }

        Write-Log "Detected changes:"
        Write-Log $status

        Start-Sleep -Seconds 10

        Invoke-Git "git pull --rebase --autostash origin main" {
            git pull --rebase --autostash origin main
        }

        Invoke-Git "git add digests data papers.db" {
            git add digests data papers.db
        }

        git diff --cached --quiet
        $diffExit = $LASTEXITCODE

        if ($diffExit -eq 0) {
            Write-Log "No staged changes after git add."
            return
        }

        if ($diffExit -ne 1) {
            throw "git diff --cached --quiet failed with exit code $diffExit"
        }

        $today = Get-Date -Format "yyyy-MM-dd"
        $commitMessage = "daily lattice digest: $today"

        Invoke-Git "git commit" {
            git commit -m $commitMessage
        }

        Invoke-Git "git push origin main" {
            git push origin main
        }

        Write-Log "Successfully pushed digest changes to GitHub."
    }
    catch {
        Write-Log "ERROR: $($_.Exception.Message)"
    }
    finally {
        Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Log "Lattice digest Git auto-push watcher started."
Write-Log "Watching: digests/, data/, papers.db"
Write-Log "Project: $Root"

while ($true) {
    Push-DigestChanges
    Start-Sleep -Seconds 60
}
