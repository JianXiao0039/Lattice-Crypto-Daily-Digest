from __future__ import annotations

import urllib.parse
from datetime import datetime, timezone

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_json, normalize_date, within_since
from lattice_digest.source_queries import critical_query_requests, legacy_query_requests


class SemanticScholarSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        if context.dry_run:
            context.add_warning("dry-run: skipped Semantic Scholar network request", self.name)
            return []
        fields = (
            "paperId,title,abstract,authors,venue,year,publicationDate,updatedAt,"
            "releaseDate,externalIds,url,openAccessPdf"
        )
        api_key = (context.api_keys.get("SEMANTIC_SCHOLAR_API_KEY") or "").strip()
        context.health(self.name).api_key_used = bool(api_key)
        configured_limit = int(self.config.get("max_results", 50))
        limit = configured_limit if api_key else min(configured_limit, 10)
        requests = critical_query_requests(self.config, syntax="plain")
        requests.extend(legacy_query_requests(self.config, keys=("query_groups", "query_terms")))
        if not requests:
            requests = legacy_query_requests({"query_terms": ["lattice cryptography LWE SIS NTRU BKZ FHE"]}, keys=("query_terms",))
        health = context.health(self.name)
        health.query_groups_total = len(requests)
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
        normalized: list[PaperRecord] = []
        filtered: list[PaperRecord] = []
        skipped_year_only = 0
        raw_count = 0
        seen: set[str] = set()
        for request in requests:
            params = urllib.parse.urlencode({"query": request.query_text, "limit": limit, "fields": fields})
            data = fetch_json(context, f"{self.config['url']}?{params}", headers=headers, source_name=self.name)
            if data is None:
                context.record_query_attempt(self.name, request.family_id, request.query_text, status="failed")
                health.query_groups_failed += 1
                continue
            health.query_groups_success += 1
            items = data.get("data", [])
            context.record_query_attempt(self.name, request.family_id, request.query_text, status="success", raw_candidates=len(items))
            raw_count += len(items)
            for item in items:
                title = item.get("title")
                source_url = item.get("url")
                if not title or not source_url or source_url in seen:
                    continue
                external = item.get("externalIds") or {}
                publication_date = normalize_date(item.get("publicationDate") or item.get("releaseDate"))
                update_date = normalize_date(item.get("updatedAt") or item.get("updated_at"))
                record = make_paper_record(
                    title=title, authors=[author.get("name", "") for author in item.get("authors", []) if author.get("name")],
                    abstract=item.get("abstract") or "", source="semantic_scholar", source_url=source_url,
                    pdf_url=(item.get("openAccessPdf") or {}).get("url"), paper_id=item.get("paperId"),
                    arxiv_id=external.get("ArXiv"), doi=external.get("DOI"), venue=item.get("venue"),
                    publication_date=publication_date, update_date=update_date, categories=["semantic_scholar"],
                    source_query_family=request.family_id, source_query_text=request.query_text,
                    retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
                )
                seen.add(source_url)
                normalized.append(record)
                if self.config.get("exclude_year_only_from_since_window", True) and item.get("year") and not publication_date and not update_date:
                    skipped_year_only += 1
                    continue
                if within_since(record.publication_date, record.update_date, context.since):
                    filtered.append(record)
        if skipped_year_only:
            context.add_warning(
                f"{self.name}: skipped {skipped_year_only} year-only record(s) without publicationDate/updatedAt",
                self.name,
            )
        context.set_source_counts(
            self.name,
            raw=raw_count,
            normalized=len(normalized),
            date_filtered=len(filtered),
        )
        return filtered
