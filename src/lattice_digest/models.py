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
    publication_timestamp: str | None = None
    publication_date_kind: str = "AUTHORITATIVE_PUBLICATION_DATE"
    announcement_date: str | None = None
    announcement_date_kind: str = "AUTHORITATIVE_ANNOUNCEMENT_DATE"
    update_date: str | None = None
    update_timestamp: str | None = None
    update_date_kind: str = "AUTHORITATIVE_CONTENT_REVISION_DATE"
    first_seen_date: str | None = None
    first_seen_at: str | None = None
    source_observed_at: str | None = None
    document_claimed_date: str | None = None
    official_status_change_date: str | None = None
    source_metadata_correction_date: str | None = None
    manually_requested_backfill_date: str | None = None
    selected_date_basis: str = "TODO_VERIFY"
    freshness_bucket: str = "date_uncertain_todo_verify"
    freshness_reason: str = ""
    primary_today_new_eligible: bool = False
    freshness_policy_version: str = ""
    cross_day_event: str = ""
    prior_promotion_dates: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    taxonomy_tags: list[str] = Field(default_factory=list)
    keywords_matched: list[str] = Field(default_factory=list)
    source_evidence_terms: list[str] = Field(default_factory=list)
    inferred_topic_tags: list[str] = Field(default_factory=list)
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
    user_relevance_tags: list[str] = Field(default_factory=list)
    phd_application_relevance: str = ""
    recommendation_risk_flags: list[str] = Field(default_factory=list)
    recommendation_evidence_basis: list[str] = Field(default_factory=list)
    recommendation_score_breakdown: dict[str, int] = Field(default_factory=dict)
    research_value_score: int = 0
    primary_action_allowed: bool = False
    suggested_action: str = ""
    TODO_VERIFY_flags: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    evidence_tier: str = ""
    source_health: str = ""
    security_impact_severity: str = "UNKNOWN"
    evidence_confidence: str = "TODO_VERIFY"
    document_maturity: str = "unknown"
    critical_signal_relations: list[dict[str, str]] = Field(default_factory=list)
    critical_signal_explanation: str = ""
    critical_claim_zh: str = ""
    translation_fidelity_status: str = "not_applicable"
    translation_fidelity_flags: list[str] = Field(default_factory=list)
    source_query_family: str = ""
    source_query_text: str = ""
    retrieval_timestamp: str = ""
    observability_route: str = "OBSERVED_PENDING_EVIDENCE"
    observability_reasons: list[str] = Field(default_factory=list)
    raw_occurrence_ids: list[str] = Field(default_factory=list)
    source_ids: list[dict[str, str]] = Field(default_factory=list)
    query_ids: list[str] = Field(default_factory=list)
    date_evidence: list[dict[str, str | None]] = Field(default_factory=list)
    evidence_versions: list[dict[str, Any]] = Field(default_factory=list)
    content_hashes: list[str] = Field(default_factory=list)
    version_relations: list[dict[str, str]] = Field(default_factory=list)
    conflicting_metadata: list[dict[str, Any]] = Field(default_factory=list)
    merge_rationale: list[str] = Field(default_factory=list)
    provenance_strength: str = "unknown"
    merge_proposals: list[dict[str, Any]] = Field(default_factory=list)
    consequence_edges: list[dict[str, Any]] = Field(default_factory=list)
    enrichment_events: list[dict[str, Any]] = Field(default_factory=list)


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
    data.setdefault("source_evidence_terms", [])
    data.setdefault("inferred_topic_tags", [])
    data.setdefault("negative_keywords_matched", [])
    return PaperRecord(**data)


def record_to_dict(record: PaperRecord) -> dict[str, Any]:
    return record.model_dump(mode="json")


def copy_record(record: PaperRecord) -> PaperRecord:
    return record.model_copy(deep=True)
