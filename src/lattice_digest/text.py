from __future__ import annotations

import re
import unicodedata

SPACE_RE = re.compile(r"\s+")
TOKEN_BOUNDARY = r"(?<![a-z0-9]){}(?![a-z0-9])"


def normalize_whitespace(value: str | None) -> str:
    return SPACE_RE.sub(" ", (value or "").replace("\n", " ")).strip()


def normalize_title(title: str | None) -> str:
    text = unicodedata.normalize("NFKC", normalize_whitespace(title).lower())
    text = text.replace("-", " ")
    text = re.sub(r"[^\w\s.+#]", " ", text)
    text = SPACE_RE.sub(" ", text).strip()
    return text


def normalize_for_match(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", normalize_whitespace(value).lower())
    return SPACE_RE.sub(" ", text).strip()


def combined_text(*parts: str | None) -> str:
    return normalize_for_match(" ".join(part or "" for part in parts))


def term_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(normalize_for_match(term))
    escaped = escaped.replace(r"\ ", r"[\s-]+")
    escaped = escaped.replace(r"\-", r"[\s-]+")
    return re.compile(TOKEN_BOUNDARY.format(escaped), re.IGNORECASE)


def find_terms(text: str, terms: list[str]) -> list[str]:
    haystack = normalize_for_match(text)
    found: list[str] = []
    for term in terms:
        if not term:
            continue
        if term_pattern(term).search(haystack):
            found.append(term)
    return sorted(set(found), key=lambda item: item.lower())


def parse_duration_to_hours(value: str) -> int:
    raw = value.strip().lower()
    match = re.fullmatch(r"(\d+)\s*([hd])", raw)
    if not match:
        raise ValueError(f"Unsupported duration: {value}. Use forms like 36h or 7d.")
    amount = int(match.group(1))
    unit = match.group(2)
    return amount if unit == "h" else amount * 24
