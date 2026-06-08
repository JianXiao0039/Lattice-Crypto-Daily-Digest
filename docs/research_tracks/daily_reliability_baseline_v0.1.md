# Daily Reliability Baseline v0.1

Status: frozen public baseline for the current automation module tuning cycle.

# Freeze Date

- `2026-06-08`

# Current Baseline

| Field | Value |
| --- | --- |
| `python_version` | `3.15.0b2` |
| `package_version` | `0.3.3` |
| `latest_daily_artifact` | `data\2026-06-08.json` |
| `latest_weekly_artifact` | `data\weekly\2026-W23.json` |
| `latest_handoff_artifact` | `handoffs\weekly\2026-W23-handoff-packets.json` |
| `source_total_count` | `6` |
| `source_green_count` | `2` |
| `source_yellow_count` | `4` |
| `source_red_count` | `0` |
| `source_reachability_rate` | `1.0` |
| `retryable_error_count` | `1` |
| `digest_record_count` | `6` |
| `final_record_count` | `6` |
| `high_priority_count` | `5` |
| `iacr_latest_status` | `fetched` |
| `iacr_latest_records` | `100` |
| `semantic_scholar_key_present_boolean` | `True` |
| `semantic_scholar_key_length_only_if_safe` | `44` |
| `semantic_scholar_enrichment_status` | `no_candidates_to_enrich` |
| `source_starved_true_false` | `False` |
| `empty_digest_reason` | `non_empty` |
| `weekly_handoff_candidate_count` | `20` |
| `weekly_handoff_source_starved_true_false` | `False` |
| `validation_passed` | `True` |
| `manual_recovery_needed` | `False` |

# Interpretation

- This baseline is usable but not all-green.
- DBLP and several non-primary sources are still yellow in the persisted daily artifact.
- IACR latest is part of the usable baseline.
- Semantic Scholar remains optional/advisory.
