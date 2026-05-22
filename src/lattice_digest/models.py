from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from lattice_digest.text import normalize_title


class PaperRecord(BaseModel):
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
    publication_date: str | None = None
    update_date: str | None = None
    categories: list[str] = Field(default_factory=list)
    taxonomy_tags: list[str] = Field(default_factory=list)
    keywords_matched: list[str] = Field(default_factory=list)
    negative_keywords_matched: list[str] = Field(default_factory=list)
    relevance_score: int = 0
    relevance_label: str = "D"
    reason: str = ""
    reading_priority: int = 99

    class Config:
        extra = "forbid"
        validate_assignment = True


def make_paper_record(**data: Any) -> PaperRecord:
    title = str(data.get("title") or "").strip()
    data["title"] = title
    data.setdefault("normalized_title", normalize_title(title))
    data.setdefault("chinese_title", title)
    data.setdefault("authors", [])
    data.setdefault("abstract", "")
    data.setdefault("categories", [])
    data.setdefault("taxonomy_tags", [])
    data.setdefault("keywords_matched", [])
    data.setdefault("negative_keywords_matched", [])
    return PaperRecord(**data)


def record_to_dict(record: PaperRecord) -> dict[str, Any]:
    if hasattr(record, "model_dump"):
        return record.model_dump(mode="json")
    return record.dict()


def copy_record(record: PaperRecord) -> PaperRecord:
    if hasattr(record, "model_copy"):
        return record.model_copy(deep=True)
    return record.copy(deep=True)

