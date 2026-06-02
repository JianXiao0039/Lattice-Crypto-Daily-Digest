# Phase 9S.2: Source Latest Report Enumerator and Cross-Source Ingestion Audit

Date: 2026-06-02

## Executive summary

Phase 9S.2 adds a minimal manual latest-source recovery path for IACR ePrint and a cross-source ingestion capability audit. It does not change taxonomy semantics, ranking thresholds, section classifier semantics, negative keyword semantics, query expansion semantics, generated daily / weekly artifacts, or `papers.db`.

The concrete recovery target is IACR ePrint reports:

- `2026/1115`
- `2026/1116`
- `2026/1117`
- `2026/1118`

The key strong positive remains:

- `2026/1117`: `On the Secrecy of the Encapsulation Coin in ML-KEM`

The IACR parser can extract this record from RSS/latest feed content, and the existing ranker keeps it as an A-level ML-KEM / PQC paper. The fix is source-ingestion reliability, not taxonomy or ranking.

## Why latest enumeration is needed

Broad query search is useful but not sufficient for high-confidence daily monitoring. A source-native latest feed gives a bounded list of newly visible source records. For IACR ePrint, that means RSS/latest report enumeration should be checked directly, because a newly posted ePrint may not be found reliably by broad query terms on the same day.

The latest-source path is still manual and bounded:

- no scheduler;
- no Windows Task Scheduler;
- no cron;
- no background service;
- no startup task;
- no tight retry loop;
- no high-frequency crawling.

## IACR 2026/1115-1118 diagnosis

Phase 9S found:

- the four ePrint pages were reachable;
- the IACR RSS feed contained the four target IDs;
- `parse_iacr_feed` could parse them;
- `2026/1117` ranked as A / 100 when it entered the ranker;
- local artifacts missed them because IACR source health was red or skipped by the same-day attempt guard.

Phase 9S.1 separated failed attempts from successful caches. Phase 9S.2 adds `--include-latest-sources` so a user can explicitly request manual latest-source recovery.

## Specific 2026/1117 ML-KEM recovery logic

The IACR source still reads `https://eprint.iacr.org/rss/rss.xml`.

Successful fetch behavior:

1. Fetch RSS once.
2. Cache the successful XML for the UTC day.
3. Later same-day runs reuse the successful cache.

Failed attempt behavior:

1. A failed network attempt leaves an attempt marker.
2. Normal runs still skip after that marker to preserve polite behavior.
3. A manual recovery run can use `--retry-failed-sources` and `--include-latest-sources`.
4. Successful manual recovery writes the normal successful cache.

The known sample `2026/1117` is covered by tests:

- the title is preserved exactly;
- the ePrint ID is parsed;
- it can enter the existing ranker;
- the existing ranker classifies it as A / 100.

## Cross-source latest coverage table

| Source | Capability | Mechanism | Manual flag | Notes |
| --- | --- | --- | --- | --- |
| `iacr_eprint` | supports latest enumeration | IACR ePrint RSS latest feed | `--include-latest-sources` | Successful RSS fetches are cached politely; failed same-day attempts require an explicit manual retry/latest flag. |
| `arxiv` | query search only | arXiv configured query API | none | Configured query groups improve recall, but this is not a source-native latest enumerator. |
| `dblp` | query search only | DBLP configured query API | none | Useful for publication metadata and venue records, but sparse for daily windows. |
| `openalex` | query search only | OpenAlex configured query API | none | Useful metadata source; latest-feed coverage is not wired in this project. |
| `crossref` | query search only | Crossref configured query API | none | Supplemental DOI / publication metadata source; not a latest-feed enumerator here. |
| `semantic_scholar` | query search only | Semantic Scholar Graph API paper search | none | Optional API key may be read from `SEMANTIC_SCHOLAR_API_KEY`; no key is required for tests and no key should be logged. |
| `crypto_venues` | unsupported / unknown | disabled source | none | Disabled HTML fallback; not part of normal ingestion. |
| `security_venues` | unsupported / unknown | disabled source | none | Disabled HTML fallback; not part of normal ingestion. |
| `ai_venues_low_priority` | unsupported / unknown | disabled source | none | Disabled HTML fallback; not part of normal ingestion. |

## Which sources are latest-feed capable

Currently latest-feed capable:

- IACR ePrint through RSS/latest report enumeration.

This is the only source-native latest enumerator implemented in Phase 9S.2.

## Which sources are query-only

Configured query-based sources:

- arXiv
- DBLP
- OpenAlex
- Crossref
- Semantic Scholar

These sources can still be valuable, but broad search terms are not a full substitute for source-native latest enumeration.

## Which sources are enrichment-only

No source is converted into enrichment-only behavior by this phase.

Semantic Scholar remains an existing configured source and may also be useful as optional metadata cross-check. If used with an API key, the key must come from `SEMANTIC_SCHOLAR_API_KEY`; never print or commit the key.

## Manual commands

PowerShell:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

cmd:

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

If this command writes daily JSON, Markdown, source health audit files, or `papers.db`, inspect them manually and do not stage generated artifacts unless explicitly publishing digest artifacts.

## Politeness / rate-limit rules

- Successful IACR RSS fetches remain cached for the day.
- A failed same-day attempt is not retried by normal runs.
- Manual latest recovery requires an explicit flag.
- No automatic future retry is configured.
- Do not loop the recovery command.
- Do not run it from a scheduler, startup task, watcher, cron job, or background service.

## Source health visibility

IACR source health now includes latest-feed diagnostics where available:

- `latest_feed_status`
- `latest_feed_reachable`
- `latest_feed_parsed`
- `latest_feed_records`
- `latest_feed_missing_expected`
- `latest_feed_skipped_by_guard`

Console source health also shows the latest-feed status and record count.

## What was intentionally not changed

This phase intentionally does not change:

- taxonomy config;
- negative keywords;
- ranking thresholds;
- ranking weights;
- section classifier semantics;
- query expansion semantics;
- daily digest section generation;
- weekly synthesis behavior;
- generated daily or weekly digest files;
- generated JSON files;
- `papers.db`;
- Semantic Scholar API-key requirements;
- GitHub Actions scheduling;
- local scheduled automation.

## Validation commands

Use only project-scoped pytest and Python 3.14.2:

```powershell
python --version
python -m pytest tests\test_iacr_parser.py --basetemp=.pytest_tmp
scripts\run_project_tests.bat
python scripts\check_release_hygiene.py
git diff --check
python -m lattice_digest.workflow doctor
git status -sb
```

Do not run bare `python -m pytest`.
