from __future__ import annotations

from collections.abc import Iterable

from lattice_digest.models import PaperRecord, copy_record
from lattice_digest.text import normalize_title


def dedup_keys(record: PaperRecord) -> list[str]:
    keys: list[str] = []
    if record.doi:
        keys.append("doi:" + record.doi.lower().strip())
    if record.arxiv_id:
        keys.append("arxiv:" + record.arxiv_id.lower().strip())
    if record.eprint_id:
        keys.append("eprint:" + record.eprint_id.lower().strip())
    normalized = record.normalized_title or normalize_title(record.title)
    if normalized:
        keys.append("title:" + normalized)
    return keys


def merge_records(existing: PaperRecord, incoming: PaperRecord) -> PaperRecord:
    merged = copy_record(existing)
    if len(incoming.abstract or "") > len(existing.abstract or ""):
        merged.abstract = incoming.abstract
    for field in ("pdf_url", "paper_id", "arxiv_id", "eprint_id", "doi", "venue", "publication_date", "update_date"):
        if not getattr(merged, field) and getattr(incoming, field):
            setattr(merged, field, getattr(incoming, field))
    merged.authors = list(dict.fromkeys([*merged.authors, *incoming.authors]))
    merged.categories = sorted(set(merged.categories + incoming.categories))
    merged.taxonomy_tags = sorted(set(merged.taxonomy_tags + incoming.taxonomy_tags))
    merged.keywords_matched = sorted(set(merged.keywords_matched + incoming.keywords_matched))
    merged.negative_keywords_matched = sorted(set(merged.negative_keywords_matched + incoming.negative_keywords_matched))
    if incoming.relevance_score > merged.relevance_score:
        merged.relevance_score = incoming.relevance_score
        merged.relevance_label = incoming.relevance_label
        merged.reading_priority = incoming.reading_priority
        merged.reason = incoming.reason
    if incoming.source not in merged.source.split(", "):
        merged.source = f"{merged.source}, {incoming.source}"
    return merged


def deduplicate(records: Iterable[PaperRecord]) -> list[PaperRecord]:
    by_key: dict[str, PaperRecord] = {}
    canonical: list[PaperRecord] = []
    for record in records:
        keys = dedup_keys(record)
        match = next((by_key[key] for key in keys if key in by_key), None)
        if match is None:
            stored = copy_record(record)
            canonical.append(stored)
            for key in keys:
                by_key[key] = stored
            continue
        merged = merge_records(match, record)
        index = canonical.index(match)
        canonical[index] = merged
        for key in set(dedup_keys(merged) + keys):
            by_key[key] = merged
    return canonical

