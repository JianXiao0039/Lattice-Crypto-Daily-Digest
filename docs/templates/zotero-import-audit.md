# Zotero Manual Import Audit

## 1. 基本信息

- Audit date:
- Tester:
- Repository revision:
- Export command:
- Import format tested:
  - [ ] CSL-JSON
  - [ ] BibTeX
  - [ ] RIS
- Zotero version:
- Operating system:

## 2. 导出文件检查

- Export directory:
- `zotero_items.json` exists:
- `items.csl.json` exists:
- `items.bib` exists:
- `items.ris` exists:
- `zotero_collections.json` exists:
- `export_report.md` exists:
- Files contain no API key / token / `.env` content:
- Files contain no unexpected local absolute path:

## 3. 导入数量

- Expected records:
- Imported records:
- Deduplicated records:
- Failed records:
- Notes:

## 4. 字段完整性

抽查至少 5 条高优先级论文。

| Field | Pass / Fail | Notes |
| --- | --- | --- |
| title |  |  |
| authors |  |  |
| year / date |  |  |
| URL |  |  |
| DOI |  |  |
| abstract |  |  |
| tags |  |  |
| notes / extra |  |  |

## 5. 标签质量

- `LC/Problem/LWE` / `LC/Problem/RLWE` / `LC/Problem/MLWE` 是否准确：
- `LC/Problem/SIS` / `LC/Problem/Module-SIS` / `LC/Problem/Ring-SIS` 是否准确：
- `LC/Attack/BKZ` / `LC/Attack/Hybrid` / `LC/Tool/G6K` / `LC/Tool/fplll` 是否准确：
- `LC/AI/AI4Lattice` 是否只出现在格密码相关 AI 论文：
- `LC/ResearchLine/Module-SIS-Chameleon-Hash` 是否准确：
- `LC/ResearchLine/PQC-Implementation-Security` 是否准确：
- 误报示例：
- 漏报示例：

## 6. Collection 整理

- High Priority:
- AI4Lattice:
- Lattice Reduction and Attacks:
- PQC Implementation Security:
- Lattice-Based Primitives:
- Weekly Reading Queue:
- Backfill Imported:

## 7. 问题与修复建议

- 缺 DOI:
- 缺作者:
- URL 不可靠:
- BibTeX key 冲突:
- RIS 导入异常:
- 标签过多:
- 重复论文:

## 8. 结论

- [ ] 可以作为 v0.2.0 手动 Zotero 导入流程
- [ ] 需要修复字段映射
- [ ] 需要修复标签规则
- [ ] 需要继续留在 RC 阶段

结论说明：

## English Summary

Use this template to record a file-based Zotero manual import QA run. Verify exported files, imported item counts, metadata completeness, LC tag quality, collection organization, and whether the workflow is ready for the next release candidate.
