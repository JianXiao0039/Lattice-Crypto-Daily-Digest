# Phase 12I Weekly Handoff Integration into Manual Quality Runs

生成日期：2026-06-07

本报告属于公开 research tooling integration。它不包含 target PI email、SoP draft、private application tracker、funding strategy、personal PhD narrative 或 private advisor-specific material。

# Executive Summary

Phase 12I integrates the standalone Weekly Handoff Packet Generator into the manual public workflow.

What changed:

- added manual helper scripts for weekly handoff generation;
- added runbooks for manual weekly handoff, full manual quality runs with handoff, and weekly public synthesis with handoff;
- added README and docs index navigation links;
- documented that daily public digest remains discovery-oriented;
- documented that weekly/full manual quality runs may include weekly handoff only as an explicit manual step.

What did not change:

- no source fetching semantics changed;
- no ranking thresholds changed;
- no taxonomy, section classifier, query expansion, negative keyword, source health, or release hygiene semantics changed;
- no automatic scheduler, Windows Task Scheduler, cron, background service, startup task, or future automatic run was created;
- no `PhD_Application` files were written;
- no ResearchArtifacts files were written.

# Input Evidence Used

| Input | Status | How used | Limitation |
| --- | --- | --- | --- |
| `src/lattice_digest/weekly_handoff.py` | available | Confirmed supported command and output paths | Standalone generator only |
| `tests/test_weekly_handoff.py` | available | Confirmed existing generator safety tests | Not modified in this phase |
| Phase 12G report | available | Confirmed v0.1 implementation scope | Historical implementation report |
| Phase 12H report | available | Confirmed hardening and manual command | Historical hardening report |
| usage guide v0.2 | available | Baseline for manual command documentation | No script wrapper existed yet |
| schema/non-claims/troubleshooting v0.2 docs | available | Preserved claim and safety boundaries | Documentation only |
| `scripts/run_project_tests.bat` | available | Validation helper for repository-scoped tests | Manual test helper only |
| `scripts/run_daily_digest.ps1` | available | Reviewed daily run style | Not modified |
| `scripts/run_daily_digest_and_push.ps1` | available | Confirmed push-oriented script is separate | Not modified |
| `README.md` | available | Added navigation to manual handoff docs | Public docs only |
| `docs/index.md` | available | Added navigation to manual handoff docs | Public docs only |
| `docs/manual-operations-runbook.md` | available | Added command safety notes | Public docs only |
| `handoffs/weekly/` | available | Generator output target | Generated and ignored by git |
| ResearchArtifacts RA-5 references | not required | This phase did not need read-only artifact context | ResearchArtifacts was not touched |

# Manual Integration Design

Daily Public Digest Run remains discovery-oriented. It may generate daily research digest artifacts, but it should not automatically create weekly handoff packets.

Weekly Public Synthesis Run can be followed by weekly handoff generation as an explicit manual step:

1. inspect or generate the weekly synthesis;
2. run the weekly handoff helper;
3. review `handoffs/weekly/YYYY-Www-handoff-packets.md`;
4. decide manually whether any item should move into ResearchArtifacts.

Full Manual Quality Run can include weekly handoff generation as a final explicit step after digest, weekly synthesis, doctor, tests, and release hygiene checks.

Source recovery remains separate. Weekly handoff generation reads existing weekly JSON and does not fetch sources, retry sources, or alter source health.

No scheduler is created. The integration is script and documentation only.

# Scripts Added or Updated

| Script | Purpose | Command sequence | Safety boundary | Expected output | Limitations |
| --- | --- | --- | --- | --- | --- |
| `scripts/run_weekly_handoff.bat` | cmd manual helper | cd project, set local temp, run Python/env check, run `python -m lattice_digest.weekly_handoff --latest` | no git, no scheduler, no `PhD_Application` | `handoffs/weekly/YYYY-Www-handoff-packets.json` and `.md` | Requires existing weekly JSON |
| `scripts/run_weekly_handoff.ps1` | PowerShell manual helper | set project location, set local temp, run Python/env check, run `python -m lattice_digest.weekly_handoff --latest` | no git, no scheduler, no `PhD_Application` | `handoffs/weekly/YYYY-Www-handoff-packets.json` and `.md` | Requires existing weekly JSON |

No existing workflow script was changed to force handoff generation by default.

# Documentation Added or Updated

| Doc | Purpose | How to use |
| --- | --- | --- |
| `docs/research_tracks/manual_weekly_handoff_runbook_v0.1.md` | Operator runbook for weekly handoff generation | Use for standalone manual generation and review |
| `docs/research_tracks/full_manual_quality_run_with_handoff_v0.1.md` | Full manual quality run sequence with optional handoff | Use when doing a quality-first manual public refresh |
| `docs/research_tracks/weekly_public_synthesis_with_handoff_v0.1.md` | Weekly synthesis plus handoff sequence | Use after weekly synthesis artifacts exist |
| `README.md` | Top-level navigation | Links to manual handoff docs |
| `docs/index.md` | Documentation map | Links to manual handoff docs |
| `docs/manual-operations-runbook.md` | Manual operations command matrix | Lists handoff helper as write-enabled manual command |

# Non-Claims and TODO_VERIFY Preservation

Weekly handoff remains research triage only:

- not a security proof;
- not a novelty claim;
- not a construction-validity claim;
- not a publication claim;
- not a claim that a PI works on a topic.

Xingye Lu bridge candidates remain TODO_VERIFY unless officially verified from public sources. Generic or noisy records remain excluded unless clear lattice/PQC/HE/FHE/LWE/RLWE/MLWE/SIS/Module-SIS/NTRU/ML-KEM/ML-DSA anchor evidence is present.

# Manual Usage

These commands exist and work in this repository:

```cmd
scripts\run_weekly_handoff.bat
```

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\run_weekly_handoff.ps1
```

```powershell
python -m lattice_digest.weekly_handoff --latest
```

Dry-run preview:

```powershell
python -m lattice_digest.weekly_handoff --latest --dry-run
```

There is no `scripts\generate_weekly_handoff.py` wrapper. Use the module command or the manual scripts above.

# Validation Results

Validation status is recorded after local commands complete:

| Check | Result |
| --- | --- |
| Python version | `Python 3.15.0b2` |
| Environment import check | passed: `pytest`, `pydantic`, and `ZoneInfo("Asia/Singapore")` import successfully |
| Workflow doctor | passed; package version `0.3.3`, timezone check passed, release hygiene check passed |
| Weekly handoff generation | passed via `python -m lattice_digest.weekly_handoff --latest`, `scripts\run_weekly_handoff.bat`, and `scripts\run_weekly_handoff.ps1` |
| Generated handoff files | `handoffs\weekly\2026-W23-handoff-packets.json` and `handoffs\weekly\2026-W23-handoff-packets.md` |
| Project tests | passed: `415 passed` via `scripts\run_project_tests.bat` |
| Release hygiene | passed: `version ok: 0.3.3`; legacy tracked digest artifacts noted |
| `git diff --check` | passed with LF/CRLF working-copy warnings |
| `git status -sb` | shows this phase's docs/scripts plus pre-existing generated artifact changes and earlier Phase 12G/12H untracked files |

# Risks and Limitations

- Generated handoff may be empty if weekly data has no candidates.
- Handoff quality depends on weekly JSON metadata and source health.
- ResearchArtifacts sync remains manual.
- Generated handoff output is ignored by git and should not be committed by default.
- The handoff generator does not read original papers, prove security, or verify novelty.
- This workflow has no PhD application usage.

# TODO_VERIFY

- Whether future Full Manual Quality Run should call the handoff script by default.
- Whether weekly handoff outputs should ever be committed by default.
- Whether handoff scoring should be tuned after several manually reviewed weeks.
- Whether ResearchArtifacts mirroring should remain manual.
- Whether weekly synthesis code should eventually expose track-based handoff summaries directly.
