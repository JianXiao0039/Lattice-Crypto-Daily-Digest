# Weekly Handoff Implementation Plan v0.1

Status: public implementation plan. No code is implemented in this phase.

# Proposed Architecture

```text
daily JSON
  -> existing weekly_synthesis.py
  -> existing weekly JSON
  -> future weekly_handoff.py
  -> track decisions + handoff packet drafts
  -> exports/research-handoffs/YYYY-Www/
  -> optional explicit manual mirror to ResearchArtifacts
```

# Existing Components to Reuse

| Component | Reuse |
| --- | --- |
| `weekly_synthesis.py` | weekly JSON, deduped records, seen dates/sources, source-health summary |
| `digest_sections.py` | existing research sections and report buckets as evidence |
| `ranking_explanation` | positive/negative signals and taxonomy evidence |
| `report_quality.py` | lattice/PQC anchor and false-positive risk text where useful |
| `workflow.py` | inspect later; do not integrate automatically in v0.1 |

# Proposed New Module

`src/lattice_digest/weekly_handoff.py`

Proposed pure functions:

- `load_weekly_json(path)`
- `unique_weekly_records(payload)`
- `classify_track(record)`
- `score_handoff_dimensions(record, track)`
- `decide_handoff_action(record, scores)`
- `build_handoff_packet(record, week_id)`
- `build_weekly_handoff(payload)`
- `render_handoff_markdown(payload)`
- `write_handoff_outputs(payload, output_dir)`

All functions should be deterministic. Exact names remain `TODO_VERIFY`.

# Proposed Output

```text
exports/research-handoffs/YYYY-Www/
  weekly-handoff.json
  weekly-handoff.md
  packets/
    QPH-YYYY-Www-NN.json
```

Generated outputs should not be committed by default.

# CLI Plan

```text
python -m lattice_digest.weekly_handoff \
  --weekly-json data/weekly/YYYY-Www.json \
  --output-dir exports/research-handoffs \
  --dry-run
```

Potential flags:

- `--track module-sis-chameleon-hash`
- `--action handoff_now`
- `--include-backlog`
- `--mirror-research-artifacts PATH`
- `--execute`

Rules:

- dry-run default;
- no network;
- no fetching;
- no ranking recalculation;
- no default ResearchArtifacts mirror;
- reject PhD_Application destination;
- no scheduled automation.

# Selection Layers

1. Hard anchor gate.
2. Track assignment.
3. Artifact-use assignment.
4. Handoff dimension scoring.
5. Verification and overclaim checks.
6. Action decision.
7. Stable ordering and packet ID.

# Stable Ordering

Suggested order:

1. action: handoff_now, handoff_after_verify, keep_in_radar, backlog, exclude;
2. track priority: Module-SIS chameleon hash, public Xingye bridge, implementation/parameterization, ML-KEM/ML-DSA background, AI4Lattice watchlist, noise;
3. direct usefulness score descending;
4. existing relevance score descending;
5. title ascending.

# Boundary Requirements

- Existing weekly files remain unchanged.
- Existing ranking values remain unchanged.
- No public packet contains private application material.
- ResearchArtifacts writes require explicit path and execute action.
- Packet writes cannot modify artifact code, proof, or paper files automatically.

# Phase 12G Entry Criteria

- Field schema accepted.
- Selection policy manually reviewed.
- Fixtures include true positives and generic false positives.
- Output paths confirmed ignored.
- ResearchArtifacts mirror boundary test designed.
- Non-claims policy included in every packet.

