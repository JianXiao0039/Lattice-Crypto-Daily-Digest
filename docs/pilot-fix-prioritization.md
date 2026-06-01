# Pilot Fix Prioritization

This document defines how to choose what to fix after Phase 9E pilot feedback triage. It is documentation-only and does not change workflow behavior.

Manual-only usage remains the operating model. No scheduled automation is configured by this document, and it must not introduce Windows Task Scheduler integration, cron files, background daemons, startup tasks, watchers, or automatic scheduled runs.

## Prioritization rules

Apply these rules in order.

## 1. Protect manual reading queue state first

Reading queue manual statuses should be preserved. Any issue that can overwrite, delete, reorder destructively, or silently reinterpret user-maintained reading queue state gets priority over output polish.

Prioritize:

- preserving manual statuses and notes;
- making recovery steps clear;
- documenting backups before write-enabled commands;
- preventing accidental state edits during dry-run or no-network checks.

## 2. Prevent generated artifacts from being committed

Generated artifacts must not be committed by default. Prioritize fixes that keep generated files out of normal feature commits, especially:

- `exports/`;
- `audits/`;
- `research_artifacts/`;
- `.pytest_tmp/`;
- `__pycache__/`;
- local logs and caches;
- local test digest outputs;
- `papers.db` when it was only touched by local testing rather than an explicit digest publishing flow.

If documentation and tooling disagree, fix the confusing guidance before adding new outputs.

## 3. Preserve dry-run safety

Dry-run safety is a core boundary. A command that appears dry-run or is documented as dry-run must not write files.

Fix these before convenience improvements:

- dry-run commands writing files;
- docs implying `--execute` is optional for writes;
- output that hides whether a command is planned versus executed;
- pilot steps that make write-enabled commands look routine.

## 4. Preserve no-network behavior

No-network behavior must remain trustworthy. `--no-network` and `--offline` should avoid external fetches and should be suitable for travel, metered networks, and low-load review.

Prioritize:

- accidental network access in no-network mode;
- docs that blur no-network versus normal source fetching;
- source health output that makes no-network runs look like source failures.

## 5. Reduce false positives before adding features

Classification false positives waste reading time and make the manual workflow feel noisy. Prefer classifier calibration, negative keyword clarity, and ranking explanation improvements before adding new workflow steps.

This usually maps to `Phase 9F: classifier calibration follow-up`.

## 6. Improve confusing output before adding new workflow steps

If users cannot tell what a command did, whether it wrote files, or what to review next, improve the output or docs before adding another command.

Prioritize:

- planned versus executed step clarity;
- source health wording;
- low-load mode visibility;
- clear cleanup instructions;
- explicit risky command labels.

This usually maps to `Phase 9G: workflow UX polish` or `Phase 9J: docs polish`.

## 7. Avoid automatic background execution

Do not solve pilot friction by adding scheduled automation. Avoid:

- Windows Task Scheduler files;
- cron files;
- background daemons or services;
- startup tasks;
- watchers;
- automatic scheduled runs.

If a request requires background execution, label it `wont_fix` for this manual pilot unless the user explicitly opens a future automation design phase.

## 8. Defer cosmetic fixes unless they block usability

Cosmetic issues are valid but should not displace safety, classification quality, or manual workflow clarity.

Defer:

- minor wording preferences;
- heading style changes;
- optional cross-links;
- formatting cleanup that does not affect safe operation.

Promote a cosmetic issue only if it blocks usability, causes misoperation, or hides a safety boundary.

## Priority matrix

| Priority | Typical severity | Fix before next pilot? | Examples |
| --- | --- | --- | --- |
| P0 | high | Yes | reading queue state loss, dry-run writes, no-network fetches, generated artifacts staged |
| P1 | high / medium | Usually | confusing write-enabled output, severe source health ambiguity, Windows file lock blocker |
| P2 | medium | When scoped | false positives, ranking noise, artifact cleanup friction |
| P3 | low | Later | wording polish, optional links, non-blocking template cleanup |

## Phase mapping

- `Phase 9F: classifier calibration follow-up`: false positives, false negatives, ranking noise.
- `Phase 9G: workflow UX polish`: confusing command output, slow command explanation, source health wording.
- `Phase 9H: artifact cleanup ergonomics`: generated artifact clutter, cleanup guidance, Obsidian scaffold review ergonomics.
- `Phase 9I: reading queue safety hardening`: reading queue manual status protection.
- `Phase 9J: docs polish`: docs gaps, missing links, unclear pilot instructions.
- `Phase 9K: release hardening`: CI-only problems, release hygiene checks, Windows path or lock issues.
- `wont_fix`: requests that violate manual-only, dry-run safety, no-network behavior, or no scheduled automation boundaries.

## Decision checklist

Before selecting a fix, confirm:

- Does it protect reading queue manual statuses?
- Does it keep generated artifacts out of commits?
- Does it preserve dry-run safety?
- Does it preserve no-network behavior?
- Does it keep low-load mode manual and predictable?
- Does it avoid scheduled automation and background execution?
- Does it reduce false positives or confusion before adding features?
- Can it be tested with docs-only or narrow behavior tests?

