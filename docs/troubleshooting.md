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
python -m pytest tests\test_storage_sqlite_cleanup.py --basetemp=.pytest_tmp
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
python -m pytest tests --basetemp=.pytest_tmp
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

症状：Windows 上 `python -m pytest tests --basetemp=.pytest_tmp` 误收集全局或环境目录中的外部包测试，例如 `site-packages` / pywin32 `win32comext.taskscheduler`，甚至触发 Python access violation。

常见原因：旧的外部 ChatGPT / Codex recurring automation prompt 仍在每天运行，并继续使用陈旧命令 `python -m lattice_digest.run --since 36h --output markdown,json --send none` 与裸 `python -m pytest tests --basetemp=.pytest_tmp`。本项目不推荐任何本地自动每日运行；请停用这类外部 recurring automation，并改用 [manual-codex-quality-run-prompt.md](manual-codex-quality-run-prompt.md) 中的手动 prompt。

处理：

```powershell
python -m pytest tests --basetemp=.pytest_tmp
```

项目的 `pyproject.toml` 已将 `testpaths` 限定到 `tests`，通过 `norecursedirs` 排除 `.venv`、`venv`、`site-packages`、`Lib`、`Scripts`、`exports`、`audits`、`.pytest_tmp`、`__pycache__` 等目录，并通过 `--basetemp=.pytest_tmp` 将测试临时文件写到仓库本地 ignored 目录。不要让 pytest 收集外部 site-packages 测试，也不要让项目测试使用 Windows 系统 Temp 目录。

cmd 用户可运行：

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
scripts\run_project_tests.bat
```

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

### Semantic Scholar enrichment skipped or rate-limited

Semantic Scholar metadata enrichment 是可选补充层，不是 primary source，也不是 ranking authority。缺少 `SEMANTIC_SCHOLAR_API_KEY` 时，enrichment 应该显示为 skipped；这不应阻止日报、周报、workflow doctor 或 CI。

如果你本地配置了 key：

- 只通过环境变量 `SEMANTIC_SCHOLAR_API_KEY` 设置；
- 不要提交 `.env` 或任何真实 API key；
- key 只应通过 `x-api-key` header 发送；
- 每秒最多 1 个请求；
- HTTP 429 / timeout / 503 应视为 retryable / non-fatal；
- `citationCount` 与 `influentialCitationCount` 只作为人工参考，不直接改变 A/B/C ranking。

手动 dry-run：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.semantic_scholar_enrichment --input data\2026-06-03.json --dry-run
```

详情见 [Semantic Scholar enrichment](semantic-scholar-enrichment.md)。

### IACR ePrint failed attempt blocks same-day retry

症状：

- Source Health 中 `iacr_eprint` 为 red；
- warning 包含 `URLError` 或 `already requested today`；
- IACR RSS 或单篇 ePrint 页面后来已经可访问，但当天本地 retry 仍然没有重新抓取；
- 典型漏报样例：`2026/1117`，`On the Secrecy of the Encapsulation Coin in ML-KEM`。

原因：IACR ePrint 采用礼貌缓存与 once-per-UTC-day guard。成功抓取会写入当天 RSS cache，后续运行复用 cache；失败抓取会留下 same-day attempt marker。为了避免高频请求，普通运行看到 attempt marker 会跳过 IACR。

手动恢复：确认这是你主动触发的一次恢复运行后，使用 `--retry-failed-sources` 允许对失败 attempt 做一次手动 retry。若目的是显式恢复 source-native latest feed，可同时使用 `--include-latest-sources`。成功 cache 仍然不会被绕过。

PowerShell：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

cmd：

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

注意：

- 这是手动恢复路径，不是后台任务。
- 不要把它放进 Windows Task Scheduler、cron、startup task 或 background service。
- 不要用它做高频循环请求。
- `--include-latest-sources` 当前用于让 IACR ePrint RSS/latest feed 的状态进入 source health，并允许对失败 attempt 做一次显式手动 latest recovery。
- 如果需要回填历史日期，优先使用明确的 backfill 流程，并在运行前检查 `git status -sb`。

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
