# Phase 9Q Source Query Coverage Audit

本报告基于 Phase 9P real-run false positive review、当前查询配置、负面关键词配置以及 2026-05-31 到 2026-06-02 的 daily / weekly artifacts。此阶段只做审计和未来 patch plan，不修改 query、negative keyword、taxonomy、ranking、section classifier、fetcher、workflow、生成日报、生成 JSON 或 `papers.db`。

## Executive summary

- 当前 `config/sources.yaml` 的 Phase 9O query expansion 基本符合 lattice/PQC anchored 原则。未发现 `federated learning`、`LLM fine-tuning`、`DP-SGD`、`registration encryption`、`zero-knowledge proof`、`anonymous credential`、`commitment scheme`、`functional encryption` 这类泛词作为独立 query 出现。
- 主要覆盖缺口不是 query 不足，而是 source health / network starvation：`2026-06-01` 和 `2026-06-02` daily artifacts 均为空，且多个 source 为 red/yellow。
- Phase 9P 中最明确的误报，如 `Falcon-X` 和 `Practical Anonymous Two-Party Gradient Boosting Decision Tree`，根因更像 section classifier ambiguity 与 ranking score inflation，而不是 source query 太宽。
- `config/negative_keywords.yaml` 已覆盖 registration / image registration / graph isomorphism / generic FL / DP-SGD / LLM fine-tuning / generic ZK / credential / commitment / FE 等主要误报族。
- 不建议在 Phase 9Q 直接改 query 或 negative keywords。最小后续 patch 应优先做 section classifier golden-case guard；source health 方向应进入单独 Phase 9S 诊断。

## Inputs inspected

| Input | Status | Audit note |
|---|---|---|
| `docs/reports/phase-9p-real-run-review.md` | inspected | 提取 false positives、missing coverage、A-level audit、section audit、source health issues |
| `config/sources.yaml` | inspected | 查询扩展已包含 Phase 9O anchored topics |
| `config/negative_keywords.yaml` | inspected | 已覆盖主要泛 registration / isomorphism / FL / DP / ZK / credential / commitment false positives |
| `config/taxonomy.yaml` | inspected | 包含 LWE/SIS/NTRU/FHE/PQC/implementation/AI4Lattice 等 taxonomy families |
| `data/2026-05-31.json` | inspected | records=0；source health mixed, no final records |
| `data/2026-06-01.json` | inspected | records=0；source health mixed, no final records |
| `data/2026-06-02.json` | inspected | records=0；all source records red, no final records |
| `data/weekly/2026-W22.json` | inspected | unique_records=12；A=9, B=1, C=2 |
| `data/weekly/2026-W23.json` | inspected | unique_records=0；source health degraded |
| Markdown daily/weekly digests | inspected | 用于确认日报/周报呈现与 JSON 一致 |

## Phase 9P issue mapping

| Issue from Phase 9P | Likely root cause | Evidence | Future action |
|---|---|---|---|
| `Falcon-X` enters PQC Falcon and A-level | section classifier ambiguity; ranking score inflation; metadata/title ambiguity | Title contains `Falcon-X` but abstract is time-series foundation model; no lattice/PQC/FN-DSA/signature anchor | Add Falcon scheme context gate; golden test before logic change |
| `Practical Anonymous Two-Party GBDT` enters AI-assisted lattice, SIS/NTRU, PQC, A=100 | section classifier ambiguity; ranking score inflation; expected acceptable noise at source query level | It contains HE/LWE-like signals, but is privacy-preserving ML, not lattice cryptanalysis | Demote/reroute via section gates; avoid hard negative unless no HE/LWE anchor |
| EKE over P-256 enters PQC / Implementation section | section classifier ambiguity; missing lattice/PQC section anchor | C=45 is acceptable as generic crypto, but section assignment is misleading | Keep generic C/Other; require lattice/PQC scheme context for PQC section |
| Doubly Aggregatable Signatures enters PQC / Implementation section | section classifier ambiguity; generic signature term | No visible lattice/PQC anchor | Keep C/Other unless lattice/PQC construction exists |
| CKKS bootstrapping lands in Other / Watchlist | missing section route | Genuine CKKS/FHE paper hidden under Other | Add FHE/CKKS section routing in future section patch |
| W23 has no records | source health / network starvation | W23 source health red/yellow only; daily 2026-06-01/02 records=0 | Treat as source health diagnostics problem, not taxonomy evidence |

## Source query coverage table

| Source | Query count observed | Anchored coverage judgment | Potential overbroad candidates | Notes |
|---|---:|---|---|---|
| `iacr_eprint` | 0 explicit query terms | N/A | none | RSS/OAI source; not query-expanded in config |
| `arxiv` | 104 total query strings including query groups | Good | `Learning with Errors`, `Short Integer Solution`, `LLL`, `SVP`, `CVP`, `sieving`, `enumeration`, `G6K`, `fplll`, `bootstrapping` look unanchored by string regex but are lattice/FHE hard-scope terms | arXiv has broadest coverage and highest query pressure; query groups = 37 in source health |
| `dblp` | 11 | Good | none | Anchored phrases only; DBLP source health degraded in real run |
| `openalex` | 17 | Good | none | Anchored phrases only |
| `crossref` | 17 | Good | none | Anchored phrases only; supplemental source with strong relevance filter |
| `semantic_scholar` | 17 | Good | none | Anchored phrases only; 429/rate-limit was visible |

## Missing query anchor candidates

| Anchor candidate | Current status | Recommendation |
|---|---|---|
| lattice-based registration-based encryption | present | Keep |
| LWE-based registration-based encryption | present | Keep |
| SIS-based registration-based encryption | present | Keep |
| LWE / RLWE / MLWE | present | Keep |
| SIS / Short Integer Solution | present | Keep |
| Module-SIS standalone | partially covered through `Module-SIS chameleon hash`; no standalone `Module-SIS` query in all source query strings | Consider adding standalone `Module-SIS` query only if future real-run evidence shows missed Module-SIS papers; postpone |
| NTRU | present | Keep |
| lattice-based commitment | present | Keep |
| SIS-based commitment | present | Keep |
| Module-SIS chameleon hash | present | Keep |
| lattice-based zero-knowledge proof | present | Keep |
| lattice-based anonymous credential | present | Keep |
| PQC attribute-based encryption | present | Keep |
| lattice-based privacy-preserving training | present | Keep |
| RLWE-based secure aggregation federated learning | present | Keep |
| FHE private LLM fine-tuning RLWE | present | Keep |
| lattice isomorphism problem | present | Keep |

## Overbroad query candidates

No generic standalone privacy/registration/isomorphism/ZK/credential/commitment/FE queries were found.

The following arXiv query strings may look broad in a naive regex audit but are acceptable because they are core lattice/FHE terms:

- `Learning with Errors`
- `Short Integer Solution`
- `LLL`
- `SVP`
- `CVP`
- `sieving`
- `enumeration`
- `G6K`
- `fplll`
- `bootstrapping`

Risk note: `Falcon` remains semantically ambiguous. The current problem is not source query breadth alone; it is downstream interpretation of the token `Falcon` without scheme context.

## Negative keyword gaps

Current negative keyword coverage is strong for the requested generic false-positive families:

| False-positive family | Covered? | Config location |
|---|---:|---|
| account / user / domain registration | yes | hard negative |
| image / medical image / point cloud registration | yes | hard negative |
| graph / code / model / neural / chemical isomorphism | yes | hard negative |
| generic federated learning | yes | soft negative |
| generic DP-SGD | yes | soft negative |
| generic LLM fine-tuning | yes | soft negative |
| generic secure aggregation | yes | soft negative |
| generic zero-knowledge | yes | soft negative |
| generic anonymous credential | yes | soft negative |
| generic commitment scheme | yes | soft negative |
| generic functional encryption | yes | soft negative |
| homomorphic-sounding ML terms | partial | soft negative covers homomorphic feature matching / representation learning / embedding |

Potential future additions, only after more evidence:

- `Falcon-X` as a soft negative or explicit false-positive alias. This is not recommended as the first fix; a Falcon positive-context gate is safer.
- Generic `foundation model` should not be a hard negative because AI4Lattice may legitimately mention foundation models if paired with LWE/BKZ/cryptanalysis.

## Negative keyword overblocking risks

| Risk | Why it matters | Current judgment |
|---|---|---|
| `zero-knowledge` soft negative | Lattice ZK papers are in-scope when lattice/PQC anchored | Acceptable as soft negative; should not hard-filter anchored true positives |
| `anonymous credential` soft negative | Lattice-based anonymous credentials are in-scope | Acceptable as soft negative; requires section classifier to preserve lattice/PQC anchored papers |
| `federated learning` soft negative | RLWE/FHE secure aggregation for FL is in-scope | Acceptable as soft negative; do not hard-filter |
| `commitment scheme` soft negative | SIS/Module-SIS commitments are in-scope | Acceptable as soft negative; do not hard-filter |
| `functional encryption` soft negative | LWE/lattice FE is in-scope | Acceptable as soft negative; do not hard-filter |

Current config includes lattice/PQC/HE/FHE/LWE/RLWE/MLWE/SIS/Module-SIS/NTRU anchors in `crypto_context_required_if_only_lattice`, so the major overblocking risk is manageable if downstream logic respects strong context.

## Source health observations

| Artifact | Source health | Coverage interpretation |
|---|---|---|
| `data/2026-05-31.json` | arXiv yellow, Crossref yellow, DBLP red, IACR red, OpenAlex yellow, Semantic Scholar red | Low confidence. Empty daily records may reflect date filtering plus source failures. |
| `data/2026-06-01.json` | arXiv yellow, Crossref yellow, DBLP yellow, IACR red, OpenAlex yellow, Semantic Scholar red | Low confidence. Crossref had date-filtered candidates but no final records. |
| `data/2026-06-02.json` | all sources red | Very low confidence. Treat as source-starved run, not evidence of no papers. |
| `data/weekly/2026-W22.json` | source health available; 2 green, 15 yellow, 7 red | Usable for false-positive review, but still not perfect coverage. |
| `data/weekly/2026-W23.json` | 8 red, 4 yellow; no unique records | Not reliable for false-negative conclusions. |

Distinction:

- `Falcon-X`, GBDT, EKE, and generic signatures are not source health issues; they are downstream classification issues.
- Empty W23 and empty 2026-06-02 daily are source health / network starvation issues; do not patch taxonomy based on these alone.

## Recommended minimal future patch

Recommended next step: Phase 9Q.1 should be a small section-classifier / golden-test patch, not a query rewrite.

Minimal patch scope:

1. Add real-run golden tests from Phase 9P:
   - `Falcon-X` must not enter PQC Falcon or A-level lattice tracking.
   - `Practical Anonymous Two-Party Gradient Boosting Decision Tree` must not enter AI-assisted lattice cryptanalysis, SIS/NTRU, or PQC Falcon.
   - `Beyond 128 Bits: The Concrete Security of EKE` must not enter PQC/Implementation sections without lattice/PQC anchors.
   - `Doubly Aggregatable Signatures` must not enter PQC/Implementation sections without lattice/PQC anchors.
   - `Sparse Hermite Interpolation Method for Discrete-CKKS Functional Bootstrapping` should route to FHE/CKKS, not only Other/Watchlist.
2. Add positive-context gates:
   - Falcon counts only with Falcon signature / FN-DSA / lattice signature / NIST PQC / implementation security / side-channel/fault context.
   - AI-assisted lattice cryptanalysis requires AI/ML plus lattice cryptanalysis/LWE/BKZ/attack-interface evidence.
   - SIS/NTRU/Commitment section requires explicit SIS/NTRU/commitment/chameleon/trapdoor primitive evidence.
   - PQC Standards section requires explicit PQC scheme or standardization/deployment context, not generic signature or unrelated model names.
3. Preserve ranking thresholds and query/negative configs initially.

## Changes explicitly not recommended

Do not do the following based on current evidence:

- Do not remove Phase 9O anchored queries.
- Do not add broad hard negatives for `federated learning`, `LLM fine-tuning`, `zero-knowledge`, `anonymous credential`, `commitment`, or `functional encryption`.
- Do not change A/B/C/D thresholds from this review alone.
- Do not rewrite fetchers.
- Do not treat W23 empty result as a clean negative signal.
- Do not add scheduled automation, cron, Task Scheduler, watcher, background service, startup task, or automatic run.
- Do not modify generated daily/weekly artifacts as part of the audit.

## Manual reviewer checklist

- [ ] Confirm `Falcon-X` is ordinary ML and should be excluded from Falcon/FN-DSA tracking.
- [ ] Confirm whether GBDT paper has actual LWE/HE construction depth; if yes, route to General Privacy / FHE background rather than AI4Lattice.
- [ ] Verify whether CKKS functional bootstrapping should become a dedicated FHE high-priority route.
- [ ] Review W23 after a healthier source run before declaring missing coverage.
- [ ] Keep query expansion unchanged until at least one more successful real run.
- [ ] Prefer golden tests before classifier/ranking adjustments.

## Decision

Recommended path:

1. Proceed to Phase 9Q.1 patch for section-classifier golden cases and context gates.
2. In parallel or next, run Phase 9S source health diagnostics for arXiv/Semantic Scholar/DBLP/Crossref network starvation.
3. Defer Phase 9R report polish until section over-assignment is reduced, otherwise polished reports may still surface misleading A-level candidates.

Decision summary: Phase 9Q.1 patch first, Phase 9S diagnostics second, Phase 9R report polish after classifier correction.
