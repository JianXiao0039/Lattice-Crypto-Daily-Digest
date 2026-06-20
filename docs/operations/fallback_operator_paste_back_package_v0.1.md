# Fallback Operator Paste-Back Package v0.1

Use this compact format when the user runs DeepSeek-Claude or Kimi Code outside Codex and wants Codex to compare outputs.

```text
BEGIN FALLBACK_OPERATOR_PASTE_BACK

## Operator

## Tool / model

## Date/time

## Working directory

## Boundary self-check

## Commands run

## Commands unavailable

## Artifacts generated

## Source-health table

## Monthly audit result

## Reading queue / Obsidian result

## Failures / warnings

## Git status before

## Git status after

## Final status

## Request for Codex review

END FALLBACK_OPERATOR_PASTE_BACK
```

## Required Values

- If a command did not run, write `command_unavailable` and the observed reason.
- If the operator did not run, write `not_run`.
- If source health is degraded, classify the source and do not claim "no relevant papers" from a failed source.
- If any boundary was violated, write `boundary_drift` and stop.

## Codex Comparison Use

Codex should paste this block into `docs/operations/cross_operator_output_comparison_template_v0.1.md` or a phase report and classify drift using `docs/operations/cross_operator_drift_taxonomy_v0.1.md`.

