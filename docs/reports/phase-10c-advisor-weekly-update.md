# 本周研究进展概览

生成日期：2026-06-03

本周我把 2026-W23 的 digest、Phase 10A reading pipeline 和 Phase 10B Top 3 paper notes 收敛成一个可向导师汇报的短阅读计划。当前所有技术内容仍处于 TODO_VERIFY：我已经用 digest metadata 做了初筛和研究方向映射，但还没有完成原文精读、定理核验、实验复现或参数检查。

本周核心发现：

- LWE / MLWE 攻击与安全估计方向出现多篇强相关论文，尤其是 dual attack score distribution、Module-LWE quantum attack claim、以及 ML-KEM implementation security。
- `Unified Dual Attack Analyses` 最适合作为深读论文和 AI4Lattice attack-cost proxy 背景。
- `Module Lattice Security (Part IV)` 具有高冲击潜力，但必须先核验 assumptions、parameter scope 和社区反馈。
- `On the Secrecy of the Encapsulation Coin in ML-KEM` 很适合做 advisor update，因为主题清楚、PQC implementation security 连接强，但 library behavior 和 threat model 必须 TODO_VERIFY。

# 本周最值得汇报的 3 篇论文

## 1. Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE

* Source / ID：IACR ePrint 2026/1048，https://eprint.iacr.org/2026/1048
* Priority：A / 100，reading_priority_score 95，必须精读
* Lattice/PQC anchor evidence：LWE/RLWE/MLWE；ML-KEM/Kyber；ML-DSA/Dilithium；PQC anchor；BKZ/lattice attack
* Why it matters：digest metadata 显示该论文聚焦 LWE dual attack 的 score distribution / covariance analysis，可能影响 dual attack 成功率估计、Kyber / ML-KEM 安全讨论和 attack estimator 校准。

### 论文事实

- Digest metadata 给出作者为 Yechen Li 和 Qunxiong Zheng。
- Digest abstract 说明它讨论 dual attacks on LWE 中 score expectation / variance，以及 prior independence assumption 的问题。
- 当前排名和阅读优先级来自项目 digest，不等于论文结论已被人工核验。

### 背景补充

- Dual attack 的 score distribution 与 false positive / success probability 有关，是 LWE security estimation 的基础部件。
- 对 AI4Lattice 来说，score / covariance / attack success signal 可以成为 learning-to-rank 或 attack-cost proxy 的候选监督信号。

### 我的推断

- 这篇最适合连接我的 AI-assisted lattice cryptanalysis 主线：不是让模型端到端破解 LWE，而是让模型辅助 classical dual attack pipeline 的 ranking、cost prediction 或 hard/easy instance triage。
- 它也能帮助我把 Swin-guided coordinate selection 的叙事建立在 classical attack score 上，而不是只讲 neural heuristic。

### Relation to my research direction

- AI4Lattice / Swin-guided attack：强相关。
- LWE / MLWE cryptanalysis：强相关。
- ML-KEM / Kyber security estimation：中强相关，需原文核验。
- Module-SIS chameleon hash：间接相关，只能作为参数安全分析背景。

### TODO_VERIFY

- 核验 score expectation / variance 公式。
- 核验实验设置和参数是否与 Kyber / ML-KEM 直接相关。
- 核验是否真的能转化为可复现实验特征。

## 2. Module Lattice Security (Part IV): Probabilistic Polynomial Quantum Attack on Module-LWE over 2-Power Cyclotomics

* Source / ID：arXiv:2605.17412，http://arxiv.org/abs/2605.17412v2
* Priority：A / 100，reading_priority_score 92，必须精读
* Lattice/PQC anchor evidence：LWE/RLWE/MLWE；NTRU；ML-KEM/Kyber；ML-DSA/Dilithium；Falcon/FN-DSA；PQC anchor；lattice
* Why it matters：digest metadata 显示该论文提出关于 Module-LWE over 2-power cyclotomics 的 quantum attack claim，并提到 ML-KEM-1024、Falcon、Hawk、NTRU 等对象。由于 claim 潜在冲击很大，应作为重点核验对象。

### 论文事实

- Digest metadata 给出作者为 Ming-Xing Luo。
- Digest abstract 声称讨论 quantum attack、ML-KEM-1024、2-power cyclotomic lattice schemes 和 polynomial-time quantum algorithm。
- 这些 claim 目前只来自 digest metadata，不能作为已接受结论。

### 背景补充

- MLWE / RLWE 的 ring structure、cyclotomic structure 和 module structure 是 lattice-based PQC 安全分析核心。
- 强 quantum attack claim 通常需要特别谨慎：要看 problem definition、reduction chain、parameter regime、success probability、是否适用于真实标准参数。

### 我的推断

- 这篇对我的 RLWE / MLWE negative-cyclic modeling 主线很重要，因为它可能涉及结构化环表示和 2-power cyclotomic ring。
- 它不应直接被拿来支持 Module-SIS chameleon hash；MLWE 与 Module-SIS 的安全目标和证明结构不同。

### Relation to my research direction

- MLWE / RLWE negative-cyclic modeling：强相关。
- ML-KEM / Kyber security narrative：强相关但 TODO_VERIFY。
- AI4Lattice：间接相关，可作为 structured representation 背景。
- Module-SIS chameleon hash：间接相关，仅作为 module lattice assumption literacy。

### TODO_VERIFY

- 核验 Parts I-III 是否必须先读。
- 核验 attack model、assumption mapping、parameter scope。
- 核验是否有社区讨论或反驳。
- 核验是否能影响真实 ML-KEM 参数，还是仅限特定模型。

## 3. On the Secrecy of the Encapsulation Coin in ML-KEM

* Source / ID：IACR ePrint 2026/1117，https://eprint.iacr.org/2026/1117
* Priority：A / 100，reading_priority_score 76，建议精读；本周作为 advisor update 高优先级
* Lattice/PQC anchor evidence：LWE/RLWE/MLWE；ML-KEM/Kyber；ML-DSA/Dilithium；PQC anchor
* Why it matters：digest metadata 显示该论文直接讨论 ML-KEM encapsulation coin secrecy 和多个 library 的 implementation behavior。它非常适合连接 PQC deployment / implementation security / reproducibility artifact。

### 论文事实

- Digest metadata 给出作者为 Madjid G. Tehrani、William J Buchanan、Mouad Lemoudden。
- Digest abstract 说明 ML-KEM encapsulation 使用 fresh 32-byte coin，并讨论 coin secrecy 在实践中的保护问题。
- Digest abstract 提到 OpenSSL、wolfSSL、AWS-LC、Go、Bouncy Castle、CIRCL 等 library，但具体行为必须原文核验。

### 背景补充

- ML-KEM / Kyber 是标准化 module-lattice KEM；实现中的 randomness handling、API exposure、validated configuration 可能影响实际部署安全。
- Implementation-security paper 必须区分 attack、misuse、test-only hook、build-time substitution、production API exposure 和 FIPS validated configuration。

### 我的推断

- 这篇可以成为短期 advisor update 中最容易讲清楚的一篇：它不要求先推完整 lattice attack 公式，但能直接说明 deployable PQC 的安全工程问题。
- 它可能发展成一个小型 implementation audit / reproducibility checklist，但不能在未读原文前声称已经存在可复现实验。

### Relation to my research direction

- ML-KEM / Kyber implementation security：强相关。
- PhD narrative：强相关，可连接 systems security + PQC deployment。
- AI4Lattice：弱相关，不应硬连。
- Module-SIS chameleon hash：无直接关系，只能作为“实现细节影响实际安全”的背景类启发。

### TODO_VERIFY

- 核验每个 library 的具体路径和配置条件。
- 核验 threat model：攻击者能力、是否需要 build-time control、是否是 test-only path。
- 核验 FIPS-140-3 相关表述。
- 核验是否适合做最小 reproduction artifact。

# 与我的研究主线的关系

## Module-SIS chameleon hash / commitment line

本周 Top 3 中没有直接的 Module-SIS chameleon hash 构造论文。`Module Lattice Security (Part IV)` 和 `Improved Dual Attack` 类论文可作为 module lattice assumption / trapdoor sampling 背景，但不能把 MLWE 或 trapdoor sampling 结论直接迁移到 Module-SIS chameleon hash。当前最合理的做法是：把它们放入 parameter/security-analysis background，而不是改短期 Module-SIS artifact 的构造目标。

## MLWE / ML-KEM / ML-DSA line

`Module Lattice Security (Part IV)` 和 `On the Secrecy of the Encapsulation Coin in ML-KEM` 是本周 MLWE / ML-KEM 主线的两个重点：前者偏理论与结构安全 claim，后者偏 implementation security。两者都必须 TODO_VERIFY，但很适合形成一个“理论安全估计 + 部署安全工程”的 PhD narrative 小节。

## AI-assisted lattice cryptanalysis / Swin-guided attack line

`Unified Dual Attack Analyses` 是最有价值的 AI4Lattice 背景。我的推断是：可以把 dual attack score distribution、covariance feature、success probability proxy 作为 learning-assisted attack pipeline 的监督信号，而不是做端到端 key recovery。Swin-guided coordinate selection 若要讲得扎实，应以这种 classical attack score 为 baseline。

## Lattice/PQC privacy primitive line

本周 notes 里没有直接选择 BRaccoon，但 Phase 10A 中它仍是 secondary-watch。它可能与 blind lattice signatures、privacy primitives、credentials、ring signatures 有关，适合作为 Module-SIS / PQ privacy narrative 的 related work，而非本周第一优先精读。

# 本周可以向导师汇报的 3 个结论

1. 本周最强的理论阅读入口是 LWE dual attack score distribution，而不是泛 survey 或泛 PQC paper。它能直接支持我的 AI4Lattice baseline 设计。
2. MLWE / ML-KEM security claim 需要分层处理：`Module Lattice Security (Part IV)` 可能很重要，但强 quantum attack claim 必须先做 TODO_VERIFY，不能在未核验前作为结论。
3. ML-KEM encapsulation coin 论文适合快速形成 advisor discussion：它连接 standardized PQC、implementation audit 和 reproducibility artifact，但需要严格区分 paper-reported behavior 与我尚未验证的实现结果。

# 下周具体行动计划

* Quick reading task：先读 `On the Secrecy of the Encapsulation Coin in ML-KEM` 的 abstract、threat model、library table，整理一页 advisor-ready note。
* Deep technical reading task：精读 `Unified Dual Attack Analyses` 的 score distribution / covariance derivation，整理公式和实验假设。
* Experiment / implementation task：为 ML-KEM coin paper 做一个非执行型 audit checklist：library、path、attacker capability、configuration、TODO_VERIFY，不运行真实 exploit。
* Writing / research narrative task：写一段 300-500 字中文研究叙事，连接 dual attack score modeling、AI4Lattice attack-cost proxy、以及 deployable PQC implementation security。

# 导师可能追问的问题

## 1. 为什么选这三篇，而不是所有 A / 100 论文都读？

我准备如何回答：我按研究主线而不是单纯分数排序。第一篇服务 LWE dual attack 和 AI4Lattice baseline；第二篇是高冲击 MLWE / ML-KEM security claim；第三篇直接连接 ML-KEM implementation security。其他 A / 100 中有 survey、FHE application 或疑似 false positive，先放 secondary-watch。

## 2. 哪些内容已经验证，哪些只是 TODO_VERIFY？

我准备如何回答：目前只验证了 digest metadata、source URL、ranking、anchor evidence 和阅读优先级。论文定理、实验、参数、library behavior、security conclusion 都还是 TODO_VERIFY，需要读原文。

## 3. `Unified Dual Attack Analyses` 对我的 AI4Lattice 方向有什么实际用处？

我准备如何回答：我的推断是，它可以提供 classical dual attack score / covariance / success probability 的理论 baseline，用来设计 learning-assisted ranking 或 attack-cost proxy。它不是端到端破解，而是把 AI 放进 classical attack pipeline 的可解释环节。

## 4. `Module Lattice Security (Part IV)` 的 quantum attack claim 是否可信？

我准备如何回答：我还不能判断。下一步会先核验 problem definition、assumption、parameter scope、Parts I-III 和社区反馈。汇报时只能说它是需要重点核验的 high-impact claim。

## 5. 这和 Module-SIS chameleon hash 有什么关系？

我准备如何回答：没有直接构造关系。它们可以帮助我理解 module lattice security 和参数分析背景，但 MLWE 结论不能直接迁移到 Module-SIS chameleon hash。短期 Module-SIS artifact 仍应保持自己的 correctness、collision / adaptation、assumption mapping 和 parameter estimation。

## 6. ML-KEM coin paper 是否说明 ML-KEM 本身不安全？

我准备如何回答：不能这样说。根据 digest metadata，它讨论的是 encapsulation coin secrecy 和 implementation behavior。需要区分标准方案安全性、实现 API / build-time / test hook / validated configuration 等层次。

## 7. 这三篇里哪一篇最适合组会？

我准备如何回答：如果偏理论组会，选 `Unified Dual Attack Analyses`；如果偏工程安全或短汇报，选 ML-KEM coin paper；如果导师想看高冲击安全 claim，则选 `Module Lattice Security`，但要明确 TODO_VERIFY。

## 8. 是否能从这些论文发展短期投稿？

我准备如何回答：短期投稿不能直接从阅读跳到 claim。比较现实的是两个方向：一是基于 dual attack score 的 small AI4Lattice benchmark；二是基于 ML-KEM coin paper 的 implementation audit checklist / reproduction note。两者都需要先完成原文核验。

## 9. Semantic Scholar metadata 有没有影响选择？

我准备如何回答：没有。Semantic Scholar enrichment 只作为 advisory context，不覆盖 ranking，也不作为选择 Top 3 的权威依据。本次选择主要基于 digest metadata、reading_priority_score、anchor evidence 和研究主线匹配。

## 10. 这周最可能的 false positive 是什么？

我准备如何回答：Falcon-X 是明显风险，因为 Falcon 可能只是 time-series model 名称，不是 Falcon / FN-DSA signature。Practical Anonymous Two-Party GBDT 也可能是 privacy / secure analytics，而不是 AI4Lattice 或 lattice cryptanalysis。

## 11. 先读哪一篇最省时间？

我准备如何回答：先读 ML-KEM coin paper，因为它的 problem statement 和 implementation angle 最容易快速判断价值；然后读 Unified Dual Attack 做深技术积累。

## 12. 长期 PhD narrative 怎么串起来？

我准备如何回答：可以形成两条互补线：第一条是 AI-assisted but classical-grounded lattice cryptanalysis，以 dual attack score modeling 为 baseline；第二条是 deployable PQC implementation security，以 ML-KEM / ML-DSA audit 为系统安全连接点。Module-SIS chameleon hash 作为短期 primitive artifact 保持独立推进。

# 我准备如何回答

我的总体回答策略：

- 对论文事实：只引用 digest metadata 和原文读后确认的内容。
- 对背景补充：明确说这是 general lattice/PQC context。
- 对我的推断：明确标注为研究方向连接，不当作论文 claim。
- 对强 claim：统一加 TODO_VERIFY，尤其是 Module-LWE quantum attack 和 ML-KEM library behavior。
- 对短期计划：不承诺实验结果，只承诺阅读、核验、整理 checklist 和准备 advisor questions。

# Risks and caveats

* Source health caveats：W23 source health 里存在 arXiv timeout / rate limit、Semantic Scholar rate_limit、以及部分 yellow / red source 状态。报告可用，但不能替代原文核验。
* Digest metadata limitations：digest ranking 和 anchor evidence 是 triage 工具，不是 bibliographic authority，也不是安全结论。
* Semantic Scholar enrichment limitations：Semantic Scholar metadata 只作 advisory context，不能覆盖研究相关性判断，也不能替代 paper reading。
* Unverified paper content：所有 theorem、attack、experiment、parameter、implementation behavior 均为 TODO_VERIFY。
* False positive / false negative risk：Falcon-X 和 Practical Anonymous Two-Party GBDT 已被标为 watchlist 风险；也可能存在 digest 漏掉的重要 paper。

# Manual checklist before sending to advisor

* Verify paper URLs.
* Verify authors.
* Read abstracts.
* Check main theorem / construction / attack / experiment.
* Remove unsupported claims.
* Decide which 1-2 papers to actually read first.
* For ML-KEM coin paper, verify library / configuration claims.
* For Module-LWE quantum attack paper, verify assumptions and parameter scope.
* For Unified Dual Attack, verify formulas and experiment tables.
* Keep TODO_VERIFY markers until original paper reading is complete.
