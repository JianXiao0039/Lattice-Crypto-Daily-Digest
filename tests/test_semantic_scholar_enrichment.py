from __future__ import annotations

from pathlib import Path

import lattice_digest.semantic_scholar_enrichment as enrichment
from lattice_digest.config import load_config_bundle
from lattice_digest.http import HttpResponse, HttpWarning
from lattice_digest.models import make_paper_record
from lattice_digest.ranker import classify_record
from lattice_digest.semantic_scholar_enrichment import SemanticScholarEnricher


def _record():
    return make_paper_record(
        title="On the Secrecy of the Encapsulation Coin in ML-KEM",
        abstract="We study ML-KEM and Kyber security.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2026/1117",
        eprint_id="2026/1117",
        doi="10.0000/example",
    )


def test_missing_key_skips_enrichment_gracefully(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SEMANTIC_SCHOLAR_API_KEY", raising=False)
    called = {"request": False}

    def fake_request_json(*args, **kwargs):
        called["request"] = True
        return {}, HttpResponse(ok=True, url="https://example.test")

    monkeypatch.setattr(enrichment, "request_json", fake_request_json)
    enricher = SemanticScholarEnricher(root=tmp_path)

    result = enricher.enrich_record(_record())

    assert result.status == "skipped"
    assert "SEMANTIC_SCHOLAR_API_KEY" in " ".join(result.warnings)
    assert called["request"] is False


def test_present_fake_key_is_used_only_in_x_api_key_header(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "unit-test-placeholder")
    captured: dict[str, object] = {}

    def fake_request_json(*args, **kwargs):
        captured["url"] = args[0]
        captured["headers"] = kwargs.get("headers")
        captured["min_interval_seconds"] = kwargs.get("min_interval_seconds")
        return (
            {
                "corpusId": 123,
                "paperId": "S2-PAPER-ID",
                "externalIds": {"DOI": "10.0000/example"},
                "url": "https://www.semanticscholar.org/paper/example",
                "title": "On the Secrecy of the Encapsulation Coin in ML-KEM",
                "abstract": "Metadata abstract.",
                "authors": [{"authorId": "1", "name": "Alice Example"}],
                "venue": "IACR ePrint",
                "year": 2026,
                "referenceCount": 10,
                "citationCount": 0,
                "influentialCitationCount": 0,
                "openAccessPdf": {"url": "https://eprint.iacr.org/2026/1117.pdf"},
            },
            HttpResponse(ok=True, url="https://api.semanticscholar.org"),
        )

    monkeypatch.setattr(enrichment, "request_json", fake_request_json)
    enricher = SemanticScholarEnricher(root=tmp_path)

    result = enricher.enrich_record(_record())

    assert result.status == "enriched"
    assert result.metadata is not None
    assert result.metadata["paperId"] == "S2-PAPER-ID"
    assert result.metadata["corpusId"] == 123
    assert captured["headers"] == {"x-api-key": "unit-test-placeholder"}
    assert "unit-test-placeholder" not in str(captured["url"])
    assert captured["min_interval_seconds"] == 1.0
    cache_text = "\n".join(path.read_text(encoding="utf-8") for path in (tmp_path / "cache").rglob("*.json"))
    assert "unit-test-placeholder" not in cache_text


def test_request_limit_bounds_enrichment_requests(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "unit-test-placeholder")
    calls = {"count": 0}

    def fake_request_json(*args, **kwargs):
        calls["count"] += 1
        return {"title": "A", "authors": []}, HttpResponse(ok=True, url="https://api.semanticscholar.org")

    monkeypatch.setattr(enrichment, "request_json", fake_request_json)
    enricher = SemanticScholarEnricher(root=tmp_path, max_requests_per_run=1)
    first = make_paper_record(title="First LWE paper", abstract="", source="arxiv", source_url="https://arxiv.org/abs/1")
    second = make_paper_record(title="Second LWE paper", abstract="", source="arxiv", source_url="https://arxiv.org/abs/2")

    results, summary = enricher.enrich_records([first, second])

    assert calls["count"] == 1
    assert summary.requests_attempted == 1
    assert summary.skipped_count == 1
    assert results[1]["semantic_scholar_enrichment"]["status"] == "skipped"
    assert "request limit reached" in results[1]["semantic_scholar_enrichment"]["warnings"]


def test_enrichment_failure_is_retryable_and_nonfatal(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "unit-test-placeholder")

    def fake_request_json(*args, **kwargs):
        warning = HttpWarning(
            url="https://api.semanticscholar.org/graph/v1/paper/search/match",
            source="semantic_scholar_enrichment",
            status_code=429,
            reason="Too Many Requests",
            attempts=1,
        )
        warnings = kwargs.get("warnings")
        if warnings is not None:
            warnings.append(warning.to_message())
        return None, HttpResponse(ok=False, url=warning.url, warning=warning)

    monkeypatch.setattr(enrichment, "request_json", fake_request_json)
    enricher = SemanticScholarEnricher(root=tmp_path)

    result = enricher.enrich_record(_record())

    assert result.status == "failed"
    assert result.retryable is True
    assert result.metadata is None


def test_network_error_is_retryable_and_nonfatal(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "unit-test-placeholder")

    def fake_request_json(*args, **kwargs):
        warning = HttpWarning(
            url="https://api.semanticscholar.org/graph/v1/paper/DOI%3A10.0000%2Fexample",
            source="semantic_scholar_enrichment",
            attempts=1,
            error="URLError simulated network failure",
        )
        warnings = kwargs.get("warnings")
        if warnings is not None:
            warnings.append(warning.to_message())
        return None, HttpResponse(ok=False, url=warning.url, warning=warning)

    monkeypatch.setattr(enrichment, "request_json", fake_request_json)
    enricher = SemanticScholarEnricher(root=tmp_path)

    result = enricher.enrich_record(_record())

    assert result.status == "failed"
    assert result.retryable is True
    assert result.metadata is None


def test_corpus_id_lookup_precedes_title_fallback() -> None:
    lookup = enrichment.build_semantic_scholar_lookup(
        {
            "title": "Title fallback should not be used",
            "corpusId": 123456,
        }
    )

    assert lookup == ("paper", "CorpusId:123456")


def test_enrichment_does_not_change_ranking_thresholds(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "unit-test-placeholder")
    configs = load_config_bundle()
    record = _record()
    before = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

    def fake_request_json(*args, **kwargs):
        return {"title": record.title, "citationCount": 999999, "authors": []}, HttpResponse(ok=True, url="https://api.semanticscholar.org")

    monkeypatch.setattr(enrichment, "request_json", fake_request_json)
    SemanticScholarEnricher(root=tmp_path).enrich_record(record)
    after = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

    assert after.relevance_score == before.relevance_score
    assert after.relevance_label == before.relevance_label


def test_no_scheduled_automation_files_are_introduced() -> None:
    root = Path(__file__).resolve().parents[1]
    forbidden_suffixes = {".cron", ".service"}
    forbidden_names = {"taskscheduler.xml", "scheduler.xml"}
    for path in root.rglob("*"):
        if ".git" in path.parts or ".pytest_tmp" in path.parts or "__pycache__" in path.parts:
            continue
        assert path.suffix.lower() not in forbidden_suffixes
        assert path.name.lower() not in forbidden_names
