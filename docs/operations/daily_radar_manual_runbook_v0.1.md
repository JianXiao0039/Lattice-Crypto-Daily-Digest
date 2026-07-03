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

- `digests/YYYY/daily/YYYY-MM-DD.md`
- `data/YYYY/daily/YYYY-MM-DD.json`
- `papers.db`

Do not stage or commit these outputs from this runbook.

## Scratch QA Run

Use `--output-root` when you need a fresh Daily artifact for manual QA without
touching repository-authoritative `data/`, `digests/`, `papers.db`, or
source-health outputs:

```powershell
python -m lattice_digest.run --since 36h --output markdown,json --send none --output-root D:\Code\CodexProjects\_lattice_digest_scratch_daily_qa\post_fix_sample
```

Expected scratch outputs:

- `<output-root>\data\YYYY\daily\YYYY-MM-DD.json`
- `<output-root>\digests\YYYY\daily\YYYY-MM-DD.md`
- `<output-root>\papers.db`
- `<output-root>\audits\source-health\YYYY-MM-DD.json`
- `<output-root>\audits\source-health\YYYY-MM-DD.md`

Scratch output uses the same collection, ranking, freshness, venue/CCF,
bilingual metadata, recommendation metadata, and source-health logic as the
normal Daily run. It does not require `--force` because existing authoritative
repository outputs are not consulted or overwritten.

By default, artifact reads are canonical-only. Legacy read fallback is temporary
and requires explicit process-scoped opt-in:

```powershell
$env:LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK = "1"
```

This opt-in never changes Daily writer output paths.

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
