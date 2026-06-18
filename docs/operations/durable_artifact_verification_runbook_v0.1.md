# Durable Artifact Verification Runbook v0.1

## Command

```powershell
python scripts\verify_durable_artifacts.py --date YYYY-MM-DD --week YYYY-Www --month YYYY-MM
```

Partial checks are allowed:

```powershell
python scripts\verify_durable_artifacts.py --date YYYY-MM-DD
python scripts\verify_durable_artifacts.py --week YYYY-Www
python scripts\verify_durable_artifacts.py --month YYYY-MM
```

## Daily Requirements

- `digests/YYYY-MM-DD.md` exists.
- `data/YYYY-MM-DD.json` exists.
- JSON parses.
- Markdown is non-empty and has the Daily heading/sections.
- Source-health summary exists or missing status is explicit.
- Source-starved status is explicit when record count is zero or sources failed.

## Weekly Requirements

- `digests/weekly/YYYY-Www.md` exists.
- `data/weekly/YYYY-Www.json` exists.
- JSON parses.
- Missing Daily inputs are reported.
- Source-starved Daily inputs are represented honestly.

## Monthly Requirements

- `digests/monthly/YYYY-MM.md` exists.
- `data/monthly/YYYY-MM.json` exists.
- JSON parses.
- Input Daily files are listed.
- Missing days are listed.
- `source_starved` field is present.
- Core papers include rationale/evidence basis where available.

## Result Classification

- `verified`: representative artifacts satisfy required checks.
- `partial`: some artifact classes pass and others are missing or incomplete.
- `missing`: required Markdown/JSON pair is absent.
- `invalid`: JSON is not parseable or Markdown is empty.
