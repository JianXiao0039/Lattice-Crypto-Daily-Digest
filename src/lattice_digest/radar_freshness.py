from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Mapping

from lattice_digest.models import PaperRecord
from lattice_digest.venue_registry import TODO_VERIFY, VenueRegistryEntry, find_registry_entry


FRESHNESS_WINDOW_DAYS = 1


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
) -> FreshnessDecision:
    for basis in ("publication_date", "announcement_date", "update_date"):
        value = _field(record, basis)
        if _in_window(value, run_date, window_days):
            return FreshnessDecision(basis, "primary_today_new", f"{basis} within freshness window", True)

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

    first_seen = _field(record, "first_seen_date")
    if _in_window(first_seen, run_date, window_days):
        return FreshnessDecision(
            "first_seen_date",
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
    text = " ".join(
        str(_field(record, name) or "")
        for name in ("title", "abstract", "reason", "taxonomy_tags", "keywords_matched")
    ).lower()
    topics = [
        ("AI-assisted lattice cryptanalysis", ("ai-assisted", "neural", "transformer", "coordinate")),
        ("lattice cryptography", ("lattice", "lwe", "rlwe", "mlwe", "sis", "ntru")),
        ("Module-SIS", ("module-sis", "msis", "commitment", "chameleon")),
        ("ML-KEM / ML-DSA / FN-DSA / HAWK", ("ml-kem", "kyber", "ml-dsa", "dilithium", "fn-dsa", "falcon", "hawk")),
        ("PQC implementation", ("implementation", "side-channel", "fault", "constant-time")),
        ("cryptanalysis", ("cryptanalysis", "bkz", "attack", "svp", "cvp", "hybrid")),
        ("systems/security deployment", ("tls", "deployment", "migration", "standardization")),
        ("ZK-friendly PQ primitives", ("zero-knowledge", "zk", "proof")),
    ]
    matched = [label for label, terms in topics if any(term in text for term in terms)]
    if not matched:
        return "TODO_VERIFY: insufficient reliable topic evidence for a specific recommendation reason."
    return "Useful for " + "; ".join(matched[:3]) + "."


def _generated_zh_summary(text: str, fallback: str) -> str:
    if not text:
        return f"TODO_VERIFY: {fallback}"
    compact = " ".join(text.split())
    return f"model-generated zh summary: {compact[:180]}"


def enrich_record_for_daily_radar(
    record: PaperRecord,
    run_date: date,
    window_days: int = FRESHNESS_WINDOW_DAYS,
) -> PaperRecord:
    freshness = decide_freshness(record, run_date, window_days)
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
    if freshness.selected_date_basis == TODO_VERIFY:
        todo_flags.append("selected_date_basis")
    if venue.venue_status == TODO_VERIFY:
        todo_flags.append("venue")
    if venue.ccf_rank == TODO_VERIFY or venue.ccf_status == "todo_verify":
        todo_flags.append("CCF_rank")
    ccf_rank = venue.ccf_rank if venue.ccf_rank in {"A", "B", "C", "N/A", "unknown", TODO_VERIFY} else TODO_VERIFY
    score = int(record.relevance_score)
    return record.model_copy(
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
            "lattice_crypto_relevance": record.reason or recommendation_reason(record),
            "abstract_en": abstract_en,
            "abstract_zh": _generated_zh_summary(record.abstract, "source abstract missing"),
            "conclusion_en": conclusion_en,
            "conclusion_zh": _generated_zh_summary(conclusion or record.abstract, "source conclusion missing"),
            "recommendation_level": recommendation_level(score, freshness.freshness_bucket),
            "recommendation_score": score,
            "recommendation_reason": recommendation_reason(record),
            "TODO_VERIFY_flags": sorted(set(todo_flags)),
            "source_urls": [record.source_url] if record.source_url else [],
            "source_refs": [record.source_url] if record.source_url else [],
        }
    )


def apply_daily_freshness_policy(
    records: list[PaperRecord],
    run_date: date,
    window_days: int = FRESHNESS_WINDOW_DAYS,
) -> tuple[list[PaperRecord], list[PaperRecord]]:
    enriched = [enrich_record_for_daily_radar(record, run_date, window_days) for record in records]
    primary = [record for record in enriched if record.primary_today_new_eligible]
    routed = [record for record in enriched if not record.primary_today_new_eligible]
    return primary, routed
