# Phase 12Q: Daily Automation Stabilization Decision and v0.4 Planning

生成日期：2026-06-10

# Executive Summary

- 2026-06-04 through 2026-06-10 的本地 backfill / refresh 产物不完整。
- daily artifacts 存在于 `2026-06-04`, `2026-06-05`, `2026-06-07`, `2026-06-08`, `2026-06-10`；缺失 `2026-06-06` 和 `2026-06-09`。
- 2026-06-04 / 05 / 07 是 source-starved，不应解释为“无相关论文”。
- 2026-06-08 / 10 恢复为 degraded-but-usable；2026-06-10 有 18 条记录、9 条高优先级记录、IACR latest `fetched/100`。
- Weekly artifact 仍是 `2026-W23`，窗口到 `2026-06-07`，未覆盖到 `2026-06-10`；weekly handoff 仍为 `2026-W23`，20 packets。
- Daily Public Digest Run stabilization decision: `insufficient_evidence`。
- Weekly Public Synthesis Run decision: `keep_active_with_source_starved_warning`。
- Full Manual Quality Run decision: `keep_paused`，除非用户要做发布前验证或连续失败恢复。
- v0.4 推荐聚焦 source-health reliability、source-starved false-success prevention、IACR latest recovery、Semantic Scholar diagnostics、daily reliability dashboard、weekly handoff quality。

# Backfill Audit

| date | digest MD | data JSON | record count | source health | source-starved | IACR latest | Semantic Scholar | notes |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `2026-06-04` | yes | yes | 0 | 0 green / 0 yellow / 6 red | true | `failed/0` | `source_red` | source-starved |
| `2026-06-05` | yes | yes | 0 | 0 green / 0 yellow / 6 red | true | `failed/0` | `source_red` | source-starved |
| `2026-06-06` | no | no | n/a | missing | false | `missing/0` | `missing` | TODO_VERIFY missing artifact |
| `2026-06-07` | yes | yes | 0 | 0 green / 0 yellow / 6 red | true | `failed/0` | `source_red` | source-starved |
| `2026-06-08` | yes | yes | 6 | 2 green / 4 yellow / 0 red | false | `fetched/100` | `key_used` | degraded-but-usable |
| `2026-06-09` | no | no | n/a | missing | false | `missing/0` | `missing` | TODO_VERIFY missing artifact |
| `2026-06-10` | yes | yes | 18 | 2 green / 4 yellow / 0 red | false | `fetched/100` | `key_used` | degraded-but-usable |

GitHub-ready artifact status:

- Not ready as a complete 2026-06-04 through 2026-06-10 submission, because 2026-06-06 and 2026-06-09 are missing.
- Some local artifacts may already have prior commits or partial refresh history, but this phase did not stage or submit anything.
- Before GitHub submission, decide whether to backfill missing dates or explicitly exclude them with documented source-starved / missing-artifact rationale.

# Automation Stabilization Decision

| module | decision | reason | risk |
| --- | --- | --- | --- |
| Daily Public Digest Run | `insufficient_evidence` | window has missing dates and three source-starved days, despite 2026-06-08 / 10 recovery | cannot claim stable automation over the full period |
| Weekly Public Synthesis Run | `keep_active_with_source_starved_warning` | handoff still works and produces 20 packets, but weekly artifact only covers W23 and misses 2026-06-06 / 07 | weekly can amplify stale/source-starved input |
| Full Manual Quality Run | `keep_paused` | latest available daily is usable and tests pass | run once manually only for release / GitHub submission validation |

# Source Health Summary

| source | status over window | v0.4 implication |
| --- | --- | --- |
| arxiv | red on 06-04/05/07, recovered by 06-08/10 | require source-starved labeling and retry visibility |
| crossref | red on 06-04/05/07, recovered by 06-08/10 | same |
| dblp | red then yellow; 06-10 has `ssl_error` retryable warning | preserve yellow diagnostics and manual retry path |
| iacr_eprint | `failed/0` then `fetched/100` | keep latest recovery diagnostics central |
| openalex | red then yellow with zero final records | keep separate from paper irrelevance |
| semantic_scholar | red then yellow/key_used | keep advisory-only and no-key-printing policy |

# v0.4 Planning

## Goal

Make the public digest workflow reliable enough that daily/weekly outputs distinguish healthy discovery, source-starved runs, partial source degradation, and handoff-quality status without private-data leakage or background automation.

## Non-Goals

- No private PhD application tooling.
- No target PI email or SoP generation.
- No automatic background service.
- No source ranking overhaul unless a reliability bug requires it.
- No default single-paper deep reading engine.

## Planned Work Packages

1. Source-health reliability: consolidate red/yellow/green interpretation across daily, weekly, audit, and dashboard.
2. Source-starved false-success prevention: every empty output must explain whether sources were all-red.
3. IACR latest recovery: distinguish `failed/0`, cache hit, parser failure, manual retry, and successful fetched state.
4. Semantic Scholar diagnostics: report key presence safely, no key values, rate-limit/auth/network/no-candidate states.
5. Daily reliability dashboard: include missing-artifact windows and latest three-run trend.
6. Weekly handoff quality: warn when handoff is based on source-starved or incomplete weekly input.
7. Module-SIS track usefulness: keep handoff packets relevant to the public research radar, not private planning.
8. Manual recovery commands: keep manual-only scripts explicit and non-scheduled.
9. Release hygiene: ensure docs/scripts/tests do not recommend forbidden commands.

## Tests

- Backfill audit script tests.
- Source-starved classification tests.
- Weekly handoff tests.
- Reliability dashboard tests.
- Documentation command-policy tests.

## Risk

- Missing dates can look like successful quiet days unless explicitly labeled.
- Weekly reports can mask daily source failures.
- Semantic Scholar availability can fluctuate and must remain advisory.
- GitHub submission could include generated artifacts unintentionally if commit scope is not reviewed.

# GitHub Submission Review

Expected commit candidates after user approval only:

- Phase 12G-12Q public docs if the user wants to publish the workflow evolution.
- Additive scripts:
  - `scripts\generate_weekly_handoff.py`
  - `scripts\summarize_three_day_observation.py`
  - `scripts\audit_backfill_2026_06_04_to_2026_06_10.py`
- Focused tests:
  - `tests\test_three_day_observation_summary.py`
  - `tests\test_backfill_audit.py`
- Daily digest artifacts only if the user explicitly wants generated artifacts submitted.

Recommended grouping:

1. Source-health / reliability tooling and tests.
2. Weekly handoff / research-track docs.
3. Generated digest artifacts, if approved, as a separate commit.

Do not commit by default:

- `.env`
- secrets
- `papers.db` unless explicitly approved as generated digest state
- `.arts/`
- `.pytest_tmp/`
- caches / logs / `__pycache__`
- private PhD materials
- `D:\ResearchArtifacts` files

Post-push verification, if the user later asks to submit:

- `git status -sb`
- `git diff --check`
- `scripts\run_project_tests.bat`
- `python scripts\check_release_hygiene.py`
- Verify GitHub Actions output does not claim missing dates are successful discovery days.

# Regression Check

| check | result |
| --- | --- |
| Python | `3.15.0b2` |
| env import check | passed |
| doctor | passed |
| backfill audit | passed |
| weekly handoff | passed, 20 packets |
| project tests | passed, 435 tests |
| release hygiene | passed |
| git diff --check | passed with existing `.gitignore` CRLF/LF warning |
| private writes | none |

# TODO_VERIFY

- Backfill or explicitly document `2026-06-06` and `2026-06-09`.
- Observe next Daily Public Digest Run.
- Observe next Weekly Public Synthesis Run.
- Verify whether all sources remain green/yellow without returning to all-red.
- Verify Semantic Scholar does not return repeated rate-limit/auth failures.
- Verify IACR latest remains `fetched` or `cache_hit`.
- Decide whether Full Manual Quality Run should run once before GitHub submission.
