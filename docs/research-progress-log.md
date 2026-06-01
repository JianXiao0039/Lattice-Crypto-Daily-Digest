# Research Progress Log / Advisor Update

本页说明 Phase 8I 的研究进展导出层。它只读取已有周报、阅读队列、Source Health ledger、Obsidian 笔记和 research artifact manifest，不运行抓取器，不修改 reading queue，也不写入 Zotero、Obsidian vault 或论文数据库。

## 1. 用途

`lattice_digest.research_progress` 用于把一周内已经生成的研究情报材料整理成四类可人工编辑的草稿：

- `advisor-update-draft.md`：给导师汇报前的周进展草稿。
- `research-progress-log.md`：个人研究进展日志。
- `next-week-plan.md`：下一周阅读、验证、实验和工程维护计划。
- `verification-backlog.md`：需要核验原文、数学证明、代码复现和元数据的清单。

这些文件是辅助材料，不是论文结论，也不会声称已经证明安全性或完成实验。

## 2. 输入

默认读取：

- `data/weekly/YYYY-Www.json`
- `state/reading-queue.json`
- `audits/source-health/*.json`
- `exports/obsidian-paper-notes/Papers/**/*.md`
- `exports/research-artifacts/*/manifest.json`

所有输入都是只读。缺少周报或阅读队列时，命令仍会生成空框架，并在 manifest 中记录输入缺失状态。

## 3. 输出

默认输出到：

```text
exports/research-progress/YYYY-Www/
```

目录内包含：

- `manifest.json`
- `advisor-update-draft.md`
- `research-progress-log.md`
- `next-week-plan.md`
- `verification-backlog.md`

`exports/research-progress/` 是本地运行产物，默认不提交。

## 4. PowerShell 用法

在项目根目录运行：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.research_progress generate --days 7
```

指定周：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.research_progress generate --week-id 2026-W22
```

指定日期范围：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.research_progress generate --from-date 2026-05-25 --to-date 2026-05-31
```

Dry-run 只打印摘要，不写文件：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.research_progress generate --week-id 2026-W22 --dry-run
```

## 5. 可选输入路径

可以显式传入路径，便于在临时目录或外部研究工作区审计：

```powershell
python -m lattice_digest.research_progress generate `
  --weekly-json data\weekly\2026-W22.json `
  --reading-queue state\reading-queue.json `
  --source-health-dir audits\source-health `
  --obsidian-notes-dir exports\obsidian-paper-notes\Papers `
  --artifact-dir exports\research-artifacts `
  --output-dir exports\research-progress
```

## 6. 保守表述原则

生成内容只做研究管理和汇报草稿：

- 不声称某篇论文已经证明新安全结论。
- 不声称某个攻击已经破解真实参数。
- 不把候选 idea 写成已完成成果。
- 对需要读原文、复现实验、核验数学证明的内容保留 TODO / verification backlog。

## 7. 与其他模块的关系

- Weekly Research Synthesis 负责聚合每日 digest。
- Reading Queue 负责跟踪阅读和核验状态。
- Source Health Ledger 负责记录数据源红黄绿状态。
- Research Progress Log 只把这些已有信息整理成导师更新和个人进展记录。

它不改变抓取、过滤、排序、日报 8 节结构、周报结构、Zotero export 或 reading queue 状态。

## English Summary

The research progress layer generates deterministic weekly advisor update drafts, personal progress logs, next-week plans, and verification backlogs from existing weekly synthesis JSON, reading queue state, source health ledgers, Obsidian notes, and artifact manifests. It is read-only with respect to inputs and does not run fetchers, mutate the reading queue, or claim verified research results.
