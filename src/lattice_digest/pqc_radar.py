from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from lattice_digest.config import load_config_bundle, load_structured_file, project_root


IMPLEMENTATION_REVIEW_DATE = "2026-06-25"


class EvidenceTier(str, Enum):
    S0 = "S0"
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"


@dataclass(frozen=True)
class SchemeEntry:
    canonical_name: str
    aliases: tuple[str, ...]
    scheme_family: str
    underlying_assumption: str
    lifecycle_status: str
    standard_identifier: str = ""
    standardization_body: str = ""
    process_name: str = ""
    current_round_or_stage: str = ""
    evidence_tier: EvidenceTier = EvidenceTier.S4
    primary_source_label: str = ""
    last_verified_at: str = IMPLEMENTATION_REVIEW_DATE
    confidence: str = "medium"
    todo_verify: bool = True
    historical: bool = False


@dataclass(frozen=True)
class DynamicStatus:
    scheme: str
    current_status: str
    previous_status: str = ""
    round_or_stage: str = ""
    process_name: str = ""
    primary_source: str = ""
    evidence_tier: EvidenceTier = EvidenceTier.S4
    last_verified_at: str = IMPLEMENTATION_REVIEW_DATE
    status_confidence: str = "medium"
    todo_verify: bool = True


@dataclass(frozen=True)
class HawkDecision:
    accepted: bool
    reason: str
    matched_crypto_contexts: tuple[str, ...] = ()
    matched_negative_contexts: tuple[str, ...] = ()


@dataclass(frozen=True)
class InclusionDecision:
    accepted: bool
    reason: str
    lattice_anchors: tuple[str, ...] = ()
    material_impact_terms: tuple[str, ...] = ()
    todo_verify: bool = False


@dataclass(frozen=True)
class QueryFamily:
    identifier: str
    description: str
    scheme_or_lattice_anchors: tuple[str, ...]
    process_or_event_anchors: tuple[str, ...]
    context_anchors: tuple[str, ...]
    noise_terms: tuple[str, ...] = ()
    academic_sources: tuple[str, ...] = ()
    official_status_sources: tuple[str, ...] = ()
    production_retrieval_enabled: bool = False


@dataclass(frozen=True)
class DryRunAdapterConstraint:
    adapter_id: str
    status: str
    accepted_input: str
    rejected_input: str
    output_schema: str
    evidence_tier_mapping: str
    source_health_behavior: str
    source_starved_behavior: str
    todo_verify_behavior: str
    implementation_risk: str


@dataclass(frozen=True)
class SourceAwareQueryPlan:
    family: str
    adapter_id: str
    status: str
    architecture: str
    production_retrieval_enabled: bool
    accepted_input: str
    rejected_input: str
    output_schema: str
    query_groups: tuple[tuple[str, ...], ...] = ()
    queries: tuple[str, ...] = ()
    post_filter_terms: tuple[str, ...] = ()
    disabled_reason: str = ""
    evidence_tier_mapping: str = ""
    source_health_guard: str = ""
    source_starved_guard: str = ""
    todo_verify_guard: str = ""
    guardrails: tuple[str, ...] = ()
    max_query_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "adapter_id": self.adapter_id,
            "status": self.status,
            "architecture": self.architecture,
            "production_retrieval_enabled": self.production_retrieval_enabled,
            "accepted_input": self.accepted_input,
            "rejected_input": self.rejected_input,
            "output_schema": self.output_schema,
            "query_groups": [list(group) for group in self.query_groups],
            "queries": list(self.queries),
            "post_filter_terms": list(self.post_filter_terms),
            "disabled_reason": self.disabled_reason,
            "evidence_tier_mapping": self.evidence_tier_mapping,
            "source_health_guard": self.source_health_guard,
            "source_starved_guard": self.source_starved_guard,
            "todo_verify_guard": self.todo_verify_guard,
            "guardrails": list(self.guardrails),
            "max_query_count": self.max_query_count,
        }


ONTOLOGY_GROUPS: tuple[str, ...] = (
    "lattice_assumptions",
    "scheme_families",
    "standardized_schemes",
    "active_candidates",
    "historical_candidates",
    "standardization_processes",
    "migration_lifecycle_events",
    "protocols_and_pki",
    "libraries_and_vendors",
    "hardware_and_embedded_systems",
    "implementation_security",
    "cryptanalysis",
    "regulation_and_jurisdictions",
    "industry_sectors",
    "multilingual_aliases",
    "disambiguation_requirements",
    "negative_contexts",
)


EVIDENCE_TIER_RULES: dict[EvidenceTier, dict[str, object]] = {
    EvidenceTier.S0: {
        "label": "primary authoritative",
        "can_verify_status": True,
        "can_finalize_security_claim": False,
        "requires_todo_verify": False,
    },
    EvidenceTier.S1: {
        "label": "primary technical",
        "can_verify_status": False,
        "can_finalize_security_claim": True,
        "requires_todo_verify": False,
    },
    EvidenceTier.S2: {
        "label": "authoritative implementation",
        "can_verify_status": False,
        "can_finalize_deployment_claim": True,
        "requires_todo_verify": False,
    },
    EvidenceTier.S3: {
        "label": "reliable secondary",
        "can_verify_status": False,
        "requires_todo_verify": True,
    },
    EvidenceTier.S4: {
        "label": "discovery only",
        "can_verify_status": False,
        "requires_todo_verify": True,
    },
}


HAWK_CRYPTO_COANCHORS: tuple[str, ...] = (
    "signature",
    "signatures",
    "digital signature",
    "digital signatures",
    "cryptography",
    "cryptographic",
    "post-quantum",
    "post quantum",
    "pqc",
    "nist",
    "lattice",
    "ntru",
    "mlip",
    "signing",
    "verification",
    "key generation",
    "cryptanalysis",
    "specification",
    "security proof",
)


HAWK_NEGATIVE_CONTEXTS: tuple[str, ...] = (
    "bird",
    "birds",
    "wildlife",
    "sports",
    "team",
    "hawkeye",
    "aircraft",
    "missile",
    "missiles",
    "radar",
    "defense system",
    "malware-detection",
    "malware detection",
    "graph neural network",
    "computer vision",
    "load monitoring",
    "stock",
    "ticker",
    "company",
    "game",
    "fictional character",
)


LATTICE_ANCHORS: tuple[str, ...] = (
    "lwe",
    "rlwe",
    "mlwe",
    "module-lwe",
    "sis",
    "module-sis",
    "ntru",
    "ntru prime",
    "ml-kem",
    "kyber",
    "ml-dsa",
    "dilithium",
    "fn-dsa",
    "falcon",
    "hawk",
    "frodokem",
    "saber",
    "newhope",
    "lattice-based",
    "lattice cryptography",
    "module lattice isomorphism",
    "mlip",
)


MATERIAL_LATTICE_IMPACT_TERMS: tuple[str, ...] = (
    "diversity",
    "backup",
    "migration",
    "transition",
    "standardization",
    "selection",
    "comparison",
    "hybrid",
    "composite",
    "replacement",
    "procurement",
)


ACADEMIC_SOURCES: tuple[str, ...] = (
    "arxiv",
    "iacr_eprint",
    "crossref",
    "dblp",
    "openalex",
    "semantic_scholar",
)


OFFICIAL_STATUS_SOURCES: tuple[str, ...] = (
    "nist_csrc",
    "ietf",
    "cfrg",
    "lamps",
    "etsi",
    "iso",
    "government_guidance",
)


SOURCE_AWARE_QUERY_ARCHITECTURE = (
    "SCHEME_OR_LATTICE_ANCHOR AND PROCESS_OR_EVENT_ANCHOR AND CONTEXT_ANCHOR AND NOT NOISE_CONTEXT"
)


SOURCE_AWARE_GUARDRAILS: tuple[str, ...] = (
    "no_global_broad_enablement",
    "lattice_anchor_mandatory",
    "standardization_status_requires_S0",
    "technical_security_claim_requires_S1",
    "vendor_deployment_claim_requires_S2_or_official_release",
    "S4_discovery_only_keeps_TODO_VERIFY",
    "source_starved_state_must_be_explicit",
    "source_health_failure_must_remain_visible",
    "non_lattice_content_requires_material_lattice_impact",
    "no_ranking_taxonomy_relevance_drift",
)


DRY_RUN_ADAPTER_CONSTRAINTS: dict[str, DryRunAdapterConstraint] = {
    "arxiv": DryRunAdapterConstraint(
        "arxiv",
        "guarded_dry_run_mapping",
        "bounded query_groups generated from lattice scheme, process, context, and noise terms",
        "global flat broad PQC term lists or live retrieval enablement",
        "query_groups",
        "S1 technical source for papers; not valid for S0 status finalization",
        "query group totals, successes, and failures must remain visible",
        "all group failures can contribute to explicit source-starved state",
        "status and deployment claims remain TODO_VERIFY without stronger evidence",
        "medium",
    ),
    "dblp": DryRunAdapterConstraint(
        "dblp",
        "guarded_dry_run_mapping",
        "bounded query strings generated from lattice-centric query families",
        "unbounded per-anchor Cartesian expansion",
        "queries",
        "bibliographic discovery; claims require primary source follow-up",
        "adapter failures must remain visible",
        "no DBLP hits cannot prove no relevant lattice papers",
        "DBLP-only leads retain TODO_VERIFY for claims",
        "medium",
    ),
    "iacr_eprint": DryRunAdapterConstraint(
        "iacr_eprint",
        "guarded_post_filter_planning",
        "feed retrieval plus lattice-aware post-filter terms",
        "pretending the IACR feed supports expanded live query retrieval",
        "post_filter_terms",
        "S1 technical evidence when original ePrint content is available",
        "feed failures remain red/yellow and visible",
        "feed failure can source-starve technical coverage",
        "technical claims still require paper-level support",
        "medium-low",
    ),
    "openalex": DryRunAdapterConstraint(
        "openalex",
        "disabled_live_behavior",
        "dry-run split-query plan only",
        "live split-query behavior without rate and source-health guardrails",
        "disabled_plan",
        "S3/S4 discovery unless primary source is separately verified",
        "rate-limit and degradation warnings must remain visible",
        "failures cannot prove absence of lattice activity",
        "OpenAlex-only claims remain TODO_VERIFY",
        "high",
    ),
    "crossref": DryRunAdapterConstraint(
        "crossref",
        "disabled_live_behavior",
        "dry-run split-query plan only",
        "live split-query behavior without rate and source-health guardrails",
        "disabled_plan",
        "S3/S4 metadata context unless primary source is verified",
        "degraded Crossref status remains visible",
        "failure contributes only to caveats",
        "Crossref-only claims remain TODO_VERIFY",
        "high",
    ),
    "semantic_scholar": DryRunAdapterConstraint(
        "semantic_scholar",
        "disabled_live_behavior",
        "dry-run split-query plan only",
        "live high-volume broad query expansion",
        "disabled_plan",
        "S3/S4 discovery unless original paper evidence is obtained",
        "429 and rate-limit behavior must remain visible",
        "rate-limit source starvation must be explicit",
        "Semantic Scholar-only claims remain TODO_VERIFY",
        "high",
    ),
    "official_status_sources": DryRunAdapterConstraint(
        "official_status_sources",
        "out_of_scope",
        "manual review design only",
        "crawler, scheduler, polling, or live retrieval implementation",
        "manual_review_plan",
        "S0 only in a later authorized phase",
        "not applicable in this batch",
        "absence of an official-source adapter cannot finalize status",
        "status remains TODO_VERIFY without S0 evidence",
        "high",
    ),
    "vendor_library_sources": DryRunAdapterConstraint(
        "vendor_library_sources",
        "out_of_scope",
        "manual review design only",
        "vendor/library crawler or deployment-claim finalization",
        "manual_review_plan",
        "S2 or S0 only in a later authorized phase",
        "not applicable in this batch",
        "missing vendor source cannot imply no deployment",
        "deployment claims remain TODO_VERIFY without official release evidence",
        "high",
    ),
}


def normalize_term(value: str) -> str:
    value = value.lower().replace("–", "-").replace("—", "-").replace("−", "-")
    value = re.sub(r"[^a-z0-9+-]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = normalize_term(text)
    normalized_phrase = normalize_term(phrase)
    if not normalized_phrase:
        return False
    if re.fullmatch(r"[a-z0-9+-]{1,8}", normalized_phrase):
        pattern = r"(?<![a-z0-9])" + re.escape(normalized_phrase) + r"(?![a-z0-9])"
        return re.search(pattern, normalized_text) is not None
    return normalized_phrase in normalized_text


def _matches(text: str, terms: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({term for term in terms if _contains_phrase(text, term)}, key=str.lower))


def scheme_registry() -> dict[str, SchemeEntry]:
    entries = (
        SchemeEntry(
            canonical_name="ML-KEM",
            aliases=("Kyber", "CRYSTALS-Kyber", "FIPS 203"),
            scheme_family="lattice-based key encapsulation",
            underlying_assumption="MLWE",
            lifecycle_status="standardized",
            standard_identifier="FIPS 203",
            standardization_body="NIST",
            process_name="NIST PQC standardization",
            current_round_or_stage="final standard",
            evidence_tier=EvidenceTier.S0,
            primary_source_label="NIST FIPS 203",
            confidence="high",
            todo_verify=False,
        ),
        SchemeEntry(
            canonical_name="ML-DSA",
            aliases=("Dilithium", "CRYSTALS-Dilithium", "FIPS 204"),
            scheme_family="lattice-based digital signature",
            underlying_assumption="MLWE / Module-SIS",
            lifecycle_status="standardized",
            standard_identifier="FIPS 204",
            standardization_body="NIST",
            process_name="NIST PQC standardization",
            current_round_or_stage="final standard",
            evidence_tier=EvidenceTier.S0,
            primary_source_label="NIST FIPS 204",
            confidence="high",
            todo_verify=False,
        ),
        SchemeEntry(
            canonical_name="FN-DSA",
            aliases=("Falcon", "FALCON", "FIPS 206"),
            scheme_family="NTRU-lattice digital signature",
            underlying_assumption="NTRU lattices",
            lifecycle_status="anticipated_standard",
            standard_identifier="FIPS 206",
            standardization_body="NIST",
            process_name="NIST PQC standardization",
            current_round_or_stage="selected for standardization",
            evidence_tier=EvidenceTier.S0,
            primary_source_label="NIST PQC selected algorithms / FIPS 206 tracking",
            confidence="medium",
            todo_verify=True,
        ),
        SchemeEntry(
            canonical_name="HAWK",
            aliases=("Hawk",),
            scheme_family="lattice-based digital signature",
            underlying_assumption="NTRU / MLIP",
            lifecycle_status="active_candidate",
            standardization_body="NIST",
            process_name="NIST Additional Digital Signature Schemes",
            current_round_or_stage="Round 3 candidate",
            evidence_tier=EvidenceTier.S0,
            primary_source_label="NIST IR 8610 and NIST Round 3 announcement",
            confidence="high",
            todo_verify=False,
        ),
        SchemeEntry(
            canonical_name="NTRU",
            aliases=("NTRUEncrypt", "NTRU lattice", "NTRU assumption"),
            scheme_family="NTRU lattice encryption / KEM",
            underlying_assumption="NTRU assumptions",
            lifecycle_status="historical_or_alternative",
            historical=True,
        ),
        SchemeEntry(
            canonical_name="NTRU-HRSS",
            aliases=("HRSS", "NTRU HRSS"),
            scheme_family="NTRU lattice KEM",
            underlying_assumption="NTRU assumptions",
            lifecycle_status="historical_candidate",
            historical=True,
        ),
        SchemeEntry(
            canonical_name="NTRU Prime",
            aliases=("NTRUPrime", "sntrup", "Streamlined NTRU Prime"),
            scheme_family="NTRU lattice KEM",
            underlying_assumption="NTRU Prime assumptions",
            lifecycle_status="alternative_candidate",
        ),
        SchemeEntry(
            canonical_name="FrodoKEM",
            aliases=("Frodo",),
            scheme_family="lattice-based key encapsulation",
            underlying_assumption="LWE",
            lifecycle_status="historical_candidate",
            historical=True,
        ),
        SchemeEntry(
            canonical_name="Saber",
            aliases=("LightSaber", "FireSaber"),
            scheme_family="lattice-based key encapsulation",
            underlying_assumption="Module-LWR",
            lifecycle_status="historical_candidate",
            historical=True,
        ),
        SchemeEntry(
            canonical_name="NewHope",
            aliases=("New Hope",),
            scheme_family="lattice-based key exchange",
            underlying_assumption="RLWE",
            lifecycle_status="historical_candidate",
            historical=True,
        ),
        SchemeEntry("LWE", ("Learning With Errors",), "assumption", "LWE", "active_assumption"),
        SchemeEntry("RLWE", ("Ring-LWE", "Ring Learning With Errors"), "assumption", "RLWE", "active_assumption"),
        SchemeEntry("MLWE", ("Module-LWE", "Module Learning With Errors"), "assumption", "MLWE", "active_assumption"),
        SchemeEntry("SIS", ("Short Integer Solution",), "assumption", "SIS", "active_assumption"),
        SchemeEntry("Module-SIS", ("MSIS", "Module Short Integer Solution"), "assumption", "Module-SIS", "active_assumption"),
        SchemeEntry("NTRU assumptions", ("NTRU problem", "NTRU lattice problem"), "assumption", "NTRU", "active_assumption"),
        SchemeEntry("lattice isomorphism problem", ("LIP",), "assumption", "lattice isomorphism", "active_assumption"),
        SchemeEntry(
            "module lattice isomorphism problem",
            ("MLIP", "module lattice isomorphism"),
            "assumption",
            "module lattice isomorphism",
            "active_assumption",
        ),
    )
    return {entry.canonical_name: entry for entry in entries}


def hawk_dynamic_status() -> DynamicStatus:
    return DynamicStatus(
        scheme="HAWK",
        current_status="active Round 3 candidate",
        previous_status="Round 2 candidate",
        round_or_stage="Round 3 candidate",
        process_name="NIST Additional Digital Signature Schemes",
        primary_source="NIST Round 3 announcement and NIST IR 8610",
        evidence_tier=EvidenceTier.S0,
        last_verified_at=IMPLEMENTATION_REVIEW_DATE,
        status_confidence="high",
        todo_verify=False,
    )


def evidence_tier_can_verify_status(tier: EvidenceTier | str) -> bool:
    normalized = EvidenceTier(tier)
    return bool(EVIDENCE_TIER_RULES[normalized].get("can_verify_status", False))


def evidence_tier_requires_todo_verify(tier: EvidenceTier | str) -> bool:
    normalized = EvidenceTier(tier)
    return bool(EVIDENCE_TIER_RULES[normalized].get("requires_todo_verify", False))


def evidence_tier_can_finalize_security_claim(tier: EvidenceTier | str) -> bool:
    normalized = EvidenceTier(tier)
    return bool(EVIDENCE_TIER_RULES[normalized].get("can_finalize_security_claim", False))


def classify_hawk_context(title: str, body: str = "") -> HawkDecision:
    text = f"{title} {body}"
    if not _contains_phrase(text, "hawk"):
        return HawkDecision(False, "no_hawk_token")
    negative_matches = _matches(text, HAWK_NEGATIVE_CONTEXTS)
    crypto_matches = _matches(text, HAWK_CRYPTO_COANCHORS)
    if negative_matches and not crypto_matches:
        return HawkDecision(False, "hawk_negative_context", (), negative_matches)
    if not crypto_matches:
        return HawkDecision(False, "hawk_without_crypto_coanchor", (), negative_matches)
    if negative_matches:
        return HawkDecision(False, "hawk_conflicting_negative_context", crypto_matches, negative_matches)
    return HawkDecision(True, "hawk_crypto_context_verified", crypto_matches, ())


def lattice_centric_inclusion(title: str, body: str = "") -> InclusionDecision:
    text = f"{title} {body}"
    hawk = classify_hawk_context(title, body)
    anchors = _matches(text, LATTICE_ANCHORS)
    impacts = _matches(text, MATERIAL_LATTICE_IMPACT_TERMS)
    if hawk.accepted:
        anchors = tuple(sorted(set((*anchors, "HAWK")), key=str.lower))
    if anchors:
        return InclusionDecision(True, "explicit_lattice_anchor", anchors, impacts, False)
    if impacts and _contains_phrase(text, "pqc"):
        return InclusionDecision(
            True,
            "non_lattice_candidate_materially_affects_lattice_position",
            (),
            impacts,
            True,
        )
    return InclusionDecision(False, "no_lattice_anchor_or_material_lattice_impact", (), impacts, False)


def query_families() -> dict[str, QueryFamily]:
    registry = scheme_registry()
    scheme_anchors = tuple(sorted(registry.keys()))
    hawk_anchors = ("HAWK", "Hawk")
    return {
        "scheme_standardization": QueryFamily(
            "scheme_standardization",
            "Scheme anchors paired with official process and status terms.",
            scheme_anchors,
            ("standardization", "standard", "FIPS", "NIST", "round", "candidate", "status"),
            ("PQC", "post-quantum", "digital signature", "KEM"),
            ("marketing", "generic quantum computing"),
            ACADEMIC_SOURCES,
            OFFICIAL_STATUS_SOURCES,
            False,
        ),
        "hawk_high_precision": QueryFamily(
            "hawk_high_precision",
            "HAWK must co-occur with cryptographic context and avoid non-crypto meanings.",
            hawk_anchors,
            ("Round 3", "specification", "implementation", "benchmark", "cryptanalysis", "side-channel"),
            HAWK_CRYPTO_COANCHORS,
            HAWK_NEGATIVE_CONTEXTS,
            ACADEMIC_SOURCES,
            ("nist_csrc",),
            False,
        ),
        "scheme_migration": QueryFamily(
            "scheme_migration",
            "Lattice schemes paired with migration and procurement events.",
            scheme_anchors,
            ("migration", "transition", "deadline", "procurement", "inventory", "crypto agility"),
            ("government", "enterprise", "guidance", "deployment"),
            ("generic quantum-safe marketing",),
            ACADEMIC_SOURCES,
            OFFICIAL_STATUS_SOURCES,
            False,
        ),
        "scheme_protocol_pki": QueryFamily(
            "scheme_protocol_pki",
            "Lattice schemes paired with protocol, certificate, and identity contexts.",
            scheme_anchors,
            ("TLS", "X.509", "PKI", "certificate", "IETF", "CFRG", "LAMPS", "hybrid"),
            ("deployment", "integration", "interoperability", "draft"),
            ("ordinary TLS", "ordinary PKI"),
            ACADEMIC_SOURCES,
            ("ietf", "cfrg", "lamps"),
            False,
        ),
        "scheme_implementation_security": QueryFamily(
            "scheme_implementation_security",
            "Lattice schemes paired with implementation security contexts.",
            scheme_anchors,
            ("constant-time", "side-channel", "fault", "masking", "benchmark", "HSM", "hardware"),
            ("implementation", "library", "firmware", "embedded", "FPGA", "ASIC"),
            ("computer vision", "load monitoring"),
            ACADEMIC_SOURCES,
            ("official_library_release", "vendor_release"),
            False,
        ),
        "scheme_cryptanalysis": QueryFamily(
            "scheme_cryptanalysis",
            "Lattice schemes or assumptions paired with cryptanalytic events.",
            scheme_anchors,
            ("cryptanalysis", "attack", "security proof", "lattice reduction", "BKZ", "sieving"),
            ("parameter", "estimate", "implementation", "proof"),
            ("non-cryptographic lattice",),
            ACADEMIC_SOURCES,
            (),
            False,
        ),
    }


def generate_query_templates(family_ids: Sequence[str] | None = None) -> list[dict[str, object]]:
    families = query_families()
    selected = family_ids or tuple(families)
    templates: list[dict[str, object]] = []
    for family_id in selected:
        family = families[family_id]
        templates.append(
            {
                "family": family.identifier,
                "architecture": "SCHEME_OR_LATTICE_ANCHOR AND PROCESS_OR_EVENT_ANCHOR AND CONTEXT_ANCHOR AND NOT NOISE_CONTEXT",
                "scheme_or_lattice_anchors": list(family.scheme_or_lattice_anchors),
                "process_or_event_anchors": list(family.process_or_event_anchors),
                "context_anchors": list(family.context_anchors),
                "noise_terms": list(family.noise_terms),
                "academic_sources": list(family.academic_sources),
                "official_status_sources": list(family.official_status_sources),
                "production_retrieval_enabled": family.production_retrieval_enabled,
            }
        )
    return templates


def _bounded_terms(values: Sequence[str], limit: int) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:
        text = str(value)
        if text not in seen:
            seen.append(text)
        if len(seen) >= limit:
            break
    return tuple(seen)


def _dry_run_query_groups(family: QueryFamily) -> tuple[tuple[str, ...], ...]:
    return (
        _bounded_terms(family.scheme_or_lattice_anchors, 6),
        _bounded_terms(family.process_or_event_anchors, 4),
        _bounded_terms(family.context_anchors, 4),
        _bounded_terms(family.noise_terms, 3),
    )


def _dry_run_dblp_queries(family: QueryFamily) -> tuple[str, ...]:
    schemes = _bounded_terms(family.scheme_or_lattice_anchors, 3)
    events = _bounded_terms(family.process_or_event_anchors, 2)
    contexts = _bounded_terms(family.context_anchors, 2)
    query = " ".join((*schemes, *events, *contexts))
    return (query.strip(),) if query.strip() else ()


def _dry_run_post_filter_terms(family: QueryFamily) -> tuple[str, ...]:
    return tuple(
        term
        for term in (
            *_bounded_terms(family.scheme_or_lattice_anchors, 8),
            *_bounded_terms(family.process_or_event_anchors, 4),
            *_bounded_terms(family.context_anchors, 4),
        )
        if term
    )


def source_aware_adapter_constraints() -> dict[str, DryRunAdapterConstraint]:
    return dict(DRY_RUN_ADAPTER_CONSTRAINTS)


def generate_source_aware_dry_run_plan(
    family_ids: Sequence[str] | None = None,
    adapter_ids: Sequence[str] | None = None,
) -> list[dict[str, object]]:
    families = query_families()
    selected_families = tuple(family_ids or families.keys())
    constraints = source_aware_adapter_constraints()
    selected_adapters = tuple(adapter_ids or constraints.keys())
    plans: list[SourceAwareQueryPlan] = []

    for family_id in selected_families:
        family = families[family_id]
        for adapter_id in selected_adapters:
            constraint = constraints[adapter_id]
            query_groups: tuple[tuple[str, ...], ...] = ()
            queries: tuple[str, ...] = ()
            post_filter_terms: tuple[str, ...] = ()
            disabled_reason = ""
            max_query_count = 0

            if adapter_id == "arxiv":
                query_groups = _dry_run_query_groups(family)
                max_query_count = len(query_groups)
            elif adapter_id == "dblp":
                queries = _dry_run_dblp_queries(family)
                max_query_count = len(queries)
            elif adapter_id == "iacr_eprint":
                post_filter_terms = _dry_run_post_filter_terms(family)
                max_query_count = 0
            else:
                disabled_reason = (
                    "live retrieval is disabled for this adapter in Phase 15B-04B Batch 1; "
                    "the plan is metadata only"
                )

            plans.append(
                SourceAwareQueryPlan(
                    family=family.identifier,
                    adapter_id=adapter_id,
                    status=constraint.status,
                    architecture=SOURCE_AWARE_QUERY_ARCHITECTURE,
                    production_retrieval_enabled=False,
                    accepted_input=constraint.accepted_input,
                    rejected_input=constraint.rejected_input,
                    output_schema=constraint.output_schema,
                    query_groups=query_groups,
                    queries=queries,
                    post_filter_terms=post_filter_terms,
                    disabled_reason=disabled_reason,
                    evidence_tier_mapping=constraint.evidence_tier_mapping,
                    source_health_guard=constraint.source_health_behavior,
                    source_starved_guard=constraint.source_starved_behavior,
                    todo_verify_guard=constraint.todo_verify_behavior,
                    guardrails=SOURCE_AWARE_GUARDRAILS,
                    max_query_count=max_query_count,
                )
            )
    return [plan.to_dict() for plan in plans]


def _taxonomy_group_for_category(category: str) -> str:
    if category.startswith("A"):
        return "cryptanalysis"
    if category.startswith("B"):
        return "lattice_assumptions"
    if category.startswith("C"):
        return "scheme_families"
    if category.startswith("D01"):
        return "scheme_families"
    if category.startswith("D"):
        return "protocols_and_pki"
    if category.startswith("E04"):
        return "hardware_and_embedded_systems"
    if category.startswith("E") or category.startswith("F"):
        return "implementation_security"
    if category.startswith("G"):
        return "standardization_processes"
    if category.startswith("H"):
        return "cryptanalysis"
    if category.startswith("I"):
        return "cryptanalysis"
    return "disambiguation_requirements"


def iter_taxonomy_keywords(taxonomy_config: Mapping[str, Any] | None = None) -> Iterable[tuple[str, str, str]]:
    taxonomy = taxonomy_config or load_config_bundle()["taxonomy"]
    for group_name, group_value in taxonomy.items():
        if not isinstance(group_value, Mapping):
            continue
        for category, category_value in group_value.items():
            if not isinstance(category_value, Mapping):
                continue
            keywords = category_value.get("keywords", [])
            if isinstance(keywords, str):
                keywords = [keywords]
            if not isinstance(keywords, Sequence):
                continue
            for keyword in keywords:
                yield str(group_name), str(category), str(keyword)


def map_existing_taxonomy_keywords(taxonomy_config: Mapping[str, Any] | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    registry_aliases = {
        normalize_term(alias): entry.canonical_name
        for entry in scheme_registry().values()
        for alias in (entry.canonical_name, *entry.aliases)
    }
    for group_name, category, keyword in iter_taxonomy_keywords(taxonomy_config):
        normalized = normalize_term(keyword)
        rows.append(
            {
                "original_group": group_name,
                "original_category": category,
                "original_spelling": keyword,
                "normalized_spelling": normalized,
                "new_ontology_group": _taxonomy_group_for_category(category),
                "retained": True,
                "alias_of": registry_aliases.get(normalized, ""),
                "conflict": "",
                "deprecation_status": "retained",
                "TODO_VERIFY": False,
            }
        )
    return rows


def metadata_defaults() -> dict[str, object]:
    return {
        "scheme": "",
        "scheme_alias": "",
        "scheme_family": "",
        "underlying_assumption": "",
        "standardization_body": "",
        "process_name": "",
        "round_or_stage": "",
        "current_status": "",
        "previous_status": "",
        "lifecycle_event": "",
        "protocol": "",
        "deployment_layer": "",
        "jurisdiction": "",
        "industry_sector": "",
        "evidence_tier": "",
        "primary_source": "",
        "last_verified_at": "",
        "status_confidence": "",
        "TODO_VERIFY": [],
    }


def apply_metadata_defaults(record: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(record)
    for key, default in metadata_defaults().items():
        result.setdefault(key, list(default) if isinstance(default, list) else default)
    return result


def load_pqc_radar_config(config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or project_root() / "config" / "pqc_radar_queries.yaml"
    return load_structured_file(path)


def proposed_commit_paths() -> tuple[str, ...]:
    return (
        "config/pqc_radar_queries.yaml",
        "docs/operations/lattice_pqc_radar_ontology_v0.1.md",
        "src/lattice_digest/pqc_radar.py",
        "src/lattice_digest/ranker.py",
        "tests/test_phase_15b_04a_hawk_disambiguation.py",
        "tests/test_phase_15b_04a_keyword_compatibility.py",
        "tests/test_phase_15b_04a_no_ranking_drift.py",
        "tests/test_phase_15b_04a_pqc_ontology.py",
        "tests/test_phase_15b_04a_source_queries.py",
        "tests/test_phase_15b_04a_status_and_evidence.py",
    )
