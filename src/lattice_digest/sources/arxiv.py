from __future__ import annotations

import re
import urllib.parse
import xml.etree.ElementTree as ET

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_text, normalize_date, within_since
from lattice_digest.text import normalize_whitespace

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
                publication_date=normalize_date(_child_text(entry, "published")),
                update_date=normalize_date(_child_text(entry, "updated")),
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
            int(self.config.get("per_query_results", self.config.get("per_group_results", 25))),
            25,
        )
        category_query = " OR ".join(f"cat:{category}" for category in categories)
        groups = _query_groups(self.config)
        health = context.health(self.name)
        health.query_groups_total = len(groups)
        raw_count = 0
        normalized_by_key: dict[str, PaperRecord] = {}
        for group in groups:
            term_query = " OR ".join(term for term in (_format_query_term(term) for term in group) if term)
            if not term_query:
                continue
            search_query = f"({category_query}) AND ({term_query})" if category_query else term_query
            params = urllib.parse.urlencode(
                {
                    "search_query": search_query,
                    "sortBy": "lastUpdatedDate",
                    "sortOrder": "descending",
                    "max_results": per_group_results,
                }
            )
            xml_text = fetch_text(context, f"{self.config['url']}?{params}", source_name=self.name)
            if xml_text is None:
                health.query_groups_failed += 1
                continue
            try:
                root = ET.fromstring(xml_text)
                group_raw_count = sum(1 for element in root.iter() if _local_name(element.tag) == "entry")
                group_records = parse_arxiv_atom(xml_text)
            except ET.ParseError as exc:
                health.query_groups_failed += 1
                context.add_warning(f"{self.name}: failed to parse arXiv query group {group}: {exc}", self.name)
                continue
            raw_count += group_raw_count
            health.query_groups_success += 1
            for record in group_records:
                key = record.arxiv_id or record.source_url or record.title.lower()
                normalized_by_key.setdefault(key, record)
        normalized = list(normalized_by_key.values())
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
