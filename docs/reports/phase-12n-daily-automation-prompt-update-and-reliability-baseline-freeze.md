# Phase 12N Daily Automation Prompt Update and Reliability Baseline Freeze

生成日期：2026-06-08

本报告属于公开 research tooling 文档，不包含任何 private application material，也不写入 `D:\ResearchArtifacts`。

# Executive Summary

Phase 12N 已完成以下工作：

- 冻结当前 Daily reliability baseline；
- 生成 Daily / Weekly / Full Manual 三个 automation module 的 prompt v0.3 文本；
- 明确 source-starved false-success guard；
- 生成 automation UI 手工更新清单；
- 增加一个可打印当前 baseline 的脚本：
  - `scripts\print_current_reliability_baseline.py`
  - `scripts\print_current_reliability_baseline.bat`

本 phase 没有创建新 scheduler，没有修改 ChatGPT automation UI 本身。仓库只提供可手工复制的 prompt 文本和基线冻结说明。

Daily / Weekly / Full 三个模块的推荐角色现在已经清晰：

- Daily Public Digest Run：主公开日报 intake 和 source-health 报告模块
- Weekly Public Synthesis Run：weekly synthesis + handoff 模块
- Full Manual Quality Run：保持 paused，作为重型人工恢复/验证模块

source-starved false-success guard 已单独落文档，并已在 v0.3 prompt 中显式要求：

- `0 records + all-red sources` 不是“发现无论文”的成功结果；
- empty weekly handoff under source-starved input 也不是“无 handoff 候选”的成功结果。

用户下一步需要手工做的唯一 UI 动作：

- 打开现有 automation UI；
- 把三个模块的 prompt 替换为仓库中的 v0.3 文本；
- 保持 Full Manual Quality Run 为 paused；
- 观察下一次真实 Daily / Weekly automation 输出。

# Input Evidence Used

| Input | Status | How used | Limitation |
| --- | --- | --- | --- |
| `docs/reports/phase-12m-daily-digest-reliability-dashboard-and-three-run-stability-check.md` | found | 作为 12N baseline freeze 的主证据 | 属于上一 phase 的人工运行快照 |
| `docs/reports/phase-12m-three-run-stability-check-log.md` | found | 复核三次稳定性检查结论 | 不等于未来所有运行都稳定 |
| `docs/research_tracks/daily_digest_reliability_dashboard_v0.1.md` | found | 复用 dashboard 语义 | 只定义 dashboard，不冻结 UI prompt |
| `docs/research_tracks/daily_digest_success_metrics_v0.2.md` | found | 复用指标名 | 不含 UI 更新步骤 |
| `docs/research_tracks/automation_module_prompt_recommendations_v0.2.md` | found | 升级到 v0.3 的基础 | 仍缺 baseline freeze 说明 |
| `docs/research_tracks/daily_public_digest_run_prompt_v0.2.md` | found | 升级到 v0.3 | 需补 baseline freeze / false-success guard 口径 |
| `docs/research_tracks/weekly_public_synthesis_run_prompt_v0.2.md` | found | 升级到 v0.3 | 需补 weekly source-starved guard |
| `docs/research_tracks/full_manual_quality_run_prompt_v0.2.md` | found | 升级到 v0.3 | 需补 baseline freeze 背景 |
| `scripts/daily_reliability_dashboard.py` | found | 作为 baseline printer 的底层能力 | 默认会尝试 probe，不适合直接 freeze |
| `scripts/print_current_reliability_baseline.py` | created in this phase | 打印 artifact-first 基线 | 不做 live probe |
| `scripts/generate_weekly_handoff.py` | missing | 作为 missing command 明确记录 | 当前只能用 `.bat` 或 `-m` 入口 |
| latest `data/*.json`, `data/weekly/*.json`, `handoffs/weekly/*.json` | found | 用于 artifact-first baseline freeze | 只反映当前持久化产物，不反映未来瞬时网络 |

# Current Automation Module Baseline

- Daily Public Digest Run：active
- Weekly Public Synthesis Run：active
- Full Manual Quality Run：paused

推荐角色：

- Daily：必须输出 source health、source-starved、IACR latest、Semantic Scholar enrichment 状态、`git status -sb`
- Weekly：基于现有 weekly artifact 做 synthesis，并调用 working weekly handoff 入口
- Full Manual：仅在 source recovery、tests、release hygiene、weekly handoff 重跑时使用

# Reliability Baseline Freeze

本 phase 冻结的 baseline 来自：

- `python scripts\print_current_reliability_baseline.py`
- 最新持久化日报/周报/handoff artifact

Frozen baseline：

| Metric | Value |
| --- | --- |
| `baseline_date` | `2026-06-08` |
| `python_version` | `3.15.0b2` |
| `package_version` | `0.3.3` |
| `active_automation_modules` | `Daily Public Digest Run`, `Weekly Public Synthesis Run` |
| `paused_automation_modules` | `Full Manual Quality Run` |
| `latest_daily_artifact` | `data\2026-06-08.json` |
| `latest_weekly_artifact` | `data\weekly\2026-W23.json` |
| `latest_handoff_artifact` | `handoffs\weekly\2026-W23-handoff-packets.json` |
| `source_total_count` | `6` |
| `source_green_count` | `2` |
| `source_yellow_count` | `4` |
| `source_red_count` | `0` |
| `source_reachability_rate` | `1.0` |
| `retryable_error_count` | `1` |
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
| `validation_passed` | `True` |
| `manual_recovery_needed` | `False` |

Baseline 解释：

- 当前不是 source-starved；
- 当前 Daily 是 degraded-but-usable，不是 fully green；
- IACR latest 已恢复到可见、可解析状态；
- Semantic Scholar 当前不是 missing key，而是 key 在、latest daily 中没有候选 enrichment；
- Weekly handoff 当前可用，但周覆盖仍缺 `2026-06-06` 和 `2026-06-07`。

# Prompt v0.3 Summary

本 phase 新增：

- `docs/research_tracks/automation_module_prompt_recommendations_v0.3.md`
- `docs/research_tracks/daily_public_digest_run_prompt_v0.3.md`
- `docs/research_tracks/weekly_public_synthesis_run_prompt_v0.3.md`
- `docs/research_tracks/full_manual_quality_run_prompt_v0.3.md`

Daily prompt v0.3：

- 固定 project path 和 Python 3.15.0b2 policy
- 明确允许/禁止命令
- 明确 source-starved false-success guard
- 明确 IACR latest / Semantic Scholar 状态必须报告
- 明确 no git add / commit / push
- 明确 no `PhD_Application` / `ResearchArtifacts` writes

Weekly prompt v0.3：

- 明确 weekly inputs
- 明确使用 working weekly handoff 入口
- 明确 empty handoff 不能过度解释
- 明确 source-starved weekly input guard

Full Manual prompt v0.3：

- 明确 paused / heavy validation role
- 明确何时使用
- 明确 source recovery / tests / release hygiene / weekly handoff replay
- 明确禁止背景自动化和 git 操作

# Manual Automation UI Update Checklist

手工 UI 更新说明已写入：

- `docs/research_tracks/automation_ui_manual_update_checklist_v0.1.md`

用户要做的事：

1. 打开现有 automation UI
2. 不新增重复模块，优先更新已有三项
3. 将三份 v0.3 prompt 文本手工复制到对应模块
4. 保持 Full Manual Quality Run 为 paused
5. 观察下一次 Daily / Weekly run 的输出

# False-Success Guard

false-success guard 文档：

- `docs/research_tracks/source_starved_false_success_guard_v0.1.md`

核心规则：

- `0 records + all-red sources = source-starved`
- source-starved 不是成功的 paper-discovery result
- source-starved 下的 empty daily digest 不是“今天无相关论文”的证据
- source-starved 下的 empty weekly handoff 不是“没有 handoff 候选”的证据
- recovery 必须保持 manual-only
- 不允许自动 retry loop

# Code / Script / Docs Changes

| Path | Reason | Risk | Test coverage |
| --- | --- | --- | --- |
| `src/lattice_digest/reliability_dashboard.py` | 增加 baseline 构建能力 | low | targeted tests |
| `scripts/print_current_reliability_baseline.py` | 打印 artifact-first baseline | low | manual run |
| `scripts/print_current_reliability_baseline.bat` | cmd wrapper | low | manual run |
| `tests/test_reliability_baseline.py` | baseline 字段测试 | low | targeted tests |
| `docs/reports/phase-12n-daily-automation-prompt-update-and-reliability-baseline-freeze.md` | 12N 主报告 | low | documentation only |
| `docs/reports/phase-12n-reliability-baseline-freeze.md` | baseline freeze 报告 | low | documentation only |
| `docs/research_tracks/automation_module_prompt_recommendations_v0.3.md` | v0.3 prompt 总览 | low | documentation only |
| `docs/research_tracks/daily_public_digest_run_prompt_v0.3.md` | Daily prompt v0.3 | low | documentation only |
| `docs/research_tracks/weekly_public_synthesis_run_prompt_v0.3.md` | Weekly prompt v0.3 | low | documentation only |
| `docs/research_tracks/full_manual_quality_run_prompt_v0.3.md` | Full Manual prompt v0.3 | low | documentation only |
| `docs/research_tracks/daily_reliability_baseline_v0.1.md` | baseline 定义与当前冻结值 | low | documentation only |
| `docs/research_tracks/daily_reliability_monitoring_checklist_v0.1.md` | 后续监控清单 | low | documentation only |
| `docs/research_tracks/automation_ui_manual_update_checklist_v0.1.md` | UI 手工更新步骤 | low | documentation only |
| `docs/research_tracks/source_starved_false_success_guard_v0.1.md` | false-success guard 规则 | low | documentation only |

# Validation Results

| Check | Result |
| --- | --- |
| Python version | `Python 3.15.0b2` |
| Environment import check | passed |
| Doctor | passed |
| Reliability baseline generation | passed via `python scripts\print_current_reliability_baseline.py` and `.bat` wrapper |
| Tests | full suite passed: `431 passed`; managed sandbox 内初次失败属于临时目录权限噪声，提权重跑后通过 |
| Release hygiene | passed |
| `git diff --check` | passed; only LF/CRLF working-copy warnings |
| `git status -sb` | dirty worktree includes prior phase files plus new Phase 12N files; no private workspace paths touched |

# TODO_VERIFY

- next actual Daily Public Digest Run after manual UI update
- next Weekly Public Synthesis Run after manual UI update
- whether Full Manual Quality Run should remain paused
- whether baseline should be refreshed weekly
