# Phase 12G Weekly Handoff Packet Generator v0.1

生成日期：2026-06-05

本报告属于公开 research tooling implementation。它不包含 target PI email、SoP draft、private application tracker、funding strategy、personal PhD narrative 或 private advisor-specific material。

# Executive Summary

Phase 12G implements a minimal additive Weekly Handoff Packet Generator v0.1.

The generator reads an existing weekly JSON artifact, applies a deterministic track/handoff policy, and writes structured JSON and Markdown packet files under `handoffs/weekly/`. It is a standalone manual command and is not integrated into the existing daily, weekly, full, or background workflow.

The generator supports:

- Module-SIS chameleon hash candidates;
- public Xingye Lu technical bridge candidates;
- AI4Lattice longline candidates;
- ML-KEM / ML-DSA background candidates;
- lattice/PQC privacy watchlist candidates;
- explicit excluded/noise records.

It does not fetch papers, recalculate relevance scores, modify weekly/daily artifacts, write ResearchArtifacts, or touch `PhD_Application`.

# Implementation Scope

Implemented:

- standalone Python module and CLI;
- deterministic weekly record deduplication;
- deterministic packet IDs and ordering;
- hard lattice/PQC anchor gate;
- six supported tracks;
- five action labels;
- packet-level scoring fields;
- packet-level `todo_verify`;
- mandatory non-claims;
- valid empty output;
- source-health caveat preservation;
- dry-run;
- explicit refusal to write into a `PhD_Application` path;
- generated-output ignore rule for `handoffs/`.

Not implemented:

- workflow command-center integration;
- automatic or scheduled execution;
- ResearchArtifacts mirroring;
- network fetching;
- original-paper verification;
- automatic security, novelty, construction, parameter, or publication claims.

# Files Added

- `src/lattice_digest/weekly_handoff.py`
- `tests/test_weekly_handoff.py`
- `docs/reports/phase-12g-weekly-handoff-packet-generator-v0.1.md`
- `docs/research_tracks/weekly_handoff_generator_usage_v0.1.md`

Modified:

- `.gitignore`: added generated `handoffs/` output directory.

# Handoff Packet Schema

Every packet contains:

- `handoff_id`
- `week_id`
- `source_record_id`
- `title`
- `authors_raw`
- `source`
- `url_or_identifier`
- `track`
- `action_label`
- `lattice_pqc_anchor_evidence`
- `module_sis_relevance_score`
- `chameleon_hash_relevance_score`
- `xingye_bridge_relevance_score`
- `ai4lattice_relevance_score`
- `implementation_reproducibility_usefulness`
- `proof_usefulness`
- `parameterization_usefulness`
- `verification_burden`
- `overclaim_risk`
- `intended_research_artifact_target`
- `todo_verify`
- `non_claims`

Top-level output also preserves:

- week ID;
- coverage;
- source-health summary;
- source-health caveat;
- track/action counts;
- exclusions;
- global TODO_VERIFY.

# Track Selection Rules

## Module-SIS chameleon hash

Requires a lattice/PQC anchor and direct/adjacent evidence involving:

- Module-SIS / SIS;
- chameleon hash;
- lattice/SIS commitment;
- lattice trapdoor or trapdoor sampling.

Metadata-level candidates use `handoff_after_verify`, not `handoff_now`.

## Public Xingye Lu technical bridge

Requires a lattice/PQC anchor and a technical bridge involving:

- linkable ring signatures;
- lattice ring signatures;
- blind lattice signatures;
- hash-then-one-way signatures;
- programmable hash;
- anonymous authentication.

Every bridge packet states that no professor-specific fact is asserted.

## AI4Lattice longline

Requires both:

- an AI/ML signal;
- a lattice cryptanalysis, LWE/RLWE/MLWE, BKZ, or primal/dual/hybrid attack signal.

Generic AI is excluded.

## ML-KEM / ML-DSA background

Explicit ML-KEM, Kyber, ML-DSA, Dilithium, FIPS 203, or FIPS 204 items are background/watch candidates. They do not automatically become direct Module-SIS handoffs.

## Privacy / registration watchlist

Requires a lattice/PQC anchor. Generic privacy, registration, commitment, ring signature, or ZK is excluded.

## Excluded noise

Records without a sufficiently specific lattice/PQC-anchored handoff use are marked `exclude`.

# Non-Claims Policy

Every packet states:

- this is not a security proof;
- this is not a novelty claim;
- this is not a claim that the construction works;
- this is not a publication claim;
- this is a research triage and handoff record only.

The generator does not promote metadata-level evidence into verified technical facts.

# Tests Added

`tests/test_weekly_handoff.py` covers:

- valid JSON schema;
- valid Markdown;
- Module-SIS/chameleon-hash candidate inclusion;
- generic hash exclusion;
- generic commitment exclusion;
- public Xingye bridge TODO_VERIFY handling;
- empty weekly input;
- dry-run writes no files;
- input weekly JSON remains unchanged;
- normal output writes JSON/Markdown without network;
- PhD_Application output refusal;
- deterministic generation.

# Manual Usage

Generate from the latest weekly JSON:

```powershell
python -m lattice_digest.weekly_handoff --latest
```

Preview without writing:

```powershell
python -m lattice_digest.weekly_handoff --latest --dry-run
```

Generate from a specific weekly JSON:

```powershell
python -m lattice_digest.weekly_handoff --weekly-json data\weekly\2026-W23.json
```

Custom output directory:

```powershell
python -m lattice_digest.weekly_handoff --latest --output-dir handoffs\weekly
```

The command is manual-only. No scheduler or background service is configured.

# Limitations

- Track classification is deterministic keyword/evidence policy, not original-paper understanding.
- The current generator does not parse original PDFs.
- Metadata may contain false-positive tags.
- `handoff_now` is intentionally not assigned to metadata-only Module-SIS or public bridge candidates.
- No ResearchArtifacts mirroring is implemented.
- No workflow command-center integration is implemented.
- Handoff scores are policy scores, not existing ranking scores and not security judgments.
- The generator reads `sections` or a fallback top-level `records` list; historical unusual weekly formats may require future compatibility work.

# TODO_VERIFY

- Review generated packets against several weeks of real data.
- Decide whether direct verified records may later use `handoff_now`.
- Decide whether original-paper verification status should become a structured input.
- Decide whether a future explicit ResearchArtifacts mirror is useful.
- Review the hard anchor policy for false positives and false negatives.
- Decide whether packet-level abstracts should be included later.
- Confirm whether `handoffs/` should remain entirely local/ignored.

# Next Phase Recommendation

Recommended next phase:

**Phase 12H: Weekly Handoff Manual Pilot and Golden Fixtures**

The pilot should review generated packets manually for several weeks before considering workflow integration or ResearchArtifacts mirroring.

