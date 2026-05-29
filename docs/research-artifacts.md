# Research Artifact Scaffold

Research Artifact Scaffold 用于把 Paper Plan 变成可以直接开工的项目骨架。它只读取已有 `exports/paper_plans/*.json` 或 `.md`，不会运行论文抓取，不会修改 digest、data、`papers.db`，也不会执行 git 操作。

## 1. 目的

- 把研究计划落成代码、实验、论文和组会材料目录。
- 让 3-6 个月 MVP 从第一天就有 reproducibility 结构。
- 为导师讨论准备 `PROJECT_BRIEF.md`。
- 为后续 GitHub artifact 和论文写作准备统一骨架。

## 2. 从 Paper Plan 创建 Artifact

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\create_research_artifact.ps1 -Plan exports\paper_plans\example.json
```

Python 等价命令：

```bash
python -m lattice_digest.artifact_scaffold --plan exports/paper_plans/example.json --output-dir research_artifacts
```

dry-run 不写文件：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\create_research_artifact.ps1 -Plan exports\paper_plans\example.json -DryRun
```

## 3. 目录用途

默认生成：

- `README.md`：项目问题、MVP、路线、风险和下一步。
- `TODO.md`：Today / This Week / Month 1-3 / Advisor Discussion / Risks / Reading List。
- `PROJECT_BRIEF.md`：组会快速汇报材料。
- `paper/outline.md`：论文大纲。
- `configs/`：实验和参数配置。
- `src/`：实现代码。
- `experiments/`：实验脚本或 notebook。
- `scripts/`：运行脚本。
- `tests/`：最小测试。
- `results/`：实验输出占位。
- `docs/`：reproducibility、audit、privacy model 等文档。
- `notes/`：阅读笔记和导师讨论记录。

不同 track 会自动加目录，例如：

- AI4Lattice：`src/datasets`、`src/models`、`src/attacks`、`src/baselines`。
- Module-SIS：`src/primitives`、`src/params`、`experiments/parameter_estimation`。
- BKZ：`src/g6k_bridge`、`src/fplll_bridge`、`experiments/block_size_sweep`。
- ML-KEM / ML-DSA：`src/audit`、`src/ct_checks`、`src/test_vectors`。
- ZK-friendly PQ Privacy：`src/commitments`、`src/encodings`、`docs/privacy_model.md`。

## 4. 哪些文件可以提交

如果你明确决定把某个 artifact 作为正式研究项目，可以提交：

- `README.md`
- `TODO.md`
- `PROJECT_BRIEF.md`
- `configs/`
- `src/`
- `scripts/`
- `tests/`
- `docs/`
- `paper/outline.md`

提交前应人工确认没有真实密钥、私人笔记或未准备公开的实验数据。

## 5. 哪些结果文件暂不提交

默认不要提交：

- `research_artifacts/` 生成物，除非你明确确认；
- 大型 `results/`；
- 临时 logs；
- 私人 notes；
- 未清理的 notebooks；
- 任何真实 API key、邮箱密码或 token。

## 6. 进入真实实验

建议顺序：

1. 阅读来源论文并核对 `TODO_VERIFY`。
2. 写最小参数或最小 benchmark。
3. 实现 baseline。
4. 跑最小实验。
5. 记录失败样例和环境。
6. 决定继续推进、降级为 artifact，或停放。

## 7. 用于组会

直接从 `PROJECT_BRIEF.md` 准备 5 分钟汇报：

- 一句话问题；
- 为什么不是平庸拼接；
- 最小实验或构造；
- 当前风险；
- 需要导师拍板的问题。

## 8. 用于导师讨论

优先讨论：

- 这个 MVP 是否足以支撑短期论文；
- 哪些安全证明或参数分析是硬门槛；
- 实验结果不显著时能否降级；
- 投稿定位是否过高或过低；
- 是否适合作为 PhD 长期线的一部分。

## 9. 连接 PhD 长期研究规划

Artifact scaffold 把长期叙事压缩成可执行单元。AI4Lattice 方向应聚焦 classical attack pipeline 的可验证子模块；Module-SIS / ZK-friendly PQ privacy 方向应收敛到小原语、小 benchmark 或小实现，再逐步扩展到 privacy-preserving authentication、post-quantum identity systems 和后量子隐私计算。
