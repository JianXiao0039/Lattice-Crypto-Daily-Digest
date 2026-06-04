# Phase 11C Mini-Artifact

## Selected Paper

Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE

- Source / ID: IACR ePrint 2026/1048
- URL: `https://eprint.iacr.org/2026/1048`
- Selection source: Phase 11B deep reading pack

## Purpose

This folder turns the Phase 11B selected paper into a public reading-to-artifact scaffold. It is designed to support parameter extraction, reproducibility planning, and cautious research transfer from digest metadata to technical reading.

## Scope

This artifact focuses on:

- LWE dual attack reading;
- score-distribution TODO_VERIFY extraction;
- covariance-model TODO_VERIFY extraction;
- parameter/security checklist planning;
- possible downstream AI4Lattice baseline mapping.

The folder name contains `mlkem-coin-security` because the Phase 11C prompt requested that path. Since Phase 11B selected an LWE dual-attack paper, ML-KEM coin-security items are treated only as comparison fields and TODO_VERIFY items.

## Files

- `README.md`: overview and usage.
- `parameter_checklist.md`: checklist for LWE dual-attack extraction and ML-KEM/KEM coin-security comparison fields.
- `reproducibility_plan.md`: 2-hour, 1-day, 1-week, and 1-month artifact levels.
- `todo_verify.md`: unverified technical points.
- `artifact_scope.md`: boundaries and non-claims.

## How to Use

1. Read the original paper abstract and introduction.
2. Fill `todo_verify.md` with verified section/page references.
3. Fill `parameter_checklist.md` only with facts from the paper.
4. Use `reproducibility_plan.md` to choose a small next artifact.
5. Keep all claims cautious until definitions, parameters, and experiments are verified.

## TODO_VERIFY

- exact problem setting;
- exact attack model;
- score definition;
- covariance target;
- parameters;
- relation to MLWE / ML-KEM;
- whether any experiment or implementation exists.

## Not a Security Claim

This artifact is not a proof, reproduction, attack, implementation result, or claim about the paper's correctness. It is a public reading scaffold.
