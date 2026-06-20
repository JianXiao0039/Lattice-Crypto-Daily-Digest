# Operator Divergence Remediation Policy v0.1

Status: `operator_divergence_policy_ready`.

Use `docs/operations/cross_operator_drift_taxonomy_v0.1.md` as the source of truth for drift labels.

## not_run_drift

Action:

- block fallback acceptance;
- require a real dry run;
- do not infer parity from documentation.

## command_drift

Action:

- update the operator prompt;
- require `command_unavailable` instead of invented success;
- rerun the common task set.

## artifact_drift

Action:

- update the report template;
- run durable artifact verification;
- require Codex review if artifacts will be used as release or operations evidence.

## source_health_interpretation_drift

Examples:

- arXiv 429 not classified as rate_limited.
- IACR failed/0 interpreted as no relevant papers.

Action:

- update source-health interpretation table;
- rerun low-load probe;
- never treat failed sources as proof of no relevant papers.

## boundary_drift

Legacy heading: Boundary Violation.

Action:

- stop trusting that operator for fallback use;
- mark operator unsafe;
- require stricter prompt;
- require Codex review before future use.

## report_format_drift

Action:

- require common final report sections;
- rerun or request corrected paste-back package.

## environment_drift

Action:

- document shell, Python version, platform, and network differences;
- accept only if commands and artifacts remain comparable.

## quality_audit_drift

Action:

- require same monthly audit command;
- compare decision, score, keyword-only status, bilingual status, TODO_VERIFY, and reading-action findings.
