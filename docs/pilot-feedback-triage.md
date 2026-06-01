# Pilot Feedback Triage

This document defines a documentation-only triage framework for Phase 9E. It helps classify issues found during the one-week manual pilot, assign severity, choose a likely follow-up phase, and decide what to fix next.

It does not add product features, change workflow behavior, or configure any automatic execution.

## Purpose

Use this triage framework after manual pilot runs to:

- group feedback into consistent issue categories;
- separate bugs from docs gaps, classification problems, and intentional non-goals;
- assign low / medium / high severity;
- select a phase target label for follow-up work;
- keep fixes small, reversible, and aligned with the manual low-load research workflow.

## Manual-only principle

Manual-only usage is the rule for pilot feedback. A pilot issue should be reproduced by a user-triggered command, a manually reviewed artifact, or a manually inspected document.

Do not turn pilot feedback into background execution. If an issue seems to ask for "run this automatically", record it as `workflow_confusion`, `release_hygiene`, or `wont_fix` unless the user explicitly approves a later design change.

Low-load mode remains a manual operator choice. Prefer commands such as `python -m lattice_digest.workflow weekly --low-load` when collecting pilot notes on a laptop.

## No scheduled automation principle

No scheduled automation is configured by this triage framework. Do not add or recommend:

- Windows Task Scheduler integration;
- cron files;
- background daemons or services;
- startup tasks;
- watchers;
- automatic scheduled runs.

Triage may mention GitHub Actions only as existing cloud CI / provisional digest context. It must not add local scheduling or background automation.

## Safety boundaries

Preserve these boundaries before proposing any follow-up fix:

- Dry-run safety: workflow commands should remain dry-run by default unless the user explicitly passes `--execute`.
- No-network behavior: `--no-network` and `--offline` should continue to avoid network fetches.
- Generated artifacts must not be committed unless an explicit publishing or release process asks for them.
- Reading queue manual statuses should be preserved; do not overwrite user-maintained reading status fields during triage or cleanup.
- Pilot triage should not modify fetcher, ranking, section classifier, daily / weekly workflow, reading queue, Obsidian scaffold, research progress, source health, Zotero export, or release hygiene semantics.

## Issue categories

Use one or more exact category labels:

- `classification_false_positive`: an irrelevant or weakly related item was classified too strongly.
- `classification_false_negative`: a relevant lattice / PQC item was missed or ranked too low.
- `ranking_noise`: the item is relevant, but score, priority, explanation, or ordering is noisy.
- `workflow_confusion`: command output or pilot steps make manual operation unclear.
- `slow_command`: a manual command is unexpectedly slow for low-load mode.
- `artifact_clutter`: generated outputs are too noisy, scattered, or hard to clean up.
- `reading_queue_state`: manual reading queue status, notes, or local state may be overwritten or confusing.
- `obsidian_scaffold`: Obsidian note scaffold output is confusing, incomplete, or too eager.
- `source_health_confusion`: source health output makes reliability hard to judge.
- `windows_path_or_lock`: Windows path handling, SQLite lock behavior, or file lock behavior blocks use.
- `ci_only`: the issue appears only in CI and does not reproduce locally.
- `docs_gap`: documentation is missing, stale, ambiguous, or not linked.
- `release_hygiene`: release checks, ignored artifacts, or packaging expectations are unclear.
- `wont_fix`: the behavior is intentional, out of scope, or too risky to change.

## Severity levels

### High

Use `high` when the issue can cause data loss, unsafe writes, broken manual operation, accidental commits of generated artifacts, loss of reading queue manual statuses, or violation of dry-run / no-network / no-scheduled-automation boundaries.

Examples:

- `weekly --execute` overwrites manual reading queue statuses.
- `--no-network` still fetches external sources.
- Generated artifacts are staged or documented as safe to commit by default.
- A proposed fix requires Windows Task Scheduler, cron, daemon, startup task, watcher, or automatic scheduled run.

### Medium

Use `medium` when the issue reduces pilot usefulness but has a workaround and does not violate core safety boundaries.

Examples:

- Source health output is hard to interpret.
- Low-load output is too verbose or unclear.
- A false positive distracts from the research reading queue.
- Cleanup instructions are incomplete but generated artifacts remain unstaged.

### Low

Use `low` when the issue is cosmetic, wording-level, or mildly inconvenient.

Examples:

- A heading is unclear.
- A template field needs a better label.
- A doc link is useful but not required for pilot safety.

## Phase target labels

Choose one exact phase target label:

- `Phase 9F: classifier calibration follow-up`
- `Phase 9G: workflow UX polish`
- `Phase 9H: artifact cleanup ergonomics`
- `Phase 9I: reading queue safety hardening`
- `Phase 9J: docs polish`
- `Phase 9K: release hardening`
- `wont_fix`

Recommended mapping:

- `classification_false_positive`, `classification_false_negative`, `ranking_noise` -> `Phase 9F: classifier calibration follow-up`
- `workflow_confusion`, `slow_command`, `source_health_confusion` -> `Phase 9G: workflow UX polish`
- `artifact_clutter`, `obsidian_scaffold` -> `Phase 9H: artifact cleanup ergonomics`
- `reading_queue_state` -> `Phase 9I: reading queue safety hardening`
- `docs_gap` -> `Phase 9J: docs polish`
- `ci_only`, `release_hygiene`, `windows_path_or_lock` -> `Phase 9K: release hardening`
- `wont_fix` -> `wont_fix`

## Triage workflow

1. Record the pilot date, command run, and whether low-load mode, dry-run, or no-network behavior was used.
2. Capture expected behavior and actual behavior without guessing hidden causes.
3. Assign one or more issue categories from the exact labels above.
4. Assign severity: `low`, `medium`, or `high`.
5. Decide whether the issue is a bug, docs issue, classification issue, or won't fix.
6. Select one phase target label.
7. Propose the smallest safe follow-up. Prefer documentation or calibration before new workflow steps.
8. Check `git status -sb` before and after any later fix; generated artifacts must not be committed.
9. Preserve reading queue manual statuses when inspecting or repairing state.

## What counts as a bug

An issue counts as a bug when documented or expected behavior is violated by current implementation.

Examples:

- A dry-run command writes files.
- No-network behavior still performs an external fetch.
- Reading queue manual statuses are overwritten.
- Generated artifacts are created in a path that release hygiene treats as source.
- A manual command fails on a normal Windows path or common SQLite file lock condition.

## What counts as a docs issue

An issue counts as a docs issue when behavior is acceptable but the operator guidance is missing, misleading, stale, or hard to find.

Examples:

- README does not link the relevant pilot guidance.
- Low-load mode is available but not explained near the pilot steps.
- Safe commands and risky commands are not distinguished.
- The no scheduled automation principle is not visible where a user would expect it.

## What counts as a classification issue

An issue counts as a classification issue when paper relevance, category, score, priority, or explanation quality is wrong or noisy.

Examples:

- A materials "lattice" paper is accepted as lattice cryptography.
- An LWE / MLWE / SIS / BKZ / PQC implementation paper is missed.
- A C-class background paper is ranked above A/B core lattice cryptography.
- Matched keywords or negative keywords do not explain the decision well enough for manual review.

## What counts as won't fix

Use `wont_fix` when the requested change conflicts with project safety boundaries, pilot scope, or explicit user constraints.

Examples:

- Add Windows Task Scheduler, cron, background daemon, startup task, watcher, or automatic scheduled run for the local pilot.
- Make workflow commands write by default instead of preserving dry-run safety.
- Commit generated artifacts by default.
- Replace manual reading queue review with automatic status changes.
- Add a product feature during this documentation-only phase.

