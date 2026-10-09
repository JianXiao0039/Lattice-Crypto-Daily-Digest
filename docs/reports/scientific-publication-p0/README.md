# 格密码科学相关性与 Daily 发布语义 P0：本地验收报告

本补丁只在外部干净候选中实施，基线来自实际已发布 origin/main
`0f387ef1ad388a1db47b9d062480929dd7d239d5`。三天 canonical 原件、脏开发目录、
runtime、自动化均未覆盖。本报告中的回放、Weekly/Monthly 文件是离线候选，未发布。

## 三天原件与逐行核账

原始六文件 SHA-256、完整原始 metadata、采集计数、来源健康与 QA 保存在
[incident-freeze.json](incident-freeze.json)。原件来源为 canonical 年分区路径。
原报告的 selected 263 / 263 / 319 被 JSON 逐行独立确认，但其人口是档案与新论文的混合。
所有三份原件都使用 backfill，原语义 QA 都为 PASS。

| 日期 | 原 selected | 原 Primary New | 保留观察 | L1 格相关身份 | 新 Primary | 真修订 | 新核验提醒 | 背景更新 | 历史观察 | 新 core Daily 事件 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-10-07 | 263 | 4 | 263 | 193 | 2 | 0 | 1 | 2 | 258 | 3 |
| 2026-10-08 | 263 | 0 | 263 | 193 | 0 | 0 | 0 | 0 | 263 | 0 |
| 2026-10-09 | 319 | 4 | 319 | 223 | 2 | 0 | 0 | 2 | 315 | 2 |

事件、背景更新、历史观察构成完整逐日分区，所有 845 条记录保留。
跨日强身份归并得到 343 个身份；源版本事件保留。没有设定“应存活几篇”的目标。
L1 仍可包含来源日期待核实的格论文，但它们不能建立 L2 或 L3。

[完整逐行审计](row-audit.json) 与 [来源角色证据](source-role-evidence.json)
以 evidence ID 连接；每行保留原标签、分数、来源、身份、版本、规则、决定和不确定性。
这是机器规则/模型来源解释，不能作为 human-adjudicated gold。

## 根因与修复

源 adapter、原始 occurrence、规范化、V3 身份合并构成 L0。此前 run.py 的 backfill
保留逻辑，加上 authority.py 对所有 ABC 行的计数，将历史库升级成了 Daily 入选人口。
未见过的 arXiv v2+ 又被跨日逻辑强制标成 recent revision，未核实更新是否在覆盖窗内。

原 evidence_contract 只要看到 PRIM/IMPL/PROOF 关键词就能判定直接相关；HQC 的 ML-KEM
比较、混合 AKE 的 ML-KEM 组件、一般证明中的 LWE 假设因而可以获得 A/90。
现在分类只使用原始 title/abstract 的主对象与带摘录、SHA-256 的类型角色。
具体格构造的硬度假设可以支持范围；一般证明仅假设 LWE 本身不够。
FO/TDF 可实例化性论文因此是邻接背景，不外推 ML-KEM 原生安全结果。
related-work、比较、方法子程序和 ontology neighbor 不能升级为直接对象。
物理 LLL（Landau level）、原子成像 ideal lattice、Steinberg/Leavitt 代数等
必须通过学科与密码学共同证据门槛；没有密码学/欧几里得格算法对象时判为 D。
物理泄漏等确有 ML-KEM 等目标的安全论文仍保留。
没有格来源角色的泛 PQC 新观察也不自动填充 Daily 背景节。
生成结论、译文、标签与建议不参与重新分类。

新增 source-role 门槛将纯元数据、低证据记录保留在 L0，阻止其通过事件层进入 Daily。
80/60/40 的单一分数到标签映射保持不变。邻接/一般背景的语义上限为 59，
当前具体分数为 49（有格背景角色）或 45（邻接 PQC）；无证据的泛化背景可为 D/0。
A/B 的来源与角色必须通过机器 gate。

publication_events 提供唯一分区：新论文、真修订、新关键核验、背景更新、历史观察。
只有前三类进入 core Daily。记录日期、来源版本/内容、既往观察共同建立事件；
历史重复采集不能产生事件。跨源别名不重复推荐；未变化的关键来源不重开告警。

Daily renderer 使用同一账本生成摘要、完整紧凑索引、事件分类与动作分区。
详读/背景预算只影响展开，机器账本和完整事件索引不截断。
计数、事件行、Primary 标志、重复事件、渲染分区不一致会被 QA 拒绝。
实测首次发表仍在窗口内的 v2 曾被旧 cross-day QA 误拒绝；发布 QA 现以 canonical
primary event 为准，两种调用者 Primary 标志均验证通过，同时保留真正跨日伪 Primary 的拒绝。
原 report_quality/semantic QA 无事件分区审计，三天均未发现这些问题；新 gate 补上这层。

recommendation_calibration 的建议不能决定 freshness。无完整问题、瓶颈、closest work、
差异、终点与创新不确定性证据时，Daily 写入
`NO_ACTIONABLE_RESEARCH_IDEA_FROM_CURRENT_EVIDENCE`。Weekly 不重新制造项目候选。
SQLite 改为保留旧身份的 upsert，避免每次 Daily 删除历史发现。

完整预实施根因与任务约束见 [P0 contract](../../operations/scientific_publication_p0_contract.md)。

## 原统计的具体消解

- 10 月 7 日：263 个身份，但 265 个编号论文标题，2 个重复详述；原动作分区
  2 read_now + 154 skim + 38 save + 69 verify = 263。原 ABC=235/5/23，包含旧论文与日期待核实项。
- 10 月 8 日：196 是“research_value>=70 或 level=Backfill”的非主项子集，
  另有 67 个非主项，共 263。原动作分区 0+156+38+69=263；并非 196 个当日事件。
- 10 月 9 日：1 Medium 是推荐等级子集，另 3 个 Primary 是 Low；read_now=4 来自不同谓词。
  原有 323 个编号标题对 319 个身份，4 个重复详述；原 ABC=286/5/28。
- 新事件 ABC：3/0/0、0/0/0、2/0/0；新动作分区依次为
  skim=2+verify_first=1、空、skim=1+read_now=1。全部由事件行推导。

## 真实正负对照与日期

[26 个分层来源复核样本](stratified-source-review.json) 包含六个指定正对照、
七个负/邻接对照、日期不确定、关键 watch、跨日历史版本、额外 FO 假设对照，
以及五个格/FHE/构造正对照和四个物理/成像负对照。
来源摘录、技术目标、角色、科学范围、标签、理由和不确定性均保留。
复核者是 Codex，证明未独立核验，human gold 为空。

Too Small to Hide、LWE 次指数算法、Adelic module reduction、trapdoor projective sampling、
ML-DSA hint weight、lattice blind signatures 的真实格相关性均保留。
Adelic 是约简理论；LWE 算法不自动成为 ML-KEM 攻破；hint weight 不自动成为密钥恢复。
HQC、code-based sieving、SQIsign 不因比较或子程序成为格核心；HSP 的一般 SVP 背景、
F2[x] 通用算术、Schnorr、泛化 hybrid AKE 均有显式范围。
没有按标题编写生产例外。

Benchmark V2 的七篇材料/化学 MLIP 论文、一篇 DCP 背景论文，以及原本误标 D 的
五个真实格算法/构造/FHE 正对照，原始标签与 source snapshot
保持不变，在已有 correction map 中添加来源复核修正。MLIP 的材料学同名缩写不能成为
Module-LIP 的证据。最终 Benchmark V2 的精度为 93.62%，召回为 99.25%，critical recall
为 100%；剩余 9 个相对 D 标签差异均为 C 类观察，没有 A/B 假升级。唯一相对 A 标签
“漏报”是高熵合金材料论文，分类为 D 符合原始摘要；保持标签冲突记录，不伪造人工裁决。
详细指标与 source excerpt 见 benchmark-v2-final.json 和 benchmark-label-conflicts.json。保留全部 200 个样本与原验收阈值，没有制造人工 gold。

[日期审计](date-uncertainty-audit.json) 包含三天各 15 条不确定记录：5 个 2027 年份值、
10 个月份精度值。年份/月值不能替代覆盖窗内时间戳；2027 proceedings 也不自动不可能。
这些论文保持可观察；独立真实 preprint/revision 时间戳可建立相应事件，缺少时不 Primary。

## 关键旧信号与 period 输入

[事件清单](actionable-event-index.json) 包含四个真实新身份和一个 DCP 来源勘误核验提醒。
DCP 原发布日期保留；Oct 7 来源注记及其摘录/哈希产生 verify-first，后两天不重复重开。
CRITICAL_WATCH 保留来源版本/哈希、归约方向、受影响问题、已知来源更正、TODO_VERIFY
与人工复核动作。它不计 Primary，也没有证明已攻破标准化 ML-KEM/ML-DSA。
未进行独立 PDF 证明或反驳文献检索。

Weekly/Monthly 聚合 5 个 canonical 事件与 5 个事件论文身份，另列 4 个背景更新、
历史观察/版本与来源覆盖，不把 845 条重复观察解释为发现趋势。
真实三天 period fixture 的 Weekly 为 degraded，Monthly 因仅提供三天而缺 28 天，
明确 incomplete；缺失日期是 fixture 覆盖，不断言真实仓库那 28 天缺报。
缺失和语义失败输入继续传播，不能用于全球领域趋势推断。
真实 incident 没有建立新增版本事件；真实历史 v2 样本是负对照，真修订用独立 synthetic
事件测试覆盖，没有编造真实 cross-day revision。

## 验证与复现

Python315 的干净已发布基线：1135 passed。最终完整候选：1203 passed，0 failed，
323.08 秒，新增 68 项且保留原 1135 项。最终发布定向组合：87 passed。
完整矩阵包含 classifier/co-anchor、分数标签、freshness/history、critical watch、角色、
Daily/W/M、publication QA/durable verifier、Retrieval V3、Benchmark V1/V2、missed registry、
正常/backfill、runtime provenance 与 release hygiene。没有通过排除测试消解失败。
阶段失败、污染基线与缺 .git 环境基线均保留日志和说明，见 [validation.json](validation.json)。

离线复现命令（output 必须是尚不存在的外部独立目录）：

```powershell
Set-Location D:/Code/CodexProjects/lattice-digest-p0-candidate-20261009
D:/CyberSecurity/Python315/python.exe scripts/replay_scientific_publication_p0.py `
  --input-dir D:/Code/CodexProjects/lattice-digest-p0-evidence-20261009 `
  --history-dir D:/Code/CodexProjects/lattice-digest-p0-evidence-20261009/history `
  --output-dir D:/Code/CodexProjects/lattice-digest-p0-new-replay
```

[回放 manifest](replay-output-manifest.json) 与 [实际候选 provenance](candidate-replay-provenance.json)
将原始 runtime 来源与本次未发布候选代码分开。冻结来源健康及其原 pipeline 计数被明确保留为
原运行观察，不能解释为新 Daily 入选计数。没有重新抓取 live sources 或启动 connector。

## 集成、发布准备与剩余边界

[开发目录 reconciliation](development-reconciliation.json) 确认未提交 status/diff 与开始时一致，
候选改动与未提交路径无重叠。开发 HEAD 与已发布基线有 8 个树差异，涉及补丁中的
runtime_dependencies、evidence_contract、storage。未 fetch/改写开发目录内部状态，
没有将候选复制回旧 checkout。候选始终以实际已发布基线为准。

本地代码与事件语义验收通过，具备准备下一阶段发布审查的条件；尚未发布。
译文后端仍未授权，双语交付不可宣称完成。规则分类不是 proof adjudication，真实
source date/version、关键归约与参数依然需要针对性 human review。部分来源覆盖限制保留。
14 天/体积有界的历史读取仍是既有运行边界；源质量不足或过界文件必须保留 diagnostics。

精确 changed paths 和 SHA-256 在 changed-paths.json。只提交源代码、回归与本阶段审计证据；
不提交 data/digests/papers.db、测试缓存或大体积原始 Daily 快照。
未 push、release、修改 runtime/自动化、写真实 Zotero 或删除历史科研资料。
下一阶段授权为 `AUTHORIZE_LATTICE_DIGEST_P0_RELEASE_AND_THREE_DAY_REPAIR`。
