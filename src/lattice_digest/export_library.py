from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from lattice_digest.ideas import normalize_key, sanitize, short_hash
from lattice_digest.library_taxonomy import TaxonomyResult, classify_text


SCHEMA_VERSION = 1
POLLUTION_MARKERS = ("contentReference", "oaicite", "id=")
SECRET_PATTERNS = (
    r"ghp_[A-Za-z0-9_]+",
    r"github_pat_[A-Za-z0-9_]+",
    r"sk-[A-Za-z0-9_-]+",
    r"xoxb-[A-Za-z0-9-]+",
    r"AKIA[0-9A-Z]+",
)

FORMAT_ALIASES = {
    "all": ("csl-json", "bibtex", "ris", "tags", "report"),
    "json": ("json",),
    "library-json": ("json",),
    "csl": ("csl-json",),
    "csl-json": ("csl-json",),
    "bib": ("bibtex",),
    "bibtex": ("bibtex",),
    "ris": ("ris",),
    "tags": ("tags",),
    "report": ("report",),
}


@dataclass(frozen=True)
class LibraryExportResult:
    items: list[dict[str, Any]]
    output_dir: Path
    formats: list[str]
    written_paths: list[Path]
    dry_run: bool = False


def clean_text(value: object) -> str:
    text = sanitize(value)
    text = re.sub(r"<[^>]+>", "", text)
    for marker in POLLUTION_MARKERS:
        text = text.replace(marker, "")
    for pattern in SECRET_PATTERNS:
        text = re.sub(pattern, "[REDACTED_SECRET]", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_url(value: object) -> str:
    text = clean_text(value)
    return text.replace(" ", "%20")


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
        # Authors sometimes arrive as "A, B and C"; keep conservative splitting.
        if " and " in value:
            parts = value.split(" and ")
        elif ";" in value:
            parts = value.split(";")
        else:
            parts = [value]
        return _stable(clean_text(part) for part in parts if clean_text(part))
    return []


def _stable(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _field(record: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = record.get(name)
        if value not in (None, "", [], {}):
            return value
    return ""


def _score(value: object) -> int:
    try:
        return max(0, min(100, int(value or 0)))
    except (TypeError, ValueError):
        return 0


def _year_from(value: object) -> int | None:
    text = clean_text(value)
    match = re.search(r"(19|20)\d{2}", text)
    if not match:
        return None
    return int(match.group(0))


def _date_from_record(record: dict[str, Any]) -> str:
    return clean_text(_field(record, "date", "publication_date", "published_date", "update_date", "updatedAt", "publicationDate"))


def _record_digest_date(payload: dict[str, Any] | list[Any], path: Path) -> str:
    if isinstance(payload, dict):
        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            for key in ("target_date", "run_date", "date"):
                value = clean_text(metadata.get(key))
                if value:
                    return value[:10]
    return path.stem[:10]


def _source_type(source: str) -> str:
    text = source.lower()
    if "arxiv" in text or "eprint" in text or "iacr" in text:
        return "preprint"
    if "dblp" in text:
        return "bibliography"
    if any(name in text for name in ("crossref", "openalex", "semantic")):
        return "metadata"
    return "unknown"


def _normalize_identifier(value: object) -> str:
    return clean_text(value).strip().strip(".").lower()


def _normalized_title_hash(title: str) -> str:
    return short_hash(normalize_key(title), 16)


def dedup_key_for_record(record: dict[str, Any]) -> str:
    identifiers = [
        ("doi", _field(record, "doi", "crossref_doi")),
        ("arxiv", _field(record, "arxiv_id")),
        ("eprint", _field(record, "eprint_id")),
        ("semantic_scholar", _field(record, "semantic_scholar_id", "paperId")),
        ("openalex", _field(record, "openalex_id", "openalex")),
    ]
    for prefix, value in identifiers:
        normalized = _normalize_identifier(value)
        if normalized:
            return f"{prefix}:{normalized}"
    url = clean_url(_field(record, "url", "source_url", "pdf_url"))
    if url:
        return f"url:{url.lower()}"
    title = clean_text(record.get("title"))
    return f"title:{_normalized_title_hash(title)}"


def _item_id(dedup_key: str) -> str:
    return f"lib-{short_hash(dedup_key, 14)}"


def _source_tag(source: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", source.lower()).strip("_")
    return f"source/{normalized or 'unknown'}"


def _priority_tag(label: str, score: int) -> str:
    if label == "必须精读" or score >= 85:
        return "priority/must-read"
    if label == "建议精读" or score >= 70:
        return "priority/recommended"
    if label == "可略读" or score >= 50:
        return "priority/skim"
    return "priority/archive"


def _combined_existing_tags(record: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    for key in ("tags", "research_tags", "taxonomy_tags", "categories", "keywords_matched"):
        tags.extend(_as_list(record.get(key)))
    return _stable(tags)


def _taxonomy_for_record(record: dict[str, Any]) -> TaxonomyResult:
    title = clean_text(record.get("title"))
    abstract = clean_text(record.get("abstract"))
    existing_tags = _combined_existing_tags(record)
    priority_label = clean_text(record.get("priority_label"))
    suggested_action = clean_text(record.get("suggested_action"))
    reason = clean_text(_field(record, "reason_for_priority", "reason", "why_it_matters"))
    primary_text = normalize_key(f"{title} {abstract}")
    crypto_terms = (
        "cryptograph",
        "cryptanalysis",
        "lattice",
        "lwe",
        "rlwe",
        "mlwe",
        "sis",
        "ntru",
        "kyber",
        "ml kem",
        "ml dsa",
        "dilithium",
        "fn dsa",
        "signature",
        "post quantum",
        "fhe",
    )
    if re.search(r"\bfalcon[- ]x\b", primary_text) and not any(term in primary_text for term in crypto_terms):
        # Older digest records may have over-eager Falcon/FN-DSA tags attached to
        # unrelated Falcon-X time-series models. Library export should not
        # propagate that into Zotero/Obsidian tags.
        existing_tags = []
        reason = ""
    return classify_text(
        title=title,
        abstract=abstract,
        existing_tags=existing_tags,
        priority_label=priority_label,
        suggested_action=suggested_action,
        reason_for_priority=reason,
    )


def _export_warnings(item: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not item.get("doi"):
        warnings.append("missing_doi")
    if not item.get("authors"):
        warnings.append("missing_authors")
    if not item.get("abstract"):
        warnings.append("missing_abstract")
    if not item.get("url"):
        warnings.append("missing_url")
    if not item.get("date") and not item.get("year"):
        warnings.append("missing_date")
    if not (
        item.get("lattice_tags")
        or item.get("pqc_tags")
        or item.get("attack_tags")
        or item.get("primitive_tags")
        or item.get("implementation_tags")
        or item.get("ai_tags")
    ):
        warnings.append("insufficient_tags")
    if warnings:
        warnings.append("TODO_VERIFY")
    return _stable(warnings)


def record_to_library_item(record: dict[str, Any], digest_date: str) -> dict[str, Any]:
    title = clean_text(record.get("title"))
    source = clean_text(record.get("source"))
    url = clean_url(_field(record, "url", "source_url"))
    doi = _normalize_identifier(_field(record, "doi", "crossref_doi"))
    date_value = _date_from_record(record)
    year = _year_from(_field(record, "year", date_value))
    score = _score(_field(record, "reading_priority_score", "relevance_score"))
    priority_label = clean_text(_field(record, "priority_label", "relevance_label"))
    reason = clean_text(_field(record, "reason_for_priority", "reason"))
    why = clean_text(_field(record, "why_it_matters", "reason"))
    suggested_action = clean_text(_field(record, "suggested_action", "reading_priority"))
    taxonomy = _taxonomy_for_record(record)
    priority_tag = _priority_tag(priority_label, score)
    source_tag = _source_tag(source)
    dedup_key = dedup_key_for_record(record)

    item: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "item_id": _item_id(dedup_key),
        "dedup_key": dedup_key,
        "title": title,
        "authors": _as_list(record.get("authors")),
        "year": year,
        "date": date_value,
        "source": source,
        "source_type": _source_type(source),
        "venue": clean_text(_field(record, "venue", "journal", "conference")),
        "abstract": clean_text(record.get("abstract")),
        "url": url,
        "pdf_url": clean_url(record.get("pdf_url")),
        "doi": doi,
        "arxiv_id": _normalize_identifier(record.get("arxiv_id")),
        "eprint_id": _normalize_identifier(record.get("eprint_id")),
        "semantic_scholar_id": _normalize_identifier(_field(record, "semantic_scholar_id", "paperId")),
        "openalex_id": _normalize_identifier(_field(record, "openalex_id", "openalex")),
        "dblp_url": clean_url(record.get("dblp_url")) or (url if "dblp" in source.lower() else ""),
        "crossref_doi": doi if "crossref" in source.lower() else _normalize_identifier(record.get("crossref_doi")),
        "normalized_identifiers": {
            "doi": doi,
            "arxiv_id": _normalize_identifier(record.get("arxiv_id")),
            "eprint_id": _normalize_identifier(record.get("eprint_id")),
            "semantic_scholar_id": _normalize_identifier(_field(record, "semantic_scholar_id", "paperId")),
            "openalex_id": _normalize_identifier(_field(record, "openalex_id", "openalex")),
            "normalized_title_hash": _normalized_title_hash(title),
        },
        "source_trace": _stable([source, *_as_list(record.get("source_trace"))]),
        "first_seen_date": digest_date,
        "last_seen_date": digest_date,
        "digest_dates": [digest_date] if digest_date else [],
        "reading_priority_score": score,
        "priority_label": priority_label,
        "reason_for_priority": reason,
        "why_it_matters": why,
        "suggested_action": suggested_action,
        "research_tags": _stable([*taxonomy.research_tags, *_as_list(record.get("research_tags"))]),
        "lattice_tags": taxonomy.lattice_tags,
        "pqc_tags": taxonomy.pqc_tags,
        "ai_tags": taxonomy.ai_tags,
        "attack_tags": taxonomy.attack_tags,
        "primitive_tags": taxonomy.primitive_tags,
        "implementation_tags": taxonomy.implementation_tags,
        "zotero_tags": _stable([*taxonomy.zotero_tags, priority_tag, source_tag]),
        "obsidian_links": taxonomy.obsidian_links,
        "obsidian_note_hint": f"{digest_date}__{normalize_key(title).replace(' ', '-')[:80]}".strip("_-"),
        "idea_hooks": _as_list(record.get("research_hooks")),
        "advisor_questions": _as_list(record.get("advisor_questions")),
        "export_warnings": [],
    }
    item["export_warnings"] = _export_warnings(item)
    return item


def _merge_list_values(first: list[str], second: list[str]) -> list[str]:
    return _stable([*first, *second])


def merge_items(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    if int(incoming.get("reading_priority_score") or 0) > int(existing.get("reading_priority_score") or 0):
        for key in ("reading_priority_score", "priority_label", "reason_for_priority", "why_it_matters", "suggested_action"):
            merged[key] = incoming.get(key, merged.get(key))
    for key in (
        "authors",
        "source_trace",
        "digest_dates",
        "research_tags",
        "lattice_tags",
        "pqc_tags",
        "ai_tags",
        "attack_tags",
        "primitive_tags",
        "implementation_tags",
        "zotero_tags",
        "obsidian_links",
        "idea_hooks",
        "advisor_questions",
        "export_warnings",
    ):
        merged[key] = _merge_list_values(_as_list(merged.get(key)), _as_list(incoming.get(key)))
    for key in ("abstract", "url", "pdf_url", "doi", "venue", "date", "source", "source_type"):
        if not merged.get(key) or len(str(incoming.get(key) or "")) > len(str(merged.get(key) or "")):
            merged[key] = incoming.get(key, merged.get(key))
    dates = sorted(date for date in _as_list(merged.get("digest_dates")) if date)
    merged["first_seen_date"] = dates[0] if dates else clean_text(merged.get("first_seen_date"))
    merged["last_seen_date"] = dates[-1] if dates else clean_text(merged.get("last_seen_date"))
    return merged


def _load_digest_payload(path: Path) -> tuple[list[dict[str, Any]], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    digest_date = _record_digest_date(payload, path)
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        raw_records = payload.get("records", [])
        records = raw_records if isinstance(raw_records, list) else []
    else:
        records = []
    return [dict(record) for record in records if isinstance(record, dict)], digest_date


def _iter_input_files(input_path: Path, from_date: str | None = None, to_date: str | None = None) -> list[Path]:
    if input_path.is_file():
        candidates = [input_path]
    else:
        candidates = sorted(input_path.glob("*.json"))
    selected: list[Path] = []
    for path in candidates:
        day = path.stem[:10]
        if from_date and day < from_date:
            continue
        if to_date and day > to_date:
            continue
        selected.append(path)
    return selected


def load_library_items(
    input_path: Path,
    *,
    from_date: str | None = None,
    to_date: str | None = None,
    dedup: bool = True,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    deduped: dict[str, dict[str, Any]] = {}
    for path in _iter_input_files(input_path, from_date, to_date):
        records, digest_date = _load_digest_payload(path)
        for record in records:
            item = record_to_library_item(record, digest_date)
            if dedup:
                key = str(item["dedup_key"])
                deduped[key] = merge_items(deduped[key], item) if key in deduped else item
            else:
                items.append(item)
    if dedup:
        items = list(deduped.values())
    return sorted(items, key=lambda item: (-int(item.get("reading_priority_score") or 0), str(item.get("title") or "")))


def _split_csv(values: Iterable[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        for part in str(value).split(","):
            cleaned = clean_text(part)
            if cleaned:
                result.append(cleaned)
    return _stable(result)


def _item_tag_set(item: dict[str, Any]) -> set[str]:
    tags: list[str] = []
    for key in (
        "research_tags",
        "lattice_tags",
        "pqc_tags",
        "ai_tags",
        "attack_tags",
        "primitive_tags",
        "implementation_tags",
        "zotero_tags",
    ):
        tags.extend(_as_list(item.get(key)))
    return {tag.lower() for tag in tags}


def filter_items(
    items: list[dict[str, Any]],
    *,
    min_priority_score: int = 0,
    priority_labels: Iterable[str] = (),
    tags: Iterable[str] = (),
    sources: Iterable[str] = (),
    limit: int | None = None,
) -> list[dict[str, Any]]:
    labels = {label.lower() for label in priority_labels}
    tag_filters = {tag.lower() for tag in tags}
    source_filters = {source.lower() for source in sources}
    filtered: list[dict[str, Any]] = []
    for item in items:
        if int(item.get("reading_priority_score") or 0) < min_priority_score:
            continue
        if labels and str(item.get("priority_label") or "").lower() not in labels:
            continue
        if source_filters and str(item.get("source") or "").lower() not in source_filters:
            continue
        item_tags = _item_tag_set(item)
        if tag_filters and not all(tag in item_tags for tag in tag_filters):
            continue
        filtered.append(item)
    if limit is not None:
        return filtered[:limit]
    return filtered


def parse_formats(raw_format: str) -> list[str]:
    formats: list[str] = ["json"]
    for part in _split_csv([raw_format or "all"]):
        alias = FORMAT_ALIASES.get(part.lower())
        if not alias:
            raise ValueError(f"Unsupported library export format: {part}")
        formats.extend(alias)
    return _stable(formats)


def _issued(date_value: str, year: int | None) -> dict[str, Any] | None:
    if date_value:
        parts = [int(part) for part in re.findall(r"\d+", date_value[:10])[:3]]
        if parts:
            return {"date-parts": [parts]}
    if year:
        return {"date-parts": [[year]]}
    return None


def _csl_type(item: dict[str, Any]) -> str:
    venue = str(item.get("venue") or "").lower()
    if any(word in venue for word in ("crypto", "eurocrypt", "asiacrypt", "ccs", "usenix", "ndss", "ieee")):
        return "paper-conference"
    if item.get("doi") and venue:
        return "article-journal"
    return "report"


def render_csl_json(items: list[dict[str, Any]], *, include_abstract: bool = True, include_notes: bool = True) -> list[dict[str, Any]]:
    csl_items: list[dict[str, Any]] = []
    for item in items:
        entry: dict[str, Any] = {
            "id": item["item_id"],
            "type": _csl_type(item),
            "title": item.get("title") or "",
            "author": [{"literal": author} for author in _as_list(item.get("authors"))],
        }
        issued = _issued(str(item.get("date") or ""), item.get("year") if isinstance(item.get("year"), int) else None)
        if issued:
            entry["issued"] = issued
        if item.get("url"):
            entry["URL"] = item["url"]
        if item.get("doi"):
            entry["DOI"] = item["doi"]
        if include_abstract and item.get("abstract"):
            entry["abstract"] = item["abstract"]
        if include_notes:
            entry["note"] = clean_text(
                " | ".join(
                    [
                        f"source: {item.get('source') or 'unknown'}",
                        f"reading_priority_score: {item.get('reading_priority_score')}",
                        f"priority_label: {item.get('priority_label')}",
                        f"why_it_matters: {item.get('why_it_matters')}",
                        f"suggested_action: {item.get('suggested_action')}",
                        f"research_tags: {', '.join(_as_list(item.get('research_tags')))}",
                    ]
                )
            )
        csl_items.append(entry)
    return csl_items


def bibtex_key(item: dict[str, Any]) -> str:
    authors = _as_list(item.get("authors"))
    first = normalize_key(authors[0]).split(" ")[-1] if authors else "item"
    year = str(item.get("year") or "noyear")
    title_hash = short_hash(str(item.get("dedup_key") or item.get("title") or ""), 6)
    key = re.sub(r"[^A-Za-z0-9]+", "", f"{first}{year}{title_hash}")
    return key or f"item{title_hash}"


def _bib_escape(value: object) -> str:
    text = clean_text(value)
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
    for item in items:
        entry_type = "article" if item.get("doi") and item.get("venue") else "misc"
        fields = {
            "title": item.get("title") or "",
            "author": " and ".join(_as_list(item.get("authors"))),
            "year": item.get("year") or "",
            "url": item.get("url") or "",
            "doi": item.get("doi") or "",
            "note": f"source={item.get('source') or 'unknown'}; priority={item.get('priority_label') or ''}; score={item.get('reading_priority_score')}",
        }
        lines = [f"@{entry_type}{{{bibtex_key(item)},"]
        for key, value in fields.items():
            if value not in (None, ""):
                lines.append(f"  {key} = {{{_bib_escape(value)}}},")
        lines.append("}")
        entries.append("\n".join(lines))
    return "\n\n".join(entries) + ("\n" if entries else "")


def render_ris(items: list[dict[str, Any]], *, include_abstract: bool = True, include_notes: bool = True) -> str:
    lines: list[str] = []
    for item in items:
        lines.append("TY  - JOUR" if item.get("doi") and item.get("venue") else "TY  - GEN")
        lines.append(f"TI  - {clean_text(item.get('title'))}")
        for author in _as_list(item.get("authors")):
            lines.append(f"AU  - {author}")
        if item.get("year"):
            lines.append(f"PY  - {item['year']}")
        if item.get("doi"):
            lines.append(f"DO  - {item['doi']}")
        if item.get("url"):
            lines.append(f"UR  - {item['url']}")
        if include_abstract and item.get("abstract"):
            lines.append(f"AB  - {item['abstract']}")
        for tag in _as_list(item.get("zotero_tags")):
            lines.append(f"KW  - {tag}")
        if include_notes:
            lines.append(f"N1  - source={item.get('source') or 'unknown'}; priority={item.get('priority_label')}; score={item.get('reading_priority_score')}")
        lines.append("ER  -")
        lines.append("")
    return "\n".join(lines)


def render_zotero_tags(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for item in items:
        priority_tag = _priority_tag(str(item.get("priority_label") or ""), int(item.get("reading_priority_score") or 0))
        source_tag = _source_tag(str(item.get("source") or ""))
        payload.append(
            {
                "item_id": item.get("item_id"),
                "title": item.get("title"),
                "zotero_tags": _as_list(item.get("zotero_tags")),
                "priority_tags": [priority_tag],
                "source_tags": [source_tag],
                "research_tags": _as_list(item.get("research_tags")),
            }
        )
    return payload


def _count_tags(items: list[dict[str, Any]], key: str) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for item in items:
        counter.update(_as_list(item.get(key)))
    return counter.most_common()


def render_import_report(items: list[dict[str, Any]], *, input_path: Path, from_date: str | None, to_date: str | None, formats: list[str]) -> str:
    warning_counter: Counter[str] = Counter()
    for item in items:
        warning_counter.update(_as_list(item.get("export_warnings")))
    lines = [
        "# Library Export Import Report",
        "",
        "## 1. 导出摘要",
        "",
        f"- 输入路径：{input_path}",
        f"- 日期范围：{from_date or '未限制'} 至 {to_date or '未限制'}",
        f"- 总条目：{len(items)}",
        f"- 去重后条目：{len(items)}",
        f"- 导出格式：{', '.join(formats)}",
        "",
        "## 2. 高优先级论文",
        "",
    ]
    for item in sorted(items, key=lambda value: -int(value.get("reading_priority_score") or 0))[:10]:
        lines.append(f"- {item.get('title') or 'Untitled'}：{item.get('reading_priority_score')} / {item.get('priority_label') or 'unknown'}")
    if not items:
        lines.append("- 暂无可导出的条目。")
    lines.extend(["", "## 3. 标签分布", ""])
    for key in ("research_tags", "lattice_tags", "attack_tags", "ai_tags", "primitive_tags", "implementation_tags"):
        lines.append(f"### {key}")
        counts = _count_tags(items, key)
        if counts:
            lines.extend(f"- {tag}: {count}" for tag, count in counts[:20])
        else:
            lines.append("- 无")
        lines.append("")
    lines.extend(
        [
            "## 4. Zotero 导入建议",
            "",
            "- 优先尝试 CSL JSON，保留结构化字段与 note。",
            "- BibTeX 适合论文写作工具链。",
            "- RIS 适合作为兼容性备选。",
            "",
            "## 5. 质量警告",
            "",
        ]
    )
    if warning_counter:
        lines.extend(f"- {warning}: {count}" for warning, count in warning_counter.most_common())
    else:
        lines.append("- 未发现明显质量警告。")
    lines.extend(
        [
            "",
            "## 6. 人工检查清单",
            "",
            "- 作者是否正确。",
            "- DOI 是否正确。",
            "- arXiv / ePrint 是否重复。",
            "- 标签是否过多。",
            "- 是否需要移动到专门 collection。",
            "",
            "## 7. 下一步动作",
            "",
            "- 导入 Zotero。",
            "- 生成 Obsidian 卡片。",
            "- 加入 Weekly Brief。",
            "- 进入 Idea Bank / Paper Plan。",
            "",
        ]
    )
    return "\n".join(lines)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_exports(
    items: list[dict[str, Any]],
    output_dir: Path,
    *,
    input_path: Path,
    from_date: str | None,
    to_date: str | None,
    formats: list[str],
    dedup_enabled: bool,
    include_abstract: bool,
    include_notes: bool,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": SCHEMA_VERSION,
        "input_path": str(input_path),
        "from_date": from_date,
        "to_date": to_date,
        "total_items": len(items),
        "dedup_enabled": dedup_enabled,
        "formats": formats,
        "export_profile": "stable-library-export-v1",
    }
    library_path = output_dir / "library-items.json"
    _write_json(library_path, {"metadata": metadata, "items": items})
    written.append(library_path)
    if "csl-json" in formats:
        path = output_dir / "library-items.csl.json"
        _write_json(path, render_csl_json(items, include_abstract=include_abstract, include_notes=include_notes))
        written.append(path)
    if "bibtex" in formats:
        path = output_dir / "library-items.bib"
        path.write_text(render_bibtex(items), encoding="utf-8")
        written.append(path)
    if "ris" in formats:
        path = output_dir / "library-items.ris"
        path.write_text(render_ris(items, include_abstract=include_abstract, include_notes=include_notes), encoding="utf-8")
        written.append(path)
    if "tags" in formats:
        path = output_dir / "zotero-tags.json"
        _write_json(path, render_zotero_tags(items))
        written.append(path)
    if "report" in formats:
        path = output_dir / "import-report.md"
        path.write_text(render_import_report(items, input_path=input_path, from_date=from_date, to_date=to_date, formats=formats), encoding="utf-8")
        written.append(path)
    return written


def generate_library_export(
    input_path: Path,
    output_dir: Path,
    *,
    from_date: str | None = None,
    to_date: str | None = None,
    formats: str = "all",
    min_priority_score: int = 0,
    priority_labels: Iterable[str] = (),
    tags: Iterable[str] = (),
    sources: Iterable[str] = (),
    limit: int | None = None,
    dry_run: bool = False,
    include_abstract: bool = True,
    include_notes: bool = True,
    dedup: bool = True,
) -> LibraryExportResult:
    parsed_formats = parse_formats(formats)
    items = load_library_items(input_path, from_date=from_date, to_date=to_date, dedup=dedup)
    items = filter_items(
        items,
        min_priority_score=min_priority_score,
        priority_labels=_split_csv(priority_labels),
        tags=_split_csv(tags),
        sources=_split_csv(sources),
        limit=limit,
    )
    if dry_run:
        return LibraryExportResult(items=items, output_dir=output_dir, formats=parsed_formats, written_paths=[], dry_run=True)
    written = write_exports(
        items,
        output_dir,
        input_path=input_path,
        from_date=from_date,
        to_date=to_date,
        formats=parsed_formats,
        dedup_enabled=dedup,
        include_abstract=include_abstract,
        include_notes=include_notes,
    )
    return LibraryExportResult(items=items, output_dir=output_dir, formats=parsed_formats, written_paths=written)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export digest JSON records to stable library interoperability formats.")
    parser.add_argument("--input", default="data", help="Digest JSON file or data directory.")
    parser.add_argument("--from-date", default=None)
    parser.add_argument("--to-date", default=None)
    parser.add_argument("--format", default="all")
    parser.add_argument("--output-dir", default="exports/library")
    parser.add_argument("--min-priority-score", type=int, default=0)
    parser.add_argument("--priority-label", action="append", default=[])
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--include-abstract", dest="include_abstract", action="store_true", default=True)
    parser.add_argument("--no-include-abstract", dest="include_abstract", action="store_false")
    parser.add_argument("--include-notes", dest="include_notes", action="store_true", default=True)
    parser.add_argument("--no-include-notes", dest="include_notes", action="store_false")
    parser.add_argument("--dedup", dest="dedup", action="store_true", default=True)
    parser.add_argument("--no-dedup", dest="dedup", action="store_false")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = generate_library_export(
        Path(args.input),
        Path(args.output_dir),
        from_date=args.from_date,
        to_date=args.to_date,
        formats=args.format,
        min_priority_score=args.min_priority_score,
        priority_labels=args.priority_label,
        tags=args.tag,
        sources=args.source,
        limit=args.limit,
        dry_run=args.dry_run,
        include_abstract=args.include_abstract,
        include_notes=args.include_notes,
        dedup=args.dedup,
    )
    print(f"library items: {len(result.items)}")
    print(f"output dir: {result.output_dir}")
    print(f"formats: {', '.join(result.formats)}")
    if result.dry_run:
        print("dry-run: no files written")
    else:
        for path in result.written_paths:
            print(f"wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
