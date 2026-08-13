from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any
from uuid import uuid4

from lattice_digest.http import request_json, request_text
from lattice_digest.models import PaperRecord
from lattice_digest.source_queries import QueryRequest
from lattice_digest.source_roles import primary_source_role, serialized_source_roles


@dataclass
class SourceHealth:
    name: str
    raw_candidates: int = 0
    normalized_candidates: int = 0
    date_filtered_candidates: int = 0
    deduped_candidates: int = 0
    relevance_filtered_candidates: int = 0
    scoring_threshold_candidates: int = 0
    final_records: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    query_groups_total: int = 0
    query_groups_success: int = 0
    query_groups_failed: int = 0
    api_key_used: bool | None = None
    latest_feed_status: str | None = None
    latest_feed_reachable: bool | None = None
    latest_feed_parsed: bool | None = None
    latest_feed_records: int = 0
    latest_feed_missing_expected: list[str] = field(default_factory=list)
    latest_feed_skipped_by_guard: bool = False

    def _problem_text(self) -> str:
        values = [*self.errors, *self.warnings]
        return str(values[0]) if values else ""

    def error_type(self) -> str | None:
        message = self._problem_text().lower()
        if not message:
            return None
        if "plan upgrade" in message or "premium" in message:
            return "plan_upgrade_required"
        if "http 429" in message or "too many requests" in message or "rate limit" in message:
            return "rate_limit"
        if "timeouterror" in message or "timeout" in message:
            return "timeout"
        if "sslerror" in message or "ssl" in message:
            return "ssl_error"
        if "http 400" in message or "bad request" in message:
            return "invalid_request"
        if "http 500" in message or "internal server error" in message:
            return "server_error"
        if self.errors:
            return "source_error"
        return "warning"

    def retryable(self) -> bool:
        error_type = self.error_type()
        if error_type in {None, "plan_upgrade_required", "invalid_request"}:
            return False
        return error_type in {"rate_limit", "timeout", "ssl_error", "server_error", "source_error", "warning"}

    def health_status(self) -> str:
        if self.errors:
            return "red"
        if self.query_groups_total and self.query_groups_failed >= self.query_groups_total and not self.query_groups_success:
            return "red"
        if self.warnings:
            if self.raw_candidates or self.date_filtered_candidates or self.final_records or self.query_groups_success:
                return "yellow"
            return "red"
        if self.final_records:
            return "green"
        return "yellow"

    def error_message(self) -> str | None:
        message = self._problem_text()
        if not message:
            return None
        return " ".join(message.split())[:240]

    def to_dict(self) -> dict[str, object]:
        health_status = self.health_status()
        return {
            "source": self.name,
            "health_status": health_status,
            "status": health_status,
            "raw_candidates": self.raw_candidates,
            "raw_count": self.raw_candidates,
            "normalized_candidates": self.normalized_candidates,
            "normalized_count": self.normalized_candidates,
            "date_filtered_candidates": self.date_filtered_candidates,
            "date_filtered_count": self.date_filtered_candidates,
            "deduped_candidates": self.deduped_candidates,
            "relevance_filtered_candidates": self.relevance_filtered_candidates,
            "scoring_threshold_candidates": self.scoring_threshold_candidates,
            "final_records": self.final_records,
            "final_count": self.final_records,
            "error_type": self.error_type(),
            "error_message": self.error_message(),
            "retryable": self.retryable(),
            "query_groups_total": self.query_groups_total,
            "query_groups_success": self.query_groups_success,
            "query_groups_failed": self.query_groups_failed,
            "api_key_used": self.api_key_used,
            "latest_feed_status": self.latest_feed_status,
            "latest_feed_reachable": self.latest_feed_reachable,
            "latest_feed_parsed": self.latest_feed_parsed,
            "latest_feed_records": self.latest_feed_records,
            "latest_feed_missing_expected": list(self.latest_feed_missing_expected),
            "latest_feed_skipped_by_guard": self.latest_feed_skipped_by_guard,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass
class FetchContext:
    root: Path
    since: datetime
    dry_run: bool
    timeout_seconds: int = 20
    user_agent: str = "lattice-crypto-daily-digest/0.1"
    cache_dir: Path | None = None
    http_cache_ttl_seconds: int = 12 * 60 * 60
    per_domain_min_interval_seconds: float = 1.0
    max_retries: int = 2
    retry_failed_sources: bool = False
    include_latest_sources: bool = False
    api_keys: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    source_health: dict[str, SourceHealth] = field(default_factory=dict)
    query_attempts: list[dict[str, object]] = field(default_factory=list)
    raw_occurrences: list[dict[str, object]] = field(default_factory=list)
    normalized_candidates: list[dict[str, object]] = field(default_factory=list)
    route_events: list[dict[str, object]] = field(default_factory=list)
    source_role_map: dict[str, list[str]] = field(default_factory=dict)
    run_id: str = ""
    run_started_at: str = ""

    def __post_init__(self) -> None:
        if self.cache_dir is None:
            self.cache_dir = self.root / "cache"
        if not self.run_started_at:
            self.run_started_at = datetime.now(timezone.utc).isoformat()
        if not self.run_id:
            stamp = self.run_started_at.replace(":", "").replace("-", "").replace("+", "_")
            self.run_id = f"retrieval-{stamp}-{uuid4().hex[:8]}"

    def register_source(self, config: dict[str, Any]) -> None:
        name = str(config.get("name") or config.get("type") or "unknown")
        self.source_role_map[name] = serialized_source_roles(config)

    def source_roles(self, source_name: str) -> list[str]:
        return list(self.source_role_map.get(source_name, ["LOW_CONFIDENCE_FALLBACK"]))

    def health(self, source_name: str) -> SourceHealth:
        if source_name not in self.source_health:
            self.source_health[source_name] = SourceHealth(name=source_name)
        return self.source_health[source_name]

    def add_warning(self, message: str, source_name: str | None = None) -> None:
        self.warnings.append(message)
        if source_name:
            self.health(source_name).warnings.append(message)

    def add_error(self, message: str, source_name: str | None = None) -> None:
        if source_name:
            self.health(source_name).errors.append(message)
        self.add_warning(message, source_name)

    def set_source_counts(
        self,
        source_name: str,
        *,
        raw: int | None = None,
        normalized: int | None = None,
        date_filtered: int | None = None,
    ) -> None:
        health = self.health(source_name)
        if raw is not None:
            health.raw_candidates = raw
        if normalized is not None:
            health.normalized_candidates = normalized
        if date_filtered is not None:
            health.date_filtered_candidates = date_filtered

    def set_latest_feed_state(
        self,
        source_name: str,
        *,
        status: str,
        reachable: bool | None = None,
        parsed: bool | None = None,
        records: int | None = None,
        missing_expected: list[str] | None = None,
        skipped_by_guard: bool | None = None,
    ) -> None:
        health = self.health(source_name)
        health.latest_feed_status = status
        if reachable is not None:
            health.latest_feed_reachable = reachable
        if parsed is not None:
            health.latest_feed_parsed = parsed
        if records is not None:
            health.latest_feed_records = records
        if missing_expected is not None:
            health.latest_feed_missing_expected = list(missing_expected)
        if skipped_by_guard is not None:
            health.latest_feed_skipped_by_guard = skipped_by_guard

    def source_health_summary(self) -> list[dict[str, object]]:
        return [
            self.source_health[name].to_dict()
            for name in sorted(self.source_health)
        ]

    def begin_query_attempt(self, source_name: str, request: QueryRequest) -> str:
        attempt_id = f"attempt-{len(self.query_attempts) + 1:06d}"
        self.query_attempts.append(
            {
                "attempt_id": attempt_id,
                "run_id": self.run_id,
                "run_date": self.run_started_at[:10],
                "source_family": source_name,
                "source_roles": self.source_roles(source_name),
                "source_role": self.source_roles(source_name)[0],
                "query_id": request.query_id,
                "query_family": request.family_id,
                "query_expression_hash": request.expression_hash,
                "query_expression_safe": request.query_text,
                "intent": request.intent,
                "native_syntax": request.native_syntax,
                "status": "started",
                "source_health_state": self.health(source_name).health_status(),
                "raw_candidates": None,
                "http_error_category": None,
                "coverage_semantics": "UNKNOWN_COVERAGE",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None,
            }
        )
        return attempt_id

    def finish_query_attempt(
        self,
        attempt_id: str,
        *,
        status: str,
        raw_candidates: int | None = 0,
        error_category: str | None = None,
    ) -> None:
        attempt = next(item for item in self.query_attempts if item["attempt_id"] == attempt_id)
        attempt.update(
            {
                "status": status,
                "raw_candidates": raw_candidates,
                "http_error_category": error_category,
                "coverage_semantics": "OBSERVED_RESULTS" if status == "success" else "UNKNOWN_COVERAGE",
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        if status == "success" and raw_candidates == 0:
            self.record_route_event("query_attempt", attempt_id, "QUERY", "QUERY_ZERO_HIT", "source returned zero items")
        elif status in {"failed", "rate_limited"}:
            decision = "RATE_LIMITED" if error_category == "rate_limit" else "SOURCE_FAILED"
            self.record_route_event("query_attempt", attempt_id, "SOURCE", decision, error_category or "source request failed")

    def record_query_attempt(
        self,
        source_name: str,
        query_family: str,
        query_text: str,
        *,
        status: str,
        raw_candidates: int = 0,
    ) -> None:
        request = QueryRequest(query_family, query_text, source_family=source_name)
        attempt_id = self.begin_query_attempt(source_name, request)
        self.finish_query_attempt(attempt_id, status=status, raw_candidates=raw_candidates)

    def record_raw_occurrence(
        self,
        source_name: str,
        attempt_id: str,
        *,
        raw_title: str,
        source_identifier: str | None = None,
        source_url: str | None = None,
        publication_date: str | None = None,
        update_date: str | None = None,
        abstract_present: bool = False,
        parser_result: str = "PENDING",
        parser_failure_reason: str | None = None,
        normalization_eligible: bool = True,
    ) -> str:
        occurrence_id = f"occurrence-{len(self.raw_occurrences) + 1:07d}"
        self.raw_occurrences.append(
            {
                "raw_occurrence_id": occurrence_id,
                "run_id": self.run_id,
                "source_family": source_name,
                "source_roles": self.source_roles(source_name),
                "query_attempt_id": attempt_id,
                "raw_title": str(raw_title or ""),
                "source_identifier": source_identifier,
                "source_url": source_url,
                "raw_publication_date": publication_date,
                "raw_update_date": update_date,
                "abstract_present": bool(abstract_present),
                "parser_result": parser_result,
                "parser_failure_reason": parser_failure_reason,
                "normalization_eligible": normalization_eligible,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        if parser_result == "RAW_PARSE_FAILED" or not normalization_eligible:
            self.record_route_event(
                "raw_occurrence",
                occurrence_id,
                "NORMALIZATION",
                "RAW_PARSE_FAILED",
                parser_failure_reason or "not normalization eligible",
                terminal=True,
            )
        return occurrence_id

    def record_normalized_candidate(
        self,
        occurrence_id: str,
        record: PaperRecord | None,
        *,
        status: str = "NORMALIZED",
        reason: str | None = None,
    ) -> str:
        normalized_id = f"normalized-{len(self.normalized_candidates) + 1:07d}"
        occurrence = next(item for item in self.raw_occurrences if item["raw_occurrence_id"] == occurrence_id)
        fingerprint = None
        if record is not None:
            stable = "|".join(
                [record.doi or "", record.arxiv_id or "", record.eprint_id or "", record.normalized_title or record.title.lower()]
            )
            fingerprint = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:24]
        self.normalized_candidates.append(
            {
                "normalized_candidate_id": normalized_id,
                "raw_occurrence_id": occurrence_id,
                "query_attempt_id": occurrence["query_attempt_id"],
                "source_family": occurrence["source_family"],
                "normalization_status": status,
                "normalization_reason": reason,
                "record_fingerprint": fingerprint,
                "normalized_title": record.normalized_title if record else None,
                "identifiers": {
                    "doi": record.doi if record else None,
                    "arxiv_id": record.arxiv_id if record else None,
                    "eprint_id": record.eprint_id if record else None,
                    "paper_id": record.paper_id if record else None,
                },
                "parsed_date_basis": (
                    "update_date" if record and record.update_date else "publication_date" if record and record.publication_date else "NOT_OBSERVABLE"
                ),
                "publication_date": record.publication_date if record else None,
                "update_date": record.update_date if record else None,
                "abstract_present": bool(record and record.abstract),
                "evidence_availability": "TITLE_AND_ABSTRACT" if record and record.abstract else "TITLE_ONLY",
                "source_evidence_terms": list(record.source_evidence_terms) if record else [],
                "inferred_topic_tags": list(record.inferred_topic_tags) if record else [],
                "relevance_inputs": ["title", "abstract" if record and record.abstract else "abstract_missing"],
            }
        )
        if status != "NORMALIZED":
            self.record_route_event(
                "normalized_candidate",
                normalized_id,
                "NORMALIZATION",
                "NORMALIZATION_FAILED",
                reason or "unknown",
                terminal=True,
            )
        elif record is not None and not record.abstract:
            self.record_route_event("normalized_candidate", normalized_id, "EVIDENCE", "NO_ABSTRACT", "source supplied no abstract")
        return normalized_id

    def record_route_event(
        self,
        entity_type: str,
        entity_id: str,
        stage: str,
        decision: str,
        reason: str,
        *,
        terminal: bool = False,
    ) -> None:
        self.route_events.append(
            {
                "event_id": f"route-{len(self.route_events) + 1:07d}",
                "run_id": self.run_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "stage": stage,
                "decision": decision,
                "reason": reason,
                "terminal": terminal,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        )


class SourceAdapter:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.name = config.get("name") or config.get("type") or self.__class__.__name__
        self.source_roles = serialized_source_roles(config)
        self.primary_source_role = primary_source_role(config)

    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        raise NotImplementedError


def fetch_text(
    context: FetchContext,
    url: str,
    headers: dict[str, str] | None = None,
    source_name: str = "http",
) -> str | None:
    assert context.cache_dir is not None
    source_warnings: list[str] = []
    response = request_text(
        url,
        source=source_name,
        user_agent=context.user_agent,
        timeout_seconds=context.timeout_seconds,
        headers=headers,
        cache_dir=context.cache_dir / "http",
        cache_ttl_seconds=context.http_cache_ttl_seconds,
        min_interval_seconds=context.per_domain_min_interval_seconds,
        max_retries=context.max_retries,
        warnings=source_warnings,
    )
    for warning in source_warnings:
        context.add_warning(warning, source_name)
    return response.text if response.ok else None


def fetch_json(
    context: FetchContext,
    url: str,
    headers: dict[str, str] | None = None,
    source_name: str = "http",
) -> dict[str, Any] | None:
    assert context.cache_dir is not None
    source_warnings: list[str] = []
    data, _ = request_json(
        url,
        source=source_name,
        user_agent=context.user_agent,
        timeout_seconds=context.timeout_seconds,
        headers=headers,
        cache_dir=context.cache_dir / "http",
        cache_ttl_seconds=context.http_cache_ttl_seconds,
        min_interval_seconds=context.per_domain_min_interval_seconds,
        max_retries=context.max_retries,
        warnings=source_warnings,
    )
    for warning in source_warnings:
        context.add_warning(warning, source_name)
    return data


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        from email.utils import parsedate_to_datetime

        parsed = parsedate_to_datetime(raw)
        if parsed:
            return parsed.date().isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
        return raw[:10]
    return raw


def parse_date_for_filter(value: str | None) -> datetime | None:
    normalized = normalize_date(value)
    if not normalized:
        return None
    if len(normalized) == 4 and normalized.isdigit():
        normalized = f"{normalized}-01-01"
    elif len(normalized) == 7 and normalized[4] == "-":
        normalized = f"{normalized}-01"
    try:
        return datetime.fromisoformat(normalized).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def within_since(publication_date: str | None, update_date: str | None, since: datetime) -> bool:
    parsed = parse_date_for_filter(update_date) or parse_date_for_filter(publication_date)
    if parsed is None:
        return False
    return parsed >= since
