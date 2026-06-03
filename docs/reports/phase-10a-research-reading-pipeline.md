# Phase 10A Research Reading Pipeline

生成日期：2026-06-03

输入来源：

- `digests/2026-06-03.md`
- `data/2026-06-03.json`
- `digests/weekly/2026-W23.md`
- `data/weekly/2026-W23.json`
- `state/reading-queue.json`（只读检查）
- `exports/research-progress/2026-W23/`（只读参考）
- `exports/obsidian-paper-notes/`（只读参考）

本报告只做人工阅读队列规划，不修改 fetcher、ranking、taxonomy、source health、workflow、reading queue state、Obsidian notes、`papers.db` 或任何生成的日报/周报产物。

## 1. 一句话结论

本周最值得立即精读的是 LWE / Module-LWE attack 与 dual attack 线索：`Unified Dual Attack Analyses`、`Module Lattice Security (Part IV)`、`Improved Dual Attack and Trapdoor Sampling`。6 月 3 日日报新增的 ML-KEM encapsulation coin 论文是强 positive，建议作为本周 PQC implementation security 补读，而不是挤掉前三篇 attack / security estimation 主线。

## 2. Must-read：3 篇本周优先精读

### 1. Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE

- Source：IACR ePrint
- URL：https://eprint.iacr.org/2026/1048
- Date：2026-05-25
- Relevance / reading priority：A / 100，reading_priority_score 95，必须精读
- Queue preview：HIGH，TODO_READ，TODO_VERIFY
- Why it matters：该论文直接落在 LWE dual attack 的 score distribution / covariance analysis 上，可用于理解 dual attack 代价模型、错误独立性假设、Kyber / ML-KEM 安全讨论和 attack estimator 校准。
- lattice/PQC anchor evidence：LWE/RLWE/MLWE；ML-KEM/Kyber；ML-DSA/Dilithium；PQC anchor；BKZ/lattice attack
- Relation to PhD / research directions：最贴近 LWE / MLWE cryptanalysis、dual attack、attack cost model、AI4Lattice 中的 attack-cost proxy 与 learned ranking baseline。
- Relation to Module-SIS chameleon hash：间接相关。它不直接构造 Module-SIS chameleon hash，但可作为参数安全分析和 lattice assumption discussion 的背景。
- Relation to Swin-guided lattice cryptanalysis：强相关。可提取 dual attack score / covariance / feature distribution 作为 supervised ranking 或 hard/easy instance separation 的标签来源。
- Suggested reading priority：今日精读，先读 abstract、attack model、score distribution derivation、实验/参数表，再决定是否进入组会候选。
- Concrete next action：用 45 分钟整理一页阅读卡，重点回答“score distribution prediction 对 Kyber / ML-KEM 安全估计有什么实际影响？”

### 2. Module Lattice Security (Part IV): Probabilistic Polynomial Quantum Attack on Module-LWE over 2-Power Cyclotomics

- Source：arXiv
- URL：http://arxiv.org/abs/2605.17412v2
- Date：2026-05-17
- Relevance / reading priority：A / 100，reading_priority_score 92，必须精读
- Queue preview：HIGH，TODO_READ，TODO_VERIFY
- Why it matters：该论文声称讨论 Module-LWE over 2-power cyclotomics 与 quantum attack，对 ML-KEM / module lattice security 叙事影响很大。由于结论潜在冲击强，必须先精读并人工核验，不应只依赖 digest 排名。
- lattice/PQC anchor evidence：LWE/RLWE/MLWE；ML-KEM/Kyber；ML-DSA/Dilithium；Falcon/FN-DSA；PQC anchor；lattice
- Relation to PhD / research directions：直接服务 MLWE / RLWE negative-cyclic modeling、module lattice security、ML-KEM security estimation 和 long-term PhD narrative。
- Relation to Module-SIS chameleon hash：间接相关。可帮助梳理 module lattice assumptions 的安全边界，但不要把 MLWE 结论直接迁移到 SIS / Module-SIS 原语。
- Relation to Swin-guided lattice cryptanalysis：中强相关。若论文涉及 cyclotomic / module structure，可转化为 structured representation、negative-cyclic modeling 或 block-circulant feature 的背景材料。
- Suggested reading priority：今日精读，但以“核验 claim”为目标。
- Concrete next action：先标出 precise assumption、attack target、complexity model、是否只对特定 cyclotomic / parameter 有效；把所有强安全结论标为 TODO_VERIFY。

### 3. Improved Dual Attack and Trapdoor Sampling via Quantum Rejection Sampling

- Source：arXiv
- URL：http://arxiv.org/abs/2605.24798v1
- Date：2026-05-24
- Relevance / reading priority：A / 100，reading_priority_score 91，必须精读
- Queue preview：HIGH，TODO_READ，TODO_VERIFY
- Why it matters：该论文连接 dual attack、GPV trapdoor sampling 和 quantum rejection sampling。它同时触及 LWE attack、trapdoor sampling、lattice primitive security proof background，非常适合放进“攻击线 + 原语线”的交叉阅读。
- lattice/PQC anchor evidence：LWE/RLWE/MLWE；SIS/Module-SIS；ML-KEM/Kyber；ML-DSA/Dilithium；lattice-based primitive；PQC anchor；BKZ/lattice attack
- Relation to PhD / research directions：对 LWE / MLWE cryptanalysis、lattice trapdoor、security proof intuition 和 attack baseline 都有价值。
- Relation to Module-SIS chameleon hash：中等相关。trapdoor sampling / GPV 背景可用于对照 chameleon hash 中 trapdoor / adaptation / collision generation 的证明入口，但不能直接当成构造结果。
- Relation to Swin-guided lattice cryptanalysis：中等相关。可作为 dual attack / sampling bottleneck 的理论背景；不一定直接给训练数据，但能帮助设计 attack pipeline labels。
- Suggested reading priority：今日或明日精读。
- Concrete next action：画出 dual attack 与 trapdoor sampling 中 sampling bottleneck 的流程图；记录哪些部分可转为实验或 proof-sketch discussion。

## 3. Secondary-watch：5 篇本周跟踪

| Priority | Paper | Source | Score | Why watch | Next action |
| --- | --- | --- | --- | --- | --- |
| 1 | From Perfect to Approximate Hints: Efficient LWE Secret Recovery Leveraging Low Hamming Weight | IACR ePrint | A / 100，read 89 | sparse / low-Hamming-weight LWE secret recovery，贴近 side-channel hints、support recovery、AI4Lattice coordinate selection | 本周精读，抽取 threat model、hint model、secret recovery baseline |
| 2 | CoNAN: A Structure-Aware Framework for Lattice Cryptanalysis | IACR ePrint | A / 100，read 83 | structure-aware lattice cryptanalysis，适合作为 AI4Lattice / structured MLWE representation 背景 | 本周读 introduction + method，判断是否能接到 negative-cyclic / block-circulant modeling |
| 3 | BRaccoon: Concurrently Secure Blind Lattice Signatures from Raccoon | IACR ePrint | A / 100，read 82 | blind lattice signatures、privacy primitive、lattice advanced primitive，接近 Module-SIS / commitment / ring signature narrative | 略读 construction interface、assumption、proof goal，加入 Module-SIS 原语 related work |
| 4 | On the Secrecy of the Encapsulation Coin in ML-KEM | IACR ePrint | A / 100，read 76 | ML-KEM encapsulation coin secrecy，强 PQC implementation security positive | 本周读实验设置、受影响 library、coin recovery threat model，准备问导师是否值得做 implementation audit mini-project |
| 5 | When Removing Reductions Goes Wrong: Auditing Reduction Placement in Production ML-DSA Implementations | IACR ePrint | A / 100，read 74 | ML-DSA / Dilithium production audit、NTT / Montgomery reduction placement，适合 PQC implementation security 叙事 | 略读 audit method 和 bug model，作为 ML-DSA implementation checklist 素材 |

备选补读：

- GPU Acceleration of Learning With Errors KEMs Using OpenACC for Post-Quantum Cryptography：偏 implementation / acceleration，适合做 systems background，不优先精读。
- HRA-Secure Lattice-based Proxy Re-Encryption without Noise Flooding：高级 lattice primitive，可作为 privacy primitive / PRE related work，但对当前短期 Module-SIS chameleon hash 不是第一优先级。

## 4. Noise / Watchlist：建议降级或人工复核

### Falcon-X: A Time Series Foundation Model for Heterogeneous Multivariate Modeling

- 来源：research progress draft 中出现为 HIGH / TODO_READ。
- 风险：标题中的 Falcon 更像 time-series model 名称，不是 Falcon / FN-DSA signature。
- 建议：标为 false-positive risk，除非正文明确连接 PQC Falcon、FN-DSA、lattice signatures 或 cryptographic implementation，否则不进入阅读队列。

### Practical Anonymous Two-Party Gradient Boosting Decision Tree

- 来源：weekly JSON 与 verification backlog。
- 风险：它可能因为 privacy / secure computation / FHE 相关词被拉入，但核心看起来偏 GBDT / PSI / secure analytics。
- 建议：只作为 privacy / FHE application watchlist。除非原文明确使用 lattice-based FHE、CKKS/BFV/BGV/TFHE 参数、安全估计或实现细节，否则不进入 AI-assisted lattice / LWE / SIS / PQC 主线。

### A gentle introduction to lattice-based cryptography

- 来源：IACR ePrint，A / 100，read 75。
- 风险：可能是 survey / introduction，不一定提供新结果。
- 建议：作为 onboarding / reference map，不作为本周 must-read；可快速扫目录和 references。

## 5. Reading Queue Preview

只读检查 `state/reading-queue.json` 显示，上述 must-read / secondary-watch 大多已经以 `HIGH`、`TODO_READ`、`TODO_VERIFY` 进入队列。Phase 10A 不修改状态，建议后续手动操作：

- 把 3 篇 must-read 保持 `HIGH / TODO_READ / TODO_VERIFY`。
- 把 `From Perfect to Approximate Hints` 与 `CoNAN` 保持 HIGH，但排在 3 篇 must-read 之后。
- 把 `BRaccoon` 放入 Module-SIS / privacy primitive related work。
- 把 `On the Secrecy of the Encapsulation Coin in ML-KEM` 与 `When Removing Reductions Goes Wrong` 放入 PQC implementation security 子队列。
- 把 Falcon-X 标记为 suspected false positive，等待人工核验后降级或移出。

## 6. Advisor Update Draft Preview

可直接问导师的 5 个问题：

1. `Unified Dual Attack Analyses` 是否值得作为本周组会的主报告论文，重点讲 covariance-based score distribution 和 Kyber / ML-KEM 安全估计？
2. `Module Lattice Security (Part IV)` 的 quantum attack claim 应该如何核验？是否需要先找 Parts I-III 和相关评论？
3. `Improved Dual Attack and Trapdoor Sampling` 是否能作为连接 LWE attack 与 lattice primitive trapdoor proof background 的桥梁论文？
4. ML-KEM encapsulation coin secrecy 是否适合发展成一个小型 implementation audit / reproducibility artifact？
5. BRaccoon 这类 blind lattice signature 是否能为 Module-SIS chameleon hash / credential / ZK-friendly PQ privacy narrative 提供 related work，而不是立即转成短期论文主线？

## 7. Obsidian Note Scaffold Preview

只读检查显示 `exports/obsidian-paper-notes/` 下已有若干 paper note scaffold，包括 `on-the-secrecy-of-the-encapsulation...`、`from-perfect-to-approximate-hints...`、`braccoon...` 等。Phase 10A 不生成或修改 notes。

建议手动创建或补全的 note 顺序：

1. `Unified Dual Attack Analyses`：核心 attack reading note。
2. `Module Lattice Security (Part IV)`：claim verification note。
3. `Improved Dual Attack and Trapdoor Sampling`：attack / trapdoor bridge note。
4. `From Perfect to Approximate Hints`：sparse LWE / support recovery note。
5. `On the Secrecy of the Encapsulation Coin in ML-KEM`：PQC implementation audit note。

每个 note 先只写：

- paper facts
- assumptions / target
- lattice/PQC anchor evidence
- what to verify
- relation to your research direction
- one concrete experiment or proof-check idea

## 8. Source Health Caveats

W23 coverage 显示：

- expected_days：7
- loaded_days：2026-05-28 到 2026-06-03，缺失 0 天
- total_records：31
- unique_records：31
- label_counts：A 19，B 5，C 7

source health summary 显示 arXiv / Crossref / DBLP / IACR / OpenAlex / Semantic Scholar 都有记录，但包含 yellow / red 状态。Semantic Scholar 多次 rate_limit，arXiv 存在 timeout / rate limit。结论：

- 本周阅读队列可以用，但仍需人工核验原文。
- Semantic Scholar metadata 只可作为 advisory context，不作为 ranking authority。
- 对高冲击 claim，尤其 Module-LWE quantum attack，应优先核验原文和后续社区反馈。

## 9. Suggested 3-day Reading Plan

### Day 1：attack baseline

- 精读 `Unified Dual Attack Analyses`。
- 输出：一页中文 summary，包含 attack setting、score distribution、assumption、与 ML-KEM/Kyber 的关系。

### Day 2：claim verification

- 精读 `Module Lattice Security (Part IV)`。
- 输出：claim checklist，标出哪些是 theorem、哪些是 experiment/verification、哪些需要 TODO_VERIFY。

### Day 3：bridge to primitive / implementation

- 精读 `Improved Dual Attack and Trapdoor Sampling` 的核心部分。
- 略读 `On the Secrecy of the Encapsulation Coin in ML-KEM`。
- 输出：一个 advisor question list，区分 LWE attack 主线、Module-SIS primitive 主线、PQC implementation security 主线。

## 10. Immediate Next Actions

- 今天：读 `Unified Dual Attack Analyses`，不要先被其他 A / 100 分散注意力。
- 本周：完成 3 篇 must-read 的 TODO_VERIFY，给导师准备 5 个问题。
- 暂不做：不要把 Falcon-X 当成 PQC Falcon；不要把 GBDT privacy paper 当成 AI4Lattice；不要把 FHE application 直接升级为核心 idea。
- 可选：若后续手动执行 workflow，可先 dry-run reading queue update，再人工确认是否改变状态。
