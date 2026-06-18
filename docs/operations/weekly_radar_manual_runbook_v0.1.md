# Weekly Radar Manual Runbook v0.1

## Purpose

Generate Weekly synthesis from existing Daily evidence while preserving Daily ranking/order semantics.

## Pre-Run Checks

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
git status -sb
python --version
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
```

## Dry Run First

```powershell
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
```

Review planned date coverage and missing days before execution.

## Execute

```powershell
python -m lattice_digest.workflow weekly --low-load --skip-hygiene --execute
```

Optional date range when needed:

```powershell
python -m lattice_digest.workflow weekly --from-date YYYY-MM-DD --to-date YYYY-MM-DD --low-load --skip-hygiene --execute
```

Expected outputs:

- `data/weekly/YYYY-Www.json`
- `digests/weekly/YYYY-Www.md`
- handoff files when weekly handoff generation is enabled by existing workflow behavior

## Review Checklist

- Weekly Markdown and JSON exist.
- JSON is parseable.
- Missing Daily files are reported.
- Source-starved Daily inputs are not interpreted as no relevant research.
- Top papers include compact rationale and `TODO_VERIFY`.
- Existing ranking, class labels, and order are not changed by the operator.
