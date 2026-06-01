# Query Expansion and Negative Keywords

本文档说明 Phase 9O 的查询扩展和负面关键词边界。它只定义召回配置和误报控制原则，不改变 fetcher 行为、ranking 权重、A/B/C/D 阈值、workflow 语义，也不新增任何计划任务或后台自动化。

English summary: Phase 9O improves anchored query recall and false-positive filtering. It does not change ranking thresholds, workflow behavior, scheduled automation, or digest semantics.

## 1. 核心原则

新增查询必须是 lattice / PQC grounded。泛 registration、encryption、DP、federated learning、LLM fine-tuning、isomorphism、zero-knowledge、credential、commitment、functional encryption 或 privacy 关键词不能单独进入格密码源查询。

允许的锚点包括：

- lattice-based / from lattices
- post-quantum / PQC
- HE / FHE / homomorphic encryption
- LWE / RLWE / MLWE / Module-LWE
- SIS / Module-SIS / Ring-SIS
- NTRU
- BKZ / lattice reduction / lattice cryptanalysis

## 2. Lattice + Privacy / FL / LLM Fine-tuning

允许查询示例：

- lattice-based secure aggregation federated learning
- RLWE-based secure aggregation federated learning
- LWE-based secure aggregation federated learning
- homomorphic encryption private federated learning RLWE
- FHE private LLM fine-tuning RLWE
- post-quantum secure aggregation federated learning
- lattice-based privacy-preserving training
- RLWE encrypted gradient aggregation

不允许作为独立查询：

- federated learning
- LLM fine-tuning
- DP-SGD
- private training
- secure aggregation

## 3. Registration-Based Encryption

允许查询示例：

- lattice-based registration-based encryption
- LWE-based registration-based encryption
- SIS-based registration-based encryption
- post-quantum registration-based encryption
- PQC registration-based encryption
- registration-based encryption from lattices

不允许作为独立查询：

- registration encryption
- user registration encryption
- account registration
- registered user encryption

## 4. Lattice Isomorphism

允许查询示例：

- lattice isomorphism problem
- isomorphism of lattices
- lattice automorphism cryptography
- lattice isomorphism post-quantum
- structured lattice isomorphism

负面边界：

- graph isomorphism
- code isomorphism
- model isomorphism
- neural isomorphism
- chemical isomorphism
- image registration
- point cloud registration

## 5. Advanced Lattice Primitives

允许查询示例：

- Module-SIS chameleon hash
- SIS-based commitment
- lattice-based commitment
- lattice-based anonymous credential
- lattice-based ring signature
- LWE-based functional encryption
- lattice-based zero-knowledge proof
- PQC attribute-based encryption

不允许作为独立查询：

- zero-knowledge proof
- anonymous credential
- commitment scheme
- functional encryption
- attribute-based encryption

## 6. Negative Keyword Policy

硬负面关键词用于明显非格密码误报，例如 user/account/domain registration、medical image registration、point cloud registration、graph isomorphism、model isomorphism 等。若论文没有强密码学上下文，这些命中应过滤为低相关。

软负面关键词用于记录泛 DP/FL/LLM/ZK/credential/commitment/FE 风险上下文。软负面本身不应误杀带有 lattice/PQC/HE/FHE/LWE/RLWE/MLWE/SIS/Module-SIS 锚点的真阳性。

## 7. True Positive Preservation

以下类型必须保留：

- LWE-based registration-based encryption
- RLWE-based secure aggregation for federated learning
- Module-SIS chameleon hash
- SIS-based commitment
- lattice-based zero-knowledge proof
- lattice-based anonymous credential

这些论文可能同时命中 registration、secure aggregation、credential 或 commitment 等泛词，但只要有明确 lattice/PQC/SIS/LWE/RLWE/MLWE 锚点，就不能被负面词直接过滤。

## 8. Workflow Boundary

Phase 9O 不添加：

- Windows Task Scheduler
- cron
- watcher
- background service
- startup task
- automatic scheduled run

本阶段只调整查询配置、负面关键词、文档和测试。
