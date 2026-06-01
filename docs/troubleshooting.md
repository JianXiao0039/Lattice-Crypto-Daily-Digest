# Troubleshooting

本文件收集本项目最常见的本地与 CI 问题。项目不配置自动调度；所有命令都应由用户手动触发。

## 1. Command shell confusion

### `Set-Location is not recognized`

原因：在 cmd 中运行了 PowerShell 命令。

PowerShell：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
```

cmd：

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
```

## 2. Dry-run and execute confusion

Workflow command center 默认 dry-run：

```powershell
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
```

写文件必须显式：

```powershell
python -m lattice_digest.workflow weekly --execute --low-load --skip-hygiene
```

如果你不想访问网络，可使用：

```powershell
python -m lattice_digest.workflow daily --no-network --skip-hygiene
python -m lattice_digest.workflow daily --offline --skip-hygiene
```

## 3. Low-load mode

`--low-load` 是手动低负载 profile，适合笔记本和临时运行：

```powershell
python -m lattice_digest.workflow daily --low-load --skip-hygiene
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
```

它不是后台任务，也不会配置 scheduled automation。

## 4. SQLite / papers.db lock on Windows

症状：

- `PermissionError: [WinError 32]`
- `sqlite3.OperationalError: database is locked`
- pytest 临时目录删除 `papers.db` 失败

处理：

```powershell
Get-Process python -ErrorAction SilentlyContinue
python -m pytest tests\test_storage_sqlite_cleanup.py
```

关闭持有数据库的 Python、编辑器插件或 SQLite GUI 后重试。不要直接删除正式 `papers.db`。

## 5. ZoneInfo / tzdata issue

症状：

- `ZoneInfoNotFoundError`
- `No time zone found with key Asia/Singapore`

检查：

```powershell
python -c "from zoneinfo import ZoneInfo; print(ZoneInfo('Asia/Singapore'))"
python -m pip show tzdata
```

修复：

```powershell
python -m pip install -e ".[dev]"
```

## 6. CI failure triage

先运行：

```powershell
python -m pytest
python scripts\check_release_hygiene.py
git diff --check
git status -sb
```

常见原因：

- release docs/test 中的旧版本断言没有归档化；
- Windows SQLite file lock；
- Windows 缺 `tzdata`；
- generated artifacts 被误追踪；
- line ending warning；
- 文档断言缺失 README link。

## 7. Network source warnings

外部源可能出现：

- Semantic Scholar 429；
- arXiv timeout；
- OpenAlex 429；
- SSL warning；
- temporary network failure。

这些通常应记录为 source health red/yellow，而不是直接让主流程崩溃。若需要降低压力，先使用 `--low-load` 或扩大到本地 backfill。

## 8. Generated artifacts accidentally changed

查看：

```powershell
git status -sb
git status --ignored -sb -- exports audits state data digests papers.db .pytest_tmp __pycache__
```

默认不要提交：

- `exports/`
- `audits/`
- `.pytest_tmp/`
- `__pycache__/`
- `state/reading-queue.json`
- `data/*.json`
- `digests/*.md`
- `papers.db`
- `.env`

## 9. Reading queue looks wrong

先备份：

```powershell
New-Item -ItemType Directory -Force -Path "backups\reading-queue" | Out-Null
Copy-Item "state\reading-queue.json" "backups\reading-queue\reading-queue-$(Get-Date -Format yyyyMMdd-HHmmss).json"
```

审计：

```powershell
python -m lattice_digest.reading_queue audit
```

如果是 import 造成的，检查 weekly JSON 和 dedup key；人工状态应被保留。

## 10. English summary

Use PowerShell commands in PowerShell and cmd commands in cmd. Workflow commands are dry-run by default. Use `--execute` only when you intend to write files. Low-load mode is manual and laptop-friendly. No scheduled automation is configured. Generated artifacts and secrets must not be committed by default.
