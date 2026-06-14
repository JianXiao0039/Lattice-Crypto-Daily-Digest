# Phase 13E Shadow Error Review Log

## Inputs

- Phase 13D adjudicated annotations: 25 rows, 0 valid human-gold labels.
- Refreshed Phase 13D shadow pilot predictions: 67 records.
- Existing v0.1 shadow rules: diagnostic baseline.
- v0.2 rules: experimental candidate, not executed by production.

## Results

- Production-shadow agreements: 29.
- Production-shadow disagreements: 38.
- Codex-review-shadow disagreements: 27.
- Reviewed union: 42.
- Primary causes: generic keyword false positive 17; production label limitation 13; ambiguous paper 7; bad rule 3; bad track definition 2.
- Contributing causes: generic keyword false positive 21; bad rule 20; production label limitation 13; ambiguous paper 7; shadow overreach 3; bad track definition 2.
- Author-name leakage observed: 0.
- Insufficient-metadata cases observed: 0.

All counts are diagnostic and non-gold.

## Per-Track Summary

- Track A: 5 Codex-reviewed, 1 shadow exact, 4 missed, 1 shadow selection.
- Track B: 6 Codex-reviewed, 0 shadow exact, 6 missed, 0 shadow selections.
- Track C: 10 Codex-reviewed, 3 shadow exact, 7 missed, 3 shadow selections.
- Track D: 28 Codex-reviewed, 28 shadow exact; shadow selected Track D for 50 records.

## Diagnostic Fix

The initial review failed on `v05-0063` because the dynamic 67-record pilot had outgrown the static 62-record sample. Predictions now retain `available_evidence`, and the review falls back to that self-contained evidence for broader-pool records. No production classifier or workflow was changed.
