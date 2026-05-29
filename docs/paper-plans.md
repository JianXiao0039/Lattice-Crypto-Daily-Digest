# Paper Plan 自动升级器

Paper Plan 用于把 Idea Bank 中的高价值线索升级成保守、可执行、可验证的研究计划草案。它不是最终论文，不包含实验结果、安全证明或录用判断，也不会调用 LLM API。

## 1. Paper Plan 的目的

- 支持 3-6 个月短期论文或 artifact 计划。
- 支持组会汇报和导师讨论。
- 支持 GitHub artifact 目录规划。
- 支持 PhD 申请和长期研究主线沉淀。
- 帮助区分“可以马上做的 MVP”和“适合长期观察的方向”。

## 2. 和 Idea Bank 的关系

Idea Bank 负责从 digest、weekly brief、paper card 等已有材料中沉淀研究线索。Paper Plan 只读取 `exports/ideas/idea-bank.json`，从中筛选高分 idea，并生成更结构化的研究计划。

Paper Plan 不回写 Idea Bank，也不修改 digest、weekly brief、paper cards、`papers.db` 或任何抓取逻辑。

## 3. 它不是最终论文

Paper Plan 中所有安全证明、实验、实现和投稿判断都只是“需要做什么”的计划，不是已经完成的结论。特别注意：

- 不编造实验结果。
- 不声称已经证明安全性。
- 不声称 AI 可以端到端破解真实 LWE。
- 不把 toy phenomenon 夸大到真实参数。
- 不给出会议录用概率。

## 4. 生成 Top 5 Paper Plans

默认从 `exports/ideas/idea-bank.json` 读取，并输出到：

- `exports/paper_plans/`
- `exports/obsidian/paper_plans/`

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_paper_plans.ps1
```

等价 Python 命令：

```bash
python -m lattice_digest.paper_plans --idea-bank exports/ideas/idea-bank.json --output-dir exports/paper_plans --obsidian-dir exports/obsidian/paper_plans --top 5
```

## 5. Dry-run

dry-run 只打印将生成的计划，不写文件：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_paper_plans.ps1 -DryRun
```

## 6. 按 Track 生成

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_paper_plans.ps1 -Tracks "AI4Lattice","Module-SIS Primitive"
```

也可以指定最低 idea 分数：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_paper_plans.ps1 -MinIdeaScore 85
```

## 7. paper_plan_score

`paper_plan_score` 范围为 0-100：

- 85-100：优先推进
- 70-84：值得推进
- 50-69：备选计划
- 30-49：暂存计划
- 0-29：不建议推进

评分综合考虑：idea 分数、maturity、是否有 MVP、实验路径、证明或安全分析入口、artifact 可行性、短期可投性、PhD 叙事连接，以及是否避免平庸拼接。

## 8. 升级为 GitHub Artifact

一个成熟 Paper Plan 可以进一步拆成 artifact 仓库：

- `artifact/`
- `src/`
- `experiments/`
- `data/`
- `configs/`
- `notebooks/`
- `scripts/`
- `tests/`
- `docs/`
- `results/`
- `README.md`

先实现最小 MVP，再补 benchmark、参数、实验日志和复现实验命令。

## 9. 用于组会

建议把 Paper Plan 压缩成 6 页组会材料：

1. 研究问题；
2. 为什么不是关键词拼接；
3. 最低可做版本；
4. 实验或证明路线；
5. 风险和降级方案；
6. 需要导师判断的问题。

## 10. 用于 PhD 长期研究规划

Paper Plan 会区分：

- 硕士阶段短期产出；
- PhD 前两年的可扩展研究线；
- PhD 后期及后续研究可能延展。

AI4Lattice 不应被狭隘理解为 Swin-only。它可以包括 Transformer、Swin、Mamba、GNN、RL、Bayesian optimization、learning-to-rank 等模型，但必须插入 classical lattice attack pipeline 的具体环节。

## 11. ZK-friendly PQ Privacy 的定位

ZK-friendly PQ privacy primitives 不应只被视作申博叙事。它可以连接：

- lattice commitments；
- post-quantum anonymous credentials；
- ZK-friendly cryptographic encodings；
- privacy-preserving authentication；
- linkable ring signatures；
- post-quantum identity systems。

但短期 MVP 必须收敛到小原语、小 benchmark 或小实现 artifact，避免一开始做大而空系统愿景。

## 12. 不建议提交的输出

以下是生成物，默认不建议提交：

- `exports/paper_plans/*.json`
- `exports/paper_plans/*.md`
- `exports/obsidian/paper_plans/*.md`

建议提交的只有代码、脚本、测试和文档。
