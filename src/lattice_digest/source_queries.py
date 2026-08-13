from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Iterable


@dataclass(frozen=True)
class QueryRequest:
    family_id: str
    query_text: str
    query_id: str = ""
    intent: str = "DISCOVERY"
    source_family: str = "unknown"
    expected_topic: str = "lattice_cryptography"
    critical_security_relevant: bool = False
    cost_rate_limit_risk: str = "MEDIUM"
    enabled: bool = True
    compatibility_version: str = "v1"
    native_syntax: str = "plain"

    def __post_init__(self) -> None:
        if not self.query_id:
            object.__setattr__(
                self,
                "query_id",
                stable_query_id(self.source_family, self.family_id, version=self.compatibility_version),
            )

    @property
    def query_family(self) -> str:
        return self.family_id

    @property
    def expression_hash(self) -> str:
        return hashlib.sha256(self.query_text.encode("utf-8")).hexdigest()

    def to_diagnostic_dict(self) -> dict[str, object]:
        return {
            "query_id": self.query_id,
            "query_family": self.family_id,
            "intent": self.intent,
            "source_family": self.source_family,
            "source_native_expression": self.query_text,
            "query_expression_hash": self.expression_hash,
            "expected_topic": self.expected_topic,
            "critical_security_relevant": self.critical_security_relevant,
            "cost_rate_limit_risk": self.cost_rate_limit_risk,
            "enabled": self.enabled,
            "compatibility_version": self.compatibility_version,
            "native_syntax": self.native_syntax,
        }


def _slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-") or "UNKNOWN"


def stable_query_id(source_family: str, family_id: str, *, version: str = "v1") -> str:
    return f"Q-{_slug(source_family)}-{_slug(family_id)}-{_slug(version)}"


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
    source_family = str(config.get("name") or config.get("type") or "unknown")
    version = str(config.get("query_portfolio_version") or "v1")
    cost = str(config.get("query_cost_rate_limit_risk") or "MEDIUM").upper()
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
                    variant_family = f"{family_id}_{index + 1:02d}"
                    requests.append(
                        QueryRequest(
                            variant_family,
                            query,
                            query_id=stable_query_id(source_family, variant_family, version=version),
                            intent="CRITICAL_SECURITY_DISCOVERY",
                            source_family=source_family,
                            expected_topic="quantum_lattice_security",
                            critical_security_relevant=True,
                            cost_rate_limit_risk=cost,
                            compatibility_version=version,
                            native_syntax=syntax,
                        )
                    )
        else:
            query = render_structured_query(spec, syntax=syntax)
            if query:
                requests.append(
                    QueryRequest(
                        family_id,
                        query,
                        query_id=stable_query_id(source_family, family_id, version=version),
                        intent="CRITICAL_SECURITY_DISCOVERY",
                        source_family=source_family,
                        expected_topic="quantum_lattice_security",
                        critical_security_relevant=True,
                        cost_rate_limit_risk=cost,
                        compatibility_version=version,
                        native_syntax=syntax,
                    )
                )
    return requests


def legacy_query_requests(config: dict, *, keys: tuple[str, ...]) -> list[QueryRequest]:
    source_family = str(config.get("name") or config.get("type") or "unknown")
    version = str(config.get("query_portfolio_version") or "v1")
    intent = str(config.get("default_query_intent") or "DISCOVERY").upper()
    cost = str(config.get("query_cost_rate_limit_risk") or "MEDIUM").upper()
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
                family_id = f"legacy_{key}_{index + 1:02d}"
                requests.append(
                    QueryRequest(
                        family_id,
                        query,
                        query_id=stable_query_id(source_family, family_id, version=version),
                        intent=intent,
                        source_family=source_family,
                        expected_topic=str(config.get("expected_topic") or "lattice_cryptography"),
                        critical_security_relevant=False,
                        cost_rate_limit_risk=cost,
                        compatibility_version=version,
                        native_syntax=str(config.get("query_native_syntax") or "free_text"),
                    )
                )
        return requests
    return []


def native_feed_query_request(config: dict, *, family_id: str, expression: str) -> QueryRequest:
    source_family = str(config.get("name") or config.get("type") or "unknown")
    version = str(config.get("query_portfolio_version") or "v1")
    return QueryRequest(
        family_id,
        expression,
        query_id=stable_query_id(source_family, family_id, version=version),
        intent=str(config.get("default_query_intent") or "DISCOVERY").upper(),
        source_family=source_family,
        expected_topic="lattice_cryptography",
        critical_security_relevant=False,
        cost_rate_limit_risk=str(config.get("query_cost_rate_limit_risk") or "LOW").upper(),
        compatibility_version=version,
        native_syntax="native_feed",
    )


def query_portfolio_for_source(config: dict) -> list[QueryRequest]:
    source_type = str(config.get("type") or config.get("name") or "")
    if source_type == "iacr_eprint":
        return [native_feed_query_request(config, family_id="native_iacr_latest_feed", expression=str(config.get("url") or ""))]
    syntax = "arxiv" if source_type == "arxiv" else "free_text" if source_type in {"dblp", "crossref"} else "plain"
    requests = critical_query_requests(config, syntax=syntax)
    keys = ("query_groups", "query_terms")
    if source_type == "dblp":
        keys = ("queries",)
    requests.extend(legacy_query_requests(config, keys=keys))
    return [request for request in requests if request.enabled]
