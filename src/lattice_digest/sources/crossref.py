from __future__ import annotations

import html
import re
import urllib.parse

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_json, normalize_date
from lattice_digest.text import normalize_whitespace

TAG_RE = re.compile(r"<[^>]+>")


class CrossrefSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        if context.dry_run:
            context.warnings.append("dry-run: skipped Crossref network request")
            return []
        params = urllib.parse.urlencode(
            {
                "query.bibliographic": "lattice cryptography LWE SIS NTRU BKZ FHE",
                "rows": int(self.config.get("max_results", 50)),
                "sort": "published",
                "order": "desc",
            }
        )
        data = fetch_json(context, f"{self.config['url']}?{params}")
        records: list[PaperRecord] = []
        for item in data.get("message", {}).get("items", []):
            titles = item.get("title") or []
            title = titles[0] if titles else None
            doi = item.get("DOI")
            source_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)
            if not title or not source_url:
                continue
            authors = [
                " ".join(part for part in [author.get("given"), author.get("family")] if part)
                for author in item.get("author", [])
            ]
            abstract = normalize_whitespace(TAG_RE.sub(" ", html.unescape(item.get("abstract") or "")))
            date_parts = (item.get("published-print") or item.get("published-online") or item.get("created") or {}).get("date-parts", [])
            date_text = "-".join(str(part) for part in date_parts[0]) if date_parts else None
            records.append(
                make_paper_record(
                    title=title,
                    authors=[author for author in authors if author],
                    abstract=abstract,
                    source="crossref",
                    source_url=source_url,
                    paper_id=doi or source_url,
                    doi=doi,
                    venue=(item.get("container-title") or [None])[0],
                    publication_date=normalize_date(date_text),
                    categories=["crossref"],
                )
            )
        return records

