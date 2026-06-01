# Recovery Playbook

本 playbook 用于本地误操作、测试产物残留、SQLite 文件锁、reading queue 误改和 `papers.db` 恢复。项目不配置 scheduled automation；恢复操作也必须手动执行。

English summary: use this document for manual recovery only. No background recovery service or scheduled task is configured.

## 1. First response checklist

PowerShell：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
git status -sb
git diff --stat
git diff --check
```

cmd：

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
git status -sb
git diff --stat
git diff --check
```

先确认是否只是 ignored generated artifacts，不要急着删除或 reset。

## 2. Cleanup commands

清理 pytest 临时目录：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
if (Test-Path ".pytest_tmp") { Remove-Item ".pytest_tmp" -Recurse -Force }
```

清理 Python cache：

```powershell
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

查看将被 Git 忽略规则清理的文件，不真正删除：

```powershell
git clean -ndX
```

确认列表安全后，才可以手动执行：

```powershell
git clean -fdX
```

不要用 `git clean -fdx`，它会删除未忽略的本地文件，风险更高。

## 3. Reading queue backup and recovery

`state/reading-queue.json` 保存人工阅读状态，默认不提交。执行会写 queue 的命令前，建议备份：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
New-Item -ItemType Directory -Force -Path "backups\reading-queue" | Out-Null
Copy-Item "state\reading-queue.json" "backups\reading-queue\reading-queue-$(Get-Date -Format yyyyMMdd-HHmmss).json"
```

恢复：

```powershell
Copy-Item "backups\reading-queue\<backup-file>.json" "state\reading-queue.json"
python -m lattice_digest.reading_queue audit
```

如果 `state/reading-queue.json` 不存在，可从 weekly JSON 或 artifact manifest 重新 import，但手动状态可能丢失。

## 4. papers.db recovery

`papers.db` 是生成数据库。不要随意删除。恢复顺序：

1. 确认是否只是 SQLite file lock。
2. 关闭正在运行的 Python、pytest、编辑器预览或文件索引工具。
3. 重新运行测试或 digest 命令。
4. 如果数据库损坏，先备份当前文件，再从 Git 或最近发布产物恢复。

备份当前数据库：

```powershell
Copy-Item "papers.db" "papers.db.backup.$(Get-Date -Format yyyyMMdd-HHmmss)"
```

如果 `papers.db` 是 Git 跟踪的正式产物，需要人工决定是否从 `origin/main` 恢复，不要自动覆盖。

## 5. Windows SQLite file lock issue

典型症状：

- `PermissionError: [WinError 32]`
- TemporaryDirectory 删除 `papers.db` 失败
- SQLite database is locked

处理步骤：

1. 关闭占用 `papers.db` 的 Python 进程。
2. 关闭打开数据库的 GUI 工具。
3. 确认测试代码使用 deterministic close；不要让 SQLite connection 悬挂。
4. 重新运行相关测试：

```powershell
python -m pytest tests\test_storage_sqlite_cleanup.py tests\test_backfill_metadata.py tests\test_source_health.py
```

## 6. tzdata / ZoneInfo issue

典型症状：

- `ZoneInfoNotFoundError`
- `No time zone found with key Asia/Singapore`

Windows runner 需要 `tzdata` 依赖。检查：

```powershell
python -c "from zoneinfo import ZoneInfo; print(ZoneInfo('Asia/Singapore'))"
python -m pip show tzdata
```

如果缺失，安装项目依赖：

```powershell
python -m pip install -e ".[dev]"
```

不要把 `Asia/Singapore` 改成 UTC 来规避问题。

## 7. CI failure triage

CI 失败时按顺序看：

1. 失败平台：Windows 还是 Ubuntu。
2. 失败类型：测试断言、文档断言、SQLite lock、ZoneInfo、line ending、generated artifact。
3. 是否是历史 release 测试 stale。
4. 是否误提交了 ignored artifact。
5. 是否由网络源失败导致；fixture-based 测试不应依赖网络。

本地复现：

```powershell
python -m pytest
python scripts\check_release_hygiene.py
git diff --check
```

## 8. If generated artifacts accidentally appear

先查看：

```powershell
git status -sb
git status --ignored -sb -- exports audits state data digests papers.db .pytest_tmp __pycache__
```

如果只是 ignored artifacts，通常不需要提交。需要清理时按第 2 节执行。`data/`、`digests/`、`papers.db` 若是正式日报产物，必须单独判断，不要混入功能修复。
