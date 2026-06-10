# Daily Success Metrics v0.1

Status: public metric definition doc.

# Metrics

| Metric | Meaning |
| --- | --- |
| `source_reachability_rate` | reachable sources / configured sources |
| `source_green_count` | count of green sources in source health |
| `source_red_count` | count of red sources in source health |
| `retryable_error_count` | sources marked retryable in source health |
| `digest_record_count` | number of records in latest daily JSON |
| `final_record_count` | final retained records after filtering/scoring |
| `high_priority_count` | count of top-priority papers if available |
| `IACR_latest_records` | latest feed record count for IACR if reported |
| `Semantic_Scholar_enrichment_available` | whether enrichment metadata is available for candidates |
| `source_starved` | true when `0 records + all-red` or equivalent degraded source state |
| `empty_digest_reason` | classified explanation for empty output |
| `generated_artifacts_present` | whether expected daily JSON/Markdown exist |
| `validation_passed` | whether env/doctor/tests/hygiene checks pass |
| `manual_recovery_needed` | whether operator should run bounded manual recovery |

