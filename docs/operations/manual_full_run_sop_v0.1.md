# Manual Full Run SOP v0.1

Status: `daily_weekly_monthly_manual_workflow_ready`.

A full manual run is a foreground command sequence. It is not a scheduled task, watcher, cron job, background service, startup task, or automatic future run.

## Pre-Run

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
git status -sb
python --version
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
```

## Daily

```powershell
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

## Weekly

```powershell
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
python -m lattice_digest.workflow weekly --low-load --skip-hygiene --execute
```

## Monthly

```powershell
python -m lattice_digest.monthly_synthesis --month YYYY-MM
```

## Source Health and Durable Evidence

```powershell
python scripts\probe_source_health.py --low-load
python scripts\verify_durable_artifacts.py --date YYYY-MM-DD --week YYYY-Www --month YYYY-MM
```

## Exports and Quality Audit

```powershell
python scripts\export_reading_queue.py --latest
python scripts\export_obsidian_notes.py --latest
python scripts\audit_monthly_rationale_quality.py --latest
```

## Optional Engineering Checks

```powershell
scripts\run_project_tests.bat
python scripts\check_release_hygiene.py
git diff --check
git status -sb
```

End with the manual operation report template. Do not stage, commit, push, tag, or create scheduled automation.
