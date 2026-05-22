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
            context.warnings.append("dry-run: skipped arXiv network request")
            return []

        categories = self.config.get("categories", [])
        max_results = min(int(self.config.get("max_results", 50)), 50)
        query_terms = [
            '"lattice cryptography"',
            "LWE",
            "Ring-LWE",
            "Module-LWE",
            "SIS",
            "NTRU",
            "BKZ",
            "ML-KEM",
            "ML-DSA",
            "FHE",
            "Kyber",
            "Dilithium",
            "Falcon",
        ]
        category_query = " OR ".join(f"cat:{category}" for category in categories)
        term_query = " OR ".join(f"all:{term}" for term in query_terms)
        search_query = f"({category_query}) AND ({term_query})" if category_query else term_query
        params = urllib.parse.urlencode(
            {
                "search_query": search_query,
                "sortBy": "lastUpdatedDate",
                "sortOrder": "descending",
                "max_results": max_results,
            }
        )
        xml_text = fetch_text(context, f"{self.config['url']}?{params}", source_name=self.name)
        if xml_text is None:
            return []
        return [
            record
            for record in parse_arxiv_atom(xml_text)
            if within_since(record.publication_date, record.update_date, context.since)
        ]
