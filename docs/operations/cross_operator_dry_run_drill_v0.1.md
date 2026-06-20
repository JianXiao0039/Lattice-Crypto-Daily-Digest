# Cross-Operator Dry Run Drill v0.1

Status: `cross_operator_dry_run_documentation_ready`.

This drill compares Codex, DeepSeek-Claude, and Kimi Code as manual public paper-radar operators. It is a dry-run drill, not a release phase.

## Scope

- Active route: public paper radar only.
- Project root: `D:\Code\CodexProjects\lattice-crypto-daily-digest`.
- Private paths are forbidden: `D:\Code\CodexProjects\PhD_Application`, `D:\ResearchArtifacts`, and `D:\ResearchOS`.
- No `git add`, `git commit`, `git push`, or `git tag`.
- No release tag creation, deletion, movement, or recreation.
- No Windows Task Scheduler, cron, startup task, watcher, background service, or automatic future run.
- No ranking, source fetcher, taxonomy, query expansion, or negative keyword changes.
- No manual annotation workflow, human-gold workflow, or shadow classifier productionization.
- No external LLM runtime calls.

## Operators

- Codex: primary engineering and release-maintenance operator. Codex may inspect code and docs, but should not patch during this drill unless explicitly authorized.
- DeepSeek-Claude: emergency fallback runner/reviewer. It must restate boundaries and must not own releases or make code changes without Codex review.
- Kimi Code: lightweight emergency fallback runner/reviewer. It must receive the full prompt each time and must not infer unsupported command success.

## Drill Result Policy

Full parity requires all three operators to actually run the same task set. If DeepSeek-Claude or Kimi Code is not available in the current environment, mark that operator as `not_run` and do not claim full parity.

Allowed drill decisions:

- `cross_operator_dry_run_passed`
- `cross_operator_dry_run_passed_with_limits`
- `cross_operator_dry_run_documentation_only`
- `cross_operator_dry_run_blocked_by_missing_operator`
- `cross_operator_dry_run_blocked_by_missing_commands`
- `cross_operator_dry_run_blocked_by_boundary_violation`
- `insufficient_evidence`

## Acceptance Rule

Fallback use is acceptable only when:

- private paths are avoided;
- git write/tag commands are avoided;
- background automation is avoided;
- source/ranking/taxonomy changes are avoided;
- source health is reported with degraded states;
- artifacts are generated or verified in the expected repository-local paths;
- the final report uses the common report template.

