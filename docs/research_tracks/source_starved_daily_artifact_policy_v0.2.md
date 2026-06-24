# Source-Starved Daily Artifact Policy v0.2

## Core Rule

`0 records + all-red effective source health = source-starved`.

A source-starved run is an operationally valid diagnostic artifact, but it is not a successful paper-discovery result.

## Required Artifact Behavior

- Write `data/YYYY/daily/YYYY-MM-DD.json` when JSON output is requested.
- Write `digests/YYYY/daily/YYYY-MM-DD.md` when Markdown output is requested.
- Preserve per-source status, error type, retryability, IACR latest status, and Semantic Scholar availability.
- State that no relevant-paper conclusion can be drawn from source-starved input.
- Recommend only manual recovery.

## Date-Targeted Recovery

`--date YYYY-MM-DD` follows the same source-starved rule. Exact-date filtering must not suppress output creation when the filtered record set is empty.

## Interpretation Matrix

| Records | Source health | Interpretation |
|---:|---|---|
| greater than 0 | mixed/healthy | usable result with recorded caveats |
| 0 | at least one healthy source | empty discovery result; inspect coverage and filters |
| 0 | all red/unavailable | source-starved; not evidence of no relevant papers |

## IACR and Semantic Scholar

- IACR `failed/0` must be classified as network, parser, guard, cache, or genuine zero-record state when evidence exists.
- Semantic Scholar enrichment failure means metadata enrichment is unavailable; it does not lower paper relevance by itself.
- Never print API key values.

## Non-Actions

- No automatic retry loop.
- No scheduler or background service.
- No silent empty success.
- No automatic Git staging, commit, push, or tag.
- No private workspace writes.

