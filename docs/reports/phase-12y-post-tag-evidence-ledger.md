# Phase 12Y: Post-Tag Evidence Ledger

## Reference

- Tag: `v0.4.0`
- Target: `08c5f07967739ecd008773c4b167cd736848df88`
- Target time: `2026-06-11T01:05:06+08:00`
- Collection method: Git metadata, repository artifacts, public GitHub Actions API, and prior Phase 12V validation evidence.

## Counts

| Evidence class | Count |
|---|---:|
| `automation_post_tag_actual` | 1 |
| `manual_post_tag_equivalent` | 1 |
| `pre_tag_baseline` | 20 |
| `historical_ci_evidence` | 3 |
| `synthetic_test_fixture` | 0 |
| `unknown` | 0 |

## Ledger

| Observation ID | Date/time | Evidence class | Artifact | Commit/run | Validation | Confidence | TODO_VERIFY |
|---|---|---|---|---|---|---|---|
| `github-run-27327344162` | `2026-06-11T06:04:39Z` | `automation_post_tag_actual` | ephemeral `data/YYYY-MM-DD.json`, `digests/YYYY-MM-DD.md` | run `27327344162`, commit `08c5f079` | tests, generation, and artifact verification passed; commit step failed | high | exact commit error; source-health and record counts |
| `manual-weekly-handoff-phase-12v` | 2026-06-11 | `manual_post_tag_equivalent` | `handoffs/weekly/2026-W23-handoff-packets.json` | manual Phase 12V | 20 packets from pre-tag W23 input | high | not an actual Weekly run; 5/7 coverage |
| `daily-artifact-2026-05-22` through `daily-artifact-2026-06-10` | pre-tag | `pre_tag_baseline` | 20 daily JSON artifacts | repository history | persisted | high | none |
| `github-run-27332720722` | `2026-06-11T08:01:43Z` | `historical_ci_evidence` | none | CI run | failure | high | exact failed log |
| `github-run-27334237513` | `2026-06-11T08:30:26Z` | `historical_ci_evidence` | none | CI run | failure | high | exact failed log |
| `github-run-27336481022` | `2026-06-11T09:12:23Z` | `historical_ci_evidence` | none | current-head CI | Ubuntu pass, Windows test failure | high | authenticated Windows failure log |

## Evidence Limits

- File modification time was not used alone to prove automation execution.
- The pre-tag daily artifacts are not counted as post-tag actual evidence.
- Connectivity probes are not counted as Daily automation runs.
- The manual W23 handoff replay is not counted as Weekly Public Synthesis automation.
- Public API metadata verifies run and step states, but exact failed logs require authenticated GitHub access.

Reproduce the expanded ledger with:

```powershell
python scripts\collect_post_tag_run_evidence.py
```
