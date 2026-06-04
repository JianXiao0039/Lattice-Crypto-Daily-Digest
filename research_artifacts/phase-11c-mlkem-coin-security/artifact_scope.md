# Artifact Scope

## What This Artifact Is

This is a public reading-to-artifact scaffold for the Phase 11B selected paper:

Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE.

It supports:

- careful paper reading;
- parameter extraction;
- attack-model extraction;
- reproducibility planning;
- TODO_VERIFY tracking;
- cautious research-transfer planning.

## What This Artifact Is Not

It is not:

- a completed reproduction;
- a proof;
- an implementation;
- an attack;
- a benchmark result;
- a security claim;
- a claim that ML-KEM is affected;
- a claim about the selected paper's correctness.

## Folder Name Boundary

The folder name is:

`phase-11c-mlkem-coin-security`

This name follows the Phase 11C requested path. However, Phase 11B selected an LWE dual-attack paper, not the ML-KEM encapsulation coin paper. Therefore:

- ML-KEM / KEM coin-security fields are included only as TODO_VERIFY comparison scaffolding.
- The main artifact is LWE dual-attack reproducibility planning.
- If the research target shifts to `On the Secrecy of the Encapsulation Coin in ML-KEM`, a separate artifact should be created or this folder should be renamed in a future manual phase.

## Privacy Boundary

This artifact is public research tooling output. It must not contain:

- target PI emails;
- SoP drafts;
- funding strategy;
- personal PhD narrative;
- private application tracker content;
- private self-assessment.

## Automation Boundary

This artifact does not create:

- scheduled automation;
- Windows Task Scheduler tasks;
- cron jobs;
- background services;
- startup tasks;
- automatic future runs.
