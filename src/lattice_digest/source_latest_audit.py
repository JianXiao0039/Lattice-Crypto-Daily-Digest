from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceLatestCapability:
    source: str
    source_type: str
    status: str
    mechanism: str
    manual_flag: str
    notes: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "source_type": self.source_type,
            "status": self.status,
            "mechanism": self.mechanism,
            "manual_flag": self.manual_flag,
            "notes": self.notes,
        }


def classify_source_latest_capability(source_config: dict[str, Any]) -> SourceLatestCapability:
    source = str(source_config.get("name") or source_config.get("type") or "unknown")
    source_type = str(source_config.get("type") or source)
    enabled = bool(source_config.get("enabled", False))

    if source_type == "iacr_eprint":
        return SourceLatestCapability(
            source=source,
            source_type=source_type,
            status="supports latest enumeration",
            mechanism="IACR ePrint RSS latest feed",
            manual_flag="--include-latest-sources",
            notes="Successful RSS fetches are cached politely; failed same-day attempts require an explicit manual retry/latest flag.",
        )
    if source_type == "semantic_scholar":
        return SourceLatestCapability(
            source=source,
            source_type=source_type,
            status="query search only",
            mechanism="Semantic Scholar Graph API paper search",
            manual_flag="none",
            notes="No native latest feed is wired here; SEMANTIC_SCHOLAR_API_KEY is optional and must never be logged.",
        )
    if source_type in {"arxiv", "dblp", "openalex", "crossref"}:
        return SourceLatestCapability(
            source=source,
            source_type=source_type,
            status="query search only",
            mechanism=f"{source_type} configured query API",
            manual_flag="none",
            notes="Configured broad query search is useful for recall but is not a source-native latest enumerator.",
        )
    if not enabled:
        return SourceLatestCapability(
            source=source,
            source_type=source_type,
            status="unsupported / unknown",
            mechanism="disabled source",
            manual_flag="none",
            notes="Disabled source; not part of normal ingestion.",
        )
    return SourceLatestCapability(
        source=source,
        source_type=source_type,
        status="unsupported / unknown",
        mechanism="unknown",
        manual_flag="none",
        notes="No source-native latest enumeration capability is known.",
    )


def audit_latest_capabilities(sources_config: dict[str, Any]) -> list[SourceLatestCapability]:
    sources = sources_config.get("sources", [])
    if not isinstance(sources, list):
        return []
    return [classify_source_latest_capability(source) for source in sources if isinstance(source, dict)]


def render_latest_capability_table(capabilities: list[SourceLatestCapability]) -> str:
    lines = [
        "| Source | Capability | Mechanism | Manual flag | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for capability in capabilities:
        lines.append(
            "| {source} | {status} | {mechanism} | {manual_flag} | {notes} |".format(
                source=capability.source,
                status=capability.status,
                mechanism=capability.mechanism,
                manual_flag=capability.manual_flag,
                notes=capability.notes,
            )
        )
    return "\n".join(lines)
