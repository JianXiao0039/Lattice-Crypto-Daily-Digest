from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError

import lattice_digest.http as http
from lattice_digest.sources.arxiv import ArxivSource
from lattice_digest.sources.base import FetchContext


class _Headers(dict):
    def get(self, key: str, default: str | None = None) -> str | None:
        return super().get(key, default)


def test_source_429_does_not_crash() -> None:
    original_urlopen = http.urlopen

    def fake_urlopen(request: object, timeout: int) -> object:
        raise HTTPError(
            "https://export.arxiv.org/api/query",
            429,
            "Too Many Requests",
            _Headers({"Retry-After": "0"}),
            None,
        )

    with TemporaryDirectory() as tmp:
        context = FetchContext(
            root=Path(tmp),
            since=datetime(2026, 5, 21, tzinfo=timezone.utc),
            dry_run=False,
            max_retries=1,
            per_domain_min_interval_seconds=0,
        )
        source = ArxivSource(
            {
                "name": "arxiv",
                "type": "arxiv",
                "url": "https://export.arxiv.org/api/query",
                "categories": ["cs.CR"],
                "max_results": 50,
            }
        )
        try:
            http.urlopen = fake_urlopen
            records = source.fetch(context)
        finally:
            http.urlopen = original_urlopen

    assert records == []
    assert any("arxiv" in warning and "HTTP 429" in warning for warning in context.warnings)

