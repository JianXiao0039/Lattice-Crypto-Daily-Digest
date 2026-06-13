# Phase 13D Shadow Pilot Log

## Inputs

- Phase 13C annotation pack: 25 records.
- Repository-grounded broader pool: 62 unique records.
- Valid human-gold labels: 0.
- Experimental rules: `experiments/v0_5_shadow_track_rules.json`.

## Results

| Measure | Result |
|---|---:|
| Production-shadow exact agreement | 27 |
| Total disagreement | 35 |
| Primary-track disagreement | 23 |
| Production labeled / shadow irrelevant | 10 |
| Secondary-track disagreement | 2 |
| Agreement rate | 43.55% |
| Explanation completeness | 100% |
| Strict metadata insufficiency | 0% |

## Error Signals

- Track D bucket drift: 21.
- Track B under-coverage: 6.
- Shadow under-coverage: 10.
- Codex-review diagnostic false-positive assignments: 22.
- Codex-review diagnostic false-negative assignments: 19.
- Ambiguous Codex-reviewed cases: 7.

These counts are not human-gold error rates.

## Decisions

- Shadow pilot: `shadow_pilot_complete_without_gold_metrics`.
- Shadow-mode gate: `manual_shadow_pilot_only_pending_user_annotation`.
- Production gate: `blocked_by_multiple_conditions`.
