# Phase 14G Codex Dry Run Log

## 1. Operator

- Operator: Codex.
- Model/tool: Codex desktop local workspace.
- Date/time: 2026-06-21 Asia/Shanghai.
- Working directory: `D:\Code\CodexProjects\lattice-crypto-daily-digest`.

## 2. Boundaries

- PhD_Application read/write: no.
- ResearchArtifacts read/write: no.
- ResearchOS write: no.
- `git add` / `git commit` / `git push` / `git tag`: no.
- Automation created: no.
- External LLM runtime added: no.
- Anti-bot bypass used: no.
- Ranking/source/taxonomy changes: no.

## 3. Commands Run

1. `git status -sb`
2. `python --version`
3. `python -m lattice_digest.workflow doctor`
4. `python -m lattice_digest.workflow status`
5. `python -c "import lattice_digest; print(lattice_digest.__version__)"`
6. `python -m lattice_digest.run --since 36h --output markdown,json --send none`
7. `python -m lattice_digest.workflow weekly --low-load --skip-hygiene`
8. `python -m lattice_digest.monthly_synthesis --month 2026-06`
9. `python scripts/probe_source_health.py --low-load`
10. `python scripts/verify_durable_artifacts.py --date 2026-06-15 --week 2026-W25 --month 2026-06`
11. `python scripts/export_reading_queue.py --latest`
12. `python scripts/export_obsidian_notes.py --latest`
13. `python scripts/audit_monthly_rationale_quality.py --latest`

Final validation commands are recorded in the main Phase 14G report.

## 4. Artifacts Generated

- Daily Markdown/JSON: `digests/2026-06-21.md`, `data/2026-06-21.json`.
- Weekly Markdown/JSON: dry-run planned `digests/weekly/2026-W25.md`, `data/weekly/2026-W25.json`; no weekly execute was run.
- Monthly Markdown/JSON: `digests/monthly/2026-06.md`, `data/monthly/2026-06.json`.
- Source-health audit/probe: terminal low-load probe output; latest ledger also reported by workflow status as `audits/source-health/2026-06-20.json`.
- Reading queue: `state/reading-queue.json`, `exports/reading-queue/*.md`.
- Obsidian export: `exports/obsidian-paper-notes/Papers/*.md`.
- Quality audit: monthly audit output for 2026-06.

## 5. Source Health

- arXiv: yellow/rate_limited in Daily run; probe classified 429 as `rate_limited`.
- DBLP: yellow/ssl_error in Daily run; probe classified as `ssl_failure` with TLS failure class.
- IACR: yellow in Daily because no candidate records; probe returned RSS feed successfully with 100 records.
- Semantic Scholar: red/rate_limited in Daily run; probe classified 429 as `rate_limited` and did not print the API key.
- OpenAlex: yellow/empty in Daily run; probe returned one low-load result.
- Crossref: green; Daily run produced candidate records and probe returned one result.

## 6. Radar Output Quality

- Recommendation rationale quality: monthly audit returned `monthly_rationale_quality_passed_with_limits`.
- Bilingual top-paper rationale: `bilingual_top_paper_rationale_present`.
- TODO_VERIFY present: no missing TODO_VERIFY findings.
- Keyword-only regression: passed.
- Reading action clarity: warning present; five sampled monthly papers had action/bucket mismatch.

## 7. Durable Artifact Status

Durable verifier returned `overall_status: verified` for:

- Daily 2026-06-15.
- Weekly 2026-W25.
- Monthly 2026-06.

## 8. Failures / Warnings

- Workspace was dirty before the drill and remains dirty.
- Daily source health is degraded: arXiv and Semantic Scholar rate-limited; DBLP TLS/SSL failure.
- Monthly audit passed with limits due to reading-action alignment warnings.

## 9. Next Recommended Operator

- Codex review required: yes for any code change or if generated artifacts are used as release evidence.
- Safe for DeepSeek-Claude rerun: yes, with full prompt and no code changes.
- Safe for Kimi Code rerun: yes, with full prompt and no code changes.

## 10. Final Status

`run_ok_with_degraded_sources`.

