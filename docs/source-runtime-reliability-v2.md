# Source runtime reliability and continuity V2

Baseline: `2be145a8abc59545f55e7d32d76274444cc0302c` (locally verified evidence contract).
Scientific relevance, source expressions, taxonomy, score/label policy, and Query
Portfolio V3 activation are unchanged. Global/source budgets remain 600s/120s.

## Failure scope and partial preservation

HTTP 400/406 and invalid queries are QUERY_LOCAL and cannot increment a provider
circuit. Explicit FAMILY_LOCAL failures also cannot poison the provider. Transport
failures and provider outages retain bounded circuit protection. Repeated malformed
responses can open a circuit, with MALFORMED_RESPONSE visible rather than a false
successful zero-hit response. HTTP 429 is RATE_LIMIT_DEFERRED: at most one bounded
retry, honoring Retry-After when it fits the existing cap/deadline; after a terminal
429 all subsequent provider requests are deferred for the run. Partial results stay
available. TLS verification remains enabled and there is no credential rotation.

Malformed JSON diagnostics retain HTTP status, Content-Type, effective URL, and a
500-character maximum body preview. Full redirect history is UNKNOWN when urllib
does not expose it; effective URL is observable. HTML is never valid API metadata.
Health summaries retain source_roles, failure scopes, bounded request diagnostics,
and cache-hit counters. Selected record provenance continues to use the V2 mapper.

## Production family execution fairness

The 2026-10-06 journal contains 40 successful arXiv groups and four failed/skipped
groups: legacy_arxiv_34, 35, 36, 37. These are the four final groups in fixed order.
Total measured query wall time was 119.36 seconds, including 19.11 seconds for
critical groups. This supports a budget-tail starvation diagnosis for that run;
it does not establish all historical source failures have the same cause.

Round-robin visits active query families once before taking their next request.
The first family rotates by the source coverage-date ordinal. The full production
query set, expressions and identifiers are preserved. Rotation prevents the same
families being last every day; it does not guarantee all queries fit every budget.
Query attempt telemetry records duration, critical flag, failure scope and runtime
reason. Cache reuse is tested; the historical journal lacks cache-hit telemetry,
so historical cache effectiveness remains UNKNOWN. V3 remains shadow.

## Executable code identity and public automation

Every generated Daily records runtime_git_head, runtime_origin_main,
runtime_code_manifest_sha256, runtime_code_state, and
runtime_dirty_production_paths. The manifest covers source, configuration,
dependency manifests, workflows and the declared runtime launcher scripts.
Docs, tests, artifacts and ad-hoc audit scripts do not make executable code dirty.
Git text CRLF/LF differences are normalized for the manifest; missing tracked
production paths are explicit. Comparison uses observed local origin/main; it
performs no fetch and records that limitation.

States: PUBLISHED_CLEAN_RUNTIME, PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_FILES,
UNPUBLISHED_RUNTIME_CODE, UNKNOWN_RUNTIME_PROVENANCE. A different HEAD with only
documentation/artifact changes does not falsely imply unpublished code. Production
differences from origin/main or dirty production paths do. Canonical Daily execution
with known unpublished code fails closed before network/output; GitHub Actions or
explicit LATTICE_DIGEST_PUBLIC_AUTOMATION=1 also fails closed on UNKNOWN. Explicit
external scratch runs remain possible. No entire-repository cleanliness is required.

Scheduled metadata may be supplied through LATTICE_DIGEST_SCHEDULED_FOR (aware ISO
timestamp), LATTICE_DIGEST_TRIGGER_KIND (SCHEDULED/MANUAL/BACKFILL/RETRY), and
LATTICE_DIGEST_SCHEDULE_TIMEZONE. Absent/invalid values are UNKNOWN, never inferred
from the clock. run_started_at is actual. Artifact run_finished_at remains UNKNOWN
until publication; actual finish telemetry is in the referenced runtime journal's
RUN_FINISHED event after durable output and SQLite writes. No scheduler setting is
changed by this implementation.

## Read-only Daily continuity

`python -m lattice_digest.daily_continuity --data-dir PATH --start YYYY-MM-DD --end
YYYY-MM-DD` audits at most 62 days of canonical pairs without writes. It distinguishes
missing, error-only, malformed, one-sided and target-mismatched artifacts. A gap cause
requires evidence. Missing artifacts alone never establish a scheduler failure.
Weekly/Monthly input summaries expose additive continuity_status with UNKNOWN causes
unless separately established. Durable period verification preserves compatibility
with old artifacts lacking this telemetry; all original authority fields remain
strictly checked.

Read-only inspection of 2026-09-18 through 2026-10-06 finds 16 paired days and three
gaps (09-19, 09-25, 09-27). Their cause remains UNKNOWN: no error-only pair or tracked
artifact history establishes failure/removal, and local trigger history is not
complete enough to prove non-trigger. W40 is later complete.

The live app and TOML both retain ACTIVE daily 09:00 RRULE; the prompt specifies
Asia/Singapore. 09-26 has an automation thread at 00:59 local and a later 09:00
validation thread. Session provenance confirms automation origin but does not
identify manual invocation, nominal scheduling time, or catch-up behavior. Root
cause is UNKNOWN, so no timezone/schedule patch is justified. Recent 10-06 starts
around 09:05 local. Bounded live provider outcomes are separate external evidence,
not prerequisites for deterministic implementation success.
