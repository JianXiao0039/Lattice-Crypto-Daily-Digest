from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError

from lattice_digest.http import request_text
from lattice_digest.models import make_paper_record
from lattice_digest.run import _collect_records
from lattice_digest.source_queries import QueryRequest
from lattice_digest.sources.base import FetchContext


class _Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return b"ok"


class _Clock:
    def __init__(self, value: float = 100.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


def _context(tmp_path: Path, clock: _Clock | None = None, **overrides) -> FetchContext:
    values = {
        "root": tmp_path,
        "since": datetime(2026, 8, 14, tzinfo=timezone.utc),
        "dry_run": False,
        "per_source_time_budget_seconds": 10,
        "global_time_budget_seconds": 100,
        "source_circuit_breaker_failures": 2,
    }
    values.update(overrides)
    if clock is not None:
        values["monotonic_func"] = clock
    return FetchContext(**values)


def test_normal_request_completes_without_sleep(tmp_path: Path) -> None:
    sleeps: list[float] = []
    response = request_text(
        "https://example.test/ok",
        user_agent="test",
        cache_dir=tmp_path,
        min_interval_seconds=0,
        sleep_func=sleeps.append,
        open_func=lambda request, timeout: _Response(),
    )
    assert response.ok is True
    assert sleeps == []


def test_short_retry_after_is_respected_and_bounded(tmp_path: Path) -> None:
    calls = 0
    sleeps: list[float] = []

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise HTTPError(request.full_url, 429, "rate limit", {"Retry-After": "2"}, None)
        return _Response()

    response = request_text(
        "https://example.test/short",
        user_agent="test",
        cache_dir=tmp_path,
        min_interval_seconds=0,
        max_retries=1,
        max_retry_after_seconds=5,
        sleep_func=sleeps.append,
        open_func=opener,
    )
    assert response.ok and sleeps == [2.0]


def test_huge_retry_after_never_sleeps_past_configured_cap(tmp_path: Path) -> None:
    calls = 0
    sleeps: list[float] = []

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise HTTPError(request.full_url, 429, "rate limit", {"Retry-After": "3600"}, None)
        return _Response()

    response = request_text(
        "https://example.test/huge",
        user_agent="test",
        cache_dir=tmp_path,
        min_interval_seconds=0,
        max_retries=1,
        max_retry_after_seconds=3,
        sleep_func=sleeps.append,
        open_func=opener,
    )
    assert not response.ok and sleeps == [] and calls == 1
    assert response.warning.retry_after == 3600


def test_timeout_finishes_without_unbounded_retry(tmp_path: Path) -> None:
    calls = 0

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        raise TimeoutError("bounded timeout")

    response = request_text(
        "https://example.test/timeout",
        user_agent="test",
        cache_dir=tmp_path,
        min_interval_seconds=0,
        max_retries=5,
        open_func=opener,
    )
    assert response.ok is False
    assert calls == 1


def test_per_source_budget_exhaustion_records_reason(tmp_path: Path) -> None:
    clock = _Clock()
    context = _context(tmp_path, clock)
    context.register_source({"name": "arxiv"})
    clock.value += 11
    assert context.request_allowed("arxiv") is False
    health = context.health("arxiv")
    assert health.runtime_reason_code == "SOURCE_TIME_BUDGET_EXHAUSTED"
    assert health.runtime_state == "partial"


def test_global_budget_skips_future_external_io(tmp_path: Path) -> None:
    clock = _Clock()
    context = _context(tmp_path, clock, global_time_budget_seconds=5)
    context.register_source({"name": "arxiv"})
    clock.value += 6
    assert context.request_allowed("arxiv") is False
    assert context.health("arxiv").runtime_reason_code == "GLOBAL_TIME_BUDGET_EXHAUSTED"


def test_source_circuit_breaker_opens_after_repeated_retryable_failures(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context.register_source({"name": "openalex"})
    context.note_request_result("openalex", ok=False, failure_category="timeout")
    context.note_request_result("openalex", ok=False, failure_category="rate_limit")
    assert context.request_allowed("openalex") is False
    assert context.health("openalex").runtime_reason_code == "PROVIDER_RETRY_AFTER_DEFERRED"


def test_successful_zero_hit_does_not_trip_circuit(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context.register_source({"name": "crossref"})
    request = QueryRequest("test-family", "LWE", source_family="crossref")
    attempt = context.begin_query_attempt("crossref", request)
    context.finish_query_attempt(attempt, status="success", raw_candidates=0)
    assert context.request_allowed("crossref") is True
    assert context.health("crossref").circuit_open is False


def test_runtime_journal_is_durable_before_normal_completion(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context.register_source({"name": "iacr_eprint"})
    rows = [json.loads(line) for line in context.runtime_journal_path.read_text(encoding="utf-8").splitlines()]
    assert [row["event"] for row in rows[:2]] == ["RUN_STARTED", "SOURCE_STARTED"]
    serialized = json.dumps(rows)
    assert "api_key" not in serialized.lower()


def test_partial_source_health_is_serializable_and_checkpointed(tmp_path: Path) -> None:
    clock = _Clock()
    context = _context(tmp_path, clock)
    context.register_source({"name": "semantic_scholar"})
    clock.value += 11
    context.request_allowed("semantic_scholar")
    context.finish_source("semantic_scholar", 2)
    row = context.source_health_summary()[0]
    assert row["runtime_state"] == "partial"
    assert row["partial_results_preserved"] is True
    assert row["runtime_reason_code"] == "SOURCE_TIME_BUDGET_EXHAUSTED"


def test_records_from_completed_source_survive_later_source_failure(tmp_path: Path, monkeypatch) -> None:
    good = make_paper_record(title="LWE result", source="good", source_url="https://example.test/good")

    class Adapter:
        def __init__(self, name: str) -> None:
            self.name = name

        def fetch(self, context):
            if self.name == "bad":
                raise TimeoutError("simulated")
            return [good]

    monkeypatch.setattr("lattice_digest.run.build_source", lambda config: Adapter(config["name"]))
    context = _context(tmp_path)
    records = _collect_records([{"name": "good"}, {"name": "bad"}], context)
    assert records == [good]
    assert context.health("bad").health_status() == "red"


def test_runtime_reliability_uses_no_background_worker_primitives() -> None:
    source = (Path(__file__).parents[1] / "src" / "lattice_digest" / "sources" / "base.py").read_text(encoding="utf-8")
    assert "ThreadPoolExecutor" not in source
    assert "ProcessPoolExecutor" not in source
    assert "asyncio.create_task" not in source
