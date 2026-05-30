# Library Interoperability Layer

## 中文说明

## 1. 目的

Library Interoperability Layer 是 `lattice-crypto-daily-digest` 的稳定文献库导出层，用于连接每日 digest、Zotero、Obsidian、BibTeX、RIS、CSL JSON，以及未来可能开发的 Zotero XPI 插件。

这一层只读取已有的 `data/*.json`，不会重新抓取论文，不会修改 `digests/`、`papers.db` 或 source health。它把 digest records 转换成稳定的 `library item`，保留题名、作者、来源、URL、摘要、研究优先级、格密码标签、Zotero tags、Obsidian 双链提示和质量警告。

## 2. 为什么不直接做 Zotero 插件

Zotero 插件应当是前端适配器，而不是论文抓取、过滤和 ranking 的核心。当前项目的 Python core 已经负责采集、去重、过滤、研究优先级排序和 source health 诊断。稳定 export schema 是 Zotero XPI 插件之前的必要前置条件：

- Python core 输出稳定、可测试的 library item。
- Zotero / Obsidian / dashboard / local API 只消费这个稳定格式。
- 即使没有插件，也可以通过 CSL JSON、BibTeX 或 RIS 导入 Zotero。
- 插件未来可以专注 UI、collection、tag 同步和 note 跳转，而不是重复实现抓取逻辑。

## 3. 支持格式

导出命令：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\export_library.ps1 -Days 7
```

支持输出：

- `library-items.json`：完整稳定交换格式。
- `library-items.csl.json`：Zotero-ready CSL JSON。
- `library-items.bib`：保守 BibTeX。
- `library-items.ris`：基础 RIS。
- `zotero-tags.json`：Zotero tag mapping。
- `import-report.md`：中文导入报告。

也可以 dry-run：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\export_library.ps1 -Days 7 -DryRun
```

## 4. 格密码标签体系

导出层复用 `src/lattice_digest/library_taxonomy.py`，用 deterministic keyword rules 生成多层标签，不调用 LLM，也不编造论文结论。

标签类别：

- **Lattice Problems**：LWE、RLWE、MLWE、SIS、Module-SIS、Ring-SIS、NTRU、SVP、CVP、BDD、q-ary lattice、module lattice 等。
- **Lattice Reduction**：LLL、BKZ、G6K、fplll、sieving、enumeration、pruning、GSA、lattice estimator 等。
- **Lattice Cryptanalysis**：primal attack、dual attack、hybrid attack、secret recovery、distinguisher、BKW、failure oracle 等。
- **PQC Schemes**：ML-KEM、Kyber、ML-DSA、Dilithium、Falcon、FN-DSA、FrodoKEM、Saber、NIST PQC 等。
- **Primitives**：commitment、Module-SIS commitment、chameleon hash、FHE、CKKS、BFV、BGV、TFHE、ZK-friendly primitives 等。
- **Implementation Security**：constant-time、side-channel、fault attack、masking、NTT、production audit、benchmark、artifact evaluation 等。
- **AI4Lattice**：Transformer LWE、neural lattice reduction、Swin-guided coordinate selection、learned pruning、BKZ parameter prediction、candidate ranking 等。普通 AI/Transformer 论文如果没有 lattice/LWE/BKZ/cryptanalysis 语境，不会被打成 AI4Lattice。
- **Research Workflow**：Must Read、Recommended Read、Skim、Archive、Paper Idea、Experiment Candidate、TODO_VERIFY 等。

## 5. Zotero 导入流程

推荐流程：

1. 运行 `scripts\export_library.ps1` 生成 `exports/library/`。
2. 打开 Zotero。
3. 选择 `File -> Import`。
4. 优先选择 `library-items.csl.json`；如果兼容性不佳，再尝试 `library-items.bib` 或 `library-items.ris`。
5. 导入后检查作者、DOI、URL、tags 和 note。
6. 手动整理 collection，例如 `LWE Attacks`、`Module-SIS Primitives`、`PQC Implementation Security`。

导出层不会编造 DOI 或作者。缺失字段会在 `export_warnings` 和 `import-report.md` 中标记。

## 6. Obsidian 联动

`zotero_tags` 和 `obsidian_links` 用途不同：

- `zotero_tags` 是扁平、短、适合 Zotero 过滤和 collection 整理的标签。
- `obsidian_links` 是概念双链提示，例如 `[[LWE]]`、`[[Module-SIS]]`、`[[BKZ]]`、`[[AI4Lattice]]`。

Obsidian paper cards 仍由已有 Obsidian 导出流程生成。Library Export 只负责文献库互操作，不覆盖用户手写笔记。

## 7. 未来 Zotero XPI 插件路线

建议路线：

- v0.2.0：stable library export。
- v0.3.0：static dashboard。
- v0.4.0：local API。
- v0.5.0：Zotero plugin MVP。

插件不应直接负责论文抓取、ranking 或 source health。它应消费 `library-items.json`，负责 Zotero 内部的 tag、collection、note 和外部链接同步。

## 8. 常见问题

**为什么没有 DOI？**  
很多 arXiv、IACR ePrint 或元数据源候选没有 DOI。导出层不会编造 DOI，会写入 `missing_doi`。

**为什么作者缺失？**  
部分源返回摘要或标题但缺作者。导出层使用空数组，并在质量警告中写 `missing_authors`。

**为什么 Zotero 标签很多？**  
标签来自研究主线、格密码问题、PQC 方案、攻击、实现安全和 workflow 标签。导入 Zotero 后可以人工精简。

**为什么某篇论文被打 TODO_VERIFY？**  
通常说明缺 DOI、缺作者、缺摘要、缺 URL、缺日期或标签不足，需要人工核验。

**为什么普通 AI 论文没有打 AI4Lattice？**  
AI4Lattice 只有在 AI/ML 与 lattice、LWE、SIS、BKZ、cryptanalysis 等密码语境共现时才触发，避免把泛 AI 误报为格密码研究。

**为什么 FHE 应用论文优先级较低？**  
泛 FHE 应用不等于格密码攻击、参数安全或实现安全。只有和 lattice parameters、security estimation、implementation、attack 或 bootstrapping cost 明确相关时，才更适合作为高优先级研究线索。

## English Summary

The Library Interoperability Layer converts existing digest JSON files into stable library items for Zotero, Obsidian, CSL JSON, BibTeX, RIS, local dashboards, and future Zotero plugins. It does not fetch papers, modify digests, update `papers.db`, or change ranking logic.

The layer provides:

- `library-items.json` as the stable exchange format.
- Zotero-ready CSL JSON.
- Conservative BibTeX and RIS exports.
- `zotero-tags.json` for tag mapping.
- `import-report.md` for quality warnings and import guidance.

The taxonomy is deterministic and lattice-cryptography focused. It distinguishes LWE/RLWE/MLWE, SIS/Module-SIS/Ring-SIS, BKZ/lattice reduction, PQC schemes, lattice primitives, implementation security, and AI4Lattice. Generic AI papers do not receive AI4Lattice tags unless they explicitly connect to lattice cryptography, LWE, SIS, BKZ, or cryptanalysis.

Future Zotero integration should treat the plugin as a frontend adapter. The Python core remains responsible for collection, filtering, ranking, source health, and export schema stability.
