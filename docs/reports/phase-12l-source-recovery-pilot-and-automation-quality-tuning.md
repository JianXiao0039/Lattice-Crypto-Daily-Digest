# Phase 12L Source Recovery Pilot and Automation Quality Tuning

生成日期：2026-06-08

本报告属于公开 source-recovery / automation quality tuning。它不包含 target PI email、SoP draft、PI-specific application note、funding strategy、personal PhD narrative、private application tracker 或 private application material。

# Executive Summary

Phase 12L used the current manual recovery and weekly handoff tooling to tune quality policy for the user-reported automation modules:

- Daily Public Digest Run: active
- Weekly Public Synthesis Run: active
- Full Manual Quality Run: paused

Source recovery pilot result:

- connectivity probe shows arXiv, Crossref, DBLP, IACR, and OpenAlex reachable;
- Semantic Scholar is not green in probe mode because the API currently returns HTTP 429 rate limit, even though the key is present;
- explicit manual recovery succeeded and confirmed usable source health for arXiv/Crossref/IACR, with IACR latest operating from same-day cache;
- the latest persisted daily artifact is now `data/2026-06-08.json` with 6 records, 2 green sources, 4 yellow sources, 0 red sources, and `source_starved=False`;
- the older `data/2026-06-07.json` artifact remains an important historical example of a source-starved day;
- weekly handoff remains usable because `handoffs/weekly/2026-W23-handoff-packets.json` contains 20 packets.

Daily Public Digest quality policy was improved through:

- a dedicated daily quality probe script;
- explicit source-starved interpretation policy;
- recommended prompt updates with quality gates;
- success metrics for daily module evaluation.

Weekly and Full Manual module policies were clarified. No new background automation was created. No private PhD files or ResearchArtifacts files were written.

# Automation Module Status

User-reported automation UI status:

- Daily Public Digest Run: active
- Weekly Public Synthesis Run: active
- Full Manual Quality Run: paused

Recommended role:

- Daily Public Digest Run: primary public source-intake module; must expose source health and source-starved outcome clearly.
- Weekly Public Synthesis Run: track-based synthesis on top of current weekly artifacts; must not overclaim when daily inputs are degraded.
- Full Manual Quality Run: heavier manual validation path for source recovery, tests, hygiene, and handoff refresh; it should remain paused unless intentionally used.

Recommended prompt updates are documented in:

- `docs/research_tracks/automation_module_prompt_recommendations_v0.1.md`

# Source Recovery Pilot Result

Commands run:

- `python --version`
- `python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; ..."`
- `python -m lattice_digest.workflow doctor`
- `python scripts\probe_source_connectivity.py`
- `scripts\recover_failed_sources_manual.bat`
- `scripts\run_project_tests.bat`
- `python scripts\check_release_hygiene.py`
- `git diff --check`
- `git status -sb`

Pilot summary:

- connectivity probe: arXiv/Crossref/DBLP/IACR/OpenAlex reachable; Semantic Scholar returned HTTP 429 rate limit;
- IACR latest: cache state visible, parser parsed 100 RSS records, latest recovery status effectively `cache_hit/100` during manual recovery;
- Semantic Scholar: key present, length 44, value not printed, probe classified as retryable rate limit rather than missing-key failure;
- manual recovery run: daily overwrite was skipped because `2026-06-08` already exists as `local_codex/authoritative`;
- latest persisted daily digest count: 6 in `data/2026-06-08.json`;
- latest persisted daily source health: 2 green, 4 yellow, 0 red, retryable count 1, `source_starved=False`;
- historical source-starved reference: `data/2026-06-07.json` with 0 records and all-red source health;
- weekly handoff output: 20 packets and 1 excluded item in `handoffs/weekly/2026-W23-handoff-packets.json`.

# Daily Public Digest Quality Tuning

Desired quality gates:

- report Python/env/doctor status;
- expose per-source health and retryable error counts;
- classify `0 records + all-red sources` as source-starved;
- report IACR latest state and Semantic Scholar enrichment availability;
- end with validation summary and `git status -sb`;
- never print secrets;
- never auto-commit/push;
- never write `PhD_Application` or `D:\ResearchArtifacts`.

Recommended helper:

- `scripts\daily_quality_probe.bat`
- `scripts\daily_quality_probe.ps1`

Success metrics are defined in:

- `docs/research_tracks/daily_success_metrics_v0.1.md`

TODO_VERIFY:

- whether three consecutive daily runs remain stable;
- whether source-starved status should be surfaced directly in automation UI prompt text.

# Weekly Public Synthesis Quality Tuning

Desired quality gates:

- operate on current weekly artifacts only;
- generate track-based synthesis and then weekly handoff;
- if weekly input is source-starved or partly source-starved, label coverage conservatively;
- do not interpret empty or sparse weekly outputs as no relevant papers;
- do not touch private or ResearchArtifacts workspaces;
- do not auto-commit/push.

Policy is documented in:

- `docs/research_tracks/weekly_public_synthesis_quality_policy_v0.1.md`

TODO_VERIFY:

- whether weekly module prompt should mention missing loaded days explicitly;
- whether weekly handoff should surface latest daily source-starved warning inline.

# Full Manual Quality Run Policy

Why it can remain paused:

- it is intentionally heavier than the daily/weekly paths;
- it is appropriate for source recovery pilots, tests, hygiene checks, and handoff refresh;
- it should not behave like a default background service.

What not to do:

- no scheduler;
- no background retry loop;
- no auto-commit/push;
- no private application writes;
- no business-logic mutation unless explicitly requested.

Policy is documented in:

- `docs/research_tracks/full_manual_quality_run_policy_v0.1.md`

TODO_VERIFY:

- whether the module should remain paused after several successful daily runs.

# Source Health Recovery Details

| Source | Current status | Error class | Manual recovery path | TODO_VERIFY |
| --- | --- | --- | --- | --- |
| arxiv | green in latest daily artifact | probe reachable; no active failure in latest run | rerun manual recovery only when future daily runs degrade | source-specific rate-limit stability |
| crossref | green in latest daily artifact | probe reachable; no active failure in latest run | rerun manual recovery only when future daily runs degrade | transient network sensitivity |
| dblp | yellow in latest daily artifact | ingestion-time `ssl_error` despite successful connectivity probe | retry later manually; do not reinterpret as ranking/taxonomy issue | batch-query SSL stability |
| iacr_eprint | yellow in latest daily artifact, but latest feed operational | same-day cache hit / latest feed parsed 100 RSS records | `--retry-failed-sources --include-latest-sources` or recovery script | feed stability over next days |
| openalex | yellow in latest daily artifact | reachable in probe; 0 final records in current digest window | rerun manually only if coverage matters | whether zero results are normal for the query window |
| semantic_scholar | yellow in latest daily artifact | probe `rate_limit` HTTP 429; advisory enrichment only | keep advisory-only; retry manually when quota/window clears | quota/auth stability |

# Code / Script / Docs Changes

| Path | Reason | Risk | Test coverage |
| --- | --- | --- | --- |
| `scripts/daily_quality_probe.bat` | manual daily quality gate helper | low; read-only quality summary | validated manually in this phase |
| `scripts/daily_quality_probe.ps1` | PowerShell variant of daily quality probe | low | validated manually in this phase |
| `docs/reports/phase-12l-source-recovery-pilot-and-automation-quality-tuning.md` | 12L main report | low | documentation only |
| `docs/reports/phase-12l-daily-public-digest-quality-audit.md` | focused daily-module quality audit | low | documentation only |
| `docs/research_tracks/daily_public_digest_quality_policy_v0.1.md` | daily module policy | low | documentation only |
| `docs/research_tracks/weekly_public_synthesis_quality_policy_v0.1.md` | weekly module policy | low | documentation only |
| `docs/research_tracks/full_manual_quality_run_policy_v0.1.md` | full manual module policy | low | documentation only |
| `docs/research_tracks/automation_module_prompt_recommendations_v0.1.md` | prompt recommendations for UI updates | low | documentation only |
| `docs/research_tracks/source_recovery_pilot_run_log_v0.1.md` | pilot run evidence log | low | documentation only |
| `docs/research_tracks/daily_success_metrics_v0.1.md` | metric definitions | low | documentation only |
| `docs/research_tracks/source_starved_triage_checklist_v0.1.md` | operator checklist | low | documentation only |

# Validation Results

| Check | Result |
| --- | --- |
| Python version | `Python 3.15.0b2` |
| Environment import check | passed |
| Doctor | passed |
| Source probe | passed; Semantic Scholar returned HTTP 429 rate limit; other five probe endpoints reachable |
| Manual recovery command | passed via `scripts\recover_failed_sources_manual.bat` |
| Weekly handoff generation | passed via `scripts\run_weekly_handoff.bat`; 20 packets |
| Tests | passed: `423 passed` |
| Release hygiene | passed |
| `git diff --check` | passed with LF/CRLF working-copy warnings |
| `git status -sb` | shows Phase 12L files plus pre-existing Phase 12G/12H/12K worktree state |

# TODO_VERIFY

- source stability over next 3 daily runs;
- Semantic Scholar rate-limit behavior over repeated manual runs;
- IACR latest guard behavior after same-day successful cache hit;
- whether Daily / Weekly / Full module prompt text should be updated manually in ChatGPT automation UI;
- whether Full Manual Quality Run should stay paused.
