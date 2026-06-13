# Phase 13C Shadow Classifier Evaluation Log

## Inputs

- Phase 13B repository-grounded sample: 62 records.
- Human gold labels: 0.
- Experimental rules: `experiments/v0_5_shadow_track_rules.json`.

## Run Result

- Shadow records: 62.
- Exact production-shadow primary/secondary matches: 27.
- Primary-track disagreements: 23.
- Production-labeled/shadow-irrelevant: 10.
- Secondary-track disagreements: 2.
- Shadow Track A: 1.
- Shadow Track B: 0.
- Shadow Track C: 3.
- Shadow Track D: 46.
- Shadow irrelevant: 12.

## Corrections During Design

1. Removed broad `PQC`, `post-quantum`, and generic `implementation` direct positives from Track D.
2. Removed Phase 13B positive/exclusion annotation text from prediction inputs to prevent label leakage.
3. Added tests for generic commitment, generic ML, human-review boundaries, output isolation, and production non-integration.

## Interpretation

The run exposes useful disagreements but does not measure accuracy. Track D over-inclusion and Track B under-coverage remain design limitations.
