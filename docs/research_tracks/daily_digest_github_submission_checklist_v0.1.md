# Daily Digest GitHub Submission Checklist v0.1

## Before Submission

- [ ] Confirm the expected `digests/YYYY-MM-DD.md` exists.
- [ ] Confirm the corresponding `data/YYYY-MM-DD.json` exists if structured data is intended for publication.
- [ ] Confirm source health and source-starved interpretation.
- [ ] Run project tests and release hygiene.
- [ ] Review `.gitignore` matches with `git check-ignore -v --no-index`.

## Tracking Verification

- [ ] `git ls-files` includes every intended Markdown artifact.
- [ ] `git ls-files` includes every intended JSON artifact, or the omission is explicitly documented.
- [ ] `git log --oneline -- <path>` shows the intended commit.
- [ ] After fetch, `git ls-tree -r --name-only origin/main` contains every intended remote artifact.

## Current June 4-10 State

- [x] All seven Markdown files are tracked and remote.
- [ ] All seven JSON files are tracked and remote.
- [x] Push commit is identifiable as `5433a19`.
- [ ] Ubuntu CI passes.

## Boundaries

- Do not publish secrets, `.env`, caches, local logs, private application content, or ResearchArtifacts content.
- Do not assume a successful push means CI passed.
- Do not assume local existence means Git tracking or remote presence.

