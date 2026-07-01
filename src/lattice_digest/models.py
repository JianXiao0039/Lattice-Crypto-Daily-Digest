from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from lattice_digest.text import normalize_title


class PaperRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    title: str
    normalized_title: str = ""
    chinese_title: str = ""
    authors: list[str] = Field(default_factory=list)
    abstract: str = ""
    source: str
    source_url: str
    pdf_url: str | None = None
    paper_id: str | None = None
    arxiv_id: str | None = None
    eprint_id: str | None = None
    doi: str | None = None
    venue: str | None = None
    venue_type: str = "unknown"
    publisher_or_source: str = "unknown"
    CCF_rank: str = "unknown"
    venue_status: str = "unknown"
    venue_expanded_security_crypto_systems_scope: bool = False
    venue_relevance: str = "peripheral"
    venue_confidence: str = "low"
    publication_date: str | None = None
    announcement_date: str | None = None
    update_date: str | None = None
    first_seen_date: str | None = None
    official_status_change_date: str | None = None
    source_metadata_correction_date: str | None = None
    manually_requested_backfill_date: str | None = None
    selected_date_basis: str = "TODO_VERIFY"
    freshness_bucket: str = "date_uncertain_todo_verify"
    freshness_reason: str = ""
    primary_today_new_eligible: bool = False
    categories: list[str] = Field(default_factory=list)
    taxonomy_tags: list[str] = Field(default_factory=list)
    keywords_matched: list[str] = Field(default_factory=list)
    negative_keywords_matched: list[str] = Field(default_factory=list)
    relevance_score: int = 0
    relevance_label: str = "D"
    reason: str = ""
    reading_priority: int = 99
    title_en: str = ""
    title_zh: str = ""
    abstract_en: str = ""
    abstract_zh: str = ""
    conclusion: str = ""
    conclusion_en: str = ""
    conclusion_zh: str = ""
    lattice_crypto_relevance: str = ""
    recommendation_level: str = "TODO_VERIFY"
    recommendation_score: int = 0
    recommendation_reason: str = ""
    TODO_VERIFY_flags: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    evidence_tier: str = ""
    source_health: str = ""


def make_paper_record(**data: Any) -> PaperRecord:
    title = str(data.get("title") or "").strip()
    data["title"] = title
    data.setdefault("normalized_title", normalize_title(title))
    data.setdefault("chinese_title", title)
    data.setdefault("title_en", title)
    data.setdefault("title_zh", data.get("chinese_title") or title)
    data.setdefault("authors", [])
    data.setdefault("abstract", "")
    data.setdefault("abstract_en", data.get("abstract") or "")
    data.setdefault("categories", [])
    data.setdefault("taxonomy_tags", [])
    data.setdefault("keywords_matched", [])
    data.setdefault("negative_keywords_matched", [])
    return PaperRecord(**data)


def record_to_dict(record: PaperRecord) -> dict[str, Any]:
    return record.model_dump(mode="json")


def copy_record(record: PaperRecord) -> PaperRecord:
    return record.model_copy(deep=True)
