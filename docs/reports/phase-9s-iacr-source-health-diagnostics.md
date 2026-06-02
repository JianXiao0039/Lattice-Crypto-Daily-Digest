# Phase 9S: IACR ePrint Source Health Recovery and Missed Paper Diagnostics

Date: 2026-06-02

## 1. Scope

This is a one-time manual diagnostic report for the IACR ePrint source health issue observed around recent ePrint reports:

- https://eprint.iacr.org/2026/1115
- https://eprint.iacr.org/2026/1116
- https://eprint.iacr.org/2026/1117
- https://eprint.iacr.org/2026/1118

The main paper of concern is:

- 2026/1117, "On the Secrecy of the Encapsulation Coin in ML-KEM"

This report does not modify fetcher behavior, ranking thresholds, taxonomy configuration, section classifier semantics, generated daily or weekly digest files, generated JSON files, or `papers.db`.

## 2. Environment Check

Required Python version:

```powershell
python --version
```

Observed:

```text
Python 3.14.2
```

The version requirement is satisfied.

## 3. Local Artifact Search

Searched recent local daily and weekly artifacts for these terms:

```text
2026/1115
2026/1116
2026/1117
2026/1118
ML-KEM
Encapsulation Coin
AuditPay
Proof-of-Work Consensus
Wide-Block Memory Encryption
```

Checked files:

- `data/2026-05-31.json`
- `data/2026-06-01.json`
- `data/2026-06-02.json`
- `data/weekly/2026-W22.json`
- `data/weekly/2026-W23.json`
- `digests/2026-05-31.md`
- `digests/2026-06-01.md`
- `digests/2026-06-02.md`
- `digests/weekly/2026-W22.md`
- `digests/weekly/2026-W23.md`

Findings:

- No local artifact contains `2026/1115`, `2026/1116`, `2026/1117`, or `2026/1118`.
- No local artifact contains the specific title fragment `Encapsulation Coin`.
- Generic `ML-KEM` mentions exist in headings, query metadata, or older records, but not for ePrint `2026/1117`.

Conclusion: the specific ML-KEM ePrint report was not included in the generated artifacts.

## 4. Source Health Evidence

Recent local JSON artifacts show IACR ePrint source health degradation.

### 2026-05-31

Metadata:

- `target_date`: `2026-05-31`
- `run_date`: `2026-06-02`
- `since_window`: `36h`
- `coverage_start`: `2026-05-30T04:00:00+00:00`
- `coverage_end`: `2026-05-31T16:00:00+00:00`
- `total_records`: `0`
- `collector`: `local_codex`
- `quality_status`: `authoritative_backfill`
- `run_mode`: `backfill`

IACR status:

- `status`: `red`
- `raw_count`: `0`
- `final_count`: `0`
- `error_type`: `warning`
- `error_message`: `IACR ePrint already requested today; skipped to honor max once per day`
- `retryable`: `true`

### 2026-06-01

Metadata:

- `target_date`: `2026-06-01`
- `run_date`: `2026-06-02`
- `since_window`: `36h`
- `coverage_start`: `2026-05-31T04:00:00+00:00`
- `coverage_end`: `2026-06-01T16:00:00+00:00`
- `total_records`: `0`
- `collector`: `local_codex`
- `quality_status`: `authoritative_backfill`
- `run_mode`: `backfill`

IACR status:

- `status`: `red`
- `raw_count`: `0`
- `final_count`: `0`
- `error_type`: `warning`
- `error_message`: `IACR ePrint already requested today; skipped to honor max once per day`
- `retryable`: `true`

### 2026-06-02

Metadata:

- `target_date`: `2026-06-02`
- `run_date`: `2026-06-02`
- `since_window`: `7d`
- `coverage_start`: `2026-05-26T08:46:46.662679+00:00`
- `coverage_end`: `2026-06-02T08:46:46.662679+00:00`
- `total_records`: `0`
- `collector`: `local_codex`
- `quality_status`: `authoritative`
- `run_mode`: `daily`

IACR status:

- `status`: `red`
- `raw_count`: `0`
- `final_count`: `0`
- `error_type`: `warning`
- `error_message`: `iacr_eprint: skipped https://eprint.iacr.org/rss/rss.xml after 1 attempt(s): request error URLError`
- `retryable`: `true`

Conclusion: the relevant local runs did not have successful IACR candidate ingestion. Backfill runs were blocked by the once-per-UTC-day attempt guard, and the 7d daily run observed an IACR RSS request error.

## 5. IACR Fetcher Behavior

Relevant implementation:

- `config/sources.yaml`
- `src/lattice_digest/sources/iacr.py`
- `src/lattice_digest/sources/base.py`
- `src/lattice_digest/run.py`

Current IACR source configuration:

- Source name: `iacr_eprint`
- URL: `https://eprint.iacr.org/rss/rss.xml`
- `max_per_day`: `1`
- `max_requests_per_day`: `1`
- `cache_ttl_hours`: `24`
- `once_per_utc_day`: `true`

Current fetch behavior:

1. The source fetches only the IACR RSS feed configured at `https://eprint.iacr.org/rss/rss.xml`.
2. It writes `cache/iacr_eprint_YYYY-MM-DD.attempt` before the network request.
3. If the request fails and no RSS cache file is written, later runs on the same UTC day see the attempt file and skip IACR completely.
4. If a cache XML file exists for the UTC day, later runs reuse that cache instead of re-fetching.
5. The parser supports RSS `<item>` and Atom `<entry>` records.
6. The parser extracts ePrint IDs such as `2026/1117` from links or titles.
7. Date filtering uses `update_date` first, then `publication_date`.
8. Records without a parsed publication or update date fail the source-level since filter.

Important diagnostic point:

- The once-per-day guard is intentional, but its current behavior can turn an early failed request into a same-day IACR blackout for later daily or backfill runs.

## 6. Narrow Network Probe

The following narrow probes were run manually. They did not generate daily reports and did not write `data/`, `digests/`, or `papers.db`.

### ePrint page probe

Command shape:

```powershell
python - <<in-memory urllib script for only 2026/1115..1118>
```

Observed:

```text
2026/1115    HTTP 200    The Fact of the MATTER: Efficient Hardware Accelerators for Wide-Block Memory Encryption
2026/1116    HTTP 200    Fast Difficulty Adjustment in Proof-of-Work Consensus
2026/1117    HTTP 200    On the Secrecy of the Encapsulation Coin in ML-KEM
2026/1118    HTTP 200    AuditPay: Anonymous Payments with Controlled Oversight
```

Conclusion: the four ePrint pages are reachable from the local environment at diagnostic time.

### RSS probe

Command shape:

```powershell
python - <<in-memory urllib script for https://eprint.iacr.org/rss/rss.xml>
```

Observed:

```text
RSS HTTP 200 bytes=222636 items=100
2026/1115    in_rss=True
2026/1116    in_rss=True
2026/1117    in_rss=True
2026/1118    in_rss=True
```

Conclusion: the current IACR RSS feed contains the four target IDs. The project source design can see them when the RSS request succeeds.

## 7. Parser and Date Filter Probe

Using the current `parse_iacr_feed` implementation against the current RSS feed:

```text
parsed_records=100
2026/1118    AuditPay: Anonymous Payments with Controlled Oversight    2026-05-31    within_36h_from_2026-05-31T16Z=False    within_7d_from_2026-05-26T0846Z=True
2026/1117    On the Secrecy of the Encapsulation Coin in ML-KEM         2026-05-31    within_36h_from_2026-05-31T16Z=False    within_7d_from_2026-05-26T0846Z=True
2026/1116    Fast Difficulty Adjustment in Proof-of-Work Consensus      2026-05-31    within_36h_from_2026-05-31T16Z=False    within_7d_from_2026-05-26T0846Z=True
2026/1115    The Fact of the MATTER: Efficient Hardware Accelerators... 2026-05-31    within_36h_from_2026-05-31T16Z=False    within_7d_from_2026-05-26T0846Z=True
```

Interpretation:

- The parser can extract the target records.
- The four target records have `publication_date = 2026-05-31` and no update date.
- A broad 7d run should include them at source-date-filter level when IACR RSS succeeds.
- A precise 36h target-date backfill can miss them depending on the computed coverage window and date-only UTC interpretation.

## 8. Ranking Probe

Using the current ranker and taxonomy on the four parsed records:

```text
2026/1115    D    35     The Fact of the MATTER: Efficient Hardware Accelerators for Wide-Block Memory Encryption
2026/1116    D    35     Fast Difficulty Adjustment in Proof-of-Work Consensus
2026/1117    A    100    On the Secrecy of the Encapsulation Coin in ML-KEM
2026/1118    D    35     AuditPay: Anonymous Payments with Controlled Oversight
included_non_D_after_dedup 1
```

Interpretation:

- `2026/1117` is correctly recognized as an A-class ML-KEM paper if it reaches the ranker.
- The current ranking/taxonomy logic is not the reason `2026/1117` was absent.
- The other three papers are filtered as D-class by the current lattice-cryptography relevance policy.

## 9. Root Cause Assessment

Most likely cause for missing `2026/1117`:

1. IACR ePrint source ingestion failed or was skipped during the relevant local runs.
2. The once-per-UTC-day attempt guard prevented later same-day runs or backfill runs from retrying IACR after a failed attempt.
3. The backfill runs for `2026-05-31` and `2026-06-01` show IACR `red` with `raw_count = 0`, so no target ePrint record could enter normalization, ranking, or digest output.
4. The current RSS feed includes `2026/1117`, and the current parser/ranker would include it as A-class if fetched successfully.

Secondary contributing factor:

- Date-only IACR RSS records are interpreted as UTC midnight. This can make narrow target-date backfill windows behave counterintuitively. The 7d window is safer for source recovery.

Not the primary cause:

- Taxonomy rules.
- Negative keyword filtering.
- Ranking threshold.
- Section assignment.

## 10. Recommended Recovery Actions

Recommended manual recovery, without changing taxonomy or ranking:

1. Clear or bypass only the failed IACR same-day attempt state before a manual recovery run, instead of changing ranking or filters.
2. Run a manual broad-window digest or a targeted source recovery path that allows IACR to fetch again.
3. Prefer a 7d or 30d recovery window for IACR source recovery, because ePrint RSS records can carry date-only metadata.
4. If implementing a code fix later, consider making the once-per-day guard distinguish successful cache files from failed attempts:
   - successful RSS fetch: keep 24h cache behavior;
   - failed RSS fetch: allow a limited manual retry or allow backfill mode to retry;
   - do not remove the IACR politeness constraint entirely.
5. Consider adding a narrow missed-ePrint diagnostic command in a future phase:
   - input: explicit ePrint IDs;
   - output: parser/ranker/source-health diagnostic only;
   - no full digest regeneration unless explicitly requested.

## 11. What Was Not Changed

This phase did not modify:

- fetcher behavior;
- ranking behavior;
- source health semantics;
- taxonomy configuration;
- negative keywords;
- section classifier rules;
- daily digest files;
- weekly digest files;
- generated JSON files;
- `papers.db`;
- scheduled automation;
- Task Scheduler, cron, background services, startup tasks;
- git staging, commits, pushes, or tags.

## 12. Validation

Validation commands requested for this phase:

```powershell
python --version
scripts\run_project_tests.bat
python scripts\check_release_hygiene.py
git diff --check
python -m lattice_digest.workflow doctor
git status -sb
```

Results are recorded in the final Phase 9S response.
