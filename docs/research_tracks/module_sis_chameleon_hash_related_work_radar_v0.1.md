# Module-SIS Chameleon Hash Related Work Radar v0.1

Status: public research radar. This is not a deep reading note and not a proof.

## Directly Relevant

Current recent digest status:

- No verified direct Module-SIS chameleon hash construction found in W23.

Needed:

- lattice-based chameleon hash constructions;
- SIS / Module-SIS commitments;
- trapdoor collision mechanisms.

## Construction-Adjacent

| Candidate | Why adjacent | Action | TODO_VERIFY |
| --- | --- | --- | --- |
| BRaccoon: Concurrently Secure Blind Lattice Signatures from Raccoon | lattice signature / privacy primitive context | skim | assumptions and relation to SIS / Module-SIS |
| Witness Pseudorandom Functions for Vector Commitments and Applications | commitment-related topic with LWE/SIS metadata | skim | whether construction is lattice-based |
| HRA-Secure Lattice-based Proxy Re-Encryption without Noise Flooding | lattice-based PRE / LWE background | backlog | relevance to primitive proof techniques |
| Ciphertext-Updatable Attribute-Based and Predicate Encryption from Lattices | lattice advanced primitive background | backlog | assumptions and transferability |

## Parameterization / Implementation Support

| Candidate | Why useful | Action | TODO_VERIFY |
| --- | --- | --- | --- |
| Improved Dual Attack and Trapdoor Sampling via Quantum Rejection Sampling | trapdoor sampling and attack background | read_now | whether it informs trapdoor/adaptation mechanism |
| Module Lattice Security (Part IV) | module-lattice security caution | watch | exact claim and relation to Module-SIS |
| KAT-Seeded Fuzzing of Stateful Hash-Based Signature Verification in liboqs | reproducibility / implementation discipline | watch | whether relevant to lattice signatures |

## Background Only

- `On the Secrecy of the Encapsulation Coin in ML-KEM`: useful PQC maturity background, not quick-paper core.
- `When Removing Reductions Goes Wrong`: ML-DSA implementation background.
- FHE / CKKS / BGV papers: useful only if parameterization/reproducibility lessons transfer.

## Exclude / Noise

- Generic privacy ML or GBDT papers without verified lattice/FHE construction.
- Generic ring signature papers without lattice/PQC anchor.
- Generic hash or commitment papers without SIS/lattice anchor.

## Weekly Radar Rule

Escalate only if a paper can plausibly support:

- definition;
- proof sketch;
- assumption mapping;
- parameter selection;
- implementation artifact;
- related-work comparison.
