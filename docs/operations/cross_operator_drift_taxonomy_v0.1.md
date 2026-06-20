# Cross-Operator Drift Taxonomy v0.1

Status: `cross_operator_drift_taxonomy_ready`.

This taxonomy classifies differences between Codex, DeepSeek-Claude, and Kimi Code dry-run outputs.

## Drift Types

### not_run_drift

The operator did not actually run. Parity is `insufficient_evidence`.

Decision policy: block fallback acceptance and require a real dry run.

### command_drift

The operator used different commands, omitted required commands, invented unsupported flags, used the wrong shell syntax, or skipped a command without reporting `command_unavailable`.

Decision policy: update the prompt and rerun.

### artifact_drift

The operator generated different paths, failed to report artifact paths, reported missing artifacts as success, or failed to distinguish generated versus verified artifacts.

Decision policy: update the report template and rerun.

### source_health_interpretation_drift

The operator interpreted source failures differently. Examples:

- arXiv HTTP 429 not classified as `rate_limited`;
- DBLP TLS/SSL failure treated as generic failure;
- IACR failed/0 treated as "no relevant papers";
- Semantic Scholar missing key, auth failure, rate limit, timeout, and network error conflated;
- OpenAlex empty response treated as network failure without evidence;
- Crossref empty response treated as source failure without evidence.

Decision policy: update the source-health interpretation table and rerun.

### boundary_drift

The operator touched private paths, ran git write/tag commands, created automation, changed source/ranking/taxonomy/query behavior, or attempted release/tag work.

Decision policy: mark the operator unsafe until a stricter prompt is accepted and Codex reviews.

### report_format_drift

The operator did not use the common final report sections.

Decision policy: update the final report template and rerun.

### environment_drift

Python version, shell, network, platform, or local path behavior differs, but commands and boundaries remain valid.

Decision policy: acceptable only if documented and artifacts remain comparable.

### quality_audit_drift

Monthly audit, bilingual rationale, TODO_VERIFY, keyword-only regression, or reading action results are missing or interpreted inconsistently.

Decision policy: require the same audit command and same decision fields.

## Non-Drift Conditions

These are not drift if honestly reported:

- source health is degraded but explicitly classified;
- Daily command refuses to overwrite authoritative artifacts without `--force`;
- weekly command is dry-run only;
- generated artifacts differ only by current date and are reported as such.

