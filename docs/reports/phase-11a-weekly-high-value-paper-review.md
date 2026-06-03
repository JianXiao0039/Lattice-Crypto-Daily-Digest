# Phase 11A Weekly High-Value Paper Review

生成日期：2026-06-04

本报告是公开研究工具轨道中的 weekly paper review。它只使用公开 digest / JSON / research workflow artifacts 中的论文元数据、ranking 信息、source health 信息和 public-safe 研究线索，不包含 PhD application 私人材料、target PI email、SoP、申请 tracker 或个人 self-assessment。

# Executive Summary

本周 W23 覆盖 2026-05-28 到 2026-06-03，共 loaded 7 天、missing 0 天、unique records 31 条，其中 A 类 19 条、B 类 5 条、C 类 7 条。最适合作为本周唯一 deep-read 的论文是 `Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE`，因为它在现有 digest 中为 A / 100、reading_priority_score 95，并直接连接 LWE dual attack、score distribution、attack-cost proxy 和 AI4Lattice baseline。`On the Secrecy of the Encapsulation Coin in ML-KEM` 是强 PQC / ML-KEM positive，建议 fast-skim 后决定是否进入 implementation audit 小任务。`BRaccoon` 和 `When Removing Reductions Goes Wrong` 分别适合作为 lattice privacy primitive / signature related work 与 ML-DSA implementation security checklist 素材。`Practical Anonymous Two-Party Gradient Boosting Decision Tree` 虽在 weekly JSON 中显示 A / 100，但从标题和 Phase 10A 风险说明看，应先降为 privacy / FHE watchlist，不应直接当作 AI4Lattice 或 lattice/PQC 主线论文。

# Input Evidence Used

| Input | Status | How used | Limitations |
| --- | --- | --- | --- |
| `digests/weekly/2026-W23.md` | available | 提取 weekly coverage、section grouping、high-priority list、source health summary | Markdown 是生成报告，仍需结合 JSON 核验字段 |
| `data/weekly/2026-W23.json` | available | 提取 label_counts、coverage、records、research_sections、ranking metadata | 周报 sections 中部分泛化分类可能过宽，需要人工判断 |
| `digests/2026-06-03.md` | available | 提取日报高优先级论文、source health 红黄绿概览 | 只覆盖 2026-06-03 单日 |
| `data/2026-06-03.json` | available | 提取 daily records、source_health、ranking_explanation | Semantic Scholar red，enrichment 不完整 |
| `docs/reports/phase-10a-research-reading-pipeline.md` | available | 参考 must-read / secondary-watch / noise 判断 | 属于上一阶段人工阅读规划，不等同论文事实 |
| `docs/reports/phase-10b-top-3-obsidian-notes.md` | available | 参考 Top 3 note scaffold 选择 | note scaffold 中技术细节仍需 TODO_VERIFY |
| `docs/reports/phase-10c-advisor-weekly-update.md` | available | 仅作为 public-safe 研究问题背景，不引用私人申请内容 | 不复制 advisor-facing 私人表达 |
| `docs/reports/phase-10d-dynamic-research-idea-backlog.md` | available | 参考 idea seed 风险控制和方向分布 | 不复制 PhD application positioning |
| `notes/papers/*.md` | available | 确认已有 paper note scaffold for 2026/1048、2026/1117、2605.17412 | 不把私人判断或未核验 claim 当作论文事实 |

# Weekly Paper Ranking Overview

| Paper | Source / ID | Priority | Score / label | Lattice/PQC anchor evidence | Why it matters | Read / skim / ignore | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE | IACR ePrint 2026/1048 | 必须精读 | A / 100; reading 95 | LWE; dual attack; covariance; ML-KEM / ML-DSA context in tags | 最贴近 LWE cryptanalysis、attack-cost model、AI4Lattice ranking baseline | read deeply | Verify attack model, score distribution derivation, parameter impact |
| Module Lattice Security (Part IV): Probabilistic Polynomial Quantum Attack on Module-LWE over 2-Power Cyclotomics | arXiv 2605.17412v2 | 必须精读 | A / 100; reading 92 | Module-LWE; cyclotomic; ML-KEM; module lattice security | 潜在影响 MLWE / module lattice security 叙事，但强 claim 必须谨慎核验 | skim now, deep-read after 2026/1048 | Verify claim scope, prior parts, complexity model |
| From Perfect to Approximate Hints: Efficient LWE Secret Recovery Leveraging Low Hamming Weight | IACR ePrint 2026/1081 | 必须精读 | A / 100; reading 89 | LWE; low Hamming weight; secret recovery; cryptanalysis | 适合作为 sparse / hinted LWE、support recovery、hybrid ranking 的候选 baseline | skim this week | Verify hint model, threat model, whether side-channel is actually central |
| CoNAN: A Structure-Aware Framework for Lattice Cryptanalysis | IACR ePrint 2026/1041 | 建议精读 | A / 100; reading 83 | lattice cryptanalysis; structure-aware framework | 可能支撑 structured MLWE / negative-cyclic / representation learning 背景 | skim this week | Verify whether method is deterministic, heuristic, or implementation-specific |
| BRaccoon: Concurrently Secure Blind Lattice Signatures from Raccoon | IACR ePrint 2026/1084 | 建议精读 | A / 100; reading 82 | blind lattice signatures; Raccoon; commitments / ZK keywords | 连接 lattice signatures、privacy primitives、commitment / ring signature related work | fast skim | Verify assumptions, security model, relation to Module-SIS |
| HRA-Secure Lattice-based Proxy Re-Encryption without Noise Flooding | IACR ePrint 2026/1113 | 建议精读 | A / 100; reading 77 | lattice-based PRE; LWE; BGV; no noise flooding | 可作为 lattice privacy / PRE / FHE background | skim | Verify construction assumptions and whether it helps current primitive line |
| On the Secrecy of the Encapsulation Coin in ML-KEM | IACR ePrint 2026/1117 | 建议精读 | A / 100; reading 76 | ML-KEM; KEM; FIPS 203; OpenSSL; PQC implementation | 强 ML-KEM implementation security positive，适合 audit checklist | fast skim | Verify affected libraries, threat model, coin secrecy claim |
| GPU Acceleration of Learning With Errors KEMs Using OpenACC for Post-Quantum Cryptography | arXiv 2606.01211v1 | 建议精读 | A / 100; reading 75 | LWE; KEM; PQC; implementation | 更偏 acceleration / systems，可作为 implementation background | skim | Verify whether it is ML-KEM-adjacent or generic LWE KEM |
| A gentle introduction to lattice-based cryptography | IACR ePrint 2026/1098 | 建议精读 | A / 100; reading 75 | Kyber; Dilithium; KEM; lattice cryptography | 适合 onboarding / reference map，不是新技术贡献优先项 | skim selectively | Verify whether survey adds useful references |
| When Removing Reductions Goes Wrong: Auditing Reduction Placement in Production ML-DSA Implementations | IACR ePrint 2026/1032 | 建议精读 | A / 100; reading 74 | ML-DSA; production implementation; reduction placement | 可转成 ML-DSA implementation checklist 和 reproducibility note | fast skim | Verify bug model, implementation scope, production relevance |
| Practical Anonymous Two-Party Gradient Boosting Decision Tree | arXiv 2605.26903v1 | 可略读 | A / 100; reading 57 | FHE / privacy tags in digest, but lattice/PQC anchor uncertain | 可能是 privacy / secure analytics application，不能直接当 AI4Lattice | watchlist / likely noise | Verify whether it uses lattice FHE with real parameters |
| Privacy-preserving collective reinforcement learning using fully homomorphic encryption in usage-based insurance | Crossref DOI 10.1016/j.ins.2026.123598 | B 类跟踪 | B / 70 | FHE keyword, application setting | 应作为 FHE application watchlist，不应高估为 lattice cryptanalysis | watchlist | Verify actual HE scheme and cryptographic depth |

# One Deep-Read Paper

Selected paper: **Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE**

## Why this is the best deep-read choice

论文事实：

- Weekly JSON / digest 记录该论文为 IACR ePrint 2026/1048。
- 现有 ranking 为 A / 100，reading_priority_score 为 95，priority_label 为必须精读。
- 现有字段显示 research_tags 包括 LWE、ML-KEM、SIS、ML-DSA、Lattice Reduction、Cryptanalysis、FHE。
- research_sections 包括 LWE / RLWE / MLWE 与 BKZ / LLL / G6K / Lattice Reduction / Attacks。

背景补充：

- Dual attack、score distribution、covariance analysis 这类主题很适合转化为可复现的 attack-cost reasoning、参数估计和 AI4Lattice ranking baseline。
- 相比 ML-KEM implementation paper，它更直接服务 LWE / MLWE cryptanalysis 主线。

我的推断：

- 这篇最适合用 3 小时 deep pass，目标不是马上接受结论，而是抽取 attack model、score distribution assumptions、参数表和可复现实验入口。
- 它可能成为后续 Swin-guided coordinate selection / hybrid ranking 的 label 或 cost-proxy 背景，但这需要读原文后 TODO_VERIFY。

## Expected payoff

- 得到一个 dual attack / score distribution 的结构化阅读卡。
- 明确它是否能影响 Kyber / ML-KEM 或 MLWE security estimation。
- 抽取可能服务 AI4Lattice baseline 的 feature / label / cost proxy。

## Technical prerequisites

- LWE / MLWE 基本定义。
- Dual attack 基本流程。
- BKZ / lattice reduction 与 estimator 背景。
- 概率分布、covariance、score distribution 的基本理解。
- Kyber / ML-KEM 参数与 security estimation 背景。

## Risks

- 摘要级 metadata 不足以判断 claim 强度。
- 可能只适用于特定参数或假设。
- digest 中无法确认实验是否可复现。
- 不应把 covariance score model 直接当作 AI model label，必须先核验原文定义。

## TODO_VERIFY

- Verify exact attack target and assumption.
- Verify whether analysis is classical, quantum, heuristic, or proof-level.
- Verify whether parameters are close to ML-KEM or only illustrative.
- Verify whether code, estimator script, or data is available.
- Verify whether score distribution can be cleanly mapped to AI4Lattice ranking labels.

# Three Fast-Skim Papers

## 1. On the Secrecy of the Encapsulation Coin in ML-KEM

- Why skim: 强 ML-KEM / FIPS 203 / OpenSSL anchor，直接服务 PQC implementation security。
- What to extract: threat model, affected library/configuration, encapsulation coin exposure path, whether the issue is API-level, implementation-level, or deployment-level.
- Decision after skim: 如果 paper 给出清晰 reproducible cases，则进入 implementation audit checklist；否则保留为 ML-KEM security review related work。

## 2. BRaccoon: Concurrently Secure Blind Lattice Signatures from Raccoon

- Why skim: lattice blind signature / Raccoon / commitment / ZK 相关，贴近 lattice privacy primitive 与 signature-adjacent research line。
- What to extract: assumptions, security model, whether SIS / Module-SIS / lattice trapdoor appears, relation to blind signature and linkability.
- Decision after skim: 如果 assumptions 与 Module-SIS / commitments 可比较，加入 primitive connection map；否则作为 advanced lattice protocol related work。

## 3. When Removing Reductions Goes Wrong: Auditing Reduction Placement in Production ML-DSA Implementations

- Why skim: ML-DSA / production implementation / reduction placement anchor 明确，适合形成 checklist。
- What to extract: reduction placement bug model, affected implementation pattern, test method, reproducibility details.
- Decision after skim: 如果方法可复现，加入 ML-DSA implementation audit checklist；如果高度工程依赖，作为 implementation cautionary related work。

# One Research-Idea Candidate

## Working idea title

Dual-Attack Score Distribution Review and Reproducible AI4Lattice Baseline Map

## Minimum viable artifact

一份 public-safe technical note，围绕 `Unified Dual Attack Analyses`、`From Perfect to Approximate Hints`、`CoNAN` 三类论文整理：

- attack target
- input assumptions
- score / covariance / support signal
- possible label source
- reproducibility status
- relation to classical baseline
- TODO_VERIFY list

## Relation to user's research profile

- LWE / MLWE：核心 anchor。
- lattice reduction / attacks：dual attack、hybrid attack、score distribution。
- AI-assisted lattice cryptanalysis：可作为 coordinate ranking / attack-cost proxy 的前置整理。
- Swin-guided coordinate selection：可能提供标签和结构化 feature 方向，但不能在未读原文前声称可直接训练。

## Risk

- Novelty risk: medium. 可能只是 literature map，而非新 cryptanalytic contribution。
- Implementation risk: medium. 需要找到可复现参数、脚本或自己实现 baseline。
- Claim risk: high if overclaimed. 必须避免 “AI breaks LWE/MLWE” 这类表述。

## TODO_VERIFY

- Verify whether papers expose enough parameters for a reproducible benchmark.
- Verify whether score distribution can be used as ML label without changing meaning.
- Verify existing literature on learning-assisted lattice attack ranking.
- Verify whether a toy benchmark is acceptable as a research artifact.

# Noise / Watchlist Items

## Practical Anonymous Two-Party Gradient Boosting Decision Tree

- Current generated ranking: weekly JSON shows A / 100, reading_priority_score 57.
- Risk: title suggests anonymous two-party GBDT, which may be privacy / secure computation rather than lattice cryptography.
- Watchlist rule: include only if original paper clearly uses lattice-based FHE, CKKS/BFV/BGV/TFHE, RLWE parameters, or PQC-grounded primitives.
- Current action: watchlist / likely noise for AI4Lattice and LWE/SIS/PQC sections.

## Privacy-preserving collective reinforcement learning using fully homomorphic encryption in usage-based insurance

- Current generated ranking: B / 70.
- Risk: application FHE paper may not discuss lattice assumptions, RLWE parameters, or security analysis deeply.
- Current action: FHE application watchlist only.

## A gentle introduction to lattice-based cryptography

- Current generated ranking: A / 100, reading 75.
- Risk: likely introductory / survey material, not a new result.
- Current action: skim references and definitions; do not spend deep-read slot.

## Generic advanced crypto papers

Examples from weekly sections include adaptor signatures, vector commitments, PIR, traitor tracing, and functional encryption.

- Rule: keep only if the paper is explicitly lattice/PQC/HE/FHE anchored.
- Current action: C/B related work queue, not deep-read.

## Falcon-X

- Phase 10A identified Falcon-X as a false-positive risk from earlier workflow material.
- Rule: title word "Falcon" is insufficient. It must mean Falcon / FN-DSA lattice signature or related cryptographic implementation.
- Current action: ignore unless original source clearly connects to PQC Falcon / FN-DSA.

# Source Health Caveats

## Source health red/yellow/green

Weekly coverage:

- expected_days: 7
- missing_days: 0
- total_records: 31
- unique_records: 31
- label_counts: A 19, B 5, C 7

Daily 2026-06-03 source health:

- green: crossref, iacr_eprint
- yellow: arxiv, dblp, openalex
- red: semantic_scholar

Weekly source health summary:

- sources observed: arxiv, crossref, dblp, iacr_eprint, openalex, semantic_scholar
- status counts in summary: green 4, yellow 22, red 16

## Semantic Scholar enrichment limitations

Semantic Scholar is optional enrichment only. The report must not depend on it for ranking authority. If `SEMANTIC_SCHOLAR_API_KEY` is not configured or rate limited, paper selection should still rely on source-native metadata, digest scores, and manual verification.

## IACR latest/RSS confidence

IACR ePrint appears as a productive source for W23 and 2026-06-03. The ML-KEM paper `2026/1117` is present in weekly and daily artifacts, which supports recent IACR latest/RSS recovery confidence for this sample. This does not prove every IACR item was captured; false negatives remain possible.

## Possible false negatives

- arXiv had yellow / timeout / rate-limit caveats in daily source health.
- DBLP and OpenAlex had yellow degradation.
- Semantic Scholar was red, so citation / corpus metadata may be missing.
- Papers with weak titles but strong abstracts may be missed or under-ranked if source metadata is sparse.

# Weekly Reading Plan

## 90-minute quick pass

1. 20 min: read abstract / contribution list of `On the Secrecy of the Encapsulation Coin in ML-KEM`.
2. 20 min: skim `BRaccoon` for assumptions and security model.
3. 20 min: skim `When Removing Reductions Goes Wrong` for audit method and implementation pattern.
4. 15 min: scan `Practical Anonymous Two-Party GBDT` only to decide whether lattice/FHE anchor is real.
5. 15 min: update TODO_VERIFY list and decide which papers leave watchlist.

## 3-hour deep pass

Deep-read `Unified Dual Attack Analyses`.

Suggested breakdown:

- 30 min: abstract, intro, threat model.
- 45 min: dual attack setup and score distribution definitions.
- 45 min: covariance analysis and assumptions.
- 30 min: parameter / experiment / comparison table.
- 30 min: write reading card with TODO_VERIFY and possible baseline extraction.
- 30 min: decide whether to link it to AI4Lattice coordinate ranking.

## One reproducibility or parameter-check task

Create a small public-safe parameter checklist for `Unified Dual Attack Analyses`:

- target LWE / MLWE family
- dimension / modulus / noise fields if available
- secret distribution
- attack model
- claimed complexity or score model
- code availability
- estimator compatibility

Do not claim reproduction until actually run.

## One note-writing task

Write or update one note:

- title: `2026-W23-dual-attack-score-distribution-reading-card.md`
- content: paper facts, background, inference, TODO_VERIFY, possible AI4Lattice baseline hooks.

Keep it public-safe and avoid application-specific content.

# Research Backlog Updates

## Seed 1: Dual attack score distribution baseline

- lattice/PQC anchor: LWE dual attack, MLWE / ML-KEM security estimation.
- short-term value: reading card plus parameter extraction.
- long-term value: AI4Lattice cost proxy / coordinate ranking baseline.
- TODO_VERIFY: whether score distribution can be cleanly operationalized.

## Seed 2: Hinted / low-Hamming-weight LWE secret recovery map

- lattice/PQC anchor: LWE secret recovery and sparse secrets.
- short-term value: threat model table for hinted LWE papers.
- long-term value: support recovery and Swin-guided coordinate selection.
- TODO_VERIFY: exact hint model and whether side-channel assumptions are present.

## Seed 3: ML-KEM encapsulation coin audit checklist

- lattice/PQC anchor: ML-KEM / Kyber / FIPS 203.
- short-term value: implementation-security checklist.
- long-term value: reproducible PQC deployment review workflow.
- TODO_VERIFY: affected libraries and exploitability claims.

## Seed 4: ML-DSA reduction placement implementation checklist

- lattice/PQC anchor: ML-DSA / Dilithium implementation.
- short-term value: audit method summary.
- long-term value: PQC implementation reproducibility artifact.
- TODO_VERIFY: production scope and test reproducibility.

## Seed 5: Lattice blind signatures and privacy primitive map

- lattice/PQC anchor: BRaccoon, blind lattice signatures, commitments / ZK-related signals.
- short-term value: related-work map for lattice privacy primitives.
- long-term value: bridge to ring signatures, commitments, and chameleon hash variants.
- TODO_VERIFY: assumptions and whether Module-SIS is directly involved.

## Seed 6: Structure-aware lattice cryptanalysis reading cluster

- lattice/PQC anchor: CoNAN and structure-aware lattice cryptanalysis.
- short-term value: identify representation / feature extraction ideas.
- long-term value: negative-cyclic / block-structured MLWE modeling.
- TODO_VERIFY: whether method is reproducible and not merely heuristic.

## Seed 7: LWE KEM acceleration as implementation background

- lattice/PQC anchor: LWE KEM, PQC, OpenACC.
- short-term value: systems background for implementation section.
- long-term value: performance / reproducibility track.
- TODO_VERIFY: relation to standardized ML-KEM versus generic LWE KEM.

## Seed 8: FHE application watchlist filter

- lattice/PQC anchor: FHE only if CKKS/BFV/BGV/TFHE/RLWE parameters are explicit.
- short-term value: prevent generic privacy ML papers from polluting core queue.
- long-term value: cleaner FHE / secure aggregation review discipline.
- TODO_VERIFY: actual cryptographic scheme and parameter depth.

# Next Actions

## Tomorrow

1. Deep-read `Unified Dual Attack Analyses` for 90 minutes minimum.
2. Write a one-page TODO_VERIFY reading card.
3. Skim `On the Secrecy of the Encapsulation Coin in ML-KEM` and extract threat model fields.

## This week

1. Finish 3-hour deep pass on `Unified Dual Attack Analyses`.
2. Fast-skim `BRaccoon` and `When Removing Reductions Goes Wrong`.
3. Decide whether `Practical Anonymous Two-Party GBDT` is real FHE/lattice watchlist or noise.
4. Add 1 public-safe reproducibility / parameter checklist.

## Next week

1. Pick one of two clusters for deeper work:
   - dual attack / score distribution / AI4Lattice baseline
   - ML-KEM / ML-DSA implementation audit checklist
2. Convert one cluster into a small reproducible artifact plan.
3. Re-run weekly review manually after the next weekly digest is available.

# Boundary and Safety Notes

- No source ingestion, ranking thresholds, taxonomy semantics, section classifier, query expansion, negative keywords, workflow semantics, release metadata, digest artifacts, `papers.db`, `.env`, or secrets were modified by this report.
- This report does not contain PhD application materials, target PI emails, SoP drafts, private application tracker entries, or personal self-assessment.
- No scheduled automation is introduced. All next actions are manual.
