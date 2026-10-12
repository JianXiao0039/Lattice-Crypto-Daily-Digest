# Verified report-pair repair

Owner-only manual repair, never a scheduled task. It performs no discovery and
does not write papers.db. Use the published independent runtime and explicit
canonical root. `REPORT_REPAIR` has its own reviewed command dependency closure;
the public Daily/Weekly/Monthly profiles remain separate.

Prepare a scratch pair under canonical `.ops/scratch` using the published renderer,
and a SHA-256 reviewed plan under `.ops/evidence`. Every plan entry records kind,
target, candidate root, original JSON/Markdown hashes and candidate JSON/Markdown
hashes. No wildcard and no force flag. Only existing pairs can be replaced.

`python -m lattice_digest.report_repair --plan <absolute.json> --plan-sha256 <sha>`
validates without promotion. Add `--execute` only after owner review. Each pair
has an exclusive creation lock, exact hash guards, structural/semantic/cross-day
and durable checks, byte-exact compressed originals, and a transaction journal.
Independent blocked items remain unchanged; successful items have exact receipts.

Daily raw source fields, identity, dates, provider health, historical window and
publication policy cannot change. Legacy source-window/event gaps stay explicit;
repairing a no-news assertion does not invent a publication ledger. Period data
must equal a rebuild from actual canonical Daily inputs; incomplete or degraded
coverage cannot be upgraded. October monthly output cannot be repaired as a
completed month while that month remains open.

Replacement is atomic per file, not a crash-atomic two-file transaction. Ordinary
I/O failures restore both original bytes using atomic replacements. A crash between
files is detectable by the retained journal and pair verifier; do not call an
interrupted transaction successful. Restore sealed originals from the journal's
gzip files, verify their hashes, and audit the pair before further publication.
