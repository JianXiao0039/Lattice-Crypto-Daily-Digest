# Phase 13B ARS Offline Track Evaluation Protocol

## Material Passport

- Origin skill: `academic-research-suite`
- Workflow: `experiment-agent`
- Mode: `plan` and reproducibility validation
- Adapter version: `0.1.11`
- Date: `2026-06-12`
- Verification status: `ANALYZED`
- Production logic changed: `false`

## Objective

Construct a repository-grounded annotation queue and evaluate an experimental track proposer without changing production taxonomy, ranking, queries, negative keywords, fetchers, section classification, or track assignment.

The primary experimental question is whether retained repository evidence is sufficient to distinguish four research tracks and three control conditions. This phase does not establish production accuracy because no labels are yet user-confirmed or user-corrected.

## Inputs

| Input | Scope | Role |
|---|---|---|
| `data/YYYY-MM-DD.json` | Existing repository records | Primary record source |
| `data/weekly/*.json` | Existing repository records | Additional provenance and deduplication |
| v0.1 manual sample | 15 provisional records | Annotation-history audit only |
| Track scope documents | Existing repository policy | Label-definition evidence |

External paper search, external metadata enrichment, private workspaces, and ResearchArtifacts are excluded.

## Sample Construction

1. Enumerate all daily and weekly JSON records.
2. Deduplicate by paper ID, DOI, record ID, URL, then title fallback.
3. Prefer the retained copy with an abstract when duplicate records differ in completeness.
4. Preserve every repository artifact path in `source_provenance` using POSIX separators.
5. Reuse valid v0.1 identifiers, but do not inherit their labels as human gold.
6. Include every usable unique repository record when fewer than 80 exist.
7. Record actual strata and coverage gaps rather than fabricating balance.

Target: 80. Minimum acceptable: 60. Recommended strata are planning targets, not quotas that permit invented records.

## Stratification

The intended strata are Tracks A-D, hard negatives, and ambiguous/multi-track records. Selection is evidence-led:

- Track A requires SIS/Module-SIS, lattice commitment, trapdoor, chameleon-hash, sanitizable-signature, or exposure-model evidence.
- Track B requires a technical lattice privacy/authentication/signature bridge. Author identity is not evidence.
- Track C requires lattice cryptanalysis, reduction, primal/dual/hybrid attack, sparse-secret recovery, or learning-guided attack evidence.
- Track D requires concrete PQC schemes, parameterization, implementation, side-channel/fault analysis, systems integration, or lattice/FHE engineering.
- Hard negatives retain keyword collisions, generic cryptography, and non-lattice PQC families.
- Ambiguous cases retain missing anchors or unclear technical centrality.

## Leakage Prevention

1. Production labels and scores may be retained as evidence fields but are not treated as gold.
2. The experimental evaluator does not import or invoke the production classifier.
3. Machine proposals use a script-local rule table under `scripts/`.
4. Codex-reviewed labels are stored separately from machine proposals.
5. Human-gold fields remain empty until the user confirms or corrects a record.
6. Metrics against Codex-reviewed labels are named diagnostics, not human-gold metrics.
7. No rule candidate may be copied into production logic during Phase 13B.

## Annotation Workflow

Each row passes through four explicit states:

1. `machine_proposed_label`: deterministic experimental proposal.
2. `codex_reviewed_label`: evidence-based provisional review using retained repository fields.
3. `human_gold_label`: empty until user adjudication.
4. `human_review_status`: one of the allowed status values.

Only `user_confirmed` and `user_corrected` rows count in human-gold metrics. `needs_user_review`, `not_reviewed`, and insufficient-metadata rows do not.

## Ambiguity and Multi-Label Handling

- Use `ambiguous` when evidence cannot support a single track.
- Use one primary track plus secondary tracks when multiple technical relations are supported.
- Use `multi_track` as a control label, not as a substitute for primary/secondary labels.
- Exclude ambiguous records from any future forced single-label accuracy calculation unless the user adjudicates them.
- Multi-label micro F1 must compare sets of primary and secondary tracks.

## Metrics

Human-gold metrics, when valid labels exist:

- per-track precision, recall, and F1;
- macro precision, recall, and F1;
- micro F1 for multi-label evaluation;
- irrelevant false-positive rate;
- ambiguous coverage;
- no-label rate;
- multi-track disagreement rate;
- explanation completeness rate;
- annotation coverage.

When zero valid human-gold labels exist, all human-gold precision/recall/F1 fields must be `N/A`. A machine-to-Codex comparison may be reported only as a provisional diagnostic.

## Error Analysis

Review errors by mechanism rather than only by count:

- generic signature/commitment/privacy term without lattice anchor;
- scheme-name collision such as non-cryptographic Falcon;
- generic ML or AI without lattice cryptanalysis;
- generic FHE application incorrectly absorbed by Track B or D;
- classical attack omitted because it lacks AI terminology;
- Track D over-expansion into miscellaneous PQC;
- technical multi-track relations collapsed to one label.

False-positive and false-negative lists must retain sample ID, track, title, provenance, and the relevant evidence limitation.

## Reproducibility

- Command: `python scripts/evaluate_v0_5_track_precision.py`
- Working directory: repository root
- Determinism class: deterministic for a fixed set of repository JSON files and script revision
- Expected outputs: v0.2 sample JSON/Markdown and evaluation reports under `docs/`
- Success criteria: exit code 0, at least 60 records, no production artifact changes, schema validation tests pass
- Comparison: rerun output should be byte-identical when inputs and code are unchanged
- Environment: record Python version and repository status with the evaluation log

The script must not write `data/`, `digests/`, `handoffs/`, `src/`, private workspaces, or ResearchArtifacts.

## Stopping Criteria

Stop sample expansion when all existing unique repository records have been considered. Do not synthesize additional records to meet 80.

Stop metric interpretation when there are no user-confirmed/user-corrected labels. Report coverage and diagnostic disagreement only.

## Production-Change Gate

Production changes remain blocked until:

1. a sufficiently broad human-adjudicated sample exists;
2. human-gold metrics meet a separately approved target;
3. false positives and false negatives are reviewed by mechanism;
4. CI is green or a platform exception is explicitly accepted;
5. durable post-tag run evidence exists;
6. proposed rules first pass a shadow-mode evaluation.

Phase 13B may conclude `sample_design_ready` or `sample_design_ready_with_coverage_gaps`. It must not conclude `implementation_ready`.

