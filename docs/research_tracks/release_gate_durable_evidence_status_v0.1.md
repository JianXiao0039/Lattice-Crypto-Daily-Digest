# Release Gate Durable Evidence Status v0.1

## Decision

`durable_evidence_ready` for v0.5 representative artifacts.

`insufficient_evidence` for v0.4.1 tagged commit durable Daily evidence.

## v0.5 Representative Evidence

| Artifact | Path | Status |
| --- | --- | --- |
| Daily JSON | `data/2026-06-15.json` | exists, non-empty, parseable |
| Daily Markdown | `digests/2026-06-15.md` | exists, non-empty |
| Weekly JSON | `data/weekly/2026-W25.json` | exists, non-empty, parseable |
| Weekly Markdown | `digests/weekly/2026-W25.md` | exists, non-empty |
| Monthly JSON | `data/monthly/2026-06.json` | exists, non-empty, parseable |
| Monthly Markdown | `digests/monthly/2026-06.md` | exists, non-empty |
| Source-health audit | `audits/source-health/2026-06-15.json` | exists, non-empty, parseable |
| Reading queue | `state/reading-queue.json` | exists, non-empty, parseable |
| Reading dashboard | `exports/reading-queue/reading-dashboard.md` | exists, non-empty |
| Obsidian notes | `exports/obsidian-paper-notes/` | present |

Verifier command:

```powershell
python scripts\verify_durable_artifacts.py --date 2026-06-15 --week 2026-W25 --month 2026-06
```

Result: `verified`.

## v0.4.1 Tagged Commit Evidence

The v0.4.1 target commit does not contain the representative v0.5 Daily pair or current durable evidence manifest. It remains blocked as historical v0.4.1 evidence.
