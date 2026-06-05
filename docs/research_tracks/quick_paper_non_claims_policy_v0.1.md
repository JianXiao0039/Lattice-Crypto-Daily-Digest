# Quick-Paper Non-Claims Policy v0.1

Status: public research safety policy.

# Purpose

Prevent a research-radar handoff from being mistaken for a cryptographic result.

# A Handoff Is

- a structured transfer of potentially useful public research material;
- an evidence-and-question packet;
- a pointer to a concrete artifact task;
- a record of verification gaps;
- a public research workflow artifact.

# A Handoff Is Not

- a security proof;
- a reduction;
- a novelty claim;
- a claim that a construction works;
- a claim that Module-SIS is the correct or sufficient assumption;
- a claim that parameters are secure;
- an implementation result;
- a benchmark result;
- a publishable contribution;
- a professor-specific fact or private application statement.

# Required Non-Claims by Category

## Construction candidate

State:

- no working construction is claimed;
- correctness and adaptation remain TODO_VERIFY;
- trapdoor mechanism remains TODO_VERIFY;
- security model remains TODO_VERIFY.

## Proof candidate

State:

- proof usefulness is provisional;
- no full reduction is claimed;
- assumption compatibility remains TODO_VERIFY.

## Parameterization candidate

State:

- no parameter set is claimed secure;
- estimator inputs and bounds require verification;
- toy values are not production recommendations.

## Implementation candidate

State:

- no production readiness is claimed;
- no benchmark result is claimed unless logs exist;
- implementation may be a toy or reproducibility scaffold.

## Related-work candidate

State:

- title/metadata does not establish technical relevance;
- original paper reading is required;
- no novelty comparison is claimed.

## Public technical bridge candidate

State:

- no professor-specific fact is claimed;
- no PI fit or application strategy is included;
- the bridge is technical and TODO_VERIFY.

# Evidence Separation

Every packet must separate:

- verified facts;
- background context;
- inferred possible use;
- TODO_VERIFY;
- non-claims.

# Forbidden Wording

Avoid:

- "this proves";
- "secure parameters";
- "novel construction";
- "production-ready";
- "directly applicable" without verification;
- "confirmed fit";
- any unsupported performance or security conclusion.

# Safe Wording

Prefer:

- "may support";
- "possible artifact use";
- "metadata suggests";
- "needs original-paper verification";
- "proof obligation";
- "toy implementation scope";
- "no security claim";
- "TODO_VERIFY".

# Enforcement

If a packet cannot state its non-claims clearly, it must remain `keep_in_radar`, `backlog`, or `exclude`.

