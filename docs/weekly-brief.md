# Weekly Research Brief 周报

## 目的

Weekly Research Brief 从一周内的 `data/YYYY-MM-DD.json` 聚合论文记录，去重后按 `reading_priority_score` 排序，生成中文周报，用于组会汇报、导师沟通、研究 idea 沉淀和 PhD 申请材料积累。

## 生成指定周

```powershell
python -m lattice_digest.weekly --week 2026-W22
```

PowerShell 包装脚本：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_weekly_brief.ps1 -Week 2026-W22
```

## 生成指定日期范围

```powershell
python -m lattice_digest.weekly --from-date 2026-05-25 --to-date 2026-05-31
```

PowerShell：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_weekly_brief.ps1 -FromDate 2026-05-25 -ToDate 2026-05-31
```

## 输出位置

周报会同时写入：

- `exports/weekly/YYYY-Www.md`
- `exports/obsidian/weekly/YYYY-Www.md`

第一份用于普通归档，第二份方便直接放进 Obsidian。

## 周报包含什么

周报固定包含 9 个中文章节：

1. 本周核心结论
2. 本周必须精读论文 Top 5
3. AI4Lattice / LWE 攻击动向
4. BKZ / 格基约简 / Hybrid Attack 动向
5. Module-SIS / Commitment / Chameleon Hash 动向
6. ML-KEM / ML-DSA 实现安全动向
7. 可孵化论文 idea
8. 下周阅读计划
9. 可问导师的问题

## 与 Obsidian paper_card 的关系

`paper_card` 是单篇论文的初筛卡片；Weekly Research Brief 是一周内论文的研究态势摘要。建议先用周报决定本周精读队列，再把 Top papers 导出为 Obsidian paper_card 或迁移为手写 `paper_note`。

## 不建议提交的生成物

不要提交：

- `exports/weekly/`
- `exports/obsidian/weekly/`
- 手写组会材料或私人笔记

建议只提交周报生成代码、脚本、测试和文档。
