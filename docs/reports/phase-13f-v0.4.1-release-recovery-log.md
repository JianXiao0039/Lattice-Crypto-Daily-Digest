# Phase 13F v0.4.1 Release Recovery Log

## Git Evidence

- Active package: 0.4.1.
- Existing v0.4.1 tag: `95215b5`, June 12, 2026.
- Current origin/main: `355962b8`.
- v0.4.0 remains `08c5f079`.
- No tag operation was performed.

## CI Evidence

Public GitHub Actions API run `27486242311` failed at tests on Ubuntu and Windows. Scheduled Daily run `27458195293` failed at tests before digest generation.

## Persistence Evidence

No June 11-14 Markdown/JSON pair is tracked or present in origin/main. Local June 12 and June 13 pairs are untracked and have insufficient provenance for durable classification.

## Contract Evidence

The narrow date-specific force-add correction exists only as an unstaged worktree change to `.github/workflows/daily.yml`; HEAD, origin/main, and the v0.4.1 tag still use the ineffective ignored glob staging command.

Decision: `blocked_by_multiple_conditions`.

Local doctor, version checks, release hygiene, 521 repository tests, and whitespace checks pass. These local results do not satisfy the failed remote CI and missing durable-run gates.
