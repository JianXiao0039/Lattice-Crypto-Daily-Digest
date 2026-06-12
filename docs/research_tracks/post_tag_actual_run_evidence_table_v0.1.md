# Post-Tag Actual Run Evidence Table v0.1

Tag reference: `v0.4.0` -> `08c5f07967739ecd008773c4b167cd736848df88`, commit time `2026-06-11T01:05:06+08:00`.

## Summary Counts

| Evidence class | Count | Interpretation |
|---|---:|---|
| `automation_post_tag_actual` | 1 | Daily scheduled run attempt; generated artifacts were not persisted |
| `manual_post_tag_equivalent` | 1 | Manual W23 handoff replay only |
| `pre_tag_baseline` | 20 | Persisted daily JSON records through 2026-06-10 |
| `historical_ci_evidence` | 3 | Post-tag push/CI runs, not Daily/Weekly automation |
| `synthetic_test_fixture` | 0 | Not counted |
| `unknown` | 0 | None in the collected ledger |

## Material Observations

| Observation | Time | Class | Artifact | Validation | Confidence | TODO_VERIFY |
|---|---|---|---|---|---|---|
| GitHub run `27327344162` | `2026-06-11T06:04:39Z` | `automation_post_tag_actual` | ephemeral daily JSON/Markdown | generation and artifact verification passed; commit step failed | high | authenticated failure log |
| Phase 12V W23 replay | 2026-06-11 | `manual_post_tag_equivalent` | `handoffs/weekly/2026-W23-handoff-packets.json` | 20 packets from stale W23 input | high | not an actual Weekly synthesis run |
| Daily artifacts 2026-05-22 through 2026-06-10 | pre-tag | `pre_tag_baseline` | `data/YYYY-MM-DD.json` | persisted | high | none |
| GitHub CI runs `27332720722`, `27334237513`, `27336481022` | 2026-06-11 | `historical_ci_evidence` | none | CI failures with platform details available for current run | high | exact older failed logs |

The complete machine-collected ledger is reproducible with `python scripts\collect_post_tag_run_evidence.py`.
