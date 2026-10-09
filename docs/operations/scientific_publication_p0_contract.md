# Scientific relevance and Daily publication P0

Tool-ID: Codex. Task-ID: SCIENTIFIC_RELEVANCE_DAILY_PUBLICATION_P0.
Base: live origin/main 0f387ef1ad388a1db47b9d062480929dd7d239d5.
Candidate: D:/Code/CodexProjects/lattice-digest-p0-candidate-20261009.
Allowed paths: source modules for evidence, relevance, events, Daily/Weekly/Monthly,
their regression tests, this contract, replay script and audit reports.
Forbidden: development edits, runtime, canonical Daily files, automation, credentials,
Query Portfolio V3 activation, external publication. Local exact-path commit authorized.

## Preimplementation evidence and root causes

Frozen evidence: D:/Code/CodexProjects/lattice-digest-p0-evidence-20261009.
freeze-reconciliation.json contains SHA-256, complete original metadata, source health,
QA, row identities, freshness, action partitions and Markdown heading occurrence counts.
Original pairs are copied before source changes; they remain immutable replay inputs.

1. run.py _filter_records_to_coverage(include_backfill=True) retains every old record.
   All incidents used backfill mode; 263/263/319 rows reached storage.
2. evidence_contract.classify_scope accepts ANY PRIM/IMPL/PROOF match as direct.
   An ML-KEM comparison in HQC or an ML-KEM component in generic AKE becomes A/90.
   Raw matched concepts do not distinguish technical-object roles. Generated conclusion
   lacks explicit provenance requirements. Ontology neighbors must remain inference.
3. promotion_history.classify_event treats an unseen arXiv v2+ as a new version;
   apply_promotion_history overwrites even stale freshness with recent_content_revision.
   Historical revision labels in the incidents are not evidence of in-window events.
   History remembers only primary promotions, losing revision/watch deduplication.
4. authority.derive_authority counts all ABC rows as selected irrespective of freshness.
5. storage.build_daily_payload enriches rows; digest.generate_markdown independently
   enriches, counts, then renders high-priority entries again in topic sections.
   Oct 7: 265 numbered headings for 263 identities; Oct 9: 323 for 319.
6. Oct 8's 196 is the subset (research_value>=70 OR level=Backfill), not all 263
   nonprimary rows. Action partition is 0+156+38+69=263.
7. Oct 9's 1 Medium counts a recommendation tier; 4 primary and read_now=4 count
   different populations. The reader verdict silently omits the three Low primary rows.
8. semantic QA checks score/label and source fields but not the event/archive partition
   or full rendering identity counts. All three original semantic QA reports said PASS.
9. Weekly and Monthly aggregate every Daily record, dedup identities but still turn
   historical observation into period population and trend inputs.
10. digest._append_idea_and_questions creates topic-template ideas without a concrete
    bottleneck, closest work or novelty evidence. Weekly recomputation can regenerate
    generic candidate buckets even if Daily strips them; event inputs now suppress them.
11. storage.write_sqlite deletes the complete papers table before each Daily insert.
    Separating L0 from Daily makes this especially unsafe; upserts must preserve old
    discoveries rather than delete the historical library.
12. Benchmark V2's existing source snapshots contain seven materials/chemistry MLIP
    false positives and a dihedral-coset background-only paper labelled A. Raw labels
    and all snapshots remain unchanged; explicit Codex source-review corrections are
    added in the existing correction map. No human adjudication is claimed.
13. The primary-role parser initially still accepted physical LLL (Landau level)
    and atomic ideal-lattice references. Explicit noncryptographic-domain gates
    now reject these unless source-grounded cryptographic context is present;
    mixed physical-security papers with a genuine lattice target remain eligible.

## Required semantics

L0 contains all observations; L1 requires qualifying source roles; L2 is a timestamped,
identity/version/content-grounded event; L3 is a recommendation on a qualified event.
ABC relevance and freshness are separate. No maximum survivor count is imposed.
Existing score thresholds 80/60/40 are retained. Adjacent/general scope has a semantic ceiling of 59; implemented scores are 49 for quoted lattice background/comparison and 45 for adjacent PQC without such a role.
Roles: PRIMARY_RESEARCH_OBJECT, LATTICE_HARDNESS_ASSUMPTION, SECURITY_TARGET,
IMPLEMENTED_PRIMITIVE, ATTACK_TARGET, METHOD_SUBROUTINE, COMPARISON_BASELINE,
BACKGROUND_MENTION, ONTOLOGY_NEIGHBOR, USER_RESEARCH_HYPOTHESIS.
Roles are deterministic MODEL_INFERENCE about quoted source spans, never human gold.
Primary lattice objects, direct targets and explicitly constructed lattice instantiation assumptions qualify;
a generic impossibility/proof assumption by itself does not establish a lattice primary object;
comparison, generic protocol components and method-only adjacent contributions do not.

Event collections: primary_publication_events, revision_events,
new_critical_verify_events, background_updates, historical_library_observations.
Only first three are automatic core Daily input. Historical/uncertain records remain
machine observable. Backfill run mode does not authorize dumping the historical library.
Critical watches preserve original date, evidence change date, source hash, proof status,
reduction direction and review action; unchanged watches do not reopen automatically.
Future proceedings year is independent of authoritative preprint/revision timestamp.
Missing/ambiguous/future-only dates cannot create a primary event.

One event ledger supplies counts, rendering and period inputs. Display budgets affect
detail only; a complete compact event index remains visible. Period deduplication uses
event IDs and paper identities separately and exposes missing/failed Daily inputs.
No actionable research idea is emitted without a structured, source-supported proposal.

## Validation and gates

Offline three-day replay, all-row machine audit, stratified independent source review
(MODEL_REVIEW, not human adjudication), positive/negative canaries, event QA mutation
tests, period deduplication, source-health/authority regression, full Python315 suite.
No tests deleted or skipped to hide failures. No success marker before all tests pass.
Publication remains a separate authorization: AUTHORIZE_LATTICE_DIGEST_P0_RELEASE_AND_THREE_DAY_REPAIR.

14. A first-posted in-window arXiv v2 identity was accepted by the new event ledger
    but rejected by legacy cross-day QA as GEN_NEW_VERSION. Publication QA now
    honors the canonical primary event while still rejecting explicit forged
    prior-identity primary flags; both caller flag states are regression-tested.
