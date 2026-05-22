# 格密码每日论文推送：{{date}}

## 今日结论

请用 3-5 句话总结今天的论文情况：

- 今天是否有 A 类核心格密码论文；
- 是否出现 LWE/RLWE/MLWE、SIS/NTRU、BKZ/G6K/fplll、ML-KEM/Kyber、ML-DSA/Dilithium、Falcon/FN-DSA、FHE、格基实现/侧信道/故障攻击、AI-assisted lattice cryptanalysis 相关内容；
- 哪 1-3 篇最值得优先阅读；
- 如果没有强相关论文，明确写出：今日无强相关格密码论文。

---

## A 类：今日必读格密码论文

> A 类标准：直接研究 LWE/RLWE/MLWE/SIS/NTRU、格基困难问题、BKZ/LLL/G6K/fplll、ML-KEM/ML-DSA/Falcon、格基协议、FHE、格基实现/侧信道/故障攻击或 AI-assisted lattice cryptanalysis。

{{#each papers_A}}

### {{index}}. {{chinese_title}}

- 原标题：{{title}}
- 作者：{{authors}}
- 来源：{{source}}
- 会议/期刊：{{venue}}
- 链接：{{source_url}}
- PDF：{{pdf_url}}
- 论文 ID：{{paper_id}}
- arXiv ID：{{arxiv_id}}
- ePrint ID：{{eprint_id}}
- DOI：{{doi}}
- 发布日期：{{publication_date}}
- 更新日期：{{update_date}}
- 相关性分类：A
- 相关性分数：{{relevance_score}}
- 子领域标签：{{taxonomy_tags}}
- 命中关键词：{{keywords_matched}}
- 阅读优先级：必读

**中文摘要：**
{{summary_zh}}

**为什么值得关注：**
{{why_it_matters}}

**与我的研究方向的关系：**

- LWE/RLWE/MLWE：{{relation_lwe}}
- SIS/NTRU：{{relation_sis_ntru}}
- BKZ/G6K/fplll：{{relation_bkz}}
- ML-KEM/Kyber：{{relation_mlkem}}
- ML-DSA/Dilithium：{{relation_mldsa}}
- Falcon/FN-DSA：{{relation_falcon}}
- FHE/CKKS/BFV/BGV/TFHE：{{relation_fhe}}
- 实现/侧信道/故障攻击：{{relation_implementation_security}}
- AI-assisted lattice cryptanalysis：{{relation_ai}}

**建议阅读方式：**

1. 先读 Abstract 和 Introduction，确认问题设定、威胁模型和核心贡献。
2. 如果是攻击论文，重点读攻击模型、参数设置、复杂度估计和实验表格。
3. 如果是构造论文，重点读困难假设、归约证明、安全模型和参数选择。
4. 如果是实现/侧信道论文，重点读实验平台、泄漏模型、测量方法和 countermeasure。
5. 如果与 AI 辅助格密码分析相关，重点看数据生成方式、标签定义、是否泄漏 oracle 信息、是否能接入传统攻击流程。

{{/each}}

---

## B 类：值得跟踪论文

> B 类标准：不是纯核心格密码论文，但明确涉及格基 PQC、标准化、部署、安全评估、协议迁移或实现工程。

{{#each papers_B}}

### {{index}}. {{chinese_title}}

- 原标题：{{title}}
- 作者：{{authors}}
- 来源：{{source}}
- 会议/期刊：{{venue}}
- 链接：{{source_url}}
- PDF：{{pdf_url}}
- 相关性分类：B
- 相关性分数：{{relevance_score}}
- 子领域标签：{{taxonomy_tags}}
- 命中关键词：{{keywords_matched}}
- 阅读优先级：值得跟踪

**中文摘要：**
{{summary_zh}}

**为什么值得跟踪：**
{{why_it_matters}}

**建议阅读方式：**

1. 判断它是否影响 ML-KEM、ML-DSA、Falcon 或其他格基方案的部署。
2. 判断它是否提供新的安全评估、实现经验、协议迁移经验或标准化信息。
3. 如果只是泛 PQC 讨论，快速扫读即可；如果含具体格基参数或实验，应详细记录。

{{/each}}

---

## C 类：可选关注 / 背景启发

> C 类标准：可能对格密码研究有间接启发，但不是直接格密码论文。

| 序号 | 中文标题 | 原标题 | 来源 | 链接 | 可能启发 | 是否建议细读 |
| ---: | -------- | ------ | ---- | ---- | -------- | ------------ |

{{#each papers_C}}
| {{index}} | {{chinese_title}} | {{title}} | {{source}} | {{source_url}} | {{why_it_matters}} | {{reading_priority}} |
{{/each}}

---

## D 类过滤说明

今天过滤掉的典型误匹配包括：

- crystal lattice
- lattice QCD
- lattice Boltzmann
- spin lattice
- optical lattice
- materials lattice
- solid-state lattice
- phonon lattice
- lattice oxygen
- lattice thermal conductivity
- lattice gauge theory
- lattice field theory
- 其他只包含 “lattice” 但没有密码学上下文的论文

过滤原则：

1. 只出现 lattice 一个词，不代表是格密码论文。
2. 必须同时出现 cryptography、cryptanalysis、post-quantum、LWE、SIS、NTRU、BKZ、FHE、KEM、signature、ZKP、side-channel、implementation 等密码学上下文。
3. 命中硬负关键词且没有密码学上下文的论文，一律标记为 D 类并排除。
4. SQIsign、SIKE、SIDH、CSIDH 等同源密码论文不是格密码论文；只有在直接比较格基方案时才可作为 C 类背景参考。

---

## 今日统计

- A 类核心格密码论文：{{count_A}} 篇
- B 类强相关论文：{{count_B}} 篇
- C 类可选关注论文：{{count_C}} 篇
- D 类过滤论文：{{count_D}} 篇
- 总候选论文：{{count_total}} 篇
- 去重后论文：{{count_deduplicated}} 篇

---

## 明日跟踪建议

明天建议继续重点关注以下关键词：

- LWE / RLWE / MLWE
- SIS / NTRU
- BKZ / LLL / G6K / fplll
- primal attack / dual attack / hybrid attack
- Kyber / ML-KEM
- Dilithium / ML-DSA
- Falcon / FN-DSA
- FrodoKEM / Saber / Hawk / HAETAE / Raccoon
- FHE / CKKS / BFV / BGV / TFHE
- NTT / Gaussian sampling / rejection sampling
- side-channel / fault attack / masking
- AI-assisted lattice cryptanalysis
- neural lattice reduction
- coordinate selection for hybrid attacks
- modular arithmetic learning

---

## 今日一句话总结

{{one_sentence_summary}}
