from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lattice_digest.http import request_json, request_text
from lattice_digest.models import PaperRecord


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

    def __post_init__(self) -> None:
        if self.cache_dir is None:
            self.cache_dir = self.root / "cache"


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
        warnings=context.warnings,
    )
    return response.text if response.ok else None


def fetch_json(
    context: FetchContext,
    url: str,
    headers: dict[str, str] | None = None,
    source_name: str = "http",
) -> dict[str, Any] | None:
    assert context.cache_dir is not None
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
        warnings=context.warnings,
    )
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
    try:
        return datetime.fromisoformat(normalized).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def within_since(publication_date: str | None, update_date: str | None, since: datetime) -> bool:
    parsed = parse_date_for_filter(update_date) or parse_date_for_filter(publication_date)
    if parsed is None:
        return True
    return parsed >= since
