# Weekly Handoff Test Plan v0.1

Status: proposed tests for a future Phase 12G implementation.

# Test Principles

- deterministic fixtures;
- temporary directories;
- no network;
- no real ResearchArtifacts modification;
- no PhD_Application access;
- no secrets;
- no ranking changes;
- dry-run first.

# Core Schema Tests

1. Weekly handoff output contains schema version, week ID, packets, exclusions, TODO_VERIFY, coverage, and source-health summary.
2. Each packet contains all required handoff fields.
3. Missing authors/identifier fields remain empty or null.
4. Handoff IDs are deterministic.
5. Packet ordering is deterministic.

# Selection Tests

1. Explicit `Module-SIS chameleon hash` record becomes a Module-SIS track candidate.
2. Explicit lattice commitment / trapdoor candidate can become `handoff_after_verify`.
3. Generic hash without lattice/PQC anchor is excluded.
4. Generic commitment without lattice/PQC anchor is excluded.
5. Generic ring signature without lattice/PQC anchor is excluded or TODO_VERIFY.
6. Generic privacy / AI / LLM / optimization / blockchain / registration / ZK is excluded.
7. ML-KEM / ML-DSA background remains backlog unless a concrete artifact use is present.
8. AI4Lattice requires explicit lattice attack / LWE / BKZ / hybrid anchor.

# Public Xingye Bridge Tests

1. A lattice/PQC linkable-ring-signature candidate can enter the public technical bridge track.
2. Professor-specific facts are never generated.
3. Bridge candidates include `TODO_VERIFY`.
4. Bridge packets include the professor-specific non-claim.

# Decision Rubric Tests

1. Direct verified candidate can become `handoff_now`.
2. Plausible but metadata-only candidate becomes `handoff_after_verify`.
3. Relevant candidate without artifact use remains `keep_in_radar`.
4. Background candidate becomes `backlog`.
5. Missing-anchor candidate becomes `exclude`.
6. High overclaim risk prevents `handoff_now`.

# Stability and Boundary Tests

1. Existing weekly JSON is not modified.
2. Existing relevance scores and labels are unchanged.
3. Existing weekly Markdown is unchanged.
4. Dry-run writes no files.
5. Default execution writes only to the supplied public output directory.
6. No files are written under `PhD_Application`.
7. ResearchArtifacts mirror requires explicit flag and test temp directory.
8. Mirror cannot modify code, proof, parameter, or paper files.
9. No scheduler, cron, Task Scheduler, daemon, or startup file is created.

# Security and Privacy Tests

Outputs must not contain:

- API keys or secret patterns;
- `.env` contents;
- private application text;
- unsupported security claims;
- unsupported novelty claims;
- HTML or internal citation markers.

# Suggested Fixture Cases

- true positive: Module-SIS chameleon hash construction placeholder with explicit anchor;
- construction-adjacent: lattice commitment with SIS anchor;
- trapdoor candidate: lattice trapdoor sampling;
- public bridge: lattice-based linkable ring signature;
- background: ML-KEM implementation review;
- AI4Lattice true positive: LWE hybrid attack coordinate ranking;
- false positives:
  - generic commitment;
  - generic hash;
  - generic ring signature;
  - generic privacy ML;
  - generic AI optimization.

# Suggested Future Test File

`tests/test_weekly_handoff.py`

Potential supporting fixtures:

`tests/fixtures/weekly_handoff/`

# Validation Commands for Phase 12G

Use project-scoped tests and repository-local basetemp:

```text
python -m pytest tests/test_weekly_handoff.py --basetemp=.pytest_tmp
python -m pytest tests --basetemp=.pytest_tmp
```

