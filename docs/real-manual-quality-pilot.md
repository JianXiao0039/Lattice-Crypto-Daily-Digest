# Real Manual Quality-first Pilot

This document defines the real manual pilot mode for quality-first content generation. It does not add automation and does not change workflow semantics.

中文说明：本 pilot 面向“用户手动触发时优先质量”的真实使用方式。低负载、dry-run、no-network/offline 是 fallback 或 diagnostic modes，不是高质量内容生成的默认目标。

## 1. Manual-only boundary

Manual-only usage is mandatory.

For Codex copy/paste usage, use the manual-only prompt in [Manual Codex Quality Run Prompt](manual-codex-quality-run-prompt.md). Do not place that prompt into a recurring automation.

No scheduled automation is configured. Do not add:

- Windows Task Scheduler integration
- cron jobs
- background service
- startup task
- watcher
- automatic runs

Every command in this pilot must be started by the user manually from PowerShell or cmd.

## 2. Quality-first manual run philosophy

This is the quality-first manual run mode for real content generation.

When the user manually triggers a real content-generation run, quality is preferred over minimum load. This means:

- use normal manual execution for real daily / weekly / full research outputs;
- allow network access for real digest generation unless diagnosing connectivity;
- run validation before publishing;
- review generated artifacts before committing anything;
- keep low-load, dry-run, and no-network as fallback modes.

Low-load is fallback, not default for quality generation. Dry-run is fallback or planning mode. No-network/offline is diagnostic mode or travel mode.

## 3. Recommended high-quality manual commands

PowerShell:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
python -m lattice_digest.workflow daily --execute
python -m lattice_digest.workflow weekly --execute --generate-notes
python -m lattice_digest.workflow full --execute --generate-notes
```

cmd:

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
python -m lattice_digest.workflow daily --execute
python -m lattice_digest.workflow weekly --execute --generate-notes
python -m lattice_digest.workflow full --execute --generate-notes
```

Expected behavior:

- commands are manually triggered;
- write commands only run because `--execute` is explicit;
- notes are generated only because `--generate-notes` is explicit;
- generated artifacts must not be committed without review.

## 4. When to use low-load

Use `--low-load` when:

- using a laptop on battery;
- avoiding high CPU or network pressure;
- doing a quick daily check;
- validating workflow planning without wanting a full quality-first run.

Example:

```powershell
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
```

## 5. When to use dry-run

Use dry-run when:

- checking planned steps;
- reviewing expected output paths;
- preparing a manual run;
- diagnosing command behavior.

Workflow commands default to dry-run unless `--execute` is explicitly supplied.

## 6. When to use no-network / offline

Use `--no-network` or `--offline` when:

- external APIs are rate-limited;
- the machine is offline;
- checking local workflow behavior;
- avoiding fetch steps during troubleshooting.

Example:

```powershell
python -m lattice_digest.workflow daily --no-network --skip-hygiene
python -m lattice_digest.workflow daily --offline --skip-hygiene
```

## 7. What not to automate

Do not run these from any scheduler, startup task, background process, watcher, or automatic local service:

- `python -m lattice_digest.workflow daily --execute`
- `python -m lattice_digest.workflow weekly --execute --generate-notes`
- `python -m lattice_digest.workflow full --execute --generate-notes`
- any manual GitHub publish helper

If a command writes files, it should be visible, intentional, and reviewable.
