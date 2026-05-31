from __future__ import annotations

from typing import Any

from lattice_digest.models import PaperRecord


SCHEMA_VERSION = 1

THRESHOLDS: dict[str, dict[str, int]] = {
    "A": {"min": 80, "max": 100},
    "B": {"min": 60, "max": 79},
    "C": {"min": 40, "max": 59},
    "D": {"min": 0, "max": 39},
}


def _stable_terms(values: list[str] | tuple[str, ...] | None) -> list[str]:
    if not values:
        return []
    return sorted({str(value).strip() for value in values if str(value).strip()}, key=str.lower)


def _contains_term(text: str, term: str) -> bool:
    return term.lower() in text.lower()


def _field_matches(record: PaperRecord, terms: list[str]) -> dict[str, list[str]]:
    fields = {
        "title": record.title or "",
        "abstract": record.abstract or "",
        "source": record.source or "",
        "venue": record.venue or "",
    }
    return {
        field: [term for term in terms if _contains_term(text, term)]
        for field, text in fields.items()
        if text and any(_contains_term(text, term) for term in terms)
    }


def build_ranking_explanation(record: PaperRecord) -> dict[str, Any]:
    keywords = _stable_terms(record.keywords_matched)
    taxonomy = _stable_terms(record.taxonomy_tags)
    negatives = _stable_terms(record.negative_keywords_matched)

    positive_signals: list[dict[str, Any]] = []
    if keywords:
        positive_signals.append(
            {
                "signal": "keyword_matches",
                "matches": keywords,
                "field_matches": _field_matches(record, keywords),
                "score_delta": None,
            }
        )
    if taxonomy:
        positive_signals.append(
            {
                "signal": "taxonomy_matches",
                "matches": taxonomy,
                "score_delta": None,
            }
        )
    if record.source or record.venue:
        positive_signals.append(
            {
                "signal": "source_context",
                "source": record.source,
                "venue": record.venue,
                "score_delta": None,
            }
        )

    negative_signals: list[dict[str, Any]] = []
    if negatives:
        negative_signals.append(
            {
                "signal": "negative_keyword_matches",
                "matches": negatives,
                "field_matches": _field_matches(record, negatives),
                "score_delta": None,
            }
        )
    if record.relevance_label == "D":
        negative_signals.append(
            {
                "signal": "filtered_or_low_relevance",
                "reason": record.reason,
                "score_delta": None,
            }
        )

    decision = "include" if record.relevance_label in {"A", "B", "C"} else "filter"
    notes = [record.reason] if record.reason else []
    if keywords or taxonomy:
        notes.append("Signals are derived from the existing ranker output; exact score deltas are not exposed.")

    return {
        "schema_version": SCHEMA_VERSION,
        "relevance_score": record.relevance_score,
        "relevance_label": record.relevance_label,
        "decision": decision,
        "matched_taxonomy": taxonomy,
        "positive_signals": positive_signals,
        "negative_signals": negative_signals,
        "thresholds": THRESHOLDS,
        "notes": notes,
    }


def concise_ranking_explanation(record: PaperRecord) -> str:
    explanation = build_ranking_explanation(record)
    keywords = _stable_terms(record.keywords_matched)
    taxonomy = _stable_terms(record.taxonomy_tags)
    negatives = _stable_terms(record.negative_keywords_matched)
    matched = [*keywords, *[tag for tag in taxonomy if tag not in keywords]]
    matched_text = ", ".join(matched[:8]) if matched else "no positive signals"
    negative_text = f"negative signals: {', '.join(negatives[:6])}" if negatives else "no negative signals"
    return (
        "Ranking: {label} / {score} — matched {matched}; {negative}.".format(
            label=explanation["relevance_label"],
            score=explanation["relevance_score"],
            matched=matched_text,
            negative=negative_text,
        )
    )
