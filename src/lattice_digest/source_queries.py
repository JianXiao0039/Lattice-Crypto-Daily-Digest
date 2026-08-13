from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class QueryRequest:
    family_id: str
    query_text: str


def _quote(term: str) -> str:
    value = str(term).strip()
    if not value:
        return ""
    if " " in value and not (value.startswith('"') and value.endswith('"')):
        return f'"{value}"'
    return value


def _plain_group(terms: Iterable[str]) -> str:
    rendered = [_quote(term) for term in terms if str(term).strip()]
    if len(rendered) == 1:
        return rendered[0]
    return "(" + " OR ".join(rendered) + ")"


def render_structured_query(spec: dict, *, syntax: str) -> str:
    groups = spec.get("all_of_groups") or []
    rendered_groups: list[str] = []
    for group in groups:
        terms = [str(item) for item in (group if isinstance(group, list) else [group]) if str(item).strip()]
        if not terms:
            continue
        if syntax == "arxiv":
            arxiv_terms = [f"all:{_quote(term)}" for term in terms]
            rendered_groups.append(arxiv_terms[0] if len(arxiv_terms) == 1 else "(" + " OR ".join(arxiv_terms) + ")")
        else:
            rendered_groups.append(_plain_group(terms))
    return " AND ".join(rendered_groups)


def critical_query_requests(config: dict, *, syntax: str) -> list[QueryRequest]:
    requests: list[QueryRequest] = []
    for spec in config.get("critical_query_groups", []):
        if not isinstance(spec, dict):
            continue
        family_id = str(spec.get("id") or "critical_lattice_security")
        if syntax == "free_text":
            groups = [group if isinstance(group, list) else [group] for group in spec.get("all_of_groups", [])]
            combinations: list[list[str]] = [[]]
            for group in groups:
                combinations = [prefix + [str(term)] for prefix in combinations for term in group if str(term).strip()]
            for index, combination in enumerate(combinations):
                query = " ".join(_quote(term) for term in combination)
                if query:
                    requests.append(QueryRequest(f"{family_id}_{index + 1:02d}", query))
        else:
            query = render_structured_query(spec, syntax=syntax)
            if query:
                requests.append(QueryRequest(family_id, query))
    return requests


def legacy_query_requests(config: dict, *, keys: tuple[str, ...]) -> list[QueryRequest]:
    for key in keys:
        values = config.get(key)
        if not values:
            continue
        requests: list[QueryRequest] = []
        for index, value in enumerate(values):
            if isinstance(value, list):
                query = _plain_group(str(item) for item in value)
            else:
                query = str(value).strip()
            if query:
                requests.append(QueryRequest(f"legacy_{key}_{index + 1:02d}", query))
        return requests
    return []
