# Date-Targeted Backfill Usage v0.1

## Purpose

Use `--date` to generate the daily Markdown and JSON artifacts for exactly one Asia/Singapore calendar date.

## Syntax

```powershell
python -m lattice_digest.run --date YYYY-MM-DD --output markdown,json --send none
```

The date must be a valid zero-padded ISO date. The output names are `digests/YYYY-MM-DD.md` and `data/YYYY-MM-DD.json`.

## Examples

```powershell
python -m lattice_digest.run --date 2026-06-06 --output markdown,json --send none --retry-failed-sources --include-latest-sources
python -m lattice_digest.run --date 2026-06-09 --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

## Interaction With --since

`--date` and `--since` are mutually exclusive. Combining them is rejected by the CLI. Existing commands that use `--since` retain their previous behavior, and omitting both options keeps the default 36-hour lookback.

The older `--target-date` option remains available for compatibility. Do not combine it with `--date`.

## Source-Starved Behavior

A date-targeted run must still write valid Markdown and JSON when zero records are found. When all sources are red or unavailable, the artifacts must preserve source-health details and must be interpreted as source-starved, not as evidence that no relevant papers exist.

## Recovery Usage

1. Run `python -m lattice_digest.workflow doctor`.
2. Use `--retry-failed-sources` only for an explicit manual retry.
3. Use `--include-latest-sources` when the IACR latest-source recovery path is required.
4. Inspect source health, IACR latest status, Semantic Scholar status, and record count.
5. Regenerate the weekly handoff only after the daily artifacts exist.

## What Not To Do

- Do not combine `--date` and `--since`.
- Do not interpret an all-red zero-record run as normal discovery success.
- Do not print API keys or `.env` contents.
- Do not create retry schedules or background loops.
- Do not automatically stage, commit, push, or tag generated artifacts.
- Do not write public research outputs into private application or ResearchArtifacts workspaces.

