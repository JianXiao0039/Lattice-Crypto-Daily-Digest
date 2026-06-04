# AI4Lattice Longline Track

Status: public research track document.

## Purpose

Track long-term AI-assisted lattice cryptanalysis ideas while avoiding unrealistic claims. This track supports future experiment planning around classical-grounded attack assistance.

## In-Scope

- Swin-guided coordinate selection for LWE / RLWE / MLWE.
- Sparse LWE secret recovery.
- RLWE / MLWE negative-cyclic modeling.
- Dual / primal / hybrid attack support.
- BKZ / lattice reduction interfaces.
- Support recovery and candidate ranking.
- Attack-cost proxy.
- Learned pruning.
- Parameter prediction.
- Structured modular arithmetic for cryptanalytic tasks.

## Required Anchor

AI/ML papers must explicitly connect to at least one:

- LWE / RLWE / MLWE;
- SIS / NTRU;
- lattice cryptanalysis;
- BKZ / lattice reduction;
- dual / primal / hybrid attacks;
- cryptographic modular arithmetic;
- attack search, ranking, or pruning.

## Out-of-Scope

- generic AI;
- generic LLM;
- generic optimization;
- generic graph/image/model/code tasks;
- generic federated learning;
- generic privacy ML without lattice/PQC/FHE anchor.

## Weekly Watchlist Template

| Paper | Lattice attack anchor | Possible baseline | Feature / label idea | Hype risk | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- |
| TODO | LWE / BKZ / dual / hybrid | TODO | TODO | low/medium/high | TODO |

## Non-Claim Policy

Do not claim:

- AI breaks MLWE;
- learned model improves real-parameter attacks;
- toy experiments transfer to real security;
- labels are valid without classical baseline.

All AI4Lattice ideas require baseline comparison.
