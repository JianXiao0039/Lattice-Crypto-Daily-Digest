# Release Gate Release Notes Cleanup v0.1

## Decision

`release_notes_need_update`

## Findings

`docs/releases/v0.4.1.md` is stale:

- It says no `v0.4.1` tag is created by the preparation phase.
- Current Git evidence shows local and remote `v0.4.1` tags exist.
- In short: the tag now exists, so the old preparation wording is stale.
- The tag points to `95215b5afe18b1f13463d03929bfe27f15788695`, not HEAD.
- Durable Daily evidence for the v0.4.1 tagged commit remains insufficient.

The v0.5 RC release notes draft is mostly accurate but still has TODO items:

- CI green must be confirmed.
- v0.4.1 historical release clarity must be documented.

## Cleanup Draft

Suggested v0.4.1 note:

> v0.4.1 exists as an immutable historical corrective-release tag. It points to commit `95215b5afe18b1f13463d03929bfe27f15788695`. The tag is not moved or recreated. Its durable post-tag Daily evidence gate remains insufficient, so it should be treated as blocked historical evidence unless a future manual release decision supersedes it.

Suggested v0.5 RC note:

> v0.5 is a paper-radar usability release candidate covering recommendation rationale, Daily/Weekly/Monthly outputs, source-health diagnostics, durable artifact verification, reading queue, Obsidian export, and manual operations runbooks. Final release requires CI green evidence and final release-note review.

## Claims to Avoid

- Do not claim v0.4.1 is fully releasable.
- Do not claim CI is green until verified.
- Do not claim source health is fully recovered.
- Do not claim v0.5 is production-ready while it is still RC.
- Do not mention human-gold metrics or manual annotation improvements as release features.
- Do not include private PhD or Module-SIS artifact work.
