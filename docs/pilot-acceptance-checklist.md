# Pilot Acceptance Checklist

This checklist defines the acceptance criteria for the one-week manual pilot. It is intentionally operator-facing and does not introduce new workflow behavior.

## 1. Manual-only operation

- [ ] manual-only usage is preserved.
- [ ] No scheduled automation is configured.
- [ ] No Windows Task Scheduler integration is added.
- [ ] No cron file is added.
- [ ] No background daemon, startup task, watcher, or automatic scheduled run is added.

## 2. Read-only commands

- [ ] `python -m lattice_digest.workflow status` is read-only.
- [ ] `python -m lattice_digest.workflow doctor` is read-only.
- [ ] Read-only commands do not write data, digests, exports, audits, state, or notes.

## 3. Dry-run default

- [ ] dry-run default remains active for workflow commands.
- [ ] `weekly` dry-run writes no files.
- [ ] `daily` dry-run writes no files.
- [ ] `full` dry-run writes no files.

## 4. Low-load mode

- [ ] low-load mode is available with `--low-load`.
- [ ] low-load mode is reflected in planned steps.
- [ ] low-load workflow remains usable on a laptop without background execution.

## 5. No-network / offline usage

- [ ] `--no-network` skips network fetch steps.
- [ ] `--offline` skips network fetch steps.
- [ ] no-network/offline usage is documented before using it in a pilot.

## 6. Weekly workflow behavior

- [ ] `weekly --execute --low-load` writes only expected weekly workflow outputs.
- [ ] `weekly --execute` does not generate Obsidian notes unless `--generate-notes` is explicitly provided.
- [ ] Generated notes, if intentionally produced, remain local generated artifacts by default.

## 7. Reading queue

- [ ] reading queue manual statuses should be preserved.
- [ ] Existing manual statuses are not overwritten by import or weekly workflow steps.
- [ ] `state/reading-queue.json` is treated as local state unless intentionally backed up.

## 8. Generated artifacts

- [ ] generated artifacts must not be committed.
- [ ] `exports/`, `audits/`, `.pytest_tmp/`, `__pycache__/`, `data/*.json`, `data/weekly/`, `digests/*.md`, `digests/weekly/`, `papers.db`, `.env`, and local logs remain unstaged unless intentionally handled.
- [ ] `git status -sb` does not show forbidden artifacts staged.

## 9. Research usability

- [ ] Source health output is understandable.
- [ ] Advisor/progress docs are usable.
- [ ] Ranking explanations are readable enough to triage papers.
- [ ] Workflow output is clear about planned versus executed steps.

## 10. Acceptance result

Accept the pilot only if all critical items pass:

- no automatic background execution
- status command is read-only
- doctor command is read-only
- dry-run writes no files
- low-load workflow remains usable
- no-network skips network fetch
- reading queue manual statuses are preserved
- generated artifacts remain ignored
- git status does not show forbidden artifacts staged

If any critical item fails, open an issue entry using `docs/pilot-issue-log-template.md`.
