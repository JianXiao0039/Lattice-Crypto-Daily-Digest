# Full Radar Manual Runbook v0.1

## Definition

A full radar run is a manual foreground sequence. It is not a scheduled task, watcher, background service, cron job, or automatic future run.

## Sequence

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
git status -sb
python --version
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
```

Daily:

```powershell
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

Weekly:

```powershell
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
python -m lattice_digest.workflow weekly --low-load --skip-hygiene --execute
```

Monthly:

```powershell
python -m lattice_digest.monthly_synthesis --month YYYY-MM
```

Source health:

```powershell
python scripts\probe_source_health.py --low-load
```

Durable artifacts:

```powershell
python scripts\verify_durable_artifacts.py --date YYYY-MM-DD --week YYYY-Www --month YYYY-MM
```

Exports:

```powershell
python scripts\export_reading_queue.py --latest
python scripts\export_obsidian_notes.py --latest
```

Checks:

```powershell
scripts\run_project_tests.bat
python scripts\check_release_hygiene.py
git diff --check
git status -sb
```

## Policy

This runbook never authorizes Git write operations, tag operations, private workspace access, or scheduled automation.
