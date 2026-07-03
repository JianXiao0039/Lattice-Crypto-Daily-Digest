from __future__ import annotations

import re
from dataclasses import dataclass


TODO_VERIFY = "TODO_VERIFY"


@dataclass(frozen=True)
class VenueRegistryEntry:
    canonical_venue_name: str
    aliases: tuple[str, ...]
    venue_type: str
    source_family: str
    publisher_or_source: str
    ccf_rank: str
    ccf_status: str
    ccf_evidence_status: str
    applicability: str
    topic_area: str
    expanded_security_crypto_systems_scope: bool
    venue_relevance: str
    confidence: str
    todo_verify_required: bool
    notes: str = ""


def _entry(
    canonical_venue_name: str,
    aliases: tuple[str, ...],
    venue_type: str,
    source_family: str,
    publisher_or_source: str,
    ccf_rank: str,
    ccf_status: str,
    ccf_evidence_status: str,
    applicability: str,
    topic_area: str,
    expanded_scope: bool,
    venue_relevance: str,
    confidence: str,
    todo_verify_required: bool,
    notes: str = "",
) -> VenueRegistryEntry:
    if ccf_rank in {"A", "B", "C"} and ccf_status != "trusted_local":
        raise ValueError(f"{canonical_venue_name}: CCF A/B/C requires trusted_local status")
    if ccf_rank == "N/A" and applicability not in {
        "preprint_source",
        "eprint_source",
        "standard_source",
        "advisory_source",
        "metadata_index",
    }:
        raise ValueError(f"{canonical_venue_name}: CCF N/A requires non-applicable source type")
    return VenueRegistryEntry(
        canonical_venue_name=canonical_venue_name,
        aliases=aliases,
        venue_type=venue_type,
        source_family=source_family,
        publisher_or_source=publisher_or_source,
        ccf_rank=ccf_rank,
        ccf_status=ccf_status,
        ccf_evidence_status=ccf_evidence_status,
        applicability=applicability,
        topic_area=topic_area,
        expanded_security_crypto_systems_scope=expanded_scope,
        venue_relevance=venue_relevance,
        confidence=confidence,
        todo_verify_required=todo_verify_required,
        notes=notes,
    )


VENUE_REGISTRY: tuple[VenueRegistryEntry, ...] = (
    _entry("CRYPTO", ("crypto", "iacr crypto"), "conference", "iacr", "IACR", "A", "trusted_local", "repo_policy", "paper_venue", "cryptography", True, "direct", "high", False),
    _entry("EUROCRYPT", ("eurocrypt",), "conference", "iacr", "IACR", "A", "trusted_local", "repo_policy", "paper_venue", "cryptography", True, "direct", "high", False),
    _entry("ASIACRYPT", ("asiacrypt",), "conference", "iacr", "IACR", "A", "trusted_local", "repo_policy", "paper_venue", "cryptography", True, "direct", "high", False),
    _entry("CHES/TCHES", ("ches", "tches", "transactions on cryptographic hardware and embedded systems"), "journal", "iacr", "IACR", "A", "trusted_local", "repo_policy", "paper_venue", "cryptography", True, "direct", "high", False),
    _entry("ACM CCS", ("acm ccs", "computer and communications security"), "conference", "acm", "ACM", "A", "trusted_local", "repo_policy", "paper_venue", "security", True, "direct", "high", False),
    _entry("IEEE S&P", ("ieee s&p", "ieee symposium on security and privacy", "oakland"), "conference", "ieee", "IEEE", "A", "trusted_local", "repo_policy", "paper_venue", "security", True, "direct", "high", False),
    _entry("USENIX Security", ("usenix security", "usenix security symposium"), "conference", "usenix", "USENIX", "A", "trusted_local", "repo_policy", "paper_venue", "security", True, "direct", "high", False),
    _entry("NDSS", ("ndss", "network and distributed system security"), "conference", "internet society", "Internet Society", "A", "trusted_local", "repo_policy", "paper_venue", "security", True, "direct", "high", False),
    _entry("PKC", ("pkc", "public key cryptography"), "conference", "iacr", "IACR", "B", "trusted_local", "repo_policy", "paper_venue", "cryptography", True, "direct", "medium", False),
    _entry("TCC", ("tcc", "theory of cryptography"), "conference", "iacr", "IACR", "B", "trusted_local", "repo_policy", "paper_venue", "cryptography", True, "direct", "medium", False),
    _entry("ESORICS", ("esorics",), "conference", "springer", "Springer", "B", "trusted_local", "repo_policy", "paper_venue", "security", True, "peripheral", "medium", False),
    _entry("AsiaCCS", ("asiaccs", "asia ccs", "asia-ccs"), "conference", "acm", "ACM", "B", "trusted_local", "repo_policy", "paper_venue", "security", True, "peripheral", "medium", False),
    _entry("PQCrypto", ("pqcrypto", "post-quantum cryptography conference"), "conference", "pqc", "PQCrypto", "unknown", "unknown", "missing_trusted_source", "paper_venue", "pqc", True, "direct", "medium", True),
    _entry("SAC", ("sac", "selected areas in cryptography"), "conference", "springer", "Springer", "unknown", "unknown", "missing_trusted_source", "paper_venue", "cryptography", True, "peripheral", "medium", True),
    _entry("LATINCRYPT", ("latincrypt",), "conference", "springer", "Springer", "unknown", "unknown", "missing_trusted_source", "paper_venue", "cryptography", True, "peripheral", "medium", True),
    _entry("RAID", ("raid", "research in attacks intrusions and defenses"), "conference", "security", "RAID", "unknown", "unknown", "missing_trusted_source", "paper_venue", "security", True, "peripheral", "medium", True),
    _entry("ACSAC", ("acsac", "annual computer security applications conference"), "conference", "security", "ACSAC", "unknown", "unknown", "missing_trusted_source", "paper_venue", "security", True, "peripheral", "medium", True),
    _entry("DSN", ("dsn", "dependable systems and networks"), "conference", "ieee", "IEEE", "unknown", "unknown", "missing_trusted_source", "paper_venue", "systems_security", True, "peripheral", "medium", True),
    _entry("CSF", ("csf", "computer security foundations"), "conference", "ieee", "IEEE", "unknown", "unknown", "missing_trusted_source", "paper_venue", "security", True, "peripheral", "medium", True),
    _entry("Journal of Cryptology", ("journal of cryptology",), "journal", "springer/iacr", "Springer/IACR", "unknown", "unknown", "missing_trusted_source", "paper_venue", "cryptography", True, "direct", "medium", True),
    _entry("Designs, Codes and Cryptography", ("designs codes and cryptography", "designs, codes and cryptography"), "journal", "springer", "Springer", "unknown", "unknown", "missing_trusted_source", "paper_venue", "cryptography", True, "peripheral", "medium", True),
    _entry("Cybersecurity", ("cybersecurity",), "journal", "springer", "TODO_VERIFY", TODO_VERIFY, "todo_verify", "missing_trusted_source", "paper_venue", "journal_security", True, "peripheral", "low", True),
    _entry("Computers & Security", ("computers & security", "computers and security"), "journal", "elsevier", "Elsevier", TODO_VERIFY, "todo_verify", "missing_trusted_source", "paper_venue", "journal_security", True, "peripheral", "low", True),
    _entry("IEEE Transactions on Information Forensics and Security", ("ieee transactions on information forensics and security", "ieee tifs", "tifs"), "journal", "ieee", "IEEE", TODO_VERIFY, "todo_verify", "missing_trusted_source", "paper_venue", "journal_security", True, "peripheral", "low", True),
    _entry("IEEE Transactions on Dependable and Secure Computing", ("ieee transactions on dependable and secure computing", "ieee tdsc", "tdsc"), "journal", "ieee", "IEEE", TODO_VERIFY, "todo_verify", "missing_trusted_source", "paper_venue", "journal_security", True, "peripheral", "low", True),
    _entry("ACM Transactions on Privacy and Security", ("acm transactions on privacy and security", "acm tops", "tops"), "journal", "acm", "ACM", TODO_VERIFY, "todo_verify", "missing_trusted_source", "paper_venue", "journal_security", True, "peripheral", "low", True),
    _entry("Journal of Computer Security", ("journal of computer security",), "journal", "ios press", "IOS Press", TODO_VERIFY, "todo_verify", "missing_trusted_source", "paper_venue", "journal_security", True, "peripheral", "low", True),
    _entry("IACR ePrint", ("iacr eprint", "cryptology eprint archive", "iacr_eprint"), "preprint", "iacr", "IACR", "N/A", "not_applicable", "not_applicable", "eprint_source", "preprint", True, "direct", "high", False),
    _entry("arXiv", ("arxiv",), "preprint", "arxiv", "arXiv", "N/A", "not_applicable", "not_applicable", "preprint_source", "preprint", True, "direct", "high", False),
    _entry("NIST", ("nist", "nist pqc", "fips"), "standardization body", "nist", "NIST", "N/A", "not_applicable", "not_applicable", "standard_source", "standardization", True, "direct", "high", False),
    _entry("IETF", ("ietf", "rfc", "internet-draft"), "standardization body", "ietf", "IETF", "N/A", "not_applicable", "not_applicable", "standard_source", "standardization", True, "direct", "high", False),
    _entry("Vendor Security Advisory", ("vendor security advisory", "security advisory", "cve", "vendor release", "implementation release notes"), "vendor/security advisory", "vendor", "vendor/security advisory", "N/A", "not_applicable", "not_applicable", "advisory_source", "advisory", True, "direct", "medium", False),
    _entry("Crossref", ("crossref",), "indexing source", "crossref", "Crossref", "N/A", "not_applicable", "not_applicable", "metadata_index", "metadata", False, "source_only", "medium", False),
    _entry("DBLP", ("dblp",), "indexing source", "dblp", "DBLP", "N/A", "not_applicable", "not_applicable", "metadata_index", "metadata", False, "source_only", "medium", False),
    _entry("OpenAlex", ("openalex",), "indexing source", "openalex", "OpenAlex", "N/A", "not_applicable", "not_applicable", "metadata_index", "metadata", False, "source_only", "medium", False),
    _entry("Semantic Scholar", ("semantic scholar", "semantic_scholar"), "indexing source", "semantic_scholar", "Semantic Scholar", "N/A", "not_applicable", "not_applicable", "metadata_index", "metadata", False, "source_only", "medium", False),
)


def _metadata_key_matches(text: str, key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    normalized_key = re.sub(r"[^a-z0-9]+", " ", key.lower()).strip()
    if not normalized_key:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(normalized_key) + r"(?![a-z0-9])"
    return re.search(pattern, normalized) is not None


def _matches_entry(text: str, entry: VenueRegistryEntry) -> bool:
    return any(_metadata_key_matches(text, alias) for alias in entry.aliases)


def find_registry_entry(raw_venue: str, raw_source: str) -> VenueRegistryEntry | None:
    venue_text = raw_venue.strip().lower()
    source_text = raw_source.strip().lower()
    paper_entries = [entry for entry in VENUE_REGISTRY if entry.applicability not in {"metadata_index"}]
    metadata_entries = [entry for entry in VENUE_REGISTRY if entry.applicability == "metadata_index"]

    if venue_text:
        for entry in paper_entries:
            if _matches_entry(venue_text, entry):
                return entry
        return None

    if source_text:
        for entry in paper_entries:
            if entry.applicability in {"preprint_source", "eprint_source", "standard_source", "advisory_source"} and _matches_entry(source_text, entry):
                return entry
        for entry in metadata_entries:
            if _matches_entry(source_text, entry):
                return entry
    return None
