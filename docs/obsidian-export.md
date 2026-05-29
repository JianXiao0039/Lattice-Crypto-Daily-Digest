# Obsidian 论文卡片导出

## Phase 4A 目的

Phase 4A 将每日 digest JSON 中的高优先级论文导出为 Obsidian 兼容 Markdown 卡片，用于格密码论文阅读、组会候选、研究 idea 沉淀和 PhD 申请材料积累。

## 从 digest JSON 导出

默认导出今天的 digest：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\export_obsidian_cards.ps1
```

指定日期：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\export_obsidian_cards.ps1 -Date 2026-05-29
```

指定最低精读分：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\export_obsidian_cards.ps1 -Date 2026-05-29 -MinPriority 70
```

也可以直接调用 Python 模块：

```powershell
python -m lattice_digest.obsidian --input data/2026-05-29.json --output-dir exports/obsidian/papers --min-priority 70
```

## 默认输出目录

默认写入项目内：

```text
exports/obsidian/papers/YYYY-MM-DD/
```

每篇论文生成一张 `YYYY-MM-DD__normalized-title.md` 卡片。

## 指定真实 Obsidian vault

默认不会写真实 vault。确认要导入到自己的 vault 时显式传入目录：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\export_obsidian_cards.ps1 -Date 2026-05-29 -OutputDir "D:\ObsidianVault\LatticeCrypto\Papers"
```

建议先用 `-DryRun` 检查将要生成的文件路径。

## 为什么默认不覆盖

论文卡片后续会加入手写阅读笔记、导师问题和 idea。为避免覆盖手写内容，导出器默认不覆盖已存在文件，而是写成：

- `title.md`
- `title__new.md`
- `title__new-2.md`

只有显式传入 `-Force` / `--force` 才会覆盖，且覆盖前会备份到 `exports/obsidian/backups/`。

## dry-run

只预览将导出的卡片，不写文件：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\export_obsidian_cards.ps1 -Date 2026-05-29 -MinPriority 70 -DryRun
```

## 只导出必须精读 / 建议精读

```powershell
python -m lattice_digest.obsidian --input data/2026-05-29.json --output-dir exports/obsidian/papers --min-priority 0 --labels 必须精读,建议精读
```

PowerShell：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\export_obsidian_cards.ps1 -Date 2026-05-29 -MinPriority 0 -Labels "必须精读,建议精读"
```

## paper_card 与 paper_note

- `paper_card` 是初筛卡片：来自 digest JSON，包含 metadata、优先级、候选双链、摘要、research hooks 和待办。
- `paper_note` 是精读笔记：阅读原文后手写，包含证明路线、实验复现、参数表、贡献判断和组会素材。

## 迁移到组会材料

对于 `priority_label` 为“必须精读”或“建议精读”的卡片：

1. 打开原文链接核对摘要和贡献。
2. 在“我的阅读笔记”中记录核心问题、方法、结论和局限。
3. 如果适合组会，把卡片迁移或链接到 `paper_note`。
4. 若服务 Module-SIS、MLWE attack 或 AI4Lattice 主线，加入 idea bank。

## 不建议提交的生成物

不要提交：

- `exports/obsidian/`
- 真实 Obsidian vault 中的卡片
- 手写阅读笔记
- 任何包含私人路径或个人笔记的文件

建议只提交导出器代码、脚本、测试和文档。
