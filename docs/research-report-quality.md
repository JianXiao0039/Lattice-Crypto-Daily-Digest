# Research Report Quality

This document describes the report-quality polish layer for daily and weekly research review. It is manual-only and does not add scheduled automation, Windows Task Scheduler tasks, cron jobs, background services, startup tasks, or automatic runs.

## 1. 目的

Phase 9R 的目标是让 daily digest、weekly synthesis、research artifact export 和 advisor/progress draft 更适合格密码研究阅读，而不是只列出论文标题。

报告展示层应该清楚区分：

- paper facts：来自 source metadata 的题名、作者、日期、来源、URL；
- ranking explanation：当前 ranker 给出的 relevance label / score / matched signals；
- source health uncertainty：外部源红黄绿、rate limit、timeout、latest/RSS 状态；
- research relevance：和 LWE/RLWE/MLWE、SIS/Module-SIS、NTRU、ML-KEM/Kyber、ML-DSA/Dilithium、FHE/HE、lattice-based primitive、PQC anchor 的关系；
- action recommendation：今日精读、本周阅读、暂存、人工核验等。

## 2. 不改变的语义

Phase 9R 不改变：

- fetcher behavior；
- ranking thresholds；
- taxonomy semantics；
- section classifier semantics；
- query expansion；
- negative keywords；
- source health semantics；
- workflow execution semantics；
- daily/weekly generated artifacts unless user explicitly runs generation；
- `papers.db`。

新增的是展示层 evidence 和 caveat，不是新的 ranking authority。

## 3. Lattice/PQC anchor evidence

报告会显式展示 lattice/PQC anchor evidence，例如：

- LWE/RLWE/MLWE；
- SIS/Module-SIS；
- NTRU；
- ML-KEM/Kyber；
- ML-DSA/Dilithium；
- FHE/HE；
- lattice-based primitive；
- PQC anchor；
- BKZ/lattice attack；
- AI-assisted lattice。

如果没有明确 anchor，报告应提示需要人工核验，而不是把 generic privacy、FL、LLM、ZK、registration、isomorphism 论文过度解释为格密码主线。

## 4. False-positive risk notes

报告会对以下风险做保守提示：

- generic privacy / federated learning / LLM；
- generic ZK / credential；
- generic registration / isomorphism；
- Falcon-name collision，例如非密码学 Falcon 模型名。

这些 notes 只用于人工 review，不会自动删除论文，也不会改变 A/B/C/D ranking。

## 5. Semantic Scholar advisory metadata

如果记录中存在 Semantic Scholar enrichment metadata，报告可以展示：

- year；
- venue；
- citationCount；
- influentialCitationCount；
- DOI；
- CorpusId；
- openAccessPdf。

这些信息只能作为 advisory context。`citationCount` 和 `influentialCitationCount` 不得覆盖 relevance ranking、reading priority 或 paper-plan 判断。

## 6. 推荐人工阅读流程

1. 先看 Top A-level papers。
2. 检查每篇论文的 paper facts 是否完整。
3. 看 ranking explanation 和 matched signals。
4. 检查 lattice/PQC anchor evidence。
5. 若 source health 有 red/yellow，保守解释当天覆盖率。
6. 对 generic privacy / FL / ZK / registration / isomorphism 项目先放 watchlist。
7. 进入阅读队列前打开原文核验摘要、作者、日期、DOI、arXiv/ePrint ID。

## English Summary

The report-quality layer improves daily and weekly research reports by separating source metadata, ranking explanations, source-health uncertainty, lattice/PQC anchor evidence, research relevance, and action recommendations. It does not change fetchers, ranking thresholds, taxonomy semantics, section classification, source-health semantics, or workflow execution. Semantic Scholar metadata is displayed only as advisory context and must not override relevance ranking.
