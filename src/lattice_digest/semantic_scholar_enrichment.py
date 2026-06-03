from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from lattice_digest.http import HttpResponse, request_json


SEMANTIC_SCHOLAR_API_BASE = "https://api.semanticscholar.org/graph/v1"
ENRICHMENT_FIELDS = (
    "paperId,corpusId,externalIds,url,title,abstract,authors,venue,year,referenceCount,"
    "citationCount,influentialCitationCount,openAccessPdf"
)


@dataclass
class EnrichmentResult:
    status: str
    metadata: dict[str, Any] | None = None
    retryable: bool = False
    cache_hit: bool = False
    warnings: list[str] = field(default_factory=list)
    lookup: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "metadata": self.metadata,
            "retryable": self.retryable,
            "cache_hit": self.cache_hit,
            "warnings": list(self.warnings),
            "lookup": self.lookup,
        }


@dataclass
class EnrichmentSummary:
    enabled: bool
    api_key_used: bool
    records_considered: int = 0
    requests_attempted: int = 0
    request_limit: int = 20
    enriched_count: int = 0
    cache_hits: int = 0
    skipped_count: int = 0
    failure_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "api_key_used": self.api_key_used,
            "records_considered": self.records_considered,
            "requests_attempted": self.requests_attempted,
            "request_limit": self.request_limit,
            "enriched_count": self.enriched_count,
            "cache_hits": self.cache_hits,
            "skipped_count": self.skipped_count,
            "failure_count": self.failure_count,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _field(record: Any, *names: str) -> Any:
    for name in names:
        if isinstance(record, dict) and name in record:
            return record.get(name)
        if hasattr(record, name):
            return getattr(record, name)
    return None


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _cache_key(lookup: str) -> str:
    return hashlib.sha256(lookup.encode("utf-8")).hexdigest()


def _safe_authors(value: Any) -> list[dict[str, Any]]:
    authors: list[dict[str, Any]] = []
    for item in value or []:
        if not isinstance(item, dict):
            continue
        author = {
            "authorId": item.get("authorId"),
            "name": _normalize_text(item.get("name")),
        }
        authors.append(author)
    return authors


def sanitize_semantic_scholar_metadata(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "paperId": _normalize_text(data.get("paperId")),
        "corpusId": data.get("corpusId"),
        "externalIds": data.get("externalIds") if isinstance(data.get("externalIds"), dict) else {},
        "url": _normalize_text(data.get("url")),
        "title": _normalize_text(data.get("title")),
        "abstract": _normalize_text(data.get("abstract")),
        "authors": _safe_authors(data.get("authors")),
        "venue": _normalize_text(data.get("venue")),
        "year": data.get("year"),
        "referenceCount": data.get("referenceCount"),
        "citationCount": data.get("citationCount"),
        "influentialCitationCount": data.get("influentialCitationCount"),
        "openAccessPdf": data.get("openAccessPdf") if isinstance(data.get("openAccessPdf"), dict) else None,
    }


def build_semantic_scholar_lookup(record: Any) -> tuple[str, str] | None:
    doi = _normalize_text(_field(record, "doi", "DOI"))
    if doi:
        return "paper", f"DOI:{doi}"
    arxiv_id = _normalize_text(_field(record, "arxiv_id", "arxivId", "arxiv"))
    if arxiv_id:
        return "paper", f"ARXIV:{arxiv_id}"
    corpus_id = _normalize_text(_field(record, "semantic_scholar_corpus_id", "corpusId", "corpus_id"))
    if corpus_id:
        return "paper", f"CorpusId:{corpus_id}"
    paper_id = _normalize_text(_field(record, "semantic_scholar_id", "paperId", "paper_id"))
    source = _normalize_text(_field(record, "source")).lower()
    if paper_id and ("semantic" in source or len(paper_id) >= 20):
        return "paper", paper_id
    title = _normalize_text(_field(record, "title"))
    if title:
        return "search_match", title
    return None


class SemanticScholarEnricher:
    def __init__(
        self,
        *,
        root: Path,
        max_requests_per_run: int = 20,
        min_interval_seconds: float = 1.0,
        timeout_seconds: int = 20,
        user_agent: str = "lattice-crypto-daily-digest/semantic-scholar-enrichment",
        cache_dir: Path | None = None,
        sleep_func=time.sleep,
        open_func=None,
    ) -> None:
        self.root = root
        self.api_key = (os.environ.get("SEMANTIC_SCHOLAR_API_KEY") or "").strip()
        self.max_requests_per_run = max(0, int(max_requests_per_run))
        self.min_interval_seconds = max(1.0, float(min_interval_seconds))
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent
        self.cache_dir = cache_dir or root / "cache" / "semantic-scholar-enrichment"
        self.sleep_func = sleep_func
        self.open_func = open_func
        self.requests_attempted = 0

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _cache_path(self, lookup: str) -> Path:
        return self.cache_dir / f"{_cache_key(lookup)}.json"

    def _read_cache(self, lookup: str) -> dict[str, Any] | None:
        path = self._cache_path(lookup)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        metadata = payload.get("metadata")
        return metadata if isinstance(metadata, dict) else None

    def _write_cache(self, lookup: str, metadata: dict[str, Any]) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_path(lookup).write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "lookup": lookup,
                    "fetched_at": _now_iso(),
                    "metadata": metadata,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _build_url(self, lookup_type: str, lookup_value: str) -> str:
        if lookup_type == "paper":
            encoded = urllib.parse.quote(lookup_value, safe="")
            params = urllib.parse.urlencode({"fields": ENRICHMENT_FIELDS})
            return f"{SEMANTIC_SCHOLAR_API_BASE}/paper/{encoded}?{params}"
        params = urllib.parse.urlencode({"query": lookup_value, "fields": ENRICHMENT_FIELDS})
        return f"{SEMANTIC_SCHOLAR_API_BASE}/paper/search/match?{params}"

    def enrich_record(self, record: Any) -> EnrichmentResult:
        lookup = build_semantic_scholar_lookup(record)
        if lookup is None:
            return EnrichmentResult(status="skipped", retryable=False, warnings=["missing lookup fields"])
        lookup_type, lookup_value = lookup
        lookup_id = f"{lookup_type}:{lookup_value}"
        if not self.enabled:
            return EnrichmentResult(status="skipped", retryable=False, warnings=["SEMANTIC_SCHOLAR_API_KEY not set"], lookup=lookup_id)
        cached = self._read_cache(lookup_id)
        if cached is not None:
            return EnrichmentResult(status="enriched", metadata=cached, cache_hit=True, lookup=lookup_id)
        if self.requests_attempted >= self.max_requests_per_run:
            return EnrichmentResult(status="skipped", retryable=True, warnings=["request limit reached"], lookup=lookup_id)

        self.requests_attempted += 1
        warnings: list[str] = []
        url = self._build_url(lookup_type, lookup_value)
        data, response = request_json(
            url,
            source="semantic_scholar_enrichment",
            user_agent=self.user_agent,
            timeout_seconds=self.timeout_seconds,
            headers={"x-api-key": self.api_key},
            cache_dir=self.root / "cache" / "http",
            cache_ttl_seconds=12 * 60 * 60,
            min_interval_seconds=self.min_interval_seconds,
            max_retries=1,
            retry_statuses=(429, 503),
            warnings=warnings,
            sleep_func=self.sleep_func,
            open_func=self.open_func,
        )
        if data is None:
            return EnrichmentResult(
                status="failed",
                retryable=_is_retryable_response(response),
                warnings=warnings or ["Semantic Scholar enrichment request failed"],
                lookup=lookup_id,
            )
        metadata = sanitize_semantic_scholar_metadata(data)
        self._write_cache(lookup_id, metadata)
        return EnrichmentResult(status="enriched", metadata=metadata, lookup=lookup_id)

    def enrich_records(self, records: Iterable[Any]) -> tuple[list[dict[str, Any]], EnrichmentSummary]:
        items: list[dict[str, Any]] = []
        summary = EnrichmentSummary(
            enabled=self.enabled,
            api_key_used=self.enabled,
            request_limit=self.max_requests_per_run,
        )
        for record in records:
            summary.records_considered += 1
            result = self.enrich_record(record)
            if result.status == "enriched":
                summary.enriched_count += 1
            elif result.status == "failed":
                summary.failure_count += 1
            else:
                summary.skipped_count += 1
            if result.cache_hit:
                summary.cache_hits += 1
            items.append(
                {
                    "title": _normalize_text(_field(record, "title")),
                    "source_url": _normalize_text(_field(record, "source_url", "url")),
                    "semantic_scholar_enrichment": result.to_dict(),
                }
            )
        summary.requests_attempted = self.requests_attempted
        return items, summary


def _is_retryable_response(response: HttpResponse) -> bool:
    warning = response.warning
    if warning and warning.status_code in {429, 500, 502, 503, 504}:
        return True
    if warning and warning.error:
        return True
    return False


def _load_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        records = payload.get("records")
        if isinstance(records, list):
            return [item for item in records if isinstance(item, dict)]
    return []


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optional Semantic Scholar metadata enrichment for existing digest records.")
    parser.add_argument("--input", type=Path, required=True, help="Existing digest JSON file.")
    parser.add_argument("--output-dir", type=Path, default=Path("exports") / "semantic-scholar-enrichment")
    parser.add_argument("--max-requests", type=int, default=20)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    records = _load_records(args.input)
    if args.limit is not None:
        records = records[: max(0, args.limit)]
    enricher = SemanticScholarEnricher(root=Path.cwd(), max_requests_per_run=args.max_requests)
    if args.dry_run:
        print(
            "Semantic Scholar enrichment dry-run: "
            f"records={len(records)}, enabled={enricher.enabled}, max_requests={enricher.max_requests_per_run}"
        )
        if not enricher.enabled:
            print("Semantic Scholar enrichment skipped: SEMANTIC_SCHOLAR_API_KEY is not set.")
        return 0
    items, summary = enricher.enrich_records(records)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / f"{args.input.stem}.semantic-scholar.json"
    output.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "input": str(args.input),
                "summary": summary.to_dict(),
                "items": items,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {output}")
    print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
