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
            params = urllib.parse.urlencode({"query.bibliographic": request.query_text, "rows": min(int(self.config.get("max_results", 50)), 25), "sort": "published", "order": "desc"})
            data = fetch_json(context, f"{self.config['url']}?{params}", source_name=self.name)
            if data is None:
                context.record_query_attempt(self.name, request.family_id, request.query_text, status="failed")
                health.query_groups_failed += 1
                continue
            health.query_groups_success += 1
            items = data.get("message", {}).get("items", [])
            context.record_query_attempt(self.name, request.family_id, request.query_text, status="success", raw_candidates=len(items))
            raw_count += len(items)
            for item in items:
                titles = item.get("title") or []
                title = titles[0] if titles else None
                doi = item.get("DOI")
                source_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)
                if not title or not source_url or source_url in seen:
                    continue
                authors = [" ".join(part for part in [author.get("given"), author.get("family")] if part) for author in item.get("author", [])]
                abstract = normalize_whitespace(TAG_RE.sub(" ", html.unescape(item.get("abstract") or "")))
                date_parts = (item.get("published-print") or item.get("published-online") or item.get("created") or {}).get("date-parts", [])
                date_text = "-".join(str(part) for part in date_parts[0]) if date_parts else None
                normalized.append(make_paper_record(
                    title=title, authors=[author for author in authors if author], abstract=abstract, source="crossref",
                    source_url=source_url, paper_id=doi or source_url, doi=doi, venue=(item.get("container-title") or [None])[0],
                    publication_date=normalize_date(date_text), categories=["crossref"],
                    source_query_family=request.family_id, source_query_text=request.query_text,
                    retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
                ))
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
