# Weekly Report Examples v0.1

Status: public examples. These examples use already-known public project artifacts and are not new paper claims.

## Example: Module-SIS Chameleon Hash Entry

| Paper | Source / ID | Anchor | Use for definition / proof / parameters / implementation | Action | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- |
| `BRaccoon: Concurrently Secure Blind Lattice Signatures from Raccoon` | IACR ePrint 2026/1084 | lattice signature / Raccoon / commitment keywords from digest metadata | related-work background for lattice signatures and privacy primitives | skim | verify assumptions; verify whether SIS / Module-SIS is directly involved |

Note:

- This is an example. Do not claim direct Module-SIS chameleon hash relevance until original paper reading verifies it.

## Example: Xingye Lu Technical Bridge Entry

| Paper | Source / ID | Technical bridge | Verified anchor | Action | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- |
| public ring-signature paper placeholder | TODO | linkable ring signature / anonymous authentication | TODO_VERIFY lattice/PQC anchor | watch | verify assumption and relation to post-quantum primitives |

Note:

- Do not include professor-specific claims or private application strategy.

## Example: MLWE / ML-KEM / ML-DSA Background Entry

| Paper | Source / ID | Scheme / primitive | Why it matters | Escalate? | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- |
| `On the Secrecy of the Encapsulation Coin in ML-KEM` | IACR ePrint 2026/1117 | ML-KEM / FIPS 203 / randomness | useful for PQC implementation-security maturity and checklist design | yes, if original paper supports reproducible checklist | verify threat model, library scope, and exact standard references |

## Example: AI4Lattice Longline Entry

| Paper | Source / ID | Lattice attack anchor | Baseline connection | Hype risk | Action | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- | --- |
| `Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE` | IACR ePrint 2026/1048 | LWE / dual attack | possible score/cost proxy for classical-grounded baseline | medium | backlog / read in ChatGPT web | verify score definition and whether ML labels are meaningful |

## Example: Noise / Exclusion Entry

| Paper | Matched generic term | Missing anchor | Exclusion reason | Recheck needed? |
| --- | --- | --- | --- | --- |
| generic privacy-preserving ML paper placeholder | privacy / ML | no explicit lattice/PQC/FHE anchor observed | generic privacy ML is not enough for this project | yes, only if original paper shows FHE / HE / lattice construction |

## Example: Next 3 Papers to Read in ChatGPT Web

| Rank | Paper | Track | Why read in ChatGPT web | First question |
| --- | --- | --- | --- | --- |
| 1 | Module-SIS or lattice commitment candidate | Module-SIS Chameleon Hash | direct quick-paper support | What assumption and trapdoor mechanism are used? |
| 2 | ML-KEM implementation-security candidate | MLWE / ML-KEM / ML-DSA Background | standards maturity | What is the exact threat model? |
| 3 | LWE attack-model candidate | AI4Lattice Longline | long-term baseline | Can the score/feature be made reproducible? |

## Example: Idea Backlog Update

| Idea seed | Track | Evidence | Short-term value | Long-term value | Risk | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- | --- |
| Module-SIS chameleon hash parameter checklist | Module-SIS Chameleon Hash | TODO paper cluster | supports quick-paper artifact | supports primitive research line | novelty risk | verify prior constructions and parameter standards |
