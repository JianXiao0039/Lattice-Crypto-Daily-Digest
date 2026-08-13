from __future__ import annotations

import urllib.parse
from datetime import datetime, timezone

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_json, normalize_date, within_since
from lattice_digest.source_queries import critical_query_requests, legacy_query_requests


def _abstract_from_inverted_index(index: dict | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, offsets in index.items():
        for offset in offsets:
            positions.append((int(offset), word))
    return " ".join(word for _, word in sorted(positions))


def _sort_key(record: PaperRecord) -> datetime:
    for value in (record.update_date, record.publication_date):
        if value:
            try:
                return datetime.fromisoformat(value[:10]).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return datetime.min.replace(tzinfo=timezone.utc)


class OpenAlexSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        if context.dry_run:
            context.add_warning("dry-run: skipped OpenAlex network request", self.name)
            return []
        requests = critical_query_requests(self.config, syntax="plain")
        requests.extend(legacy_query_requests(self.config, keys=("query_groups", "query_terms")))
        if not requests:
            requests = legacy_query_requests({"query_terms": ["lattice cryptography LWE SIS NTRU BKZ FHE"]}, keys=("query_terms",))
        health = context.health(self.name)
        health.query_groups_total = len(requests)
        contact_email = context.api_keys.get("CONTACT_EMAIL", "").strip()
        headers = {}
        if contact_email:
            headers["User-Agent"] = f"{context.user_agent} (mailto:{contact_email})"
        normalized: list[PaperRecord] = []
        seen: set[str] = set()
        raw_count = 0
        for request in requests:
            attempt_id = context.begin_query_attempt(self.name, request)
            params = urllib.parse.urlencode({"search": request.query_text, "per-page": min(int(self.config.get("max_results", 25)), 25)})
            if contact_email:
                params = f"{params}&{urllib.parse.urlencode({'mailto': contact_email})}"
            data = fetch_json(context, f"{self.config['url']}?{params}", headers=headers, source_name=self.name)
            if data is None:
                context.finish_query_attempt(attempt_id, status="failed", raw_candidates=None, error_category=health.error_type())
                health.query_groups_failed += 1
                continue
            health.query_groups_success += 1
            results = data.get("results", [])
            context.finish_query_attempt(attempt_id, status="success", raw_candidates=len(results))
            raw_count += len(results)
            for item in results:
                title = item.get("title")
                source_url = item.get("doi") or item.get("id")
                abstract = _abstract_from_inverted_index(item.get("abstract_inverted_index"))
                occurrence_id = context.record_raw_occurrence(
                    self.name,
                    attempt_id,
                    raw_title=str(title or ""),
                    source_identifier=item.get("id") or item.get("doi"),
                    source_url=source_url,
                    publication_date=item.get("publication_date"),
                    update_date=item.get("updated_date"),
                    abstract_present=bool(abstract),
                    parser_result="PARSED" if title and source_url else "RAW_PARSE_FAILED",
                    parser_failure_reason=None if title and source_url else "missing title or source URL",
                    normalization_eligible=bool(title and source_url),
                )
                if not title or not source_url:
                    continue
                if source_url in seen:
                    context.record_route_event("raw_occurrence", occurrence_id, "DEDUP", "DUPLICATE_WITHIN_SOURCE", "same OpenAlex work returned by another query", terminal=True)
                    continue
                authors = [authorship.get("author", {}).get("display_name", "") for authorship in item.get("authorships", [])]
                record = make_paper_record(
                    title=title, authors=[author for author in authors if author],
                    abstract=abstract, source="openalex",
                    source_url=source_url, paper_id=item.get("id"), doi=item.get("doi"),
                    venue=((item.get("primary_location") or {}).get("source") or {}).get("display_name"),
                    publication_date=normalize_date(item.get("publication_date")), update_date=normalize_date(item.get("updated_date")),
                    categories=["openalex"], source_query_family=request.family_id, source_query_text=request.query_text,
                    retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
                )
                context.record_normalized_candidate(occurrence_id, record)
                seen.add(source_url)
                normalized.append(record)
        filtered = [
            record
            for record in normalized
            if within_since(record.publication_date, record.update_date, context.since)
        ]
        filtered.sort(key=_sort_key, reverse=True)
        context.set_source_counts(
            self.name,
            raw=raw_count,
            normalized=len(normalized),
            date_filtered=len(filtered),
        )
        return filtered
