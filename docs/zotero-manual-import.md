# Zotero Manual Import QA

## 1. 目标

本文档用于验证 Stable Library Export Layer / Zotero Compatibility Layer 是否适合 Zotero 手动导入。Phase 7D 只做离线导出和人工 QA，不调用 Zotero Web API，不创建 `.xpi` 插件，不联网，不写入真实 Zotero 文献库。

当前支持的导出格式：

- Zotero editable-style JSON：`zotero_items.json`
- CSL-JSON：`items.csl.json`
- BibTeX：`items.bib`
- RIS：`items.ris`
- 建议 collection tree：`zotero_collections.json`
- 中文工程报告：`export_report.md`

推荐导入格式优先级：

1. CSL-JSON：字段结构较清晰，适合 Zotero 兼容性测试。
2. BibTeX：适合论文写作工具链和 citation key 验证。
3. RIS：作为跨工具兼容性备选。

## 2. 从 fresh clone 到生成导出文件

### Windows PowerShell

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m pip install -e ".[dev]"
python -m pytest
powershell.exe -ExecutionPolicy Bypass -File scripts\qa_zotero_manual_import.ps1 -Days 7
powershell.exe -ExecutionPolicy Bypass -File scripts\export_zotero.ps1 -Days 7
```

### Windows CMD

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
python -m pip install -e ".[dev]"
python -m pytest
powershell.exe -ExecutionPolicy Bypass -File scripts\qa_zotero_manual_import.ps1 -Days 7
powershell.exe -ExecutionPolicy Bypass -File scripts\export_zotero.ps1 -Days 7
```

注意：PowerShell 使用 `Set-Location`；CMD 使用 `cd /d`。不要把 PowerShell 命令直接粘到 CMD。

### 指定日期范围

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\qa_zotero_manual_import.ps1 -FromDate 2026-05-25 -ToDate 2026-05-31
powershell.exe -ExecutionPolicy Bypass -File scripts\export_zotero.ps1 -FromDate 2026-05-25 -ToDate 2026-05-31
```

默认输出目录：

```text
exports/zotero/YYYY-MM-DD/
```

`exports/` 是运行产物，默认不要提交。

## 3. 如何在 Zotero 中导入

1. 打开 Zotero。
2. 选择 `File -> Import`。
3. 先选择 `items.csl.json` 做第一轮测试。
4. 如果 CSL-JSON 导入效果不理想，再测试 `items.bib`。
5. 如果仍需兼容性备选，再测试 `items.ris`。
6. 导入完成后，不要立即批量合并；先检查 5 到 10 条高优先级论文。
7. 按 `zotero_collections.json` 中建议的 collection tree 手动整理。

当前 `zotero_items.json` 是面向未来 Zotero Web API 的离线 editable JSON 风格，不建议直接当作 Zotero 官方导入格式使用。

## 4. 手动检查字段

导入后至少检查：

- 快速字段清单：title/authors/year/url/abstract/tags/collections/notes。
- `title`：标题是否完整，无 HTML、`contentReference`、`oaicite`、`id=` 污染。
- `authors`：作者是否拆分正确；缺作者时不要出现 fabricated anonymous。
- `year` / `date`：年份是否正确，Semantic Scholar 只有 year 的旧记录不要误当今日论文。
- `url`：是否指向 arXiv、IACR ePrint、DOI、出版社或可信 source。
- `abstract`：是否保留摘要；缺摘要时在 Zotero 备注中做 TODO。
- `tags`：是否出现 `LC/*` 标签，是否过多或误报。
- `collections`：是否能手动整理到 High Priority、AI4Lattice、Lattice Reduction and Attacks 等 collection。
- `notes` / `extra`：是否包含 `LatticeDigestID`、`CanonicalID`、`PriorityScore`、`PriorityLabel`、`WhyItMatters`、`DigestDate`。

## 5. 标签 QA

### 中文标签与英文标签

Zotero 导出默认使用英文 `LC/*` 标签，便于跨系统稳定检索；中文解释保留在导出报告和 digest 中。建议不要在 Zotero 里大量手动创建中文重复标签，避免后续同步和自动化规则复杂化。

### AI4Lattice 标签

只有同时出现 AI/ML 与 lattice/LWE/RLWE/MLWE/SIS/BKZ/cryptanalysis 语境时，才应出现：

- `LC/AI/AI4Lattice`
- `LC/AI/Transformer`
- `LC/AI/Swin`
- `LC/AI/Coordinate-Selection`
- `LC/ResearchLine/AI4Lattice-Hybrid-Ranking`

普通 Transformer / Mamba / CNN 论文如果没有格密码或密码分析上下文，不应打 AI4Lattice。

### 格密码细分标签

重点检查：

- LWE / RLWE / MLWE 不要混淆。
- SIS / Module-SIS / Ring-SIS 不要混淆。
- BKZ / LLL / G6K / fplll 应进入 lattice reduction / attack 相关标签。
- Module-SIS chameleon hash 应进入 `LC/ResearchLine/Module-SIS-Chameleon-Hash`。
- ML-KEM / ML-DSA implementation security 应进入 `LC/ResearchLine/PQC-Implementation-Security`。

## 6. 常见失败原因和修复方法

**没有导出文件**  
先运行 dry-run QA，确认 record 数量是否大于 0：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\qa_zotero_manual_import.ps1 -Days 7
```

**CSL-JSON 导入字段缺失**  
换用 BibTeX 或 RIS 做交叉测试。若所有格式都缺字段，检查 `data/YYYY-MM-DD.json` 的原始 record 是否缺作者、URL、摘要或 DOI。

**BibTeX citation key 冲突**  
导出 key 是 deterministic，并附带 short hash；如果 Zotero 或 LaTeX 项目中已有同名 key，可以在 Zotero 中人工重命名。

**RIS 标签过多**  
RIS 的 `KW` 会带入多个 `LC/*` 标签。可在 Zotero 中保留主线标签，删除过细标签。

**缺 DOI**  
不要手动猜 DOI。打开 URL 或 PDF 后核验，再补到 Zotero。

**缺作者**  
不要填 anonymous。打开原文或 source 页面核验作者列表。

**重复论文**  
检查 DOI、arXiv ID、IACR ePrint ID、标题和 URL。必要时在 Zotero 中合并重复条目。

**出现本地路径或 secret**  
导出文件不应包含 `.env`、API key、SMTP 密码、Zotero key 或本地绝对路径。若发现，停止导入并检查导出代码。

## 7. QA 结论记录

每次手动导入测试后，建议复制 [docs/templates/zotero-import-audit.md](templates/zotero-import-audit.md)，记录：

- 测试日期；
- 使用的导出格式；
- 导入条目数；
- 字段完整性；
- 标签误报；
- collection 整理问题；
- 是否建议进入下一阶段。

## English Summary

This guide documents file-based Zotero manual import QA for the offline Zotero compatibility layer. Start with dry-run QA, export CSL-JSON / BibTeX / RIS, import manually into Zotero, then verify title, authors, year, URL, abstract, tags, collections, and notes. The current phase does not call Zotero APIs, does not create an XPI plugin, and does not upload any data.
