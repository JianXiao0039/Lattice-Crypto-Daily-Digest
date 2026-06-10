# Phase 12H Weekly Handoff Generator Hardening and Docs

生成日期：2026-06-05

本报告属于公开 research tooling hardening。它不包含 target PI email、SoP draft、private application tracker、funding strategy、personal PhD narrative 或 private advisor-specific material。

# Executive Summary

Phase 12H reviewed and hardened the standalone Weekly Handoff Packet Generator introduced in Phase 12G.

Hardening focused on output safety, schema consistency, conservative claim boundaries, input compatibility, and regression coverage. The generator remains manual-only, local, offline, and separate from the existing daily/weekly workflow.

Code changed only in:

- `src/lattice_digest/weekly_handoff.py`
- `tests/test_weekly_handoff.py`

Documentation added:

- Phase 12H hardening report;
- usage guide v0.2;
- schema guide v0.2;
- non-claims policy v0.2;
- troubleshooting guide v0.1.

Generated W23 JSON and Markdown were regenerated and validated. Existing daily/weekly artifacts, ranking, source ingestion, taxonomy, section classifier, source health, release metadata, ResearchArtifacts, and `PhD_Application` were not modified.

# Input Evidence Used

| Input | Status | How used | Limitation |
| --- | --- | --- | --- |
| `src/lattice_digest/weekly_handoff.py` | available | Generator behavior and safety audit | Deterministic keyword/evidence policy, not original-paper understanding |
| `tests/test_weekly_handoff.py` | available | Existing regression coverage audit | Phase 12G tests needed stronger schema/path coverage |
| `handoffs/weekly/2026-W23-handoff-packets.json` | available | Real output schema and classification audit | Generated artifact; ignored by git |
| `handoffs/weekly/2026-W23-handoff-packets.md` | available | Markdown readability and non-claim audit | Generated artifact; ignored by git |
| Phase 12G implementation report | available | Original scope and limitations | Pre-hardening state |
| usage guide v0.1 | available | Manual command baseline | Did not cover schema validation or `.git` refusal |
| Phase 12F implementation/schema/test plans | available | Planned field and test expectations | Planning documents only |
| quick-paper handoff protocol | available | Required packet and non-claim boundaries | Manual policy |
| latest weekly JSON | available | Real W23 generation input | Metadata may contain broad or incorrect tags |
| ResearchArtifacts RA-4 summary | available read-only | Safe/unsafe claim boundary reference | ResearchArtifacts was not modified |
| safe/unsafe claim-boundary docs | available read-only | Strengthened non-claim wording | Public generic wording only |

# Generator Behavior Review

## Input source

The generator reads:

- `--latest`: latest JSON under `data/weekly/`;
- `--weekly-json PATH`: a specific weekly JSON.

It reads records from:

- top-level `records`, when present;
- `sections`;
- `report_buckets`, as a compatibility fallback.

Records are deduplicated deterministically before packet construction.

## Output paths

Default:

- `handoffs/weekly/YYYY-Www-handoff-packets.json`
- `handoffs/weekly/YYYY-Www-handoff-packets.md`

`handoffs/` is ignored by git.

The generator refuses to write under:

- any `PhD_Application` path;
- any `.git` directory.

It does not write ResearchArtifacts automatically.

## Handoff schema

The generated top-level JSON uses `schema_version: 1`. The Phase 12H schema v0.2 document is a documentation/hardening revision; it does not silently change the machine-readable schema version.

Every packet is validated before output:

- required fields exist;
- handoff IDs are unique;
- track and action labels are supported;
- all policy scores are integers from 0 to 5;
- `todo_verify` and `non_claims` are lists;
- all mandatory non-claims are present.

## Track labels

- `module_sis_chameleon_hash`
- `xingye_lu_bridge`
- `ai4lattice_longline`
- `mlkem_mldsa_background`
- `privacy_registration_watchlist`
- `excluded_noise`

## Action labels

- `handoff_now`
- `handoff_after_verify`
- `keep_in_radar`
- `backlog`
- `exclude`

Metadata-level Module-SIS and public Xingye bridge candidates remain `handoff_after_verify`.

## Non-claims

Every packet explicitly states:

- this is not a security proof;
- this is not a novelty claim;
- this is not a claim that the construction works;
- this is not a claim that a PI works on a topic;
- this is not a publication claim;
- this is a research triage and handoff record only.

## TODO_VERIFY

Packets require original-paper verification, assumption/security-model verification, and artifact-use verification. Public Xingye bridge packets additionally state that no professor-specific fact is asserted.

## Noise exclusion

Broad weekly sections are not hard handoff evidence. Generic hash, commitment, registration, privacy, AI, LLM, optimization, blockchain, ZK, and ring-signature records remain excluded unless explicit lattice/PQC/HE/FHE/LWE/RLWE/MLWE/SIS/Module-SIS/NTRU/ML-KEM/ML-DSA evidence is present.

# Hardening Changes

| File | Change | Reason | Risk | Test coverage |
| --- | --- | --- | --- | --- |
| `src/lattice_digest/weekly_handoff.py` | Added mandatory PI-topic non-claim | Align with public bridge and RA-4 claim boundaries | Low, additive string field | Markdown/non-claim tests |
| `src/lattice_digest/weekly_handoff.py` | Added packet schema validation | Ensure stable, consistent JSON before write | Low; invalid internal payload now fails early | missing field, bad score, valid/empty payload tests |
| `src/lattice_digest/weekly_handoff.py` | Reject `.git` output paths | Enforce repository safety boundary | Low | `.git` refusal test |
| `src/lattice_digest/weekly_handoff.py` | Added `report_buckets` input fallback | Support valid weekly shapes missing `sections` | Low; deduplication remains deterministic | report-buckets-only test |
| `tests/test_weekly_handoff.py` | Added generic registration/privacy/AI/ZK noise cases | Strengthen hard anchor regression coverage | None | parametrized exclusions |

No changes were made to main daily or weekly digest semantics.

# Schema v0.2

Documentation:

`docs/research_tracks/weekly_handoff_schema_v0.2.md`

Packet fields:

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

# Manual Usage

The implemented command is:

```powershell
python -m lattice_digest.weekly_handoff --latest
```

Dry-run:

```powershell
python -m lattice_digest.weekly_handoff --latest --dry-run
```

Specific weekly file:

```powershell
python -m lattice_digest.weekly_handoff --weekly-json data\weekly\2026-W23.json
```

No `scripts\generate_weekly_handoff.py` wrapper exists. The module command is the supported command.

# Non-Claims Policy

The generator is a public research triage tool. It does not establish:

- a security proof;
- novelty;
- a working Module-SIS construction;
- secure parameters;
- a PI's research agenda;
- publication readiness;
- implementation or benchmark results.

Detailed policy:

`docs/research_tracks/weekly_handoff_non_claims_policy_v0.2.md`

# Troubleshooting

Detailed guide:

`docs/research_tracks/weekly_handoff_troubleshooting_v0.1.md`

Covered cases:

- missing weekly JSON;
- empty records;
- all records excluded;
- pytest scope;
- Python dependency check;
- no network requirement;
- no `PhD_Application` or `.git` writes.

# TODO_VERIFY

- Whether weekly workflow integration should ever be added; standalone manual use remains safer.
- Whether ResearchArtifacts synchronization should remain entirely manual.
- Whether generated packet JSON should remain ignored rather than committed.
- Whether handoff policy scores need tuning after several manually reviewed weeks.
- Whether original-paper verification status should become structured input.
- Whether hard-anchor evidence should become more source-field-specific after a pilot.

# Next Phase Recommendation

Run a manual multi-week golden-fixture pilot before changing classification policy or integrating the generator with other workflows.

