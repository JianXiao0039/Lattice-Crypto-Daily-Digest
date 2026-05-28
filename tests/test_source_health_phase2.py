from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import lattice_digest.sources.arxiv as arxiv
import lattice_digest.sources.openalex as openalex
import lattice_digest.sources.semantic_scholar as semantic_scholar
from lattice_digest.sources.arxiv import ArxivSource
from lattice_digest.sources.base import FetchContext
from lattice_digest.sources.base import SourceHealth
from lattice_digest.sources.openalex import OpenAlexSource
from lattice_digest.sources.semantic_scholar import SemanticScholarSource


def _context(tmp: str, api_keys: dict[str, str] | None = None) -> FetchContext:
    return FetchContext(
        root=Path(tmp),
        since=datetime(2026, 5, 20, tzinfo=timezone.utc),
        dry_run=False,
        per_domain_min_interval_seconds=0,
        max_retries=0,
        api_keys=api_keys or {},
    )


def test_source_health_dict_includes_red_yellow_green_fields() -> None:
    health = SourceHealth(
        name="openalex",
        warnings=["openalex: HTTP 429 rate limit Too Many Requests"],
    ).to_dict()

    assert health["health_status"] == "red"
    assert health["raw_count"] == 0
    assert health["normalized_count"] == 0
    assert health["date_filtered_count"] == 0
    assert health["final_count"] == 0
    assert health["error_type"] == "rate_limit"
    assert health["retryable"] is True


def test_openalex_query_does_not_use_paid_updated_sort() -> None:
    captured: dict[str, str] = {}

    def fake_fetch_json(context: FetchContext, url: str, **kwargs: object) -> dict:
        captured["url"] = url
        return {
            "results": [
                {
                    "id": "https://openalex.org/W1",
                    "title": "LWE Cryptanalysis with BKZ",
                    "doi": "https://doi.org/10.0000/openalex",
                    "publication_date": "2026-05-27",
                    "updated_date": "2026-05-28",
                    "authorships": [{"author": {"display_name": "Alice Example"}}],
                    "primary_location": {"source": {"display_name": "OpenAlex Test"}},
                }
            ]
        }

    original_fetch_json = openalex.fetch_json
    openalex.fetch_json = fake_fetch_json
    try:
        with TemporaryDirectory() as tmp:
            source = OpenAlexSource(
                {
                    "name": "openalex",
                    "type": "openalex",
                    "url": "https://api.openalex.org/works",
                    "max_results": 25,
                }
            )
            records = source.fetch(_context(tmp))
    finally:
        openalex.fetch_json = original_fetch_json

    assert len(records) == 1
    assert "sort=updated_date" not in captured["url"]


def test_openalex_plan_upgrade_429_is_red_but_nonfatal() -> None:
    def fake_fetch_json(context: FetchContext, url: str, **kwargs: object) -> None:
        context.add_warning(
            "openalex: skipped https://api.openalex.org/works after 3 attempt(s): "
            'HTTP 429 rate limit Too Many Requests; body_preview={"error":"Plan upgrade required"}',
            "openalex",
        )
        return None

    original_fetch_json = openalex.fetch_json
    openalex.fetch_json = fake_fetch_json
    try:
        with TemporaryDirectory() as tmp:
            source = OpenAlexSource(
                {
                    "name": "openalex",
                    "type": "openalex",
                    "url": "https://api.openalex.org/works",
                    "max_results": 25,
                }
            )
            context = _context(tmp)
            records = source.fetch(context)
            health = context.source_health_summary()[0]
    finally:
        openalex.fetch_json = original_fetch_json

    assert records == []
    assert health["health_status"] == "red"
    assert health["error_type"] == "plan_upgrade_required"
    assert health["retryable"] is False


def test_semantic_scholar_uses_api_key_header_without_leaking_value() -> None:
    captured: dict[str, object] = {}

    def fake_fetch_json(context: FetchContext, url: str, headers: dict[str, str] | None = None, **kwargs: object) -> dict:
        captured["headers"] = headers or {}
        return {"data": []}

    original_fetch_json = semantic_scholar.fetch_json
    semantic_scholar.fetch_json = fake_fetch_json
    try:
        with TemporaryDirectory() as tmp:
            context = _context(tmp, {"SEMANTIC_SCHOLAR_API_KEY": "secret-test-key"})
            source = SemanticScholarSource(
                {
                    "name": "semantic_scholar",
                    "type": "semantic_scholar",
                    "url": "https://api.semanticscholar.org/graph/v1/paper/search",
                    "max_results": 50,
                }
            )
            records = source.fetch(context)
            health = context.source_health_summary()[0]
    finally:
        semantic_scholar.fetch_json = original_fetch_json

    assert records == []
    assert captured["headers"] == {"x-api-key": "secret-test-key"}
    assert health["api_key_used"] is True
    assert "secret-test-key" not in str(health)


def test_semantic_scholar_without_api_key_still_runs_anonymously() -> None:
    captured: dict[str, object] = {}

    def fake_fetch_json(context: FetchContext, url: str, headers: dict[str, str] | None = None, **kwargs: object) -> dict:
        captured["headers"] = headers or {}
        captured["url"] = url
        return {"data": []}

    original_fetch_json = semantic_scholar.fetch_json
    semantic_scholar.fetch_json = fake_fetch_json
    try:
        with TemporaryDirectory() as tmp:
            context = _context(tmp)
            source = SemanticScholarSource(
                {
                    "name": "semantic_scholar",
                    "type": "semantic_scholar",
                    "url": "https://api.semanticscholar.org/graph/v1/paper/search",
                    "max_results": 50,
                }
            )
            source.fetch(context)
            health = context.source_health_summary()[0]
    finally:
        semantic_scholar.fetch_json = original_fetch_json

    assert captured["headers"] == {}
    assert "limit=10" in str(captured["url"])
    assert health["api_key_used"] is False


def test_semantic_scholar_429_is_red_but_nonfatal() -> None:
    def fake_fetch_json(context: FetchContext, url: str, **kwargs: object) -> None:
        context.add_warning(
            "semantic_scholar: skipped https://api.semanticscholar.org after 3 attempt(s): "
            "HTTP 429 rate limit Too Many Requests",
            "semantic_scholar",
        )
        return None

    original_fetch_json = semantic_scholar.fetch_json
    semantic_scholar.fetch_json = fake_fetch_json
    try:
        with TemporaryDirectory() as tmp:
            context = _context(tmp)
            source = SemanticScholarSource(
                {
                    "name": "semantic_scholar",
                    "type": "semantic_scholar",
                    "url": "https://api.semanticscholar.org/graph/v1/paper/search",
                }
            )
            records = source.fetch(context)
            health = context.source_health_summary()[0]
    finally:
        semantic_scholar.fetch_json = original_fetch_json

    assert records == []
    assert health["health_status"] == "red"
    assert health["error_type"] == "rate_limit"
    assert health["api_key_used"] is False


def test_arxiv_partial_query_failure_keeps_successful_groups() -> None:
    atom = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2601.00001v1</id>
        <updated>2026-05-28T00:00:00Z</updated>
        <published>2026-05-28T00:00:00Z</published>
        <title>Learning with Errors and BKZ</title>
        <summary>A lattice cryptanalysis paper.</summary>
        <author><name>Alice Example</name></author>
        <category term="cs.CR"/>
      </entry>
    </feed>
    """
    calls = {"count": 0}

    def fake_fetch_text(context: FetchContext, url: str, **kwargs: object) -> str | None:
        calls["count"] += 1
        if calls["count"] == 1:
            context.add_warning("arxiv: simulated query-group timeout", "arxiv")
            return None
        return atom

    original_fetch_text = arxiv.fetch_text
    arxiv.fetch_text = fake_fetch_text
    try:
        with TemporaryDirectory() as tmp:
            context = _context(tmp)
            source = ArxivSource(
                {
                    "name": "arxiv",
                    "type": "arxiv",
                    "url": "https://export.arxiv.org/api/query",
                    "categories": ["cs.CR"],
                    "query_groups": [["bad group"], ["Learning with Errors"]],
                    "per_query_results": 25,
                }
            )
            records = source.fetch(context)
            health = context.source_health_summary()[0]
    finally:
        arxiv.fetch_text = original_fetch_text

    assert len(records) == 1
    assert health["query_groups_total"] == 2
    assert health["query_groups_success"] == 1
    assert health["query_groups_failed"] == 1
    assert health["health_status"] == "yellow"
