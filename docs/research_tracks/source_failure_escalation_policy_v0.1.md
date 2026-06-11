# Source Failure Escalation Policy v0.1

## Normal Observation

- keep Daily and Weekly active;
- record source health and artifacts;
- do not retry automatically.

## Degraded but Usable

- retain output with warnings;
- report failed sources and retryability;
- do not interpret enrichment failure as irrelevance.

## Source-Starved Warning

- label 0 records plus all-red sources as source-starved;
- run the connectivity probe manually;
- do not claim no relevant papers exist.

## Diagnostic Required

Use a one-time manual diagnostic when:

- starvation repeats;
- expected artifacts are missing;
- IACR latest repeatedly fails;
- weekly coverage remains stale after backfill;
- CI and local tests disagree.

Run Full Manual Quality only from a worktree where generated changes and code changes can be attributed safely.

## Forbidden Escalation

- no scheduler;
- no background retry loop;
- no automatic tag or release;
- no private workspace write;
- no secret output.
