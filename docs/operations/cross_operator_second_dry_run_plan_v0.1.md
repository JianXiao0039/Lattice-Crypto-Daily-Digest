# Cross-Operator Second Dry Run Plan v0.1

Status: `eligible_for_phase_14i_second_dry_run`.

Phase 14G established that Codex ran successfully with degraded but explicit source health, while DeepSeek-Claude and Kimi Code were not run. Phase 14H fixes the prompt/runbook drift so the next drill can collect real fallback-operator evidence.

## Sequence

1. User runs DeepSeek-Claude with `docs/operations/deepseek_claude_dry_run_prompt_v0.1.md`.
2. User copies the `BEGIN FALLBACK_OPERATOR_PASTE_BACK` block into Codex.
3. User runs Kimi Code with `docs/operations/kimi_code_dry_run_prompt_v0.1.md`.
4. User copies the `BEGIN FALLBACK_OPERATOR_PASTE_BACK` block into Codex.
5. Codex runs or reuses its own dry-run evidence.
6. Codex compares all outputs using `docs/operations/cross_operator_output_comparison_template_v0.1.md`.
7. Codex classifies drift using `docs/operations/cross_operator_drift_taxonomy_v0.1.md`.
8. Codex decides fallback acceptance using `docs/operations/cross_operator_fallback_acceptance_gate_v0.1.md`.

## Stop Conditions

Stop and require Codex review if any fallback operator:

- reads or writes private paths;
- runs `git add`, `git commit`, `git push`, or `git tag`;
- creates automation;
- changes source/ranking/taxonomy/query behavior;
- modifies code;
- invents command success;
- omits the final paste-back block.

## Expected Phase 14I Outcome

Phase 14I should be able to decide:

- `cross_operator_dry_run_passed`;
- `cross_operator_dry_run_passed_with_limits`;
- `cross_operator_dry_run_blocked_by_missing_operator`;
- `cross_operator_dry_run_blocked_by_boundary_violation`;
- `cross_operator_dry_run_blocked_by_operator_drift`.

