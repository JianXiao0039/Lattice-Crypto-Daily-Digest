$ErrorActionPreference = "Continue"

function Write-Check {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Message = ""
    )
    if ($Message) {
        Write-Host ("[{0}] {1}: {2}" -f $Status, $Name, $Message)
    } else {
        Write-Host ("[{0}] {1}" -f $Status, $Name)
    }
}

function Test-CommandExists {
    param([string]$CommandName)
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

Write-Host "Lattice Crypto Daily Digest - Deployment Check"
Write-Host "当前目录: $(Get-Location)"

$coreFailed = $false
$optionalMissing = $false

$hasProjectFile = (Test-Path -LiteralPath "pyproject.toml") -or (Test-Path -LiteralPath "src\lattice_digest")
if ($hasProjectFile) {
    Write-Check "项目目录" "OK" "找到 pyproject.toml 或 src\lattice_digest。"
} else {
    Write-Check "项目目录" "FAIL" "请先进入项目根目录，例如：Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest'"
    $coreFailed = $true
}

if (Test-CommandExists "python") {
    $pythonVersionText = (& python --version 2>&1) -join " "
    Write-Check "Python" "OK" $pythonVersionText
    $versionMatch = [regex]::Match($pythonVersionText, "Python\s+(\d+)\.(\d+)")
    if ($versionMatch.Success) {
        $major = [int]$versionMatch.Groups[1].Value
        $minor = [int]$versionMatch.Groups[2].Value
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Check "Python 版本" "FAIL" "需要 Python 3.11+。请安装新版 Python 后重试。"
            $coreFailed = $true
        } else {
            Write-Check "Python 版本" "OK" "满足 Python 3.11+。"
        }
    } else {
        Write-Check "Python 版本" "FAIL" "无法解析 Python 版本。"
        $coreFailed = $true
    }
} else {
    Write-Check "Python" "FAIL" "未找到 python。请安装 Python 3.11+ 并加入 PATH。"
    $coreFailed = $true
}

if (Test-CommandExists "python") {
    & python -m pip --version *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Check "pip" "OK" "python -m pip 可用。"
    } else {
        Write-Check "pip" "FAIL" "pip 不可用。可尝试：python -m ensurepip --upgrade"
        $coreFailed = $true
    }
}

if (Test-CommandExists "git") {
    $gitVersion = (& git --version 2>&1) -join " "
    Write-Check "git" "OK" $gitVersion
} else {
    Write-Check "git" "FAIL" "未找到 git。请安装 Git for Windows 并加入 PATH。"
    $coreFailed = $true
}

if (Test-CommandExists "python") {
    & python -c "import lattice_digest" *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Check "import lattice_digest" "OK" "当前 Python 可导入项目包。"
    } else {
        Write-Check "import lattice_digest" "FAIL" "无法导入 lattice_digest。请运行：python -m pip install -e ."
        $coreFailed = $true
    }
}

if (Test-Path -LiteralPath "scripts\run_local_digest_backfill.ps1") {
    Write-Check "本地回填脚本" "OK" "scripts\run_local_digest_backfill.ps1 存在。"
} else {
    Write-Check "本地回填脚本" "FAIL" "缺少 scripts\run_local_digest_backfill.ps1。"
    $coreFailed = $true
}

if (Test-Path -LiteralPath ".github\workflows\daily.yml") {
    Write-Check "GitHub Actions workflow" "OK" ".github\workflows\daily.yml 存在。"
} else {
    Write-Check "GitHub Actions workflow" "FAIL" "缺少 .github\workflows\daily.yml。"
    $coreFailed = $true
}

if ([Environment]::GetEnvironmentVariable("SEMANTIC_SCHOLAR_API_KEY", "Process") -or [Environment]::GetEnvironmentVariable("SEMANTIC_SCHOLAR_API_KEY", "User") -or [Environment]::GetEnvironmentVariable("SEMANTIC_SCHOLAR_API_KEY", "Machine")) {
    Write-Check "SEMANTIC_SCHOLAR_API_KEY" "OK" "已设置；未打印 key 内容。"
} else {
    Write-Check "SEMANTIC_SCHOLAR_API_KEY" "WARN" "未设置。核心运行可继续，但 Semantic Scholar 更容易遇到 rate limit。"
    $optionalMissing = $true
}

if ($coreFailed) {
    Write-Host "核心环境检查失败。请按上方提示修复后重试。"
    exit 1
}

if ($optionalMissing) {
    Write-Host "核心环境通过，但存在可选项缺失。"
    exit 2
}

Write-Host "核心环境通过。"
exit 0
