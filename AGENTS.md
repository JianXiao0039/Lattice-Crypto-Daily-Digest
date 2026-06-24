# AGENTS.md

## Project Mission

This repository implements a daily paper-monitoring and digest system for lattice-based cryptography.

When this file conflicts with `.codeartsdoer/skills/lattice-paper-digest/SKILL.md`, the skill file is the source of truth.

The system must collect, classify, deduplicate, summarize, and publish papers that are strongly related to:

- lattice-based cryptography
- post-quantum lattice schemes
- LWE/RLWE/MLWE/SIS/NTRU assumptions
- lattice reduction and lattice cryptanalysis
- lattice-based protocols
- lattice-based fully homomorphic encryption
- implementation, side-channel, and fault analysis of lattice schemes
- AI-assisted lattice cryptanalysis, only when explicitly connected to lattice cryptography

The final daily digest must be written in Chinese.

## Artifact Path Compatibility Default

Artifact readers now default to canonical year-partitioned paths when
`LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK` is unset. Legacy fallback is temporary,
read-only, and requires explicit process-scoped opt-in such as:

```powershell
$env:LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK = "1"
```

Writers must remain canonical-only and must not use compatibility fallback to
choose output paths.

---

## Hard Scope: Always Treat as In-Scope

The following topics are always relevant.

### 1. Lattice assumptions and hard problems

- LWE
- Learning With Errors
- RLWE
- Ring-LWE
- MLWE
- Module-LWE
- Polynomial-LWE
- TLWE
- LWR
- Learning With Rounding
- SIS
- MSIS
- ISIS
- Ring-SIS
- Module-SIS
- NTRU
- NTRU lattice
- ideal lattice
- module lattice
- standard lattice
- Euclidean lattice
- non-commutative algebraic lattice
- SVP
- Shortest Vector Problem
- CVP
- Closest Vector Problem
- BDD
- Bounded Distance Decoding
- uSVP
- Unique SVP
- GapSVP
- GapCVP
- Minimax-CVP
- lattice decoding
- lattice trapdoor
- discrete Gaussian
- Gaussian sampling
- rejection sampling
- gadget decomposition

### 2. Lattice reduction and attacks

- LLL
- Lenstra-Lenstra-Lovasz
- BKZ
- BKZ 2.0
- Block Korkine-Zolotarev
- HKZ
- Hermite-Korkine-Zolotarev
- slide reduction
- progressive BKZ
- non-deterministic BKZ
- Voronoi reduction
- Seysen reduction
- lattice sieving
- enumeration
- extreme pruning
- Schnorr-Euchner enumeration
- primal attack
- dual attack
- hybrid attack
- lattice reduction attack
- lattice enumeration attack
- lattice sieving attack
- meet-in-the-middle attack for lattice schemes
- G6K
- fplll
- lattice estimator
- security estimation
- root Hermite factor
- GSA
- learning-augmented GSA
- learned pruning
- neural lattice reduction

### 3. Standard and non-standard lattice-based PQC schemes

- Kyber
- ML-KEM
- Module-Lattice-Based Key-Encapsulation Mechanism
- Dilithium
- ML-DSA
- Module-Lattice-Based Digital Signature Algorithm
- Falcon
- FN-DSA
- FrodoKEM
- Saber
- LightSaber
- FireSaber
- NewHope
- qTESLA
- NTRUEncrypt
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

- SQIsign and other isogeny-based schemes are not lattice-based. Include them only as C-class background if they compare directly with lattice schemes.

### 4. Lattice-based advanced protocols

- lattice-based zero-knowledge proof
- lattice ZKP
- lattice-based zero-knowledge argument
- lattice ZKA
- lattice commitment
- lattice-based IBE
- identity-based encryption from lattices
- lattice-based ABE
- attribute-based encryption from lattices
- lattice-based PRE
- proxy re-encryption from lattices
- lattice-based functional encryption
- lattice FE
- lattice-based blind signature
- lattice ring signature
- lattice group signature
- lattice signcryption
- lattice proxy signature
- lattice broadcast encryption
- lattice-based MPC
- lattice-based multiparty computation
- lattice-based oblivious transfer
- lattice OT
- lattice-based threshold cryptography
- lattice secret sharing

### 5. FHE and lattice-based homomorphic encryption

- fully homomorphic encryption
- FHE
- lattice-based FHE
- CKKS
- BFV
- BGV
- TFHE
- GSW
- Gentry-Sahai-Waters
- HEAAN
- leveled FHE
- somewhat homomorphic encryption
- bootstrapping
- lattice bootstrapping
- homomorphic evaluation
- RLWE-based homomorphic encryption

### 6. Implementation, hardware, and software optimization

- NTT
- number theoretic transform
- polynomial multiplication
- modular multiplication
- modular reduction
- Montgomery reduction
- Barrett reduction
- Gaussian sampler
- binomial sampler
- rejection sampler
- CDT sampler
- Knuth-Yao sampler
- constant-time implementation
- optimized implementation
- AVX
- AVX2
- AVX512
- NEON
- SIMD
- vectorization
- FPGA
- ASIC
- RISC-V
- Cortex-M
- Cortex-A
- instruction set extension
- HLS
- RTL
- hardware/software co-design
- low-power implementation
- high-speed implementation

### 7. Physical security

- side-channel attack on lattice schemes
- lattice SCA
- power analysis
- timing attack
- cache attack
- electromagnetic attack
- template attack
- profiled attack
- deep-learning side-channel attack on lattice schemes
- fault attack on lattice schemes
- fault injection
- laser fault injection
- voltage glitch
- clock glitch
- masking
- threshold masking
- side-channel countermeasure
- fault countermeasure

### 8. Standardization and deployment

- NIST PQC
- PQC standardization
- post-quantum standard
- ML-KEM deployment
- ML-DSA deployment
- FN-DSA deployment
- TLS hybrid key exchange
- IETF
- CFRG
- LAMPS
- quantum-safe migration
- post-quantum TLS
- open-source PQC implementations
- PQC parameter optimization
- decryption failure analysis
- noise analysis

### 9. AI-assisted lattice cryptanalysis

Only include AI/ML papers when they explicitly connect to cryptography, lattice cryptanalysis, LWE, RLWE, MLWE, SIS, NTRU, BKZ, modular arithmetic, or cryptanalytic search.

Relevant topics include:

- Transformer for LWE
- Swin Transformer for LWE/RLWE/MLWE
- neural cryptanalysis of LWE
- machine learning attacks on LWE
- learning-augmented lattice reduction
- learning-guided BKZ
- neural lattice reduction
- coordinate selection for hybrid attacks
- learned pruning
- modular arithmetic learning
- algorithmic reasoning for cryptanalysis
- discrete structure learning for cryptographic problems

---

## Strict Exclusion: Always Filter Out

The following uses of “lattice” are out of scope unless the paper explicitly discusses cryptography or cryptanalysis:

- crystal lattice
- lattice QCD
- lattice Boltzmann
- spin lattice
- optical lattice
- solid-state lattice
- material lattice
- materials lattice
- lattice oxygen
- lattice thermal conductivity
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
- lattice model in physics
- lattice path combinatorics without cryptographic relevance
- distributive lattice
- Boolean lattice
- lattice-ordered group
- lattice polytope without cryptographic relevance

A paper that only contains the word “lattice” is not enough. It must contain cryptographic context.

---

## Classification Policy

Use four relevance labels.

### A: Core lattice cryptography

Must include in the daily digest.

A paper is A-class if it directly studies at least one of:

- LWE/RLWE/MLWE/LWR/SIS/NTRU
- SVP/CVP/BDD/GapSVP/GapCVP in cryptographic context
- lattice reduction attacks
- BKZ/LLL/sieving/enumeration for cryptanalysis
- Kyber/ML-KEM
- Dilithium/ML-DSA
- Falcon/FN-DSA
- FrodoKEM/Saber/Hawk/HAETAE/Raccoon
- lattice-based KEM/signature/encryption
- lattice-based ZKP/IBE/ABE/PRE/FE/MPC/OT
- FHE/CKKS/BFV/BGV/TFHE
- side-channel or fault attacks on lattice schemes
- implementation of lattice schemes
- AI-assisted LWE or lattice cryptanalysis

### B: Strongly related PQC/security/implementation paper

Include in the daily digest.

A paper is B-class if it is not purely about lattice theory but clearly involves:

- PQC deployment involving lattice schemes
- TLS/IETF/NIST standardization involving ML-KEM, ML-DSA, Falcon, or other lattice schemes
- security evaluation of post-quantum protocols involving lattice schemes
- comparison of PQC schemes where lattice schemes are central
- implementation engineering of PQC stacks involving lattice algorithms

### C: Potentially useful background

Include briefly.

Examples:

- AI for modular arithmetic but not explicitly LWE
- generic optimization that may inspire lattice attack heuristics
- algorithmic reasoning for discrete structures
- general cryptanalysis methodology not directly tied to lattices
- non-lattice PQC papers that compare against lattice schemes
- broad PQC surveys with lattice sections

### D: Irrelevant or false positive

Exclude from the daily digest.

Examples:

- physics/materials/biology papers using “lattice”
- lattice QCD
- lattice Boltzmann
- crystal lattice
- spin lattice
- papers without a reliable URL or source
- papers with no cryptographic relevance

---

## Required Data Sources

Prefer stable APIs, RSS, Atom, OAI-PMH, and structured metadata.

Primary sources:

1. IACR ePrint RSS / Atom / OAI-PMH
2. arXiv API / RSS / OAI-PMH
3. DBLP API
4. OpenAlex API
5. Crossref REST API
6. Semantic Scholar Graph API
7. IACR venues:
   - CRYPTO
   - EUROCRYPT
   - ASIACRYPT
   - PKC
   - TCC
   - CHES / TCHES
   - FSE / ToSC
   - Journal of Cryptology
   - Communications in Cryptology
   - Real World Crypto
8. PQCrypto official pages
9. NIST PQC official pages
10. Major security conferences:

- IEEE S&P
- ACM CCS
- USENIX Security
- NDSS
- AsiaCCS
- ESORICS
- RAID
- ACSAC

AI conferences are low priority and should only be searched when cryptographic relevance is explicit.

---

## Reliability Rules

Never invent:

- papers
- authors
- venues
- years
- abstracts
- URLs
- DOI
- arXiv IDs
- ePrint IDs
- PDF links

If metadata is incomplete, mark it as unknown.

Do not include papers without a trustworthy source URL.

Deduplicate by:

1. DOI
2. arXiv ID
3. IACR ePrint ID
4. normalized title
5. normalized title + first author + year
6. fuzzy title similarity when necessary

IACR ePrint must not be queried more than once per day.

HTML scraping is only a fallback. Prefer API, RSS, Atom, OAI-PMH, JSON, XML.

---

## Output Requirements

The daily digest must generate:

- `digests/YYYY/daily/YYYY-MM-DD.md`
- `data/YYYY/daily/YYYY-MM-DD.json`
- `papers.db`

The Markdown digest must be Chinese.

For each A/B paper, include:

- 中文标题翻译
- Original title
- Authors
- Source
- Venue
- URL
- PDF URL if available
- Relevance label
- Relevance score
- Taxonomy tags
- Matched keywords
- Negative keywords if any
- 100-200 Chinese character abstract
- Why it matters
- Suggested reading priority
- Connection to:
  - LWE/RLWE/MLWE
  - BKZ/G6K/fplll
  - ML-KEM/Kyber
  - ML-DSA/Dilithium
  - Falcon/FN-DSA
  - FHE
  - implementation/side-channel/fault attacks
  - AI-assisted lattice cryptanalysis

If no A/B papers are found, still generate a digest saying:

“今日无强相关格密码论文。”

If no A/B/C papers are found, say:

“今日未发现值得记录的格密码相关新论文。”

Required Markdown structure, matching `.codeartsdoer/skills/lattice-paper-digest/SKILL.md`:

1. 今日结论
2. A 类：今日必读格密码论文
3. B 类：值得跟踪论文
4. C 类：可选关注 / 背景启发
5. D 类过滤说明
6. 今日统计
7. 明日跟踪建议
8. 今日一句话总结

Each A/B paper must include paper ID, arXiv ID, ePrint ID, DOI, publication date, update date, reading priority, Chinese summary, why it matters, relation to the user's research directions, and suggested reading strategy.

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

If not related, write “弱相关” or “无直接关系”; do not force a relationship.

If a daily run fails, do not silently fail. Generate `digests/YYYY/daily/YYYY-MM-DD-error.md` containing the failed source, failed command, error summary, suspected cause, suggested fix, and whether outputs were partially generated.

Scoring thresholds must follow the skill:

- 80-100: A, 必读
- 60-79: B, 值得跟踪
- 40-59: C, 可选关注
- 0-39: D, 过滤

---

## Commands

Use these commands:

```bash
python -m lattice_digest.run --since 36h --output markdown,json --send none
python -m lattice_digest.run --since 36h --dry-run
python -m pytest
```

---

## Local Automation Git Rule

For routine local Codex automation, Codex may run:

```powershell
.\scripts\run_daily_digest_and_push.ps1
```

Outside that script, Codex must not expand the `git add` scope for daily automation.
Automatic daily commits may include only:

- `digests/`
- `data/`
- `papers.db`

If the digest command fails or `python -m pytest` fails, Codex must not commit or push.
