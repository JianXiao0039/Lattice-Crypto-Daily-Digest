from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
from typing import Any, Protocol, Sequence

from pydantic import BaseModel, ConfigDict, Field

from lattice_digest.models import PaperRecord, copy_record


class EnrichmentStatus(StrEnum):
    EVIDENCE_UPGRADED = "EVIDENCE_UPGRADED"
    NO_EVIDENCE_AVAILABLE = "NO_EVIDENCE_AVAILABLE"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    NOT_SELECTED = "NOT_SELECTED"
    UNSUPPORTED_ACCESS = "UNSUPPORTED_ACCESS"


class EnrichmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_identity: str
    requested_reasons: tuple[str, ...]
    allowed_evidence_types: tuple[str, ...] = (
        "official_metadata",
        "abstract",
        "keywords",
        "first_page_text",
        "introduction_snippet",
        "contribution_snippet",
        "conclusion_snippet",
        "official_pdf_metadata",
        "citation_relation",
    )


class EnrichmentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    source_url: str
    status: EnrichmentStatus
    fields: dict[str, Any] = Field(default_factory=dict)
    failure_reason: str = ""


class EnrichmentEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_identity: str
    requested_reason: tuple[str, ...]
    source: str
    source_url: str
    content_hash: str
    fields_upgraded: tuple[str, ...]
    failure_reason: str
    status: EnrichmentStatus


class EvidenceEnricher(Protocol):
    name: str

    def enrich(self, record: PaperRecord, request: EnrichmentRequest) -> EnrichmentPayload:
        ...


@dataclass(frozen=True)
class EnrichmentResult:
    records: tuple[PaperRecord, ...]
    events: tuple[EnrichmentEvent, ...]
    selected_count: int
    request_count: int
    upgraded_count: int


class SelectiveEnrichmentCoordinator:
    def __init__(
        self,
        providers: Sequence[EvidenceEnricher] = (),
        *,
        max_candidates: int = 25,
        max_requests: int = 50,
    ) -> None:
        self.providers = tuple(providers)
        self.max_candidates = max(0, max_candidates)
        self.max_requests = max(0, max_requests)

    def run(self, records: Sequence[PaperRecord]) -> EnrichmentResult:
        output: list[PaperRecord] = []
        events: list[EnrichmentEvent] = []
        request_count = 0
        selected_count = 0
        upgraded_count = 0
        for index, source_record in enumerate(records):
            record = copy_record(source_record)
            reasons = enrichment_reasons(record)
            identity = record.paper_id or record.source_url
            if not reasons or selected_count >= self.max_candidates:
                event = _event(
                    identity,
                    reasons,
                    source="none",
                    source_url=record.source_url,
                    status=EnrichmentStatus.NOT_SELECTED,
                    failure_reason="no trigger" if not reasons else "candidate budget exhausted",
                )
                events.append(event)
                record.enrichment_events.append(event.model_dump(mode="json"))
                output.append(record)
                continue
            selected_count += 1
            request = EnrichmentRequest(candidate_identity=identity, requested_reasons=tuple(reasons))
            if not self.providers:
                event = _event(
                    identity,
                    reasons,
                    source="none",
                    source_url=record.source_url,
                    status=EnrichmentStatus.NO_EVIDENCE_AVAILABLE,
                    failure_reason="no authorized enrichment provider configured",
                )
                events.append(event)
                record.enrichment_events.append(event.model_dump(mode="json"))
                output.append(record)
                continue
            for provider in self.providers:
                if request_count >= self.max_requests:
                    event = _event(
                        identity,
                        reasons,
                        source=provider.name,
                        source_url=record.source_url,
                        status=EnrichmentStatus.NOT_SELECTED,
                        failure_reason="global request budget exhausted",
                    )
                    events.append(event)
                    record.enrichment_events.append(event.model_dump(mode="json"))
                    break
                request_count += 1
                try:
                    payload = provider.enrich(record, request)
                except Exception as exc:  # provider failures are bounded and never erase Stage-1 evidence.
                    payload = EnrichmentPayload(
                        source=provider.name,
                        source_url=record.source_url,
                        status=EnrichmentStatus.NO_EVIDENCE_AVAILABLE,
                        failure_reason=f"{type(exc).__name__}: {exc}",
                    )
                upgraded = _apply_payload(record, payload)
                event = _event(
                    identity,
                    reasons,
                    source=payload.source,
                    source_url=payload.source_url,
                    status=payload.status if not upgraded else EnrichmentStatus.EVIDENCE_UPGRADED,
                    fields_upgraded=upgraded,
                    failure_reason=payload.failure_reason,
                    payload=payload.fields,
                )
                events.append(event)
                record.enrichment_events.append(event.model_dump(mode="json"))
                if upgraded:
                    upgraded_count += 1
                    break
            output.append(record)
        return EnrichmentResult(tuple(output), tuple(events), selected_count, request_count, upgraded_count)


def enrichment_reasons(record: PaperRecord) -> list[str]:
    reasons: list[str] = []
    if not record.abstract:
        reasons.append("abstract_missing")
    if record.relevance_score < 60 and record.relevance_score >= 25:
        reasons.append("relevance_borderline")
    if record.security_impact_severity in {"CRITICAL", "HIGH"} or any(
        edge.get("critical_eligible") for edge in record.consequence_edges
    ):
        reasons.append("possible_critical_implication")
    if any(item.get("field") in {"publication_date", "update_date"} for item in record.conflicting_metadata):
        reasons.append("date_version_conflict")
    if record.consequence_edges and any(
        edge.get("evidence_state") == "INFERRED_HYPOTHESIS" for edge in record.consequence_edges
    ):
        reasons.append("consequence_hypothesis")
    if record.provenance_strength in {"primary_source", "authoritative_metadata"} and not record.abstract:
        reasons.append("authoritative_crypto_source_title_weak")
    if record.merge_proposals:
        reasons.append("identity_conflict")
    return list(dict.fromkeys(reasons))


def _apply_payload(record: PaperRecord, payload: EnrichmentPayload) -> tuple[str, ...]:
    if payload.status != EnrichmentStatus.EVIDENCE_UPGRADED:
        return ()
    allowed_fields = {
        "abstract",
        "conclusion",
        "doi",
        "arxiv_id",
        "eprint_id",
        "publication_date",
        "publication_timestamp",
        "publication_date_kind",
        "update_date",
        "update_timestamp",
        "update_date_kind",
        "venue",
        "pdf_url",
        "categories",
    }
    upgraded: list[str] = []
    conflicts: list[dict[str, object]] = []
    for field, value in payload.fields.items():
        if field not in allowed_fields or _is_empty(value):
            continue
        current = getattr(record, field)
        if not _is_empty(current) and current != value:
            if field in {"abstract", "conclusion"} and len(str(value)) > len(str(current)):
                setattr(record, field, value)
                upgraded.append(field)
            else:
                conflicts.append({"field": field, "existing": current, "incoming": value, "source": payload.source})
            continue
        setattr(record, field, value)
        upgraded.append(field)
    record.conflicting_metadata.extend(conflicts)
    if upgraded:
        content_hash = hashlib.sha256(repr(sorted(payload.fields.items())).encode("utf-8")).hexdigest()
        record.content_hashes.append(content_hash)
        record.evidence_versions.append(
            {
                "source": payload.source,
                "source_url": payload.source_url,
                "content_hash": content_hash,
                "fields_upgraded": upgraded,
            }
        )
    return tuple(upgraded)


def _is_empty(value: object) -> bool:
    return value is None or value == "" or value == []


def _event(
    identity: str,
    reasons: Sequence[str],
    *,
    source: str,
    source_url: str,
    status: EnrichmentStatus,
    fields_upgraded: Sequence[str] = (),
    failure_reason: str = "",
    payload: dict[str, Any] | None = None,
) -> EnrichmentEvent:
    content_hash = hashlib.sha256(repr(sorted((payload or {}).items())).encode("utf-8")).hexdigest() if payload else ""
    return EnrichmentEvent(
        candidate_identity=identity,
        requested_reason=tuple(reasons),
        source=source,
        source_url=source_url,
        content_hash=content_hash,
        fields_upgraded=tuple(fields_upgraded),
        failure_reason=failure_reason,
        status=status,
    )
