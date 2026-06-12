# Phase 12Y: Post-Tag Actual-Run Evidence Collection and v0.5 Precision Design Gate

## Executive Summary

Phase 12Y found one actual post-tag Daily automation attempt and no actual post-tag Weekly Public Synthesis run. GitHub Actions run `27327344162` started after `v0.4.0`; its tests, digest generation, and artifact verification passed, but its commit step failed. Therefore it is valid `automation_post_tag_actual` evidence of execution, but not evidence of persisted Daily reliability.

A manual post-tag W23 handoff replay generated 20 packets. It is classified `manual_post_tag_equivalent`, not a Weekly automation run, because it reused pre-tag W23 input with 5/7-day coverage.

The `v0.4.0` tag points to package version `0.3.3`; verdict: `inconsistent_requires_followup`. Ubuntu CI passes while Windows CI fails at tests, so release confidence remains platform-limited.

A 15-record offline precision sample was built only from existing repository records. Offline design may proceed with more annotation: `design_ready_with_more_annotation`. Production classification changes remain `blocked_by_multiple_conditions`.

## v0.4.0 Tag Evidence

| Field | Value |
|---|---|
| Tag | `v0.4.0` |
| Target commit | `08c5f07967739ecd008773c4b167cd736848df88` |
| Commit time | `2026-06-11T01:05:06+08:00` |
| Tag type | lightweight |
| Current describe | tag remains reachable in current history |

The existing tag was not modified.

## Version and Tag Consistency

- package version at tag: `0.3.3`;
- current package version: `0.3.3`;
- release notes located: through `v0.3.3`;
- public GitHub Release for `v0.4.0`: not found;
- verdict: `inconsistent_requires_followup`.

This phase deliberately does not repair or reinterpret the version.

## Actual Post-Tag Daily Evidence

| Run | Evidence class | Result | Persisted artifact | Confidence |
|---|---|---|---|---|
| GitHub `27327344162` | `automation_post_tag_actual` | tests, generation, and artifact verification passed; commit failed | none after 2026-06-10 | high |

The run proves that Daily automation executed after the tag. It does not establish record count, source-starved state, IACR status, Semantic Scholar status, or repository publication because those outputs were not persisted.

No file timestamp was treated as sufficient execution evidence.

## Actual Post-Tag Weekly Evidence

Verified actual Weekly automation observations: 0.

One post-tag manual equivalent exists:

- command role: weekly handoff replay;
- output: 20 packets;
- input: pre-tag W23 data;
- coverage: 5 of 7 days;
- classification: `manual_post_tag_equivalent`.

It validates generator execution, not the Weekly Public Synthesis automation or post-tag source reliability.

## Evidence Confidence

| Class | Count | Confidence note |
|---|---:|---|
| `automation_post_tag_actual` | 1 | high for run occurrence; low for paper/source outcome |
| `manual_post_tag_equivalent` | 1 | high for handoff replay |
| `pre_tag_baseline` | 20 | high; excluded from post-tag counts |
| `historical_ci_evidence` | 3 | high for status metadata |
| `synthetic_test_fixture` | 0 | not counted |
| `unknown` | 0 | no unclassified ledger entries |

Overall post-tag reliability confidence remains low because there is no persisted Daily artifact and no actual Weekly run.

## Windows and Ubuntu CI Evidence

For current-head run `27336481022`:

- Ubuntu job: pass;
- Windows job: fail at repository tests;
- local Windows repository-scoped tests: pass;
- exact remote Windows failure log: `TODO_VERIFY`, because `gh` is not authenticated.

Windows CI affects one platform, not the Ubuntu result. It remains a production-change blocker until fixed or formally accepted as non-blocking.

## Manual Precision Sample

The generated offline sample contains 15 existing records and covers:

- lattice commitments, SIS/preimage sampling, and trapdoor topics;
- blind and linkable signature bridge examples;
- ML-KEM, ML-DSA, and implementation/fault background;
- LWE recovery and module-lattice reduction;
- a structure-aware lattice cryptanalysis ambiguity;
- clear and difficult false positives.

No threshold-PQC-specific record was verified. No paper metadata, professor fact, or production label was invented. Output files:

- `docs/research_tracks/v0.5_manual_precision_gold_sample_v0.1.json`;
- `docs/research_tracks/v0.5_manual_precision_gold_sample_v0.1.md`.

## v0.5 Precision Design Gate

Decision: `design_ready_with_more_annotation`.

Offline design may continue because the sample supports explanation design, false-positive review, and focused test planning. Before treating it as a gold sample, verify original sources, adjudicate ambiguous entries, and add a verified threshold-PQC example.

## v0.5 Production Change Gate

Decision: `blocked_by_multiple_conditions`.

Blockers:

1. the only actual post-tag Daily run failed to persist artifacts;
2. no actual post-tag Weekly run exists;
3. Windows CI is red;
4. the manual precision sample is not yet adjudicated;
5. tag/package version consistency is unresolved.

No taxonomy, ranking, query expansion, negative keyword, classifier, source, or package-version behavior changed.

## Continued Observation Plan

1. Observe the next persisted Daily run and capture workflow ID, artifact commit, source-health counts, IACR latest, and Semantic Scholar status.
2. Verify at least one actual post-tag Weekly Public Synthesis run.
3. Separate manual replay from automation evidence.
4. Inspect authenticated Windows CI failure logs.
5. Expand and adjudicate the offline precision sample.
6. Keep production implementation blocked until the documented gate exits are met.

## Changes Made

- Added a read-only post-tag evidence collector and Windows wrapper.
- Added a repository-record-only precision sample builder.
- Added 6 focused tests covering evidence taxonomy, tag-version extraction, and sample integrity.
- Added Phase 12Y reports, schemas, observations, CI impact analysis, and gate policies.
- Generated a 15-record offline Markdown/JSON precision sample.

No source implementation, source retry policy, ranking, taxonomy, query expansion, negative keyword, section classifier, reading queue, package version, tag, or authoritative daily artifact was changed.

## Validation Results

Final validation:

- Python: `3.15.0b2`;
- import check: passed;
- workflow doctor: passed;
- focused Phase 12Y tests: 6 passed;
- evidence collector: passed;
- sample builder: passed, 15 records;
- full repository tests: 458 passed;
- release hygiene: passed with the existing legacy tracked-artifact warning; package version remains `0.3.3`;
- `git diff --check`: passed, with the existing `.gitignore` LF-to-CRLF warning;
- tag verification: unchanged at `08c5f07967739ecd008773c4b167cd736848df88`;
- final worktree: dirty from pre-existing changes plus Phase 12Y untracked outputs; nothing was staged.

## TODO_VERIFY

- exact GitHub commit-step failure for run `27327344162`;
- first persisted post-tag Daily run;
- first actual post-tag Weekly run;
- Windows CI root cause;
- threshold-PQC sample coverage;
- intended relationship between tag `v0.4.0` and package version `0.3.3`.
