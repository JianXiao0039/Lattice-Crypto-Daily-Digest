# Documentation Map

This map is the starting point for the manual low-load research workflow documentation. It is navigation-only and does not define new workflow behavior.

Safety baseline: manual-only usage, dry-run default, explicit low-load mode, no-network / offline usage where supported, and local review before any write-enabled command. No scheduled automation is configured. Do not add Windows Task Scheduler entries, cron files, background services, startup tasks, watchers, or automatic scheduling from these docs.

## Manual operation

- [Manual operations runbook](manual-operations-runbook.md): safe daily operating commands, command safety matrix, generated artifact boundaries.
- [Workflow command center](workflow-command-center.md): `daily`, `weekly`, `full`, `status`, and `doctor` command behavior.
- [Manual low-load workflow](manual-low-load-workflow.md): explicit `--low-load`, `--no-network`, and `--offline` usage.
- [Manual Codex quality run prompt](manual-codex-quality-run-prompt.md): quality-first copy/paste prompt for manual Codex runs only.
- [Research scope taxonomy](research-scope-taxonomy.md): topical sections, inclusion rules, exclusion rules, and golden examples.
- [Research report quality](research-report-quality.md): report polish rules for paper facts, ranking explanation, source health caveats, anchor evidence, and advisory metadata.
- [Query expansion and negative keywords](query-expansion-and-negative-keywords.md): anchored query expansion and false-positive suppression boundaries.
- [Semantic Scholar enrichment](semantic-scholar-enrichment.md): optional metadata enrichment for existing papers; no API key is required for CI or normal digest generation.

## Recovery and safety

- [Recovery playbook](recovery-playbook.md): cleanup commands, reading queue backup, `papers.db` recovery, Windows SQLite file lock, tzdata / ZoneInfo.
- [Artifact retention policy](artifact-retention-policy.md): generated artifacts that must not be committed by default.
- [Troubleshooting](troubleshooting.md): CI, release hygiene, version mismatch, README links, workflow doctor, Windows, timezone, and line-ending issues.

## Pilot docs

- [One-week manual pilot](one-week-manual-pilot.md): 7-day manual low-load pilot routine.
- [Pilot acceptance checklist](pilot-acceptance-checklist.md): acceptance criteria for the manual pilot.
- [Pilot issue log template](pilot-issue-log-template.md): issue log fields for reproducible pilot feedback.
- [Pilot feedback triage](pilot-feedback-triage.md): issue categories, severity levels, and phase target labels.
- [Pilot feedback summary template](pilot-feedback-summary-template.md): reusable summary format after pilot runs.
- [Pilot fix prioritization](pilot-fix-prioritization.md): rules for choosing safe follow-up fixes.

## Release notes

- [Release checklist](release-checklist.md)
- [v0.3.3 release notes](releases/v0.3.3.md)
- [v0.3.2 release notes](releases/v0.3.2.md)
- [v0.3.1 release notes](releases/v0.3.1.md)
- [v0.3.0 release notes](releases/v0.3.0.md)
- [v0.2.0 release notes](releases/v0.2.0.md)
- [v0.2.0-rc1 release notes](releases/v0.2.0-rc1.md)
- [v0.1.0 release notes](releases/v0.1.0.md)

## Local state and artifacts

- reading queue manual statuses / local state live in `state/reading-queue.json` and should be preserved.
- generated artifacts must not be committed by default.
- `exports/`, `audits/`, `research_artifacts/`, `.pytest_tmp/`, `__pycache__/`, local logs, caches, and local test outputs are local artifacts unless an explicit release or digest publishing process says otherwise.
