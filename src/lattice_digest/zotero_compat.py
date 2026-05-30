from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from lattice_digest.export_library import (
    clean_text,
    clean_url,
    dedup_key_for_record,
    filter_items,
    merge_items,
    record_to_library_item,
)
from lattice_digest.ideas import normalize_key, short_hash


SECRET_PATTERNS = (
    r"ghp_[A-Za-z0-9_]+",
    r"github_pat_[A-Za-z0-9_]+",
    r"sk-[A-Za-z0-9_-]+",
    r"xoxb-[A-Za-z0-9-]+",
    r"AKIA[0-9A-Z]+",
)
POLLUTION_MARKERS = ("contentReference", "oaicite", "id=")

FORMAT_ALIASES = {
    "all": ("zotero-json", "csl-json", "bibtex", "ris", "collections", "report"),
    "zotero": ("zotero-json",),
    "zotero-json": ("zotero-json",),
    "json": ("zotero-json",),
    "csl": ("csl-json",),
    "csl-json": ("csl-json",),
    "bib": ("bibtex",),
    "bibtex": ("bibtex",),
    "ris": ("ris",),
    "collections": ("collections",),
    "report": ("report",),
}


@dataclass(frozen=True)
class ZoteroExportResult:
    items: list[dict[str, Any]]
    zotero_items: list[dict[str, Any]]
    output_dir: Path
    run_dir: Path
    formats: list[str]
    written_paths: list[Path]
    dry_run: bool = False


def _stable(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, dict):
                item = item.get("name") or item.get("literal") or item.get("family") or ""
            cleaned = clean_text(item)
            if cleaned:
                result.append(cleaned)
        return _stable(result)
    if isinstance(value, str):
        if " and " in value:
            parts = value.split(" and ")
        elif ";" in value:
            parts = value.split(";")
        else:
            parts = [value]
        return _stable(clean_text(part) for part in parts if clean_text(part))
    return []


def _split_csv(values: Iterable[str] | str | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    result: list[str] = []
    for value in values:
        for part in str(value).split(","):
            cleaned = clean_text(part)
            if cleaned:
                result.append(cleaned)
    return _stable(result)


def _clean_output_text(value: object) -> str:
    text = clean_text(value)
    for marker in POLLUTION_MARKERS:
        text = text.replace(marker, "")
    for pattern in SECRET_PATTERNS:
        text = re.sub(pattern, "[REDACTED_SECRET]", text)
    return re.sub(r"\s+", " ", text).strip()


def _year(value: object) -> int | None:
    if isinstance(value, int):
        return value
    match = re.search(r"(19|20)\d{2}", clean_text(value))
    return int(match.group(0)) if match else None


def _date_parts(value: object, year: int | None = None) -> dict[str, Any] | None:
    text = clean_text(value)
    if text:
        parts = [int(part) for part in re.findall(r"\d+", text[:10])[:3]]
        if parts:
            return {"date-parts": [parts]}
    if year:
        return {"date-parts": [[year]]}
    return None


def _input_files(input_dir: Path, from_date: str | None, to_date: str | None) -> list[Path]:
    if input_dir.is_file():
        candidates = [input_dir]
    else:
        candidates = sorted(input_dir.glob("*.json"))
    selected: list[Path] = []
    for path in candidates:
        day = path.stem[:10]
        if from_date and day < from_date:
            continue
        if to_date and day > to_date:
            continue
        selected.append(path)
    return selected


def _metadata_from_payload(payload: object, path: Path) -> dict[str, str]:
    metadata: dict[str, Any] = {}
    if isinstance(payload, dict) and isinstance(payload.get("metadata"), dict):
        metadata = payload["metadata"]
    target_date = clean_text(metadata.get("target_date") or metadata.get("run_date") or path.stem[:10])[:10]
    return {
        "digest_date": target_date,
        "collector": clean_text(metadata.get("collector")),
        "quality_status": clean_text(metadata.get("quality_status")),
        "run_mode": clean_text(metadata.get("run_mode")),
    }


def _load_items_with_metadata(
    input_dir: Path,
    *,
    from_date: str | None,
    to_date: str | None,
    include_provisional: bool,
    dedup: bool = True,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    deduped: dict[str, dict[str, Any]] = {}
    for path in _input_files(input_dir, from_date, to_date):
        payload = json.loads(path.read_text(encoding="utf-8"))
        meta = _metadata_from_payload(payload, path)
        if not include_provisional and meta.get("quality_status") == "provisional":
            continue
        records = payload if isinstance(payload, list) else payload.get("records", []) if isinstance(payload, dict) else []
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            item = record_to_library_item(record, meta["digest_date"])
            item["collector"] = clean_text(record.get("collector") or meta.get("collector"))
            item["quality_status"] = clean_text(record.get("quality_status") or meta.get("quality_status"))
            item["run_mode"] = clean_text(record.get("run_mode") or meta.get("run_mode"))
            if dedup:
                key = str(item["dedup_key"])
                deduped[key] = merge_items(deduped[key], item) if key in deduped else item
            else:
                items.append(item)
    if dedup:
        items = list(deduped.values())
    return sorted(items, key=lambda item: (-int(item.get("reading_priority_score") or 0), str(item.get("title") or "")))


def normalize_authors_to_zotero_creators(record: dict[str, Any]) -> list[dict[str, str]]:
    creators: list[dict[str, str]] = []
    for author in _as_list(record.get("authors")):
        creators.append({"creatorType": "author", "name": _clean_output_text(author)})
    return creators


def normalize_authors_to_csl(record: dict[str, Any]) -> list[dict[str, str]]:
    return [{"literal": _clean_output_text(author)} for author in _as_list(record.get("authors"))]


def infer_zotero_item_type(record: dict[str, Any]) -> str:
    text = normalize_key(" ".join(str(record.get(key) or "") for key in ("source", "source_type", "venue", "title")))
    if any(term in text for term in ("crypto", "eurocrypt", "asiacrypt", "usenix", "ieee s p", "ccs", "ndss", "conference", "proceedings")):
        return "conferencePaper"
    if any(term in text for term in ("journal", "tches", "tosc")):
        return "journalArticle"
    if any(term in text for term in ("iacr", "eprint", "arxiv", "preprint")):
        return "report"
    if record.get("doi") and record.get("venue"):
        return "journalArticle"
    return "report"


def infer_csl_type(record: dict[str, Any]) -> str:
    item_type = infer_zotero_item_type(record)
    if item_type == "conferencePaper":
        return "paper-conference"
    if item_type == "journalArticle":
        return "article-journal"
    if item_type == "webpage":
        return "webpage"
    return "report"


def build_stable_citation_key(record: dict[str, Any]) -> str:
    authors = _as_list(record.get("authors"))
    first = normalize_key(authors[0]).split(" ")[-1] if authors else normalize_key(record.get("source") or "item")
    year = str(record.get("year") or _year(record.get("date")) or "noyear")
    words = [word for word in normalize_key(record.get("title") or "").split() if len(word) > 2][:3]
    short_title = "".join(word.title() for word in words) or "Untitled"
    digest = short_hash(str(record.get("dedup_key") or dedup_key_for_record(record)), 6)
    key = re.sub(r"[^A-Za-z0-9]+", "", f"{first.title()}{year}{short_title}{digest}")
    return key or f"Item{year}{digest}"


def _source_tag(source: str) -> str:
    text = normalize_key(source)
    mapping = {
        "iacr eprint": "LC/Source/IACR-ePrint",
        "iacr_eprint": "LC/Source/IACR-ePrint",
        "arxiv": "LC/Source/arXiv",
        "semantic scholar": "LC/Source/Semantic-Scholar",
        "semantic_scholar": "LC/Source/Semantic-Scholar",
        "openalex": "LC/Source/OpenAlex",
        "crossref": "LC/Source/Crossref",
        "dblp": "LC/Source/DBLP",
    }
    for needle, tag in mapping.items():
        if needle in text:
            return tag
    return "LC/Source/Unknown"


def _priority_tag(label: str, score: int) -> str:
    if label == "必须精读" or score >= 85:
        return "LC/Priority/Must-Read"
    if label == "建议精读" or score >= 70:
        return "LC/Priority/Should-Read"
    if label == "可略读" or score >= 50:
        return "LC/Priority/Skim"
    return "LC/Priority/Stash"


def _collector_tag(collector: str) -> str | None:
    text = normalize_key(collector)
    if "github" in text:
        return "LC/Collector/GitHub-Actions"
    if "local" in text or "codex" in text:
        return "LC/Collector/Local-Codex"
    return None


def _quality_tag(quality: str) -> str | None:
    text = normalize_key(quality)
    if "authoritative backfill" in text or "authoritative_backfill" in quality:
        return "LC/Quality/Authoritative-Backfill"
    if "authoritative" in text:
        return "LC/Quality/Authoritative"
    if "provisional" in text:
        return "LC/Quality/Provisional"
    return None


def _lc_from_tags(item: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    lattice = set(_as_list(item.get("lattice_tags")))
    pqc = set(_as_list(item.get("pqc_tags")))
    attacks = set(_as_list(item.get("attack_tags")))
    primitives = set(_as_list(item.get("primitive_tags")))
    implementation = set(_as_list(item.get("implementation_tags")))
    ai = set(_as_list(item.get("ai_tags")))
    text = normalize_key(" ".join(str(item.get(key) or "") for key in ("title", "abstract", "reason_for_priority", "why_it_matters")))

    for tag in ("LWE", "Ring-LWE", "Module-LWE", "SIS", "Module-SIS", "NTRU"):
        if tag in lattice:
            name = {"Ring-LWE": "RLWE", "Module-LWE": "MLWE"}.get(tag, tag)
            tags.append(f"LC/Problem/{name}")
    if "Module-LWE" in lattice:
        tags.append("LC/Problem/Module-LWE")
    if "Chameleon Hash" in primitives or "Module-SIS Chameleon Hash" in primitives:
        tags.extend(["LC/Primitive/Chameleon-Hash", "LC/ResearchLine/Module-SIS-Chameleon-Hash"])
    if "Commitment" in primitives or any("Commitment" in tag for tag in primitives):
        tags.append("LC/Primitive/Commitment")
    if "KEM" in pqc or "ML-KEM" in pqc or "Kyber" in pqc:
        tags.append("LC/Primitive/KEM")
    if "Signature" in pqc or {"ML-DSA", "Dilithium", "Falcon"} & pqc:
        tags.append("LC/Primitive/Signature")
    if {"ZK-Friendly", "Zero-Knowledge", "Anonymous Credential"} & primitives:
        tags.append("LC/Primitive/ZK-Friendly-PQ")
    for tag in ("ML-KEM", "Kyber", "ML-DSA", "Dilithium"):
        if tag in pqc:
            tags.append(f"LC/Scheme/{tag}")
    if "Primal Attack" in attacks:
        tags.append("LC/Attack/Primal")
    if "Dual Attack" in attacks:
        tags.append("LC/Attack/Dual")
    if "Hybrid Attack" in attacks or "Dual Hybrid Attack" in attacks or "Primal Hybrid Attack" in attacks:
        tags.append("LC/Attack/Hybrid")
    if "BKZ" in lattice:
        tags.append("LC/Attack/BKZ")
    if "LLL" in lattice:
        tags.append("LC/Attack/LLL")
    if "Sieving" in lattice:
        tags.append("LC/Attack/Sieving")
    if "Enumeration" in lattice:
        tags.append("LC/Attack/Enumeration")
    if "G6K" in lattice:
        tags.append("LC/Tool/G6K")
    if "fplll" in lattice:
        tags.append("LC/Tool/fplll")
    if "AI4Lattice" in ai:
        tags.append("LC/AI/AI4Lattice")
    for tag, lc_tag in (
        ("Transformer LWE", "LC/AI/Transformer"),
        ("Swin Transformer", "LC/AI/Swin"),
        ("Mamba", "LC/AI/Mamba"),
        ("VMamba", "LC/AI/VMamba"),
        ("Candidate Ranking", "LC/AI/Ranking"),
        ("Hybrid Ranking", "LC/AI/Ranking"),
        ("Coordinate Selection", "LC/AI/Coordinate-Selection"),
        ("Swin-guided Coordinate Selection", "LC/AI/Coordinate-Selection"),
        ("Negative-Cyclic Modeling", "LC/AI/Negative-Cyclic-Modeling"),
    ):
        if tag in ai:
            tags.append(lc_tag)
    if "AI4Lattice" in ai and ("hybrid" in text or "ranking" in text or "coordinate selection" in text):
        tags.append("LC/ResearchLine/AI4Lattice-Hybrid-Ranking")
    if ("negative cyclic" in text or "negative-cyclic" in text or "negacyclic" in text) and ({"Ring-LWE", "Module-LWE"} & lattice):
        tags.append("LC/ResearchLine/RLWE-MLWE-Negative-Cyclic")
    if "Constant-Time" in implementation:
        tags.append("LC/Implementation/Constant-Time")
    if "Side-Channel" in implementation:
        tags.append("LC/Implementation/Side-Channel")
    if "Fault Attack" in implementation or "Fault Injection" in implementation:
        tags.append("LC/Implementation/Fault-Attack")
    if ({"ML-KEM", "ML-DSA", "Kyber", "Dilithium"} & pqc) and (
        {"Side-Channel", "Fault Attack", "Fault Injection", "Constant-Time", "Implementation Audit", "Production Audit"} & implementation
    ):
        tags.append("LC/ResearchLine/PQC-Implementation-Security")
    return tags


def _ensure_library_like(record: dict[str, Any]) -> dict[str, Any]:
    category_keys = (
        "lattice_tags",
        "pqc_tags",
        "ai_tags",
        "attack_tags",
        "primitive_tags",
        "implementation_tags",
        "zotero_tags",
    )
    if any(record.get(key) for key in category_keys):
        return record
    converted = record_to_library_item(record, "")
    for key in ("collector", "quality_status", "run_mode"):
        if record.get(key):
            converted[key] = record[key]
    return converted


def build_zotero_tags(record: dict[str, Any]) -> list[dict[str, str]]:
    record = _ensure_library_like(record)
    score = int(record.get("reading_priority_score") or 0)
    raw_tags = [
        *_lc_from_tags(record),
        _priority_tag(str(record.get("priority_label") or ""), score),
        _source_tag(str(record.get("source") or "")),
    ]
    collector = _collector_tag(str(record.get("collector") or ""))
    quality = _quality_tag(str(record.get("quality_status") or ""))
    if collector:
        raw_tags.append(collector)
    if quality:
        raw_tags.append(quality)
    raw_tags.extend(_as_list(record.get("zotero_tags")))
    stable = sorted(_stable(_clean_output_text(tag) for tag in raw_tags if tag))
    return [{"tag": tag} for tag in stable]


def build_zotero_collections(record: dict[str, Any]) -> list[str]:
    record = _ensure_library_like(record)
    tags = {entry["tag"] for entry in build_zotero_tags(record)}
    collections = ["Lattice Crypto Daily Digest"]
    if "LC/Priority/Must-Read" in tags or "LC/Priority/Should-Read" in tags:
        collections.append("High Priority")
    if "LC/AI/AI4Lattice" in tags:
        collections.append("AI4Lattice")
    if any(tag.startswith("LC/Attack/") or tag.startswith("LC/Tool/") for tag in tags):
        collections.append("Lattice Reduction and Attacks")
    if "LC/ResearchLine/PQC-Implementation-Security" in tags:
        collections.append("PQC Implementation Security")
    if any(tag.startswith("LC/Primitive/") for tag in tags):
        collections.append("Lattice-Based Primitives")
    if "LC/Quality/Authoritative-Backfill" in tags:
        collections.append("Backfill Imported")
    if "LC/Priority/Must-Read" in tags or "LC/Priority/Should-Read" in tags:
        collections.append("Weekly Reading Queue")
    return _stable(collections)


def build_extra_field(record: dict[str, Any]) -> str:
    record = _ensure_library_like(record)
    fields = [
        ("LatticeDigestID", record.get("item_id")),
        ("CanonicalID", record.get("dedup_key")),
        ("Source", record.get("source")),
        ("PriorityScore", record.get("reading_priority_score")),
        ("PriorityLabel", record.get("priority_label")),
        ("WhyItMatters", record.get("why_it_matters") or record.get("reason_for_priority")),
        ("SuggestedAction", record.get("suggested_action")),
        ("ResearchTags", ", ".join(_as_list(record.get("research_tags")))),
        ("DigestDate", ", ".join(_as_list(record.get("digest_dates")))),
        ("Collector", record.get("collector")),
        ("QualityStatus", record.get("quality_status")),
        ("RunMode", record.get("run_mode")),
        ("SourceHealth", record.get("source_health_ref")),
        ("OriginalURL", record.get("url")),
        ("PDFURL", record.get("pdf_url")),
        ("DOI", record.get("doi")),
    ]
    lines = []
    for key, value in fields:
        text = _clean_output_text(value)
        if text:
            lines.append(f"{key}: {text}")
    return "\n".join(lines)


def _relations(record: dict[str, Any]) -> dict[str, list[str]]:
    relations: dict[str, list[str]] = {}
    urls = [clean_url(record.get("url")), clean_url(record.get("pdf_url"))]
    urls = [url for url in urls if url]
    if urls:
        relations["dc:relation"] = urls
    return relations


def record_to_zotero_item(record: dict[str, Any]) -> dict[str, Any]:
    record = _ensure_library_like(record)
    item_type = infer_zotero_item_type(record)
    item: dict[str, Any] = {
        "itemType": item_type,
        "latticeDigestID": _clean_output_text(record.get("item_id")),
        "canonicalID": _clean_output_text(record.get("dedup_key")),
        "title": _clean_output_text(record.get("title")),
        "creators": normalize_authors_to_zotero_creators(record),
        "abstractNote": _clean_output_text(record.get("abstract")),
        "date": _clean_output_text(record.get("date") or record.get("year")),
        "url": clean_url(record.get("url")),
        "extra": build_extra_field(record),
        "tags": build_zotero_tags(record),
        "collections": build_zotero_collections(record),
        "relations": _relations(record),
    }
    doi = _clean_output_text(record.get("doi"))
    venue = _clean_output_text(record.get("venue"))
    if doi:
        item["DOI"] = doi
    if venue:
        if item_type == "conferencePaper":
            item["proceedingsTitle"] = venue
        else:
            item["publicationTitle"] = venue
    return {key: value for key, value in item.items() if value not in (None, "", [], {})}


def record_to_csl_item(record: dict[str, Any]) -> dict[str, Any]:
    record = _ensure_library_like(record)
    entry: dict[str, Any] = {
        "id": _clean_output_text(record.get("item_id") or record.get("dedup_key")),
        "type": infer_csl_type(record),
        "title": _clean_output_text(record.get("title")),
        "author": normalize_authors_to_csl(record),
        "keyword": ", ".join(entry["tag"] for entry in build_zotero_tags(record)),
        "note": build_extra_field(record),
    }
    issued = _date_parts(record.get("date"), record.get("year") if isinstance(record.get("year"), int) else None)
    if issued:
        entry["issued"] = issued
    if record.get("abstract"):
        entry["abstract"] = _clean_output_text(record.get("abstract"))
    if record.get("doi"):
        entry["DOI"] = _clean_output_text(record.get("doi"))
    if record.get("url"):
        entry["URL"] = clean_url(record.get("url"))
    if record.get("venue"):
        entry["container-title"] = _clean_output_text(record.get("venue"))
    return {key: value for key, value in entry.items() if value not in (None, "", [], {})}


def _bib_escape(value: object) -> str:
    text = _clean_output_text(value)
    replacements = {
        "\\": "\\textbackslash{}",
        "{": "\\{",
        "}": "\\}",
        "&": "\\&",
        "%": "\\%",
        "#": "\\#",
        "_": "\\_",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def render_bibtex(items: list[dict[str, Any]]) -> str:
    entries: list[str] = []
    for raw_item in items:
        item = _ensure_library_like(raw_item)
        entry_type = "inproceedings" if infer_zotero_item_type(item) == "conferencePaper" else "article" if infer_zotero_item_type(item) == "journalArticle" else "misc"
        fields = {
            "title": item.get("title") or "",
            "author": " and ".join(_as_list(item.get("authors"))),
            "year": item.get("year") or _year(item.get("date")) or "",
            "url": item.get("url") or "",
            "doi": item.get("doi") or "",
            "note": f"source={item.get('source') or 'unknown'}; priority={item.get('priority_label') or ''}; score={item.get('reading_priority_score')}; tags={'; '.join(entry['tag'] for entry in build_zotero_tags(item))}",
        }
        if item.get("venue"):
            fields["booktitle" if entry_type == "inproceedings" else "journal"] = item.get("venue")
        lines = [f"@{entry_type}{{{build_stable_citation_key(item)},"]
        for key, value in fields.items():
            if value not in (None, ""):
                lines.append(f"  {key} = {{{_bib_escape(value)}}},")
        lines.append("}")
        entries.append("\n".join(lines))
    return "\n\n".join(entries) + ("\n" if entries else "")


def render_ris(items: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for raw_item in items:
        item = _ensure_library_like(raw_item)
        lines.append("TY  - CONF" if infer_zotero_item_type(item) == "conferencePaper" else "TY  - JOUR" if infer_zotero_item_type(item) == "journalArticle" else "TY  - GEN")
        lines.append(f"TI  - {_clean_output_text(item.get('title'))}")
        for author in _as_list(item.get("authors")):
            lines.append(f"AU  - {_clean_output_text(author)}")
        year = item.get("year") or _year(item.get("date"))
        if year:
            lines.append(f"PY  - {year}")
        if item.get("doi"):
            lines.append(f"DO  - {_clean_output_text(item.get('doi'))}")
        if item.get("url"):
            lines.append(f"UR  - {clean_url(item.get('url'))}")
        if item.get("abstract"):
            lines.append(f"AB  - {_clean_output_text(item.get('abstract'))}")
        for tag in (entry["tag"] for entry in build_zotero_tags(item)):
            lines.append(f"KW  - {tag}")
        note = build_extra_field(item)
        if note:
            lines.append(f"N1  - {note.replace(chr(10), ' | ')}")
        lines.append("ER  -")
        lines.append("")
    return "\n".join(lines)


def dedup_records_for_zotero(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for record in records:
        key = str(record.get("dedup_key") or dedup_key_for_record(record))
        merged[key] = merge_items(merged[key], record) if key in merged else record
    return sorted(merged.values(), key=lambda item: (-int(item.get("reading_priority_score") or 0), str(item.get("title") or "")))


def parse_formats(raw: str) -> list[str]:
    formats: list[str] = []
    for part in _split_csv(raw or "all"):
        alias = FORMAT_ALIASES.get(part.lower())
        if not alias:
            raise ValueError(f"Unsupported Zotero export format: {part}")
        formats.extend(alias)
    return _stable(formats)


def _collection_tree() -> dict[str, Any]:
    return {
        "name": "Lattice Crypto Daily Digest",
        "children": [
            {"name": "High Priority", "children": []},
            {"name": "AI4Lattice", "children": []},
            {"name": "Lattice Reduction and Attacks", "children": []},
            {"name": "PQC Implementation Security", "children": []},
            {"name": "Lattice-Based Primitives", "children": []},
            {"name": "Weekly Reading Queue", "children": []},
            {"name": "Backfill Imported", "children": []},
        ],
    }


def render_export_report(items: list[dict[str, Any]], *, input_dir: Path, from_date: str | None, to_date: str | None, formats: list[str], dedup_count: int) -> str:
    input_display = input_dir.name if input_dir.is_absolute() else str(input_dir)
    missing_doi = sum(1 for item in items if not item.get("doi"))
    missing_author = sum(1 for item in items if not _as_list(item.get("authors")))
    high_priority = sum(1 for item in items if int(item.get("reading_priority_score") or 0) >= 70)
    tag_sets = [set(entry["tag"] for entry in build_zotero_tags(item)) for item in items]
    ai_hits = sum(1 for tags in tag_sets if "LC/AI/AI4Lattice" in tags)
    module_sis_hits = sum(1 for tags in tag_sets if "LC/ResearchLine/Module-SIS-Chameleon-Hash" in tags)
    bkz_hits = sum(1 for tags in tag_sets if {"LC/Attack/BKZ", "LC/Attack/Hybrid", "LC/Tool/G6K", "LC/Tool/fplll"} & tags)
    lines = [
        "# Zotero Compatibility Export Report",
        "",
        "## 1. 导出摘要",
        "",
        f"- 输入目录：{input_display}",
        f"- 日期范围：{from_date or '未限制'} 至 {to_date or '未限制'}",
        f"- record 数量：{len(items)}",
        f"- 格式数量：{len(formats)}",
        f"- 缺失 DOI 数量：{missing_doi}",
        f"- 缺失 author 数量：{missing_author}",
        f"- dedup 合并数量：{dedup_count}",
        f"- 高优先级论文数量：{high_priority}",
        f"- AI4Lattice 命中数量：{ai_hits}",
        f"- Module-SIS / chameleon hash 命中数量：{module_sis_hits}",
        f"- BKZ / hybrid attack 命中数量：{bkz_hits}",
        "",
        "## 2. 推荐 Zotero 导入步骤",
        "",
        "1. 优先用 CSL-JSON 或 BibTeX 做手动导入测试。",
        "2. 在 Zotero 中选择 File -> Import。",
        "3. 导入后人工核对 title、authors、year、URL、DOI、abstract、tags 和 extra。",
        "4. 根据 `zotero_collections.json` 手动整理 collection tree。",
        "5. 真实 Zotero Web API push 留到后续阶段；本阶段不上传。",
        "",
        "## 3. 高优先级条目",
        "",
    ]
    if not items:
        lines.append("- 没有可导出的条目。")
    else:
        for item in items[:10]:
            lines.append(f"- {item.get('title') or 'Untitled'}：{item.get('reading_priority_score')} / {item.get('priority_label') or 'unknown'}")
    lines.extend(["", "## 4. 标签分布", ""])
    counter: Counter[str] = Counter()
    for tags in tag_sets:
        counter.update(tags)
    if counter:
        lines.extend(f"- {tag}: {count}" for tag, count in counter.most_common(30))
    else:
        lines.append("- 无")
    lines.extend(["", "## 5. 工程验收说明", "", "- 本报告为离线导出验收报告，不调用 Zotero API。", "- 不包含 API key、用户真实 Zotero ID 或私有 collection key。", ""])
    return "\n".join(lines)


def _assert_clean_payload(paths: Iterable[Path]) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for marker in POLLUTION_MARKERS:
            if marker in text:
                raise ValueError(f"Export output contains pollution marker {marker}: {path}")
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, text):
                raise ValueError(f"Export output contains secret-like pattern: {path}")


def write_zotero_exports(
    items: list[dict[str, Any]],
    run_dir: Path,
    *,
    input_dir: Path,
    from_date: str | None,
    to_date: str | None,
    formats: list[str],
    dedup_count: int,
) -> tuple[list[dict[str, Any]], list[Path]]:
    run_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    zotero_items = [record_to_zotero_item(item) for item in items]
    if "zotero-json" in formats:
        path = run_dir / "zotero_items.json"
        path.write_text(json.dumps(zotero_items, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(path)
    if "csl-json" in formats:
        path = run_dir / "items.csl.json"
        path.write_text(json.dumps([record_to_csl_item(item) for item in items], ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(path)
    if "bibtex" in formats:
        path = run_dir / "items.bib"
        path.write_text(render_bibtex(items), encoding="utf-8")
        written.append(path)
    if "ris" in formats:
        path = run_dir / "items.ris"
        path.write_text(render_ris(items), encoding="utf-8")
        written.append(path)
    if "collections" in formats:
        path = run_dir / "zotero_collections.json"
        path.write_text(json.dumps(_collection_tree(), ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(path)
    if "report" in formats:
        path = run_dir / "export_report.md"
        path.write_text(render_export_report(items, input_dir=input_dir, from_date=from_date, to_date=to_date, formats=formats, dedup_count=dedup_count), encoding="utf-8")
        written.append(path)
    _assert_clean_payload(written)
    return zotero_items, written


def _default_dates(days: int | None, from_date: str | None, to_date: str | None) -> tuple[str | None, str | None]:
    if days is None or from_date or to_date:
        return from_date, to_date
    today = date.today()
    start = today - timedelta(days=max(0, days - 1))
    return start.isoformat(), today.isoformat()


def generate_zotero_export(
    *,
    input_dir: Path = Path("data"),
    output_dir: Path = Path("exports/zotero"),
    days: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    formats: str = "all",
    min_priority_score: int = 0,
    include_provisional: bool = False,
    dry_run: bool = False,
    fail_on_empty: bool = False,
) -> ZoteroExportResult:
    from_date, to_date = _default_dates(days, from_date, to_date)
    parsed_formats = parse_formats(formats)
    raw_items = _load_items_with_metadata(input_dir, from_date=from_date, to_date=to_date, include_provisional=include_provisional, dedup=False)
    deduped = dedup_records_for_zotero(raw_items)
    items = filter_items(deduped, min_priority_score=min_priority_score)
    if fail_on_empty and not items:
        raise ValueError("No Zotero-compatible records found for the requested input/date range.")
    run_day = to_date or from_date or datetime.now(timezone.utc).date().isoformat()
    run_dir = output_dir / run_day
    if dry_run:
        zotero_items = [record_to_zotero_item(item) for item in items]
        return ZoteroExportResult(items=items, zotero_items=zotero_items, output_dir=output_dir, run_dir=run_dir, formats=parsed_formats, written_paths=[], dry_run=True)
    zotero_items, written = write_zotero_exports(
        items,
        run_dir,
        input_dir=input_dir,
        from_date=from_date,
        to_date=to_date,
        formats=parsed_formats,
        dedup_count=max(0, len(raw_items) - len(deduped)),
    )
    return ZoteroExportResult(items=items, zotero_items=zotero_items, output_dir=output_dir, run_dir=run_dir, formats=parsed_formats, written_paths=written)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export digest records to offline Zotero-compatible formats.")
    parser.add_argument("--days", type=int, default=None)
    parser.add_argument("--from-date", default=None)
    parser.add_argument("--to-date", default=None)
    parser.add_argument("--input-dir", default="data")
    parser.add_argument("--output-dir", default="exports/zotero")
    parser.add_argument("--formats", default="all")
    parser.add_argument("--min-priority-score", type=int, default=0)
    parser.add_argument("--include-provisional", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fail-on-empty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = generate_zotero_export(
            input_dir=Path(args.input_dir),
            output_dir=Path(args.output_dir),
            days=args.days,
            from_date=args.from_date,
            to_date=args.to_date,
            formats=args.formats,
            min_priority_score=args.min_priority_score,
            include_provisional=args.include_provisional,
            dry_run=args.dry_run,
            fail_on_empty=args.fail_on_empty,
        )
    except ValueError as exc:
        print(f"zotero export failed: {exc}")
        return 1
    print(f"zotero records: {len(result.items)}")
    print(f"output dir: {result.run_dir}")
    print(f"formats: {', '.join(result.formats)}")
    if result.dry_run:
        print("dry-run: no files written")
    else:
        for path in result.written_paths:
            print(f"wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
