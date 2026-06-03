# Phase 9Q: Source Query Coverage Audit

Date: 2026-06-03

This is a manual one-time audit report. It does not change source queries, negative keywords, taxonomy, ranking, section classification, fetchers, workflow behavior, generated daily / weekly artifacts, generated JSON files, or `papers.db`.

## Executive summary

- Phase 9P shows the strongest quality issues are false-positive classification and section over-assignment, not a simple missing-query problem.
- Phase 9S and Phase 9S.2 show that the missing IACR ePrint `2026/1117`, `On the Secrecy of the Encapsulation Coin in ML-KEM`, was a source ingestion / source health / latest enumeration issue. It is not a taxonomy problem: when it enters the parser/ranker path, the current ranker treats it as A-level, observed as A / 100 in diagnostics.
- `config/sources.yaml` is mostly lattice/PQC anchored. The broad-looking terms that deserve future review are not obviously wrong, but they need anchor guards: `isomorphism of lattices`, `registration-based encryption from lattices`, `Learning with Errors`, `Short Integer Solution`, `SVP`, `CVP`, `sieving`, `enumeration`, `G6K`, `fplll`, and `bootstrapping` are acceptable in lattice context but risky if a source search engine interprets them loosely.
- Negative keywords already cover many non-lattice false-positive families: image registration, graph isomorphism, generic federated learning, DP-SGD, generic LLM fine-tuning, generic secure aggregation, generic zero-knowledge, generic anonymous credential, generic commitment, generic functional encryption, and homomorphic-sounding non-cryptographic ML terms.
- The local environment was checked without printing secrets: `SEMANTIC_SCHOLAR_API_KEY` is currently not present / not non-empty. This is acceptable for Phase 9Q because Semantic Scholar must remain optional and gracefully degraded.
- The 2026-06-03 daily artifacts are present and show recovery compared with W23 starvation: `data/2026-06-03.json` has 20 records; IACR ePrint is green with 100 raw candidates and 18 final records, while Semantic Scholar remains red / `rate_limit` / retryable.
- Do not patch query or negative keyword config in Phase 9Q. The next minimal patch should be small and test-driven: section / ranking guard golden cases for `Falcon-X`, generic privacy-preserving ML, generic EKE, and generic signatures, while keeping source-health recovery separate.

## Inputs inspected

| Input | Status | Audit note |
| --- | --- | --- |
| `docs/reports/phase-9p-real-run-review.md` | inspected | Extracted false positives, suspicious A-level papers, weak section assignments, and source health concerns. |
| `docs/reports/phase-9s-iacr-source-health-diagnostics.md` | inspected | Confirmed IACR `2026/1115..1118` absence from local artifacts and source-health root cause for `2026/1117`. |
| `docs/reports/phase-9s2-source-latest-enumerator.md` | inspected | Confirmed IACR RSS/latest path, manual latest recovery flag, and cross-source latest capability table. |
| `config/sources.yaml` | inspected | Audited query terms, query groups, IACR RSS URL, enabled sources, and disabled HTML fallbacks. |
| `config/negative_keywords.yaml` | inspected | Audited hard / soft negative coverage and overblocking safeguards. |
| `config/taxonomy.yaml` | inspected | Confirmed broad lattice/PQC/implementation/AI4Lattice taxonomy families exist. |
| `src/lattice_digest/source_latest_audit.py` | inspected when present | Confirms deterministic source latest/query capability classification. |
| `src/lattice_digest/source_health_ledger.py` | inspected | Confirms source health ledger can expose `latest_feed_*` observability. |
| `src/lattice_digest/sources/` | inspected | Confirms configured source adapters: IACR, arXiv, DBLP, OpenAlex, Crossref, Semantic Scholar. |
| Daily artifacts `2026-05-31..2026-06-02` | inspected | All three daily JSONs had `records = 0`; source health was degraded. |
| Daily artifacts `2026-06-03` | inspected | `data/2026-06-03.json` exists with 20 records and 6 source-health entries; `digests/2026-06-03.md` exists. |
| Weekly artifacts `2026-W22`, `2026-W23` | inspected | W22 has usable but noisy records; W23 has no unique records and degraded source health. |
| `SEMANTIC_SCHOLAR_API_KEY` environment readiness | checked without printing value | Present: false; non-empty: false. No API call was made and no key value was logged. |

## Phase 9P issue mapping

| Issue | Likely root cause | Evidence | Future action |
| --- | --- | --- | --- |
| `Falcon-X: A Time Series Foundation Model...` entered PQC/Falcon and A-level tracking | section classifier ambiguity; ranking score inflation; source query acceptable noise | `Falcon-X` is a model name, not Falcon / FN-DSA lattice signature. No visible lattice/PQC anchor. | Add positive Falcon context gate: require signature, FN-DSA, lattice, PQC, side-channel/fault, implementation security, or NIST context. |
| `Practical Anonymous Two-Party Gradient Boosting Decision Tree` over-ranked and over-sectioned | ranking inflation; AI/privacy ambiguity; section classifier over-propagation | It may mention HE/LWE, but appears privacy-preserving ML / secure computation, not AI-assisted lattice cryptanalysis. | Keep only as background if lattice HE is central; exclude from AI-assisted lattice and PQC/Falcon/SIS sections unless explicit. |
| `Beyond 128 Bits: The Concrete Security of EKE` entered PQC/implementation sections | section classifier ambiguity; generic security terms | EKE over classical elliptic-curve context is not lattice/PQC. | Gate PQC implementation sections by explicit ML-KEM/ML-DSA/Falcon/lattice/PQC implementation target. |
| `Doubly Aggregatable Signatures` entered PQC/implementation sections | generic signature ambiguity | Signature alone is not lattice signature. | Require lattice/PQC construction or scheme anchor for PQC signature sections. |
| `Streamlined Symmetric PIR via Renyi Divergence` looks A-ish but over-sectioned | metadata / ranking nuance; section over-assignment | LWE/post-quantum privacy may be relevant, but SIS/NTRU/PQC Falcon sections are overbroad. | Review manually; route to LWE/privacy/FHE background if confirmed. |
| CKKS bootstrapping paper routed to `Other / Watchlist` | missing FHE section routing | It is genuine CKKS/FHE and should not be hidden in Other. | Add or restore FHE/CKKS/BFV/BGV/TFHE section routing in a future report-quality phase. |

## Phase 9S / 9S.2 source health implications

| Finding | Root cause class | Implication |
| --- | --- | --- |
| `2026/1117` absent from local artifacts but reachable in IACR RSS/latest | source health / network starvation plus failed attempt guard | Do not tune taxonomy or ranking for this miss. Use manual IACR recovery path. |
| IACR source path is `https://eprint.iacr.org/rss/rss.xml` | source-native latest feed exists | IACR is the highest-confidence latest-feed source and should remain source-native, not query-only. |
| `--include-latest-sources` + `--retry-failed-sources` provide manual recovery | manual latest recovery | This should remain manual and bounded; do not schedule it. |
| Source health ledger exposes `latest_feed_*` fields | observability improvement | Future audits can distinguish RSS/latest failure from ranking/filtering failure. |
| W23 empty daily/weekly outputs had red/yellow source health | source health / network starvation | Empty output does not prove no relevant papers existed. |

## Source query coverage table

| Source | Current configured mode | Query / feed coverage | Anchor quality | Audit judgment |
| --- | --- | --- | --- | --- |
| IACR ePrint | source-native RSS/latest | `https://eprint.iacr.org/rss/rss.xml` | Strong: source-native latest feed, no broad query terms | Keep. Missing `2026/1117` was ingestion/health, not query coverage. |
| arXiv | query groups | 37 configured query groups; includes lattice/PQC/FHE/AI4Lattice expanded topics | Mostly anchored. Some short technical terms are broad outside crypto: `SVP`, `CVP`, `sieving`, `enumeration`, `G6K`, `fplll`, `bootstrapping`. | Keep for now; future patch should add downstream guards, not remove queries immediately. |
| DBLP | query search | 11 broad venue/query strings | Anchored: all include lattice/PQC/FHE/BKZ/Module-SIS/ZK or related terms | Keep; sparse daily windows and venue metadata limits are bigger risks. |
| OpenAlex | query search | Lattice/PQC/FHE/implementation/privacy topics | Anchored | Keep; monitor rate limits and metadata quality. |
| Crossref | supplemental query search | Lattice/PQC/FHE/registration/isomorphism/SIS/PQC ABE | Anchored but supplemental-only | Keep; require strong relevance as currently configured. |
| Semantic Scholar | configured query source, optional metadata cross-check | Lattice/PQC/FHE/structured topics | Anchored | Existing code implements it as a source; also useful for optional enrichment. Do not require API key. |
| Disabled HTML fallbacks | disabled / unknown | Crypto/security/AI venue pages | Not active | Do not enable in this phase. |

## Source-native latest coverage table

| Source | Latest/RSS capable | Query-only | Enrichment-only | Unknown / unsupported | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| IACR ePrint | yes | no | no | no | RSS/latest feed is the concrete latest enumerator. |
| arXiv | not currently wired as latest | yes | no | no | API query groups are configured; no separate source-native latest feed path in current project. |
| DBLP | not currently wired as latest | yes | no | no | Venue/query metadata source; daily latest completeness is limited. |
| OpenAlex | not currently wired as latest | yes | no | no | Query metadata source; avoid paid-only sort behavior. |
| Crossref | not currently wired as latest | yes | no | no | Supplemental query source with strong relevance filters. |
| Semantic Scholar | not currently wired as latest | yes | optional cross-check only | no | Existing source can query; `SEMANTIC_SCHOLAR_API_KEY` is optional and must not be logged. |
| `crypto_venues`, `security_venues`, `ai_venues_low_priority` | no | no | no | disabled | HTML fallback only; intentionally disabled. |

## Missing query anchor candidates

These are topics that appear important to the user's research profile and should remain covered. Most are already present in `config/sources.yaml`; future work should verify successful source health before adding more query terms.

| Topic | Current coverage judgment | Future action |
| --- | --- | --- |
| LWE / RLWE / MLWE / Module-LWE | covered by arXiv, DBLP, OpenAlex, Crossref, Semantic Scholar | Keep; add golden false-positive tests before changing. |
| SIS / Module-SIS | covered, including `Module-SIS chameleon hash` and `SIS-based commitment` | Keep; consider more precise Module-SIS primitive tests later. |
| NTRU | covered in core query sets | Keep. |
| ML-KEM / Kyber | covered in query sets and IACR latest can recover `2026/1117` | Keep; source health is the main risk. |
| ML-DSA / Dilithium | covered | Keep; ensure implementation security section gates are precise. |
| Falcon / FN-DSA | covered but ambiguous | Keep query, but add positive context gate so `Falcon-X` model names do not count. |
| BKZ / LLL / lattice reduction / attacks | covered | Keep; ensure `dual`, `primal`, `hybrid` only count in lattice attack context. |
| sparse LWE | not visibly explicit in `sources.yaml` | Candidate for future query patch if source health stabilizes. |
| Module-SIS chameleon hash | covered in arXiv/DBLP/OpenAlex | Keep. |
| lattice-based commitment / ring signature / ZK / anonymous credential | covered in selected sources | Keep with lattice/PQC/SIS/LWE anchor requirement. |
| PQC attribute-based encryption | covered in arXiv/Crossref | Keep with PQC/lattice anchor requirement. |
| lattice-based registration-based encryption | covered | Keep; avoid generic registration queries. |
| lattice isomorphism problem | covered | Keep; avoid graph/code/model/image isomorphism. |
| RLWE/FHE secure aggregation / privacy-preserving ML / LLM fine-tuning | covered with anchored variants | Keep; do not use generic FL/DP/LLM terms as standalone queries. |

## Overbroad query candidates

The following are not necessarily wrong, but require careful downstream anchors:

| Query / topic | Why risky | Recommended future guard |
| --- | --- | --- |
| `Falcon` | Can match ML model/product names such as `Falcon-X`. | Require Falcon signature / FN-DSA / lattice / PQC context. |
| `bootstrapping` | Can be generic statistics/ML bootstrapping. | Require FHE/CKKS/BFV/BGV/TFHE or cryptographic context. |
| `sieving`, `enumeration`, `G6K`, `fplll` | Could be general algorithms, but usually useful in lattice context. | Require lattice reduction / SVP / CVP / BKZ context. |
| `SVP`, `CVP` | Short acronyms can be ambiguous. | Require lattice / cryptography / reduction context. |
| `isomorphism of lattices` | Better than generic isomorphism but still may be math-only. | Require cryptography/PQC/lattice cryptanalysis context for A/B. |
| `registration-based encryption from lattices` | Correctly anchored, but related generic registration terms are dangerous. | Never add standalone account/user/domain/image registration terms. |
| privacy-preserving ML / secure aggregation anchored queries | Useful but can pull application papers. | Require explicit LWE/RLWE/FHE/HE construction or proof for high priority. |

## Negative keyword gaps

`config/negative_keywords.yaml` already covers many obvious families. Future minimal patch candidates are:

| Gap candidate | Why it matters | Suggested treatment |
| --- | --- | --- |
| `Falcon-X` / foundation model names | Current false positive is scheme-name ambiguity rather than a generic negative family. | Prefer positive Falcon context gate over hard negative; optionally add exact `Falcon-X` as soft negative if repeated. |
| generic time-series foundation model | Helps avoid ML model papers with PQC scheme-name collisions. | Soft negative unless lattice/PQC context exists. |
| generic EKE / PAKE without PQC/lattice | Classical crypto papers can enter PQC sections. | Section guard rather than hard negative. |
| generic aggregate signatures | Signature alone is not lattice signature. | Section guard requiring lattice/PQC anchor. |
| generic privacy-preserving ML with HE mention | May be background, not AI4Lattice. | Demote unless LWE/RLWE/FHE construction is central. |

## Negative keyword overblocking risks

Do not add hard negative rules that suppress true positives containing:

- lattice
- LWE / RLWE / MLWE / Module-LWE
- SIS / Module-SIS / Ring-SIS
- NTRU
- PQC / post-quantum
- ML-KEM / Kyber
- ML-DSA / Dilithium
- Falcon / FN-DSA when used as lattice signature context
- FHE / CKKS / BFV / BGV / TFHE
- homomorphic encryption in the cryptographic sense
- lattice-based commitment, credential, ZK, FE, registration-based encryption

Soft negatives should continue to allow recovery when strong crypto context exists.

## Source health observations

| Artifact | Source health | Coverage implication |
| --- | --- | --- |
| `data/2026-05-31.json` | arXiv yellow, Crossref yellow, DBLP red, IACR red, OpenAlex yellow, Semantic Scholar red | Low-confidence empty report. |
| `data/2026-06-01.json` | arXiv yellow, Crossref yellow, DBLP yellow, IACR red, OpenAlex yellow, Semantic Scholar red | Low-confidence empty report. |
| `data/2026-06-02.json` | all inspected sources red | Very low-confidence empty 7d report. |
| `data/2026-06-03.json` | arXiv yellow timeout; Crossref green; DBLP yellow warning; IACR ePrint green; OpenAlex yellow; Semantic Scholar red rate-limit | Higher-confidence daily report than prior W23 artifacts; IACR latest/source recovery appears effective for this run, but Semantic Scholar is still degraded. |
| `data/weekly/2026-W22.json` | source health available; 2 green, 15 yellow, 7 red | Usable for false-positive review, but still not perfect coverage. |
| `data/weekly/2026-W23.json` | source health available; 8 red, 4 yellow | Empty weekly output is not reliable evidence of no relevant papers. |

Distinction:

- `2026/1117` missing: source-native latest / source health / retry guard issue.
- `Falcon-X`, GBDT, EKE, generic signatures: classification / section / ranking issue.
- Empty W23: source health / network starvation issue.

## Semantic Scholar key readiness note

The environment was checked in secret-safe mode only:

- `SEMANTIC_SCHOLAR_API_KEY` present: false
- `SEMANTIC_SCHOLAR_API_KEY` non-empty: false

No key value was printed, stored, logged, or committed. No live Semantic Scholar API smoke test was required for this audit. The absence of the key should not block local validation, CI, daily digest generation, or source query coverage review.

Operational implication: Semantic Scholar should be treated as optional and retryable. When it is red / `rate_limit`, as seen in `data/2026-06-03.json`, the digest must continue with other sources and source health should make the degradation visible.

## Semantic Scholar enrichment-only recommendation

Semantic Scholar is currently configured as a source and may also be useful as optional metadata cross-check. Do not require a real API key for this phase or for tests. If an API key is used in future operations, it must come only from the environment variable name `SEMANTIC_SCHOLAR_API_KEY`.

Do not print, store, log, or commit any Semantic Scholar API key.

Future Semantic Scholar work should be scoped as metadata enrichment / cross-source confirmation unless the project deliberately promotes it to a stronger primary source. Recommended constraints:

- Keep `SEMANTIC_SCHOLAR_API_KEY` optional.
- Use it only from the process environment.
- Never serialize key material into reports, source health ledger, `.env.example`, generated artifacts, or logs.
- Treat HTTP 429 / rate-limit as degraded and retryable, not as a main-flow failure.
- Prefer IACR source-native latest/RSS and arXiv query groups for first-pass discovery; use Semantic Scholar for title/author/URL/abstract/semantic metadata cross-check when available.

## Recommended minimal future patch

Recommended next implementation phase: **Phase 9Q.1 Minimal Query / Negative Keyword Patch**, but keep it narrow and mostly test-driven.

Minimal patch plan:

1. Add golden-case tests for:
   - `Falcon-X` must not enter PQC Falcon or A-level lattice tracking.
   - `Practical Anonymous Two-Party Gradient Boosting Decision Tree` must not enter AI-assisted lattice cryptanalysis, SIS/NTRU, or PQC Falcon without explicit lattice cryptanalysis evidence.
   - Generic EKE must not enter PQC/implementation sections without lattice/PQC anchors.
   - Generic aggregate signatures must not enter PQC/implementation sections without lattice/PQC anchors.
2. Add positive context gates:
   - Falcon requires Falcon/FN-DSA signature or lattice/PQC implementation/security context.
   - AI4Lattice requires AI/ML plus lattice/LWE/RLWE/MLWE/BKZ/cryptanalysis attack-interface context.
   - SIS/NTRU/commitment/chameleon section requires explicit SIS/NTRU/commitment/chameleon/trapdoor primitive evidence.
3. Add FHE/CKKS routing polish later in Phase 9R rather than mixing it into query patch.
4. Keep IACR source recovery in Phase 9S.3 if runtime evidence still shows failures.
5. Keep Semantic Scholar metadata work for Phase 9U.

## Changes explicitly not recommended

Do not do these based on this audit alone:

- Do not remove the Phase 9O expanded anchored queries yet.
- Do not add broad hard negatives for HE, FHE, zero-knowledge, commitment, functional encryption, or privacy-preserving ML.
- Do not lower all A-level scores globally because some true A-level papers are present.
- Do not treat W23 empty output as evidence that no papers existed.
- Do not convert manual IACR recovery into scheduled automation.
- Do not add or require Semantic Scholar API-key integration in this phase.
- Do not modify generated daily/weekly artifacts or `papers.db`.

## Manual reviewer checklist

- [ ] Confirm `Falcon-X` is an ML time-series model and unrelated to Falcon / FN-DSA.
- [ ] Inspect `Practical Anonymous Two-Party GBDT` for actual LWE/HE depth before deciding B/C/D.
- [ ] Check whether `Streamlined SPIR via Renyi Divergence` has central LWE construction/proof or is background privacy.
- [ ] Verify extraordinary claims in `Module Lattice Security (Part IV)` before using it in advisor discussion.
- [ ] Confirm `Sparse Hermite Interpolation Method for Discrete-CKKS Functional Bootstrapping` should route to FHE/CKKS rather than Other.
- [ ] Treat 2026-W23 as source-starved and low-confidence.
- [ ] Use IACR manual latest recovery for `2026/1117` style misses; do not tune taxonomy for them.
- [ ] Before changing query/negative config, add deterministic golden tests.

## Decision recommendation

Recommended ordering:

1. **Phase 9Q.1 Minimal Query / Negative Keyword Patch**: add golden tests and small positive context gates for the known false positives. Avoid broad query deletion.
2. **Phase 9R Research Report Quality Polish**: improve section routing, especially FHE/CKKS and General Privacy/background separation.
3. **Phase 9S.3 Source Runtime Debug**: if IACR/arXiv/Semantic Scholar/DBLP source health still red/yellow in real runs, debug runtime behavior separately from ranking.
4. **Phase 9U Semantic Scholar Metadata Enrichment**: optional only; use `SEMANTIC_SCHOLAR_API_KEY` by environment variable name, never as a stored or logged value.
5. **v0.3.3 Maintenance Release Prep**: after 9Q.1 and 9R/9S.3 selected fixes pass clean validation.

Primary recommendation: start with Phase 9Q.1, but make it a guard/test patch rather than a broad query rewrite.

## What was intentionally not changed

This audit did not change:

- `config/sources.yaml`
- `config/negative_keywords.yaml`
- taxonomy config
- ranking code
- section classifier code
- fetcher/source code
- workflow code
- generated daily/weekly digest Markdown
- generated JSON files
- `papers.db`
- `.env`
- any API key or secret
- scheduled automation
- Windows Task Scheduler
- cron
- background services
- startup tasks
