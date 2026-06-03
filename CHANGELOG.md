# Changelog

## v0.3.3 - 2026-06-03

### Release type

- Maintenance release.
- IACR recovery, optional metadata enrichment, and research report quality polish.
- Does not change fetcher semantics, ranking thresholds, taxonomy semantics, source health semantics, section classifier semantics, query expansion, negative keywords, daily / weekly workflow behavior, reading queue, Obsidian scaffold, research progress, Zotero export, release hygiene semantics, or workflow behavior.

### Added / fixed since v0.3.2

- IACR failed attempt manual retry recovery so failed source attempts do not permanently block later manual recovery retries.
- IACR latest/RSS source recovery and latest-feed observability through `latest_feed_*` source health fields.
- Cross-source latest/query/enrichment audit documenting latest-feed, query-only, enrichment-only, and unknown source roles.
- Source query coverage audit for source coverage review and manual troubleshooting.
- Optional Semantic Scholar metadata enrichment for existing papers.
- Semantic Scholar key safety through `SEMANTIC_SCHOLAR_API_KEY`; no real API key is stored, logged, printed, or committed.
- Research report quality polish for daily, weekly, artifact, and advisor/progress reports.
- Daily report `lattice/PQC anchor evidence` for high-priority papers.
- Manual quality-first workflow remains supported.

### Stable guarantees

- No scheduled automation is added: no Windows Task Scheduler integration, cron job, startup task, background service, watcher, daemon, or automatic scheduled local run.
- No ranking threshold changes are included.
- No taxonomy semantic changes are included.
- Semantic Scholar citation metadata is advisory only and never overrides A/B/C/D ranking.
- Low-load / no-network / dry-run modes remain fallback modes for reduced pressure, diagnostics, and safety checks; they do not replace manual quality-first generation.

### Upgrade notes

- Pull latest `main`.
- Run `python -m pytest tests\test_release_v033_docs.py --basetemp=.pytest_tmp`.
- Run `python -m pytest tests --basetemp=.pytest_tmp` or `scripts\run_project_tests.bat`.
- Run `python scripts\check_release_hygiene.py`.
- Run `git diff --check`.
- Keep `exports/`, `audits/`, `research_artifacts/`, `.pytest_tmp/`, `__pycache__/`, `state/reading-queue.json`, local test `data/*.json`, `digests/*.md`, `papers.db`, `.env`, and local caches out of feature commits.

### English summary

v0.3.3 is a maintenance release after v0.3.2. It packages IACR failed attempt manual retry recovery, IACR latest/RSS source recovery and latest-feed observability, cross-source latest/query/enrichment audit, source query coverage audit, optional Semantic Scholar metadata enrichment with `SEMANTIC_SCHOLAR_API_KEY` safety, and research report quality polish including daily `lattice/PQC anchor evidence` for high-priority papers.

No scheduled automation is added. There is no Windows Task Scheduler integration, cron job, startup task, background service, watcher, daemon, or automatic scheduled local run. No ranking threshold changes and no taxonomy semantic changes are included. Semantic Scholar citation metadata remains advisory only.

## v0.3.2 - 2026-06-01

### Release type

- Documentation and maintenance release.
- No product feature expansion.
- Does not change fetcher, ranking, source health semantics, section classifier, daily digest generation, weekly synthesis, reading queue, Obsidian scaffold, research progress, Zotero export, release hygiene semantics, or workflow behavior.

### Added / fixed since v0.3.1

- Documentation polish for the stable manual low-load research workflow.
- `docs/index.md` documentation map for manual operations, recovery, pilot feedback, troubleshooting, and release notes.
- README safe manual quickstart with manual-only workflow guidance.
- Command safety matrix covering read-only status, write behavior, network behavior, low-load support, and notes.
- One-week manual pilot docs for manual acceptance review.
- Pilot feedback triage docs, summary template, and fix prioritization rules.
- Maintenance cleanup / warning reduction from Phase 9C where applicable.

### Stable guarantees

- Workflow command center remains manual-only.
- `daily`, `weekly`, and `full` workflows still use dry-run default behavior.
- Writing workflow runs still require explicit `--execute`.
- Low-load mode still requires explicit `--low-load`.
- No-network/offline usage still requires explicit `--no-network` or `--offline` where supported.
- No scheduled automation is added: no Windows Task Scheduler integration, cron job, startup task, background service, watcher, daemon, or automatic scheduled local run.
- Generated artifacts must not be committed by default.
- Reading queue manual statuses and local state remain user-owned.

### Upgrade notes

- Pull latest `main`.
- Run `python -m pytest tests\test_release_v032_docs.py`.
- Run `python -m pytest`.
- Run `python scripts\check_release_hygiene.py`.
- Run `git diff --check`.
- Keep `exports/`, `audits/`, `research_artifacts/`, `.pytest_tmp/`, `__pycache__/`, `state/reading-queue.json`, local test `data/*.json`, `digests/*.md`, `papers.db`, `.env`, and local caches out of feature commits.

### English summary

v0.3.2 is a documentation and maintenance release after v0.3.1. It packages documentation polish, the `docs/index.md` documentation map, the README safe manual quickstart, command safety matrix, one-week manual pilot docs, pilot feedback triage docs, and maintenance cleanup / warning reduction where applicable. It preserves the manual-only workflow, dry-run default, explicit low-load mode, no-network/offline usage, and adds no scheduled automation.

## v0.3.1 - 2026-06-01

### Release type

- Patch release.
- Documentation and validation hardening release.
- Does not change fetcher, ranking, source health semantics, section classifier, daily digest generation, weekly synthesis, reading queue, Obsidian scaffold, research progress, or workflow behavior.

### Added / fixed since v0.3.0

- Deterministic E2E workflow acceptance suite for the manual low-load research workflow chain.
- Stale release test hotfix so v0.2.x and v0.3.0 tests remain archival and do not pin the current version.
- Manual operations runbook for dry-run default, low-load mode, no-network/offline usage, and read-only versus write-file commands.
- Recovery playbook covering cleanup, reading queue backup, `papers.db` recovery, Windows SQLite file locks, CI triage, and `tzdata` / `ZoneInfo` issues.
- Artifact retention policy documenting generated artifacts that must not be committed by default.
- Troubleshooting docs for shell differences, workflow execution, SQLite locks, timezone data, CI failures, and generated artifact hygiene.

### Stable guarantees

- Workflow command center remains manual-only.
- `daily`, `weekly`, and `full` workflows still default to dry-run.
- Writing workflow runs still require explicit `--execute`.
- No Windows Task Scheduler integration, cron job, startup task, background service, watcher, or automatic scheduled local run is added.
- Generated artifacts remain ignored and should not be staged by default.

### Upgrade notes

- Pull latest `main`.
- Run `python -m pytest`.
- Run `python scripts\check_release_hygiene.py`.
- Run `git diff --check`.
- Keep `exports/`, `audits/`, `state/reading-queue.json`, `data/*.json`, `digests/*.md`, `papers.db`, `.env`, and local caches out of feature commits.

### English summary

v0.3.1 is a patch release for validation and operator documentation. It adds deterministic E2E workflow acceptance tests, fixes stale archival release tests after v0.3.0, and documents manual operations, recovery, artifact retention, and troubleshooting. It does not add scheduled automation or change workflow, fetcher, ranking, source health, daily digest, weekly synthesis, reading queue, Obsidian scaffold, or research progress behavior.

## v0.3.0 - 2026-06-01

### Release type

- Stabilization release.
- Research workflow orchestration release.
- Does not change fetcher, ranking, source health semantics, daily digest sections, or weekly synthesis semantics.

### Added since v0.2.0

- CI and release hygiene checks for Windows / Ubuntu validation.
- Runtime Source Health Ledger under `audits/source-health/`.
- Ranking explainability in JSON and Markdown digest output.
- Research-oriented daily digest section assignment.
- Golden examples for section classifier calibration.
- Weekly Research Synthesis from existing daily JSON.
- Research Artifact Export Pack.
- Reading Queue Workflow and Review Status Tracker.
- Obsidian Paper Note Scaffold.
- Advisor Update and Research Progress Log.
- Workflow Command Center with `daily`, `weekly`, `full`, `status`, and `doctor`.
- Manual low-load workflow profiles for laptop-friendly user-triggered runs.

### Stable guarantees

- Workflows remain user-triggered.
- `daily`, `weekly`, and `full` workflows default to dry-run.
- Writing workflow runs require `--execute`.
- Obsidian note generation still requires explicit `--generate-notes`.
- `status` and `doctor` are read-only.
- No Windows Task Scheduler integration, cron job, startup task, background daemon, or automatic scheduled local run is added.
- Generated workflow manifests remain under ignored `exports/workflow-runs/`.

### Known limitations

- External academic APIs can still rate-limit, timeout, or return incomplete metadata.
- GitHub Actions provisional coverage may remain weaker than local authoritative backfill.
- Workflow command center coordinates existing modules; it does not replace careful manual review.
- Low-load mode reduces workflow pressure only when explicitly requested.
- This project is research triage and workflow automation, not a formal bibliographic authority database.

### Upgrade notes

- Pull latest `main`.
- Run `python -m pytest`.
- Run `python scripts/check_release_hygiene.py`.
- Run `python -m lattice_digest.workflow doctor`.
- Use `python -m lattice_digest.workflow weekly --low-load --skip-hygiene` for a safe manual dry-run.
- Do not commit `exports/`, `audits/`, `state/reading-queue.json`, `data/*.json`, `digests/*.md`, or `papers.db` unless intentionally publishing digest artifacts.

### English summary

v0.3.0 is a stabilization release for the research workflow layer. It packages CI/release hygiene, source health ledger persistence, ranking explainability, research-oriented digest sections, weekly synthesis, artifact export, reading queue tracking, Obsidian note scaffolding, advisor progress logs, the workflow command center, and manual low-load profiles. It does not add scheduled local automation or change fetcher, ranking, section classifier, source health, daily digest, weekly synthesis, reading queue, Obsidian scaffold, research progress, or workflow semantics.

## v0.2.0 - 2026-05-30

### Release type

- Stable release.
- Research library interoperability release.
- Supersedes v0.2.0-rc1.

### Added

- Stable Library Export Layer.
- `library-items.json` export.
- CSL JSON export.
- BibTeX export.
- RIS export.
- `zotero-tags.json` export.
- `import-report.md`.
- Library item schema.
- Deep lattice cryptography taxonomy.
- Library Export Quality Audit.
- Field quality report.
- Taxonomy confusion report.
- Zotero Compatibility Layer.
- Zotero-style JSON export.
- Zotero manual import QA workflow.
- Zotero import checklist.
- Obsidian / Zotero / BibTeX / RIS / CSL JSON interoperability docs.

### Research taxonomy coverage

- LWE / RLWE / MLWE.
- SIS / Module-SIS / Ring-SIS.
- NTRU.
- BKZ / LLL / G6K / fplll / lattice reduction.
- primal / dual / hybrid attacks.
- sparse LWE / secret recovery.
- ML-KEM / Kyber.
- ML-DSA / Dilithium.
- Falcon / FN-DSA.
- Module-SIS chameleon hash.
- commitments.
- lattice-based ZK / ZK-friendly PQ privacy primitives.
- FHE / CKKS / BFV / BGV / TFHE.
- implementation security / side-channel / fault / constant-time.
- AI4Lattice / Swin-guided coordinate selection / negative-cyclic modeling / hybrid ranking.

### Stable guarantees

- File-based export is stable.
- CSL JSON / BibTeX / RIS output contracts are stable enough for manual import.
- Zotero compatibility layer is offline-only.
- Library item schema is versioned.
- Taxonomy is deterministic.
- Audit reports are reproducible from local data.

### Known limitations

- Zotero XPI plugin is not included.
- Zotero Web API sync is not included.
- Automatic PDF attachment import is not included.
- Metadata quality depends on upstream sources.
- DOI / authors / abstract may be missing.
- Some taxonomy labels may require manual verification.
- This tool is for research triage, not a complete bibliographic authority database.
- GitHub Actions provisional output may be less complete than local authoritative backfill.

### Upgrade notes

- Pull latest `main`.
- Run `python -m pytest`.
- Run `scripts\export_library.ps1` for library export.
- Run `scripts\audit_library_export.ps1` for quality audit.
- Run Zotero compatibility dry-run before manual import.
- Do not commit `exports/` or `audits/`.
- Keep secrets in `.env` or GitHub Secrets.

### Next

- Phase 8A: Zotero Web API dry-run client.
- Phase 8B: Optional Zotero Web API push with explicit user confirmation.
- Phase 8C: Zotero collection sync.
- Phase 9: Zotero XPI plugin prototype.
- Longer-term: Research dashboard and advisor-facing research intelligence portal.

### English summary

v0.2.0 is the stable Research Library Interoperability release. It stabilizes file-based library export, deep lattice-cryptography taxonomy, library export audit, offline Zotero compatibility, and Zotero manual import QA. It does not include Zotero Web API sync, automatic PDF attachment import, or a Zotero XPI plugin.

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
