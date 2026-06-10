# Phase 12Q Backfill Audit: 2026-06-04 to 2026-06-10

生成日期：2026-06-10

# Audit Result

- window_complete: `False`
- daily_decision: `insufficient_evidence`
- weekly_decision: `keep_active_with_source_starved_warning`
- full_manual_quality_run_decision: `keep_paused`

| date | digest MD | data JSON | records | final | high | source health | green/yellow/red | source-starved | IACR latest | Semantic Scholar | commit status | TODO_VERIFY |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-04 | yes | yes | 0 | 0 | 0 | yes | 0/0/6 | true | failed/0 | source_red | untracked_or_not_committed | source-starved run; do not interpret as no relevant papers |
| 2026-06-05 | yes | yes | 0 | 0 | 0 | yes | 0/0/6 | true | failed/0 | source_red | untracked_or_not_committed | source-starved run; do not interpret as no relevant papers |
| 2026-06-06 | no | no | n/a | n/a | n/a | no | 0/0/0 | false | missing/0 | missing | missing | data JSON missing, digest Markdown missing |
| 2026-06-07 | yes | yes | 0 | 0 | 0 | yes | 0/0/6 | true | failed/0 | source_red | untracked_or_not_committed | source-starved run; do not interpret as no relevant papers |
| 2026-06-08 | yes | yes | 6 | 6 | 5 | yes | 2/4/0 | false | fetched/100 | key_used | untracked_or_not_committed | none |
| 2026-06-09 | no | no | n/a | n/a | n/a | no | 0/0/0 | false | missing/0 | missing | missing | data JSON missing, digest Markdown missing |
| 2026-06-10 | yes | yes | 18 | 18 | 9 | yes | 2/4/0 | false | fetched/100 | key_used | untracked_or_not_committed | none |

# Interpretation

- The period is not complete enough for a clean GitHub submission claiming coverage through 2026-06-10.
- The missing days should be backfilled or explicitly documented as unavailable before submission.
- The source-starved days must remain labeled as source-starved.
