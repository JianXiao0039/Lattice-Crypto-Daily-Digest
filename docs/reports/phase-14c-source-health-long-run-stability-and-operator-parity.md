# Phase 14C Source Health Long-Run Stability and Operator Parity

## Decision

- Source health stability: `source_health_long_run_policy_ready`.
- Operator parity: `codex_deepseek_kimi_parity_ready`.
- Emergency fallback: `fallback_ready_with_codex_review_required`.
- Production gate: `eligible_for_v0_6_operations_stability`.

## Dependency Status

Phase 13O operations runbooks are present and were used as the base manual workflow.

Phase 13L source-health recovery outputs are present and were used as the source-specific diagnostic baseline.

Phase 14B bilingual rationale outputs are present and confirm top-paper bilingual rationale rendering is available.

## Files Inspected

- `docs/operations/radar_manual_operations_runbook_v0.1.md`
- `docs/operations/codex_operator_policy_v0.1.md`
- `docs/operations/deepseek_claude_operator_policy_v0.1.md`
- `docs/operations/kimi_code_operator_policy_v0.1.md`
- `docs/operations/source_health_manual_recovery_runbook_v0.1.md`
- `docs/reports/phase-13l-source-health-and-durable-artifact-recovery.md`
- `docs/reports/phase-14b-bilingual-rationale-polish.md`
- `scripts/probe_source_health.py`
- `scripts/verify_durable_artifacts.py`
- `src/lattice_digest/workflow.py`

## Summary

Phase 14C adds cross-operator parity docs, emergency fallback policies, a command matrix, source-health long-run stability policies, a source failure interpretation table, and a common manual operation report template.

No source fetcher, ranking, threshold, taxonomy, query expansion, negative keyword, release, tag, or automation behavior was changed.

## Validation

- `python --version`: Python 3.15.0b2.
- `python -m lattice_digest.workflow doctor`: passed.
- `python -c "import lattice_digest; print(lattice_digest.__version__)"`: 0.4.1.
- Focused Phase 14C tests: `14 passed`.
- `scripts/run_project_tests.bat`: `670 passed`.
- `python scripts/check_release_hygiene.py`: passed.
- `git diff --check`: passed with CRLF-to-LF warnings on existing modified/generated files.
- `git diff --cached --check`: passed.

## Boundaries

- No git add/commit/push/tag was executed.
- No tag was created, deleted, moved, or recreated.
- No private PhD_Application, ResearchArtifacts, or ResearchOS path was read or written.
- No manual annotation or human-gold workflow was introduced.
- No external LLM runtime or new network paper-fetching path was added.
- No anti-bot bypass or access-control evasion was recommended.
