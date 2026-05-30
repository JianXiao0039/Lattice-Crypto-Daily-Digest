# Changelog

## v0.2.0-rc1 - 2026-05-30

### Release type

- Release Candidate.
- Not a stable v0.2.0 release.
- Focus: Stable Library Export Layer.

### Added

- Stable Library Export Layer.
- `library-items.json` export.
- CSL JSON export.
- BibTeX export.
- RIS export.
- `zotero-tags.json` export.
- `import-report.md`.
- `schemas/library-item.schema.json`.
- Deep lattice cryptography taxonomy.
- Zotero-ready export workflow.
- `docs/library-interop.md`.
- `scripts/export_library.ps1`.

### Research taxonomy coverage

- LWE / RLWE / MLWE.
- SIS / Module-SIS / Ring-SIS.
- NTRU.
- BKZ / LLL / G6K / fplll / lattice reduction.
- primal / dual / hybrid attacks.
- ML-KEM / Kyber.
- ML-DSA / Dilithium.
- Falcon / FN-DSA.
- Module-SIS chameleon hash.
- commitments.
- FHE / CKKS / BFV / BGV / TFHE.
- ZK-friendly post-quantum privacy primitives.
- implementation security / side-channel / fault / constant-time.
- AI4Lattice / Swin-guided coordinate selection / negative-cyclic modeling / hybrid ranking.

### Known limitations

- Zotero XPI plugin is not included.
- Zotero manual import audit is not yet completed.
- Taxonomy false-positive audit is planned for Phase 7B.
- CSL JSON / BibTeX / RIS export quality depends on upstream metadata completeness.
- DOI / author / abstract may be missing for some sources.
- This is a research triage tool, not a complete bibliographic database.
- External API rate limits still apply.

### Upgrade notes

- Run `python -m pytest` after pulling.
- Use `scripts/export_library.ps1` for local export.
- Do not commit `exports/library/` unless intentionally publishing export artifacts.
- Keep API keys in `.env` or GitHub Secrets.

### Next

- Phase 7B: Library Export Quality Audit & Zotero Manual Import Test.
- Phase 7C: Static Curation Dashboard.
- Phase 8: Local API / Zotero Plugin preparation.

### English summary

v0.2.0-rc1 is a Library Interoperability Release Candidate, not the stable v0.2.0 release. It packages the Stable Library Export Layer introduced in Phase 7A: stable library items, CSL JSON, BibTeX, RIS, Zotero tag mapping, import reports, schema documentation, and deep lattice-cryptography taxonomy. The release is intended to validate file-based Zotero-ready export before manual import audit, taxonomy confusion audit, dashboard work, local API work, and a future Zotero XPI plugin.

## v0.1.0 - 2026-05-30

### 中文说明

v0.1.0 是本项目的第一个公开研究自动化版本。它面向格密码、后量子密码和 AI-assisted lattice cryptanalysis 研究，提供从每日论文情报、source health 诊断、本地权威回填，到 Idea Bank、Paper Plan 和 Research Artifact scaffold 的端到端研究工作流。

主要能力：

- Daily lattice crypto digest：生成格密码论文中文日报和结构化 JSON。
- Source Health red/yellow/green diagnostics：记录 IACR ePrint、arXiv、DBLP、OpenAlex、Crossref、Semantic Scholar 等 source 的健康状态。
- Local authoritative backfill：支持本地 Windows PowerShell 对 GitHub provisional 日报做权威回填。
- GitHub Actions provisional digest：云端定时生成 provisional 日报并可选发送邮件。
- Obsidian paper card export：研究工作流中保留 Obsidian 论文卡片导出接口；请以当前分支实际脚本为准。
- Weekly Research Brief：研究工作流中保留周报聚合方向；请以当前分支实际脚本为准。
- Idea Bank：从 digest 记录中沉淀长期研究 idea。
- Idea to Paper Plan：把高价值 idea 升级为保守、可验证的 Paper Plan。
- Research artifact scaffold：从 Paper Plan 生成可开工的研究 artifact 骨架。
- Deployment hardening / public deployment guide：新增公开部署指南、环境自检脚本和 release 文档。

Known limitations：

- External APIs may rate-limit.
- GitHub Actions source coverage may be weaker than local Codex/manual runs.
- Semantic Scholar works best with API key.
- This tool is research triage, not a formal bibliographic database.
- TODO: choose license.

Upgrade notes：

- Keep secrets in `.env` or GitHub Secrets.
- Do not commit `data/*.json`, `digests/*.md`, `papers.db` unless intentionally publishing digest artifacts.
- Do not mix generated research outputs such as `exports/`, `audits/`, or `research_artifacts/` into feature commits.

### English summary

v0.1.0 is the first public research automation release of Lattice Crypto Daily Digest. It provides daily lattice-cryptography paper monitoring, source health diagnostics, local authoritative backfill, GitHub Actions provisional reports, Idea Bank generation, Idea-to-Paper-Plan upgrades, research artifact scaffolding, and public deployment documentation.

This release is intended for research triage and workflow automation. It does not provide formal bibliographic guarantees, cryptographic security judgments, experimental results, or paper-writing automation.
