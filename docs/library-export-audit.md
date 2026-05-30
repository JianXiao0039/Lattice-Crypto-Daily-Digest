# Library Export Quality Audit

## 中文说明

## 1. 为什么需要审计

Phase 7A 的 Stable Library Export Layer 已经能从 `data/*.json` 生成 CSL JSON、BibTeX、RIS、`library-items.json`、`zotero-tags.json` 和 `import-report.md`。但“能导出”不等于“适合长期导入 Zotero”。字段完整性、标签误报、Zotero note 可读性、AI4Lattice 与普通 AI 的边界、LWE/RLWE/MLWE 和 SIS/Module-SIS/Ring-SIS 的区分，都需要独立审计。

Phase 7B 的审计层只读取已有导出或已有 digest JSON，不运行 fetcher，不修改 `data/`、`digests/` 或 `papers.db`，也不改变 ranking / source health / 日报结构。

## 2. 推荐审计流程

推荐流程：

1. 生成 library export：

   ```powershell
   Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
   powershell.exe -ExecutionPolicy Bypass -File scripts\export_library.ps1 -Days 7
   ```

2. 运行 audit：

   ```powershell
   powershell.exe -ExecutionPolicy Bypass -File scripts\audit_library_export.ps1 -Input exports\library\library-items.json
   ```

3. 阅读 `audits/library-export/tag-quality-report.md`。
4. 阅读 `audits/library-export/field-quality-report.md`。
5. 用 CSL JSON 手动导入 Zotero。
6. 用 BibTeX / RIS 做对照。
7. 人工确认高优先级论文的 title、authors、year、DOI、URL、tags 和 note。
8. 将稳定条目回流到 Obsidian / Idea Bank / Paper Plan。

如果只想检查命令是否可运行：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\audit_library_export.ps1 -Input exports\library\library-items.json -DryRun
```

## 3. 格密码标签误报重点

审计时重点看这些边界：

- **LWE / RLWE / MLWE 区分**：不能因为出现 LWE 就自动打 RLWE 或 MLWE。
- **SIS / Module-SIS / Ring-SIS 区分**：SIS-only 不能自动升级为 Module-SIS。
- **AI4Lattice 不等于普通 AI**：Transformer、GNN、Mamba、CNN、MLP 等只有在和 lattice / LWE / SIS / BKZ / cryptanalysis 共现时，才应成为 AI4Lattice。
- **hybrid / dual / primal 需要 lattice attack 上下文**：普通英文语境里的 dual、primal、hybrid 不应误打 attack tag。
- **FHE 应用论文不等于 lattice attack**：CKKS / BFV / BGV / TFHE 应归为 FHE 或 primitive；除非明确 attack/security/parameter/implementation，不应成为 lattice cryptanalysis。
- **toy benchmark 不等于真实安全结论**：toy、small parameters、synthetic benchmark 只能作为实验线索，不能当作真实参数攻击结论。
- **chameleon hash / commitment / hash-and-sign 不应混淆**：Module-SIS chameleon hash、SIS commitment 和 hash-and-sign 签名组件的接口、安全目标和后续 artifact 路线不同。

## 4. Zotero 手动导入检查

导入 Zotero 后，请逐项检查：

- title 是否完整。
- authors 是否缺失或顺序异常。
- year / date 是否合理。
- DOI 是否存在、是否重复。
- URL 是否能打开。
- abstract 是否缺失。
- tags 是否过多，是否需要人工精简。
- note 是否包含 source、reading priority、score、why it matters 和 research tags。
- 高优先级论文是否需要进入专门 collection。

推荐先导入 `library-items.csl.json`，再用 `library-items.bib` 和 `library-items.ris` 对照字段损失情况。

## 5. 建议 Zotero collection 结构

可先建立这些 collection：

- Lattice Problems
- Lattice Reduction
- Lattice Cryptanalysis
- PQC Standards
- Lattice Primitives
- Implementation Security
- AI4Lattice
- FHE
- ZK/PQ Privacy
- Short-Term Paper Candidates
- PhD Long-Term Direction

导入后不要盲目保留全部自动标签。自动标签用于初筛，长期文献库仍需要人工整理。

## 6. Zotero 标签治理建议

- 优先保留研究主线标签，例如 LWE/RLWE/MLWE、Module-SIS、BKZ、AI4Lattice、ML-KEM/ML-DSA implementation security。
- 对 `TODO_VERIFY` 标签要人工核验，不要把它当作已验证结论。
- 对 AI4Lattice 标签要检查是否真的有 lattice / LWE / RLWE / MLWE / SIS / BKZ / cryptanalysis 上下文。
- 对 FHE 标签要区分 theory、implementation、application、attack / security / parameter。
- 对 Module-SIS / Chameleon Hash 标签要重点保留，因为它服务短期论文 artifact 与 chameleon hash / commitment 主线。
- 对 hash-and-sign、commitment、chameleon hash 这三类原语不要混在同一个 Zotero collection 中。

## 7. 未来 Zotero XPI 插件前置条件

在开发 Zotero XPI 插件前，至少需要稳定完成：

- stable library export schema；
- taxonomy quality fixture；
- tag-quality audit；
- field-quality audit；
- manual Zotero import workflow；
- 高风险标签误报控制；
- import report 与人工检查清单。

插件应消费 `library-items.json`，而不是直接负责论文抓取、ranking 或 source health。

## English Summary

The Library Export Quality Audit validates the output of the stable library export layer before manual Zotero import or future Zotero plugin development. It checks field completeness, tag distribution, likely taxonomy false positives, and Zotero import readiness.

Recommended workflow:

1. Generate `exports/library/` with `scripts/export_library.ps1`.
2. Run `scripts/audit_library_export.ps1`.
3. Review `tag-quality-report.md` and `field-quality-report.md`.
4. Import CSL JSON into Zotero manually.
5. Compare BibTeX and RIS imports.
6. Manually clean tags and collections.

The audit does not fetch papers, mutate digest outputs, update `papers.db`, or change ranking/source-health logic. It is a quality-control layer for Zotero-ready export and future plugin work.
