# Phase 14H Cross-Operator Drift Fix Patch

## Decision

- Drift fix: `cross_operator_drift_fix_ready`.
- DeepSeek-Claude readiness: `deepseek_claude_prompt_ready_for_second_dry_run`.
- Kimi Code readiness: `kimi_code_prompt_ready_for_second_dry_run`.
- Fallback acceptance: `fallback_acceptance_blocked_until_actual_runs`.
- Production gate: `eligible_for_phase_14i_second_dry_run`.

## Phase 14G Dependency Status

Phase 14G reports and operations docs are present. The grounded Phase 14G result is:

- Codex ran successfully with degraded but explicit source health.
- DeepSeek-Claude was not run.
- Kimi Code was not run.
- Full cross-operator parity cannot be claimed.

## Files Inspected

- `docs/reports/phase-14g-cross-operator-dry-run-drill.md`
- `docs/reports/phase-14g-codex-dry-run-log.md`
- `docs/reports/phase-14g-deepseek-claude-dry-run-log.md`
- `docs/reports/phase-14g-kimi-code-dry-run-log.md`
- `docs/reports/phase-14g-cross-operator-output-comparison.md`
- `docs/reports/phase-14g-operator-divergence-and-remediation.md`
- `docs/operations/deepseek_claude_dry_run_prompt_v0.1.md`
- `docs/operations/kimi_code_dry_run_prompt_v0.1.md`
- `docs/operations/codex_dry_run_prompt_v0.1.md`
- `docs/operations/cross_operator_output_comparison_template_v0.1.md`
- `docs/operations/cross_operator_fallback_acceptance_gate_v0.1.md`

## Actual 14G Drift Summary

The current drift is `not_run_drift`, not a proven three-way output mismatch.

- Codex: `run_ok_with_degraded_sources`.
- DeepSeek-Claude: `not_run`.
- Kimi Code: `not_run`.

## Codex Result Summary

Codex generated or verified Daily 2026-06-21 artifacts, performed a weekly dry-run only, refreshed Monthly 2026-06 artifacts, verified durable Daily/Weekly/Monthly evidence, exported reading queue and Obsidian notes, and ran monthly rationale quality audit.

Observed source health:

- arXiv: rate-limited in the first 14G run, later low-load probe ok.
- DBLP: SSL/TLS failure.
- Semantic Scholar: rate-limited.
- Crossref: green.
- IACR RSS: returned records.
- OpenAlex: returned a low-load result.

Monthly rationale quality:

- `monthly_rationale_quality_passed_with_limits`.
- Keyword-only regression passed.
- Bilingual top-paper rationale present.
- Reading-action alignment warnings remain.

## Prompt Fixes

- DeepSeek-Claude prompt now includes boundary self-check, exact CMD sequence, source-health classification table, `command_unavailable` rule, common final report sections, and paste-back block.
- Kimi Code prompt now includes full-context/no-memory wording, boundary self-check, exact CMD sequence, no invented success rule, common final report sections, and paste-back block.
- Codex prompt now makes Codex the comparator/final reviewer and forbids claiming parity unless all operators actually ran.

## Acceptance Gate Changes

Fallback acceptance now requires:

- actual run evidence;
- no private path access;
- no git write/tag operation;
- no automation;
- no source/ranking/taxonomy/query changes;
- honest `command_unavailable` reporting;
- common final report sections;
- Codex review of paste-back output.

Not-run operators must remain `insufficient_evidence` or `blocked_by_missing_operator`.

## Paste-Back Package

`docs/operations/fallback_operator_paste_back_package_v0.1.md` defines the compact block the user can paste back into Codex for comparison.

## Second Dry-Run Plan

`docs/operations/cross_operator_second_dry_run_plan_v0.1.md` defines the next run sequence for DeepSeek-Claude and Kimi Code, followed by Codex comparison.

## Safety Confirmation

- No production code was changed.
- No source/ranking/taxonomy behavior was changed.
- No manual annotation workflow was introduced.
- No external LLM runtime was added.
- No background automation was created.
- No release/tag operation was executed.

