# Phase 13I: Controlled Production Patch Proposal for v0.5

## Executive Summary

Phase 13I corrects the route away from manual annotation and shadow-classifier side quests. The work is centered on the paper radar's recommendation reasons: helping the user decide which Daily/Weekly/Monthly papers to 精读, 扫读, 暂存, or 忽略.

Status:

- Rationale helper: implemented as isolated helper.
- Production Daily/Weekly pipeline: unchanged.
- Monthly synthesis: design-ready but not implemented.
- Keyword-only rationale: deprecated as a sufficient recommendation reason.
- Production gate: `eligible_for_future_controlled_rationale_patch`.

## Scope Correction

No manual annotation workflow, human-gold metrics workflow, or shadow-classifier productionization was created. The system remains a lattice/PQC paper radar.

## Helper Summary

Created `src/lattice_digest/recommendation_rationale.py`.

The helper:

- accepts normalized paper-like records;
- uses title, abstract, conclusion, keywords, source, tags, and repository notes when present;
- emits structured rationale fields;
- uses no network, no LLM, and no auxiliary skill runtime;
- does not change ranking, classification, sources, Daily workflow, or Weekly workflow.

## Evidence Handling

- Abstract exists: problem/method/contribution are abstract-supported.
- Conclusion exists: contribution may be conclusion-supported.
- Conclusion absent: no conclusion claim is made.
- Abstract absent: method and contribution stay TODO_VERIFY.
- Keyword-only: low-confidence; keywords remain supporting evidence only.

## Improved Recommendation Examples

Bad:

> Matched keywords: LWE, lattice, signature.

Better:

> 精读：The abstract says the paper studies MLWE security estimates for ML-KEM and proposes a hybrid attack model combining lattice reduction, coordinate guessing, and BKZ cost calibration. It matters because it directly connects MLWE, ML-KEM, and lattice-reduction cost modeling. TODO_VERIFY: full proof details, parameter claims, and experiment assumptions require reading the paper.

Weak FHE application:

> 暂存：The abstract uses homomorphic encryption inside a secure analytics system, but the available evidence is application/system-facing rather than a core lattice attack, parameter-estimation, or scheme-design contribution. Keep it as peripheral FHE context. TODO_VERIFY: check whether it contains reusable RLWE/FHE implementation insight.

## Daily / Weekly / Monthly Impact

- Daily: future controlled patch may render rationale for A/B papers after ranking evidence.
- Weekly: future controlled patch may reuse Daily rationale without inventing missing evidence.
- Monthly: only a design exists; no production monthly module was found.

## v0.4.1 Release Relation

Phase 13I does not unblock v0.4.1 release by itself. It is a v0.5 proposal/helper phase and does not create, move, delete, or recreate release tags.

## Validation

Required validation was run after implementation and is recorded in the final assistant report.

## TODO_VERIFY

- Decide whether future Daily JSON should include rationale fields by default.
- Add renderer compatibility tests before production integration.
- Keep monthly synthesis design separate until a controlled implementation phase.
