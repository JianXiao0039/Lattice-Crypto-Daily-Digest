# Doctor Strict Exit-Code Contract v0.1

## Contract

`doctor_report(strict=True)` returns nonzero when a critical environment or repository-health check fails.

Critical checks include:

- supported Python runtime;
- non-empty package version;
- real `ZoneInfo("Asia/Singapore")` availability;
- source package directory;
- release metadata and tracked-artifact hygiene.

The doctor check is deterministic with respect to unrelated staging state. Forbidden staged generated files remain blocked by the explicit release-hygiene command and workflow release gates.

The timezone check remains critical and is never mocked or downgraded. Regression tests also verify that a genuine critical release-metadata failure still returns code 1.
