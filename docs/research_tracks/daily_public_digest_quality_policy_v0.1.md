# Daily Public Digest Quality Policy v0.1

Status: public daily-module quality policy.

# Purpose

Define the expected behavior of the Daily Public Digest Run under manual-safe constraints.

# Required Behavior

The daily module should:

1. expose source-health results or provide direct access to them;
2. generate daily Markdown/JSON only through project workflow commands;
3. treat `0 records + all-red source health` as source-starved, not normal success;
4. report per-source status clearly;
5. report IACR latest recovery status clearly;
6. report Semantic Scholar enrichment availability clearly;
7. never print API keys;
8. prefer quality-first generation when manually triggered;
9. avoid dry-run for final generation unless explicitly requested;
10. not create scheduled tasks or background services;
11. not commit or push automatically;
12. not write `PhD_Application` or `D:\ResearchArtifacts`;
13. end with `git status -sb` and validation summary.

# Recommended Quality Gates

- environment imports pass;
- `python -m lattice_digest.workflow doctor` passes;
- source connectivity probe available;
- daily output is checked for source-starved status;
- latest source-health ledger/audit is inspected when available.

# Recommended Commands

```powershell
scripts\daily_quality_probe.bat
python scripts\probe_source_connectivity.py
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
git status -sb
```

# Forbidden Actions

- no background automation;
- no Task Scheduler;
- no cron;
- no auto-commit/push;
- no secret printing;
- no private workspace writes.

