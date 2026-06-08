# Daily Digest Success Metrics v0.2

Status: public metric definition doc.

# Metric Provenance Rule

Unless stated otherwise:

- source status counts come from latest daily `source_health`;
- reachability counts come from the most recent probe run;
- weekly packet counts come from the latest weekly handoff JSON.

# Metrics

| Metric | Meaning |
| --- | --- |
| `run_id` | unique dashboard run identifier |
| `run_type` | dashboard / probe / manual recovery / weekly handoff replay |
| `run_time` | UTC timestamp |
| `python_version` | runtime version |
| `package_version` | package version |
| `source_total_count` | number of source-health entries in latest daily artifact |
| `source_green_count` | count of green sources in latest daily artifact |
| `source_yellow_count` | count of yellow sources in latest daily artifact |
| `source_red_count` | count of red sources in latest daily artifact |
| `source_reachability_rate` | reachable probe endpoints / probed endpoints |
| `retryable_error_count` | retryable failures observed in the probe run |
| `non_retryable_error_count` | non-retryable failures observed in the probe run |
| `digest_record_count` | raw count of records in latest daily JSON |
| `final_record_count` | final retained record count reported by latest daily metadata |
| `high_priority_count` | records that are A-label or otherwise marked for immediate reading |
| `iacr_latest_status` | latest IACR feed status from daily source health |
| `iacr_latest_records` | latest IACR feed record count |
| `semantic_scholar_key_present_boolean` | safe key presence boolean |
| `semantic_scholar_key_length_only_if_safe` | safe key length only |
| `semantic_scholar_enrichment_status` | missing_key / key_present / auth_failure / rate_limit / network_failure / no_candidates_to_enrich / enrichment_successful |
| `source_starved_true_false` | whether the latest daily artifact is source-starved |
| `empty_digest_reason` | classified reason when daily record count is 0 |
| `weekly_handoff_candidate_count` | number of packets in latest weekly handoff |
| `weekly_handoff_source_starved_true_false` | whether latest weekly handoff should be interpreted as source-starved |
| `generated_artifacts_present` | whether expected latest daily JSON/Markdown exist |
| `validation_passed` | whether dashboard generation and required artifact parsing succeeded |
| `manual_recovery_needed` | whether operator should run bounded manual recovery |
| `notes` | short human-readable observations |
| `TODO_VERIFY` | unresolved follow-up items |
