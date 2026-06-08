# Phase 12O: Post-Update Daily Automation Observation and Regression Check

生成日期：2026-06-08

# Executive Summary

- 已完成一次 Phase 12N 之后的仓库侧观察与回归检查。
- Daily Public Digest Run 和 Weekly Public Synthesis Run 仍视为 active；Full Manual Quality Run 仍应保持 paused。
- 冻结基线与当前持久化产物对比结果整体为 `unchanged`，未看到 source-starved 或 false-success 回归。
- live probe 补充观察显示：外部源整体可达，但 Semantic Scholar 在仪表盘探测中出现 `rate_limit`，因此“可达性”与“富化可用性”需要分开看。
- IACR latest 未见回归：基线为 `fetched/100`，当前 artifact 仍为 `fetched/100`；最新 source-health audit 记录为 `cache_hit/100`，与 direct probe 的 `parsed/100` 一致指向“可用”。
- 当前输出无法仅凭仓库产物证明 ChatGPT automation UI 已完成 v0.3 prompt 手工更新；这项只能标记为 `TODO_VERIFY`。
- 本轮未写入 `PhD_Application`，未写入 `D:\ResearchArtifacts`，未执行任何 git add / commit / push / tag。

# Input Evidence Used

| 输入 | 状态 | 用途 | 局限 |
| --- | --- | --- | --- |
| `docs/reports/phase-12n-daily-automation-prompt-update-and-reliability-baseline-freeze.md` | available | 读取 Phase 12N 结论 | 不是机器可比对基线主体 |
| `docs/reports/phase-12n-reliability-baseline-freeze.md` | available | 提取冻结 baseline JSON | baseline 不含 `generated_artifacts_present` |
| `docs/research_tracks/automation_module_prompt_recommendations_v0.3.md` | available | 核对 v0.3 prompt 目标 | 无法证明 UI 已实际更新 |
| `docs/research_tracks/daily_public_digest_run_prompt_v0.3.md` | available | 对照 Daily 期望行为 | 仍需人工复制到 UI |
| `docs/research_tracks/weekly_public_synthesis_run_prompt_v0.3.md` | available | 对照 Weekly 期望行为 | 同上 |
| `docs/research_tracks/full_manual_quality_run_prompt_v0.3.md` | available | 对照 Full 模块角色 | 同上 |
| `docs/research_tracks/daily_reliability_baseline_v0.1.md` | available | 快速核对冻结指标 | 与 freeze report 存在重复 |
| `docs/research_tracks/source_starved_false_success_guard_v0.1.md` | available | 对照 false-success guard 期望 | 本轮未触发 source-starved 场景 |
| `data/2026-06-08.json` | available | 当前 daily artifact 事实来源 | 反映的是产物生成时状态，不是实时网络 |
| `data/weekly/2026-W23.json` | available | 当前 weekly artifact | 周视图会混入更早几天的 red 记录 |
| `handoffs/weekly/2026-W23-handoff-packets.json` | available | 观察 weekly handoff 候选数量与 source-starved 标记 | 周汇总不能直接代表当天网络 |
| `audits/source-health/2026-06-08.json` | available | 读取最新 source-health audit | 与 daily artifact、live probe 时间点不同 |
| `scripts/print_current_reliability_baseline.py` | available | 当前基线打印 | 默认 artifact-only |
| `scripts/daily_reliability_dashboard.py` | available | 当前可靠性仪表盘 | live probe 结果会受瞬时限流影响 |
| `scripts/probe_source_connectivity.py` | available | 直接源连通性探测 | 仅反映探测时间点 |
| `scripts/generate_weekly_handoff.py` | missing | 用户给出的候选命令 | 实际可用入口是 `scripts/run_weekly_handoff.bat` 或 `python -m lattice_digest.weekly_handoff --latest` |

# Current Automation Module Observation

- Daily Public Digest Run：active
- Weekly Public Synthesis Run：active
- Full Manual Quality Run：paused
- 仓库内 v0.3 prompt 文件已存在，但当前产物不能直接证明 automation UI 文本已经更新。
- 当前可直接观察到的 repo-side 行为：
  - daily / weekly / handoff 产物存在；
  - false-success guard 没有误触发；
  - 输出没有写入私有目录；
  - 输出没有伴随 git 操作。
- TODO_VERIFY：
  - 下一次真实 automation UI 触发后的输出是否带上了 v0.3 里要求的更明确状态说明；
  - UI 中是否已经替换为 v0.3 prompt 文本。

# Baseline vs Current Reliability Diff

以下表格以“冻结基线 vs 当前持久化产物”作为主比较口径。补充的 live probe 见后文。

| metric | baseline | current | status | interpretation | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- |
| `source_total_count` | `6` | `6` | `unchanged` | 无回归 | 否 |
| `source_green_count` | `2` | `2` | `unchanged` | 无回归 | 否 |
| `source_yellow_count` | `4` | `4` | `unchanged` | 仍是 degraded-but-usable | 否 |
| `source_red_count` | `0` | `0` | `unchanged` | 当前 daily artifact 仍非 all-red | 否 |
| `source_reachability_rate` | `1.0` | `N/A` | `unknown_due_to_missing_artifacts` | artifact-only 当前值不暴露该指标 | 是 |
| `retryable_error_count` | `1` | `1` | `unchanged` | 仍有可重试告警痕迹 | 否 |
| `digest_record_count` | `6` | `6` | `unchanged` | 无回归 | 否 |
| `final_record_count` | `6` | `6` | `unchanged` | 无回归 | 否 |
| `high_priority_count` | `5` | `5` | `unchanged` | 无回归 | 否 |
| `iacr_latest_status` | `fetched` | `fetched` | `unchanged` | IACR latest 未回退 | 否 |
| `iacr_latest_records` | `100` | `100` | `unchanged` | IACR latest 记录数稳定 | 否 |
| `semantic_scholar_enrichment_status` | `no_candidates_to_enrich` | `no_candidates_to_enrich` | `unchanged` | artifact 层面未见回归 | 否 |
| `source_starved_true_false` | `False` | `False` | `unchanged` | 未进入 source-starved | 否 |
| `empty_digest_reason` | `non_empty` | `non_empty` | `unchanged` | 非空日报 | 否 |
| `weekly_handoff_candidate_count` | `20` | `20` | `unchanged` | 周 handoff 稳定非空 | 否 |
| `weekly_handoff_source_starved_true_false` | `False` | `False` | `unchanged` | 周 handoff 未误标空白成功 | 否 |
| `generated_artifacts_present` | `N/A` | `True` | `unknown_due_to_missing_artifacts` | 冻结基线未显式冻结此字段 | 是 |
| `validation_passed` | `True` | `True` | `unchanged` | 仓库侧验证未回归 | 否 |
| `manual_recovery_needed` | `False` | `False` | `unchanged` | 当前不需要额外恢复动作 | 否 |

补充 live probe 观察：

- `source_reachability_rate`：live dashboard 一次观测为 `0.833`，原因是 Semantic Scholar 探测中出现 `rate_limit`。
- `semantic_scholar_enrichment_status`：live dashboard 一次观测为 `rate_limit`，弱于冻结基线中的 `no_candidates_to_enrich`。
- 直接运行 `probe_source_connectivity.py` 时，Semantic Scholar 也曾返回 200；因此这更像瞬时限流/不稳定，而不是稳定性硬回归。

# Source Health Regression Check

| source | baseline status | current status | regression class | likely reason | manual action |
| --- | --- | --- | --- | --- | --- |
| `arxiv` | `green` | direct probe `reachable(200)` | `unchanged` | 无明显回归 | 继续观察 |
| `crossref` | `green` | direct probe `reachable(200)` | `unchanged` | 无明显回归 | 继续观察 |
| `dblp` | `yellow` | direct probe `reachable(200)`，daily artifact 仍 `yellow` | `improved / artifact-unchanged` | 当前网络可达，但持久化日报保留了 earlier warning | 下次 daily run 观察 yellow 是否消失 |
| `iacr_eprint` | `yellow` | direct probe `reachable+parsed(100)`；audit=`cache_hit(100)` | `unchanged` | latest 可用，yellow 来自“当天无最终入选记录”而非 feed 失效 | 无需恢复，继续观察 |
| `openalex` | `yellow` | direct probe `reachable(200)`，artifact 仍 `yellow` | `improved / artifact-unchanged` | 源可达但结果仍为 0 | 继续观察 query 产出 |
| `semantic_scholar` | `yellow` | direct probe `reachable(200)`；live dashboard=`rate_limit` | `TODO_VERIFY` | 瞬时限流或探测窗口差异 | 仅手动重试，不把它解释为论文无关 |

# IACR Latest Regression Check

- baseline：`fetched / 100`
- 当前 artifact-only 对比：`fetched / 100`
- 当前 source-health audit：`cache_hit / 100`
- 当前 direct probe：RSS/latest 可达，`parser_status=parsed`，`records=100`
- 结论：
  - 未见 feed unreachable；
  - 未见 parser failure；
  - 未见 failed-attempt guard 阻断；
  - cache hit 与 direct probe 一致说明“latest 可用”；
  - 本轮 IACR latest 无回归。
- TODO_VERIFY：
  - 下一次真实 automation run 是否仍稳定落在 `fetched` 或 `cache_hit`；
  - 若 future run 出现 `failed/0`，需重新走 Phase 12K/12L 的恢复策略。

# Semantic Scholar Regression Check

- baseline：key present，`no_candidates_to_enrich`
- 当前 direct probe：key present，长度 `44`，端点返回 `200`
- 当前 live dashboard：`rate_limit`
- 当前 artifact-only：仍是 `no_candidates_to_enrich`
- 结论：
  - 没有看到 missing key；
  - 没有看到 auth failure；
  - 看到了瞬时 `rate_limit`；
  - 因此这是“富化可用性不稳定”，不是“source hard failure”。
- TODO_VERIFY：
  - 下一次 live probe 是否仍 rate-limit；
  - 是否仅在短时间连续探测时触发。

# False-Success Guard Review

- `0 records + all-red sources => source-starved` 的 guard 本轮没有触发，因为当前 daily artifact 非空，weekly handoff 非空。
- 本轮没有出现“空日报被当成成功发现结果”的现象。
- 本轮没有出现“空 weekly handoff 被解释为没有候选论文”的现象。
- 当前恢复建议仍保持 manual-only，没有自动重试循环。
- 结论：guard 在本轮属于“未触发但未失效”。

# Code / Script / Docs Changes

| 路径 | 类型 | 原因 | 风险 | 测试覆盖 |
| --- | --- | --- | --- | --- |
| `scripts/compare_reliability_baseline.py` | new script | 对比冻结基线与当前产物，支撑 12O 回归检查 | 低；只读比较 | `tests/test_compare_reliability_baseline.py` |
| `scripts/compare_reliability_baseline.bat` | new helper | Windows 手动调用入口 | 低 | 间接由脚本执行验证 |
| `tests/test_compare_reliability_baseline.py` | new test | 覆盖 JSON 提取与比较逻辑 | 低 | 已单测 |
| 本报告及 12O 文档 | new docs | 固化观察结果与清单 | 低 | 文档型，无业务逻辑改动 |

# Validation Results

- Python version：`3.15.0b2`
- environment import check：passed
- `python -m lattice_digest.workflow doctor`：passed
- `python scripts\print_current_reliability_baseline.py`：passed
- `python scripts\daily_reliability_dashboard.py --skip-probe --format json`：passed
- `python scripts\daily_reliability_dashboard.py --format json`：passed，出现 Semantic Scholar `rate_limit`
- `python scripts\probe_source_connectivity.py`：passed
- `cmd /c scripts\run_weekly_handoff.bat`：passed
- `python scripts\compare_reliability_baseline.py`：passed
- tests / release hygiene / git checks：见 `phase-12o-regression-check-log.md`

# TODO_VERIFY

- 真实 automation UI 的下一次 2 次 Daily Public Digest Run 输出；
- 下一次 Weekly Public Synthesis Run 输出；
- Semantic Scholar 是否在连续短时间探测下持续 rate-limit；
- DBLP / OpenAlex 的 yellow 是否会在后续新 daily artifact 中消退；
- v0.3 prompt 是否已被手工复制到 automation UI。
