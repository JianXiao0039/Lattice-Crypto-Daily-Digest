from __future__ import annotations

from io import BytesIO

from scripts.probe_source_health import build_probe_report


class FakeResponse:
    def __init__(self, payload: bytes, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return BytesIO(self.payload).read()


def test_probe_report_is_manual_low_load_and_sanitized() -> None:
    targets = (
        {
            "source": "semantic_scholar",
            "endpoint_label": "Semantic Scholar paper search",
            "url": "https://api.semanticscholar.org/graph/v1/paper/search?query=ML-KEM&limit=1&fields=title",
        },
    )

    report = build_probe_report(
        low_load=True,
        targets=targets,
        env={"SEMANTIC_SCHOLAR_API_KEY": "secret-value"},
        opener=lambda request, timeout: FakeResponse(b'{"data": []}'),
    )

    assert report["mode"] == "low_load"
    assert report["anti_abuse_policy"]["manual_only"] is True
    assert report["anti_abuse_policy"]["no_proxy_rotation"] is True
    assert report["semantic_scholar_key"]["present"] is True
    assert "secret-value" not in str(report)
    assert report["probes"][0]["status"] == "empty_response"
