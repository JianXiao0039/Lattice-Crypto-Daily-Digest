# Daily Radar Manual Runbook v0.1

## Purpose

Generate a manual Daily lattice/PQC paper radar artifact without changing ranking, taxonomy, source selection, or workflow scheduling.

## Pre-Run Checks

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
git status -sb
python --version
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
```

Report existing uncommitted changes before generating new files.

## Latest 36h Run

```powershell
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

Expected outputs:

- `digests/YYYY-MM-DD.md`
- `data/YYYY-MM-DD.json`
- `papers.db`

Do not stage or commit these outputs from this runbook.

## Exact Date Run

```powershell
python -m lattice_digest.run --date YYYY-MM-DD --output markdown,json --send none
```

Use this for manual recovery/backfill of one Asia/Singapore calendar date.

## Low-Load Daily Planning

The workflow command supports low-load planning and execution:

```powershell
python -m lattice_digest.workflow daily --low-load --skip-hygiene
python -m lattice_digest.workflow daily --low-load --skip-hygiene --execute
```

Low-load mode records a conservative workflow profile. It is not a bypass mechanism.

## Review Checklist

- Markdown exists and has Daily radar sections.
- JSON exists and is parseable.
- Source-health summary is present or explicitly marked missing.
- Source-starved days are stated honestly.
- A/B papers include recommendation rationale, evidence basis, reading action, and `TODO_VERIFY`.
- Keyword hits are supporting evidence, not the entire rationale.

## Failure Handling

If source failures dominate, do not claim that no relevant papers exist. Mark the run as source-starved or degraded, then run:

```powershell
python scripts\probe_source_health.py --low-load
```
