from __future__ import annotations

from enum import StrEnum
from typing import Any, Iterable


class SourceRole(StrEnum):
    DISCOVERY_PRIMARY = "DISCOVERY_PRIMARY"
    DISCOVERY_SECONDARY = "DISCOVERY_SECONDARY"
    METADATA_ENRICHMENT = "METADATA_ENRICHMENT"
    VENUE_AUTHORITY = "VENUE_AUTHORITY"
    IDENTIFIER_RESOLUTION = "IDENTIFIER_RESOLUTION"
    LOW_CONFIDENCE_FALLBACK = "LOW_CONFIDENCE_FALLBACK"


DEFAULT_SOURCE_ROLES: dict[str, tuple[SourceRole, ...]] = {
    "iacr_eprint": (
        SourceRole.DISCOVERY_PRIMARY,
        SourceRole.VENUE_AUTHORITY,
        SourceRole.IDENTIFIER_RESOLUTION,
    ),
    "arxiv": (SourceRole.DISCOVERY_PRIMARY, SourceRole.IDENTIFIER_RESOLUTION),
    "openalex": (
        SourceRole.DISCOVERY_SECONDARY,
        SourceRole.METADATA_ENRICHMENT,
        SourceRole.IDENTIFIER_RESOLUTION,
    ),
    "semantic_scholar": (SourceRole.DISCOVERY_SECONDARY, SourceRole.METADATA_ENRICHMENT),
    "dblp": (
        SourceRole.IDENTIFIER_RESOLUTION,
        SourceRole.VENUE_AUTHORITY,
        SourceRole.METADATA_ENRICHMENT,
    ),
    "crossref": (SourceRole.METADATA_ENRICHMENT, SourceRole.IDENTIFIER_RESOLUTION),
}


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
