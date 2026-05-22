from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError

from lattice_digest.http import request_text


class _FakeResponse:
    status = 200

    def __init__(self, body: str) -> None:
        self.body = body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body.encode("utf-8")


class _Headers(dict):
    def get(self, key: str, default: str | None = None) -> str | None:
        return super().get(key, default)


def test_http_backoff_retries_429_and_uses_retry_after() -> None:
    calls = {"count": 0}
    sleeps: list[float] = []

    def fake_open(request: object, timeout: int) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] == 1:
            raise HTTPError(
                "https://example.test/feed",
                429,
                "Too Many Requests",
                _Headers({"Retry-After": "2"}),
                None,
            )
        return _FakeResponse("ok")

    with TemporaryDirectory() as tmp:
        response = request_text(
            "https://example.test/feed",
            source="example",
            user_agent="test-agent",
            timeout_seconds=5,
            cache_dir=Path(tmp),
            min_interval_seconds=0,
            max_retries=2,
            warnings=[],
            sleep_func=sleeps.append,
            now_func=lambda: datetime(2026, 5, 22, tzinfo=timezone.utc),
            open_func=fake_open,
        )

    assert response.ok is True
    assert response.text == "ok"
    assert calls["count"] == 2
    assert 2 in sleeps

