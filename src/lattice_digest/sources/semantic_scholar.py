from __future__ import annotations

import urllib.parse

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_json, normalize_date, within_since


class SemanticScholarSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        if context.dry_run:
            context.warnings.append("dry-run: skipped Semantic Scholar network request")
            return []
        fields = "paperId,title,abstract,authors,venue,year,publicationDate,externalIds,url,openAccessPdf"
        api_key = context.api_keys.get("SEMANTIC_SCHOLAR_API_KEY")
        configured_limit = int(self.config.get("max_results", 50))
        limit = configured_limit if api_key else min(configured_limit, 20)
        params = urllib.parse.urlencode(
            {
                "query": "lattice cryptography LWE SIS NTRU BKZ FHE",
                "limit": limit,
                "fields": fields,
            }
        )
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
        data = fetch_json(context, f"{self.config['url']}?{params}", headers=headers, source_name=self.name)
        if data is None:
            return []
        records: list[PaperRecord] = []
        for item in data.get("data", []):
            title = item.get("title")
            source_url = item.get("url")
            if not title or not source_url:
                continue
            external = item.get("externalIds") or {}
            record = make_paper_record(
                title=title,
                authors=[author.get("name", "") for author in item.get("authors", []) if author.get("name")],
                abstract=item.get("abstract") or "",
                source="semantic_scholar",
                source_url=source_url,
                pdf_url=(item.get("openAccessPdf") or {}).get("url"),
                paper_id=item.get("paperId"),
                arxiv_id=external.get("ArXiv"),
                doi=external.get("DOI"),
                venue=item.get("venue"),
                publication_date=normalize_date(item.get("publicationDate") or str(item.get("year") or "")),
                categories=["semantic_scholar"],
            )
            if within_since(record.publication_date, record.update_date, context.since):
                records.append(record)
        return records
