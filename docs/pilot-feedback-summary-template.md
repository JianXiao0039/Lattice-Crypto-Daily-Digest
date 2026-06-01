# Pilot Feedback Summary Template

Use this reusable template at the end of a one-week manual pilot, or after any smaller manual low-load pilot window. Keep the summary factual. Do not include API keys, SMTP passwords, Zotero tokens, private notes, or unpublished research claims.

This template is documentation-only. Manual-only usage remains the rule. No scheduled automation is configured, and no Windows Task Scheduler, cron, background daemon, startup task, watcher, or automatic scheduled run should be added from this summary.

## Pilot metadata

- Pilot date range:
- Reviewer:
- Repository / branch:
- Operating system:
- Python version:
- Notes location:

## Commands run

List exact user-triggered commands. Mark whether each command was read-only, dry-run, low-load, no-network, or write-enabled.

| Date | Command | Mode | Result | Notes |
| --- | --- | --- | --- | --- |
| TODO | `python -m lattice_digest.workflow status` | read-only | TODO | TODO |
| TODO | `python -m lattice_digest.workflow weekly --low-load` | dry-run, low-load mode | TODO | TODO |
| TODO | `python -m lattice_digest.workflow daily --no-network` | dry-run, no-network behavior | TODO | TODO |

## Issue counts

- Total issues:
- High severity count:
- Medium severity count:
- Low severity count:
- Open:
- Triaged:
- Fixed:
- Won't fix:

## Issues by category

Use the exact labels from `docs/pilot-feedback-triage.md`.

| Category | Count | Highest severity | Notes |
| --- | ---: | --- | --- |
| `classification_false_positive` | 0 | TODO | TODO |
| `classification_false_negative` | 0 | TODO | TODO |
| `ranking_noise` | 0 | TODO | TODO |
| `workflow_confusion` | 0 | TODO | TODO |
| `slow_command` | 0 | TODO | TODO |
| `artifact_clutter` | 0 | TODO | TODO |
| `reading_queue_state` | 0 | TODO | TODO |
| `obsidian_scaffold` | 0 | TODO | TODO |
| `source_health_confusion` | 0 | TODO | TODO |
| `windows_path_or_lock` | 0 | TODO | TODO |
| `ci_only` | 0 | TODO | TODO |
| `docs_gap` | 0 | TODO | TODO |
| `release_hygiene` | 0 | TODO | TODO |
| `wont_fix` | 0 | TODO | TODO |

## Top pain points

1. TODO
2. TODO
3. TODO

For each pain point, include the issue category, severity, phase target label, and shortest safe next action.

## Safe commands confirmed

Record commands that behaved safely during the pilot.

- `python -m lattice_digest.workflow status`:
- `python -m lattice_digest.workflow doctor`:
- `python -m lattice_digest.workflow weekly --low-load`:
- `python -m lattice_digest.workflow daily --no-network`:
- Other:

Confirm:

- Dry-run safety was preserved:
- Low-load mode was usable:
- No-network behavior avoided external fetches:
- No scheduled automation is configured:

## Risky commands observed

List commands that require extra caution, explicit `--execute`, manual review, or cleanup.

- Command:
- Why risky:
- Mitigation:
- Was it run? yes / no

Do not convert risky commands into scheduled automation. Keep local pilot runs manual.

## Generated artifact observations

Generated artifacts must not be committed by default.

- New generated paths observed:
- Ignored paths that appeared in `git status -sb`:
- Files that should be cleaned:
- Files that should be kept locally:
- Any accidental staged artifacts:
- Follow-up phase target:

## Reading queue status observations

reading queue manual statuses should be preserved.

- Reading queue file inspected:
- Manual statuses before run:
- Manual statuses after run:
- Unexpected status changes:
- Backup or recovery needed:
- Follow-up phase target:

## Source health observations

- Sources with green health:
- Sources with yellow health:
- Sources with red health:
- Confusing warnings:
- Retryable failures:
- No-network / offline behavior observed:
- Follow-up phase target:

## Classification and ranking observations

- False positives:
- False negatives:
- Ranking noise:
- Keyword / negative keyword explanation issues:
- Proposed calibration notes:
- Follow-up phase target:

## Documentation observations

- Missing links:
- Ambiguous commands:
- Missing Windows notes:
- Missing dry-run safety notes:
- Missing no-network behavior notes:
- Missing generated artifact warning:
- Follow-up phase target:

## Proposed next phases

Use exact labels:

- `Phase 9F: classifier calibration follow-up`:
- `Phase 9G: workflow UX polish`:
- `Phase 9H: artifact cleanup ergonomics`:
- `Phase 9I: reading queue safety hardening`:
- `Phase 9J: docs polish`:
- `Phase 9K: release hardening`:
- `wont_fix`:

## Final pilot decision

- Accept pilot as-is:
- Accept with follow-up:
- Blocked by high-severity issue:
- Notes:
