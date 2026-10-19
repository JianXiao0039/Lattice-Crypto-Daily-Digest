# Explicit scope-policy compatibility

New reports use `scientific-publication-v3-v2`. Its scope evaluator contains the
V3 generic scientific-recall corrections. ABCD score thresholds, temporal rules,
stable identities and event deduplication retain their prior contracts.

`scientific-publication-p0-v1` reports are verified using the exact original
`scientific_scope.py` from published commit
`44da1e505c8a67ad28e8e98dcee554e91a8d7bec`, retained as
`scientific_scope_v1.py`. Its normalized SHA-256 is
`2181f08406cbc035601c0de65d2b54f77f578f9251894e4398b60285e318df38`.
Evidence roles, topics, score qualification and event verification use this same
explicit evaluator; no global patch or implicit downgrade is used.

Both recognized versions remain independently recomputable. Unknown explicit
versions and mismatched metadata/ledger versions fail closed. Period consumers
preserve recognized ledgers and upstream scores; they do not rebuild them as
unversioned historical inputs. Pre-P0 source-window reconstruction remains a
qualified derived view using frozen v1 scope.

A valid v1 report can retain a known scientific classification defect. Passing
its frozen integrity checks does not adjudicate that defect away. An authorized
correction must preserve source fields, original coverage and provider evidence,
retain rollback bytes and explicitly record a v1-to-v2 classification migration
with the original generation ID. The existing hash-guarded repair transaction
then rechecks classification, identity, renderer, semantic and durable QA.

This change does not resolve the older date-only midnight interpretation or
prove that an RSS announcement timestamp is the first public appearance.
Chinese abstract-based guides are not verified full-paper translations.
