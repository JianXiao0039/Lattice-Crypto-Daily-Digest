# Lattice Crypto Daily Digest

- [中文说明](#中文说明)
- [Safe manual quickstart](#safe-manual-quickstart)
- [Documentation map](#documentation-map)
- [English Version](#english-version)

## 中文说明

## 项目简介

`lattice-crypto-daily-digest` 是一个面向格密码、后量子密码和 AI-assisted lattice cryptanalysis 的科研情报自动化项目。它不是泛泛的 paper digest toy project，而是围绕格密码研究主线搭建的每日论文雷达：从多个学术数据源抓取候选论文，经过去重、硬负例过滤、相关性打分、研究优先级排序和 source health 诊断，生成中文 Markdown 日报、JSON 结构化数据和本地研究规划产物。

项目重点服务以下研究方向：

- LWE / RLWE / MLWE
- SIS / Module-SIS / NTRU
- ML-KEM / Kyber
- ML-DSA / Dilithium / Falcon
- BKZ / LLL / lattice reduction / hybrid attack
- AI4Lattice Cryptography
- Swin-guided coordinate selection
- RLWE / MLWE negative-cyclic modeling
- Module-SIS chameleon hash / commitment
- ZK-friendly post-quantum privacy primitives

## Safe manual quickstart

本地研究工作流是 manual-only usage：所有命令都由用户手动触发。No scheduled automation is configured；本地不配置 Windows Task Scheduler、cron、后台服务、startup task、watcher 或 automatic scheduling。

Workflow command center 默认 dry-run default。需要真实写文件时，先审查 dry-run 输出，再显式加入 `--execute`。

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
python -m lattice_digest.workflow daily --no-network --skip-hygiene
```

- `--low-load` 只在显式使用时降低手动运行的运行时 / 网络压力。
- `--no-network` / `--offline` 在支持的 workflow 中跳过网络抓取。
- generated artifacts must not be committed by default；`exports/`、`audits/`、`.pytest_tmp/`、`state/reading-queue.json`、本地测试 `data/` / `digests/` 和 `papers.db` 需要先人工判断。
- reading queue manual statuses / local state should be preserved.

## Documentation map

文档入口见 [docs/index.md](docs/index.md)。它汇总 manual operations、workflow command center、manual low-load workflow、recovery、artifact retention、troubleshooting、pilot feedback triage 和 release notes。

Core direct links: [docs/manual-operations-runbook.md](docs/manual-operations-runbook.md), [docs/workflow-command-center.md](docs/workflow-command-center.md), [docs/manual-low-load-workflow.md](docs/manual-low-load-workflow.md), [docs/recovery-playbook.md](docs/recovery-playbook.md), [docs/artifact-retention-policy.md](docs/artifact-retention-policy.md), [docs/troubleshooting.md](docs/troubleshooting.md), [docs/one-week-manual-pilot.md](docs/one-week-manual-pilot.md), [docs/pilot-acceptance-checklist.md](docs/pilot-acceptance-checklist.md), [docs/pilot-issue-log-template.md](docs/pilot-issue-log-template.md), [docs/pilot-feedback-triage.md](docs/pilot-feedback-triage.md), [docs/pilot-feedback-summary-template.md](docs/pilot-feedback-summary-template.md), [docs/pilot-fix-prioritization.md](docs/pilot-fix-prioritization.md).

## 快速部署 / Quick Deployment

Release status: v0.3.2 documentation and maintenance release. v0.3.1 remains the Manual Operations Patch Release, v0.3.0 remains the Research Workflow Stabilization Release, and v0.2.0 remains the Research Library Interoperability Stable Release. See [CHANGELOG.md](CHANGELOG.md), [docs/releases/v0.1.0.md](docs/releases/v0.1.0.md), [docs/releases/v0.2.0.md](docs/releases/v0.2.0.md), [docs/releases/v0.3.0.md](docs/releases/v0.3.0.md), [docs/releases/v0.3.1.md](docs/releases/v0.3.1.md), [docs/releases/v0.3.2.md](docs/releases/v0.3.2.md), historical [docs/releases/v0.2.0-rc1.md](docs/releases/v0.2.0-rc1.md), and [docs/release-checklist.md](docs/release-checklist.md).

完整公开部署说明见 [docs/deployment-public.md](docs/deployment-public.md)。不需要 Codex 自动化模块也能部署和运行；Codex is not required for deployment.

Quick Start / Local deployment / GitHub Actions deployment are documented in this README and in the public deployment guide. Recommended optional API configuration: set `SEMANTIC_SCHOLAR_API_KEY` to reduce Semantic Scholar rate-limit issues. Local authoritative backfill is recommended when GitHub Actions provisional coverage is degraded.

Manual operations, pilot feedback, recovery, artifact retention, troubleshooting, and release docs are mapped in [docs/index.md](docs/index.md).

Windows 11 PowerShell 最短本地验收命令：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m pip install -e ".[dev]"
python -m pytest
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

GitHub Actions secrets 在仓库页面配置：`Settings -> Secrets and variables -> Actions -> New repository secret`。最常用的是 `SEMANTIC_SCHOLAR_API_KEY` 和 SMTP 邮件相关 secrets。

## 项目功能

当前主分支已包含的能力：

- 每日格密码论文抓取、过滤、去重和 A/B/C/D 分类。
- 中文 8 节研究日报，输出到 `digests/YYYY-MM-DD.md`。
- 结构化 JSON 输出到 `data/YYYY-MM-DD.json`，并维护 `papers.db`。
- source health 红黄绿诊断，记录数据源成功、降级、失败和 warning。
- `reading_priority_score`、`priority_label` 和 `reason_for_priority`，用于判断“今日是否值得精读”。
- GitHub Actions provisional 日报与本地 `authoritative_backfill` 权威回填机制。
- backfill quality audit，用于比较 GitHub provisional 与本地权威回填的差异。
- Idea Bank 自动沉淀，把 digest 中的 `research_hooks`、`advisor_questions` 和优先级信息转成长期研究想法库。
- Idea -> Paper Plan 自动升级，把高价值 idea 转成保守、可执行、可验证的论文计划草案。
- Paper Plan -> Research Artifact scaffold，把论文计划转成可开工的研究项目骨架。
- Idea Bank 和 Paper Plan 的 Obsidian 兼容 Markdown 输出。
- 手动 Workflow Command Center：`daily`、`weekly`、`full`、`status`、`doctor`，默认 dry-run，写文件需要 `--execute`。
- Manual low-load mode：`--low-load` 适合笔记本和低负载手动运行；本地不默认配置 scheduled automation、Task Scheduler、cron、后台服务或自启动。

不把这些能力夸大为“自动写论文”或“自动判断安全性”。Paper Plan 和 Artifact Scaffold 只生成研究计划、目录结构、TODO 和复现实验骨架，不编造实验结果、安全证明或投稿结论。

当前 README 只描述本分支可检测到的已实现入口。单篇 Obsidian paper card 导出和 Weekly Research Brief 属于研究工作流中的自然扩展方向；如本地分支后续加入相应模块或脚本，可继续接入 `exports/obsidian/` 和 `exports/weekly/`。

## 数据源

当前配置中支持或预留的数据源包括：

- IACR ePrint
- arXiv
- DBLP
- OpenAlex
- Crossref
- Semantic Scholar

这些数据源可能出现 rate limit、HTTP 429、SSL、timeout 或网络 warning。项目的策略是记录 warning 和 source health，并尽量继续使用其他成功数据源生成报告，而不是让主流程直接崩溃。

## 本地运行

以下命令适用于 Windows 11 本地 PowerShell。请在项目根目录运行：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m pip install -e ".[dev]"
python -m pytest
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

如果只想做 dry-run：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.run --since 36h --dry-run
```

本地邮件发送脚本只读取最新的 `digests/YYYY-MM-DD.md` 正文，不会发送 `.env`、`papers.db` 或其他敏感文件内容：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python scripts\send_latest_digest_email.py
```

## 本地权威回填机制

GitHub Actions 负责 main 分支上的 provisional 日报，适合作为你不开电脑时的兜底机制。本地 Codex / PowerShell 运行负责 `authoritative` 或 `authoritative_backfill`，通常使用更稳定的本地网络和代理环境。

最近 5 天权威回填：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\run_local_digest_backfill.ps1 -Days 5
```

指定日期范围回填：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\run_local_digest_backfill.ps1 -FromDate 2026-05-25 -ToDate 2026-05-29
```

backfill 会逐日写入 `data/YYYY-MM-DD.json` 和 `digests/YYYY-MM-DD.md`。如果已有 GitHub Actions provisional 报告，本地权威回填会在允许替换时保留旧版本快照，便于后续审计。

## 主要输出

正式日报产物：

- `digests/YYYY-MM-DD.md`：中文 Markdown 日报。
- `data/YYYY-MM-DD.json`：结构化 digest 数据。
- `papers.db`：本地论文记录数据库。

回填与审计产物：

- `archive/provisional/YYYY-MM-DD.json`
- `archive/provisional/YYYY-MM-DD.md`
- `audits/backfill/YYYY-MM-DD.json`
- `audits/backfill/YYYY-MM-DD.md`

研究规划与本地生成产物：

- `exports/ideas/idea-bank.json`
- `exports/ideas/idea-bank.md`
- `exports/obsidian/ideas/idea-bank.md`
- `exports/paper_plans/*.json`
- `exports/paper_plans/*.md`
- `exports/obsidian/paper_plans/*.md`
- `research_artifacts/<slug>/`

`exports/`、`audits/` 和 `research_artifacts/` 通常是本地生成物，默认不随功能 commit 提交。`data/`、`digests/` 和 `papers.db` 可以由 GitHub Actions 或正式日报流程提交，但本地开发测试生成物不要混入功能 commit。

## Stable Library Export Layer

v0.2.0 stable 提供 Stable Library Export Layer、Zotero Compatibility Layer 和 Zotero Manual Import QA，用于把已有 `data/*.json` 转换成稳定文献库互操作格式。导出层只读取已有 digest JSON，不运行 fetcher，也不修改 `data/`、`digests/` 或 `papers.db`。

支持格式包括：

- CSL JSON
- BibTeX
- RIS
- `library-items.json`
- `zotero-tags.json`
- `import-report.md`

详细说明见 [docs/library-interop.md](docs/library-interop.md)、[docs/library-export-audit.md](docs/library-export-audit.md)、[docs/zotero-compat.md](docs/zotero-compat.md)、[docs/zotero-manual-import.md](docs/zotero-manual-import.md) 和 [docs/releases/v0.2.0.md](docs/releases/v0.2.0.md)。本地导出命令：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\export_library.ps1 -Days 7
```

Zotero XPI plugin is not included in v0.2.0. Zotero Web API push is not included in v0.2.0. Current workflow is file-based manual import: export CSL JSON / BibTeX / RIS, then use Zotero `File -> Import` and manually verify authors, year, DOI, URL, abstract, tags, and notes.

导出后可以运行 Library Export Quality Audit、taxonomy quality audit 与 Zotero Manual Import QA，检查标签误报、字段完整性和手动导入流程。说明见 [docs/library-export-audit.md](docs/library-export-audit.md)，脚本入口：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\audit_library_export.ps1 -Input exports\library\library-items.json
```

Phase 7C adds a Zotero Compatibility Layer for offline Zotero JSON / CSL-JSON / BibTeX / RIS export, without calling the Zotero API or creating an `.xpi` plugin. See [docs/zotero-compat.md](docs/zotero-compat.md) and run:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\export_zotero.ps1 -Days 7 -DryRun
```

## 研究工作流

推荐使用方式：

1. 每日运行 digest，快速发现 LWE、MLWE、Module-SIS、BKZ、PQC implementation 和 AI4Lattice 相关论文。
2. 查看 source health，判断当天数据源是否可靠。
3. 用 `reading_priority_score` 选择“今日精读 / 本周阅读 / 暂存”论文。
4. 通过 backfill 补齐 GitHub provisional 日报中可能漏掉的论文。
5. 生成 Idea Bank，把论文线索沉淀为长期研究想法。
6. 将高价值 idea 升级为 Paper Plan，用于组会、导师讨论和短期论文设计。
7. 从 Paper Plan 生成 Research Artifact scaffold，进入可复现实验和论文写作阶段。
8. 使用 `python -m lattice_digest.workflow weekly --low-load` 做手动低负载 dry-run；需要写文件时再显式加入 `--execute`。

该工作流服务两个目标：短期形成可执行的小论文或 artifact，长期沉淀 PhD 研究主线。

本地命令中心不配置自动调度；所有 workflow 都由用户手动触发。说明见 [docs/workflow-command-center.md](docs/workflow-command-center.md) 和 [docs/manual-low-load-workflow.md](docs/manual-low-load-workflow.md)。

## 云端自动运行：GitHub Actions

`.github/workflows/daily.yml` 定义了云端自动运行：

- 每天 `01:17 UTC` 运行，约为 `09:17 Asia/Shanghai / Asia/Singapore`。
- 支持 `Run workflow` 手动触发。
- 运行 `python -m pytest`。
- 运行 `python -m lattice_digest.run --since 36h --output markdown,json --send none --collector github_actions --quality-status provisional --run-mode daily`。
- 验证 Markdown、JSON 和 `papers.db`。
- 只自动提交 `digests/*.md`、`data/*.json` 和 `papers.db`。
- SMTP secrets 完整时发送最新日报邮件；不完整时输出跳过信息并继续成功。

GitHub Actions 的定位是 provisional collector，不应替代本地 authoritative backfill。

## GitHub Secrets 配置

邮件发送需要在 GitHub 仓库中配置 SMTP secrets：

`Settings -> Secrets and variables -> Actions -> New repository secret`

需要的变量：

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `DIGEST_EMAIL_TO`
- `DIGEST_EMAIL_FROM`

`SMTP_PASSWORD` 应使用邮箱授权码或应用密码，而不是明文登录密码。不要把真实 SMTP 密码、GitHub token、API key 写入仓库。

可选数据源相关变量：

- `CONTACT_EMAIL`
- `SEMANTIC_SCHOLAR_API_KEY`

## 本地手动补交到 GitHub

如果本地已经生成了日报产物，可以双击或在 CMD / PowerShell 中运行：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
cmd /c scripts\push_all_digest_outputs.bat
```

这个 bat 只做补交：

- 不抓取论文。
- 不运行分类。
- 不运行测试。
- 只提交 `digests/`、`data/` 和 `papers.db`。
- 可补交多个历史日期。

如果本地 push 失败，检查 Clash、git proxy 和 GitHub 凭据：

```powershell
git config --global --get http.proxy
git config --global --get https.proxy
git ls-remote https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git
git push
```

## 质量控制

项目测试覆盖的方向包括：

- 配置与 taxonomy / negative keyword 规则。
- 非密码学 lattice / SIS 噪声过滤。
- arXiv、IACR、Semantic Scholar、Crossref 等解析和边界行为。
- HTTP cache / backoff / 429 不崩溃。
- source health 统计。
- digest 输出结构。
- GitHub Actions workflow 和邮件脚本。
- backfill metadata 与 backfill audit。
- Idea Bank、Paper Plan 和 Research Artifact scaffold。

本地验收命令：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m pytest
```

## 不推荐 watcher 自启动

不推荐为本项目配置本地 watcher、自启动脚本或 Windows Task Scheduler 计划任务。本地 watcher 依赖电脑持续开机、本地网络、代理、GitHub 登录状态以及 Codex sandbox 对 `.git` 的写入权限，可能带来少量资源占用和权限问题。

推荐使用 GitHub Actions 做云端每日定时运行；本地只保留 `scripts\push_all_digest_outputs.bat`，用于手动补交已经生成好的 `digests/`、`data/` 和 `papers.db`。

## 不提交哪些文件

不要提交：

- `.pytest_tmp/`
- `.cache/`
- `__pycache__/`
- `.env`
- 真实 API key、SMTP 密码或 GitHub token
- 临时运行产物
- 大规模实验数据
- 真实 Obsidian vault 路径或私人笔记

`data/`、`digests/` 和 `papers.db` 是正式日报产物，可由 GitHub Actions 或明确的日报发布流程提交；不要把本地测试生成物混入功能 commit。

## Roadmap

短中期方向：

- 更稳健的数据源降级处理。
- Semantic Scholar API key 支持与限额治理。
- 更细的 AI4Lattice / lattice reduction / PQC implementation 标签体系。
- 更强的 false positive 控制。
- 单篇 Obsidian paper card 导出。
- Weekly Research Brief 周报聚合。
- Obsidian / Zotero / ChatGPT 研究工作流联动。
- Module-SIS chameleon hash artifact。
- AI4Lattice hybrid ranking baseline artifact。

## 常见问题

**GitHub Actions 成功但没有邮件怎么办？**  
检查 `SMTP_HOST`、`SMTP_PORT`、`SMTP_USERNAME`、`SMTP_PASSWORD`、`DIGEST_EMAIL_TO`、`DIGEST_EMAIL_FROM` 是否都已配置。SMTP secrets 不完整时，workflow 会输出 `Email sending skipped: SMTP secrets not configured.` 并继续成功。

**GitHub Actions 有 Node.js 20 warning 是否失败？**  
当前这是 warning，不影响日报成功。后续可以升级 actions 版本或设置 Node 24 兼容，但不需要为了 warning 改动业务逻辑。

**本地 push 失败怎么办？**  
检查 Clash 是否运行、git proxy 是否正确、GitHub 凭据是否可用。可以先运行 `git ls-remote https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git` 验证连接。

**看到 429 warning 是否说明日报失败？**  
不是。429 warning 通常表示数据源限流，项目会降级处理并继续使用其他成功数据源；这不等于失败。

**本地 Codex 无法写 `.git` 怎么办？**  
使用 `scripts\push_all_digest_outputs.bat` 手动补交已经生成的日报产物。这个方案不依赖 Codex 直接写 `.git`。

## English Version

## Overview

`lattice-crypto-daily-digest` is a research automation system for lattice-based cryptography, post-quantum cryptography, and AI-assisted lattice cryptanalysis. It is designed as a daily research radar rather than a generic paper digest demo. The system collects candidate papers from academic metadata sources, deduplicates them, filters hard false positives, ranks research relevance, records source health, and produces Chinese Markdown digests, structured JSON data, and local research-planning artifacts.

The project is built around research lines such as:

- LWE / RLWE / MLWE
- SIS / Module-SIS / NTRU
- ML-KEM / Kyber
- ML-DSA / Dilithium / Falcon
- BKZ / LLL / lattice reduction / hybrid attacks
- AI4Lattice Cryptography
- Swin-guided coordinate selection
- RLWE / MLWE negative-cyclic modeling
- Module-SIS chameleon hashes and commitments
- ZK-friendly post-quantum privacy primitives

## Core Capabilities

Capabilities currently present in this branch:

- Daily retrieval, filtering, deduplication, and A/B/C/D classification for lattice-cryptography papers.
- An 8-section Chinese research digest written to `digests/YYYY-MM-DD.md`.
- Structured JSON output written to `data/YYYY-MM-DD.json`, with `papers.db` as the local paper database.
- Green/yellow/red source health diagnostics for successful, degraded, and failed sources.
- `reading_priority_score`, `priority_label`, and `reason_for_priority` for deciding whether a paper deserves immediate reading.
- GitHub Actions provisional reports plus local `authoritative_backfill`.
- Backfill quality audit for comparing GitHub provisional reports with local authoritative reports.
- Idea Bank generation from digest records, research hooks, advisor questions, and reading-priority signals.
- Idea-to-Paper-Plan upgrade for turning promising ideas into conservative research plans.
- Paper-Plan-to-Research-Artifact scaffold generation for reproducible experiments and writing.
- Obsidian-compatible Markdown outputs for Idea Bank and Paper Plans.
- Manual Workflow Command Center with `daily`, `weekly`, `full`, `status`, and `doctor`.
- Manual low-load mode for laptop-friendly runs. Local scheduled automation is not configured by default: no Task Scheduler, cron, background service, daemon, or startup task is installed.

The project does not automatically write papers or decide cryptographic security. Paper Plans and Research Artifacts are conservative planning drafts. They do not invent experimental results, security proofs, or publication claims.

The current branch does not expose standalone modules for individual Obsidian paper-card export or Weekly Research Brief generation. Those are natural workflow extensions and are listed in the roadmap rather than presented as implemented commands.

## Data Sources

The current configuration supports or reserves the following sources:

- IACR ePrint
- arXiv
- DBLP
- OpenAlex
- Crossref
- Semantic Scholar

Academic APIs may return rate limits, HTTP 429, SSL errors, timeouts, or transient network warnings. The system records warnings and source health, then continues with other available sources whenever possible.

## Quick Start

Run the following commands in Windows 11 PowerShell from the project root:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m pip install -e ".[dev]"
python -m pytest
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

Dry-run:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.run --since 36h --dry-run
```

Send the latest local digest by email:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python scripts\send_latest_digest_email.py
```

The email script reads only the latest `digests/YYYY-MM-DD.md` body. It does not send `.env`, `papers.db`, or other sensitive files.

## Local Authoritative Backfill

GitHub Actions generates provisional reports on `main`. This is useful as a fallback when the local machine is offline. Local Codex / PowerShell runs generate `authoritative` or `authoritative_backfill` reports, typically with a more reliable local network and proxy setup.

Backfill the last 5 days:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\run_local_digest_backfill.ps1 -Days 5
```

Backfill a specific date range:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\run_local_digest_backfill.ps1 -FromDate 2026-05-25 -ToDate 2026-05-29
```

Backfill writes one report per target date and preserves provisional snapshots when replacing GitHub-generated reports.

## Outputs

Daily report outputs:

- `digests/YYYY-MM-DD.md`
- `data/YYYY-MM-DD.json`
- `papers.db`

Backfill and audit outputs:

- `archive/provisional/YYYY-MM-DD.json`
- `archive/provisional/YYYY-MM-DD.md`
- `audits/backfill/YYYY-MM-DD.json`
- `audits/backfill/YYYY-MM-DD.md`

Research-planning outputs:

- `exports/ideas/idea-bank.json`
- `exports/ideas/idea-bank.md`
- `exports/obsidian/ideas/idea-bank.md`
- `exports/paper_plans/*.json`
- `exports/paper_plans/*.md`
- `exports/obsidian/paper_plans/*.md`
- `research_artifacts/<slug>/`

`exports/`, `audits/`, and `research_artifacts/` are local generated outputs and are not submitted by default. `data/`, `digests/`, and `papers.db` may be committed by GitHub Actions or an explicit digest publishing workflow, but local test outputs should not be mixed into feature commits.

## Research Workflow

Recommended workflow:

1. Run the daily digest to discover relevant papers.
2. Inspect source health before trusting the day’s coverage.
3. Use `reading_priority_score` to decide what to read today, this week, or save for later.
4. Use local backfill to improve GitHub provisional reports.
5. Generate an Idea Bank from accumulated digest records.
6. Upgrade strong ideas into Paper Plans for advisor discussion and short-term project design.
7. Generate Research Artifact scaffolds from Paper Plans to start reproducible experiments and writing.
8. Use `python -m lattice_digest.workflow weekly --low-load` for a manual low-load dry-run; add `--execute` only when you intentionally want files written.

The workflow is meant to support both short-term paper/artifact execution and long-term PhD research-line development.

The local workflow command center is manually triggered and does not configure scheduled automation. See [docs/workflow-command-center.md](docs/workflow-command-center.md) and [docs/manual-low-load-workflow.md](docs/manual-low-load-workflow.md).

## GitHub Actions

`.github/workflows/daily.yml` defines the cloud automation:

- Runs daily at `01:17 UTC`, roughly `09:17 Asia/Shanghai / Asia/Singapore`.
- Supports manual `Run workflow`.
- Runs `python -m pytest`.
- Runs `python -m lattice_digest.run --since 36h --output markdown,json --send none --collector github_actions --quality-status provisional --run-mode daily`.
- Verifies Markdown, JSON, and `papers.db`.
- Commits only `digests/*.md`, `data/*.json`, and `papers.db`.
- Sends the latest digest email only when all SMTP secrets are configured.

GitHub Actions is a provisional collector. It should not replace local authoritative backfill.

## GitHub Secrets

Configure email secrets in:

`Settings -> Secrets and variables -> Actions -> New repository secret`

Required SMTP secrets:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `DIGEST_EMAIL_TO`
- `DIGEST_EMAIL_FROM`

`SMTP_PASSWORD` should be an email app password or authorization code, not a plain account password. Never commit real SMTP passwords, GitHub tokens, or API keys.

Optional source-related variables:

- `CONTACT_EMAIL`
- `SEMANTIC_SCHOLAR_API_KEY`

## Manual Local Push

If local commands have already generated digest outputs, you can manually submit them:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
cmd /c scripts\push_all_digest_outputs.bat
```

The batch script only submits digest outputs:

- It does not fetch papers.
- It does not run classification.
- It does not run tests.
- It only stages `digests/`, `data/`, and `papers.db`.
- It can submit multiple historical dates.

If push fails, check Clash, git proxy settings, and GitHub credentials.

## Quality Control

The test suite covers:

- Configuration and taxonomy rules.
- Hard false-positive filtering for non-cryptographic lattice / SIS papers.
- Parser and policy behavior for arXiv, IACR, Semantic Scholar, and Crossref.
- HTTP cache, backoff, and 429 continuation behavior.
- Source health statistics.
- Digest output structure.
- GitHub Actions workflow and optional email delivery.
- Backfill metadata and backfill audit.
- Idea Bank, Paper Plan, and Research Artifact scaffold generation.

Local validation:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m pytest
```

## Files Not To Commit

Do not commit:

- `.pytest_tmp/`
- `.cache/`
- `__pycache__/`
- `.env`
- Real API keys, SMTP passwords, or GitHub tokens
- Temporary runtime outputs
- Large experimental data
- Real Obsidian vault paths or private notes

`data/`, `digests/`, and `papers.db` are official digest artifacts and may be committed by the scheduled workflow or explicit publishing flow. Avoid mixing local test outputs into feature commits.

## Roadmap

Short- and medium-term directions:

- More robust source degradation handling.
- Semantic Scholar API key and quota management.
- Finer AI4Lattice / lattice reduction / PQC implementation tagging.
- Stronger false-positive control.
- Individual Obsidian paper-card export.
- Weekly Research Brief aggregation.
- Obsidian / Zotero / ChatGPT research workflow integration.
- Module-SIS chameleon hash artifact.
- AI4Lattice hybrid ranking baseline artifact.

## FAQ

**GitHub Actions succeeded but no email was sent. What should I check?**  
Check whether `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `DIGEST_EMAIL_TO`, and `DIGEST_EMAIL_FROM` are all configured. If SMTP secrets are incomplete, the workflow prints `Email sending skipped: SMTP secrets not configured.` and continues successfully.

**Does a Node.js 20 warning mean the workflow failed?**  
No. It is currently a warning and does not prevent digest generation.

**Local push failed. What should I check?**  
Check Clash, git proxy settings, and GitHub credentials. You can run `git ls-remote https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git` to test connectivity.

**Does a 429 warning mean the digest failed?**  
No. A 429 warning usually means an upstream source rate-limited the request. The project records the warning, degrades that source, and continues with other available sources when possible.

**Codex cannot write `.git` locally. What should I do?**  
Use `scripts\push_all_digest_outputs.bat` to manually submit generated digest artifacts. This does not rely on Codex writing `.git` directly.
