# Phase 12K Source Health Recovery and Retry Policy Hardening

生成日期：2026-06-07

本报告属于公开 source-health / retry-policy hardening。它不包含 target PI email、SoP draft、PI-specific application note、funding strategy、personal PhD narrative、private application tracker 或 private application material。

# Executive Summary

Phase 12K hardens manual source-health recovery policy after Phase 12J identified source-starved daily artifacts and degraded source health.

Problem addressed:

- latest daily digest had 0 records;
- all configured external sources were red in source health;
- failures were retryable warnings or rate-limit/server-style source issues;
- IACR latest recovery could be blocked by a same-day failed-attempt marker;
- Semantic Scholar enrichment was unavailable in weekly artifacts.

What was hardened:

- source connectivity probe now reports a normalized `failure_class`;
- manual failed-source recovery scripts were added;
- source retry policy, IACR latest recovery policy, Semantic Scholar recovery policy, and source-starved digest policy were documented;
- source-starved empty digest/handoff interpretation is explicit.

Code changed only in the diagnostic script and its tests:

- `scripts/probe_source_connectivity.py`
- `tests/test_probe_source_connectivity.py`

Scripts added:

- `scripts/recover_failed_sources_manual.bat`
- `scripts/recover_failed_sources_manual.ps1`

No ranking, taxonomy, query expansion, negative keyword, section classifier, source relevance scoring, or source ingestion semantics were changed. Retry behavior remains manual-only.

# Input Evidence Used

| Input | Status | How used | Limitation |
| --- | --- | --- | --- |
| Phase 12J pilot report | available | Source-starved digest and handoff context | Report-level evidence |
| Phase 12J diagnostics report | available | Probe results and IACR / Semantic Scholar findings | Point-in-time connectivity |
| Weekly handoff pilot log | available | Packet counts and source-starved interpretation | Generated output depends on weekly JSON |
| Source recovery runbook v0.1 | available | Baseline manual recovery guidance | Needed more policy separation |
| `scripts/probe_source_connectivity.py` | available | Hardened with `failure_class` | Diagnostic-only script |
| `tests/test_probe_source_connectivity.py` | available | Extended classification tests | No network dependency |
| `src/lattice_digest/sources/base.py` | available | Reviewed source health fields and retryable status | Not modified |
| `src/lattice_digest/sources/iacr.py` | available | Reviewed cache hit / failed attempt / manual retry states | Not modified |
| `src/lattice_digest/run.py` | available | Confirmed `--retry-failed-sources` and `--include-latest-sources` | Not modified |
| `config/sources.yaml` | available | Confirmed source endpoints | Not modified |
| latest weekly JSON/Markdown | available | Handoff context | Not modified by policy docs |

# Failure Classification

| Source | Observed failure | Likely class | Retryable? | Manual recovery path | TODO_VERIFY |
| --- | --- | --- | ---:| --- | --- |
| arxiv | red/yellow warnings, rate limit, timeout in artifacts; probe reachable | rate limit / timeout / unknown URLError | yes when timeout/rate-limit | retry manually after network stabilizes | exact cause of red warning on latest daily |
| crossref | red warning in latest daily; probe reachable | unknown URLError or transient HTTP/network issue | yes if retryable warning | retry manual run after probe is green | whether source filters also removed records |
| dblp | server_error / HTTP 500; probe returned HTTP 500 | HTTP status / source-side server error | yes | retry later; do not treat as parser/taxonomy bug | whether DBLP query-specific or endpoint-wide |
| iacr_eprint | red warning, failed/0, same-day attempt marker without XML cache | failed attempt guard / unknown URLError | yes via explicit manual retry | `--retry-failed-sources --include-latest-sources` | whether manual recovery produces same-day cache |
| openalex | red/yellow warning in artifacts; probe reachable | unknown URLError / transient source issue | yes if warning/timeout | retry manually after probe | whether larger query volume triggers rate behavior |
| semantic_scholar | red/rate-limit in artifacts; probe reachable with key present | rate limit / advisory enrichment unavailable | yes for rate-limit; no for invalid key until fixed | check key presence, retry manually, keep advisory-only | key validity/quota without printing key |

Failure class vocabulary used by the probe:

- `dns`
- `tls`
- `proxy`
- `timeout`
- `http_status`
- `rate_limit`
- `api_key_or_auth`
- `parser`
- `unknown_url_error`
- `reachable`

# Retry Policy

Normal run behavior:

- configured sources are queried according to existing source semantics;
- source failures are recorded in source health and warnings;
- external source failures should not crash the overall digest unless local code fails;
- successful cache reuse remains polite and should not be bypassed.

Failed attempt guard behavior:

- IACR writes an attempt marker before fetching;
- if the fetch fails, the attempt marker remains without an XML cache;
- normal same-day runs can skip IACR to avoid uncontrolled repeated requests;
- skipped source health must be treated as source-starved risk.

Explicit manual retry behavior:

- use `--retry-failed-sources` when a failed attempt marker exists and a manual recovery is intended;
- use `--include-latest-sources` when source-native latest/RSS recovery should be included;
- do not schedule these flags;
- do not loop them.

Cache behavior:

- successful cache hit is not failure;
- successful cache reuse should remain allowed;
- failed attempt marker without cache is a recovery signal, not proof that the feed has no records.

Stop and check network when:

- several sources report DNS, TLS, proxy, or timeout failure;
- probe reports proxy-related clues;
- the same source remains rate-limited after manual wait;
- Semantic Scholar returns auth/forbidden.

# IACR Latest Recovery Policy

Endpoint:

- `https://eprint.iacr.org/rss/rss.xml`

States:

| State | Meaning | Action |
| --- | --- | --- |
| `cache_hit` | successful same-day XML cache exists | use cache; do not refetch |
| `fetched` | RSS fetched and parsed | normal success |
| `skipped_by_guard` | attempt marker exists and no manual retry flag | source-starved risk; consider manual retry if appropriate |
| `manual_retry` | explicit failed-source retry | review source health after run |
| `manual_latest_retry` | explicit latest-source recovery | review latest feed status and records |
| `failed` | network/request failed | run probe and inspect DNS/TLS/proxy/rate behavior |
| parser failure | feed reached but parse failed | fix parser only if reproducible fixture shows parser regression |
| failed/0 | failed or skipped and yielded zero records | not evidence that IACR has no relevant papers |

Manual command:

```powershell
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

# Semantic Scholar Enrichment Recovery Policy

Key handling:

- read only from `SEMANTIC_SCHOLAR_API_KEY`;
- report only present/non-empty and length;
- never print the value;
- never store the value in docs, logs, fixtures, reports, or README.

Interpretation:

- missing key: enrichment disabled/skipped; digest should still work;
- auth/forbidden: likely API-key or access issue; fix manually;
- 429/rate-limit: wait and retry manually;
- no candidate records: enrichment cannot run meaningfully;
- unavailable enrichment: missing advisory metadata, not relevance evidence.

Semantic Scholar citation metadata remains advisory and does not override A/B/C/D ranking.

# Source-Starved Digest Policy

0 records plus all-red sources means source-starved.

It does not mean:

- no relevant lattice/PQC papers exist;
- IACR has no relevant papers;
- Semantic Scholar found nothing relevant;
- weekly handoff should be trusted as complete.

Weekly handoff should be interpreted with the same caveat. If the weekly JSON has prior successful records, the handoff may be non-empty even when the latest daily run is source-starved.

# Code and Script Changes

| File | Change | Why | Risk | Tests |
| --- | --- | --- | --- | --- |
| `scripts/probe_source_connectivity.py` | added `failure_class` to classify DNS/TLS/proxy/timeout/HTTP/rate-limit/auth/parser/reachable states | clearer diagnostics | low; diagnostic output only | `tests/test_probe_source_connectivity.py` |
| `tests/test_probe_source_connectivity.py` | added failure-class assertions for DNS, TLS, rate-limit, auth, and server error | regression coverage | low | targeted and full test suite |
| `scripts/recover_failed_sources_manual.bat` | added manual recovery helper | single explicit manual entrypoint | medium: writes daily artifacts when manually run | validated manually |
| `scripts/recover_failed_sources_manual.ps1` | added PowerShell manual recovery helper | Windows operator convenience | medium: writes daily artifacts when manually run | command reviewed |

# Manual Recovery Commands

Probe only:

```powershell
python scripts\probe_source_connectivity.py
```

Manual recovery command:

```powershell
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

Manual recovery script:

```cmd
scripts\recover_failed_sources_manual.bat
```

PowerShell manual recovery script:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\recover_failed_sources_manual.ps1
```

Weekly handoff:

```cmd
scripts\run_weekly_handoff.bat
```

# Validation Results

| Check | Result |
| --- | --- |
| Python version | `Python 3.15.0b2` |
| Environment import check | passed: `pytest`, `pydantic`, and `ZoneInfo("Asia/Singapore")` import successfully |
| Workflow doctor | passed |
| Source connectivity probe | passed as a diagnostic command; arXiv, Crossref, IACR, OpenAlex, and Semantic Scholar were reachable; DBLP returned retryable HTTP 500 |
| Manual recovery command | passed via `scripts\recover_failed_sources_manual.bat`; daily artifact write was skipped because `2026-06-07` was already `local_codex/authoritative`; recovery source health showed IACR `manual_latest_retry/100`, IACR final=5, arXiv final=4, Crossref final=1 |
| IACR cache state after recovery | `cache\iacr_eprint_2026-06-07.xml` exists |
| Weekly handoff | passed via `scripts\run_weekly_handoff.bat`; generated `handoffs\weekly\2026-W23-handoff-packets.json` and `.md` with 20 packets |
| Targeted tests | passed: `8 passed` for `tests\test_probe_source_connectivity.py` |
| Project tests | passed: `423 passed` via `scripts\run_project_tests.bat` |
| Release hygiene | passed: `version ok: 0.3.3`; legacy tracked digest artifacts noted |
| `git diff --check` | passed with LF/CRLF working-copy warnings |
| `git status -sb` | shows Phase 12K files plus pre-existing generated artifacts and earlier Phase 12G/12H files |

# Boundary Confirmation

- No `git add`, `git commit`, `git push`, or `git tag` was executed.
- No Windows Task Scheduler task, cron job, background service, startup task, daemon, watcher, or automatic retry loop was created.
- No files were written into `D:\Code\CodexProjects\PhD_Application`.
- No files were written into `D:\ResearchArtifacts`.
- No ranking, taxonomy, query expansion, negative keyword, section classifier, source relevance scoring, source ingestion, source selection, or release hygiene semantics were changed.

# TODO_VERIFY

- local network / VPN / proxy stability;
- source-specific rate limits;
- Semantic Scholar key validity and quota without printing key;
- IACR feed stability after manual recovery;
- whether retry policy should be integrated into Full Manual Quality Run later;
- whether weekly handoff should include source-starved daily warning summaries.
