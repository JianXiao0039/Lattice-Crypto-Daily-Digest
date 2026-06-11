# Source Failure Budget Schema v0.1

The schema is frozen for observation consistency. Thresholds are not frozen.

| Field | Definition |
|---|---|
| `observation_period` | dates and release/tag boundary covered |
| `evidence_type` | `post_tag_actual`, `pre_tag_baseline`, or `manual_diagnostic` |
| `daily_artifact_completeness` | days with both expected Markdown and JSON divided by observed days |
| `source_reachability` | green plus yellow source entries divided by source entries |
| `all_red_run_count` | runs where every recorded source is red |
| `source_starved_run_count` | zero-record runs with all sources red/unreachable |
| `retryable_failure_count` | source entries marked retryable |
| `non_retryable_failure_count` | failed source entries not marked retryable |
| `iacr_latest_usable_rate` | runs with IACR latest fetched or cache hit divided by observed runs |
| `semantic_scholar_enrichment_usable_rate` | runs with verified usable enrichment divided by observed runs |
| `weekly_coverage_completeness` | loaded weekly days divided by expected weekly days |
| `handoff_traceability` | handoff references the exact weekly source artifact |
| `windows_ci_status` | latest relevant Windows job status |
| `ubuntu_ci_status` | latest relevant Ubuntu job status |
| `confidence_level` | low, provisional, or mature based on evidence diversity |
| `TODO_VERIFY` | unresolved evidence and classification gaps |

Reliability metrics must not be used as paper relevance or ranking scores.
