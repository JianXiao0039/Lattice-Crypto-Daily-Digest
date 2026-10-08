# Daily publication QA failure evidence

Rejected pairs are operational failures. They must return nonzero and must not
become scientific zero-paper results or successful canonical publications.

`DailyPublicationQAError` retains structured issues and a diagnostic receipt
path. The Daily runner surfaces the issue codes and that path through its
existing failure handler. Receipts and redacted candidates are stored under
`CANONICAL_ROOT/audits/daily-publication-failures/<unique-id>/`, including when
the publication candidate is constructed inside an exact-recovery temporary
directory. Temporary cleanup cannot remove that receipt. An I/O failure while
persisting diagnostics remains a rejection; the exception retains the issues
and reports that persistence failed.

Diagnostic candidates have `QA_REJECTED_DIAGNOSTIC_ONLY` state. They are outside
canonical Daily data/digest paths and cannot be treated as a promoted pair.
Each receipt records the historical window, execution provenance, original
candidate hashes, redacted artifact hashes, QA decisions, issue fields and a
bounded stack without local variables. Credentials, authorization, cookies,
secret environment values and HTTP response previews are redacted. Candidate
retention is capped at 8 MiB; an oversized candidate is explicitly incomplete.
Over-budget repeated issue detail is summarized by code counts and examples,
with the original issue codes retained. Redacted files are diagnostic evidence,
not byte-identical originals or a substitute for the source evidence archive.

## Source consistency repairs

The preserved October 7 incident exposed two producer/verifier inconsistencies:

1. Legacy dedup runs after semantic analysis. Replacing an abstract with a
   longer provider abstract could leave evidence terms, concepts and tags bound
   to the shorter abstract. Merging evidence-bound records now re-extracts
   source-only edges and rebinds evidence with the existing policy. Unbound
   legacy records retain their previous merge behavior. This does not introduce
   ontology terms, query activation, threshold changes or generated evidence.
2. Binding already recognizes source-grounded typed relations through
   `source_scope_score`. The verifier formerly applied its scope cap using
   `classify_scope` without those independently extracted relations. It now
   re-extracts them from the original source fields through the same existing
   source policy. Stored edges, rationale and generated text cannot grant scope.

Score/label, source-span, research-relation, source-health, strict freshness,
cross-day suppression and existing-pair protection checks remain mandatory.
An incomplete historical observation never establishes complete historical
coverage. `authoritative_backfill` identifies controlled run provenance;
scientific authority is derived separately and may be `PARTIAL_VERIFY_FIRST`,
`AUTHORITATIVE_DEGRADED`, or `INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS`.

## Offline incident evaluation

The incident source archive was observed on October 8. Its responses are not
snapshots of the historical October 7 cutoff. Reconstructed normalized records
must retain provider publication/update dates and distinguish the original
observation from the current replay execution. The incident's original
in-memory finalized state was not retained; replay is a source-backed
reconstruction, not a claim of byte-identical original state.

Source transport replay must deny network access, honor the original journal's
successful/failed query outcomes, preserve recorded source-health degradation,
restore source-role configuration, and copy prior promotion history read-only
into an external scratch root. Compare the normalized/finalized counts and
candidate identity set before using replay for acceptance. Once publication
inputs are reconstructed, the existing publication API can rerun QA without
another source crawl. Unit scratch QA does not establish public-runtime
provenance; the published public CLI gates remain unchanged.

The real provider fragments in
`tests/fixtures/publication_qa_incident_2026_10_07.json` reproduce both defects.
They supplement, rather than replace, the separately preserved full incident
archive. Passing these tests does not authorize historical collection or
canonical recovery promotion.
