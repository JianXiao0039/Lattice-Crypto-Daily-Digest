from __future__ import annotations

import urllib.parse

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_json, normalize_date, within_since


class DblpSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        if context.dry_run:
            context.warnings.append("dry-run: skipped DBLP network request")
            return []
        records: list[PaperRecord] = []
        seen_urls: set[str] = set()
        queries = self.config.get("queries") or ["lattice cryptography LWE SIS NTRU BKZ"]
        per_query = int(self.config.get("per_query_results", self.config.get("max_results", 50)))
        per_query = min(per_query, int(self.config.get("max_results", 50)))
        for query in queries:
            params = urllib.parse.urlencode(
                {
                    "q": str(query),
                    "format": "json",
                    "h": per_query,
                }
            )
            data = fetch_json(context, f"{self.config['url']}?{params}", source_name=self.name)
            if data is None:
                continue
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            for hit in hits:
                info = hit.get("info", {})
                title = info.get("title")
                url = info.get("url") or info.get("ee")
                if not title or not url or url in seen_urls:
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
                )
                if within_since(record.publication_date, record.update_date, context.since):
                    seen_urls.add(url)
                    records.append(record)
        return records
