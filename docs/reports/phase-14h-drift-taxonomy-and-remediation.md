# Phase 14H Drift Taxonomy and Remediation

## Status

`cross_operator_drift_taxonomy_ready`.

## Drift Types

- `not_run_drift`
- `command_drift`
- `artifact_drift`
- `source_health_interpretation_drift`
- `boundary_drift`
- `report_format_drift`
- `environment_drift`
- `quality_audit_drift`

## Phase 14G Classification

Phase 14G is classified as `not_run_drift` for DeepSeek-Claude and Kimi Code.

## Remediation

- `not_run_drift`: run the operator with the fixed prompt.
- `command_drift`: normalize command list and rerun.
- `artifact_drift`: require explicit artifact paths and durable verifier output.
- `source_health_interpretation_drift`: require the common source-health table.
- `boundary_drift`: mark operator unsafe pending Codex review.
- `report_format_drift`: require the common report template.
- `environment_drift`: document Python/shell/platform/network differences.
- `quality_audit_drift`: require the same monthly audit command and decision fields.

The detailed taxonomy is in `docs/operations/cross_operator_drift_taxonomy_v0.1.md`.

