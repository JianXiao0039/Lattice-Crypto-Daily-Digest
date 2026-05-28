from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lattice_digest.http import request_json, request_text
from lattice_digest.models import PaperRecord


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
    api_keys: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    source_health: dict[str, SourceHealth] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.cache_dir is None:
            self.cache_dir = self.root / "cache"

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

    def source_health_summary(self) -> list[dict[str, object]]:
        return [
            self.source_health[name].to_dict()
            for name in sorted(self.source_health)
        ]


class SourceAdapter:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.name = config.get("name") or config.get("type") or self.__class__.__name__

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
