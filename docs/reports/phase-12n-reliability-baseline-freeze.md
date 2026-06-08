# Phase 12N Reliability Baseline Freeze

生成日期：2026-06-08

# Baseline Source

This baseline is frozen from persisted repository artifacts, not from a fresh live network probe.

Source command:

```powershell
python scripts\print_current_reliability_baseline.py
```

# Frozen Baseline

```json
{
  "baseline_date": "2026-06-08",
  "python_version": "3.15.0b2",
  "package_version": "0.3.3",
  "active_automation_modules": [
    "Daily Public Digest Run",
    "Weekly Public Synthesis Run"
  ],
  "paused_automation_modules": [
    "Full Manual Quality Run"
  ],
  "latest_daily_artifact": "data\\2026-06-08.json",
  "latest_weekly_artifact": "data\\weekly\\2026-W23.json",
  "latest_handoff_artifact": "handoffs\\weekly\\2026-W23-handoff-packets.json",
  "source_total_count": 6,
  "source_green_count": 2,
  "source_yellow_count": 4,
  "source_red_count": 0,
  "source_reachability_rate": 1.0,
  "retryable_error_count": 1,
  "digest_record_count": 6,
  "final_record_count": 6,
  "high_priority_count": 5,
  "iacr_latest_status": "fetched",
  "iacr_latest_records": 100,
  "semantic_scholar_key_present_boolean": true,
  "semantic_scholar_key_length_only_if_safe": 44,
  "semantic_scholar_enrichment_status": "no_candidates_to_enrich",
  "source_starved_true_false": false,
  "empty_digest_reason": "non_empty",
  "weekly_handoff_candidate_count": 20,
  "weekly_handoff_source_starved_true_false": false,
  "validation_passed": true,
  "manual_recovery_needed": false
}
```

# Interpretation

- The baseline is degraded-but-usable, not all-green.
- The baseline is not source-starved.
- IACR latest is currently healthy enough to be part of the baseline.
- Semantic Scholar is optional and advisory-only; baseline state is `no_candidates_to_enrich`.
- Weekly handoff is available and non-empty.

# Freeze Rule

Do not silently replace this baseline with a live-probe snapshot unless the user intentionally refreshes it after observing new Daily / Weekly automation runs.
