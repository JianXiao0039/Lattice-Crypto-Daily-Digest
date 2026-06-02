# Troubleshooting

本文件收集本项目最常见的本地与 CI 问题。项目不配置自动调度；所有命令都应由用户手动触发。No scheduled automation is configured.

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
python -m pytest tests
python scripts\check_release_hygiene.py
git diff --check
git status -sb
```

常见原因：

- release hygiene failure；
- version mismatch failure；
- README missing link failure；
- workflow doctor failure；
- release docs/test 中的旧版本断言没有归档化；
- Windows SQLite file lock；
- Windows 缺 `tzdata`；
- generated artifacts 被误追踪；
- LF/CRLF git diff --check warning；
- 文档断言缺失 README link。

### Pytest collects external package tests

症状：Windows 上 `python -m pytest` 误收集全局或环境目录中的外部包测试，例如 `site-packages` / pywin32 `win32comext.taskscheduler`，甚至触发 Python access violation。

处理：

```powershell
python -m pytest tests
```

项目的 `pyproject.toml` 已将 `testpaths` 限定到 `tests`，并通过 `norecursedirs` 排除 `.venv`、`venv`、`site-packages`、`Lib`、`Scripts`、`exports`、`audits`、`.pytest_tmp`、`__pycache__` 等目录。不要让 pytest 收集外部 site-packages 测试。

### Release hygiene failure

症状：`python scripts\check_release_hygiene.py` 返回非零，或提示 generated artifacts、版本文档、release checklist 不一致。

处理：

```powershell
python scripts\check_release_hygiene.py
git status -sb
```

先确认是否误改了 release docs、生成物或版本号；不要用提交 generated artifacts 来绕过 hygiene failure。

### Version mismatch failure

症状：README、CHANGELOG、release notes、`pyproject.toml` 或 release tests 对当前版本的描述不一致。

处理：以当前 release docs 和 `CHANGELOG.md` 为准，更新 stale wording；历史 release notes 保持历史语境，不把旧版本改成 latest。

### README missing link failure

症状：docs tests 报 README missing link。

处理：确认 README 是否链接到 [docs/index.md](index.md) 或对应核心文档；优先补导航，不要移动文档导致旧链接失效。

### Workflow doctor failure

症状：`python -m lattice_digest.workflow doctor` 报环境、依赖、路径或本地状态问题。

处理：先按 doctor 输出修复环境；如果涉及写文件，先运行 dry-run 并检查 `git status -sb`。

### LF/CRLF git diff --check warning

症状：`git diff --check` 报 whitespace、CRLF 或 trailing whitespace。

处理：修正文档或代码行尾；不要通过关闭检查来绕过。

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

generated artifacts must not be committed by default. `state/reading-queue.json` 是 local personal state；reading queue manual statuses should be preserved.

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
