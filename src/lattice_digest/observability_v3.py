from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Iterable

from pydantic import BaseModel, ConfigDict

from lattice_digest.models import PaperRecord, copy_record
from lattice_digest.radar_freshness import enrich_record_for_daily_radar


class ObservabilityRoute(StrEnum):
    OBSERVED_PENDING_EVIDENCE = "OBSERVED_PENDING_EVIDENCE"
    OBSERVED_RELEVANT_DATE_UNCERTAIN = "OBSERVED_RELEVANT_DATE_UNCERTAIN"
    OBSERVED_RELEVANT_STALE = "OBSERVED_RELEVANT_STALE"
    OBSERVED_POSSIBLE_CRITICAL = "OBSERVED_POSSIBLE_CRITICAL"
    OBSERVED_IRRELEVANT = "OBSERVED_IRRELEVANT"


class ObservabilityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_identity: str
    route: ObservabilityRoute
    reasons: tuple[str, ...]
    daily_eligible: bool = False


def assign_observability_routes(
    records: Iterable[PaperRecord],
    digest_date: date,
    *,
    coverage_start: datetime | None = None,
    coverage_end: datetime | None = None,
) -> tuple[tuple[PaperRecord, ...], tuple[ObservabilityDecision, ...]]:
    routed: list[PaperRecord] = []
    decisions: list[ObservabilityDecision] = []
    for source_record in records:
        record = copy_record(source_record)
        freshness = enrich_record_for_daily_radar(
            record,
            digest_date,
            coverage_start=coverage_start,
            coverage_end=coverage_end,
        )
        reasons: list[str] = []
        if record.relevance_label == "D":
            route = ObservabilityRoute.OBSERVED_IRRELEVANT
            reasons.append(record.reason or "semantic analysis classified the candidate as irrelevant")
        elif record.security_impact_severity == "CRITICAL" or any(
            edge.get("critical_eligible") for edge in record.consequence_edges
        ):
            route = ObservabilityRoute.OBSERVED_POSSIBLE_CRITICAL
            reasons.append("critical consequence requires source/date/claim verification")
        elif freshness.freshness_bucket == "date_uncertain_todo_verify":
            route = ObservabilityRoute.OBSERVED_RELEVANT_DATE_UNCERTAIN
            reasons.append("no authoritative current-window date evidence")
        elif not freshness.primary_today_new_eligible and freshness.freshness_bucket not in {
            "recent_content_revision",
            "CRITICAL_NEWLY_OBSERVED_VERIFY_FIRST",
        }:
            route = ObservabilityRoute.OBSERVED_RELEVANT_STALE
            reasons.append(freshness.freshness_reason or "relevant but outside the strict Daily window")
        else:
            route = ObservabilityRoute.OBSERVED_PENDING_EVIDENCE
            if not record.abstract:
                reasons.append("abstract missing; preserved for selective enrichment")
            else:
                reasons.append("observable candidate retained until strict Daily eligibility")
        record.observability_route = route.value
        record.observability_reasons = reasons
        routed.append(record)
        decisions.append(
            ObservabilityDecision(
                candidate_identity=record.paper_id or record.source_url,
                route=route,
                reasons=tuple(reasons),
                daily_eligible=freshness.primary_today_new_eligible,
            )
        )
    return tuple(routed), tuple(decisions)
