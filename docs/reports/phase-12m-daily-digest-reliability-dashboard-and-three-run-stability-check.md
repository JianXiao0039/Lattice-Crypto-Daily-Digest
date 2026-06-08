# Phase 12M Daily Digest Reliability Dashboard and Three-Run Stability Check

生成日期：2026-06-08

本报告属于公开 reliability / source-health / automation quality 文档，不包含任何 private PhD application material，也不写入 `D:\ResearchArtifacts`。

# Executive Summary

Phase 12M 已完成 three-run stability check，并新增一个可重复执行的 daily reliability dashboard 生成器：

- `scripts\daily_reliability_dashboard.py`
- `scripts\daily_reliability_dashboard.bat`
- `scripts\daily_reliability_dashboard.ps1`
- `src/lattice_digest/reliability_dashboard.py`

当前 daily reliability 相比 12J 的全红状态已经明显改善：

- 最新日报 `data/2026-06-08.json` 含 6 条记录；
- source health 为 2 green / 4 yellow / 0 red；
- `source_starved=False`；
- IACR latest 处于可见、可解析状态，当前指标为 `fetched/100`，手动 recovery 视角为 `cache_hit/100`；
- Semantic Scholar 当前 key 已存在且长度可安全观测为 44，本轮 probe 返回 200，可达；但最新日报中 enrichment 仍表现为 `no_candidates_to_enrich`，应继续视为 advisory-only；
- weekly handoff 复跑成功，`handoffs/weekly/2026-W23-handoff-packets.json` 当前含 20 个 packet，未把 source-starved 日误报成“无论文”。

结论：

- 三跑稳定性检查完成；
- 当前 sources 不再 all-red；
- Daily Public Digest Run 与 Weekly Public Synthesis Run 的 prompt 推荐应手工更新到 v0.2；
- Full Manual Quality Run 仍应保持 paused，并作为重型人工恢复/验证 profile 使用。

# Automation Module Status

当前 automation-module 状态（用户提供）：

- Daily Public Digest Run：active
- Weekly Public Synthesis Run：active
- Full Manual Quality Run：paused

建议角色：

- Daily Public Digest Run：主公开 intake 模块；必须显式展示 source health、source-starved、IACR latest、Semantic Scholar 状态。
- Weekly Public Synthesis Run：基于当前 weekly artifacts 做 track-based synthesis，并调用 weekly handoff。
- Full Manual Quality Run：仅用于重型人工验证、source recovery、tests、release hygiene、weekly handoff refresh；不应作为日常默认模块。

推荐更新文本见：

- `docs/research_tracks/automation_module_prompt_recommendations_v0.2.md`
- `docs/research_tracks/daily_public_digest_run_prompt_v0.2.md`
- `docs/research_tracks/weekly_public_synthesis_run_prompt_v0.2.md`
- `docs/research_tracks/full_manual_quality_run_prompt_v0.2.md`

# Three-Run Stability Check

## Run 1: Probe-only health check

- command: `python scripts\probe_source_connectivity.py`
- result: passed
- artifacts: no digest generation required; stdout JSON probe report only
- source status:
  - arxiv: reachable 200
  - crossref: reachable 200
  - dblp: TLS EOF, retryable
  - iacr_eprint: reachable 200, parser parsed 100 records
  - openalex: reachable 200
  - semantic_scholar: reachable 200, key present, key value not printed
- failure reason:
  - DBLP 在 probe 阶段仍表现为 TLS 类 retryable failure
- reliability interpretation:
  - 当前不是全网 all-red；
  - network/source readiness 已恢复到“可运行但部分降级”的状态；
  - DBLP 仍是主要不稳定源。
- TODO_VERIFY:
  - DBLP 的 probe-level TLS 异常是否与 ingest path 的 SSL warning 同源。

## Run 2: Manual recovery daily run

- command: `python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources`
- result: passed
- artifacts:
  - 未覆盖 `2026-06-08`，因为现有报告已是 `local_codex/authoritative`
- source status:
  - arxiv: green, final=5
  - crossref: green, final=1
  - dblp: yellow, retryable warning
  - iacr_eprint: yellow, latest=`cache_hit/100`
  - openalex: yellow, final=0
  - semantic_scholar: yellow, final=0
- failure reason:
  - 无硬失败；写入被保护策略阻止，不是 run failure
- reliability interpretation:
  - failed-attempt guard 与 authoritative overwrite guard 都按预期工作；
  - recovery command 能恢复 source health 可见性，但不会静默覆盖 authoritative 产物；
  - Daily module 已具备 bounded manual recovery 行为。
- TODO_VERIFY:
  - 若未来 source-starved 日再次出现，是否仍能在同样 flags 下稳定恢复。

## Run 3: Weekly handoff replay / synthesis check

- requested command: `python scripts\generate_weekly_handoff.py --latest`
- actual status: missing command; repository 中不存在该脚本
- working command used: `scripts\run_weekly_handoff.bat`
- result: passed
- artifacts:
  - `handoffs/weekly/2026-W23-handoff-packets.json`
  - `handoffs/weekly/2026-W23-handoff-packets.md`
- source status:
  - packets=20
  - excluded=1
  - weekly coverage missing days=`2026-06-06, 2026-06-07`
- failure reason:
  - 无；但需明确 `scripts\generate_weekly_handoff.py` 缺失
- reliability interpretation:
  - weekly handoff 当前可靠；
  - weekly output 没有把 source-starved 日误解释成“本周无相关论文”；
  - 未来 prompt / runbook 中应只写实际存在的入口。
- TODO_VERIFY:
  - 是否需要在后续 phase 单独补一个 Python wrapper，而不是继续仅依赖 `.bat` 和 `-m` 入口。

# Daily Digest Reliability Dashboard

当前 dashboard 由 `python scripts\daily_reliability_dashboard.py` 生成，当前摘要如下：

| Metric | Value |
| --- | --- |
| `python_version` | `3.15.0b2` |
| `package_version` | `0.3.3` |
| `source_total_count` | `6` |
| `source_green_count` | `2` |
| `source_yellow_count` | `4` |
| `source_red_count` | `0` |
| `source_reachability_rate` | `1.0` |
| `retryable_error_count` | `0` |
| `non_retryable_error_count` | `0` |
| `digest_record_count` | `6` |
| `final_record_count` | `6` |
| `high_priority_count` | `5` |
| `iacr_latest_status` | `fetched` |
| `iacr_latest_records` | `100` |
| `semantic_scholar_key_present_boolean` | `True` |
| `semantic_scholar_key_length_only_if_safe` | `44` |
| `semantic_scholar_enrichment_status` | `no_candidates_to_enrich` |
| `source_starved_true_false` | `False` |
| `empty_digest_reason` | `non_empty` |
| `weekly_handoff_candidate_count` | `20` |
| `weekly_handoff_source_starved_true_false` | `False` |
| `generated_artifacts_present` | `True` |
| `validation_passed` | `True` |
| `manual_recovery_needed` | `False` |

dashboard 解读：

- 当前 daily run 不是 source-starved；
- 当前 probe 视角下 6 个 source endpoint 都可达；
- 但 ingest 视角下 latest daily 仍有 4 个 yellow source，说明“probe green 不等于 ingest green”；
- Semantic Scholar 当前不是 missing key / auth failure，而是“key 在、本轮 probe 可达、latest daily 无 enrichment candidate”的状态；
- weekly handoff 当前可视为可靠，但 coverage 仍缺两天，需要保守解释。

# Source Health and Recovery Details

| Source | Status | Observed error | Likely class | Manual recovery path | Risk |
| --- | --- | --- | --- | --- | --- |
| arxiv | green | none | reachable | 仅在未来降级时重跑 recovery | low |
| crossref | green | none | reachable | 仅在未来降级时重跑 recovery | low |
| dblp | yellow | probe: TLS EOF; ingest: warning / SSL path issue | tls / retryable | 手工重跑 probe + recovery；不要误判成 ranking/taxonomy 问题 | medium |
| iacr_eprint | yellow but operational | latest visible; parser parsed 100; recovery=`cache_hit/100` | cache_hit / latest feed operational | `--retry-failed-sources --include-latest-sources` 或 recovery script | low |
| openalex | yellow | no hard error; current final=0 | no_results_or_low_signal | 仅在 coverage 需要时手工复查 | low |
| semantic_scholar | yellow | latest daily 无 candidate enrichment；probe 本轮可达 | advisory/no_candidates | 保持 optional enrichment；手工观察限流与候选出现情况 | medium |

# IACR Latest Recovery Status

本轮区分结果：

- feed unreachable：否
- parser failure：否
- failed-attempt guard：未阻断当前手工恢复
- cache hit：是，Run 2 中表现为 `cache_hit/100`
- manual retry success：是
- latest feed has 0 records：否
- TODO_VERIFY：
  - 未来连续三天运行时，`attempt marker + xml cache` 的组合是否继续稳定

# Semantic Scholar Enrichment Status

本轮区分结果：

- key missing：否
- key present：是
- auth failure：否
- rate limit：本轮 direct probe 未出现；历史上出现过
- network failure：本轮否
- no candidates to enrich：latest daily artifact 视角下是
- enrichment successful：本轮 latest daily artifact 未观察到成功 enrichment record
- TODO_VERIFY：
  - 在后续 3 次日跑里，rate-limit 与 no-candidate 两种状态是否会来回切换

# Automation Prompt Recommendations v0.2

本 phase 的 prompt 调整重点：

- Daily Public Digest Run：
  - 增加 reliability dashboard / source-starved / IACR latest / Semantic Scholar status 质量门槛
  - 仅使用存在的命令
  - 强制输出 `git status -sb`
- Weekly Public Synthesis Run：
  - 使用实际存在的 weekly handoff 入口
  - 对 missing days 与 source-starved 周输入做显式说明
- Full Manual Quality Run：
  - 保持 paused
  - 只作为恢复、tests、release hygiene、handoff refresh 的人工 profile

用户需要手工在 ChatGPT automation UI 中更新 prompt；仓库只能提供推荐文本，不能直接修改 UI。

# Code / Script / Docs Changes

| Path | Reason | Risk | Test coverage |
| --- | --- | --- | --- |
| `src/lattice_digest/reliability_dashboard.py` | 新增可测试的 reliability dashboard 逻辑 | low | `tests/test_daily_reliability_dashboard.py`, `tests/test_daily_success_metrics.py` |
| `scripts/daily_reliability_dashboard.py` | CLI 入口 | low | targeted tests + manual run |
| `scripts/daily_reliability_dashboard.bat` | cmd 入口 | low | manual run path available |
| `scripts/daily_reliability_dashboard.ps1` | PowerShell 入口 | low | command reviewed |
| `docs/reports/phase-12m-daily-digest-reliability-dashboard-and-three-run-stability-check.md` | 12M 主报告 | low | documentation only |
| `docs/reports/phase-12m-three-run-stability-check-log.md` | 三跑日志 | low | documentation only |
| `docs/research_tracks/daily_digest_reliability_dashboard_v0.1.md` | dashboard 说明 | low | documentation only |
| `docs/research_tracks/daily_digest_three_run_stability_protocol_v0.1.md` | 三跑协议 | low | documentation only |
| `docs/research_tracks/daily_digest_success_metrics_v0.2.md` | v0.2 指标定义 | low | documentation only |
| `docs/research_tracks/daily_digest_failure_classification_v0.1.md` | failure classification 文档 | low | documentation only |
| `docs/research_tracks/automation_module_prompt_recommendations_v0.2.md` | v0.2 prompt 推荐总览 | low | documentation only |
| `docs/research_tracks/daily_public_digest_run_prompt_v0.2.md` | Daily prompt 推荐文本 | low | documentation only |
| `docs/research_tracks/weekly_public_synthesis_run_prompt_v0.2.md` | Weekly prompt 推荐文本 | low | documentation only |
| `docs/research_tracks/full_manual_quality_run_prompt_v0.2.md` | Full Manual prompt 推荐文本 | low | documentation only |
| `tests/test_daily_reliability_dashboard.py` | dashboard 指标/CLI 测试 | low | targeted tests passed |
| `tests/test_daily_success_metrics.py` | success metrics 纯函数测试 | low | targeted tests passed |

# Validation Results

| Check | Result |
| --- | --- |
| Python version | `Python 3.15.0b2` |
| Environment import check | passed |
| Doctor | passed |
| Source probe | passed; DBLP TLS retryable; arXiv/Crossref/IACR/OpenAlex/Semantic Scholar reachable |
| Manual recovery run | passed; overwrite skipped by authoritative guard |
| Weekly handoff run | passed via `scripts\run_weekly_handoff.bat`; 20 packets |
| Reliability dashboard generation | passed via `python scripts\daily_reliability_dashboard.py` and `scripts\daily_reliability_dashboard.bat` |
| Tests | targeted tests passed; full suite `430 passed` |
| Release hygiene | passed |
| `git diff --check` | passed; only LF/CRLF working-copy warnings |
| `git status -sb` | dirty worktree includes prior Phase 12G/12H/12K/12L files plus new Phase 12M files; no private workspace paths touched |

# TODO_VERIFY

- next 3 actual daily automation results under normal schedule;
- source stability over the next 3 daily runs;
- Semantic Scholar rate-limit behavior vs no-candidate behavior;
- whether dashboard metrics should be committed weekly or kept manual-only;
- whether Full Manual Quality Run should remain paused after a longer stable window.
