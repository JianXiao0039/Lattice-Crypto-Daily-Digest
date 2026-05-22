from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from lattice_digest.models import PaperRecord


@dataclass
class FetchContext:
    root: Path
    since: datetime
    dry_run: bool
    timeout_seconds: int = 20
    user_agent: str = "lattice-crypto-daily-digest/0.1"
    cache_dir: Path | None = None
    api_keys: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.cache_dir is None:
            self.cache_dir = self.root / ".cache"


class SourceAdapter:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.name = config.get("name") or config.get("type") or self.__class__.__name__

    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        raise NotImplementedError


def fetch_text(context: FetchContext, url: str, headers: dict[str, str] | None = None) -> str:
    request_headers = {"User-Agent": context.user_agent, **(headers or {})}
    request = Request(url, headers=request_headers)
    try:
        with urlopen(request, timeout=context.timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"request failed for {url}: {exc}") from exc


def fetch_json(context: FetchContext, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    return json.loads(fetch_text(context, url, headers=headers))


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

