from __future__ import annotations

import html
import re
import urllib.parse
from datetime import datetime, timezone

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_json, normalize_date, within_since
from lattice_digest.text import normalize_whitespace
from lattice_digest.source_queries import critical_query_requests, legacy_query_requests

TAG_RE = re.compile(r"<[^>]+>")


class CrossrefSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        if context.dry_run:
            context.add_warning("dry-run: skipped Crossref network request", self.name)
            return []
        requests = critical_query_requests(self.config, syntax="free_text")
        requests.extend(legacy_query_requests(self.config, keys=("query_groups", "query_terms")))
        if not requests:
            requests = legacy_query_requests({"query_terms": ["lattice cryptography LWE SIS NTRU BKZ FHE"]}, keys=("query_terms",))
        health = context.health(self.name)
        health.query_groups_total = len(requests)
        normalized: list[PaperRecord] = []
        seen: set[str] = set()
        raw_count = 0
        for request in requests:
            attempt_id = context.begin_query_attempt(self.name, request)
            params = urllib.parse.urlencode({"query.bibliographic": request.query_text, "rows": min(int(self.config.get("max_results", 50)), 25), "sort": "published", "order": "desc"})
            data = fetch_json(context, f"{self.config['url']}?{params}", source_name=self.name)
            if data is None:
                context.finish_query_attempt(attempt_id, status="failed", raw_candidates=None, error_category=health.error_type())
                health.query_groups_failed += 1
                continue
            health.query_groups_success += 1
            items = data.get("message", {}).get("items", [])
            context.finish_query_attempt(attempt_id, status="success", raw_candidates=len(items))
            raw_count += len(items)
            for item in items:
                titles = item.get("title") or []
                title = titles[0] if titles else None
                doi = item.get("DOI")
                source_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)
                abstract = normalize_whitespace(TAG_RE.sub(" ", html.unescape(item.get("abstract") or "")))
                occurrence_id = context.record_raw_occurrence(
                    self.name,
                    attempt_id,
                    raw_title=str(title or ""),
                    source_identifier=doi,
                    source_url=source_url,
                    abstract_present=bool(abstract),
                    parser_result="PARSED" if title and source_url else "RAW_PARSE_FAILED",
                    parser_failure_reason=None if title and source_url else "missing title or source URL",
                    normalization_eligible=bool(title and source_url),
                )
                if not title or not source_url:
                    continue
                if source_url in seen:
                    context.record_route_event("raw_occurrence", occurrence_id, "DEDUP", "DUPLICATE_WITHIN_SOURCE", "same Crossref URL returned by another query", terminal=True)
                    continue
                authors = [" ".join(part for part in [author.get("given"), author.get("family")] if part) for author in item.get("author", [])]
                date_parts = (item.get("published-print") or item.get("published-online") or item.get("created") or {}).get("date-parts", [])
                date_text = "-".join(str(part) for part in date_parts[0]) if date_parts else None
                record = make_paper_record(
                    title=title, authors=[author for author in authors if author], abstract=abstract, source="crossref",
                    source_url=source_url, paper_id=doi or source_url, doi=doi, venue=(item.get("container-title") or [None])[0],
                    publication_date=normalize_date(date_text), categories=["crossref"],
                    source_query_family=request.family_id, source_query_text=request.query_text,
                    retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
                )
                context.record_normalized_candidate(occurrence_id, record)
                normalized.append(record)
                seen.add(source_url)
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
