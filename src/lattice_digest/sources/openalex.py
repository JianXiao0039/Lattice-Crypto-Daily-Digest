from __future__ import annotations

import urllib.parse

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_json, normalize_date, within_since


def _abstract_from_inverted_index(index: dict | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, offsets in index.items():
        for offset in offsets:
            positions.append((int(offset), word))
    return " ".join(word for _, word in sorted(positions))


class OpenAlexSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        if context.dry_run:
            context.warnings.append("dry-run: skipped OpenAlex network request")
            return []
        params = urllib.parse.urlencode(
            {
                "search": "lattice cryptography LWE SIS NTRU BKZ FHE",
                "per-page": int(self.config.get("max_results", 50)),
                "sort": "updated_date:desc",
            }
        )
        data = fetch_json(context, f"{self.config['url']}?{params}")
        records: list[PaperRecord] = []
        for item in data.get("results", []):
            title = item.get("title")
            source_url = item.get("doi") or item.get("id")
            if not title or not source_url:
                continue
            authors = [
                authorship.get("author", {}).get("display_name", "")
                for authorship in item.get("authorships", [])
            ]
            record = make_paper_record(
                title=title,
                authors=[author for author in authors if author],
                abstract=_abstract_from_inverted_index(item.get("abstract_inverted_index")),
                source="openalex",
                source_url=source_url,
                paper_id=item.get("id"),
                doi=item.get("doi"),
                venue=(item.get("primary_location") or {}).get("source", {}).get("display_name"),
                publication_date=normalize_date(item.get("publication_date")),
                update_date=normalize_date(item.get("updated_date")),
                categories=["openalex"],
            )
            if within_since(record.publication_date, record.update_date, context.since):
                records.append(record)
        return records

