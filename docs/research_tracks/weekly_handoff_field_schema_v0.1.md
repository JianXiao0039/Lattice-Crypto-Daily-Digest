# Weekly Handoff Field Schema v0.1

Status: proposed public exchange schema. This is not yet implemented.

# Top-Level Weekly Handoff

| Field | Type | Source / rule |
| --- | --- | --- |
| `schema_version` | integer | fixed handoff schema version, initially 1 |
| `week_id` | string | existing weekly JSON |
| `source_weekly_json` | string | input path, public relative path preferred |
| `generated_at` | string | generation timestamp; excluded from selection logic |
| `coverage` | object | existing weekly coverage |
| `source_health_summary` | object | existing weekly source-health summary |
| `packets` | array | deterministic handoff packets |
| `excluded` | array | deterministic exclusion records |
| `todo_verify` | array | unresolved manual verification items |

# Handoff Packet Fields

| Field | Type | Availability now | Proposed rule |
| --- | --- | --- | --- |
| `handoff_id` | string | missing | deterministic from week ID + source record ID |
| `week_id` | string | available top-level | copy from weekly payload |
| `source_record_id` | string | partial | prefer dedup key, paper ID, DOI, arXiv/ePrint ID, then normalized title |
| `title` | string | available | preserve exactly |
| `authors_raw` | array/string/null | authors list available; raw form missing | preserve authors list; do not invent raw author string |
| `source` | string | available | preserve |
| `url_or_identifier` | string/object | available but sparse by identifier type | prefer DOI/ePrint/arXiv/source URL without invention |
| `track` | string | missing | deterministic Phase 12 track classification |
| `action_label` | string | missing | handoff_now / handoff_after_verify / keep_in_radar / backlog / exclude |
| `lattice_pqc_anchor_evidence` | array/string | derivable | use title/abstract/tags/taxonomy/ranking explanation; preserve source |
| `module_sis_relevance_score` | integer 0-5 | missing | handoff-policy score, not ranking score |
| `chameleon_hash_relevance_score` | integer 0-5 | missing | handoff-policy score |
| `xingye_bridge_relevance_score` | integer 0-5 | missing | public technical bridge only |
| `ai4lattice_relevance_score` | integer 0-5 | missing | require explicit lattice-attack anchor |
| `implementation_reproducibility_usefulness` | integer 0-5 | missing | deterministic evidence-based score |
| `proof_usefulness` | integer 0-5 | missing | conservative; metadata-only records should not score high |
| `parameterization_usefulness` | integer 0-5 | missing | conservative; require explicit evidence |
| `verification_burden` | integer 0-5 | missing | higher means more manual work |
| `overclaim_risk` | integer 0-5 | missing | higher means stronger non-claim guard |
| `intended_research_artifacts_target_file` | string/null | missing | policy mapping; no automatic write |
| `todo_verify` | array | missing at packet level | required |
| `non_claims` | array | missing | required |

# Evidence Fields Reused from Current Weekly Records

- `dedup_key`
- `paper_id`
- DOI / arXiv ID / ePrint ID
- `title`
- `authors`
- `abstract`
- `source`
- source URL
- publication date
- `taxonomy_tags`
- `tags`
- `keywords_matched`
- `negative_keywords_matched`
- `ranking_explanation`
- `research_sections`
- `report_buckets`
- `research_tags`
- `why_it_matters`
- `suggested_action`
- `seen_dates`
- `seen_sources`
- `source_health_ref`

# Track Enum Proposal

- `module_sis_chameleon_hash`
- `xingye_lu_public_technical_bridge`
- `mlwe_mlkem_mldsa_background`
- `ai4lattice_longline`
- `lattice_pqc_privacy_watchlist`
- `implementation_parameterization`
- `noise_exclusion`

# Required Non-Claims

Each non-excluded packet must include at least:

- not a security proof;
- not a novelty claim;
- not a claim that a construction works;
- not a secure parameter recommendation;
- not an implementation result unless supported by actual artifact evidence.

Bridge packets also require:

- no professor-specific fact is claimed;
- no private application material is included.

# Missing-Field Policy

- Use empty arrays, empty strings, or null.
- Do not invent authors, identifiers, URLs, assumptions, proof usefulness, or artifact relevance.
- If evidence is metadata-only, add `TODO_VERIFY`.
- If no hard anchor is detected, use `exclude`.

# Compatibility

- This schema is separate from weekly synthesis schema version 1.
- Existing weekly JSON is an input and remains unchanged.
- Future readers must tolerate missing optional fields.

