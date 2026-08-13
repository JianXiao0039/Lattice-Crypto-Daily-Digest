from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from lattice_digest.dedup import dedup_keys
from lattice_digest.models import PaperRecord


def candidate_id(record: PaperRecord) -> str:
    stable = "|".join(
        [record.source, record.paper_id or record.source_url or "", record.normalized_title or record.title.lower()]
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()[:24]


def record_fingerprint(record: PaperRecord) -> str:
    stable = "|".join(
        [record.doi or "", record.arxiv_id or "", record.eprint_id or "", record.normalized_title or record.title.lower()]
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()[:24]


def _matches_any(record: PaperRecord, candidates: list[PaperRecord]) -> bool:
    record_keys = set(dedup_keys(record))
    return any(record_keys.intersection(dedup_keys(candidate)) for candidate in candidates)


def canonical_identity(record: PaperRecord) -> tuple[str, str]:
    keys = dedup_keys(record)
    key = keys[0] if keys else f"url:{record.source_url}"
    identity_type, _, value = key.partition(":")
    return identity_type.upper(), value


def _terminal_route(
    record: PaperRecord,
    coverage_kept: list[PaperRecord],
    reliable: list[PaperRecord],
    deduped: list[PaperRecord],
    final_records: list[PaperRecord],
) -> tuple[str | None, str | None, str, str]:
    if not record.title or not record.source or not record.source_url:
        return "NORMALIZATION", "missing required title/source/source_url", "dropped", "NORMALIZATION_FAILED"
    if not _matches_any(record, coverage_kept):
        return "FRESHNESS", "outside selected coverage window", "dropped", "COVERAGE_DATE_REJECTED"
    if record.relevance_label == "D" or not _matches_any(record, reliable):
        return "RELEVANCE", record.reason or "D classification", "dropped", "RELEVANCE_REJECTED"
    if not _matches_any(record, deduped):
        return "ROUTE", "deduplicated into another canonical record", "merged", "DEDUP_MERGED"
    if not _matches_any(record, final_records):
        return "SOURCE_ROLE_POLICY", "standalone low-evidence enrichment-only candidate", "dropped", "ROLE_POLICY_REJECTED"
    return None, None, "included", "FINAL_INCLUDED"


def _canonical_candidates(
    collected: list[PaperRecord],
    deduped: list[PaperRecord],
    raw_occurrences: list[dict[str, object]],
    normalized_candidates: list[dict[str, object]],
) -> list[dict[str, object]]:
    occurrence_by_normalized = {
        str(item.get("normalized_candidate_id")): str(item.get("raw_occurrence_id"))
        for item in normalized_candidates
    }
    attempts_by_occurrence = {
        str(item.get("raw_occurrence_id")): str(item.get("query_attempt_id"))
        for item in raw_occurrences
    }
    occurrence_index: dict[str, list[str]] = defaultdict(list)
    for item in normalized_candidates:
        fingerprint = item.get("record_fingerprint")
        if fingerprint:
            occurrence_index[str(fingerprint)].append(str(item.get("normalized_candidate_id")))

    rows: list[dict[str, object]] = []
    for record in deduped:
        identity_type, identity = canonical_identity(record)
        matching: list[PaperRecord] = []
        record_keys = set(dedup_keys(record))
        for raw in collected:
            if record_keys.intersection(dedup_keys(raw)):
                matching.append(raw)
        normalized_ids: list[str] = []
        occurrence_ids: list[str] = []
        attempt_ids: list[str] = []
        for raw in matching:
            fingerprint = record_fingerprint(raw)
            for normalized_id in occurrence_index.get(fingerprint, []):
                if normalized_id not in normalized_ids:
                    normalized_ids.append(normalized_id)
                occurrence_id = occurrence_by_normalized.get(normalized_id)
                if occurrence_id and occurrence_id not in occurrence_ids:
                    occurrence_ids.append(occurrence_id)
                attempt_id = attempts_by_occurrence.get(str(occurrence_id))
                if attempt_id and attempt_id not in attempt_ids:
                    attempt_ids.append(attempt_id)
        rows.append(
            {
                "canonical_candidate_id": "canonical-" + hashlib.sha256(f"{identity_type}:{identity}".encode("utf-8")).hexdigest()[:24],
                "record_fingerprint": record_fingerprint(record),
                "dedup_identity_type": identity_type,
                "dedup_identity": identity,
                "merge_target": record.paper_id or record.source_url,
                "source_families": sorted({name.strip() for name in record.source.split(",") if name.strip()}),
                "query_attempt_ids": attempt_ids,
                "raw_occurrence_ids": occurrence_ids,
                "normalized_candidate_ids": normalized_ids,
                "source_identifiers": sorted(
                    {value for item in matching for value in (item.doi, item.arxiv_id, item.eprint_id, item.paper_id) if value}
                ),
                "seen_dates": sorted({value for item in matching for value in (item.publication_date, item.update_date) if value}),
                "strongest_evidence_provenance": max(matching or [record], key=lambda item: len(item.abstract or "")).source,
                "relevance_label": record.relevance_label,
                "relevance_score": record.relevance_score,
                "security_impact_severity": record.security_impact_severity,
                "evidence_confidence": record.evidence_confidence,
            }
        )
    return rows


def _runtime_metrics(
    query_attempts: list[dict[str, object]],
    raw_occurrences: list[dict[str, object]],
    normalized_candidates: list[dict[str, object]],
    canonical_candidates: list[dict[str, object]],
    candidate_rows: list[dict[str, object]],
    source_health: list[dict[str, object]],
    canonical_final_ids: set[str],
) -> dict[str, object]:
    attempts_by_source = Counter(str(item.get("source_family")) for item in query_attempts)
    attempts_by_family = Counter(str(item.get("query_family")) for item in query_attempts)
    raw_by_source = Counter(str(item.get("source_family")) for item in raw_occurrences)
    raw_by_query: Counter[str] = Counter()
    attempt_family = {str(item.get("attempt_id")): str(item.get("query_family")) for item in query_attempts}
    for occurrence in raw_occurrences:
        raw_by_query[attempt_family.get(str(occurrence.get("query_attempt_id")), "unknown")] += 1
    normalized_by_source = Counter(str(item.get("source_family")) for item in normalized_candidates if item.get("normalization_status") == "NORMALIZED")
    parser_losses = Counter(
        str(item.get("source_family"))
        for item in raw_occurrences
        if item.get("parser_result") == "RAW_PARSE_FAILED" or not item.get("normalization_eligible", True)
    )
    abstracts_by_source: dict[str, dict[str, int | float]] = {}
    for source, count in raw_by_source.items():
        present = sum(1 for item in raw_occurrences if item.get("source_family") == source and item.get("abstract_present"))
        abstracts_by_source[source] = {"present": present, "total": count, "rate": present / count if count else 0.0}
    drop_counts = Counter(str(item.get("drop_stage") or "NONE") for item in candidate_rows)
    final_routes = Counter(str(item.get("final_route")) for item in candidate_rows)
    raw_total = len(raw_occurrences)
    unique_total = len(canonical_candidates)
    health_by_source = {str(item.get("source")): str(item.get("health_status") or item.get("status")) for item in source_health}
    relevant_by_source = Counter(
        str(item.get("source_family")) for item in candidate_rows if not str(item.get("post_relevance_status", "D:")).startswith("D:")
    )
    final_by_source = Counter(
        str(item.get("source_family")) for item in candidate_rows if item.get("lifecycle_terminal_state") == "FINAL_INCLUDED"
    )
    attempts = {str(item.get("attempt_id")): item for item in query_attempts}
    relevant_by_query: Counter[str] = Counter()
    final_by_query: Counter[str] = Counter()
    for canonical in canonical_candidates:
        family_ids = {
            str(attempts[attempt_id].get("query_family"))
            for attempt_id in canonical.get("query_attempt_ids", [])
            if attempt_id in attempts
        }
        if canonical.get("relevance_label") != "D":
            relevant_by_query.update(family_ids)
        if canonical.get("canonical_candidate_id") in canonical_final_ids:
            final_by_query.update(family_ids)
    health_adjusted: dict[str, object] = {}
    for source, raw_count in raw_by_source.items():
        status = health_by_source.get(source, "unknown")
        if status == "green":
            health_adjusted[source] = {
                "status": "MEASURED",
                "final_per_raw_occurrence": final_by_source.get(source, 0) / raw_count if raw_count else 0.0,
            }
        else:
            health_adjusted[source] = {"status": "UNKNOWN_COVERAGE", "source_health": status}
    return {
        "attempts_by_source": dict(sorted(attempts_by_source.items())),
        "attempts_by_query_family": dict(sorted(attempts_by_family.items())),
        "raw_occurrences_by_source": dict(sorted(raw_by_source.items())),
        "raw_occurrences_by_query_family": dict(sorted(raw_by_query.items())),
        "normalized_candidates_by_source": dict(sorted(normalized_by_source.items())),
        "parser_losses_by_source": dict(sorted(parser_losses.items())),
        "abstract_availability_by_source": abstracts_by_source,
        "unique_canonical_candidates": unique_total,
        "dedup_ratio": (raw_total - unique_total) / raw_total if raw_total else 0.0,
        "drop_stage_counts": dict(sorted(drop_counts.items())),
        "final_route_counts": dict(sorted(final_routes.items())),
        "relevant_yield_by_source": dict(sorted(relevant_by_source.items())),
        "relevant_yield_by_query_family": dict(sorted(relevant_by_query.items())),
        "final_yield_by_source": dict(sorted(final_by_source.items())),
        "final_yield_by_query_family": dict(sorted(final_by_query.items())),
        "source_health_state": health_by_source,
        "source_health_adjusted_yield": health_adjusted,
    }


def _occurrence_lifecycles(
    query_attempts: list[dict[str, object]],
    raw_occurrences: list[dict[str, object]],
    normalized_candidates: list[dict[str, object]],
    canonical_candidates: list[dict[str, object]],
    candidate_rows: list[dict[str, object]],
    route_events: list[dict[str, object]],
) -> list[dict[str, object]]:
    attempts = {str(item.get("attempt_id")): item for item in query_attempts}
    normalized_by_occurrence = {
        str(item.get("raw_occurrence_id")): item for item in normalized_candidates
    }
    canonical_by_normalized = {
        str(normalized_id): canonical
        for canonical in canonical_candidates
        for normalized_id in canonical.get("normalized_candidate_ids", [])
    }
    rows_by_fingerprint = {str(item.get("record_fingerprint")): item for item in candidate_rows}
    terminal_by_entity = {
        (str(item.get("entity_type")), str(item.get("entity_id"))): item
        for item in route_events
        if item.get("terminal")
    }
    lifecycles: list[dict[str, object]] = []
    for occurrence in raw_occurrences:
        occurrence_id = str(occurrence.get("raw_occurrence_id"))
        normalized = normalized_by_occurrence.get(occurrence_id)
        terminal = terminal_by_entity.get(("raw_occurrence", occurrence_id))
        canonical = canonical_by_normalized.get(str(normalized.get("normalized_candidate_id"))) if normalized else None
        candidate = rows_by_fingerprint.get(str(normalized.get("record_fingerprint"))) if normalized else None
        if terminal:
            terminal_state = str(terminal.get("decision"))
        elif candidate:
            terminal_state = str(candidate.get("lifecycle_terminal_state"))
        elif normalized:
            terminal_state = "ADAPTER_FILTERED_BEFORE_CENTRAL_PIPELINE"
        else:
            terminal_state = "UNTRACED"
        attempt = attempts.get(str(occurrence.get("query_attempt_id")), {})
        lifecycles.append(
            {
                "raw_occurrence_id": occurrence_id,
                "query_attempt_id": occurrence.get("query_attempt_id"),
                "query_id": attempt.get("query_id", "NOT_OBSERVABLE"),
                "source_family": occurrence.get("source_family"),
                "source_roles": occurrence.get("source_roles", []),
                "parser_result": occurrence.get("parser_result"),
                "normalization_status": normalized.get("normalization_status") if normalized else "NOT_NORMALIZED",
                "evidence_availability": normalized.get("evidence_availability") if normalized else "NOT_OBSERVABLE",
                "relevance": candidate.get("post_relevance_status") if candidate else "NOT_OBSERVABLE",
                "critical_signal": candidate.get("security_impact_severity") if candidate else "NOT_OBSERVABLE",
                "coverage_date_gate": candidate.get("drop_stage") if candidate else "NOT_OBSERVABLE",
                "canonical_candidate_id": canonical.get("canonical_candidate_id") if canonical else None,
                "recommendation_action": "NOT_OBSERVABLE_IN_RETRIEVAL_LEDGER",
                "terminal_state": terminal_state,
            }
        )
    return lifecycles


def build_candidate_ledger(
    collected: list[PaperRecord],
    ranked: list[PaperRecord],
    coverage_kept: list[PaperRecord],
    reliable: list[PaperRecord],
    deduped: list[PaperRecord],
    final_records: list[PaperRecord],
    source_health: list[dict[str, object]],
    target_date: date,
    query_attempts: list[dict[str, object]] | None = None,
    *,
    run_id: str = "legacy-run-not-recorded",
    run_started_at: str = "unknown",
    raw_occurrences: list[dict[str, object]] | None = None,
    normalized_candidates: list[dict[str, object]] | None = None,
    route_events: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    query_attempts = list(query_attempts or [])
    raw_occurrences = list(raw_occurrences or [])
    normalized_candidates = list(normalized_candidates or [])
    route_events = list(route_events or [])
    ranked_by_id = {candidate_id(record): record for record in ranked}
    health_by_source = {
        str(item.get("source")): str(item.get("health_status") or item.get("status") or "unknown")
        for item in source_health
    }
    rows: list[dict[str, object]] = []
    for raw in collected:
        cid = candidate_id(raw)
        record = ranked_by_id.get(cid, raw)
        drop_stage, drop_reason, final_route, lifecycle_terminal_state = _terminal_route(
            record, coverage_kept, reliable, deduped, final_records
        )
        rows.append(
            {
                "candidate_id": cid,
                "record_fingerprint": record_fingerprint(record),
                "source_family": record.source,
                "query_family": record.source_query_family or "source_native_feed_or_legacy_query",
                "query_text": record.source_query_text or "not_recorded",
                "retrieval_timestamp": record.retrieval_timestamp or "unknown",
                "source_health": health_by_source.get(record.source, record.source_health or "unknown"),
                "raw_title": raw.title,
                "normalized_title": record.normalized_title,
                "identifier": record.paper_id or record.arxiv_id or record.eprint_id or record.doi or record.source_url,
                "publication_date": record.publication_date,
                "update_date": record.update_date,
                "abstract_present": bool(record.abstract),
                "normalization_status": "normalized" if record.normalized_title else "incomplete",
                "pre_relevance_status": "candidate",
                "post_relevance_status": f"{record.relevance_label}:{record.relevance_score}",
                "source_evidence_terms": list(record.source_evidence_terms),
                "inferred_topic_tags": list(record.inferred_topic_tags),
                "security_impact_severity": record.security_impact_severity,
                "evidence_confidence": record.evidence_confidence,
                "drop_stage": drop_stage,
                "drop_reason": drop_reason,
                "final_route": final_route,
                "lifecycle_terminal_state": lifecycle_terminal_state,
            }
        )
    canonical_candidates = _canonical_candidates(collected, deduped, raw_occurrences, normalized_candidates)
    final_canonical_ids = {
        str(item.get("canonical_candidate_id"))
        for item in canonical_candidates
        if any(_matches_any(record, final_records) for record in deduped if record_fingerprint(record) == item.get("record_fingerprint"))
    }
    derived_route_events = list(route_events)
    for row in rows:
        derived_route_events.append(
            {
                "event_id": f"derived-route-{len(derived_route_events) + 1:07d}",
                "run_id": run_id,
                "entity_type": "candidate",
                "entity_id": row["candidate_id"],
                "stage": row["drop_stage"] or "OUTPUT",
                "decision": row["lifecycle_terminal_state"],
                "reason": row["drop_reason"] or "included in final output",
                "terminal": True,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    occurrence_lifecycles = _occurrence_lifecycles(
        query_attempts, raw_occurrences, normalized_candidates, canonical_candidates, rows, derived_route_events
    )
    traced = sum(1 for item in occurrence_lifecycles if item.get("terminal_state") != "UNTRACED")
    traceability = traced / len(raw_occurrences) if raw_occurrences else 1.0
    return {
        "schema_version": "2.0",
        "artifact_role": "scratch_diagnostic_non_authoritative",
        "retention_expectation": "30_days_unless_incident_evidence_is_frozen_separately",
        "privacy_contract": "no_credentials_tokens_auth_headers_or_secrets",
        "run_id": run_id,
        "run_started_at": run_started_at,
        "target_date": target_date.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "diagnostic_chain": ["SOURCE", "QUERY", "NORMALIZATION", "RELEVANCE", "FRESHNESS", "ROUTE"],
        "lifecycle_chain_v2": [
            "SOURCE", "QUERY_PORTFOLIO", "RAW_OCCURRENCE", "NORMALIZATION", "EVIDENCE_AVAILABILITY",
            "RELEVANCE", "CRITICAL_SIGNAL", "COVERAGE_DATE_GATE", "RELIABILITY", "DEDUP",
            "RECOMMENDATION", "DAILY_FRESHNESS_ROUTE", "OUTPUT",
        ],
        "source_health": source_health,
        "query_attempts": query_attempts,
        "raw_occurrences": raw_occurrences,
        "normalized_candidates": normalized_candidates,
        "canonical_candidates": canonical_candidates,
        "route_events": derived_route_events,
        "occurrence_lifecycles": occurrence_lifecycles,
        "candidates": rows,
        "traceability": {"raw_occurrences": len(raw_occurrences), "traceable": traced, "percentage": traceability * 100},
        "runtime_metrics": _runtime_metrics(
            query_attempts, raw_occurrences, normalized_candidates, canonical_candidates, rows, source_health,
            final_canonical_ids,
        ),
    }


def write_candidate_ledger(payload: dict[str, object], output_root: Path, target_date: date) -> Path:
    output_dir = output_root / "audits" / "worktree"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"candidate-retrieval-ledger-{target_date.isoformat()}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
