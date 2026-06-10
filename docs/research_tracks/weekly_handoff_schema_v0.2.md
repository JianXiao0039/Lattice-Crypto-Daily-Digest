# Weekly Handoff Schema v0.2

Status: hardened documentation revision for the Weekly Handoff Packet Generator.

Important: generated JSON currently uses machine-readable `schema_version: 1`. The `v0.2` in this filename denotes the documentation and validation revision, not a breaking JSON schema-version bump.

# Top-Level Object

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | currently fixed to 1 |
| `week_id` | string | yes | copied from weekly input or `unknown-week` |
| `source_weekly_json` | string | yes | input filename/path label |
| `coverage` | object | yes | copied from weekly input or empty object |
| `source_health_summary` | object | yes | copied or empty fallback |
| `source_health_caveat` | string | yes | conservative human-readable caveat |
| `track_counts` | object | yes | deterministic track counts |
| `action_counts` | object | yes | deterministic action counts |
| `packets` | array | yes | validated packet objects |
| `excluded` | array | yes | exclusion summary |
| `todo_verify` | array | yes | global manual verification requirements |

# Packet Fields

| Field | Type | Required | Validation |
| --- | --- | --- | --- |
| `handoff_id` | string | yes | deterministic and unique |
| `week_id` | string | yes | packet week |
| `source_record_id` | string | yes | deterministic best available identity |
| `title` | string | yes | empty string allowed, never invented |
| `authors_raw` | array/string/null | yes | preserves available author representation |
| `source` | string | yes | empty string allowed |
| `url_or_identifier` | string | yes | empty if unavailable |
| `track` | enum string | yes | must be a supported track |
| `action_label` | enum string | yes | must be a supported action |
| `lattice_pqc_anchor_evidence` | array | yes | explicit evidence or manual-review marker |
| `module_sis_relevance_score` | integer | yes | 0–5 |
| `chameleon_hash_relevance_score` | integer | yes | 0–5 |
| `xingye_bridge_relevance_score` | integer | yes | 0–5, public technical bridge only |
| `ai4lattice_relevance_score` | integer | yes | 0–5 |
| `implementation_reproducibility_usefulness` | integer | yes | 0–5 |
| `proof_usefulness` | integer | yes | 0–5, not proof validity |
| `parameterization_usefulness` | integer | yes | 0–5, not secure-parameter validity |
| `verification_burden` | integer | yes | 0–5 |
| `overclaim_risk` | integer | yes | 0–5 |
| `intended_research_artifact_target` | string/null | yes | suggestion only; no automatic write |
| `todo_verify` | array | yes | manual verification queue |
| `non_claims` | array | yes | must contain every mandatory non-claim |

# Supported Tracks

- `module_sis_chameleon_hash`
- `xingye_lu_bridge`
- `ai4lattice_longline`
- `mlkem_mldsa_background`
- `privacy_registration_watchlist`
- `excluded_noise`

# Supported Actions

- `handoff_now`
- `handoff_after_verify`
- `keep_in_radar`
- `backlog`
- `exclude`

# Mandatory Non-Claims

Every packet must include:

- `this is not a security proof`
- `this is not a novelty claim`
- `this is not a claim that the construction works`
- `this is not a claim that a PI works on a topic`
- `this is not a publication claim`
- `this is a research triage and handoff record only`

# Validation Rules

Before writing output, the generator validates:

- top-level schema version;
- packets list type;
- packet object type;
- all required fields;
- unique IDs;
- supported tracks/actions;
- score integer type and 0–5 range;
- list type for TODO_VERIFY and non-claims;
- presence of every mandatory non-claim.

# Input Compatibility

Weekly records may be read from:

- top-level `records`;
- `sections`;
- `report_buckets`.

Duplicate records are removed deterministically using the best available source identity.

# Missing Data Policy

- Do not invent data.
- Preserve missing strings as empty.
- Preserve missing authors as null.
- Add TODO_VERIFY for missing or metadata-only evidence.
- Exclude records without sufficient hard anchor evidence.

