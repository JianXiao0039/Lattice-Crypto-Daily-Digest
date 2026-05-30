# Zotero Compatibility Layer

## 1. 这个兼容层解决什么问题

Zotero compatibility layer 把 `data/*.json` 中的 digest records 转换成 Zotero 生态可消费的离线文件，包括 Zotero editable JSON、CSL-JSON、BibTeX、RIS、collection tree 和中文导出报告。

它服务的目标是：把每日格密码论文雷达、Weekly Research Brief、Stable Library Export Layer 中的论文记录继续沉淀到 Zotero 文献库生态中，方便长期检索、引用、标签管理和后续 Zotero 插件原型开发。

本阶段只做离线导出，不联网，不调用 Zotero Web API，不创建 `.xpi` 插件，不上传任何数据。

## 2. 为什么当前不直接做 Zotero .xpi 插件

当前优先做兼容层，而不是直接做 Zotero 插件，原因是：

- Python core 已经负责论文采集、过滤、去重、排序和标签生成。
- Zotero 插件应作为前端适配器，不应重新实现抓取和 ranking。
- 稳定的 JSON / CSL / BibTeX / RIS 输出是未来插件的前置条件。
- 离线文件导入便于先验证字段映射、标签体系和 collection tree。
- 手动导入测试可以避免早期插件误写真实 Zotero 文献库。

## 3. 当前支持哪些导出格式

默认输出目录：

```text
exports/zotero/YYYY-MM-DD/
```

当前支持：

- `zotero_items.json`：未来 Zotero Web API 可参考的 editable JSON 风格。
- `items.csl.json`：CSL-JSON 风格，适合 Zotero / citation tool / downstream converter 兼容测试。
- `items.bib`：BibTeX 导出，使用 deterministic citation key。
- `items.ris`：RIS 导出，包含 `TY`、`TI`、`AU`、`PY`、`DO`、`UR`、`AB`、`KW`、`ER`。
- `zotero_collections.json`：建议的 Zotero collection tree，不包含真实 Zotero collection key。
- `export_report.md`：中文工程验收报告。

## 4. 如何本地运行

Windows PowerShell：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\export_zotero.ps1 -Days 7
```

指定日期范围：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\export_zotero.ps1 -FromDate 2026-05-25 -ToDate 2026-05-31
```

直接调用 Python CLI：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.zotero_compat --days 7 --formats zotero-json,csl-json,bibtex,ris --output-dir exports/zotero
```

## 5. 如何 dry-run

dry-run 只打印将要导出的条目数量和目标路径，不写文件：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\export_zotero.ps1 -Days 7 -DryRun
```

如果希望空输入直接失败，可加：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\export_zotero.ps1 -Days 7 -DryRun -FailOnEmpty
```

## 6. 如何导入 Zotero

推荐先用文件手动导入测试：

1. 运行 `scripts\export_zotero.ps1`。
2. 打开 Zotero。
3. 选择 `File -> Import`。
4. 优先测试 `items.csl.json` 或 `items.bib`。
5. 导入后人工核对 title、authors、year、URL、DOI、abstract、tags 和 extra。
6. 根据 `zotero_collections.json` 手动整理 collection tree。

真实 Zotero API push 留到下一阶段。当前阶段不会写入 Zotero 账号，也不会需要 Zotero API key。

## 7. tag taxonomy 说明

Zotero tags 使用稳定的 `LC/*` 前缀体系，便于长期过滤：

- `LC/Problem/*`：LWE、RLWE、MLWE、SIS、Module-SIS、NTRU 等问题与假设。
- `LC/Primitive/*`：KEM、Signature、Commitment、Chameleon-Hash、ZK-Friendly-PQ。
- `LC/Scheme/*`：ML-KEM、ML-DSA、Kyber、Dilithium 等方案。
- `LC/Attack/*`：Primal、Dual、Hybrid、BKZ、LLL、Sieving、Enumeration。
- `LC/Tool/*`：G6K、fplll 等工具。
- `LC/AI/*`：AI4Lattice、Transformer、Swin、Mamba、Coordinate-Selection、Negative-Cyclic-Modeling。
- `LC/Implementation/*`：Constant-Time、Side-Channel、Fault-Attack。
- `LC/ResearchLine/*`：Module-SIS Chameleon Hash、AI4Lattice Hybrid Ranking、RLWE/MLWE Negative-Cyclic、PQC Implementation Security。
- `LC/Priority/*`：Must-Read、Should-Read、Skim、Stash。
- `LC/Source/*`：IACR ePrint、arXiv、Semantic Scholar、OpenAlex、Crossref、DBLP。
- `LC/Collector/*` 和 `LC/Quality/*`：区分 GitHub Actions provisional 与本地 authoritative backfill。

标签基于现有 `library_taxonomy.py` 与 digest record intelligence 生成，不调用 LLM，不编造论文结论。

## 8. collection mapping 说明

`zotero_collections.json` 给出建议 collection tree：

- Lattice Crypto Daily Digest
  - High Priority
  - AI4Lattice
  - Lattice Reduction and Attacks
  - PQC Implementation Security
  - Lattice-Based Primitives
  - Weekly Reading Queue
  - Backfill Imported

当前文件只描述建议结构，不包含真实 Zotero collection key，也不写入 Zotero 文献库。

## 9. 常见失败

**缺 DOI**  
很多 arXiv、IACR ePrint 或 metadata source 记录没有 DOI。导出时不会伪造 DOI，Zotero 中需要人工核验。

**缺作者**  
部分数据源可能缺作者字段。导出不会写 anonymous，Zotero 导入后需要人工补全。

**重复论文**  
导出层按 DOI、arXiv ID、ePrint ID、Semantic Scholar ID、title+author+year 和 URL fallback 去重。不同源字段差异较大时，仍建议人工检查。

**BibTeX key 冲突**  
key 使用 deterministic short hash 降低冲突概率；若 Zotero 或 LaTeX 工具链中已有同名 key，可人工重命名。

**Zotero 字段不兼容**  
不同 Zotero 版本对 itemType 和字段支持略有差异。当前优先生成保守字段，并把 digest 信息放入 `extra`。

## 10. 下一阶段路线

- Phase 7D：Zotero Web API dry-run and optional push。
- Phase 7E：Zotero collection sync。
- Phase 8：Zotero `.xpi` plugin prototype。

## English Summary

The Zotero Compatibility Layer converts existing digest JSON records into offline Zotero-friendly files: editable-style Zotero JSON, CSL JSON, BibTeX, RIS, suggested collection trees, and an engineering export report. It reuses the stable library export schema and `library_taxonomy.py`; it does not fetch papers, call Zotero APIs, upload data, or create a Zotero plugin.

Recommended workflow: export records, manually import CSL JSON or BibTeX into Zotero, verify metadata and tags, then use the results to guide future Zotero Web API and plugin work.
