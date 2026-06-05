# Quick-Paper Handoff Decision Rubric v0.1

Status: public manual triage rubric. It does not replace existing ranking scores or labels.

# Scoring Dimensions

Score each dimension from 0 to 5.

| Dimension | 0 | 1-2 | 3 | 4-5 |
| --- | --- | --- | --- | --- |
| direct Module-SIS relevance | none | generic SIS/module mention | adjacent Module-SIS context | direct and actionable Module-SIS content |
| chameleon hash relevance | none | generic hash | commitment/chameleon adjacent | direct chameleon hash definition/construction/security |
| SIS / commitment / trapdoor relevance | none | generic primitive | one relevant concept | concrete assumption, mechanism, or verified model |
| proof usefulness | none | broad intuition | possible definition/model support | explicit verified proof obligation/technique |
| parameterization usefulness | none | general parameters | possible estimator/bound relevance | concrete reproducible inputs or bounds |
| implementation usefulness | none | general engineering | transferable method | concrete tests, reference implementation, or benchmark method |
| comparison table usefulness | none | category only | plausible baseline | verified comparison dimensions |
| Xingye Lu bridge usefulness | none | generic ring/privacy | possible public technical bridge | verified lattice/PQC bridge |
| verification burden | minimal | limited metadata check | original-paper reading | broad or ambiguous verification |
| overclaim risk | minimal | controllable | moderate | high security/novelty risk |

# Interpretation

The first eight dimensions measure usefulness. The last two measure caution cost.

Do not calculate a false-precision universal total. Use the score profile and written evidence.

# Action Labels

## handoff_now

Use when:

- clear lattice/PQC anchor;
- concrete artifact task;
- direct or strong adjacent usefulness;
- verified facts are sufficient;
- non-claims control risk;
- remaining TODO_VERIFY does not block intake.

## handoff_after_verify

Use when:

- candidate appears actionable;
- original paper, assumption, construction, or source claim is not verified;
- verification would unlock a concrete artifact task.

## keep_in_radar

Use when:

- track relevance exists;
- no concrete artifact task exists yet;
- future evidence could change the decision.

## backlog

Use when:

- useful background or long-term value exists;
- immediate quick-paper actionability is low.

## exclude

Use when:

- no hard lattice/PQC anchor;
- generic keyword match only;
- no plausible artifact use;
- verification cost is unjustified.

# Decision Table

| Evidence pattern | Recommended action |
| --- | --- |
| direct Module-SIS/chameleon hash + verified source + named artifact task | handoff_now |
| direct/adjacent value + missing original-paper verification | handoff_after_verify |
| strong lattice/PQC item + no current quick-paper use | keep_in_radar |
| background standards/implementation item | backlog |
| generic hash/commitment/privacy/AI without anchor | exclude |

# Risk Overrides

Regardless of usefulness score, do not use `handoff_now` when:

- security claim is unverified;
- novelty is inferred rather than checked;
- source identity is uncertain;
- parameters are presented as secure without evidence;
- candidate is only professor-specific speculation;
- private application material would cross workspace boundaries.

# Manual Review Questions

1. What exact artifact task becomes possible?
2. Which verified fact supports the transfer?
3. What remains TODO_VERIFY?
4. What must not be claimed?
5. Which artifact file or matrix receives the packet?
6. Would the packet still be useful without its relevance score?

