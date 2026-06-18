# Phase 13R Real Paper Case Audit Log

## Artifact

- Month: `2026-06`
- Monthly JSON: `data/monthly/2026-06.json`
- Monthly Markdown: `digests/monthly/2026-06.md`
- Audit JSON: `docs/reports/phase-13r-real-paper-case-audit-log.json`

## Sample

| # | Paper | Bucket | Score | Evidence | Action quality | Keyword risk | Overclaim |
| ---: | --- | --- | ---: | --- | --- | --- | --- |
| 1 | From Perfect to Approximate Hints: Efficient LWE Secret Recovery Leveraging Low Hamming Weight | Top / A-class | 5 | abstract_supported | correct | none | low |
| 2 | Advancing Pseudorandom Codes: Beyond Parity Checks and Standard-Model CCA1 Security | Top / A-class | 5 | abstract_supported | correct | none | low |
| 3 | Towards Post-Quantum Secure Pharmacovigilance with ML-KEM and ML-DSA | Top / A-class | 5 | abstract_supported | correct | none | low |
| 4 | BRaccoon: Concurrently Secure Blind Lattice Signatures from Raccoon | Should Skim | 4 | abstract_supported | too_strong | none | low |
| 5 | Rank Ceiling for Twiddle-Perturbation Faults on the Forward NTT | Should Skim | 4 | abstract_supported | too_strong | none | none |
| 6 | Bootstrapping is All You Need: Secure Transformer Inference via Improved CKKS Functional Bootstrapping | Track Later | 4 | abstract_supported | too_strong | none | low |
| 7 | Butterfly Effect: Multi-Key FHE from Ring-LWR | Track Later | 4 | abstract_supported | too_strong | none | none |
| 8 | Achieving Shannon Capacity for Computationally Bounded Errors | Ignore / Peripheral | 4 | abstract_supported | too_strong | none | none |

## Findings

- Top paper rationale is useful and evidence-grounded.
- No sampled case was keyword-only.
- All sampled cases include `TODO_VERIFY`.
- All sampled cases use abstract-supported evidence and do not claim conclusion support.
- Reading action wording is too strong for 5 / 8 sampled cases.

## Fix List

- Align rendered reading action with Monthly bucket.
- Consider rendered bilingual top-paper block or explicitly document compact alternative in Monthly output.
