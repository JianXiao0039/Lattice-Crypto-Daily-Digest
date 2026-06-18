# Release Gate Cleanup: v0.4.1 Status v0.1

## Decision

`v0_4_1_tag_exists_blocked`

## Tag Status

- Local tag: exists.
- Remote tag: exists.
- Tag type: annotated tag.
- Local tag object: `52bdda3b491e4717f14e8b40c8a35ff2bc19bad8`.
- Peeled target commit: `95215b5afe18b1f13463d03929bfe27f15788695`.
- Target commit subject: `Validate v0.4.1 corrective release and durable run evidence`.
- Current HEAD: `e092486203d39913affb1fa8ac97cd3dd03fc513`.
- `origin/main`: `e092486203d39913affb1fa8ac97cd3dd03fc513`.

The v0.4.1 tag does not point to HEAD or current `origin/main`.

## Durable Evidence at Tagged Commit

The tagged commit does not contain:

- `data/2026-06-15.json`
- `digests/2026-06-15.md`
- `docs/research_tracks/v0.4.1_durable_daily_evidence_manifest_v0.1.json`

The current worktree verifier still reports durable post-tag Daily evidence for v0.4.1 as missing.

## CI Status

GitHub CLI was present but not authenticated, so CI could not be verified from this environment.

Current v0.4.1 durable evidence manifest in HEAD records prior CI run `27486931415` as failed on Ubuntu and Windows at Run tests.

## Release Note Status

`docs/releases/v0.4.1.md` is stale because it says the preparation phase does not create a `v0.4.1` tag, while the tag now exists.

## Recommended Action

Keep the v0.4.1 tag untouched as historical blocked release evidence. Do not delete, move, recreate, or force-update it.

Recommended future action is either:

- document v0.4.1 as blocked and superseded by a later v0.5 candidate; or
- prepare a new patch release version later if a corrective v0.4.x line is still needed.
