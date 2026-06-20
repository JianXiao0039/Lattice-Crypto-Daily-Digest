# Cross-Operator Fallback Acceptance Gate v0.1

Status: `fallback_use_requires_codex_review`.

## Required Gates

An operator is acceptable as a fallback runner only if it:

- uses `D:\Code\CodexProjects\lattice-crypto-daily-digest` as the working directory;
- avoids private paths;
- avoids `git add`, `git commit`, `git push`, and `git tag`;
- avoids release tag operations;
- avoids background automation;
- avoids source fetcher, ranking, taxonomy, query expansion, and negative keyword changes;
- runs or reports the same task set;
- reports degraded source health explicitly;
- reports Daily, Weekly, Monthly, source-health, reading queue, Obsidian, and monthly quality artifacts;
- uses the shared final report sections.

## Decisions

- Codex: `codex_primary_operator_confirmed` when the dry run completes without boundary violations.
- DeepSeek-Claude: `deepseek_claude_fallback_ready` only after an actual run completes without boundary violations.
- Kimi Code: `kimi_code_fallback_ready` only after an actual run completes without boundary violations.

If an operator is not actually run, use:

- `deepseek_claude_dry_run_not_run`
- `kimi_code_dry_run_not_run`

Do not infer parity from documentation alone.

## Release Boundary

DeepSeek-Claude and Kimi Code must not become release owners. Any release decision, code change, or tag plan requires Codex review and explicit user authorization.

