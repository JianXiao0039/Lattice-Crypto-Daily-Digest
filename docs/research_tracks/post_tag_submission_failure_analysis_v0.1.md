# Post-Tag Submission Failure Analysis v0.1

## Finding

High-confidence configuration root cause: the tag-time workflow ran:

```text
git add -- digests/*.md data/*.json papers.db
```

At the same commit, `.gitignore` ignored `data/*.json`, `digests/*.md`, and `papers.db`. The generated 2026-06-11 Markdown and JSON were new ignored paths. Public job metadata shows the commit step failed immediately after artifact verification.

`git check-ignore -v --no-index` reproduces that these path families are ignored. The authenticated job log is unavailable, so the exact stderr remains `TODO_VERIFY`.

## Consequence

- No commit was created.
- Sequential shell execution therefore did not reach a successful push.
- Runner-local files were discarded.
- `origin/main` has no 2026-06-11 Daily artifacts.

## Remediation

In a separate workflow-change phase, make the explicit publication path compatible with ignore policy, while retaining the narrow allowlist for daily artifacts. Then observe a real persisted Daily run. This Phase 12Z preparation does not change the workflow.
