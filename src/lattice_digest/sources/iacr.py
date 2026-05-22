from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_text, normalize_date, within_since
from lattice_digest.text import normalize_whitespace

EPRINT_RE = re.compile(r"eprint\.iacr\.org/(?:eprint-bin/)?(?:archive/)?(\d{4}/\d+)", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ET.Element, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in element:
        if _local_name(child.tag) in wanted and child.text:
            return normalize_whitespace(html.unescape(child.text))
    return ""


def _all_child_text(element: ET.Element, name: str) -> list[str]:
    found = []
    for child in element:
        if _local_name(child.tag) == name.lower() and child.text:
            found.append(normalize_whitespace(html.unescape(child.text)))
    return found


def _clean_abstract(value: str) -> str:
    return normalize_whitespace(TAG_RE.sub(" ", html.unescape(value or "")))


def _extract_eprint_id(*values: str) -> str | None:
    for value in values:
        match = EPRINT_RE.search(value or "")
        if match:
            return match.group(1)
    joined = " ".join(values)
    match = re.search(r"\b(\d{4}/\d{3,5})\b", joined)
    return match.group(1) if match else None


def parse_iacr_feed(xml_text: str, source_url: str = "https://eprint.iacr.org/rss/rss.xml") -> list[PaperRecord]:
    root = ET.fromstring(xml_text)
    records: list[PaperRecord] = []

    rss_items = root.findall(".//item")
    atom_entries = [element for element in root.iter() if _local_name(element.tag) == "entry"]
    items = rss_items or atom_entries

    for item in items:
        title = _child_text(item, "title")
        link = _child_text(item, "link", "id")
        if not link:
            for child in item:
                if _local_name(child.tag) == "link" and child.attrib.get("href"):
                    link = child.attrib["href"]
                    break
        abstract = _clean_abstract(_child_text(item, "description", "summary", "abstract"))
        authors = _all_child_text(item, "creator")
        for child in item:
            if _local_name(child.tag) == "author":
                author_name = _child_text(child, "name") or normalize_whitespace(child.text)
                if author_name:
                    authors.append(author_name)
        publication_date = normalize_date(_child_text(item, "pubdate", "published", "date"))
        update_date = normalize_date(_child_text(item, "updated"))
        eprint_id = _extract_eprint_id(link, title)
        pdf_url = f"https://eprint.iacr.org/{eprint_id}.pdf" if eprint_id else None
        if not title or not link:
            continue
        records.append(
            make_paper_record(
                title=title,
                authors=list(dict.fromkeys(authors)),
                abstract=abstract,
                source="iacr_eprint",
                source_url=link,
                pdf_url=pdf_url,
                paper_id=f"iacr:{eprint_id}" if eprint_id else link,
                eprint_id=eprint_id,
                venue="IACR ePrint",
                publication_date=publication_date,
                update_date=update_date,
                categories=["iacr_eprint"],
            )
        )
    return records


class IacrEprintSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        url = self.config["url"]
        if context.dry_run:
            context.warnings.append("dry-run: skipped IACR ePrint network request")
            return []

        assert context.cache_dir is not None
        context.cache_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.now(timezone.utc).date().isoformat()
        cache_path = context.cache_dir / f"iacr_eprint_{today}.xml"
        attempt_path = context.cache_dir / f"iacr_eprint_{today}.attempt"

        if cache_path.exists():
            xml_text = cache_path.read_text(encoding="utf-8")
        elif attempt_path.exists():
            context.warnings.append("IACR ePrint already requested today; skipped to honor max once per day")
            return []
        else:
            attempt_path.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
            xml_text = fetch_text(context, url, source_name=self.name)
            if xml_text is None:
                return []
            cache_path.write_text(xml_text, encoding="utf-8")

        return [
            record
            for record in parse_iacr_feed(xml_text, source_url=url)
            if within_since(record.publication_date, record.update_date, context.since)
        ]
