# Monthly Radar Manual Runbook v0.1

## Purpose

Generate manual Monthly lattice paper radar synthesis from existing Daily/Weekly artifacts.

## Command Availability

Monthly workflow is currently a module entrypoint, not a `lattice_digest.workflow` subcommand.

Supported command:

```powershell
python -m lattice_digest.monthly_synthesis --month YYYY-MM
```

Dry-run command:

```powershell
python -m lattice_digest.monthly_synthesis --month YYYY-MM --dry-run
```

## Expected Outputs

- `data/monthly/YYYY-MM.json`
- `digests/monthly/YYYY-MM.md`

## Required Sections

- Executive Summary
- Core Papers of the Month
- Direction Trends
- Reading Priority
- Source Health Summary
- `TODO_VERIFY`

## Review Checklist

- Input Daily files and missing days are listed.
- Duplicate papers are deduplicated.
- Core papers preserve existing score/order semantics.
- Recommendation rationale includes problem, method, contribution, radar relevance, evidence basis, and caveat where available.
- Title-only records do not receive invented method or contribution details.
- Monthly source-health summary is present or explicitly marked missing.
