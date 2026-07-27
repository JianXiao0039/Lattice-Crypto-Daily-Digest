from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from lattice_digest.digest_sections import (
    AI_LATTICE,
    HIGH_PRIORITY,
    IDEA_BANK_CANDIDATES,
    LATTICE_REDUCTION_ATTACKS,
    LWE_FAMILY,
    PAPER_PLAN_CANDIDATES,
    PQC_STANDARDS,
    REPORT_BUCKET_ORDER,
    RESEARCH_SECTION_ORDER,
    SIS_NTRU_COMMITMENTS,
    TOPICAL_SECTION_ORDER,
    assign_report_buckets,
    assign_research_sections,
    candidate_reason,
)
from lattice_digest.models import make_paper_record
from lattice_digest.recommendation_rationale import build_bilingual_rationale, build_recommendation_rationale, format_bilingual_rationale_markdown
from lattice_digest.report_quality import (
    anchor_evidence_text,
    false_positive_risk_text,
    semantic_scholar_advisory_text,
    source_health_caveat_text,
)
from lattice_digest.artifact_paths import (
    legacy_daily_data_candidates,
    weekly_data_path,
    weekly_digest_path,
    daily_data_path,
    resolve_existing,
)


SCHEMA_VERSION = 1
LABEL_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}
PRIMARY_FRESHNESS_BUCKET = "primary_today_new"
PRIVATE_WEEKLY_PREFIX = "_weekly_"
TOPIC_GROUP_ORDER = (
    "AI4LC",
    "lattice cryptanalysis / BKZ / G6K / sparse LWE",
    "LWE / RLWE / MLWE",
    "SIS / Module-SIS",
    "ML-KEM / ML-DSA / Falcon / HAWK",
    "lattice signatures / ring signatures / chameleon hash",
    "ZK-friendly PQ primitives",
    "PQC implementation / security engineering",
    "FHE / lattice HE",
    "generic security / other",
)
READING_QUEUE_ORDER = (
    "read now",
    "skim",
    "save for background",
    "verify first",
    "Obsidian queue",
    "blog candidate",
    "PhD/PI email candidate",
    "project idea candidate",
)


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _date_range(start: date, end: date) -> list[date]:
    days = (end - start).days
    if days < 0:
        raise ValueError("from_date must be on or before to_date")
    return [start + timedelta(days=offset) for offset in range(days + 1)]


def _week_id(value: date) -> str:
    iso = value.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {"metadata": {}, "records": payload, "source_health": []}
    if isinstance(payload, dict):
        return payload
    return {"metadata": {}, "records": [], "source_health": []}


def _records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("records")
    return [item for item in records if isinstance(item, dict)] if isinstance(records, list) else []


def _normalize_title(value: str) -> str:
    text = value.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def dedup_key(record: dict[str, Any]) -> str:
    doi = str(record.get("doi") or "").strip().lower()
    if doi:
        return f"doi:{doi.removeprefix('https://doi.org/')}"
    arxiv_id = str(record.get("arxiv_id") or "").strip().lower()
    if arxiv_id:
        return f"arxiv:{re.sub('v[0-9]+$', '', arxiv_id)}"
    eprint_id = str(record.get("eprint_id") or "").strip().lower()
    if eprint_id:
        return f"eprint:{eprint_id}"
    source_url = str(record.get("source_url") or record.get("url") or "").strip().lower()
    if source_url:
        return f"url:{source_url}"
    normalized_title = str(record.get("normalized_title") or "").strip().lower()
    title = normalized_title or _normalize_title(str(record.get("title") or "untitled"))
    return f"title:{title}"


def _publication_date(record: dict[str, Any]) -> str:
    return str(record.get("publication_date") or record.get("date") or record.get("update_date") or "")


def _date_rank(value: str) -> int:
    try:
        return -date.fromisoformat(value[:10]).toordinal()
    except ValueError:
        return 0


def _display_sort_key(record: dict[str, Any]) -> tuple[int, int, int, str]:
    label = str(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or 0)
    return (LABEL_ORDER.get(label, 9), -score, _date_rank(_publication_date(record)), str(record.get("title") or "").lower())


def _stable_sections(values: list[str]) -> list[str]:
    order = {name: index for index, name in enumerate(RESEARCH_SECTION_ORDER)}
    return sorted(
        {value for value in values if value in order},
        key=lambda value: (order.get(value, 999), value.lower()),
    )


def _stable_report_buckets(values: list[str]) -> list[str]:
    order = {name: index for index, name in enumerate(REPORT_BUCKET_ORDER)}
    return sorted(
        {value for value in values if value in order},
        key=lambda value: (order.get(value, 999), value.lower()),
    )


def _paper_record_from_dict(record: dict[str, Any]):
    return make_paper_record(
        title=str(record.get("title") or "untitled"),
        authors=[str(author) for author in record.get("authors", [])] if isinstance(record.get("authors"), list) else [],
        abstract=str(record.get("abstract") or ""),
        source=str(record.get("source") or "unknown"),
        source_url=str(record.get("source_url") or record.get("url") or ""),
        paper_id=record.get("paper_id"),
        arxiv_id=record.get("arxiv_id"),
        eprint_id=record.get("eprint_id"),
        doi=record.get("doi"),
        venue=record.get("venue"),
        publication_date=record.get("publication_date") or record.get("date"),
        update_date=record.get("update_date"),
        categories=[str(item) for item in record.get("categories", [])] if isinstance(record.get("categories"), list) else [],
        taxonomy_tags=[str(item) for item in record.get("taxonomy_tags", [])] if isinstance(record.get("taxonomy_tags"), list) else [],
        keywords_matched=[str(item) for item in record.get("keywords_matched", [])] if isinstance(record.get("keywords_matched"), list) else [],
        negative_keywords_matched=[str(item) for item in record.get("negative_keywords_matched", [])]
        if isinstance(record.get("negative_keywords_matched"), list)
        else [],
        relevance_score=int(record.get("relevance_score") or 0),
        relevance_label=str(record.get("relevance_label") or "D"),
        reason=str(record.get("reason") or record.get("reason_for_priority") or ""),
    )


def _research_sections(record: dict[str, Any]) -> list[str]:
    sections = record.get("research_sections")
    if isinstance(sections, list) and sections:
        topical = _stable_sections([str(section) for section in sections])
        if topical:
            return topical
    return assign_research_sections(_paper_record_from_dict(record))


def _report_buckets(record: dict[str, Any]) -> list[str]:
    buckets = record.get("report_buckets")
    if isinstance(buckets, list) and buckets:
        return _stable_report_buckets([str(bucket) for bucket in buckets])
    legacy_sections = record.get("research_sections")
    if isinstance(legacy_sections, list) and legacy_sections:
        legacy = _stable_report_buckets([str(section) for section in legacy_sections])
        if legacy:
            return legacy
    return assign_report_buckets(_paper_record_from_dict(record))


def _merge_record(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    seen_dates = sorted({*base.get("seen_dates", []), *incoming.get("seen_dates", [])})
    seen_sources = sorted({*base.get("seen_sources", []), *incoming.get("seen_sources", [])})
    merged["seen_dates"] = seen_dates
    merged["seen_sources"] = seen_sources
    merged["research_sections"] = _stable_sections(
        [*base.get("research_sections", []), *incoming.get("research_sections", [])]
    )
    merged["report_buckets"] = _stable_report_buckets(
        [*base.get("report_buckets", []), *incoming.get("report_buckets", [])]
    )
    for key in (
        "TODO_VERIFY_flags",
        "recommendation_risk_flags",
        "source_refs",
        "source_urls",
        "user_relevance_tags",
    ):
        base_values = base.get(key, [])
        incoming_values = incoming.get(key, [])
        if isinstance(base_values, list) or isinstance(incoming_values, list):
            values_by_key: dict[str, Any] = {}
            for values in (base_values, incoming_values):
                if not isinstance(values, list):
                    continue
                for value in values:
                    if value in (None, ""):
                        continue
                    value_key = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
                    values_by_key[value_key] = value
            merged[key] = [values_by_key[value_key] for value_key in sorted(values_by_key)]
    occurrences_by_key: dict[str, dict[str, Any]] = {}
    for values in (
        base.get(PRIVATE_WEEKLY_PREFIX + "occurrences", []),
        incoming.get(PRIVATE_WEEKLY_PREFIX + "occurrences", []),
    ):
        if not isinstance(values, list):
            continue
        for occurrence in values:
            if not isinstance(occurrence, dict):
                continue
            occurrence_key = json.dumps(occurrence, ensure_ascii=False, sort_keys=True)
            occurrences_by_key[occurrence_key] = dict(occurrence)
    merged[PRIVATE_WEEKLY_PREFIX + "occurrences"] = [
        occurrences_by_key[key] for key in sorted(occurrences_by_key)
    ]
    if _display_sort_key(incoming) < _display_sort_key(base):
        for key, value in incoming.items():
            if key not in {
                "seen_dates",
                "seen_sources",
                "research_sections",
                "report_buckets",
                "TODO_VERIFY_flags",
                "recommendation_risk_flags",
                "source_refs",
                "source_urls",
                "user_relevance_tags",
                PRIVATE_WEEKLY_PREFIX + "occurrences",
            }:
                merged[key] = value
    for key, value in incoming.items():
        if key not in merged or merged.get(key) in (None, "", [], {}):
            merged[key] = value
    occurrences = merged.get(PRIVATE_WEEKLY_PREFIX + "occurrences", [])
    if isinstance(occurrences, list):
        eligible_occurrences = [
            occurrence
            for occurrence in occurrences
            if isinstance(occurrence, dict)
            and occurrence.get("primary_today_new_eligible") is True
            and occurrence.get("freshness_bucket") == PRIMARY_FRESHNESS_BUCKET
        ]
        merged["primary_today_new_eligible"] = bool(eligible_occurrences)
        if eligible_occurrences:
            merged["freshness_bucket"] = PRIMARY_FRESHNESS_BUCKET
            reason = next(
                (
                    str(occurrence.get("freshness_reason"))
                    for occurrence in eligible_occurrences
                    if occurrence.get("freshness_reason")
                ),
                "",
            )
            if reason:
                merged["freshness_reason"] = reason
    return merged


def _source_health_summary(daily_payloads: list[tuple[date, dict[str, Any]]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for day, payload in daily_payloads:
        source_health = payload.get("source_health") or payload.get("metadata", {}).get("source_health")
        if isinstance(source_health, list):
            for item in source_health:
                if isinstance(item, dict):
                    rows.append(
                        {
                            "date": day.isoformat(),
                            "source": item.get("source"),
                            "status": item.get("health_status") or item.get("status"),
                            "final_count": item.get("final_count", item.get("final_records", 0)),
                            "error_type": item.get("error_type"),
                        }
                    )
    if not rows:
        return {"available": False, "sources": [], "note": "No source health data available in selected daily JSON files."}
    status_counts = Counter(str(row.get("status") or "unknown") for row in rows)
    sources = sorted({str(row.get("source") or "unknown") for row in rows})
    return {"available": True, "sources": sources, "status_counts": dict(sorted(status_counts.items())), "records": rows}


def load_daily_json(data_dir: Path, selected_days: list[date]) -> tuple[list[tuple[date, dict[str, Any]]], list[str]]:
    loaded: list[tuple[date, dict[str, Any]]] = []
    missing: list[str] = []
    for day in selected_days:
        path, used_legacy = resolve_existing(
            daily_data_path(day, data_dir),
            legacy_daily_data_candidates(day, data_dir),
        )
        if not path.exists():
            missing.append(day.isoformat())
            continue
        if used_legacy:
            print(f"Warning: using legacy daily JSON fallback: {path}")
        loaded.append((day, _read_json(path)))
    return loaded, missing


def _prepare_record(record: dict[str, Any], day: date) -> dict[str, Any]:
    item = dict(record)
    item["seen_dates"] = [day.isoformat()]
    source = str(item.get("source") or "unknown")
    item["seen_sources"] = [source]
    item["research_sections"] = _research_sections(item)
    item["report_buckets"] = _report_buckets(item)
    item["dedup_key"] = dedup_key(item)
    item[PRIVATE_WEEKLY_PREFIX + "occurrences"] = [
        {
            "date": day.isoformat(),
            "source": source,
            "freshness_bucket": item.get("freshness_bucket"),
            "freshness_reason": item.get("freshness_reason"),
            "primary_today_new_eligible": item.get("primary_today_new_eligible") is True,
            "recommendation_level": item.get("recommendation_level"),
            "suggested_action": item.get("suggested_action"),
        }
    ]
    return item


def aggregate_records(daily_payloads: list[tuple[date, dict[str, Any]]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for day, payload in daily_payloads:
        for record in _records(payload):
            item = _prepare_record(record, day)
            key = item["dedup_key"]
            by_key[key] = _merge_record(by_key[key], item) if key in by_key else item
    return sorted(by_key.values(), key=_display_sort_key)


def _string_values(record: dict[str, Any], key: str) -> list[str]:
    value = record.get(key)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value not in (None, ""):
        return [str(value).strip()]
    return []


def _score(record: dict[str, Any], key: str, fallback: int = 0) -> int:
    try:
        return int(record.get(key) if record.get(key) is not None else fallback)
    except (TypeError, ValueError):
        return fallback


def _all_weekly_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for container_key in ("sections", "report_buckets"):
        container = payload.get(container_key, {})
        if not isinstance(container, dict):
            continue
        for values in container.values():
            if not isinstance(values, list):
                continue
            for record in values:
                if isinstance(record, dict):
                    by_key.setdefault(dedup_key(record), record)
    return sorted(by_key.values(), key=_display_sort_key)


def _source_status_map(payload: dict[str, Any]) -> dict[str, str]:
    health = payload.get("source_health_summary", {})
    rows = health.get("records", []) if isinstance(health, dict) else []
    status_order = {"red": 3, "yellow": 2, "green": 1, "unknown": 0}
    statuses: dict[str, str] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        source = str(row.get("source") or "unknown").strip().lower()
        status = str(row.get("status") or "unknown").strip().lower()
        current = statuses.get(source, "unknown")
        if status_order.get(status, 0) > status_order.get(current, 0):
            statuses[source] = status
    return statuses


def _record_risk_flags(record: dict[str, Any], source_statuses: dict[str, str]) -> list[str]:
    flags = {
        *_string_values(record, "TODO_VERIFY_flags"),
        *_string_values(record, "recommendation_risk_flags"),
    }
    level = str(record.get("recommendation_level") or "").strip()
    if level == "TODO_VERIFY":
        flags.add("recommendation_level=TODO_VERIFY")
    if not str(record.get("selected_date_basis") or "").strip():
        flags.add("missing selected_date_basis")
    bucket = str(record.get("freshness_bucket") or "").strip().lower()
    if "todo" in bucket or "unknown" in bucket:
        flags.add(f"freshness_bucket={bucket or 'unknown'}")
    venue_status = str(record.get("venue_status") or "").strip().lower()
    if venue_status in {"todo_verify", "unknown", "ambiguous"}:
        flags.add(f"venue_status={venue_status}")
    ccf_rank = str(record.get("CCF_rank") or record.get("ccf_rank") or "").strip()
    venue_type = str(record.get("venue_type") or "").strip().lower()
    if venue_type in {"conference", "journal", "workshop"} and ccf_rank.lower() in {"", "unknown", "todo_verify"}:
        flags.add("CCF_rank=unknown")
    source = str(record.get("source") or "unknown").strip().lower()
    source_status = source_statuses.get(source)
    if source_status in {"red", "yellow"}:
        flags.add(f"source_health={source_status}:{source}")
    if not str(record.get("source_url") or record.get("url") or "").strip():
        flags.add("missing source URL")
    return sorted(flags, key=str.lower)


def _hard_verify_required(record: dict[str, Any], risk_flags: list[str]) -> bool:
    if str(record.get("recommendation_level") or "") == "TODO_VERIFY":
        return True
    if _string_values(record, "TODO_VERIFY_flags"):
        return True
    hard_fragments = (
        "missing selected_date_basis",
        "missing source url",
        "source_health=red",
        "date_uncertain",
        "metadata_uncertain",
        "todo_verify",
        "venue_status=todo_verify",
        "venue_status=ambiguous",
    )
    return any(any(fragment in flag.lower() for fragment in hard_fragments) for flag in risk_flags)


def _is_primary_new(record: dict[str, Any]) -> bool:
    return (
        record.get("primary_today_new_eligible") is True
        and str(record.get("freshness_bucket") or "") == PRIMARY_FRESHNESS_BUCKET
    )


def _weekly_sort_key(record: dict[str, Any]) -> tuple[int, int, int, str]:
    action_score = _score(record, "recommendation_score", _score(record, "relevance_score"))
    research_score = _score(record, "research_value_score", _score(record, "relevance_score"))
    relevance_score = _score(record, "relevance_score")
    return (-action_score, -research_score, -relevance_score, str(record.get("title") or "").lower())


def _backfill_sort_key(record: dict[str, Any]) -> tuple[int, int, int, str]:
    research_score = _score(record, "research_value_score", _score(record, "relevance_score"))
    action_score = _score(record, "recommendation_score", _score(record, "relevance_score"))
    relevance_score = _score(record, "relevance_score")
    return (-research_score, -action_score, -relevance_score, str(record.get("title") or "").lower())


def _route_weekly_records(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    source_statuses = _source_status_map(payload)
    routed = {"primary_new": [], "backfill": [], "verify_first": []}
    for record in _all_weekly_records(payload):
        risks = _record_risk_flags(record, source_statuses)
        routed_record = dict(record)
        routed_record[PRIVATE_WEEKLY_PREFIX + "risk_flags"] = risks
        if _hard_verify_required(routed_record, risks):
            routed["verify_first"].append(routed_record)
        elif _is_primary_new(routed_record):
            routed["primary_new"].append(routed_record)
        else:
            routed["backfill"].append(routed_record)
    routed["primary_new"].sort(key=_weekly_sort_key)
    routed["backfill"].sort(key=_backfill_sort_key)
    routed["verify_first"].sort(key=_backfill_sort_key)
    return routed


def _topic_group(record: dict[str, Any]) -> str:
    parts = [
        str(record.get("title") or ""),
        str(record.get("abstract") or record.get("abstract_en") or ""),
        *(_string_values(record, "user_relevance_tags")),
        *(_string_values(record, "taxonomy_tags")),
        *(_string_values(record, "research_sections")),
    ]
    text = " ".join(parts).lower()
    if any(token in text for token in ("ai4lc", "ai-assisted lattice", "neural cryptanalysis", "transformer lwe")):
        return TOPIC_GROUP_ORDER[0]
    if any(token in text for token in ("cryptanalysis", "bkz", "g6k", "lattice reduction", "sparse lwe", "lll")):
        return TOPIC_GROUP_ORDER[1]
    if any(token in text for token in ("rlwe", "mlwe", "module-lwe", "ring-lwe", "learning with errors", "lwe")):
        return TOPIC_GROUP_ORDER[2]
    if any(token in text for token in ("module-sis", "module sis", "msis", "ring-sis", " sis")):
        return TOPIC_GROUP_ORDER[3]
    if any(token in text for token in ("ml-kem", "kyber", "ml-dsa", "dilithium", "falcon", "fn-dsa", "hawk")):
        return TOPIC_GROUP_ORDER[4]
    if any(token in text for token in ("ring signature", "linkable", "chameleon hash", "lattice signature")):
        return TOPIC_GROUP_ORDER[5]
    if any(token in text for token in ("zero-knowledge", "zk-friendly", "lattice zkp", "post-quantum zk")):
        return TOPIC_GROUP_ORDER[6]
    if any(token in text for token in ("side-channel", "fault", "implementation", "constant-time", "pqc deployment")):
        return TOPIC_GROUP_ORDER[7]
    if any(token in text for token in ("fhe", "ckks", "bfv", "bgv", "tfhe", "homomorphic encryption")):
        return TOPIC_GROUP_ORDER[8]
    return TOPIC_GROUP_ORDER[9]


def _topic_distribution(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    distribution = {group: [] for group in TOPIC_GROUP_ORDER}
    for record in records:
        distribution[_topic_group(record)].append(record)
    return distribution


def _venue_ccf_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    ccf_counts: Counter[str] = Counter()
    venue_type_counts: Counter[str] = Counter()
    venue_status_counts: Counter[str] = Counter()
    for record in records:
        rank = str(record.get("CCF_rank") or record.get("ccf_rank") or "unknown").strip()
        normalized_rank = rank.upper() if rank.upper() in {"A", "B", "C", "N/A"} else "unknown"
        ccf_counts[normalized_rank] += 1
        venue_type_counts[str(record.get("venue_type") or "unknown").strip().lower()] += 1
        venue_status_counts[str(record.get("venue_status") or "unknown").strip().lower()] += 1
    return {
        "ccf_counts": dict(sorted(ccf_counts.items())),
        "venue_type_counts": dict(sorted(venue_type_counts.items())),
        "venue_status_counts": dict(sorted(venue_status_counts.items())),
    }


def _source_health_confidence(payload: dict[str, Any]) -> tuple[str, str, list[str]]:
    coverage = payload.get("coverage", {})
    health = payload.get("source_health_summary", {})
    status_counts = health.get("status_counts", {}) if isinstance(health, dict) else {}
    normalized_counts = {str(key).lower(): int(value) for key, value in status_counts.items()}
    red = normalized_counts.get("red", 0)
    yellow = normalized_counts.get("yellow", 0)
    green = normalized_counts.get("green", 0)
    expected = int(coverage.get("expected_days") or 0)
    loaded = len(coverage.get("loaded_days", []))
    unique = int(coverage.get("unique_records") or 0)
    degraded_sources = sorted(
        source
        for source, status in _source_status_map(payload).items()
        if status in {"red", "yellow"}
    )
    if expected and loaded * 2 <= expected:
        return "low", "source-starved partial coverage", degraded_sources
    if unique == 0 or loaded == 0 or (red and green == 0):
        return "low", "source-starved", degraded_sources
    if red or yellow or loaded < expected:
        return "medium", "degraded or partial coverage", degraded_sources
    return "high", "complete local-artifact coverage", degraded_sources


def _display_action(record: dict[str, Any], placement: str, hard_verify: bool) -> str:
    if hard_verify or placement == "verify_first":
        return "Verify source first"
    existing = str(record.get("suggested_action") or "").strip()
    if placement != "primary_new" and existing.lower() in {"read today", "read now"}:
        return "Save for background"
    if existing:
        return existing
    if placement == "primary_new":
        return "Read now" if str(record.get("recommendation_level") or "") == "Strong" else "Skim"
    return "Save for background"


def _reading_queue(
    routed: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    queues = {name: [] for name in READING_QUEUE_ORDER}
    for placement, records in routed.items():
        for record in records:
            risks = record.get(PRIVATE_WEEKLY_PREFIX + "risk_flags", [])
            hard_verify = _hard_verify_required(record, risks if isinstance(risks, list) else [])
            action = _display_action(record, placement, hard_verify).lower()
            if placement == "verify_first":
                queues["verify first"].append(record)
            elif placement == "primary_new" and action in {"read today", "read now"}:
                queues["read now"].append(record)
            elif placement == "primary_new":
                queues["skim"].append(record)
            else:
                queues["save for background"].append(record)
            tags = " ".join(_string_values(record, "user_relevance_tags")).lower()
            url = str(record.get("source_url") or record.get("url") or "")
            research_score = _score(record, "research_value_score", _score(record, "relevance_score"))
            if url and (tags or research_score >= 60):
                queues["Obsidian queue"].append(record)
            if any(token in tags for token in ("implementation", "security", "standard", "cryptanalysis")):
                queues["blog candidate"].append(record)
            phd = str(record.get("phd_application_relevance") or "").lower()
            if phd and not any(token in phd for token in ("low", "not directly", "none")):
                queues["PhD/PI email candidate"].append(record)
            if any(token in tags for token in ("module-sis", "chameleon", "ai4lc", "zk", "bkz", "g6k", "sparse lwe")):
                queues["project idea candidate"].append(record)
    for values in queues.values():
        values.sort(key=_backfill_sort_key)
    return queues


def _strip_private_weekly(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_private_weekly(item)
            for key, item in value.items()
            if not str(key).startswith(PRIVATE_WEEKLY_PREFIX)
        }
    if isinstance(value, list):
        return [_strip_private_weekly(item) for item in value]
    return value


def _section_map(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    sections = {name: [] for name in TOPICAL_SECTION_ORDER}
    for record in records:
        for section in record.get("research_sections", []):
            if section in sections:
                sections[section].append(record)
    return {name: sorted(items, key=_display_sort_key) for name, items in sections.items()}


def _report_bucket_map(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets = {name: [] for name in REPORT_BUCKET_ORDER}
    for record in records:
        for bucket in record.get("report_buckets", []):
            if bucket in buckets:
                buckets[bucket].append(record)
    return {name: sorted(items, key=_display_sort_key) for name, items in buckets.items()}


def _candidate_reason(record: dict[str, Any], section: str) -> str:
    paper = _paper_record_from_dict(record)
    paper.relevance_label = str(record.get("relevance_label") or "D")
    paper.relevance_score = int(record.get("relevance_score") or 0)
    paper.keywords_matched = [str(item) for item in record.get("keywords_matched", [])] if isinstance(record.get("keywords_matched"), list) else []
    paper.taxonomy_tags = [str(item) for item in record.get("taxonomy_tags", [])] if isinstance(record.get("taxonomy_tags"), list) else []
    return candidate_reason(paper, section)


def _idea_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        {
            "title": record.get("title"),
            "relevance_label": record.get("relevance_label"),
            "relevance_score": record.get("relevance_score"),
            "source_url": record.get("source_url") or record.get("url"),
            "research_sections": record.get("research_sections", []),
            "reason": _candidate_reason(record, IDEA_BANK_CANDIDATES),
        }
        for record in records
        if IDEA_BANK_CANDIDATES in record.get("report_buckets", [])
    ]
    return sorted(candidates, key=lambda item: (LABEL_ORDER.get(str(item.get("relevance_label")), 9), -int(item.get("relevance_score") or 0), str(item.get("title") or "").lower()))


def _paper_plan_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        {
            "title": record.get("title"),
            "relevance_label": record.get("relevance_label"),
            "relevance_score": record.get("relevance_score"),
            "source_url": record.get("source_url") or record.get("url"),
            "research_sections": record.get("research_sections", []),
            "reason": _candidate_reason(record, PAPER_PLAN_CANDIDATES),
        }
        for record in records
        if PAPER_PLAN_CANDIDATES in record.get("report_buckets", [])
    ]
    return sorted(candidates, key=lambda item: (LABEL_ORDER.get(str(item.get("relevance_label")), 9), -int(item.get("relevance_score") or 0), str(item.get("title") or "").lower()))


def build_weekly_synthesis(
    data_dir: Path,
    from_date: date,
    to_date: date,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    selected_days = _date_range(from_date, to_date)
    loaded_payloads, missing_days = load_daily_json(data_dir, selected_days)
    records = aggregate_records(loaded_payloads)
    sections = _section_map(records)
    report_buckets = _report_bucket_map(records)
    total_records = sum(len(_records(payload)) for _, payload in loaded_payloads)
    label_counts = Counter(str(record.get("relevance_label") or "D") for record in records)
    generated = generated_at or datetime.now(timezone.utc)
    return {
        "schema_version": 1,
        "week_id": _week_id(to_date),
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "generated_at": generated.isoformat(),
        "coverage": {
            "expected_days": len(selected_days),
            "loaded_days": [day.isoformat() for day, _ in loaded_payloads],
            "missing_days": missing_days,
            "total_records": total_records,
            "unique_records": len(records),
            "label_counts": dict(sorted(label_counts.items(), key=lambda item: LABEL_ORDER.get(item[0], 9))),
        },
        "label_counts": dict(sorted(label_counts.items(), key=lambda item: LABEL_ORDER.get(item[0], 9))),
        "sections": sections,
        "report_buckets": report_buckets,
        "idea_bank_candidates": _idea_candidates(records),
        "paper_plan_candidates": _paper_plan_candidates(records),
        "source_health_summary": _source_health_summary(loaded_payloads),
    }


def _placement_label(record: dict[str, Any], routed: dict[str, list[dict[str, Any]]]) -> str:
    key = dedup_key(record)
    for placement, records in routed.items():
        if any(dedup_key(item) == key for item in records):
            return placement
    return "backfill"


def _generated_marker_notes(record: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    for key in ("abstract_zh", "conclusion_en", "conclusion_zh"):
        value = str(record.get(key) or "")
        lowered = value.lower()
        if any(marker in lowered for marker in ("generated", "translated", "机器生成", "翻译生成", "系统生成")):
            notes.append(f"{key}: generated/translated marker preserved")
    return notes


def _compact_record(record: dict[str, Any], placement: str) -> str:
    risks = record.get(PRIVATE_WEEKLY_PREFIX + "risk_flags", [])
    risk_values = risks if isinstance(risks, list) else []
    hard_verify = _hard_verify_required(record, risk_values)
    action_score = _score(record, "recommendation_score", _score(record, "relevance_score"))
    research_score = _score(record, "research_value_score", _score(record, "relevance_score"))
    level = str(record.get("recommendation_level") or record.get("relevance_label") or "unknown")
    reason = str(
        record.get("recommendation_reason")
        or record.get("why_it_matters")
        or record.get("reason_for_priority")
        or build_recommendation_rationale(record).recommendation_reason
    ).strip()
    tags = _string_values(record, "user_relevance_tags") or _string_values(record, "taxonomy_tags")
    phd = str(record.get("phd_application_relevance") or "not specified")
    action = _display_action(record, placement, hard_verify)
    venue = str(record.get("venue") or "unknown")
    venue_type = str(record.get("venue_type") or "unknown")
    ccf_rank = str(record.get("CCF_rank") or record.get("ccf_rank") or "unknown")
    source = str(record.get("source") or "unknown")
    source_url = str(record.get("source_url") or record.get("url") or "unknown")
    date_basis = str(record.get("selected_date_basis") or "TODO_VERIFY")
    freshness = str(record.get("freshness_bucket") or "unknown")
    placement_text = {
        "primary_new": "PRIMARY-NEW",
        "backfill": "BACKFILL / NON-PRIMARY",
        "verify_first": "TODO_VERIFY / VERIFY FIRST",
    }.get(placement, placement.upper())
    lines = [
        f"### [{placement_text}] {record.get('title') or 'untitled'}",
        "",
        f"- Recommendation: **{level}** | action score: **{action_score}** | research value: **{research_score}**",
        f"- Suggested action: **{action}**",
        f"- Why it matters: {reason or 'TODO_VERIFY: concrete relevance reason unavailable.'}",
        f"- User relevance: {', '.join(tags) if tags else 'TODO_VERIFY'}",
        f"- PhD/application value: {phd}",
        f"- Source/date: {source} | basis={date_basis} | freshness={freshness}",
        f"- Venue/CCF: {venue} | type={venue_type} | CCF={ccf_rank}",
        f"- Source reference: {source_url}",
    ]
    if risk_values:
        lines.append(f"- Risk / TODO_VERIFY: {'; '.join(str(item) for item in risk_values)}")
    else:
        lines.append("- Risk / TODO_VERIFY: none recorded")
    markers = _generated_marker_notes(record)
    if markers:
        lines.append(f"- Generated/translated markers: {'; '.join(markers)}")
    lines.append("")
    return "\n".join(lines)


def _record_line(
    record: dict[str, Any],
    *,
    bilingual: bool = False,
    placement: str | None = None,
) -> str:
    title = str(record.get("title") or "untitled")
    label = str(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or 0)
    url = str(record.get("source_url") or record.get("url") or "unknown")
    sources = ", ".join(record.get("seen_sources", [])) if isinstance(record.get("seen_sources"), list) else str(record.get("source") or "unknown")
    dates = ", ".join(record.get("seen_dates", [])) if isinstance(record.get("seen_dates"), list) else ""
    rationale = build_recommendation_rationale(record)
    todo_verify = "；".join(rationale.todo_verify) if rationale.todo_verify else rationale.caveat
    placement_text = placement or "audit"
    recommendation_level = str(record.get("recommendation_level") or label)
    recommendation_score = _score(record, "recommendation_score", score)
    research_score = _score(record, "research_value_score", score)
    risk_flags = [
        *_string_values(record, "TODO_VERIFY_flags"),
        *_string_values(record, "recommendation_risk_flags"),
    ]
    lines = [
        f"- {title}｜{label} / {score}｜placement: {placement_text}｜sources: {sources}｜seen: {dates}｜{url}\n"
        f"  - Recommendation: {recommendation_level} / {recommendation_score}; research_value_score={research_score}; "
        f"suggested_action={record.get('suggested_action') or 'unknown'}\n"
        f"  - {anchor_evidence_text(record)}\n"
        f"  - False-positive risk: {false_positive_risk_text(record)}\n"
        f"  - Semantic Scholar advisory: {semantic_scholar_advisory_text(record)}\n"
        f"  - Rationale: {rationale.problem_summary} {rationale.radar_relevance} {rationale.recommendation_reason}\n"
        f"  - Evidence basis: {', '.join(rationale.evidence_basis)}；confidence={rationale.confidence}；TODO_VERIFY: {todo_verify}\n"
        f"  - Preserved risk flags: {'; '.join(risk_flags) if risk_flags else 'none'}"
    ]
    for key in ("abstract_en", "abstract_zh", "conclusion_en", "conclusion_zh"):
        if record.get(key):
            lines.append(f"  - {key}: {record.get(key)}")
    if bilingual:
        bilingual_rationale = build_bilingual_rationale(record, top_paper=True)
        rendered = "\n".join(f"  {line}" if line else "" for line in format_bilingual_rationale_markdown(bilingual_rationale))
        lines.append(rendered)
    return "\n".join(lines)


def render_markdown(payload: dict[str, Any]) -> str:
    coverage = payload["coverage"]
    routed = _route_weekly_records(payload)
    records = _all_weekly_records(payload)
    topics = _topic_distribution(records)
    venue_summary = _venue_ccf_summary(records)
    confidence, confidence_reason, degraded_sources = _source_health_confidence(payload)
    queues = _reading_queue(routed)
    primary_count = len(routed["primary_new"])
    backfill_count = len(routed["backfill"])
    verify_count = len(routed["verify_first"])
    top_primary = routed["primary_new"][:5]
    missing_days = coverage.get("missing_days", [])
    low_signal = primary_count == 0
    lines = [
        f"# 格密码周报 / Weekly Research Synthesis - {payload['week_id']}",
        "",
        f"- Date range: {payload['from_date']} .. {payload['to_date']}",
        f"- Coverage: {len(coverage['loaded_days'])}/{coverage['expected_days']} days; missing={len(missing_days)}",
        "",
        "## Executive Summary",
        "",
        "- 本周执行摘要 / Executive week decision:",
        (
            f"- 本周去重后 {coverage['unique_records']} 篇：安全 primary-new {primary_count} 篇，"
            f"高价值/背景 backfill {backfill_count} 篇，verify-first {verify_count} 篇。"
        ),
        f"- Weekly confidence: **{confidence}** ({confidence_reason}).",
        (
            "- 今日动作: "
            + ("优先阅读下方 primary-new 队列。" if primary_count else "无安全 primary-new；先核验风险项，再选择背景阅读。")
        ),
        "- Safety rule: recommendation_score is freshness/risk-gated; research_value_score is intrinsic value.",
        "- Backfill may be valuable but is never presented as primary-new. TODO_VERIFY is verify-first, never read-now.",
        "",
        "## 本周最值得读 / Top Papers This Week",
        "",
    ]
    if top_primary:
        for record in top_primary:
            lines.append(_compact_record(record, "primary_new"))
    else:
        lines.extend(["- 本周没有通过 freshness/risk gate 的 read-now primary-new 论文。", ""])

    lines.extend(["## Primary Today/New", ""])
    if routed["primary_new"]:
        for record in routed["primary_new"]:
            lines.append(_compact_record(record, "primary_new"))
    else:
        lines.extend(["- No safe primary-new records in this weekly window.", ""])

    lines.extend(["## High-Value Backfill / Older", ""])
    if routed["backfill"]:
        lines.append("- These items retain research value but remain non-primary.")
        for record in routed["backfill"]:
            lines.append(_compact_record(record, "backfill"))
    else:
        lines.extend(["- No backfill records.", ""])

    lines.extend(["## TODO_VERIFY / Verify First", ""])
    if routed["verify_first"]:
        lines.append("- Verify date/source/venue evidence before reading or citing.")
        for record in routed["verify_first"]:
            lines.append(_compact_record(record, "verify_first"))
    else:
        lines.extend(["- No verify-first records.", ""])

    lines.extend(["## Topic Distribution", ""])
    for topic in TOPIC_GROUP_ORDER:
        topic_records = topics[topic]
        titles = "; ".join(str(record.get("title") or "untitled") for record in topic_records[:3])
        suffix = f" - {titles}" if titles else ""
        lines.append(f"- {topic}: {len(topic_records)}{suffix}")
    lines.append("")

    lines.extend(["## Venue / CCF Summary", ""])
    lines.append(f"- Explicit CCF values only: {venue_summary['ccf_counts']}")
    lines.append(f"- Venue types: {venue_summary['venue_type_counts']}")
    lines.append(f"- Venue status: {venue_summary['venue_status_counts']}")
    lines.append("- No rank is inferred from Crossref, DBLP, OpenAlex, Semantic Scholar, source name, or topic.")
    lines.append("")

    lines.extend(["## Source Health Summary", ""])
    health = payload.get("source_health_summary", {})
    if not isinstance(health, dict) or not health.get("available"):
        lines.extend(["- No source health data available; weekly confidence is limited.", ""])
    else:
        lines.append(f"- Weekly confidence: {confidence} ({confidence_reason})")
        lines.append(f"- Sources: {', '.join(health.get('sources', []))}")
        lines.append(f"- Status counts: {health.get('status_counts', {})}")
        lines.append(f"- Degraded sources: {', '.join(degraded_sources) if degraded_sources else 'none'}")
        lines.append(f"- Caveat: {source_health_caveat_text(health)}")
        lines.append("")

    lines.extend(["## Research Actions", ""])
    if low_signal:
        lines.append("- Low-signal week: do not infer that no relevant papers exist; inspect source-health and missing-day coverage.")
    if confidence == "low":
        lines.append("- Source-starved week: verify primary sources before treating absence as evidence.")
    lines.append(f"- Read now: {len(queues['read now'])}")
    lines.append(f"- Skim: {len(queues['skim'])}")
    lines.append(f"- Save for background: {len(queues['save for background'])}")
    lines.append(f"- Verify first: {len(queues['verify first'])}")
    lines.append("")

    lines.extend(["## Reading Queue", ""])
    for queue_name in READING_QUEUE_ORDER:
        queue_records = queues[queue_name]
        lines.append(f"### {queue_name}")
        lines.append("")
        if queue_records:
            for record in queue_records:
                lines.append(f"- {record.get('title') or 'untitled'}")
            lines.append("")
        else:
            lines.extend(["- None.", ""])

    lines.extend(["## Detailed Provenance / Audit Appendix", ""])
    lines.append(f"- expected_days: {coverage['expected_days']}")
    lines.append(f"- loaded_days: {coverage['loaded_days']}")
    lines.append(f"- missing_days: {coverage['missing_days']}")
    lines.append(f"- total_records: {coverage['total_records']}")
    lines.append(f"- unique_records: {coverage['unique_records']}")
    lines.append(f"- label_counts: {coverage['label_counts']}")
    lines.append("")
    lines.extend(["### Duplicate merge provenance", ""])
    duplicate_records = [
        record
        for record in records
        if len(record.get(PRIVATE_WEEKLY_PREFIX + "occurrences", [])) > 1
    ]
    if duplicate_records:
        for record in duplicate_records:
            occurrences = record.get(PRIVATE_WEEKLY_PREFIX + "occurrences", [])
            lines.append(
                f"- {dedup_key(record)} | title={record.get('title')} | seen_dates={record.get('seen_dates', [])} "
                f"| seen_sources={record.get('seen_sources', [])} | occurrences={len(occurrences)}"
            )
    else:
        lines.append("- No duplicate merges in this window.")
    lines.append("")
    lines.extend(["### Source-health detail", ""])
    health_rows = health.get("records", []) if isinstance(health, dict) else []
    if isinstance(health_rows, list) and health_rows:
        for row in health_rows:
            if isinstance(row, dict):
                lines.append(
                    f"- {row.get('date', 'unknown')} | {row.get('source', 'unknown')} | "
                    f"status={row.get('status', 'unknown')} | final_count={row.get('final_count', 0)} | "
                    f"error_type={row.get('error_type') or 'none'}"
                )
    else:
        lines.append("- No source-health detail.")
    lines.append("")

    sections = payload.get("sections", {})
    report_buckets = payload.get("report_buckets", {})
    top_a = [record for record in records if str(record.get("relevance_label") or "D") == "A"]
    top_a = sorted(top_a, key=_weekly_sort_key)[:5]
    lines.extend(["## Top A-level Papers", ""])
    if top_a:
        lines.append("- Audit view only; placement labels remain authoritative and citation metadata is advisory.")
        for record in top_a:
            lines.append(
                _record_line(
                    record,
                    bilingual=True,
                    placement=_placement_label(record, routed),
                )
            )
        lines.append("")
    else:
        lines.extend(["- No A-level papers in the selected window.", ""])

    section_titles = ["High-Priority Papers This Week", *TOPICAL_SECTION_ORDER]
    section_lookup = {
        "High-Priority Papers This Week": "High-Priority Papers",
        **{section: section for section in TOPICAL_SECTION_ORDER},
    }
    for title in section_titles:
        lines.extend([f"## {title}", ""])
        if title == "High-Priority Papers This Week":
            section_records = routed["primary_new"]
        else:
            section_records = sections.get(section_lookup[title], []) if isinstance(sections, dict) else []
        if not section_records:
            lines.extend(["- No matching records.", ""])
            continue
        for record in section_records:
            lines.append(_record_line(record, placement=_placement_label(record, routed)))
        lines.append("")

    for title, key in [("Idea Bank Candidates", "idea_bank_candidates"), ("Paper Plan Candidates", "paper_plan_candidates")]:
        lines.extend([f"## {title}", ""])
        candidates = payload.get(key, [])
        if not candidates:
            lines.extend(["- No candidates.", ""])
            continue
        for item in candidates:
            lines.append(
                f"- {item.get('title')}｜{item.get('relevance_label')} / {item.get('relevance_score')}｜{item.get('reason')}"
            )
        lines.append("")

    lines.extend(
        [
            "## Coverage Notes",
            "",
            f"- expected_days: {coverage['expected_days']}",
            f"- loaded_days: {coverage['loaded_days']}",
            f"- missing_days: {coverage['missing_days']}",
            f"- total_records: {coverage['total_records']}",
            f"- unique_records: {coverage['unique_records']}",
            f"- label_counts: {coverage['label_counts']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_weekly_outputs(payload: dict[str, Any], json_output_dir: Path, digest_output_dir: Path) -> tuple[Path, Path]:
    json_path = weekly_data_path(str(payload["week_id"]), root=json_output_dir)
    markdown_path = weekly_digest_path(str(payload["week_id"]), root=digest_output_dir)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_payload = _strip_private_weekly(payload)
    json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, markdown_path


def _window_from_args(args: argparse.Namespace) -> tuple[date, date]:
    if args.from_date and args.to_date:
        return _parse_date(args.from_date), _parse_date(args.to_date)
    to_date = _parse_date(args.to_date) if args.to_date else datetime.now().date()
    days = int(args.days or 7)
    return to_date - timedelta(days=days - 1), to_date


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly research synthesis from daily digest JSON files.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--from-date", default=None)
    parser.add_argument("--to-date", default=None)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--json-output-dir", type=Path, default=Path("data"))
    parser.add_argument("--digest-output-dir", type=Path, default=Path("digests"))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from_date, to_date = _window_from_args(args)
    payload = build_weekly_synthesis(args.data_dir, from_date, to_date)
    print(
        "Weekly synthesis {week}: {unique} unique records, missing_days={missing}".format(
            week=payload["week_id"],
            unique=payload["coverage"]["unique_records"],
            missing=len(payload["coverage"]["missing_days"]),
        )
    )
    if args.dry_run:
        print("DRY RUN: no weekly output files were written.")
        print(f"JSON target: {weekly_data_path(str(payload['week_id']), root=args.json_output_dir)}")
        print(f"Markdown target: {weekly_digest_path(str(payload['week_id']), root=args.digest_output_dir)}")
        return 0
    json_path, markdown_path = write_weekly_outputs(payload, args.json_output_dir, args.digest_output_dir)
    print(json_path)
    print(markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
