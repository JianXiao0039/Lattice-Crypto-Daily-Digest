---
name: lattice-paper-digest
description: Daily workflow for collecting, filtering, classifying, deduplicating, ranking, and summarizing papers strongly related to lattice-based cryptography, post-quantum lattice schemes, lattice cryptanalysis, lattice implementation security, and AI-assisted lattice cryptanalysis.
---

# Lattice Paper Digest Skill

## 0. Purpose

This skill is used for the project:

`D:\CodexProjects\lattice-crypto-daily-digest`

The project implements a daily paper-monitoring system for lattice-based cryptography.

Use this skill whenever the user asks for any of the following:

- daily lattice cryptography paper digest
- Codex automation for lattice cryptography papers
- IACR ePrint monitoring
- arXiv cs.CR / math.NT / cs.IT lattice paper tracking
- PQC / ML-KEM / ML-DSA / Falcon paper monitoring
- LWE / RLWE / MLWE / SIS / NTRU paper tracking
- BKZ / LLL / G6K / fplll / lattice reduction paper tracking
- lattice-based FHE paper tracking
- lattice-based ZKP / IBE / ABE / MPC paper tracking
- lattice implementation / side-channel / fault attack monitoring
- AI-assisted lattice cryptanalysis monitoring
- daily Chinese research brief for lattice cryptography

The skill must produce a Chinese daily digest of newly published or newly updated papers that are strongly related to lattice-based cryptography.

The skill must favor precision over noisy recall.
Do not include papers merely because they contain the word “lattice”.

---

# 1. Core Mission

The mission is to build and maintain a reliable daily research radar for lattice-based cryptography.

The system must:

1. Collect candidate papers from trusted sources.
2. Normalize paper metadata.
3. Remove duplicates.
4. Filter non-cryptographic “lattice” false positives.
5. Classify each paper into A/B/C/D relevance levels.
6. Assign taxonomy tags.
7. Generate Chinese summaries.
8. Generate a Markdown daily digest.
9. Generate a JSON archive.
10. Update the local SQLite database.
11. Optionally commit changes to Git.

The final digest must help a lattice-cryptography graduate student quickly decide:

- Which papers must be read immediately;
- Which papers are worth tracking;
- Which papers are only background inspiration;
- Which false positives were filtered;
- How each paper relates to LWE/RLWE/MLWE, BKZ, ML-KEM, ML-DSA, Falcon, FHE, implementation security, or AI-assisted cryptanalysis.

---

# 2. Hard Scope: What Counts as Relevant

Always treat the following topics as in scope.

## 2.1 Lattice assumptions and hardness problems

The following are core lattice-cryptography topics:

- LWE
- Learning With Errors
- RLWE
- Ring-LWE
- Ring Learning With Errors
- MLWE
- Module-LWE
- Module Learning With Errors
- Polynomial-LWE
- PLWE
- TLWE
- LWR
- Learning With Rounding
- SIS
- Short Integer Solution
- MSIS
- Module-SIS
- ISIS
- Inhomogeneous SIS
- Ring-SIS
- NTRU
- NTRU lattice
- NTRU problem
- NTRU assumption
- NTRU module
- ideal lattice
- module lattice
- standard lattice
- Euclidean lattice
- algebraic lattice
- non-commutative algebraic lattice
- q-ary lattice
- lattice trapdoor
- gadget decomposition
- discrete Gaussian
- Gaussian sampling
- rejection sampling
- error distribution
- secret distribution
- sparse secret LWE
- binary secret LWE
- ternary secret LWE

## 2.2 Geometric lattice problems

The following are relevant when they appear in a cryptographic or cryptanalytic context:

- SVP
- Shortest Vector Problem
- approximate SVP
- uSVP
- Unique SVP
- SIVP
- GapSVP
- CVP
- Closest Vector Problem
- approximate CVP
- GapCVP
- BDD
- Bounded Distance Decoding
- Minimax-CVP
- lattice decoding
- nearest plane
- embedding technique
- decoding attack

If SVP/CVP/BDD appears only in pure geometry, physics, or unrelated mathematics without cryptographic context, classify cautiously as C or D.

## 2.3 Lattice reduction and cryptanalysis

The following are strongly relevant:

- LLL
- Lenstra-Lenstra-Lovasz
- Lenstra-Lenstra-Lovász
- BKZ
- BKZ 2.0
- Block Korkine-Zolotarev
- HKZ
- Hermite-Korkine-Zolotarev
- slide reduction
- progressive BKZ
- non-deterministic BKZ
- self-dual BKZ
- Voronoi reduction
- Seysen reduction
- lattice sieving
- enumeration
- lattice enumeration
- extreme pruning
- pruned enumeration
- Schnorr-Euchner enumeration
- tuple sieve
- nearest-neighbor sieve
- Kannan algorithm
- Kannan’s algorithm
- Babai nearest plane
- primal attack
- dual attack
- hybrid attack
- lattice reduction attack
- lattice enumeration attack
- lattice sieving attack
- meet-in-the-middle attack
- guess-and-determine attack
- drop-and-solve attack
- distinguishing attack
- root Hermite factor
- Hermite factor
- GSA
- geometric series assumption
- learning-augmented GSA
- learned pruning
- neural lattice reduction
- G6K
- fplll
- fpylll
- lattice estimator
- LWE estimator
- BKZ simulator
- attack cost estimation
- concrete security estimation

## 2.4 Standard lattice-based PQC schemes

Always treat the following as highly relevant:

- Kyber
- CRYSTALS-Kyber
- ML-KEM
- Module-Lattice-Based Key-Encapsulation Mechanism
- Dilithium
- CRYSTALS-Dilithium
- ML-DSA
- Module-Lattice-Based Digital Signature Algorithm
- Falcon
- FN-DSA
- FALCON
- NTRU signatures
- GPV signatures
- FrodoKEM
- Frodo
- Saber
- LightSaber
- FireSaber
- NewHope
- qTESLA
- NTRUEncrypt
- NTRU-HRSS
- NTRU Prime
- Hawk
- HAETAE
- Raccoon
- lattice-based KEM
- lattice-based signature
- lattice-based encryption
- lattice-based key exchange
- lattice-based post-quantum cryptography

Important distinction:

- SQIsign, SIDH, SIKE, CSIDH, and other isogeny-only schemes are not lattice-based.
- Include them only as C-class background if they directly compare against lattice-based schemes.
- Do not classify isogeny-only papers as A or B unless lattice schemes are central to the paper.

## 2.5 Lattice-based advanced protocols

The following are in scope:

- lattice-based zero-knowledge proof
- lattice zero-knowledge
- lattice ZKP
- lattice-based zero-knowledge argument
- lattice ZKA
- Stern-like protocols from lattices
- Lyubashevsky-style proofs
- lattice commitment
- lattice-based commitment
- lattice-based IBE
- identity-based encryption from lattices
- lattice-based ABE
- attribute-based encryption from lattices
- lattice-based PRE
- proxy re-encryption from lattices
- lattice-based functional encryption
- lattice FE
- lattice-based blind signature
- lattice blind signature
- lattice-based ring signature
- lattice ring signature
- lattice-based group signature
- lattice group signature
- lattice-based signcryption
- lattice signcryption
- lattice-based proxy signature
- lattice proxy signature
- lattice-based broadcast encryption
- lattice broadcast encryption
- lattice-based MPC
- lattice-based multiparty computation
- lattice-based secure multi-party computation
- lattice-based oblivious transfer
- lattice OT
- lattice-based threshold cryptography
- lattice threshold cryptography
- lattice secret sharing
- lattice-based secret sharing

## 2.6 FHE and lattice-based homomorphic encryption

The following are in scope:

- fully homomorphic encryption
- FHE
- lattice-based FHE
- homomorphic encryption from lattices
- CKKS
- BFV
- BGV
- TFHE
- GSW
- Gentry-Sahai-Waters
- HEAAN
- leveled FHE
- somewhat homomorphic encryption
- partially homomorphic encryption
- RLWE-based homomorphic encryption
- bootstrapping
- lattice bootstrapping
- homomorphic evaluation
- key switching
- modulus switching
- relinearization
- ciphertext packing
- approximate homomorphic encryption

## 2.7 Implementation, hardware, and software optimization

The following are in scope when related to lattice schemes:

- NTT
- number theoretic transform
- polynomial multiplication
- polynomial ring arithmetic
- modular multiplication
- modular reduction
- Montgomery reduction
- Barrett reduction
- rejection sampling
- Gaussian sampling
- discrete Gaussian sampling
- centered binomial sampling
- CDT sampler
- Knuth-Yao sampler
- uniform sampling
- lattice trapdoor generation
- constant-time implementation
- optimized implementation
- software implementation
- vectorization
- AVX
- AVX2
- AVX512
- NEON
- SIMD
- Cortex-M
- Cortex-A
- RISC-V
- FPGA
- ASIC
- chip implementation
- RTL
- Verilog
- VHDL
- HLS
- High-Level Synthesis
- hardware/software co-design
- instruction set extension
- low-power implementation
- high-speed implementation
- embedded implementation

## 2.8 Physical security of lattice schemes

The following are in scope when applied to lattice-based schemes:

- side-channel attack
- lattice SCA
- power analysis
- simple power analysis
- differential power analysis
- correlation power analysis
- timing attack
- cache attack
- electromagnetic attack
- EM attack
- template attack
- profiled attack
- deep-learning side-channel attack
- neural network side-channel attack
- CNN side-channel attack
- Transformer side-channel attack
- fault attack
- fault injection
- laser fault injection
- voltage glitch
- clock glitch
- fault analysis
- masking
- masked implementation
- threshold masking
- threshold implementation
- hiding
- shuffling
- leakage resilience
- leakage-resistant implementation
- side-channel countermeasure
- fault countermeasure

## 2.9 Standardization and deployment

The following are in scope when lattice schemes are involved:

- NIST PQC
- post-quantum standardization
- post-quantum standard
- FIPS 203
- FIPS 204
- FIPS 205
- ML-KEM standard
- ML-DSA standard
- FN-DSA standard
- PQC migration
- quantum-safe migration
- quantum-resistant cryptography
- post-quantum TLS
- TLS hybrid key exchange
- IETF
- CFRG
- LAMPS
- X.509 certificates with PQC
- OpenSSL PQC
- BoringSSL PQC
- Open Quantum Safe
- liboqs
- open-source PQC implementation
- decryption failure analysis
- failure probability
- parameter selection
- parameter optimization
- noise analysis
- reconciliation
- modulus switching

## 2.10 AI-assisted lattice cryptanalysis

AI/ML papers are in scope only if they explicitly connect to cryptography, cryptanalysis, lattice problems, modular arithmetic in cryptographic settings, or LWE-family problems.

Relevant topics include:

- machine learning LWE
- ML attack on LWE
- neural cryptanalysis
- Transformer for LWE
- Swin Transformer for LWE/RLWE/MLWE
- neural attack on LWE
- AI-assisted lattice cryptanalysis
- learning-augmented cryptanalysis
- learning-guided BKZ
- learned pruning
- neural lattice reduction
- self-supervised lattice reduction
- learning-based lattice reduction
- coordinate selection for hybrid attacks
- modular arithmetic learning
- algorithmic reasoning for cryptanalysis
- discrete structure learning for cryptographic problems
- SALSA-style LWE attacks
- sparse LWE learning attacks
- LWE benchmark datasets
- custom data distributions for modular arithmetic
- stepwise regression for LWE
- data repetition for LWE attacks

AI-only papers without cryptographic or lattice relevance should not be classified above C.

---

# 3. Strict Exclusion Policy

The system must aggressively filter false positives.

The word “lattice” is extremely ambiguous. It appears in physics, material science, chemistry, biology, and unrelated mathematics. Do not include those papers unless they explicitly discuss cryptography or cryptanalysis.

## 3.1 Hard negative topics

Always exclude papers about:

- crystal lattice
- crystalline lattice
- lattice QCD
- lattice quantum chromodynamics
- lattice Boltzmann
- lattice Boltzmann method
- spin lattice
- optical lattice
- solid-state lattice
- solid state lattice
- materials lattice
- material lattice
- lattice oxygen
- lattice thermal conductivity
- thermal conductivity lattice
- phonon lattice
- lattice vibration
- lattice dynamics
- lattice gauge theory
- lattice field theory
- lattice Hamiltonian
- Ising lattice
- Hubbard lattice
- Bravais lattice
- reciprocal lattice
- lattice constant
- lattice parameter
- lattice strain
- lattice defect
- lattice mismatch
- lattice relaxation
- lattice symmetry
- lattice structure
- lattice site
- lattice gas
- lattice fluid
- protein lattice
- biological lattice
- molecular lattice
- supramolecular lattice
- polymer lattice
- enzyme lattice
- cell lattice
- lattice surgery
- surface code lattice
- topological lattice model
- quantum error correction lattice
- lattice path combinatorics without cryptographic relevance
- distributive lattice
- Boolean lattice
- lattice-ordered group
- lattice polytope without cryptographic relevance

## 3.2 Required context rule

A paper must not be included merely because it contains:

- lattice
- lattice model
- lattice structure
- lattice method
- lattice simulation
- lattice network
- lattice graph

To be included, the paper must also contain at least one cryptographic context signal, such as:

- cryptography
- cryptographic
- cryptanalysis
- cryptanalytic
- post-quantum
- quantum-resistant
- quantum-safe
- LWE
- RLWE
- MLWE
- SIS
- NTRU
- BKZ
- LLL
- lattice reduction in cryptographic context
- KEM
- key encapsulation
- signature
- digital signature
- encryption
- FHE
- homomorphic encryption
- zero-knowledge
- ZKP
- side-channel
- fault attack
- masking
- Kyber
- ML-KEM
- Dilithium
- ML-DSA
- Falcon
- FN-DSA
- FrodoKEM
- Saber
- Hawk
- HAETAE
- Raccoon

---

# 4. Relevance Classification

Use four labels: A, B, C, D.

## 4.1 A-class: Core lattice cryptography

A-class papers must be included in the daily digest.

Classify a paper as A if it directly studies one or more of the following:

- LWE/RLWE/MLWE/LWR/SIS/NTRU
- SVP/CVP/BDD/GapSVP/GapCVP in cryptographic context
- lattice reduction algorithms used for cryptanalysis
- BKZ/LLL/sieving/enumeration/pruning for lattice attacks
- primal/dual/hybrid attacks
- G6K/fplll/lattice estimator/security estimation
- Kyber/ML-KEM
- Dilithium/ML-DSA
- Falcon/FN-DSA
- FrodoKEM/Saber/Hawk/HAETAE/Raccoon
- lattice-based KEM/signature/encryption/key exchange
- lattice-based ZKP/IBE/ABE/PRE/FE/MPC/OT
- lattice-based FHE/CKKS/BFV/BGV/TFHE
- implementation of lattice schemes
- side-channel or fault attacks on lattice schemes
- countermeasures for lattice implementations
- AI-assisted attacks on LWE or lattice schemes

## 4.2 B-class: Strongly related PQC/security/deployment paper

B-class papers should be included.

Classify as B if the paper is not purely about lattice theory but clearly involves lattice-based schemes in:

- PQC deployment
- protocol migration
- TLS hybrid key exchange
- IETF/CFRG/LAMPS discussions
- NIST PQC standardization
- implementation engineering
- performance evaluation
- system integration
- security evaluation
- comparison among PQC schemes where lattice-based schemes are central

A generic PQC paper without specific lattice schemes is at most B, usually C.

## 4.3 C-class: Potential background or indirect inspiration

C-class papers should be included briefly.

Classify as C if the paper may inspire lattice-cryptography research but is not itself a core lattice-cryptography paper.

Examples:

- AI for modular arithmetic without explicit LWE
- algorithmic reasoning for discrete structures
- generic optimization methods that may inspire lattice attack heuristics
- generic cryptanalysis methodology
- broad PQC surveys with useful lattice sections
- non-lattice PQC papers that compare directly with lattice schemes
- security engineering papers that may apply to PQC implementation

## 4.4 D-class: Irrelevant or false positive

D-class papers must be excluded from the digest.

Classify as D if:

- The paper is about physics/materials/biology lattice concepts.
- The paper only uses “lattice” outside cryptography.
- The paper has no reliable URL or source.
- The paper has no cryptographic relevance.
- The paper is an isogeny-only, code-only, or hash-only PQC paper with no comparison to lattice schemes.
- The paper appears to be hallucinated or has unverifiable metadata.

---

# 5. Relevance Scoring Policy

Use a conservative scoring system.

The exact implementation may be in `src/lattice_digest/ranker.py`, but the policy must follow this logic.

## 5.1 Positive scoring

Add score when evidence appears in title, abstract, venue, or metadata.

High-impact title matches:

- Title contains LWE/RLWE/MLWE/SIS/NTRU/Kyber/ML-KEM/Dilithium/ML-DSA/Falcon/BKZ/FHE:
  +45

High-impact abstract matches:

- Abstract contains core lattice terms:
  +30

Cryptographic context:

- Paper contains cryptography, cryptanalysis, post-quantum, KEM, signature, encryption, FHE, ZKP, side-channel, or similar:
  +15

Implementation/security context:

- Paper contains NTT, sampler, constant-time, AVX, NEON, FPGA, ASIC, side-channel, fault attack, masking:
  +15

AI-assisted lattice cryptanalysis:

- Paper contains AI/ML terms and explicit lattice/LWE/cryptanalysis context:
  +15

High-value source:

- Source is IACR ePrint, CRYPTO, EUROCRYPT, ASIACRYPT, PKC, TCC, CHES/TCHES, ToSC, Journal of Cryptology, PQCrypto:
  +20

Taxonomy match:

- Each matched taxonomy tag should add controlled bonus points.
- Do not allow taxonomy matches alone to overcome hard negative filters.

## 5.2 Negative scoring

Subtract score or filter when false-positive evidence appears.

Hard negative without crypto context:

- Immediate D.

Only “lattice” appears:

- Immediate D or at most C.

AI without crypto context:

- At most C.

Generic PQC without lattice scheme:

- At most B, often C.

Isogeny-only without lattice comparison:

- D or C.

Physics/materials lattice terms:

- Strong penalty.
- If no cryptographic context, immediate D.

## 5.3 Final label thresholds

Use:

- 80-100: A, 必读
- 60-79: B, 值得跟踪
- 40-59: C, 可选关注
- 0-39: D, 过滤

---

# 6. Required Data Sources

Prefer stable APIs and structured feeds.

## 6.1 Primary sources

Use these first:

1. IACR ePrint RSS / Atom / OAI-PMH
2. arXiv API / RSS / OAI-PMH
3. DBLP publication / venue API
4. OpenAlex works API
5. Crossref REST API
6. Semantic Scholar Graph API

## 6.2 Cryptography venues

Monitor official pages or metadata sources for:

- CRYPTO
- EUROCRYPT
- ASIACRYPT
- PKC
- TCC
- CHES
- TCHES
- FSE
- ToSC
- Journal of Cryptology
- Communications in Cryptology
- Real World Crypto
- PQCrypto

## 6.3 Security venues

Monitor only when lattice/PQC relevance is explicit:

- IEEE Symposium on Security and Privacy
- ACM CCS
- USENIX Security
- NDSS
- AsiaCCS
- ESORICS
- RAID
- ACSAC
- PETS / PoPETs

## 6.4 Theory and algorithms venues

Monitor only when lattice reduction, SVP/CVP/BDD, or cryptographic relevance appears:

- STOC
- FOCS
- SODA
- ITCS
- ICALP
- ESA
- APPROX/RANDOM

## 6.5 AI venues

AI venues are low priority.

Include only if the paper explicitly connects to cryptography, modular arithmetic, LWE, lattice cryptanalysis, algorithmic reasoning for crypto, or discrete structures relevant to attacks.

Potential sources:

- NeurIPS
- ICML
- ICLR
- AAAI
- IJCAI
- KDD
- AISTATS

Do not include ordinary AI papers merely because they mention “lattice”, “graph”, “transformer”, or “optimization”.

---

# 7. Metadata Requirements

Each paper must be represented using a normalized record.

Required fields:

- title
- normalized_title
- chinese_title
- authors
- abstract
- source
- source_url
- pdf_url
- paper_id
- arxiv_id
- eprint_id
- doi
- venue
- publication_date
- update_date
- categories
- taxonomy_tags
- keywords_matched
- negative_keywords_matched
- relevance_score
- relevance_label
- reason
- reading_priority

If a field is unknown, mark it as unknown.
Do not invent missing metadata.

---

# 8. Deduplication Policy

Deduplicate aggressively.

Use this priority:

1. DOI
2. arXiv ID
3. IACR ePrint ID
4. official URL
5. normalized title
6. normalized title + first author + year
7. fuzzy title similarity

If the same paper appears in multiple sources:

- Prefer official publication metadata when available.
- Keep all source URLs if useful.
- Prefer IACR/ePrint/arXiv PDF links when available.
- Do not push the same paper twice in the same digest.

Examples of duplicates:

- arXiv preprint and DBLP conference version
- IACR ePrint and conference accepted paper
- OpenAlex/Crossref/Semantic Scholar metadata for the same DOI

---

# 9. Reliability and Anti-Hallucination Rules

Never invent:

- paper title
- author list
- abstract
- venue
- publication year
- DOI
- arXiv ID
- IACR ePrint ID
- URL
- PDF link
- result counts
- citation counts
- source names

If metadata cannot be verified, mark it as unknown.

A paper without a trustworthy URL or source must not enter A/B/C digest sections.

If the daily run fails, do not silently fail. Generate an error report.

Error report path:

`digests/YYYY-MM-DD-error.md`

The error report must include:

- failed source
- command that failed
- error summary
- suspected cause
- suggested fix
- whether output files were partially generated

---

# 10. Output Requirements

The daily run must create or update:

- `digests/YYYY-MM-DD.md`
- `data/YYYY-MM-DD.json`
- `papers.db`

The Markdown digest must be written in Chinese.

## 10.1 Required Markdown structure

The digest must contain:

1. 今日结论
2. A 类：今日必读格密码论文
3. B 类：值得跟踪论文
4. C 类：可选关注 / 背景启发
5. D 类过滤说明
6. 今日统计
7. 明日跟踪建议
8. 今日一句话总结

## 10.2 Each A/B paper must include

For every A/B-class paper, include:

- 中文标题翻译
- 原标题
- 作者
- 来源
- 会议/期刊
- 链接
- PDF link if available
- paper ID
- arXiv ID
- ePrint ID
- DOI
- publication date
- update date
- relevance label
- relevance score
- taxonomy tags
- matched keywords
- negative keywords if any
- reading priority
- Chinese summary
- why it matters
- how it relates to the user’s research directions
- suggested reading strategy

## 10.3 Research-direction relation fields

For A-class papers, explicitly state relation to:

- LWE/RLWE/MLWE
- SIS/NTRU
- BKZ/G6K/fplll
- ML-KEM/Kyber
- ML-DSA/Dilithium
- Falcon/FN-DSA
- FHE/CKKS/BFV/BGV/TFHE
- implementation / side-channel / fault attacks
- AI-assisted lattice cryptanalysis

If not related, write “弱相关” or “无直接关系”.
Do not force a relationship that does not exist.

## 10.4 If no A/B papers exist

Still generate the daily digest.

Write clearly:

“今日无强相关格密码论文。”

Then list any C-class papers if present.

If no C-class papers exist either, say:

“今日未发现值得记录的格密码相关新论文。”

---

# 11. Daily Automation Behavior

When used by Codex Automation, follow this flow.

## 11.1 Run command

Use:

`python -m lattice_digest.run --since 36h --output markdown,json --send none`

## 11.2 Verify outputs

After running, verify the existence of:

- `digests/YYYY-MM-DD.md`
- `data/YYYY-MM-DD.json`
- `papers.db`

## 11.3 Run tests

Run:

`python -m pytest`

Core tests that must pass:

- ranker tests
- dedup tests
- negative filter tests

Network-dependent tests may be skipped if configured as such.

## 11.4 Commit changes

If files changed, run:

`git add AGENTS.md config prompts src tests digests data papers.db .github pyproject.toml README.md`

Then commit with:

`git commit -m "daily lattice digest: YYYY-MM-DD"`

If there are no changes, state:

“no changes to commit”

Do not treat this as an error.

---

# 12. Expected Codex Inbox Summary

After a successful daily automation run, produce a concise Chinese summary in Codex inbox.

The summary must include:

- 今日 A/B/C 类论文数量
- 最值得读的 1-3 篇论文
- 每篇为什么重要
- 与以下方向的关系：
  - LWE/RLWE/MLWE
  - BKZ/G6K/fplll
  - ML-KEM/Kyber
  - ML-DSA/Dilithium
  - Falcon/FN-DSA
  - FHE
  - implementation / side-channel / fault attacks
  - AI-assisted lattice cryptanalysis

If no A/B papers exist, say:

“今日无 A/B 类强相关格密码论文，已生成空日报或 C 类背景摘要。”

---

# 13. Common Failure Handling

## 13.1 Source unavailable

If a source is temporarily unavailable:

- Record the error.
- Continue with other sources.
- Do not fail the entire run unless all primary sources fail.
- Mention the failed source in the digest or error report.

## 13.2 API key missing

If optional API keys are missing:

- Continue with public sources.
- Do not fail unless the source is mandatory.
- Mention that metadata enrichment may be incomplete.

Optional keys may include:

- OPENAI_API_KEY
- SEMANTIC_SCHOLAR_API_KEY
- EMAIL_TO
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

## 13.3 No papers found

Generate the digest anyway.

Do not fabricate papers to fill the digest.

## 13.4 Too many false positives

Tighten filters:

- Increase negative keyword penalties.
- Require cryptographic context.
- Cap AI-only papers at C.
- Cap generic PQC papers without lattice schemes at B or C.
- Exclude physics/materials/biology lattice papers.

---

# 14. Project File Expectations

The project should contain:

- `AGENTS.md`
- `.codeartsdoer/skills/lattice-paper-digest/SKILL.md`
- `config/taxonomy.yaml`
- `config/negative_keywords.yaml`
- `config/sources.yaml`
- `config/keywords.yaml`
- `prompts/digest_writer.md`
- `prompts/relevance_classifier.md`
- `src/lattice_digest/run.py`
- `src/lattice_digest/ranker.py`
- `src/lattice_digest/dedup.py`
- `src/lattice_digest/digest.py`
- `src/lattice_digest/database.py`
- `src/lattice_digest/sources/`
- `tests/`
- `digests/`
- `data/`
- `papers.db`

If some files are missing, create them incrementally.
Do not overwrite user-edited files without checking existing content.

---

# 15. Style Requirements for Daily Digest

Use clear Chinese.

Avoid vague phrases such as:

- “这篇论文很重要”
- “值得关注”
- “可能有用”

Instead, explain specifically:

- It improves an attack model.
- It changes BKZ cost estimation.
- It affects ML-KEM deployment.
- It gives a new side-channel attack.
- It proposes a new masking countermeasure.
- It introduces a new lattice-based proof system.
- It provides a benchmark useful for AI-assisted LWE cryptanalysis.
- It affects parameter selection.
- It clarifies the security of an assumption.

Use the user’s research priorities as the interpretation lens:

1. LWE/RLWE/MLWE security analysis
2. BKZ/G6K/fplll and lattice reduction
3. ML-KEM/Kyber
4. ML-DSA/Dilithium
5. Falcon/FN-DSA
6. FHE
7. implementation and system deployment
8. side-channel and fault attacks
9. AI-assisted lattice cryptanalysis

---

# 16. Final Rule

Precision is more important than noisy recall.

Never include non-cryptographic lattice papers.

Never hallucinate.

Always generate a Chinese digest, even when there are no relevant papers.

When unsure, classify conservatively and explain the uncertainty.
