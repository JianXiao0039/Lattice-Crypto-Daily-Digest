# Phase 10E 27fall PhD Research Narrative

生成日期：2026-06-04

本报告用于从近期 digest、Top 3 paper notes、advisor weekly update 和 dynamic idea backlog 中提炼 27fall PhD 申请叙事。它不是正式 SoP，也不是论文结论。所有尚未读原文、尚未复现、尚未核验的技术内容都保留 TODO_VERIFY。

# Executive Summary

你的 emerging research identity 可以概括为：以 lattice cryptography 和 PQC 为核心，结合可复现实现、安全参数分析和 classical-grounded AI-assisted lattice cryptanalysis。短期最现实的产出路径不是直接做大而空的 AI 破译，而是围绕 Module-SIS chameleon hash / commitment、ML-KEM implementation security、ML-DSA audit checklist、以及 dual attack score modeling 做小而扎实的 artifact。长期 PhD 主线可以定位为“可部署、可验证、可解释的 lattice-based cryptography”，其中一条线关注 lattice/PQC primitives，另一条线关注 AI-assisted but classical-grounded cryptanalysis。近期 digest 证据支持 LWE / MLWE attack、ML-KEM / ML-DSA implementation security 和 lattice privacy primitives 三个方向。对 27fall 申请而言，最稳健的叙事是：先用一个短期可交付 artifact 证明执行力，再把它连接到更长期的 PQC security、privacy primitives 和 AI4Lattice 研究议程。所有强 claim，例如 Module-LWE quantum attack 或具体 library behavior，都必须 TODO_VERIFY。

# Input Evidence Used

| File | Status | How it contributed | Limitations |
| --- | --- | --- | --- |
| `docs/reports/phase-10d-dynamic-research-idea-backlog.md` | available | 提供 12 个 idea、Top 5 推荐、one-month plan、avoid list | 仍是 idea backlog，不是 novelty proof |
| `notes/ideas/dynamic-lattice-pqc-idea-backlog.md` | missing | 未使用 | 可后续手动创建 Obsidian idea note |
| `docs/reports/phase-10c-advisor-weekly-update.md` | available | 提供导师汇报叙事、问题和 cautious answers | 基于 digest metadata，技术内容仍 TODO_VERIFY |
| `docs/reports/phase-10b-top-3-obsidian-notes.md` | available | 提供 Top 3 papers 和 note paths | Paper content 未完成原文精读 |
| `notes/papers/*.md` | available | 提供三张 scaffold notes：dual attack、Module-LWE quantum claim、ML-KEM coin | scaffold notes 明确 TODO_VERIFY |
| `docs/reports/phase-10a-research-reading-pipeline.md` | available | 提供 reading order、secondary watch、noise risks | 仍是 triage，不是 final bibliography |
| `digests/2026-06-03.md` | available | 提供 daily report context | 未在本报告中直接引用为技术事实 |
| `data/2026-06-03.json` | available | 提供 ML-KEM coin paper metadata | JSON ranking 不是研究结论 |
| `digests/weekly/2026-W23.md` | available | 提供 weekly narrative context | 未替代原文阅读 |
| `data/weekly/2026-W23.json` | available | 提供 W23 rankings, source health and sections | Metadata has source health caveats |

# Current Research Identity

当前定位可以写成四层：

1. **lattice cryptography / PQC core**：围绕 LWE、RLWE、MLWE、SIS、Module-SIS、NTRU、ML-KEM、ML-DSA 和 lattice reduction / attacks。
2. **quick-paper primitive construction**：以 Module-SIS chameleon hash / commitment / lightweight lattice primitive 为短期构造方向，强调 formal syntax、correctness、security goal、parameterization 和 reproducible implementation。
3. **reproducible implementation / parameterization**：以 ML-KEM randomness、ML-DSA reduction placement、PQC implementation audit checklist 和 parameter estimation 为可交付 artifact。
4. **AI-assisted lattice cryptanalysis**：以 dual attack score distribution、sparse LWE support recovery、Swin-guided coordinate selection、structured RLWE / MLWE representation 为长期主线，但坚持 classical attack pipeline grounded，不做端到端破解真实参数的夸张表述。

隐私 primitive angle 也有潜力：lattice-based commitments、linkable ring signatures、anonymous credentials、registration-based encryption、ZK-friendly PQ privacy primitives。但当前证据还不足以把它作为唯一主线，适合作为和 Module-SIS construction 连接的 PhD longline。

# Research Narrative Version 1: Conservative

## 中文段落

我目前的研究兴趣集中在 lattice-based cryptography 和 post-quantum cryptography，尤其关注 LWE / MLWE / Module-SIS assumptions、ML-KEM / ML-DSA implementation security，以及可复现的参数化实现。我希望先从一个可控的短期项目入手，例如 Module-SIS-based chameleon hash / commitment 的 formalization 与 reproducible parameterization，或 ML-KEM randomness / encapsulation coin security review 的 reproducible audit checklist。在这个阶段，我更重视把 syntax、correctness、assumption mapping、parameter estimation 和 TODO_VERIFY 的实验边界做清楚，而不是过早声称新的安全结论。

## English paragraph

My current research interests are centered on lattice-based cryptography and post-quantum cryptography, with a focus on LWE / MLWE / Module-SIS assumptions, ML-KEM / ML-DSA implementation security, and reproducible parameterization. As a first step, I aim to work on bounded and verifiable projects, such as a Module-SIS-based chameleon hash or commitment primitive with reproducible parameters, or a structured review and audit checklist for ML-KEM randomness and encapsulation coin security. At this stage, I care more about clear syntax, correctness, assumption mapping, parameter analysis, and honest verification boundaries than making premature security claims.

## Risks

- 可能显得保守，需要补一个更有长期研究想象力的方向。
- Module-SIS chameleon hash novelty 必须做完整 literature check。
- ML-KEM audit track 可能偏工程，需要确保 cryptographic framing。

## TODO_VERIFY

- Verify prior Module-SIS chameleon hash / commitment work.
- Verify ML-KEM coin paper's library behavior claims.
- Verify what can become a publishable contribution rather than only a report.

# Research Narrative Version 2: Balanced

## 中文段落

我希望把短期可交付的 lattice primitive / PQC implementation artifact 和长期 PhD 主线连接起来。短期上，我计划推进 Module-SIS chameleon hash / lattice commitment 的可复现参数化实现，或 ML-KEM / ML-DSA implementation security review，形成一个 2-4 周内可展示的研究 artifact。中期上，我希望把这些 primitive 和 implementation insights 扩展到 lattice-based privacy primitives，例如 linkable ring signatures、anonymous credentials、registration-based encryption 或 ZK-friendly PQ primitives。长期上，我希望研究 classical-grounded AI-assisted lattice cryptanalysis，把 AI 放在 coordinate selection、attack cost prediction、support recovery 或 BKZ / dual / hybrid attack pipeline 的辅助环节，而不是声称端到端破解真实参数。

## English paragraph

I would like to connect short-term lattice primitive and PQC implementation artifacts with a longer-term PhD research agenda. In the near term, I plan to develop a reproducible Module-SIS chameleon hash or lattice commitment prototype, or an ML-KEM / ML-DSA implementation-security review artifact that can be demonstrated within a few weeks. In the medium term, I hope to connect these ideas to lattice-based privacy primitives, such as linkable ring signatures, anonymous credentials, registration-based encryption, and ZK-friendly post-quantum primitives. In the long term, I am interested in classical-grounded AI-assisted lattice cryptanalysis, where learning is used for coordinate selection, attack cost prediction, support recovery, or BKZ / dual / hybrid attack assistance rather than unrealistic end-to-end key recovery.

## Risks

- 叙事跨度较大，需要用一个清晰 artifact 作为起点。
- AI4Lattice 和 primitive construction 之间要避免硬拼接。
- Privacy primitive line 必须保持 lattice/PQC anchor，不可泛化成 generic privacy。

## TODO_VERIFY

- Verify which privacy primitives are lattice-based.
- Verify whether Swin-guided coordinate selection has enough baseline novelty.
- Verify which short-term artifact advisor prefers.

# Research Narrative Version 3: Ambitious

## 中文段落

我长期希望构建一个 AI-assisted lattice cryptanalysis research program，但这个方向必须建立在 classical attacks 的可解释结构之上。近期 digest 中的 dual attack score distribution、sparse LWE hints、structure-aware lattice cryptanalysis 和 Module-LWE security papers 为我提供了一个可行起点：先研究 LWE / RLWE / MLWE attack pipeline 中可学习、可验证、可与传统 baseline 比较的环节，例如 coordinate ranking、support recovery、attack cost proxy、BKZ / dual / hybrid parameter suggestion。这个叙事的关键是保持密码学严谨性：AI 只作为辅助模块，不声称直接破解真实参数，并且所有实验都必须与 classical estimators、random baseline 和 heuristic baseline 比较。

## English paragraph

In the long term, I hope to develop a research program on AI-assisted lattice cryptanalysis, but this program must be grounded in interpretable classical attacks. Recent digest evidence on dual-attack score distributions, sparse LWE hints, structure-aware lattice cryptanalysis, and Module-LWE security provides a concrete starting point. My goal is to study learnable and verifiable components inside LWE / RLWE / MLWE attack pipelines, such as coordinate ranking, support recovery, attack cost proxies, and BKZ / dual / hybrid parameter suggestions. The key is to maintain cryptographic rigor: machine learning should act as an auxiliary module, not as an end-to-end real-parameter breaker, and all experiments should be compared against classical estimators, random baselines, and heuristic baselines.

## Risks

- 高风险，需要较强数学、实验和 baseline 设计能力。
- 容易被误解为 neural cryptanalysis hype。
- 短期产出不如 implementation checklist 或 primitive artifact 稳定。

## TODO_VERIFY

- Verify recent AI4Lattice related work.
- Verify toy experiment scope.
- Verify whether dual attack score features can be computed reliably.

# Recommended Primary Narrative

推荐使用 **Balanced narrative** 作为 27fall 主叙事。

原因：它既有短期可交付的 artifact，也有长期 PhD 研究想象力。Conservative narrative 太稳，但可能显得缺少长期 ambition；Ambitious narrative 有吸引力，但如果没有实验和 baseline，很容易被看成过度承诺。Balanced narrative 允许你对不同 PI 调整重点：面对 lattice primitive / signature advisor，强调 Module-SIS chameleon hash 和 privacy primitives；面对 PQC implementation advisor，强调 ML-KEM / ML-DSA audit；面对 AI security / cryptanalysis advisor，强调 classical-grounded AI4Lattice。

不要把 maturity 说过头。当前最诚实的说法是：你已经建立了一个 lattice/PQC literature intelligence and research planning workflow，并正在把它转化为 concrete paper notes、advisor-ready updates 和 bounded research artifacts。

# Short-Term Paper Track

## 1. A Module-SIS-Based Post-Quantum Chameleon Hash Primitive with Reproducible Parameterization and Implementation

* research question：Can a small Module-SIS chameleon hash / commitment primitive be specified, parameterized, and prototyped with clear correctness and security-goal boundaries?
* minimum viable version：formal syntax, correctness statement, assumption mapping, toy parameter table, Python/Sage prototype stub.
* required artifacts：definition, parameter config, correctness tests, benchmark plan, related-work table.
* expected contribution：a reproducible primitive artifact and honest proof sketch / security discussion.
* feasibility score：4/5
* novelty risk：4/5
* implementation risk：3/5
* advisor pitch：This is a bounded construction-side project that can become a short paper or workshop artifact if novelty and assumptions check out.
* why it helps PhD application：It demonstrates lattice primitive design, reproducibility, and parameter literacy.
* TODO_VERIFY：prior constructions, trapdoor/adaptation mechanism, proof route, parameter choices.

## 2. ML-KEM Randomness / Encapsulation Coin Security Review and Reproducible Check

* research question：Can the ML-KEM encapsulation coin secrecy paper be converted into a careful implementation audit checklist and, if safe, a minimal reproduction artifact?
* minimum viable version：paper reading note, library behavior matrix, threat model classification, TODO_VERIFY checklist.
* required artifacts：audit checklist, library/configuration table, optional reproduction plan.
* expected contribution：structured PQC implementation security review and reproducibility checklist.
* feasibility score：5/5
* novelty risk：3/5
* implementation risk：3/5
* advisor pitch：This is a practical standardized PQC security artifact that does not overclaim a break of ML-KEM.
* why it helps PhD application：It shows deployable PQC security awareness and reproducibility discipline.
* TODO_VERIFY：library behavior, FIPS configuration statements, safe reproduction scope.

## 3. Lattice-Based Commitment / Chameleon Hash / Linkable Ring Signature Connection Map

* research question：Can lattice commitments, chameleon hashes, blind signatures, and linkable ring signatures be organized into an assumption / syntax / security-goal map?
* minimum viable version：10-15 paper map, assumptions table, primitive interface comparison.
* required artifacts：bibliography, Obsidian concept map, assumption/security-goal matrix.
* expected contribution：related-work map supporting a later construction paper.
* feasibility score：5/5
* novelty risk：3/5
* implementation risk：2/5
* advisor pitch：This is a low-risk way to prepare the Module-SIS primitive direction.
* why it helps PhD application：It shows taste and preparation for lattice privacy primitives.
* TODO_VERIFY：which papers are lattice-based, whether connections are meaningful, whether map is too survey-like.

## 4. Dual-Attack Score Distribution as an AI4Lattice Attack-Cost Proxy

* research question：Can classical dual attack score distribution features become labels or targets for learning-assisted lattice attack triage?
* minimum viable version：paper note, feature list, toy benchmark protocol.
* required artifacts：toy LWE generator, baseline ranking scripts, feature extraction, evaluation table.
* expected contribution：classical-grounded AI4Lattice benchmark proposal.
* feasibility score：4/5
* novelty risk：3/5
* implementation risk：4/5
* advisor pitch：This is a cautious AI4Lattice idea that keeps AI inside the classical attack pipeline.
* why it helps PhD application：It connects ML skill with cryptographic rigor.
* TODO_VERIFY：feature computability, related work, baseline fairness.

## 5. Semantic Scholar Enriched PQC Literature Triage Benchmark

* research question：Can source health, ranking explanations, and optional Semantic Scholar enrichment be evaluated as a reproducible PQC literature triage benchmark?
* minimum viable version：labeled W23 fixture with must-read, watchlist, false positive categories.
* required artifacts：fixture JSON, labels, evaluation script, import report.
* expected contribution：research infrastructure, not a cryptographic novelty claim.
* feasibility score：5/5
* novelty risk：5/5
* implementation risk：2/5
* advisor pitch：This is secondary tooling; it supports research workflow but should not replace crypto work.
* why it helps PhD application：It demonstrates reproducible research engineering.
* TODO_VERIFY：whether this is worth presenting externally, no private data, stable labels.

# Long-Term PhD Agenda

## 1. AI-assisted lattice cryptanalysis

* core problem：Use learning to assist coordinate selection, support recovery, attack cost prediction, or BKZ / dual / hybrid parameter suggestion.
* why it matters：Lattice attacks are central to PQC security estimation; learning may help triage hard/easy instances or guide classical pipelines.
* related assumptions：LWE, RLWE, MLWE, sparse LWE, ML-KEM / Kyber.
* technical bottlenecks：avoid hype, build classical baselines, define toy-to-real limitations, evaluate false positives.
* training needed：lattice reduction, dual/primal/hybrid attacks, ML benchmarking, PyTorch, fplll/G6K/lattice-estimator basics.
* possible publications：toy benchmark paper, learned ranking / coordinate selection workshop paper, structure-aware cryptanalysis artifact.
* target advisor fit：AI security / cryptanalysis advisor or lattice cryptanalysis advisor.
* risk assessment：high upside, medium-high risk.

## 2. lattice/PQC privacy primitives

* core problem：Design or map lattice-based commitments, chameleon hashes, linkable ring signatures, anonymous credentials, registration-based encryption, or ZK-friendly PQ primitives.
* why it matters：Post-quantum privacy systems need primitives beyond KEM/signature deployment.
* related assumptions：SIS, Module-SIS, LWE/MLWE, lattice commitments.
* technical bottlenecks：security definitions, proof routes, parameter choices, prior work saturation.
* training needed：provable security, lattice commitments, signatures, zero-knowledge, credential systems.
* possible publications：Module-SIS chameleon hash artifact, primitive comparison map, small construction paper.
* target advisor fit：lattice primitive / signature / privacy advisor.
* risk assessment：medium risk, strong fit if novelty is verified.

## 3. Module-SIS / MLWE lightweight primitives

* core problem：Build small, reproducible lattice primitives with clear syntax, assumptions, parameterization, and implementation.
* why it matters：Bridges theory and artifact, suitable for master's-to-PhD transition.
* related assumptions：Module-SIS, SIS, MLWE, NTRU where appropriate.
* technical bottlenecks：novelty, proof correctness, parameter estimation.
* training needed：SIS/Module-SIS reductions, trapdoors, commitments, implementation testing.
* possible publications：workshop primitive artifact, reproducibility note, parameterized implementation.
* target advisor fit：lattice primitive / applied cryptography advisor.
* risk assessment：medium.

## 4. PQC implementation / security / reproducibility

* core problem：Audit standardized PQC implementations and convert findings into reproducible checklists and safe experiments.
* why it matters：Standardized PQC security depends on correct and robust implementations.
* related assumptions：ML-KEM / Kyber, ML-DSA / Dilithium, Falcon / FN-DSA, modular arithmetic, randomness.
* technical bottlenecks：safe reproduction, library complexity, avoiding overclaim.
* training needed：C/C++/Go library reading, test vectors, NTT arithmetic, constant-time checks, reproducibility.
* possible publications：ML-KEM randomness audit checklist, ML-DSA reduction placement checklist, implementation benchmark.
* target advisor fit：PQC implementation / systems security advisor.
* risk assessment：medium-low for artifact, medium for publication.

# Fit with Xingye Lu

This section is cautious. The repository does not contain verified biographical or publication data about Xingye Lu. I only use user-provided fit hints and general project alignment.

## 论文事实

- No verified paper, project, or advisor-profile data about Xingye Lu was inspected in this repository.
- User-provided known interest areas include lattice-based linkable ring signatures, hash-then-one-way signature line, programmable hash / IBE-adjacent lattice primitives, Module-SIS chameleon hash / commitment, and post-quantum privacy primitives.

## 背景补充

- Lattice-based signatures, linkable ring signatures, commitments, programmable hashes, IBE-adjacent primitives, and privacy-preserving authentication can share assumptions such as SIS / Module-SIS / LWE / MLWE and often require careful security definitions.
- Module-SIS chameleon hash / commitment may be relevant as a small primitive connected to broader post-quantum privacy systems.

## 我的推断

- A good Xingye Lu-facing narrative should emphasize lattice-based privacy primitives and signatures, not just AI4Lattice.
- The strongest bridge is: “I am developing a reproducible Module-SIS chameleon hash / commitment artifact as a small primitive, and I want to connect it to post-quantum privacy primitives such as linkable ring signatures or anonymous authentication.”
- AI-assisted lattice cryptanalysis can remain a secondary long-term interest, but the first pitch should probably foreground primitive construction, commitments, signatures, and reproducibility.

# Target PI Matching Matrix

| PI / group placeholder | best-fit narrative | strongest evidence | gap to fill | email pitch angle | risk |
| --- | --- | --- | --- | --- | --- |
| lattice primitive / signature advisor | Balanced or Conservative | Module-SIS chameleon hash seed; BRaccoon; commitment / ring signature map | verify prior work and proof route | small reproducible Module-SIS primitive with privacy/signature connections | novelty risk |
| PQC implementation advisor | Conservative | ML-KEM coin paper; ML-DSA reduction paper | safe reproduction and library expertise | standardized PQC implementation audit and reproducibility | may look too engineering-focused |
| AI security / cryptanalysis advisor | Ambitious | Unified Dual Attack; sparse LWE hints; CoNAN | build toy benchmark and baselines | classical-grounded AI-assisted lattice cryptanalysis | hype risk if not careful |
| privacy / FHE advisor | Balanced secondary | FHE / CKKS / BGV / privacy watchlist | ensure lattice/FHE anchor | lattice/PQC-grounded privacy primitive and secure aggregation map | too broad if not narrowed |

# Advisor Email Pitch Building Blocks

## 1. 2-sentence short pitch in English

I am a first-year master's student focusing on lattice-based cryptography and post-quantum cryptography, with current work moving toward reproducible Module-SIS primitives and PQC implementation security. My longer-term goal is to study deployable lattice-based privacy primitives and classical-grounded AI-assisted lattice cryptanalysis, while keeping experiments and security claims carefully verified.

## 2. 1-paragraph research pitch in English

My current research direction is centered on lattice-based cryptography and post-quantum cryptography. In the short term, I am working toward bounded and reproducible artifacts, such as a Module-SIS-based chameleon hash or commitment primitive with explicit parameterization, and a careful review or audit checklist for ML-KEM / ML-DSA implementation security. In the longer term, I hope to connect lattice primitives, post-quantum privacy mechanisms, and classical-grounded AI-assisted lattice cryptanalysis, where learning is used to assist coordinate selection, attack-cost prediction, or structured lattice attack triage rather than to make unrealistic end-to-end attack claims.

## 3. 1-paragraph technical pitch in English

Technically, I am interested in how assumptions such as LWE, RLWE, MLWE, SIS, and Module-SIS shape both primitive construction and practical security evaluation. Recent papers I am reading include work on dual-attack score distributions for LWE, Module-LWE security claims over 2-power cyclotomics, and ML-KEM encapsulation randomness in real implementations. These readings motivate two concrete tracks: a reproducible primitive track around Module-SIS chameleon hashes or lattice commitments, and an attack-assistance track where classical lattice attack signals are used as interpretable targets for learning-based ranking or triage.

## 4. 1-paragraph Chinese explanation for domestic advisor discussion

我现在的研究定位是格密码和后量子密码，短期希望先做一个可交付的小 artifact，例如 Module-SIS chameleon hash / commitment 的形式化定义、参数化实现和 correctness 测试，或者 ML-KEM / ML-DSA 实现安全的可复现 audit checklist。长期我希望把 lattice primitive、PQC implementation security 和 AI-assisted lattice cryptanalysis 连接起来，但 AI 部分会保持在 classical attack pipeline 的辅助环节，例如 coordinate ranking、support recovery 或 attack cost prediction，不会夸大成端到端破解真实参数。

# SoP Research Paragraph Drafts

These are draft materials, not final SoP text.

## Conservative SoP paragraph

My research interests lie in lattice-based cryptography and post-quantum cryptography, especially in the design, analysis, and reproducible implementation of lattice primitives. I am currently exploring bounded projects such as Module-SIS-based chameleon hashes or commitments with explicit parameterization, as well as structured reviews of ML-KEM and ML-DSA implementation security. Through these projects, I aim to develop the mathematical and engineering discipline needed to reason about assumptions, correctness, parameters, and deployment constraints without overstating unverified claims.

## Balanced SoP paragraph

I am interested in building a research path that connects lattice-based primitives, post-quantum implementation security, and classical-grounded AI-assisted lattice cryptanalysis. In the near term, I plan to work on reproducible artifacts such as a Module-SIS chameleon hash or commitment prototype and an ML-KEM / ML-DSA implementation-security checklist. In the longer term, I hope to study post-quantum privacy primitives and learning-assisted lattice attack pipelines, where machine learning supports interpretable components such as coordinate selection, support recovery, and attack-cost prediction rather than replacing classical cryptanalysis.

## Ambitious SoP paragraph

My long-term goal is to develop rigorous and interpretable AI-assisted methods for lattice cryptanalysis while maintaining a strong foundation in lattice-based cryptography and post-quantum primitives. Recent work on LWE dual attacks, sparse-secret recovery, and structure-aware lattice cryptanalysis suggests opportunities for learning models to assist classical attack pipelines through ranking, feature extraction, and parameter guidance. I hope to pursue this direction alongside lattice-based privacy primitives and PQC implementation security, with an emphasis on reproducible artifacts, careful baselines, and honest limitations.

# Evidence-to-Claim Mapping

| claim | supporting project artifact | strength | missing verification | safe wording |
| --- | --- | --- | --- | --- |
| User has a lattice/PQC research workflow | v0.3.3 project outputs; Phase 10A-E reports | strong | none for tooling existence | I have built and used a local lattice/PQC research triage workflow |
| Top recent technical theme is LWE / MLWE attack and security estimation | Phase 10A, 10B, W23 JSON | medium-high | original paper reading | Recent digest metadata highlights LWE / MLWE attack papers worth reading |
| ML-KEM implementation security is a promising short-term artifact | Phase 10B, 10C, ML-KEM coin note | medium | library behavior verification | I am exploring a careful review/checklist for ML-KEM implementation security |
| Module-SIS chameleon hash is a plausible short paper track | Phase 10D idea backlog and user profile | medium | prior work and proof route | I am considering a bounded Module-SIS primitive artifact |
| AI4Lattice is a long-term direction | Phase 10A-D; Unified Dual Attack note | medium | toy experiments and related work | I am interested in classical-grounded AI-assisted lattice cryptanalysis |
| Fit with Xingye Lu may involve lattice privacy primitives | user-provided interest areas | low-medium | verified PI publications | My interests may align with lattice-based signatures, commitments, and PQ privacy primitives |

# One-Month Execution Plan

## Week 1

- Read `On the Secrecy of the Encapsulation Coin in ML-KEM`.
- Read `Unified Dual Attack Analyses`.
- Decide between ML-KEM audit checklist and Module-SIS chameleon hash as primary short-term artifact.

## Week 2

- Implement or draft minimum artifact: ML-KEM audit matrix or Module-SIS primitive syntax.
- Build related-work map for selected track.
- Keep all technical claims marked TODO_VERIFY until source checked.

## Week 3

- If ML-KEM track: produce library/configuration table and safe reproduction plan.
- If Module-SIS track: produce toy parameter table and correctness test plan.
- If AI4Lattice backup: draft toy LWE feature extraction benchmark.

## Week 4

- Present draft to advisor.
- Revise paper plan based on feedback.
- Prepare 1-page PhD research narrative with conservative, balanced, and ambitious variants.

# What to Avoid

- "AI can break MLWE end-to-end."
- "I designed a new secure primitive" without proof and literature check.
- "This is novel" without related-work verification.
- Generic DP / FL / LLM claims without lattice/PQC anchor.
- Claiming paper results before reading original papers.
- Claiming experiments or implementation results that have not been run.
- Treating Semantic Scholar metadata or citation counts as research authority.
- Mixing MLWE attack claims into Module-SIS primitive security without assumption mapping.

# Final Recommendation

Primary short-term paper track：**ML-KEM randomness / encapsulation coin security review and reproducible checklist**。This is the fastest path to a concrete, advisor-discussable artifact with strong recent evidence.

Secondary backup track：**Module-SIS chameleon hash / commitment with reproducible parameterization**。This is the best construction-side route and likely most relevant to lattice primitive / signature / privacy advisors.

Long-term PhD track：**Balanced narrative**：lattice/PQC primitives and implementation security in the short term, expanding toward classical-grounded AI-assisted lattice cryptanalysis and post-quantum privacy primitives.

Immediate next 3 actions for tomorrow：

1. Read the ML-KEM coin paper's abstract, threat model, and library behavior table.
2. Draft a one-page ML-KEM implementation audit checklist.
3. Write a 200-word balanced research pitch and mark all TODO_VERIFY claims.
