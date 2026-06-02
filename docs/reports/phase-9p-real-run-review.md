# Phase 9P Real-run False Positive Review

本报告基于 2026-05-31、2026-06-01、2026-06-02 daily artifacts 以及 2026-W22、2026-W23 weekly artifacts 的只读审计。未抓取新论文，未重生成日报或周报，未修改 `data/`、`digests/`、`papers.db` 或业务逻辑。

## Executive summary

- 三份 daily JSON：`2026-05-31`、`2026-06-01`、`2026-06-02` 的 `records` 均为 0。
- `2026-W23` weekly JSON 覆盖 `2026-06-01..2026-06-02`，`unique_records = 0`。
- `2026-W22` weekly JSON 覆盖 `2026-05-25..2026-05-31`，`unique_records = 12`，其中 `A = 9`、`B = 1`、`C = 2`。
- 最明显 false positive：
  - `Falcon-X: A Time Series Foundation Model for Heterogeneous Multivariate Modeling`：因模型名 `Falcon-X` 被误归入 PQC Falcon。
  - `Practical Anonymous Two-Party Gradient Boosting Decision Tree`：虽出现 homomorphic encryption / Learning With Errors，但它更像 privacy-preserving ML 应用论文，不应进入 AI-assisted lattice cryptanalysis、PQC Falcon、SIS/NTRU 等多个核心 section，更不应 A=100。
- 最明显 section over-assignment：
  - 多篇 LWE / FHE / generic crypto paper 被同时放入 `SIS / NTRU / Commitments / Chameleon Hash`、`PQC Standards / ML-KEM / ML-DSA / Falcon`、`Implementation / Side-channel / Systems`。
- Source health 是当前最大覆盖风险：
  - 2026-06-02 daily 所有 source 均为 red，且 final_count 为 0。
  - 2026-W23 source health 为 8 red / 4 yellow，`unique_records = 0`，不能据此判断 6 月 1-2 日确实没有相关论文。

## Input files inspected

| File | Status | Notes |
|---|---:|---|
| `data/2026-05-31.json` | inspected | `records = 0`; local authoritative backfill |
| `data/2026-06-01.json` | inspected | `records = 0`; local authoritative backfill |
| `data/2026-06-02.json` | inspected | `records = 0`; local authoritative daily |
| `data/weekly/2026-W22.json` | inspected | `unique_records = 12`; main review input |
| `data/weekly/2026-W23.json` | inspected | `unique_records = 0`; source health degraded |
| `digests/2026-05-31.md` | inspected | daily Markdown cross-check |
| `digests/2026-06-01.md` | inspected | daily Markdown cross-check |
| `digests/2026-06-02.md` | inspected | daily Markdown cross-check |
| `digests/weekly/2026-W22.md` | inspected | weekly section cross-check |
| `digests/weekly/2026-W23.md` | inspected | weekly empty-week cross-check |

## Overall quality judgment

当前 real-run artifacts 对“核心格密码攻击 / LWE / MLWE / FHE / ML-DSA 实现安全”有一定召回，但 section assignment 和 A-level 强排序仍存在明显误报。

质量判断：

- `2026-W22` 可用于人工 review，但不能无人工筛选地作为阅读队列或导师汇报输入。
- `2026-W23` 和 2026-06-01/02 daily 的空结果主要受 source health 影响，不能视为“真实无论文”。
- Phase 9O 的 query expansion 提高了 anchored recall，但也暴露出 source API rate-limit / timeout 压力。
- 当前最需要后续小步修复的是 section classifier 和 false-positive guard，不是抓取源重构。

## Likely false positives table

| Title | Source | Date / seen date | Label / score | Assigned section | Why suspicious | Likely cause | Recommended action | Timing |
|---|---|---:|---:|---|---|---|---|---|
| Falcon-X: A Time Series Foundation Model for Heterogeneous Multivariate Modeling | arXiv | 2026-05-26 | A / 100 | PQC Standards / ML-KEM / ML-DSA / Falcon; Implementation / Side-channel / Systems; High-Priority; Idea/Paper Plan candidates | `Falcon-X` 是 time-series foundation model 名称，不是 Falcon / FN-DSA lattice signature。摘要无 PQC、signature、FN-DSA、lattice、cryptanalysis 锚点。 | section classifier / ranking keyword ambiguity around `Falcon` | Add Falcon scheme context gate: Falcon only counts as PQC when paired with signature, FN-DSA, lattice, NIST PQC, implementation security, side-channel/fault, or cryptographic context. | Immediate |
| Practical Anonymous Two-Party Gradient Boosting Decision Tree | arXiv | 2026-05-26 | A / 100 | LWE/RLWE/MLWE; SIS/NTRU; PQC Standards; AI-assisted Lattice Cryptanalysis; Implementation; General Privacy | It appears to be privacy-preserving ML / secure computation. It may use LWE-style HE, but it is not AI-assisted lattice cryptanalysis and not SIS/NTRU/PQC Falcon. A=100 is too high for user's lattice cryptanalysis / Module-SIS profile. | ranking overweights `Learning With Errors` / `homomorphic encryption`; section classifier over-propagates broad privacy/ML terms | Keep as C/B background only if HE/LWE grounding is real; remove from AI-assisted lattice and PQC/Falcon/SIS sections unless explicit lattice-cryptanalysis or lattice primitive evidence exists. | Immediate |
| Beyond 128 Bits: The Concrete Security of EKE | IACR ePrint | 2026-05-25 | C / 45 | PQC Standards / ML-KEM / ML-DSA / Falcon; Implementation / Side-channel / Systems | EKE over NIST P-256 is classical elliptic-curve PAKE security, not lattice/PQC. C label is acceptable as generic crypto background only, but PQC/implementation sections are misleading. | section classifier uses generic `concrete security` / `cryptographic` without lattice/PQC anchor | Keep C/Other or General Cryptography only; remove PQC/Implementation assignment unless explicit lattice/PQC scheme appears. | Immediate |
| Doubly Aggregatable Signatures | IACR ePrint | 2026-05-23 | C / 40 | PQC Standards / ML-KEM / ML-DSA / Falcon; Implementation / Side-channel / Systems | Generic signature primitive; no visible lattice/PQC anchor. | section classifier overuses generic `signature` / `certificate` | Keep as C/Other only unless source text contains lattice/PQC construction. | Immediate |
| Streamlined Symmetric Private Information Retrieval via Rényi Divergence | IACR ePrint | 2026-05-25 | A / 85 | LWE/RLWE/MLWE; SIS/NTRU; PQC; Implementation; General Privacy | It appears LWE/post-quantum grounded, but it is PIR/privacy protocol, not necessarily user's top A-level lattice attack or Module-SIS line. SIS/NTRU and PQC Falcon sections look overbroad. | ranking treats LWE/post-quantum privacy as high priority; section classifier over-assigns adjacent sections | Consider B/high-background or A only if construction/security proof is directly LWE lattice primitive; remove SIS/NTRU/PQC Falcon sections unless explicit. | Postpone until more real-run evidence |
| Sparse Hermite Interpolation Method for Discrete-CKKS Functional Bootstrapping | IACR ePrint | 2026-05-22 | A / 100 | Other / Watchlist; High-Priority | It is genuine CKKS/FHE and relevant, but section assignment to `Other / Watchlist` is not research-useful. A=100 may be high but plausible for FHE; should not be hidden in Other. | missing FHE/CKKS section routing | Add/restore FHE/CKKS/BFV/BGV/TFHE section or route to Lattice + FHE / Implementation as appropriate. | Postpone; useful but not false positive |

## Likely false negatives or missing coverage table

No concrete title-level false negatives are visible in the inspected artifacts because the daily records for 2026-05-31, 2026-06-01, and 2026-06-02 are empty. However, source health shows substantial missing-coverage risk.

| Date / week | Evidence | Likely missing area | Why this may be false negative coverage | Likely cause | Recommended action | Timing |
|---|---|---|---|---|---|---|
| 2026-06-02 daily | all sources red; `total_records = 0`; `since_window = 7d` | any LWE/RLWE/MLWE/SIS/Module-SIS/FHE/PQC papers in the 7-day window | A 7-day authoritative run with all sources red cannot prove no papers existed. | source health / network / rate limits | Treat empty report as degraded, rerun manually later or use source-specific retry; do not tune ranking based on this day alone. | Immediate operational note |
| 2026-W23 | `unique_records = 0`; source health 8 red / 4 yellow | lattice-based RBE, FHE secure aggregation, lattice advanced primitives, LWE/MLWE attacks | The week has no records only because loaded daily files have no records and source health is poor. | source health / external API degradation | Mark W23 as low-confidence coverage; use manual backfill after network/API recovery. | Immediate operational note |
| Phase 9O expanded topics | arXiv query groups show many 429/timeout/URLError warnings | lattice-based registration-based encryption, lattice isomorphism, Module-SIS chameleon hash, lattice ZK/credential | Expanded queries exist but may fail under arXiv/Semantic Scholar/DBLP rate limits. | source health, query pressure | Do not remove expanded queries yet; collect more successful runs before reducing. | Postpone logic changes |

## A-level paper audit

| Title | Label / score | A-level judgment for user profile | Research relevance | Recommended action |
|---|---:|---|---|---|
| Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE | A / 100 | True A | Direct LWE dual attack, Kyber/Dilithium context, attack score distribution. Strongly aligned with lattice cryptanalysis and possible AI-assisted attack-interface work. | Keep A; read immediately. |
| CoNAN: A Structure-Aware Framework for Lattice Cryptanalysis | A / 100 | True A | Structured lattice cryptanalysis, security estimation, parameter selection, NTRU/LWE context. Strongly aligned. | Keep A; read immediately. |
| Improved Dual Attack and Trapdoor Sampling via Quantum Rejection Sampling | A / 100 | True A, with verification note | Dual attack / trapdoor sampling / Gaussian sampling / Kyber context. Relevant, but quantum acceleration claims need careful verification. | Keep A; read with skeptical proof/assumption check. |
| Module Lattice Security (Part IV): Probabilistic Polynomial Quantum Attack on Module-LWE over 2-Power Cyclotomics | A / 100 | True A, high-risk claim | Direct Module-LWE / ML-KEM / module lattice attack claim. Highly relevant but extraordinary; should be verified carefully. | Keep A; read immediately but mark TODO_VERIFY. |
| When Removing Reductions Goes Wrong: Auditing Reduction Placement in Production ML-DSA Implementations | A / 100 | True A for implementation security | ML-DSA production implementation, NTT, reduction placement, PQC implementation audit. Relevant to ML-DSA implementation security. | Keep A; read this week. |
| Sparse Hermite Interpolation Method for Discrete-CKKS Functional Bootstrapping | A / 100 | Mostly valid A/B | Real CKKS/FHE bootstrapping paper. Relevant but lower than LWE attack / Module-SIS lines unless FHE becomes active track. | Keep high priority but route to FHE section; consider B/A depending queue pressure. |
| Streamlined Symmetric Private Information Retrieval via Rényi Divergence | A / 85 | Borderline A; likely B | LWE/post-quantum privacy protocol, useful background but less central than attack/primitive lines. | Demote to B or high background unless lattice proof/construction is central. |
| Practical Anonymous Two-Party Gradient Boosting Decision Tree | A / 100 | Not true A | Privacy-preserving ML / secure computation; HE/LWE mention may justify background, not AI4Lattice or PQC core. | Demote to B/C; remove from AI4Lattice/PQC/SIS sections. |
| Falcon-X: A Time Series Foundation Model for Heterogeneous Multivariate Modeling | A / 100 | False A | Ordinary ML time-series foundation model; `Falcon-X` is not Falcon signature. | Demote/filter to D for lattice/PQC tracking. |

## Section assignment audit

| Section | Quality judgment | Evidence | Recommended action |
|---|---|---|---|
| LWE / RLWE / MLWE | Mixed | Correctly includes Unified Dual Attack, CoNAN, Module-LWE attack; incorrectly includes Practical Anonymous GBDT if only application-level LWE/HE. | Require direct LWE/RLWE/MLWE assumption, attack, proof, or lattice HE construction; avoid routing generic privacy ML solely on weak LWE mention. |
| SIS / NTRU / Commitments / Chameleon Hash | Weak / overbroad | Contains many LWE/PQC/privacy papers without SIS/NTRU/commitment/chameleon evidence. | Gate this section by SIS, Module-SIS, Ring-SIS, NTRU, commitment, chameleon hash, trapdoor commitment, or explicit lattice primitive. |
| PQC Standards / ML-KEM / ML-DSA / Falcon | Weak / overbroad | Includes Falcon-X, GBDT, EKE, generic signatures. | Add scheme-context gate for Falcon/Kyber/Dilithium/ML-KEM/ML-DSA/FN-DSA; generic `signature` and model name `Falcon-X` must not count. |
| BKZ / LLL / G6K / Lattice Reduction / Attacks | Good | Includes LWE dual attack, quantum rejection sampling attack, CoNAN. | Keep; ensure attack terms require lattice/LWE/BKZ context. |
| AI-assisted Lattice Cryptanalysis | Poor for W22 | Only GBDT appears; it is not AI-assisted lattice cryptanalysis. | Require AI/ML plus lattice cryptanalysis/LWE/BKZ/attack-interface terms. Privacy-preserving ML should not enter. |
| Implementation / Side-channel / Systems | Mixed | ML-DSA implementation audit is correct; Falcon-X, GBDT, EKE, generic signatures are not useful here. | Require PQC/lattice implementation target, side-channel/fault, constant-time, NTT, ML-KEM/ML-DSA/Falcon context. |
| Lattice Advanced Primitives | Good but sparse | Ciphertext-updatable ABE from lattices appears correctly. | Keep; consider adding Module-SIS/ZK/credential/chameleon specific subrouting later. |
| General Cryptography / Privacy | Reasonable | GBDT and SPIR belong here if retained. | Keep as background section; do not let this imply A-level lattice relevance. |
| Other / Watchlist | Mixed | CKKS bootstrapping appears here despite FHE relevance. | Add FHE/CKKS/BFV/BGV/TFHE route; avoid hiding true FHE papers in Other. |

## Query expansion observations

- Phase 9O anchored queries are visible in source health warnings, including lattice-based secure aggregation, FHE private LLM fine-tuning RLWE, lattice-based registration-based encryption, lattice isomorphism, Module-SIS chameleon hash, lattice-based commitment, lattice-based zero-knowledge proof, and PQC ABE.
- The query expansion itself appears correctly anchored; no evidence in these artifacts suggests generic standalone FL/LLM/ZK/credential queries were used.
- However, query expansion increases API pressure. arXiv shows 37 query groups on 2026-06-02, all failing under URLError/warnings in that run. This is a source health/load issue, not a ranking issue.
- Do not remove anchored queries immediately; the current real-run evidence is too network-degraded to know which new queries are productive.

## Negative keyword observations

- The artifacts contain no obvious generic registration/image registration/graph isomorphism false positives in final weekly W22 records.
- The `Falcon-X` false positive is not covered by generic negative keywords because it is a scheme-name ambiguity, not a standard negative keyword. It likely needs positive context gating for Falcon rather than a hard negative term.
- `Practical Anonymous Two-Party GBDT` is not an obvious hard negative: it may contain HE/LWE material. It needs ranking/section demotion rather than hard exclusion.
- Generic EKE and generic aggregate signatures should be controlled by section gates and lattice/PQC anchor checks, not necessarily by hard negative keywords.

## Ranking observations

- Too many papers reached A/100. Some are true A-level, but Falcon-X and GBDT show that keyword presence can still overwhelm context.
- The most urgent issue is not threshold adjustment; it is disambiguation and section gating:
  - Falcon must mean Falcon/FN-DSA lattice signature, not any model/product named Falcon.
  - AI-assisted lattice cryptanalysis must require cryptanalysis/attack-interface evidence, not any ML/privacy paper.
  - SIS/NTRU/commitment section must require SIS/NTRU/commitment evidence.
- Suggested next ranking action: add diagnostic tests using these real titles as golden cases before changing weights.

## Source health observations

| Artifact | Source health summary | Impact |
|---|---|---|
| `data/2026-05-31.json` | arXiv yellow, Crossref yellow, DBLP red, IACR red, OpenAlex yellow, Semantic Scholar red | Low confidence; no final records despite Crossref date-filter hits. |
| `data/2026-06-01.json` | arXiv yellow, Crossref yellow, DBLP yellow, IACR red, OpenAlex yellow, Semantic Scholar red | Low confidence; no final records. |
| `data/2026-06-02.json` | all inspected sources red; no final records | Very low confidence; empty report should be treated as degraded. |
| `data/weekly/2026-W22.json` | status counts: green 2, yellow 15, red 7 | Mixed confidence; enough records for review, but source health still noisy. |
| `data/weekly/2026-W23.json` | status counts: red 8, yellow 4; no unique records | Empty weekly output is not reliable evidence of no papers. |

## Recommended next actions

Immediate:

1. Add golden-case tests for:
   - `Falcon-X` must not enter PQC Falcon or A-level lattice tracking.
   - `Practical Anonymous Two-Party Gradient Boosting Decision Tree` must not enter AI-assisted lattice cryptanalysis, SIS/NTRU, or PQC Falcon; at most General Cryptography / Privacy unless strong lattice construction evidence is present.
   - `Beyond 128 Bits: The Concrete Security of EKE` must not enter PQC/implementation sections without lattice/PQC anchors.
   - `Doubly Aggregatable Signatures` must not enter PQC/implementation sections without lattice/PQC anchors.
2. Strengthen section gates before changing scoring weights.
3. Add FHE/CKKS-specific section routing so real CKKS bootstrapping papers do not land in `Other / Watchlist`.

Postpone until more real-run evidence:

1. Reducing Phase 9O query expansion breadth.
2. Hard-negative filtering for privacy-preserving ML papers that mention HE/LWE.
3. Global A/B/C/D threshold changes.
4. Major source fetcher changes.

## Do-not-change list

Do not change in response to this single review pack:

- fetcher behavior
- ranking thresholds
- A/B/C/D label semantics
- source health red/yellow/green semantics
- query expansion semantics
- negative keyword semantics
- workflow execution semantics
- reading queue semantics
- Obsidian scaffold behavior
- Zotero export behavior
- release hygiene
- daily or weekly generated artifacts
- `papers.db`

## Manual reviewer checklist

- [ ] Manually open `Falcon-X` and confirm it is unrelated to Falcon/FN-DSA.
- [ ] Manually inspect `Practical Anonymous Two-Party GBDT` for actual LWE/HE construction depth.
- [ ] Verify whether `Streamlined SPIR via Rényi Divergence` uses LWE centrally enough for A-level.
- [ ] Verify extraordinary claims in `Module Lattice Security (Part IV)` before using it in advisor discussion.
- [ ] Check whether `Sparse Hermite Interpolation Method for Discrete-CKKS Functional Bootstrapping` should be tracked as FHE high priority.
- [ ] Treat W23 empty output as low-confidence because source health is red/yellow only.
- [ ] Do not tune thresholds from one degraded run.
- [ ] Convert the suspicious title list into deterministic golden tests before modifying classifier logic.
