# Weekly Track Scoring Rubric v0.1

Status: public triage rubric. This is not ranking code and does not change ranking thresholds.

## Score Range

Use 0-5 for each dimension:

- 0: absent
- 1: weak / generic
- 2: possible but unclear
- 3: plausible
- 4: strong
- 5: direct and verified

## Dimensions

| Dimension | 0 | 3 | 5 |
| --- | --- | --- | --- |
| lattice/PQC anchor strength | no hard anchor | plausible but needs TODO_VERIFY | explicit lattice/PQC/HE/FHE anchor |
| Module-SIS chameleon hash relevance | none | indirect primitive/proof background | direct SIS/Module-SIS/chameleon hash support |
| Xingye Lu technical bridge relevance | none | ring/privacy primitive but anchor uncertain | explicit lattice/PQC signature/privacy bridge |
| MLWE / ML-KEM / ML-DSA relevance | none | general PQC | direct standardized lattice scheme |
| AI4Lattice relevance | generic AI only | cryptography-adjacent ML | explicit lattice attack / LWE / BKZ link |
| short-term paper potential | none | useful related work | supports 2-4 week artifact |
| long-term value | none | background | durable research direction value |
| implementation / reproducibility potential | none | maybe extractable | parameters/code/checklist available |
| novelty risk | uncontrolled | moderate | low or manageable |
| verification burden | too high | moderate | low and source-backed |

## Action Mapping

| Action | Suggested condition |
| --- | --- |
| read_now | anchor strength 5 and short-term paper or implementation potential at least 4 |
| skim | strong anchor but indirect value |
| backlog | strong long-term value, not urgent |
| watch | plausible but missing verification |
| exclude | no hard anchor or generic-only |
| TODO_VERIFY | metadata or source evidence insufficient |

## Track-Specific Notes

### Module-SIS Chameleon Hash

Prefer high scores in:

- anchor strength;
- Module-SIS relevance;
- short-term paper potential;
- parameter/reproducibility potential.

### Xingye Lu Technical Bridge

Prefer public technical bridge evidence only. Do not score professor fit, funding, or application strategy in this public rubric.

### MLWE / ML-KEM / ML-DSA

Escalate only if the item helps standards maturity, implementation security, parameter understanding, or background for lattice/PQC work.

### AI4Lattice

Require explicit lattice attack anchor. High AI novelty without cryptanalytic grounding should be excluded or watchlisted.

## Non-Claim Policy

Scores are triage aids. They do not imply correctness, novelty, publication value, or security impact.
