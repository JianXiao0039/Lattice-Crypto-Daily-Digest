from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.http import request_text


class _FakeResponse:
    status = 200

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return b"cached-body"


def test_http_cache_reuses_same_url_within_12_hours() -> None:
    calls = {"count": 0}

    def fake_open(request: object, timeout: int) -> _FakeResponse:
        calls["count"] += 1
        return _FakeResponse()

    now = datetime(2026, 5, 22, 8, 0, tzinfo=timezone.utc)
    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp)
        first = request_text(
            "https://example.test/feed?q=lwe",
            source="example",
            user_agent="test-agent",
            cache_dir=cache_dir,
            min_interval_seconds=0,
            warnings=[],
            now_func=lambda: now,
            open_func=fake_open,
        )
        second = request_text(
            "https://example.test/feed?q=lwe",
            source="example",
            user_agent="test-agent",
            cache_dir=cache_dir,
            min_interval_seconds=0,
            warnings=[],
            now_func=lambda: now,
            open_func=fake_open,
        )

    assert first.ok is True
    assert second.ok is True
    assert second.from_cache is True
    assert second.text == "cached-body"
    assert calls["count"] == 1

