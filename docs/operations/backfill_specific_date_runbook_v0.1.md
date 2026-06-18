# Backfill Specific Date Runbook v0.1

## Purpose

Recover or regenerate one Daily artifact for one Asia/Singapore calendar date.

## Preflight

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
git status -sb
python -m lattice_digest.workflow doctor
Test-Path data\YYYY-MM-DD.json
Test-Path digests\YYYY-MM-DD.md
```

If artifacts already exist, report their presence. Do not overwrite authoritative outputs unless the user explicitly authorizes `--force`.

## Backfill Command

```powershell
python -m lattice_digest.run --date YYYY-MM-DD --output markdown,json --send none --run-mode backfill --quality-status authoritative_backfill
```

If safe latest-source recovery is needed:

```powershell
python -m lattice_digest.run --date YYYY-MM-DD --output markdown,json --send none --run-mode backfill --quality-status authoritative_backfill --retry-failed-sources --include-latest-sources
```

## Verification

```powershell
python scripts\verify_durable_artifacts.py --date YYYY-MM-DD
```

Manual checks:

- `data/YYYY-MM-DD.json` exists and parses.
- `digests/YYYY-MM-DD.md` exists and is non-empty.
- Source-health status is explicit.
- Source-starved status is explicit when applicable.
- No private path is touched.
