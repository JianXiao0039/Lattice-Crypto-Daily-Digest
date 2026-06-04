# Original Paper Verification Note

Status: public artifact verification note.

## Selected Paper

On the Secrecy of the Encapsulation Coin in ML-KEM

- Source: IACR ePrint 2026/1117
- Page: `https://eprint.iacr.org/2026/1117`
- PDF: `https://eprint.iacr.org/2026/1117.pdf`

## Source Access Status

- IACR ePrint page: accessible.
- IACR PDF: accessible and downloaded to `original_paper/iacr-2026-1117.pdf`.
- IACR page snapshot: saved to `original_paper/iacr-2026-1117-page.html`.
- NIST FIPS 203 landing page: accessible.
- NIST FIPS 203 direct PDF URL attempted in this phase: TODO_VERIFY because attempted direct URL returned 404.

## Verified Metadata

| Field | Value |
| --- | --- |
| Title | On the Secrecy of the Encapsulation Coin in ML-KEM |
| Authors | Madjid G. Tehrani; William J Buchanan; Mouad Lemoudden |
| Source | Cryptology ePrint Archive |
| ePrint ID | 2026/1117 |
| Keywords | ML-KEM; FIPS 203; randomness; encapsulation coin |
| Abstract | observed on IACR page; not reproduced in full here |
| Section list | TODO_VERIFY from PDF |

## TODO_FETCH_PDF

Not needed for IACR 2026/1117: PDF was fetched successfully.

Still TODO:

- verify PDF title page;
- extract actual section names;
- read abstract/introduction;
- extract definitions and parameters.

## Original Paper vs Artifact Checklist

| Artifact item | Current status | Original paper verification |
| --- | --- | --- |
| ML-KEM coin-security scope | now supported by selected paper metadata | TODO_VERIFY technical details |
| Parameter checklist | scaffold exists | fill only after reading PDF |
| Reproducibility plan | scaffold exists | update after experiment/setup sections |
| TODO_VERIFY list | scaffold exists | add page/section references |
| LWE dual-attack language from Phase 11C | historical mismatch | should be cleaned in future phase or split into separate artifact |

## Standard Comparison Checklist

- [ ] Locate FIPS 203 key generation section.
- [ ] Locate FIPS 203 encapsulation section.
- [ ] Locate FIPS 203 decapsulation section.
- [ ] Identify where randomness / coins appear.
- [ ] Identify parameter sets.
- [ ] Compare paper terminology with standard terminology.
- [ ] Record what cannot be concluded without full standard text.

## Non-Claims

This note does not claim:

- the paper proves a security break;
- the paper proves a backdoor;
- any implementation is vulnerable beyond what the paper explicitly supports;
- experiments were reproduced;
- ML-KEM standard is flawed;
- any code has been run.

This note only records source access, metadata verification, and a plan for original-paper reading.
