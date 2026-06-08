# Phase 12M Three-Run Stability Check Log

生成日期：2026-06-08

# Run 1: Probe-only Health Check

- command: `python scripts\probe_source_connectivity.py`
- result: passed
- summary:
  - arxiv: 200 reachable
  - crossref: 200 reachable
  - dblp: TLS EOF, retryable
  - iacr_eprint: 200 reachable, parser parsed 100 records
  - openalex: 200 reachable
  - semantic_scholar: 200 reachable
- safe key observation:
  - `SEMANTIC_SCHOLAR_API_KEY` present=true, length=44
  - key value not printed

# Run 2: Manual Recovery Daily Run

- command: `python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources`
- result: passed
- summary:
  - skipped overwrite of `2026-06-08` because current report is already `local_codex/authoritative`
  - arxiv green final=5
  - crossref green final=1
  - dblp yellow retryable
  - iacr latest `cache_hit/100`
  - openalex yellow final=0
  - semantic_scholar yellow final=0

# Run 3: Weekly Handoff Replay

- requested command: `python scripts\generate_weekly_handoff.py --latest`
- status: missing command in repository
- working command: `scripts\run_weekly_handoff.bat`
- result: passed
- summary:
  - `2026-W23` packets=20
  - outputs written under `handoffs/weekly/`

# Interpretation

- current system is no longer all-red;
- daily module is degraded-but-usable, not source-starved;
- weekly handoff remains usable and non-empty;
- prompt/runbook text should reference actual working commands only.
