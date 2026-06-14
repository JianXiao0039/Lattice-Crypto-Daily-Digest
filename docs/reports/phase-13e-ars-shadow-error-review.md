# Phase 13E ARS Shadow Error Review

## Skill Use

`academic-research-suite` was available as a user-level skill. The experiment-agent workflow was used as a methodology checklist for reproducibility, sample leakage, error taxonomy, evidence provenance, and stopping criteria.

No full runtime, agent team, hooks, background agent, or external cross-model review was enabled.

## Review Findings

1. The 67-record pilot is repository-grounded, but zero rows are human gold.
2. Production-shadow disagreement and Codex-review-shadow disagreement must remain separate measurements.
3. Auxiliary taxonomy tags and matched keywords must not independently establish a track.
4. Rule revision requires held-out user-adjudicated data to avoid tuning against the review set.
5. Ambiguous cases must remain unresolved rather than forced into a track.
6. The current evidence supports error hypotheses and review priorities, not accuracy claims.

## Reproducibility Controls

- Inputs are named and versioned.
- v0.2 rules are marked `candidate_not_promoted` and experimental-only.
- The review script writes only to an explicit documentation output directory.
- Focused tests check output isolation and production non-integration.
- Production workflows do not call the review script.
- Pilot predictions retain their evidence so review results do not depend on a stale static sample snapshot.
