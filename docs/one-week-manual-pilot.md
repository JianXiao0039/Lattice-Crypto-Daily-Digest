# One-week Manual Pilot

本计划用于连续 7 天手动验收 `lattice-crypto-daily-digest` 的低负载研究工作流。它不是新功能设计，也不是自动化部署说明，而是一份人工试运行 checklist。

English summary: this pilot is a manual-only acceptance routine. No scheduled automation is configured, and no cron, Windows Task Scheduler, background daemon, startup task, or automatic run should be added.

## 1. Purpose

目标是在一周内确认：

- 手动 workflow command center 可用。
- dry-run default 不写文件。
- low-load mode 适合笔记本和日常轻量检查。
- no-network / offline usage 能避免网络抓取。
- reading queue manual statuses should be preserved。
- generated artifacts must not be committed。
- source health、advisor/progress 输出对研究工作有帮助。

## 2. Manual-only principle

本 pilot 只允许用户手动运行命令。不要配置：

- Windows Task Scheduler
- cron
- background service
- startup task
- watcher
- automatic scheduled run

No scheduled automation is configured. 如果某一步看起来需要自动运行，应先写入 issue log，而不是添加后台任务。

## 3. Working directory

PowerShell：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
```

cmd：

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
```

## 4. Recommended 7-day routine

### Day 1: baseline status / doctor

Purpose: establish a read-only baseline.

PowerShell：

```powershell
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
git status -sb
```

Expected behavior:

- `status` is read-only.
- `doctor` is read-only.
- No files are written.
- Git status does not show forbidden artifacts staged.

### Day 2: daily low-load dry-run

```powershell
python -m lattice_digest.workflow daily --low-load --skip-hygiene
```

Expected behavior:

- dry-run default is active.
- low-load mode appears in the planned steps.
- No digest, export, audit, or state files are written.

### Day 3: no-network check

```powershell
python -m lattice_digest.workflow daily --no-network --skip-hygiene
python -m lattice_digest.workflow daily --offline --skip-hygiene
```

Expected behavior:

- Network fetch steps are skipped or planned as skipped.
- Existing local state may be inspected, but no external source should be fetched.
- Use this when traveling, offline, or avoiding extra load.

### Day 4: weekly low-load dry-run

```powershell
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
```

Expected behavior:

- Weekly workflow remains dry-run by default.
- Planned outputs are listed.
- No files are written.
- Obsidian notes are not generated.

### Day 5: weekly low-load execute

Run only after checking Day 4 output:

```powershell
python -m lattice_digest.workflow weekly --execute --low-load --skip-hygiene
```

Expected behavior:

- Weekly outputs may be written under ignored generated-artifact paths.
- Obsidian notes are not generated unless `--generate-notes` is explicitly provided.
- reading queue manual statuses should be preserved.

### Day 6: optional notes generation check

Only if paper-note scaffold output is intentionally desired:

```powershell
python -m lattice_digest.workflow weekly --execute --low-load --generate-notes --skip-hygiene
```

Expected behavior:

- Notes are generated only because `--generate-notes` is explicit.
- Review generated files before keeping them.
- Do not commit generated notes by default.

### Day 7: review and cleanup

```powershell
git status -sb
git clean -ndX
python scripts\check_release_hygiene.py
```

Expected behavior:

- Generated artifacts remain ignored.
- No forbidden artifacts are staged.
- Source health output is understandable enough to decide whether a run is reliable.
- Any confusing behavior is recorded in `docs/pilot-issue-log-template.md`.

## 5. What not to run automatically

Do not run these from a scheduler, startup script, background service, cron job, or Windows Task Scheduler:

- `python -m lattice_digest.workflow daily`
- `python -m lattice_digest.workflow weekly`
- `python -m lattice_digest.workflow full`
- `python -m lattice_digest.run`
- PowerShell wrappers that generate digests, notes, exports, or progress logs

All pilot commands are user-triggered. This keeps machine load predictable and makes every write step auditable.

## 6. Pilot notes

For every issue, record:

- command run
- expected behavior
- actual behavior
- severity
- reproduction steps
- suspected cause
- proposed fix

Use `docs/pilot-issue-log-template.md` as the template.
