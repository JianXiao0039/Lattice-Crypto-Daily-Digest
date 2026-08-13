from __future__ import annotations

import urllib.parse
from datetime import datetime, timezone

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_json, normalize_date, within_since
from lattice_digest.source_queries import critical_query_requests, legacy_query_requests


class DblpSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        if context.dry_run:
            context.add_warning("dry-run: skipped DBLP network request", self.name)
            return []
        normalized: list[PaperRecord] = []
        seen_urls: set[str] = set()
        raw_count = 0
        requests = critical_query_requests(self.config, syntax="free_text")
        requests.extend(legacy_query_requests(self.config, keys=("queries",)))
        if not requests:
            requests = legacy_query_requests({"queries": ["lattice cryptography LWE SIS NTRU BKZ"]}, keys=("queries",))
        health = context.health(self.name)
        health.query_groups_total = len(requests)
        per_query = int(self.config.get("per_query_results", self.config.get("max_results", 50)))
        per_query = min(per_query, int(self.config.get("max_results", 50)))
        for request in requests:
            attempt_id = context.begin_query_attempt(self.name, request)
            params = urllib.parse.urlencode(
                {
                    "q": request.query_text,
                    "format": "json",
                    "h": per_query,
                }
            )
            data = fetch_json(context, f"{self.config['url']}?{params}", source_name=self.name)
            if data is None:
                context.finish_query_attempt(attempt_id, status="failed", raw_candidates=None, error_category=health.error_type())
                health.query_groups_failed += 1
                continue
            health.query_groups_success += 1
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            context.finish_query_attempt(attempt_id, status="success", raw_candidates=len(hits))
            raw_count += len(hits)
            for hit in hits:
                info = hit.get("info", {})
                title = info.get("title")
                url = info.get("url") or info.get("ee")
                occurrence_id = context.record_raw_occurrence(
                    self.name,
                    attempt_id,
                    raw_title=str(title or ""),
                    source_identifier=info.get("key") or hit.get("@id"),
                    source_url=url,
                    publication_date=str(info.get("year") or "") or None,
                    abstract_present=False,
                    parser_result="PARSED" if title and url else "RAW_PARSE_FAILED",
                    parser_failure_reason=None if title and url else "missing title or source URL",
                    normalization_eligible=bool(title and url),
                )
                if not title or not url:
                    continue
                if url in seen_urls:
                    context.record_route_event("raw_occurrence", occurrence_id, "DEDUP", "DUPLICATE_WITHIN_SOURCE", "same DBLP URL returned by another query", terminal=True)
                    continue
                authors_raw = info.get("authors", {}).get("author", [])
                if isinstance(authors_raw, dict):
                    authors = [authors_raw.get("text") or authors_raw.get("@pid") or ""]
                else:
                    authors = [item.get("text") if isinstance(item, dict) else str(item) for item in authors_raw]
                record = make_paper_record(
                    title=title,
                    authors=[author for author in authors if author],
                    abstract="",
                    source="dblp",
                    source_url=url,
                    paper_id=info.get("key") or hit.get("@id") or url,
                    doi=info.get("doi"),
                    venue=info.get("venue"),
                    publication_date=normalize_date(str(info.get("year")) if info.get("year") else None),
                    categories=["dblp"],
                    source_query_family=request.family_id,
                    source_query_text=request.query_text,
                    retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
                )
                context.record_normalized_candidate(occurrence_id, record)
                seen_urls.add(url)
                normalized.append(record)
        filtered = [
            record
            for record in normalized
            if within_since(record.publication_date, record.update_date, context.since)
        ]
        context.set_source_counts(
            self.name,
            raw=raw_count,
            normalized=len(normalized),
            date_filtered=len(filtered),
        )
        return filtered
