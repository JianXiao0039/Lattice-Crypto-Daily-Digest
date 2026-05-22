from __future__ import annotations

from lattice_digest.models import PaperRecord
from lattice_digest.text import combined_text, find_terms, term_pattern


def _flatten_terms(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        terms: list[str] = []
        for item in value:
            terms.extend(_flatten_terms(item))
        return terms
    if isinstance(value, dict):
        terms = []
        for item in value.values():
            terms.extend(_flatten_terms(item))
        return terms
    return []


def hard_negative_terms(negative_config: dict) -> list[str]:
    terms = []
    terms.extend(_flatten_terms(negative_config.get("hard_negative", {})))
    terms.extend(_flatten_terms(negative_config.get("negative_lattice_context", [])))
    terms.extend(_flatten_terms(negative_config.get("negative_subject_terms", [])))
    return sorted(set(terms), key=str.lower)


def soft_negative_terms(negative_config: dict) -> list[str]:
    return sorted(set(_flatten_terms(negative_config.get("soft_negative", []))), key=str.lower)


def required_context_terms(keyword_config: dict, negative_config: dict | None = None) -> list[str]:
    terms = []
    terms.extend(_flatten_terms(keyword_config.get("required_crypto_context", [])))
    terms.extend(_flatten_terms(keyword_config.get("crypto_context", [])))
    if negative_config:
        terms.extend(_flatten_terms(negative_config.get("crypto_context_required_if_only_lattice", [])))
    return sorted(set(terms), key=str.lower)


def negative_matches(record: PaperRecord, negative_config: dict) -> list[str]:
    terms = hard_negative_terms(negative_config) + soft_negative_terms(negative_config)
    text = combined_text(record.title, record.abstract, record.venue)
    return find_terms(text, terms)


def crypto_context_matches(record: PaperRecord, keyword_config: dict) -> list[str]:
    terms = []
    terms.extend(keyword_config.get("high_signal", []))
    terms.extend(keyword_config.get("medium_signal", []))
    terms.extend(keyword_config.get("crypto_context", []))
    text = combined_text(record.title, record.abstract, record.venue, " ".join(record.categories))
    return find_terms(text, terms)


def required_crypto_context_matches(record: PaperRecord, keyword_config: dict) -> list[str]:
    text = combined_text(record.title, record.abstract, record.venue, " ".join(record.categories))
    return find_terms(text, keyword_config.get("required_crypto_context", keyword_config.get("crypto_context", [])))


def has_lattice_word_only(record: PaperRecord, keyword_config: dict) -> bool:
    text = combined_text(record.title, record.abstract)
    if not term_pattern("lattice").search(text):
        return False
    return not crypto_context_matches(record, keyword_config)


def should_exclude_as_negative(record: PaperRecord, keyword_config: dict, negative_config: dict) -> tuple[bool, list[str]]:
    text = combined_text(record.title, record.abstract, record.venue)
    hard_matches = find_terms(text, hard_negative_terms(negative_config))
    soft_matches = find_terms(text, soft_negative_terms(negative_config))
    negatives = sorted(set(hard_matches + soft_matches), key=str.lower)
    if not negatives:
        return False, []
    context = find_terms(
        combined_text(record.title, record.abstract, record.venue, " ".join(record.categories)),
        required_context_terms(keyword_config, negative_config),
    )
    if context:
        return False, negatives
    return bool(hard_matches), negatives
