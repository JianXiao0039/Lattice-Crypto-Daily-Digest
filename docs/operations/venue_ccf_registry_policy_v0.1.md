# Venue / CCF Registry Policy v0.1

## Purpose

The daily lattice/PQC radar uses a deterministic local venue and source-type
registry to enrich item metadata without fabricating CCF rank, venue status, or
publisher information.

## Registry Principles

- CCF `A`, `B`, or `C` may be emitted only when the local registry marks the
  entry as `ccf_status=trusted_local`.
- `CCF_rank=N/A` is reserved for non-applicable source types such as preprint,
  ePrint, standards, advisories, vendor/library release notes, and
  indexing-only metadata sources when no paper venue applies.
- Possible paper venues without trusted local rank use `unknown` or
  `TODO_VERIFY`.
- Crossref, DBLP, OpenAlex, and Semantic Scholar are metadata/indexing sources.
  They are not CCF authorities.
- arXiv remains a preprint source unless the record is explicitly matched to a
  trusted local venue.
- IACR ePrint remains an ePrint/preprint source unless the record is explicitly
  matched to a trusted local venue.
- Unknown journal or conference status must remain visible through conservative
  metadata and item-level `TODO_VERIFY` flags.

## Source Families

- Cryptography/PQC/lattice venues include CRYPTO, EUROCRYPT, ASIACRYPT, CHES,
  TCHES, PKC, TCC, PQCrypto, SAC, LATINCRYPT, Journal of Cryptology, and
  Designs, Codes and Cryptography.
- Security venues include ACM CCS, IEEE S&P, USENIX Security, NDSS, ESORICS,
  AsiaCCS, RAID, ACSAC, DSN, and CSF.
- Security-journal candidates include Cybersecurity, Computers & Security, IEEE
  Transactions on Information Forensics and Security, IEEE Transactions on
  Dependable and Secure Computing, ACM Transactions on Privacy and Security, and
  Journal of Computer Security.
- Metadata/indexing sources include Crossref, DBLP, OpenAlex, and Semantic
  Scholar.
- Non-paper source types include NIST, IETF, standards, vendor advisories, and
  implementation release notes.

## Non-Interference

Venue and CCF metadata enrichment must not change:

- freshness policy;
- primary today/new eligibility;
- ranking behavior;
- taxonomy behavior;
- relevance classification;
- retrieval source set;
- background automation policy.

Freshness remains a hard gate before ranking. A stale paper from a high-value
venue must not enter the primary today/new section without an allowed freshness
reason.
