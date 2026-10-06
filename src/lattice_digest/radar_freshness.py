from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Mapping

from lattice_digest.models import PaperRecord
from lattice_digest.critical_translation import apply_critical_translation
from lattice_digest.recommendation_calibration import calibrate_recommendation, calibration_to_update
from lattice_digest.venue_registry import TODO_VERIFY, VenueRegistryEntry, find_registry_entry


FRESHNESS_WINDOW_DAYS = 1
STRICT_FRESHNESS_POLICY_VERSION = "strict_36h_v1"

AUTHORITATIVE_PUBLICATION_DATE = "AUTHORITATIVE_PUBLICATION_DATE"
AUTHORITATIVE_ANNOUNCEMENT_DATE = "AUTHORITATIVE_ANNOUNCEMENT_DATE"
AUTHORITATIVE_CONTENT_REVISION_DATE = "AUTHORITATIVE_CONTENT_REVISION_DATE"
INDEX_METADATA_UPDATE_DATE = "INDEX_METADATA_UPDATE_DATE"
FIRST_OBSERVED_AT = "FIRST_OBSERVED_AT"
SOURCE_METADATA_CORRECTION = "SOURCE_METADATA_CORRECTION"
PRIMARY_DATE_KINDS = {
    AUTHORITATIVE_PUBLICATION_DATE,
    AUTHORITATIVE_ANNOUNCEMENT_DATE,
    AUTHORITATIVE_CONTENT_REVISION_DATE,
}


@dataclass(frozen=True)
class FreshnessDecision:
    selected_date_basis: str
    freshness_bucket: str
    freshness_reason: str
    primary_today_new_eligible: bool


@dataclass(frozen=True)
class VenueMetadata:
    venue: str
    venue_type: str
    publisher_or_source: str
    ccf_rank: str
    venue_status: str
    expanded_security_crypto_systems_scope: bool
    venue_relevance: str
    venue_confidence: str
    ccf_status: str = "unknown"
    ccf_evidence_status: str = "missing_trusted_source"
    applicability: str = "unknown"
    todo_verify_required: bool = False

SOURCE_FAMILY_HINTS: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("vendor", "library", "release"), "vendor/security advisory", "vendor/library source"),
    (("advisory", "security bulletin", "cve"), "vendor/security advisory", "security advisory"),
    (("standard", "fips", "nist", "ietf", "rfc"), "standardization body", "standardization source"),
    (("preprint", "arxiv", "eprint"), "preprint", "preprint source"),
    (("journal",), "journal", "journal source"),
    (("workshop",), "workshop", "workshop source"),
    (("conference", "symposium"), "conference", "conference source"),
)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"unknown", TODO_VERIFY.lower()}:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def freshness_window(run_date: date, window_days: int = FRESHNESS_WINDOW_DAYS) -> tuple[date, date]:
    return run_date - timedelta(days=window_days), run_date


def _in_window(value: str | None, run_date: date, window_days: int) -> bool:
    parsed = parse_date(value)
    if parsed is None:
        return False
    start, end = freshness_window(run_date, window_days)
    return start <= parsed <= end


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"unknown", TODO_VERIFY.lower()}:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError, IndexError):
            parsed_date = parse_date(text)
            if parsed_date is None:
                return None
            return datetime.combine(parsed_date, time.min, timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _in_coverage(
    value: str | None,
    coverage_start: datetime | None,
    coverage_end: datetime | None,
    run_date: date,
    window_days: int,
) -> bool:
    if coverage_start is None or coverage_end is None:
        return _in_window(value, run_date, window_days)
    parsed = _parse_timestamp(value)
    if parsed is None:
        return False
    start = coverage_start.astimezone(timezone.utc)
    end = coverage_end.astimezone(timezone.utc)
    return start <= parsed < end


def _field(record: PaperRecord | Mapping[str, Any], name: str) -> Any:
    if isinstance(record, Mapping):
        return record.get(name)
    return getattr(record, name, None)


def _from_registry_entry(entry: VenueRegistryEntry, raw_venue: str, raw_source: str) -> VenueMetadata:
    venue = raw_venue or entry.canonical_venue_name
    return VenueMetadata(
        venue,
        entry.venue_type,
        entry.publisher_or_source or raw_source or "unknown",
        entry.ccf_rank,
        "TODO_VERIFY" if entry.todo_verify_required else "known",
        entry.expanded_security_crypto_systems_scope,
        entry.venue_relevance,
        entry.confidence,
        entry.ccf_status,
        entry.ccf_evidence_status,
        entry.applicability,
        entry.todo_verify_required,
    )


def decide_freshness(
    record: PaperRecord | Mapping[str, Any],
    run_date: date,
    window_days: int = FRESHNESS_WINDOW_DAYS,
    *,
    coverage_start: datetime | None = None,
    coverage_end: datetime | None = None,
) -> FreshnessDecision:
    event = _field(record, 'cross_day_event')
    if event and event != 'NEW_DISTINCT_PAPER':
        bucket = 'recent_content_revision' if event in {'GENUINE_NEW_VERSION', 'GENUINE_CONTENT_REVISION'} else ('date_uncertain_todo_verify' if event == 'IDENTITY_UNCERTAIN' else 'cross_day_duplicate')
        return FreshnessDecision('promotion_history', bucket, str(event), False)
    for basis, kind_field, default_kind in (
        ("publication_date", "publication_date_kind", AUTHORITATIVE_PUBLICATION_DATE),
        ("announcement_date", "announcement_date_kind", AUTHORITATIVE_ANNOUNCEMENT_DATE),
    ):
        timestamp_field = basis.replace("_date", "_timestamp")
        value = _field(record, timestamp_field) or _field(record, basis)
        kind = str(_field(record, kind_field) or default_kind)
        if kind not in PRIMARY_DATE_KINDS:
            continue
        if _in_coverage(value, coverage_start, coverage_end, run_date, window_days):
            return FreshnessDecision(
                basis,
                "primary_today_new",
                f"{basis} ({kind}) within freshness window",
                True,
            )

    update_kind = str(_field(record, "update_date_kind") or AUTHORITATIVE_CONTENT_REVISION_DATE)
    if update_kind == AUTHORITATIVE_CONTENT_REVISION_DATE and _in_coverage(
        _field(record, "update_timestamp") or _field(record, "update_date"),
        coverage_start,
        coverage_end,
        run_date,
        window_days,
    ):
        return FreshnessDecision(
            "update_date",
            "recent_content_revision",
            "source-authenticated content revision within freshness window; original publication is not relabeled new",
            False,
        )

    if _in_window(_field(record, "official_status_change_date"), run_date, window_days):
        return FreshnessDecision(
            "official_status_change_date",
            "official_status_changed",
            "official status changed within freshness window",
            False,
        )

    if _in_window(_field(record, "source_metadata_correction_date"), run_date, window_days):
        return FreshnessDecision(
            "source_metadata_correction_date",
            "source_metadata_corrected",
            "source metadata corrected within freshness window",
            False,
        )

    if _in_window(_field(record, "manually_requested_backfill_date"), run_date, window_days):
        return FreshnessDecision(
            "manually_requested_backfill_date",
            "manually_requested",
            "manually requested backfill within freshness window",
            False,
        )

    first_seen = _field(record, "first_seen_at") or _field(record, "first_seen_date")
    if _in_coverage(first_seen, coverage_start, coverage_end, run_date, window_days):
        if str(_field(record, "security_impact_severity") or "").upper() == "CRITICAL":
            return FreshnessDecision(
                "first_seen_at",
                "CRITICAL_NEWLY_OBSERVED_VERIFY_FIRST",
                "critical source-grounded item newly observed; publication freshness remains unverified/older",
                False,
            )
        return FreshnessDecision(
            "first_seen_at" if _field(record, "first_seen_at") else "first_seen_date",
            "newly_discovered_but_older",
            "first seen within freshness window; original source date is older or absent",
            False,
        )

    explicit_reason = str(_field(record, "freshness_reason") or "").strip()
    if explicit_reason:
        lower = explicit_reason.lower()
        bucket = "high_priority_security_update" if "security" in lower else "important_older_item"
        return FreshnessDecision("explicit_freshness_reason", bucket, explicit_reason, False)

    if any(parse_date(str(_field(record, name) or "")) for name in ("publication_date", "announcement_date", "update_date")):
        return FreshnessDecision("publication_date", "backfill", "outside freshness window; route outside primary today/new", False)

    return FreshnessDecision(
        TODO_VERIFY,
        "date_uncertain_todo_verify",
        "missing or ambiguous source date; cannot enter primary today/new",
        False,
    )


def detect_venue_metadata(record: PaperRecord | Mapping[str, Any]) -> VenueMetadata:
    raw_venue = str(_field(record, "venue") or "").strip()
    raw_source = str(_field(record, "source") or "").strip()
    registry_entry = find_registry_entry(raw_venue, raw_source)
    if registry_entry is not None:
        return _from_registry_entry(registry_entry, raw_venue, raw_source)
    text = f"{raw_venue} {raw_source}".lower()
    for hints, venue_type, publisher in SOURCE_FAMILY_HINTS:
        if any(hint in text for hint in hints):
            return VenueMetadata(
                raw_venue or raw_source or "unknown",
                venue_type,
                raw_source or publisher,
                "unknown",
                TODO_VERIFY,
                venue_type in {"conference", "journal", "workshop", "preprint", "standardization body", "vendor/security advisory"},
                "peripheral",
                "low",
            )
    if raw_venue:
        return VenueMetadata(raw_venue, "unknown", raw_source or "unknown", "unknown", TODO_VERIFY, False, "peripheral", "low")
    return VenueMetadata("unknown", "unknown", raw_source or "unknown", "unknown", TODO_VERIFY, False, "peripheral", "low")


def recommendation_level(score: int, freshness_bucket: str) -> str:
    if freshness_bucket != "primary_today_new":
        return "Backfill" if freshness_bucket != "date_uncertain_todo_verify" else TODO_VERIFY
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Medium"
    if score > 0:
        return "Low"
    return TODO_VERIFY


def recommendation_reason(record: PaperRecord | Mapping[str, Any]) -> str:
    from lattice_digest.evidence_contract import render_research_relations
    return render_research_relations(record, language='en')


def _generated_zh_summary(text: str, fallback: str) -> str:
    if not text:
        return f"TODO_VERIFY: TODO_VERIFY_TRANSLATION: {fallback}"
    compact = " ".join(text.split())
    return f"TODO_VERIFY: TODO_VERIFY_TRANSLATION: English source: {compact[:180]}"


def enrich_record_for_daily_radar(
    record: PaperRecord,
    run_date: date,
    window_days: int = FRESHNESS_WINDOW_DAYS,
    *,
    coverage_start: datetime | None = None,
    coverage_end: datetime | None = None,
) -> PaperRecord:
    if record.freshness_policy_version == STRICT_FRESHNESS_POLICY_VERSION and coverage_start is None and coverage_end is None:
        freshness = FreshnessDecision(
            record.selected_date_basis,
            record.freshness_bucket,
            record.freshness_reason,
            record.primary_today_new_eligible,
        )
    else:
        freshness = decide_freshness(
            record,
            run_date,
            window_days,
            coverage_start=coverage_start,
            coverage_end=coverage_end,
        )
    venue = detect_venue_metadata(record)
    abstract_en = record.abstract or TODO_VERIFY
    conclusion = getattr(record, "conclusion", "") or ""
    conclusion_en = conclusion or (
        f"model-generated from available metadata: {record.abstract[:180]}" if record.abstract else TODO_VERIFY
    )
    todo_flags = list(getattr(record, "TODO_VERIFY_flags", []) or [])
    if abstract_en == TODO_VERIFY:
        todo_flags.append("abstract_en")
    if conclusion == "":
        todo_flags.append("conclusion_en")
    todo_flags.extend(["abstract_zh", "conclusion_zh", "TODO_VERIFY_TRANSLATION"])
    if freshness.selected_date_basis == TODO_VERIFY:
        todo_flags.append("selected_date_basis")
    if venue.venue_status == TODO_VERIFY:
        todo_flags.append("venue")
    if venue.ccf_rank == TODO_VERIFY or venue.ccf_status == "todo_verify":
        todo_flags.append("CCF_rank")
    ccf_rank = venue.ccf_rank if venue.ccf_rank in {"A", "B", "C", "N/A", "unknown", TODO_VERIFY} else TODO_VERIFY
    calibration = calibrate_recommendation(
        record,
        freshness_bucket=freshness.freshness_bucket,
        primary_today_new_eligible=freshness.primary_today_new_eligible,
        selected_date_basis=freshness.selected_date_basis,
        todo_verify_flags=todo_flags,
        venue_confidence=venue.venue_confidence,
        venue_status=venue.venue_status,
        ccf_rank=ccf_rank,
    )
    todo_flags = sorted(set(todo_flags) | set(calibration.recommendation_risk_flags))
    calibrated_update = calibration_to_update(calibration)
    enriched = record.model_copy(
        update={
            "title_en": record.title,
            "title_zh": record.chinese_title or f"model-generated zh title: {record.title}",
            "venue": record.venue or venue.venue,
            "venue_type": venue.venue_type,
            "publisher_or_source": venue.publisher_or_source,
            "CCF_rank": ccf_rank,
            "venue_status": venue.venue_status,
            "venue_expanded_security_crypto_systems_scope": venue.expanded_security_crypto_systems_scope,
            "venue_relevance": venue.venue_relevance,
            "venue_confidence": venue.venue_confidence,
            "selected_date_basis": freshness.selected_date_basis,
            "freshness_bucket": freshness.freshness_bucket,
            "freshness_reason": freshness.freshness_reason,
            "primary_today_new_eligible": freshness.primary_today_new_eligible,
            "freshness_policy_version": STRICT_FRESHNESS_POLICY_VERSION,
            "abstract_en": abstract_en,
            "abstract_zh": _generated_zh_summary(record.abstract, "source abstract missing"),
            "conclusion_en": conclusion_en,
            "conclusion_zh": _generated_zh_summary(conclusion or record.abstract, "source conclusion missing"),
            "translation_fidelity_status": "TODO_VERIFY_TRANSLATION",
            "translation_fidelity_flags": sorted(set(record.translation_fidelity_flags) | {"TODO_VERIFY_TRANSLATION"}),
            **calibrated_update,
            "TODO_VERIFY_flags": todo_flags,
            "source_urls": [record.source_url] if record.source_url else [],
            "source_refs": [record.source_url] if record.source_url else [],
        }
    )
    return apply_critical_translation(enriched)


def apply_daily_freshness_policy(
    records: list[PaperRecord],
    run_date: date,
    window_days: int = FRESHNESS_WINDOW_DAYS,
    *,
    coverage_start: datetime | None = None,
    coverage_end: datetime | None = None,
) -> tuple[list[PaperRecord], list[PaperRecord]]:
    enriched = [
        enrich_record_for_daily_radar(
            record,
            run_date,
            window_days,
            coverage_start=coverage_start,
            coverage_end=coverage_end,
        )
        for record in records
    ]
    primary = [record for record in enriched if record.primary_today_new_eligible]
    routed = [record for record in enriched if not record.primary_today_new_eligible]
    return primary, routed
