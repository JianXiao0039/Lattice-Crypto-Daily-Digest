from __future__ import annotations

import re
import urllib.parse
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime, timezone

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_text, normalize_date
from lattice_digest.text import normalize_whitespace
from lattice_digest.source_queries import fair_query_schedule, QueryRequest, critical_query_requests, stable_query_id
from lattice_digest.source_completeness import arxiv_page_bounds, bounded_page_budget, record_source_coverage

ARXIV_ID_RE = re.compile(r"arxiv\.org/abs/([^?#]+)", re.IGNORECASE)
VERSION_RE = re.compile(r"v\d+$")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ET.Element, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in element:
        if _local_name(child.tag) in wanted and child.text:
            return normalize_whitespace(child.text)
    return ""


def _extract_arxiv_id(value: str) -> str | None:
    match = ARXIV_ID_RE.search(value or "")
    if not match:
        return None
    return VERSION_RE.sub("", match.group(1))


def _format_query_term(term: object) -> str:
    raw = str(term).strip()
    if not raw:
        return ""
    if " " in raw and not (raw.startswith('"') and raw.endswith('"')):
        raw = f'"{raw}"'
    return f"all:{raw}"


def _default_query_groups() -> list[list[str]]:
    return [
        ["lattice cryptography"],
        ["Learning with Errors"],
        ["Ring-LWE", "RLWE"],
        ["Module-LWE", "MLWE"],
        ["SIS", "Short Integer Solution"],
        ["Kyber", "ML-KEM"],
        ["Dilithium", "ML-DSA"],
        ["BKZ", "lattice reduction"],
        ["neural lattice reduction"],
        ["Transformer LWE"],
        ["LWQ", "ILWE", "CILWE", "hinted ISIS", "ternary SIS"],
        ["Module-BKZ", "q-ary lattice", "FFT dual attack", "MATZOV"],
        ["Mitaka", "FN-DSA", "NTRU+", "lattice polynomial commitment"],
    ]


def _query_groups(config: dict) -> list[list[str]]:
    configured = config.get("query_groups")
    if configured:
        groups: list[list[str]] = []
        for group in configured:
            if isinstance(group, str):
                groups.append([group])
            else:
                groups.append([str(term) for term in group if str(term).strip()])
        return [group for group in groups if group]
    return _default_query_groups()


def parse_arxiv_atom(xml_text: str) -> list[PaperRecord]:
    root = ET.fromstring(xml_text)
    records: list[PaperRecord] = []
    entries = [element for element in root.iter() if _local_name(element.tag) == "entry"]
    for entry in entries:
        title = _child_text(entry, "title")
        abstract = _child_text(entry, "summary")
        source_url = _child_text(entry, "id")
        authors = []
        categories = []
        pdf_url = None
        doi = None
        for child in entry:
            local = _local_name(child.tag)
            if local == "author":
                name = _child_text(child, "name")
                if name:
                    authors.append(name)
            elif local == "category" and child.attrib.get("term"):
                categories.append(child.attrib["term"])
            elif local == "link":
                if child.attrib.get("type") == "application/pdf" or child.attrib.get("title") == "pdf":
                    pdf_url = child.attrib.get("href")
            elif local == "doi" and child.text:
                doi = normalize_whitespace(child.text)
        arxiv_id = _extract_arxiv_id(source_url)
        if not title or not source_url:
            continue
        published_text = _child_text(entry, "published")
        updated_text = _child_text(entry, "updated")
        records.append(
            make_paper_record(
                title=title,
                authors=authors,
                abstract=abstract,
                source="arxiv",
                source_url=source_url,
                pdf_url=pdf_url,
                paper_id=f"arxiv:{arxiv_id}" if arxiv_id else source_url,
                arxiv_id=arxiv_id,
                doi=doi,
                venue="arXiv",
                publication_date=normalize_date(published_text),
                publication_timestamp=published_text or None,
                publication_date_kind="AUTHORITATIVE_PUBLICATION_DATE",
                update_date=normalize_date(updated_text),
                update_timestamp=updated_text or None,
                update_date_kind="AUTHORITATIVE_CONTENT_REVISION_DATE",
                categories=categories,
            )
        )
    return records


class ArxivSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        if context.dry_run:
            context.add_warning("dry-run: skipped arXiv network request", self.name)
            return []

        categories = self.config.get("categories", [])
        per_group_results = min(
            max(1, int(self.config.get("per_query_results", self.config.get("per_group_results", 25)))),
            25,
        )
        per_query_pages = bounded_page_budget(self.config, "max_pages_per_query", default=2, maximum=8)
        total_page_budget = bounded_page_budget(self.config, "max_total_pages", default=48, maximum=128)
        category_query = " OR ".join(f"cat:{category}" for category in categories)
        groups = _query_groups(self.config)
        legacy_requests = [
            QueryRequest(
                f"legacy_arxiv_{index + 1:02d}",
                " OR ".join(term for term in (_format_query_term(term) for term in group) if term),
                source_family=self.name,
                query_id=stable_query_id(self.name, f"legacy_arxiv_{index + 1:02d}", version=str(self.config.get("query_portfolio_version") or "v1")),
                native_syntax="arxiv",
            )
            for index, group in enumerate(groups)
        ]
        requests = critical_query_requests(self.config, syntax="arxiv") + legacy_requests
        requests = fair_query_schedule(requests, rotation=context.since.date().toordinal())
        context.checkpoint('QUERY_SCHEDULE', {'source': self.name, 'policy': 'PRODUCTION_FAMILY_ROUND_ROBIN',
                                           'query_ids': [r.query_id for r in requests]})
        health = context.health(self.name)
        health.query_groups_total = len(requests)
        raw_count = 0
        normalized_by_key: dict[str, PaperRecord] = {}
        # First visit every expression, then spend remaining pages on pagination.
        # This retains family fairness when one broad expression has a long tail.
        pending = deque()
        for request in requests:
            attempt_id = context.begin_query_attempt(self.name, request)
            if not request.query_text:
                context.finish_query_attempt(attempt_id, status="failed", error_category="empty_query")
                health.query_groups_failed += 1
                continue
            pending.append({"request": request, "attempt_id": attempt_id, "start": 0, "pages": 0, "raw": 0, "total": None, "page_keys": set()})
        pages_used = 0
        coverage_partial = False
        exhausted_queries = 0
        while pending:
            state = pending.popleft()
            request, attempt_id = state["request"], state["attempt_id"]
            if state["pages"] >= per_query_pages:
                coverage_partial = True
                record_source_coverage(context, self.name, state="SOURCE_PARTIAL", reason="ARXIV_QUERY_PAGE_BUDGET_EXHAUSTED",
                                       query_id=request.query_id, pages=state["pages"], observed_items=None)
                context.finish_query_attempt(attempt_id, status="skipped_by_budget", raw_candidates=None, error_category="page_budget")
                continue
            if pages_used >= total_page_budget:
                coverage_partial = True
                record_source_coverage(context, self.name, state="SOURCE_PARTIAL", reason="ARXIV_TOTAL_PAGE_BUDGET_EXHAUSTED",
                                       pages_used=pages_used, pages_budget=total_page_budget, pending_queries=1 + len(pending))
                for unfinished in [state, *pending]:
                    context.finish_query_attempt(unfinished["attempt_id"], status="partial" if unfinished["pages"] else "skipped_by_budget",
                                                 raw_candidates=unfinished["raw"] if unfinished["pages"] else None,
                                                 error_category="page_budget")
                break
            term_query = request.query_text
            search_query = f"({category_query}) AND ({term_query})" if category_query else term_query
            params = urllib.parse.urlencode(
                {
                    "search_query": search_query,
                    "sortBy": "lastUpdatedDate",
                    "sortOrder": "descending",
                    "max_results": per_group_results,
                    "start": state["start"],
                }
            )
            diagnostic_start = len(health.request_diagnostics)
            xml_text = fetch_text(context, f"{self.config['url']}?{params}", source_name=self.name)
            # The shared transport defaults to the most recently scheduled query.
            # Pagination revisits earlier queries, so bind this page explicitly.
            for diagnostic in health.request_diagnostics[diagnostic_start:]:
                if "attempt_id" in diagnostic:
                    diagnostic.update(attempt_id=attempt_id, query_id=request.query_id, pagination_start=state["start"])
            pages_used += 1
            if xml_text is None:
                coverage_partial = True
                context.finish_query_attempt(attempt_id, status="partial" if state["pages"] else "failed",
                                             raw_candidates=state["raw"] if state["pages"] else None, error_category=health.error_type())
                health.query_groups_failed += 1
                continue
            try:
                root = ET.fromstring(xml_text)
                if root.tag != '{http://www.w3.org/2005/Atom}feed':
                    raise ET.ParseError('expected arXiv Atom feed, received another document')
                if any('arxiv.org/api/errors' in _child_text(element, 'id') for element in root if _local_name(element.tag) == 'entry'):
                    raise ET.ParseError('arXiv API returned an error entry')
                group_raw_count = sum(1 for element in root.iter() if _local_name(element.tag) == "entry")
                group_records = parse_arxiv_atom(xml_text)
            except ET.ParseError as exc:
                coverage_partial = True
                health.query_groups_failed += 1
                context.add_warning(f"{self.name}: failed to parse arXiv query group {request.family_id}: {exc}", self.name)
                context.finish_query_attempt(attempt_id, status="partial" if state["pages"] else "failed",
                                             raw_candidates=state["raw"] if state["pages"] else None, error_category="parse_error")
                continue
            raw_count += group_raw_count
            state["pages"] += 1
            state["raw"] += group_raw_count
            for record in group_records:
                occurrence_id = context.record_raw_occurrence(
                    self.name,
                    attempt_id,
                    raw_title=record.title,
                    source_identifier=record.arxiv_id or record.paper_id,
                    source_url=record.source_url,
                    publication_date=record.publication_date,
                    update_date=record.update_date,
                    abstract_present=bool(record.abstract),
                    parser_result="PARSED",
                )
                record = record.model_copy(
                    update={
                        "source_query_family": request.family_id,
                        "source_query_text": request.query_text,
                        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
                        "raw_occurrence_ids": [occurrence_id],
                        "query_ids": [request.query_id],
                    }
                )
                context.record_normalized_candidate(occurrence_id, record)
                key = record.arxiv_id or record.source_url or record.title.lower()
                normalized_by_key.setdefault(key, record)
            total, coverage_reason = arxiv_page_bounds(root, requested_start=state["start"], entries=group_raw_count)
            if state["total"] is not None and total != state["total"]:
                coverage_reason = "ARXIV_RESULTS_CHANGED_DURING_PAGINATION"
            state["total"] = total
            if len(group_records) != group_raw_count:
                coverage_reason = "ARXIV_UNPARSED_ENTRIES"
            page_key = tuple((record.arxiv_id or record.source_url) for record in group_records)
            if group_raw_count and page_key in state["page_keys"]:
                coverage_reason = "ARXIV_REPEATED_PAGE"
            state["page_keys"].add(page_key)
            if coverage_reason:
                coverage_partial = True
                # A valid parsed response remains a successful transport query;
                # missing metadata must not become a false query-zero outcome.
                context.finish_query_attempt(attempt_id, status="success" if coverage_reason == "ARXIV_PAGINATION_METADATA_MISSING" and state["raw"] else "partial",
                                             raw_candidates=state["raw"], error_category=coverage_reason)
                health.query_groups_success += 1
                record_source_coverage(context, self.name, state="SOURCE_PARTIAL", reason=coverage_reason,
                                       query_id=request.query_id, pages=state["pages"], observed_items=state["raw"], total_results=total)
                continue
            if state["start"] + group_raw_count >= total:
                exhausted_queries += 1
                health.query_groups_success += 1
                context.finish_query_attempt(attempt_id, status="success", raw_candidates=state["raw"])
            elif state["pages"] >= per_query_pages:
                coverage_partial = True
                health.query_groups_success += 1
                context.finish_query_attempt(attempt_id, status="partial", raw_candidates=state["raw"], error_category="page_budget")
                record_source_coverage(context, self.name, state="SOURCE_PARTIAL", reason="ARXIV_QUERY_PAGE_BUDGET_EXHAUSTED",
                                       query_id=request.query_id, pages=state["pages"], observed_items=state["raw"], total_results=total)
            else:
                state["start"] += group_raw_count
                pending.append(state)
        normalized = list(normalized_by_key.values())
        context.set_source_counts(
            self.name,
            raw=raw_count,
            normalized=len(normalized),
            observability=len(normalized),
            date_filtered=0,
        )
        overall_state = "SOURCE_PARTIAL" if coverage_partial or exhausted_queries != len(requests) else "SOURCE_COMPLETE"
        if not health.query_groups_success and not normalized:
            overall_state = "SOURCE_UNAVAILABLE"
        record_source_coverage(context, self.name, state=overall_state,
                               reason="ARXIV_SOURCE_UNAVAILABLE" if overall_state == "SOURCE_UNAVAILABLE" else "ARXIV_QUERY_COVERAGE_PARTIAL" if overall_state == "SOURCE_PARTIAL" else "ARXIV_QUERY_EXPRESSIONS_EXHAUSTED",
                               scope="CONFIGURED_QUERY_EXPRESSIONS_NOT_ALL_ARXIV", pages_used=pages_used,
                               query_count=len(requests), exhausted_queries=exhausted_queries,
                               requested_since=context.since.isoformat(), source_time_filter_applied=False,
                               result_sort="lastUpdatedDate_descending")
        return normalized
