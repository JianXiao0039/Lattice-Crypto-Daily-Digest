# Public Deployment Guide

## 中文说明

## 1. 适用场景

本项目可以在不依赖 Codex 自动化模块的情况下部署和运行。Codex 只是开发辅助，不是运行依赖。普通 Windows、Linux、WSL、本地 PowerShell、cmd、GitHub Actions 环境都可以运行本项目。

适用场景：

- 本地每日格密码论文情报生成。
- GitHub Actions 云端 provisional 日报。
- 本地 authoritative backfill 权威回填。
- Weekly Research Brief 工作流接入。
- Obsidian 论文卡片或研究笔记工作流接入。
- Idea Bank / Paper Plan / Research Artifact 下游研究流。

推荐日常运行方式：

1. GitHub Actions 每天保底生成 provisional 日报。
2. 本地 Windows PowerShell 定期做高质量 authoritative backfill。
3. 本地按需生成 Idea Bank、Paper Plan 和 Research Artifact scaffold。

## 2. 推荐 API 与数据源配置

### 必需项

- Python 3.11+
- Git
- 网络访问

### 推荐项

- `SEMANTIC_SCHOLAR_API_KEY`：推荐配置，用于提高 Semantic Scholar 稳定性和降低 rate-limit 风险。
- GitHub Actions repository secrets：用于云端运行和邮件发送。
- SMTP secrets：仅在需要邮件发送时配置。

### 可选项

- `CONTACT_EMAIL`：代码会把它传入 source 运行上下文，适合未来更礼貌地访问学术 API。
- `HTTP_PROXY` / `HTTPS_PROXY`：本地 backfill 脚本会从 `.env` 读取这些变量到当前进程，适用于需要代理访问 GitHub 或学术 API 的机器。
- OpenAlex mailto：当前代码没有单独支持 `OPENALEX_MAILTO` 这类环境变量，不列为必需项。未来可作为数据源礼貌访问加固项。

### 数据源说明

- IACR ePrint：格密码论文主源之一。
- arXiv：预印本补充源。
- DBLP：出版元数据补充源。
- Crossref：DOI 与出版信息补充源。
- OpenAlex：开放学术元数据补充源。
- Semantic Scholar：推荐配置 API key，用于提高稳定性和支持质量。

## 3. Windows 本地部署

### PowerShell

在 Windows PowerShell 中运行：

```powershell
Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest'
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest tests --basetemp=.pytest_tmp
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

### cmd

在 Windows cmd 中运行：

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
python --version
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest tests --basetemp=.pytest_tmp
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

PowerShell 使用 `Set-Location`，cmd 使用 `cd /d`。不要把 PowerShell 命令直接粘到 cmd 中。

## 4. Linux / WSL 部署

在 Linux、WSL 或 Git Bash 类 bash 环境中运行：

```bash
cd /path/to/lattice-crypto-daily-digest
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest tests --basetemp=.pytest_tmp
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

## 5. GitHub Actions 部署

fork 或 clone 项目后，在 GitHub 仓库的 Actions 页面启用 workflow。`.github/workflows/daily.yml` 会：

- 每天运行一次，也支持手动 `Run workflow`。
- 运行测试。
- 生成 `collector=github_actions`、`quality_status=provisional` 的日报。
- 验证 Markdown、JSON 和 `papers.db`。
- 只提交 `digests/*.md`、`data/*.json` 和 `papers.db`。
- SMTP secrets 完整时发送邮件；不完整时跳过邮件且不失败。

GitHub Actions 生成的是 provisional 日报。本地回填生成 `authoritative_backfill`，可在更好的本地网络环境下覆盖 provisional。

当前 workflow 真实使用的 repository secrets：

- `CONTACT_EMAIL`
- `SEMANTIC_SCHOLAR_API_KEY`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `DIGEST_EMAIL_FROM`
- `DIGEST_EMAIL_TO`

`SMTP_USER` 是本地邮件脚本支持的 legacy alias，但当前 GitHub Actions workflow 使用 `SMTP_USERNAME`。`SMTP_FROM` / `SMTP_TO` 当前未使用；请使用 `DIGEST_EMAIL_FROM` / `DIGEST_EMAIL_TO`。

不建议把本地随手生成的 `data/`、`digests/`、`papers.db` 混入功能 commit。正式日报产物应由 GitHub Actions 或明确的发布流程提交。

## 6. 本地权威回填

最近 5 天：

```powershell
Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest'
powershell.exe -ExecutionPolicy Bypass -File scripts\run_local_digest_backfill.ps1 -Days 5
```

指定日期范围：

```powershell
Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest'
powershell.exe -ExecutionPolicy Bypass -File scripts\run_local_digest_backfill.ps1 -FromDate 2026-05-25 -ToDate 2026-05-29
```

本地 backfill 通常比 GitHub Actions 更完整，因为它可以使用你的本地网络、代理、缓存和手动重试环境。GitHub Actions 的 runner 网络可能遇到 arXiv、OpenAlex、Semantic Scholar 的 rate limit、timeout 或 SSL warning。

使用 `-Force` / `--force` 的场景：

- 你确认已有报告虽然是 authoritative，但需要重新生成。
- 你已经备份或确认可以覆盖当前 target date 的报告。
- 你理解覆盖可能改变 `data/YYYY-MM-DD.json`、`digests/YYYY-MM-DD.md` 和 `papers.db`。

回填后审计单日差异：

```powershell
Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest'
powershell.exe -ExecutionPolicy Bypass -File scripts\audit_backfill_quality.ps1 -Date 2026-05-29
```

审计日期范围：

```powershell
Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest'
powershell.exe -ExecutionPolicy Bypass -File scripts\audit_backfill_quality.ps1 -FromDate 2026-05-25 -ToDate 2026-05-29
```

## 7. 周报、Obsidian、Idea Bank、Paper Plan

当前公开分支已提供以下命令：

### Idea Bank

```powershell
Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest'
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_idea_bank.ps1 -DryRun
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_idea_bank.ps1
```

### Paper Plan

```powershell
Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest'
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_paper_plans.ps1 -DryRun
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_paper_plans.ps1 -Top 5
```

### Research Artifact scaffold

```powershell
Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest'
powershell.exe -ExecutionPolicy Bypass -File scripts\create_research_artifact.ps1 -Plan exports\paper_plans\example.json -DryRun
```

### Weekly Research Brief

当前公开分支未检测到独立的 `lattice_digest.weekly` 模块或 `scripts\generate_weekly_brief.ps1` 脚本，因此不在本文档中编造周报命令。若后续分支加入该模块，应在这里补充实际命令和测试。

### Obsidian paper cards

当前公开分支已支持 Idea Bank 和 Paper Plan 的 Obsidian Markdown 输出。未检测到独立的单篇 paper card 导出模块或脚本，因此不编造命令。若后续加入 `lattice_digest.obsidian` 或相应脚本，应在这里补充真实入口。

## 8. 常见故障排查

### Set-Location is not recognized

原因：在 cmd 中运行了 PowerShell 命令。

解决：cmd 使用：

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
```

PowerShell 使用：

```powershell
Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest'
```

### GitHub push rejected: fetch first

原因：远端有新提交。

解决：

```powershell
git fetch origin
git pull --rebase origin main
```

rebase 前先确认未跟踪产物没有和远端文件冲突。

### untracked files would be overwritten by checkout

原因：本地生成物与远端生成物同名。

解决：先移动、删除或备份本地 `data/`、`digests/`、`exports/` 等产物，再执行 checkout 或 rebase。

### Semantic Scholar 429

原因：rate limit。

解决：配置 `SEMANTIC_SCHOLAR_API_KEY`，降低请求频率，稍后重试，或使用本地 backfill。

### arXiv timeout / URL error

原因：网络或频率问题。

解决：等待、重试、缩短 since 窗口，或稍后用 backfill 补齐。

### OpenAlex 付费 sort 报错

当前项目不应再使用 `sort=updated_date:desc`。如果仍出现 plan upgrade 或付费 sort 报错，说明代码回退或远端版本不一致，应检查 `src/lattice_digest/sources/openalex.py`。

### pytest 产生 .pytest_tmp/

这是测试临时目录，不要提交。清理命令：

```cmd
rmdir /s /q .pytest_tmp
```

PowerShell 也可以运行：

```powershell
Remove-Item -LiteralPath .pytest_tmp -Recurse -Force
```

### LF will be replaced by CRLF

这是 Windows 换行警告，通常不影响运行。不要为了这个 warning 随意大规模格式化全仓库。

## 9. 安全注意事项

- 不要提交 `.env`。
- 不要提交真实 API key。
- 不要在 README、issue、日志、截图中暴露密钥。
- GitHub Actions secrets 要在仓库 Settings 中配置。
- 本地 `.env` 只留在本机。
- SMTP 密码建议使用应用专用密码，不要使用主账号密码。
- `papers.db`、`data/`、`digests/` 是生成物，是否提交要有策略，不要混进功能 commit。

## 10. 维护者工作流

功能开发：

```powershell
git checkout -b feature/xxx
# 修改代码
python -m pytest tests --basetemp=.pytest_tmp
git diff --check
git add README.md docs tests scripts .env.example
git commit -m "..."
git fetch origin
git rebase origin/main
git push origin feature/xxx
```

日报生成：

- GitHub Actions 自动保底生成 provisional 日报。
- 本地 Windows PowerShell 定期运行 backfill。
- 重要回填产物单独 commit，不要混入功能开发 commit。

## English Version

## 1. When to Use This Guide

This project can be deployed and operated without Codex automation. Codex is a development helper, not a runtime dependency.

Typical use cases:

- Local daily lattice-cryptography paper intelligence.
- GitHub Actions provisional daily reports.
- Local authoritative backfill.
- Weekly Research Brief workflow integration.
- Obsidian paper-card or research-note workflow integration.
- Idea Bank, Paper Plan, and Research Artifact downstream workflows.

Recommended setup: let GitHub Actions generate fallback provisional reports, then use local Windows PowerShell for higher-quality authoritative backfill.

## 2. API and Source Configuration

Required:

- Python 3.11+
- Git
- Network access

Recommended:

- `SEMANTIC_SCHOLAR_API_KEY`
- GitHub Actions repository secrets
- SMTP secrets if email delivery is needed

Optional:

- `CONTACT_EMAIL`
- `HTTP_PROXY` / `HTTPS_PROXY` for local backfill scripts
- OpenAlex mailto is not currently exposed as a dedicated environment variable.

Supported or reserved sources include IACR ePrint, arXiv, DBLP, Crossref, OpenAlex, and Semantic Scholar.

## 3. Windows Local Deployment

PowerShell:

```powershell
Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest'
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest tests --basetemp=.pytest_tmp
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

cmd:

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
python --version
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest tests --basetemp=.pytest_tmp
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

Use `Set-Location` in PowerShell and `cd /d` in cmd.

## 4. Linux / WSL Deployment

```bash
cd /path/to/lattice-crypto-daily-digest
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest tests --basetemp=.pytest_tmp
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

## 5. GitHub Actions Deployment

Enable Actions after forking or cloning the repository. GitHub Actions generates provisional reports. Local backfill generates authoritative reports and can replace provisional reports when appropriate.

Current workflow secrets:

- `CONTACT_EMAIL`
- `SEMANTIC_SCHOLAR_API_KEY`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `DIGEST_EMAIL_FROM`
- `DIGEST_EMAIL_TO`

`SMTP_USER` is a legacy local alias. `SMTP_FROM` and `SMTP_TO` are not used by the current workflow.

## 6. Local Authoritative Backfill

Last 5 days:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\run_local_digest_backfill.ps1 -Days 5
```

Specific range:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\run_local_digest_backfill.ps1 -FromDate 2026-05-25 -ToDate 2026-05-29
```

Use `-Force` only when you intentionally want to overwrite an existing authoritative report.

## 7. Weekly, Obsidian, Idea Bank, and Paper Plan

Implemented commands in this branch:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_idea_bank.ps1 -DryRun
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_paper_plans.ps1 -DryRun
powershell.exe -ExecutionPolicy Bypass -File scripts\create_research_artifact.ps1 -Plan exports\paper_plans\example.json -DryRun
```

This branch does not expose standalone Weekly Research Brief or individual Obsidian paper-card commands. Future branches should document the actual entry points when they are added.

## 8. Troubleshooting

- `Set-Location is not recognized`: you ran PowerShell syntax in cmd. Use `cd /d` in cmd.
- `GitHub push rejected: fetch first`: run `git fetch origin` and `git pull --rebase origin main`.
- `untracked files would be overwritten by checkout`: move, remove, or back up local generated outputs before checkout or rebase.
- `Semantic Scholar 429`: configure `SEMANTIC_SCHOLAR_API_KEY`, reduce frequency, or retry later.
- `arXiv timeout / URL error`: retry later, use a shorter window, or run backfill.
- OpenAlex paid sort errors: the project should not use `sort=updated_date:desc`; check for version mismatch if it appears.
- `.pytest_tmp/`: temporary pytest output; do not commit it.
- `LF will be replaced by CRLF`: usually harmless on Windows; do not reformat the whole repository just for this warning.

## 9. Security Notes

- Do not commit `.env`.
- Do not commit real API keys.
- Do not expose secrets in README, issues, logs, or screenshots.
- Configure GitHub Actions secrets in repository Settings.
- Keep local `.env` on the local machine.
- Use an app password for SMTP, not the primary account password.
- Treat `papers.db`, `data/`, and `digests/` as generated artifacts with an explicit commit policy.

## 10. Maintainer Workflow

Feature development:

```powershell
git checkout -b feature/xxx
python -m pytest tests --basetemp=.pytest_tmp
git diff --check
git add README.md docs tests scripts .env.example
git commit -m "..."
git fetch origin
git rebase origin/main
git push origin feature/xxx
```

Digest operations:

- GitHub Actions provides provisional daily reports.
- Local Windows PowerShell performs authoritative backfill.
- Commit important backfill outputs separately from feature commits.
