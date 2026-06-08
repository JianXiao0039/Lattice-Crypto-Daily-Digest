# Baseline vs Current Reliability Diff v0.1

基线来源：`docs/reports/phase-12n-reliability-baseline-freeze.md`

当前主比较口径：artifact-only（避免瞬时探测抖动干扰）

| Metric | Baseline | Current | Status | Interpretation | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- |
| `source_total_count` | `6` | `6` | `unchanged` | 无回归 | 否 |
| `source_green_count` | `2` | `2` | `unchanged` | 无回归 | 否 |
| `source_yellow_count` | `4` | `4` | `unchanged` | 仍有降级源 | 否 |
| `source_red_count` | `0` | `0` | `unchanged` | 非 all-red | 否 |
| `source_reachability_rate` | `1.0` | `N/A` | `unknown_due_to_missing_artifacts` | 需要 live probe | 是 |
| `retryable_error_count` | `1` | `1` | `unchanged` | 可重试告警未变 | 否 |
| `digest_record_count` | `6` | `6` | `unchanged` | 无回归 | 否 |
| `final_record_count` | `6` | `6` | `unchanged` | 无回归 | 否 |
| `high_priority_count` | `5` | `5` | `unchanged` | 无回归 | 否 |
| `iacr_latest_status` | `fetched` | `fetched` | `unchanged` | latest 稳定 | 否 |
| `iacr_latest_records` | `100` | `100` | `unchanged` | latest 记录稳定 | 否 |
| `semantic_scholar_enrichment_status` | `no_candidates_to_enrich` | `no_candidates_to_enrich` | `unchanged` | artifact 无回归 | 否 |
| `source_starved_true_false` | `False` | `False` | `unchanged` | guard 未触发 | 否 |
| `empty_digest_reason` | `non_empty` | `non_empty` | `unchanged` | 非空 | 否 |
| `weekly_handoff_candidate_count` | `20` | `20` | `unchanged` | handoff 稳定非空 | 否 |
| `weekly_handoff_source_starved_true_false` | `False` | `False` | `unchanged` | 无 source-starved 周视图 | 否 |
| `generated_artifacts_present` | `N/A` | `True` | `unknown_due_to_missing_artifacts` | 冻结基线未显式记录 | 是 |
| `validation_passed` | `True` | `True` | `unchanged` | 无回归 | 否 |
| `manual_recovery_needed` | `False` | `False` | `unchanged` | 当前不需恢复 | 否 |

## Live Probe Supplement

- `source_reachability_rate`：`0.833`
- `semantic_scholar_enrichment_status`：`rate_limit`
- 解读：repo 产物层面稳定，但 live probe 暴露出富化链路存在瞬时不稳定。
