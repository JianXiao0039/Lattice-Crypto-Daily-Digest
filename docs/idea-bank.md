# Idea Bank 自动沉淀

## 目的

Idea Bank 把 daily digest、weekly brief、paper card 中已有的 `research_hooks`、`advisor_questions`、`reason_for_priority` 和论文 metadata 转成长期研究想法库。它服务四件事：

- 格密码研究主线沉淀；
- 组会汇报候选；
- 短期论文孵化；
- 27fall 全奖 PhD 申请 narrative。

## 和 daily / weekly / paper card 的关系

- daily digest 负责发现当天论文；
- weekly brief 负责一周趋势和阅读计划；
- paper_card 是单篇论文初筛卡片；
- idea_bank 是跨天、跨周、跨论文的研究想法管理系统。

Idea Bank 不会编造论文结论，只使用已有 record 的 title、abstract、reason_for_priority、research_hooks 和 advisor_questions。

## 生成 Idea Bank

默认从 `data/` 目录生成：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_idea_bank.ps1
```

直接调用 Python：

```powershell
python -m lattice_digest.ideas --input data --output-dir exports/ideas --obsidian-dir exports/obsidian/ideas
```

## dry-run

只预览 idea 数量和 Top ideas，不写文件：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_idea_bank.ps1 -DryRun
```

## 按日期范围生成

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_idea_bank.ps1 -FromDate 2026-05-25 -ToDate 2026-05-31
```

## idea_priority_score

分数范围为 0 到 100：

- 85-100：强烈推进；
- 70-84：重点观察；
- 50-69：可做 related work / 备选；
- 30-49：暂存；
- 0-29：低优先级。

分数综合考虑：研究主线匹配度、短期可做性、artifact 可能性、PhD narrative 价值、实验路径、安全证明/参数分析入口、风险和是否只是泛背景。

## maturity

- `vague_signal`：只有弱信号；
- `literature_supported`：有论文支撑，但 MVP 还不清晰；
- `mvp_designable`：可以设计最低可做版本；
- `experiment_ready`：已有明显实验或 artifact 入口；
- `paper_outline_ready`：可以开始拆论文大纲。

## 从 idea 升级为论文计划

1. 阅读来源论文，核对 evidence snippets 是否真实支撑 idea。
2. 写出 core question 和 minimum viable project。
3. 判断需要 proof、安全分析、参数估计还是 implementation artifact。
4. 与导师确认 novelty 和投稿定位。
5. 把 candidate idea 升级为 active，并建立单独 project note。

## 导入 Obsidian

生成物会写入：

- `exports/ideas/idea-bank.json`
- `exports/ideas/idea-bank.md`
- `exports/obsidian/ideas/idea-bank.md`

Obsidian 版本包含双链，例如 `[[AI4Lattice]]`、`[[LWE]]`、`[[BKZ]]`、`[[Module-SIS]]`、`[[ML-KEM]]`、`[[FHE]]`。

## 不建议提交的输出

不要提交：

- `exports/ideas/`
- `exports/obsidian/ideas/`
- 手写 idea note；
- 任何真实 Obsidian vault 路径或私人笔记。

## AI4Lattice 不是 Swin-only

AI4Lattice 包括 Transformer、Swin、Mamba、GNN、CNN、MLP、Diffusion、RL、Bayesian optimization、evolutionary search、learning-to-rank、contrastive learning、自监督学习和神经启发式优化。重点不是端到端破解，而是介入 classical attack pipeline，例如 coordinate selection、sample selection、BKZ scheduling、pruning suggestion、hybrid guessing strategy、distinguisher feature extraction、estimator calibration 和 hard/easy instance separation。

## 短期可投稿 vs 长期 PhD narrative

短期可投稿 idea 通常需要：

- 明确 MVP；
- 可复现实验或参数估计；
- 清楚 novelty；
- 有限风险。

长期 PhD narrative idea 可以更大，但必须能持续连接 LWE/RLWE/MLWE、BKZ/hybrid attack、Module-SIS primitive、PQC implementation security 或 ZK-friendly post-quantum privacy。
