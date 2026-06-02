# Research Scope Taxonomy

本文档描述 `lattice-crypto-daily-digest` 的研究覆盖范围、section assignment 规则和误报控制边界。它只说明 taxonomy / topical section 语义，不定义新的 workflow 行为。

Phase 9M/9N 扩展主题必须保持 lattice cryptography 或 post-quantum cryptography grounded。泛 DP、FL、LLM fine-tuning、registration、encryption、isomorphism、zero-knowledge、credential、commitment 或 privacy 论文本身不够，必须出现 lattice / PQC / HE / FHE / SIS / LWE / RLWE / MLWE / NTRU / Module-SIS / Module-LWE 等明确锚点，才进入 lattice-specific sections。

English summary: this document defines research scope and deterministic topical sections. It does not add scheduled automation, cron jobs, Windows Task Scheduler integration, background services, startup tasks, or automatic runs.

## 1. Core lattice cryptography sections

The project keeps the existing core sections:

- `LWE / RLWE / MLWE`
- `SIS / NTRU / Commitments / Chameleon Hash`
- `BKZ / LLL / G6K / Lattice Reduction / Attacks`
- `PQC Standards / ML-KEM / ML-DSA / Falcon`
- `AI-assisted Lattice Cryptanalysis`
- `Implementation / Side-channel / Systems`
- `General Cryptography / Privacy`
- `Other / Watchlist`

These sections are deterministic tags for research routing. They do not change A/B/C/D ranking thresholds or source fetching behavior.

## 2. Lattice + Privacy / FL / LLM Fine-tuning

Section name: `Lattice + Privacy / FL / LLM Fine-tuning`.

Include only when privacy / federated learning / LLM fine-tuning terms co-occur with explicit lattice/PQC/HE/FHE cryptographic anchors.

Positive examples:

- Differentially private federated fine-tuning with RLWE-based secure aggregation.
- Lattice-based secure aggregation for federated learning.
- Homomorphic encryption for ML using lattice-based HE.
- Fully homomorphic encryption for private LLM fine-tuning based on RLWE.
- PQC-secure federated learning with explicit lattice or HE evidence.

False positives to exclude:

- Generic DP-SGD for LLM fine-tuning.
- Generic federated learning paper without cryptography.
- Generic secure aggregation without HE/FHE/lattice/PQC evidence.
- Generic privacy-preserving training without lattice, PQC, HE, FHE, or secure aggregation cryptographic evidence.

## 3. Lattice Isomorphism / Advanced Lattice Assumptions

Section name: `Lattice Isomorphism / Advanced Lattice Assumptions`.

Include explicit lattice-isomorphism terms:

- lattice isomorphism
- lattice isomorphism problem
- isomorphism of lattices
- lattice automorphism
- structured lattice isomorphism
- LIP only when the surrounding text is explicitly lattice/PQC/isomorphism context.

False positives to exclude:

- graph isomorphism
- model isomorphism
- code isomorphism
- neural isomorphism
- chemical isomorphism
- image registration
- point cloud registration

## 4. Registration-Based Encryption / Advanced Encryption Primitives

Section name: `Registration-Based Encryption / Advanced Encryption Primitives`.

Include only lattice/PQC-grounded RBE evidence:

- lattice-based registration-based encryption
- LWE-based registration-based encryption
- SIS-based registration-based encryption
- post-quantum registration-based encryption
- PQC registration-based encryption
- registration-based encryption from lattices

Generic `registration` plus `encryption` is not enough. Generic `registration-based encryption` without lattice/PQC/LWE/SIS anchors is also not enough for this lattice-specific section.

False positives to exclude:

- user account registration systems
- web login / signup workflows
- database account registration
- medical image registration
- point cloud registration
- domain registration
- certificate registration unless explicitly tied to lattice/PQC RBE

## 5. Lattice Advanced Primitives

Section name: `Lattice Advanced Primitives`.

Include lattice-based or PQC-backed versions of:

- chameleon hash
- commitment / trapdoor commitment
- accumulator
- ring signature / linkable ring signature / group signature
- anonymous credential
- attribute-based encryption
- functional encryption
- predicate encryption
- zero-knowledge / lattice-based proof
- Module-SIS primitive
- MLWE primitive

Do not overclassify generic ZK, anonymous credential, or privacy primitive papers as lattice work unless there is explicit lattice, PQC, SIS, LWE, RLWE, MLWE, Module-SIS, or NTRU evidence. Generic cryptographic privacy papers should route to `General Cryptography / Privacy`.

Positive examples:

- Module-SIS chameleon hash.
- SIS-based commitment.
- Lattice-based anonymous credential.
- Lattice-based ring signature.
- LWE-based functional encryption.
- Lattice-based zero-knowledge proof.

False positives to exclude:

- Generic zero-knowledge proof.
- Generic anonymous credential.
- Generic commitment scheme.
- Generic functional encryption.
- Generic accumulator, ABE, FE, predicate encryption, or ring signature without lattice/PQC evidence.

## 6. AI4Lattice boundary

`AI-assisted Lattice Cryptanalysis` requires AI/ML terms plus lattice/LWE/RLWE/MLWE/SIS/BKZ/cryptanalysis anchors. Generic Transformer, GNN, or foundation-model papers are not AI4Lattice unless the cryptanalytic or lattice context is explicit.

## 7. Falcon boundary

Falcon is treated as PQC only when the context indicates the lattice signature scheme, such as Falcon signature, FN-DSA, post-quantum signature, FIPS 205, implementation security, or side-channel/fault analysis. Model names such as Falcon-X are not routed to PQC by themselves.

## 8. Downstream propagation

The topical sections are serialized in each record as `research_sections`. Downstream consumers preserve these labels:

- weekly synthesis groups records by section;
- reading queue track assignment can use the section names;
- Obsidian scaffold frontmatter includes `research_sections`;
- research progress / advisor updates can group by section;
- research artifact export can prioritize tracks from these sections.

## 9. Safety and workflow boundary

This taxonomy expansion does not add:

- scheduled automation
- cron
- Windows Task Scheduler
- background services
- startup tasks
- automatic runs

It does not change fetcher behavior, ranking weights, A/B/C/D thresholds, reading queue status semantics, or workflow execution semantics.

## 10. Query expansion and negative keywords

Phase 9O 的查询扩展遵循同一条边界：新增召回词必须带 lattice / PQC / HE / FHE / LWE / RLWE / MLWE / SIS / Module-SIS / NTRU 等锚点。配置中可以搜索 `lattice-based secure aggregation federated learning`、`RLWE-based secure aggregation federated learning`、`FHE private LLM fine-tuning RLWE`、`lattice-based registration-based encryption`、`lattice isomorphism problem`、`Module-SIS chameleon hash`、`lattice-based zero-knowledge proof` 等 anchored queries。

不应把 `federated learning`、`LLM fine-tuning`、`DP-SGD`、`registration encryption`、`zero-knowledge proof`、`anonymous credential`、`commitment scheme`、`functional encryption` 等泛词作为独立查询加入。它们只有在同一查询或论文元数据中出现 lattice / PQC / HE / FHE / LWE / RLWE / MLWE / SIS / Module-SIS 等明确锚点时，才可进入格密码科研跟踪。

负面关键词用于减少显然非格密码的误报，例如 user/account/domain registration、medical image registration、point cloud registration、graph/code/model/neural/chemical isomorphism，以及 homomorphic-sounding 但并非密码学 HE/FHE 的机器学习表达。硬负面词在缺少密码学上下文时可以过滤；软负面词只记录风险上下文，不能误杀带有 lattice/PQC 锚点的真阳性。

English summary: query expansion is anchored by lattice/PQC/HE/FHE evidence. Generic privacy, registration, isomorphism, ZK, credential, commitment, and FE terms are insufficient as standalone lattice-tracking queries. Negative keywords reduce obvious non-lattice false positives while preserving anchored true positives.
