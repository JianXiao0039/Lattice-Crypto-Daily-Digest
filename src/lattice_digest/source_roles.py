from __future__ import annotations

from enum import StrEnum
from typing import Any, Iterable


class SourceRole(StrEnum):
    DISCOVERY_PRIMARY = "DISCOVERY_PRIMARY"
    DISCOVERY_SECONDARY = "DISCOVERY_SECONDARY"
    ENRICHMENT = "ENRICHMENT"
    METADATA_ENRICHMENT = "METADATA_ENRICHMENT"
    VENUE_AUTHORITY = "VENUE_AUTHORITY"
    IDENTIFIER_RESOLUTION = "IDENTIFIER_RESOLUTION"
    CRITICAL_WATCH = "CRITICAL_WATCH"
    LOW_CONFIDENCE_FALLBACK = "LOW_CONFIDENCE_FALLBACK"


DEFAULT_SOURCE_ROLES: dict[str, tuple[SourceRole, ...]] = {
    "iacr_eprint": (
        SourceRole.DISCOVERY_PRIMARY,
        SourceRole.VENUE_AUTHORITY,
        SourceRole.IDENTIFIER_RESOLUTION,
        SourceRole.CRITICAL_WATCH,
    ),
    "arxiv": (SourceRole.DISCOVERY_PRIMARY, SourceRole.ENRICHMENT, SourceRole.IDENTIFIER_RESOLUTION),
    "openalex": (
        SourceRole.DISCOVERY_SECONDARY,
        SourceRole.ENRICHMENT,
        SourceRole.METADATA_ENRICHMENT,
        SourceRole.IDENTIFIER_RESOLUTION,
    ),
    "semantic_scholar": (
        SourceRole.DISCOVERY_SECONDARY,
        SourceRole.ENRICHMENT,
        SourceRole.METADATA_ENRICHMENT,
        SourceRole.IDENTIFIER_RESOLUTION,
    ),
    "dblp": (
        SourceRole.IDENTIFIER_RESOLUTION,
        SourceRole.VENUE_AUTHORITY,
        SourceRole.ENRICHMENT,
        SourceRole.METADATA_ENRICHMENT,
    ),
    "crossref": (SourceRole.ENRICHMENT, SourceRole.METADATA_ENRICHMENT, SourceRole.IDENTIFIER_RESOLUTION),
}


def unique_marginal_recall(
    canonical_sources: dict[str, set[str]],
    relevant_candidate_ids: set[str],
) -> dict[str, dict[str, int | float]]:
    """Measure source diversity after canonical identity resolution.

    A configured source count is never returned as recall. A candidate is
    marginal to a source only when no other configured source observed that
    canonical identity.
    """

    sources = sorted({source for values in canonical_sources.values() for source in values})
    metrics: dict[str, dict[str, int | float]] = {}
    relevant_total = len(relevant_candidate_ids)
    for source in sources:
        contributed = {
            candidate_id
            for candidate_id, candidate_sources in canonical_sources.items()
            if source in candidate_sources
        }
        unique = {
            candidate_id
            for candidate_id in contributed
            if canonical_sources[candidate_id] == {source}
        }
        relevant = contributed.intersection(relevant_candidate_ids)
        relevant_unique = unique.intersection(relevant_candidate_ids)
        metrics[source] = {
            "canonical_contribution": len(contributed),
            "unique_canonical_contribution": len(unique),
            "relevant_contribution": len(relevant),
            "unique_relevant_contribution": len(relevant_unique),
            "unique_marginal_recall": len(relevant_unique) / relevant_total if relevant_total else 0.0,
        }
    return metrics


def normalize_source_roles(values: Iterable[str | SourceRole]) -> tuple[SourceRole, ...]:
    roles: list[SourceRole] = []
    for value in values:
        role = value if isinstance(value, SourceRole) else SourceRole(str(value).strip().upper())
        if role not in roles:
            roles.append(role)
    if not roles:
        raise ValueError("at least one source role is required")
    return tuple(roles)


def source_roles_for_config(config: dict[str, Any]) -> tuple[SourceRole, ...]:
    configured = config.get("source_roles")
    if configured:
        return normalize_source_roles(configured)
    name = str(config.get("name") or config.get("type") or "").strip()
    return DEFAULT_SOURCE_ROLES.get(name, (SourceRole.LOW_CONFIDENCE_FALLBACK,))


def serialized_source_roles(config: dict[str, Any]) -> list[str]:
    return [role.value for role in source_roles_for_config(config)]


def primary_source_role(config: dict[str, Any]) -> str:
    return source_roles_for_config(config)[0].value
