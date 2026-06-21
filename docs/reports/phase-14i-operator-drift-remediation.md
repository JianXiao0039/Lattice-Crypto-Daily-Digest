# Phase 14I Operator Drift Remediation

## Current Drift

- DeepSeek-Claude: `not_run_drift`.
- Kimi Code: `not_run_drift`.

## Remediation

1. Run DeepSeek-Claude with the Phase 14H fixed prompt.
2. Run Kimi Code with the Phase 14H fixed prompt.
3. Paste both fallback packages into Codex.
4. Codex compares using `docs/operations/cross_operator_output_comparison_template_v0.1.md`.
5. Codex classifies drift using `docs/operations/cross_operator_drift_taxonomy_v0.1.md`.
6. Codex applies `docs/operations/cross_operator_fallback_acceptance_gate_v0.1.md`.

## Stop Conditions

Stop and require Codex review if either fallback operator:

- touches private paths;
- runs git write/tag commands;
- creates automation;
- changes source/ranking/taxonomy/query behavior;
- modifies code;
- omits paste-back evidence;
- invents unavailable command success.

