# Durable Daily Artifact Submission Contract v0.1

## Selected Mechanism

Use a narrow explicit force-add only for the two verified date-specific files:

```sh
git add -f -- "$markdown_path" "$json_path"
git add -- papers.db
```

`markdown_path` and `json_path` are derived from the verified Asia/Singapore `digest_date`.

## Constraints

- Never force-add directories, globs, caches, exports, notes, private paths, or `papers.db`.
- Validate both files before staging.
- Keep local generated artifacts ignored by default.
- Keep explicit release hygiene strict for ordinary release commits.
- A Daily publication workflow is a narrow, audited exception, not a global tracking policy.

## Persistence Evidence

The workflow must retain the exact file paths, commit hash, push result, and `origin/main` path verification before the run is considered durable.
