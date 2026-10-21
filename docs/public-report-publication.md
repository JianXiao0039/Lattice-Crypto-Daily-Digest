# Public literature report contract v1

This contract governs reviewed safe publication. Code remains on main; only sanitized literature outputs enter public-digests. The P1 operator authorization permits reviewed fast-forward releases and this exact publication stage; it does not permit history rewriting or new schedulers.

## Authority and gates

main remains source-code authority. Local public_daily/public_weekly/public_monthly retain the published-runtime preflight and separate canonical root. They are internal operational entry names; their complete canonical artifacts are not a public export contract.

The cloud candidate uses cloud_daily, public sources only, and PROVISIONAL_PUBLIC. It must not assert local runtime authority, open Gmail, load a local env file, or import a local canonical database. CI retains the full Ubuntu/Windows suite. The Daily workflow uses a bounded independent smoke gate, a 35 minute job budget, one concurrency group, and cancel-in-progress false.

CODE_CI_GATE validates code. PRODUCTION_REPORT_GATE validates explicit period identity, canonical paths, UTF-8/JSON, versioned event policies, generation/hash pairing, stored and recomputed QA, writer state, and source limitations. PUBLIC_PRIVACY_GATE constructs a new public representation. REMOTE_PUBLICATION_GATE requires separate human approval and independent readback.

GitHub run created_at is the verified event clock. Scheduled resolution uses the preceding nominal 01:17 UTC occurrence with a maximum 12 hour delay. Long or ambiguous delays fail with TARGET_DATE_RECOVERY_REQUIRED. Manual targets are explicit and bounded to 36 hours. GitHub-hosted scheduling is not exact. Actual collection time and the fixed cutoff are recorded separately; late startup does not move the scientific window.

## Public representation

schemas/public-report.schema.json defines public-literature-v1. Each output is constructed from public title, public author names, reviewed identifier URLs, source-grounded topic vocabulary and verified event dates. Fixed Chinese guides distinguish E2 metadata from E3 title/abstract evidence. Neither level establishes a verified proof, benchmark or security claim.

Canonical Markdown is never copied. Canonical JSON, full abstracts, PDF text, papers.db, Gmail fields, execution paths, query dumps, research hypotheses, ideas, queues and advisor notes never enter the public tree. Unknown root/record extensions and arbitrary renderer prose fail closed. URL routes, Unicode-normalized privacy scans, payload bounds and redirect checks are additional defenses.

The reviewed source routes in v1 are arXiv abstract identifiers, IACR ePrint identifiers and DOI identifiers. Historical HTTP identifiers on these exact official hosts are upgraded to HTTPS before validation; query parameters, authentication, ports and unknown hosts still fail. The deployed deduplicator may join corroborating sources using the exact comma-space contract; every member must independently belong to the reviewed public adapter set. Unknown adapters and mailbox composites remain blocked. Other public sources require a reviewed adapter; they fail closed in v1. Public-source checks establish traceability to canonical source evidence, not independent full-text peer review or a guarantee that upstream metadata is correct.

## Isolated public branch

The public-digests branch starts from an empty isolated publication tree and a parentless first commit. It must not be created by copying main. Every subsequent report update is an ordinary fast-forward commit.

Exact paths:

```
daily/YYYY/YYYY-MM-DD.json
daily/YYYY/YYYY-MM-DD.md
weekly/ISO_YEAR/ISO_YEAR-Www.json
weekly/ISO_YEAR/ISO_YEAR-Www.md
monthly/YYYY/YYYY-MM.json
monthly/YYYY/YYYY-MM.md
index.md
manifest.json
```

Prepare a create-only candidate with python -m lattice_digest.public_report, supplying --root, --type, --period and --output. Independently review its JSON, Markdown, manifest and hashes. An interrupted candidate is ineligible. Inspecting the full tree rejects extra files, symlinks, path traversal and byte mismatches.

Only a separately authorized invocation of public_publisher may publish one reviewed report. Exact staging happens in a new temporary Git repository. A complete Git commit and a fast-forward ref update are the pair publication transaction; two working-tree files alone are not crash-atomic. The tool reconciles at most three concurrent advances, preserves other verified reports, never forces a ref update, and reads remote bytes back independently. Remote failure after an accepted push may leave a committed remote report and must be investigated before retry.

Live GitHub authentication is a separate explicit opt-in: --use-gh-credentials configures an installed gh auth git-credential helper only in the temporary publisher repository, after publication approval. Tokens never enter the remote URL, command arguments, public files or diagnostics. On Windows, --use-windows-credentials explicitly uses Git Credential Manager with interactive prompts disabled, only inside the temporary Git repository. Neither mode reads credentials into public files or command arguments.

Quality precedence is VERIFIED_AUTHORITATIVE > VALID_DEGRADED_AUTHORITATIVE > PROVISIONAL_PUBLIC. Coverage remains a separate field. Equal-authority changed content is blocked pending a reviewed version policy. An authority upgrade is a new auditable Git commit preserving the former version in ordinary history. Source generation and public generation remain distinct.

The existing manual_publish_to_github.bat remains a source-code helper; it must not publish report candidates or the canonical database. daily.yml generates and verifies a provisional candidate in a read-only job. A separate contents:write job downloads that sanitized artifact, validates the complete tree again, publishes through the exact-tree publisher and independently fetches remote bytes. Cloud output that is superseded by a higher-authority report produces an explicit verified no-op. The original ci.yml remains the full Windows/Linux code gate.

## Historical reports

scripts/index_public_eligible.py builds a read-only eligibility index using independent QA and the public projection. It exports no canonical JSON and performs no publication. Every historical batch requires independent preview/privacy review. No bulk upload of the archival pairs is authorized.

For 2026-08-22, 2026-09-11, 2026-09-19, 2026-09-25, 2026-09-27 and 2026-10-17, preserve incomplete status. Missing generation/publication QA blocks export; source failure must never be interpreted as no news. Preserve original artifacts and hash ledgers.

Tracked files are not automatically safe. Adding .gitignore or deleting a file in a later commit does not remove public history. Any actual sensitive exposure requires separately approved remediation; this phase does not rewrite history or delete evidence.

## Historical event evidence

The period gate independently rebuilds current period views. Current-schema event contributions still require full durable Daily QA. Controlled pre-policy Daily pairs may contribute only as DERIVED_HISTORICAL_EVENT_CANDIDATE after pair hashes, generation, date, controlled source QA, independent semantic replay and prior-identity checks pass. The public report then remains PROVISIONAL_PUBLIC and displays the reconstruction caveat per entry. entry_count counts listed items; event_count counts only verified current-schema events; historical_candidate_count counts reconstructed candidates separately. Candidates never inflate the verified-event count. This does not synthesize missing original-time observations or invent current-schema runtime provenance. Noncontributing legacy dates are explicitly listed as unverified inputs; malformed or mismatched byte pairs fail closed. The period pair itself must be freshly generated through the official published runtime, with current durable QA. Canonical originals are preserved.

## Existing local task stage

Only the three existing Daily/Weekly/Monthly automations may invoke the optional post-canonical stage. Keep their names, status and Asia/Singapore recurrence. After actual canonical production and QA, run from the clean published runtime with its normal isolated import/root configuration:

```
python -m lattice_digest.public_delivery --type daily --period YYYY-MM-DD --approve-reviewed-publication --use-windows-credentials
python -m lattice_digest.public_delivery --type weekly --period ISO_YEAR-Www --approve-reviewed-publication --use-windows-credentials
python -m lattice_digest.public_delivery --type monthly --period YYYY-MM --approve-reviewed-publication --use-windows-credentials
```

PUBLIC_DELIVERY has its own reviewed runtime dependency closure and live-remote preflight. Successful delivery records CANONICAL_GENERATED, CANONICAL_QA_VERIFIED, PUBLIC_EXPORT_VERIFIED, PRIVACY_QA_VERIFIED, GITHUB_PUSH_VERIFIED and REMOTE_READBACK_VERIFIED only after corresponding evidence. A verified existing no-op records its actual status and existing remote commit. Git unavailability records PUBLISH_PENDING and retains the verified sanitized candidate locally. It does not edit or delete canonical reports. --retry-pending retries at most three pending periods of the requested report type during the existing task execution or an explicitly resumed manual run. No daemon, service, extra schedule or unsafe force bypass is installed. Invalid canonical/privacy inputs block before publication; stale writer locks require inspection.

Manual E2E and configuration readback do not establish future scheduled delivery. A later actual scheduler receipt is required separately for each of Daily, Weekly and Monthly.

Cloud console diagnostics expose bounded counts and fixed gate reasons, not raw HTTP/query warning text. Raw source runtime details stay in the isolated canonical execution tree and are never part of public reports.
