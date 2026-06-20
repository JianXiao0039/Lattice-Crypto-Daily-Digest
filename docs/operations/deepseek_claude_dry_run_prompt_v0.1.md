# DeepSeek-Claude Dry Run Prompt v0.1

Project root: `D:\Code\CodexProjects\lattice-crypto-daily-digest`

Current active route: only the public paper-radar route is active.

Operator: DeepSeek-Claude.

Operator role: emergency fallback runner/reviewer. DeepSeek-Claude is not the release owner and must not modify code unless explicitly authorized. If code changes appear necessary, stop and request Codex review.

Before running, restate:

- active project path;
- private paths are forbidden;
- git write/tag commands are forbidden;
- background automation is forbidden;
- source/ranking/taxonomy changes are forbidden;
- external LLM runtime additions are forbidden.

Forbidden:

- read or write `D:\Code\CodexProjects\PhD_Application`;
- read or write `D:\ResearchArtifacts`;
- write `D:\ResearchOS`;
- run `git add`, `git commit`, `git push`, or `git tag`;
- create release tags;
- create Windows Task Scheduler tasks, cron jobs, startup tasks, watchers, background services, or automatic future runs;
- modify source fetchers, ranking scores, ranking thresholds, taxonomy semantics, query expansion, or negative keyword behavior;
- create manual annotation workflows, human-gold workflows, or shadow classifier productionization;
- add external LLM runtime calls;
- print secrets or `.env` contents;
- rely on memory as factual evidence.

Required task set:

1. Boundary confirmation.
2. `git status -sb`.
3. `python --version`.
4. `python -m lattice_digest.workflow doctor`.
5. `python -m lattice_digest.workflow status`.
6. `python -m lattice_digest.run --since 36h --output markdown,json --send none`.
7. `python -m lattice_digest.workflow weekly --low-load --skip-hygiene`.
8. `python -m lattice_digest.monthly_synthesis --month 2026-06`.
9. `python scripts/probe_source_health.py --low-load`.
10. `python scripts/verify_durable_artifacts.py --date 2026-06-15 --week 2026-W25 --month 2026-06`.
11. `python scripts/export_reading_queue.py --latest`.
12. `python scripts/export_obsidian_notes.py --latest`.
13. `python scripts/audit_monthly_rationale_quality.py --latest`.
14. `git diff --check`.
15. `git diff --cached --check`.
16. `git status -sb`.

Final report must be in Chinese and include:

- Operator
- Boundaries
- Commands Run
- Artifacts Generated
- Source Health
- Radar Output Quality
- Durable Artifact Status
- Failures / Warnings
- Next Recommended Operator
- Final Status

