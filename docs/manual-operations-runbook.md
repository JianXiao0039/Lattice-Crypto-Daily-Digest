# Manual Operations Runbook

本 runbook 面向日常手动运维。项目不配置 Windows Task Scheduler、cron、startup task、background service 或 watcher；所有 workflow 都由用户显式触发。默认策略是先 dry-run，再决定是否执行写文件命令。

English summary: this project is operated manually. No scheduled automation is configured. Prefer dry-run and low-load workflows first.

## 1. Manual-only usage

推荐入口：

- `python -m lattice_digest.workflow status`：只读状态检查。
- `python -m lattice_digest.workflow doctor`：只读环境检查。
- `python -m lattice_digest.workflow weekly --low-load --skip-hygiene`：低负载周流程 dry-run。
- `python -m lattice_digest.workflow weekly --execute --low-load --skip-hygiene`：确认后才写入周流程产物。
- `scripts\run_weekly_handoff.bat`：手动生成 weekly handoff packets，用于公开 research radar triage。

不要配置：

- Windows Task Scheduler
- cron
- startup task
- background daemon
- watcher
- auto-start service

## 2. PowerShell quick commands

在 PowerShell 中运行：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
```

写文件前先确认 dry-run 输出。确认后再运行：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow weekly --execute --low-load --skip-hygiene
```

## 3. cmd quick commands

在 Windows cmd 中运行：

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
```

不要在 cmd 中粘贴 `Set-Location`；那是 PowerShell 命令。

## 4. Dry-run default

Workflow command center 的 `daily`、`weekly`、`full` 默认 dry-run。dry-run default means the command prints planned steps first; only explicit `--execute` writes files.

推荐顺序：

1. `status`
2. `doctor`
3. `weekly --low-load`
4. `weekly --execute --low-load`

## 5. Low-load mode

低负载模式适合笔记本、临时网络或不希望占用电脑资源的场景：

```powershell
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
python -m lattice_digest.workflow daily --low-load --skip-hygiene
```

`--low-load` 会在 workflow 计划中体现低负载 profile。普通模式语义保持不变。

## 6. Offline / no-network usage

离线或不希望访问网络时：

```powershell
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
python -m lattice_digest.workflow daily --no-network --skip-hygiene
python -m lattice_digest.workflow daily --offline --skip-hygiene
```

`status` 和 `doctor` 是只读命令，不应执行网络抓取。`--no-network` / `--offline` 用于避免 daily fetch 类步骤。

## 7. Command safety matrix

| Command | Read-only or not | Writes files or not | Network behavior | Low-load support | Notes |
| --- | --- | --- | --- | --- | --- |
| `git status -sb` | Read-only | No | No network | N/A | First check before cleanup or commit decisions. |
| `git diff --check` | Read-only | No | No network | N/A | Catches whitespace and LF/CRLF diff issues. |
| `python scripts\check_release_hygiene.py` | Read-only check | No | No network | N/A | Checks release hygiene and generated artifact boundaries. |
| `python -m lattice_digest.workflow status` | Read-only | No | No network fetch | N/A | Safe local state overview. |
| `python -m lattice_digest.workflow doctor` | Read-only | No | No network fetch | N/A | Environment checks only. |
| `python -m lattice_digest.workflow weekly --low-load --skip-hygiene` | Dry-run plan | No | Uses local artifacts | Yes | Manual low-load weekly plan; add `--execute` only after review. |
| `python -m lattice_digest.workflow daily --low-load --skip-hygiene` | Dry-run plan | No | May plan network fetches | Yes | `--low-load` applies only because it is explicitly passed. |
| `python -m lattice_digest.workflow daily --no-network --skip-hygiene` | Dry-run plan | No | Skips network fetch where supported | Optional | Use for offline or no-network checks. |
| `python -m lattice_digest.workflow weekly --execute --low-load --skip-hygiene` | Not read-only | Yes | Uses local artifacts | Yes | Writes weekly outputs, reading queue updates, progress logs, and manifests. |
| `scripts\run_weekly_handoff.bat` | Not read-only | Yes | No network fetch | N/A | Manual-only helper; writes ignored `handoffs/weekly/` packet JSON/Markdown. |
| `powershell.exe -ExecutionPolicy Bypass -File scripts\run_weekly_handoff.ps1` | Not read-only | Yes | No network fetch | N/A | PowerShell version of the manual weekly handoff helper. |
| `python -m lattice_digest.run --since 36h --output markdown,json --send none` | Not read-only | Yes | Fetches configured sources | No workflow profile | Writes daily Markdown, JSON, and `papers.db`. |
| `python -m lattice_digest.obsidian_scaffold generate` | Not read-only | Yes | No network fetch expected | No workflow profile | Writes Obsidian scaffold output only when intentionally run. |

## 8. Read-only commands

这些命令用于检查，不应写入研究产物：

| Command | PowerShell example | Notes |
| --- | --- | --- |
| Git status | `git status -sb` | 只读 |
| Diff check | `git diff --check` | 只读 |
| Release hygiene | `python scripts\check_release_hygiene.py` | 只读检查 |
| Workflow status | `python -m lattice_digest.workflow status` | 只读 |
| Workflow doctor | `python -m lattice_digest.workflow doctor` | 只读 |
| Weekly dry-run | `python -m lattice_digest.workflow weekly --low-load --skip-hygiene` | dry-run，不写产物 |

## 9. Commands that write files

这些命令会写入文件，运行前先确认工作区状态：

| Command | Main outputs |
| --- | --- |
| `python -m lattice_digest.run --since 36h --output markdown,json --send none` | `data/YYYY-MM-DD.json`, `digests/YYYY-MM-DD.md`, `papers.db` |
| `python -m lattice_digest.weekly_synthesis --days 7` | `data/weekly/YYYY-Www.json`, `digests/weekly/YYYY-Www.md` |
| `python -m lattice_digest.workflow weekly --execute --low-load --skip-hygiene` | weekly JSON/Markdown, reading queue, research progress, workflow manifest |
| `scripts\run_weekly_handoff.bat` | `handoffs/weekly/YYYY-Www-handoff-packets.json`, `handoffs/weekly/YYYY-Www-handoff-packets.md` |
| `powershell.exe -ExecutionPolicy Bypass -File scripts\run_weekly_handoff.ps1` | `handoffs/weekly/YYYY-Www-handoff-packets.json`, `handoffs/weekly/YYYY-Www-handoff-packets.md` |
| `python -m lattice_digest.obsidian_scaffold generate` | Obsidian paper note scaffolds |
| `python -m lattice_digest.research_progress generate` | advisor update and verification backlog |

## 10. Generated artifacts that must not be committed by default

Generated artifacts must not be committed by default. 默认不要提交：

- `exports/`
- `handoffs/`
- `audits/`
- `.pytest_tmp/`
- `__pycache__/`
- `state/reading-queue.json`
- `data/*.json`
- `data/weekly/`
- `digests/*.md`
- `digests/weekly/`
- `papers.db`
- `.env`
- real API keys, SMTP passwords, Zotero tokens

`data/`、`digests/`、`papers.db` 只有在明确发布日报产物时才应作为单独 artifact commit 处理，不要混入功能 commit。

## 11. Before any commit

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
git status -sb
python -m pytest tests --basetemp=.pytest_tmp
python scripts\check_release_hygiene.py
git diff --check
```

如果看到运行产物，先按 `docs/recovery-playbook.md` 清理或备份。
