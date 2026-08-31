from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Iterable

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from lattice_digest.consequence_graph_v3 import RelationType


class QueryFamilyV3(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    family_id: str
    intent: str
    concept_ids: tuple[str, ...]
    relation_types: tuple[RelationType, ...]
    expected_positives: tuple[str, ...]
    required_coanchors: tuple[str, ...] = ()
    hard_negatives: tuple[str, ...] = ()
    cost_class: str
    expected_recall_contribution: str
    expected_precision_risk: str
    budget: int = Field(ge=1, le=100)
    cadence: str
    source_native: dict[str, str]

    @model_validator(mode="after")
    def _native_expressions_are_bounded(self) -> "QueryFamilyV3":
        if not self.source_native:
            raise ValueError(f"{self.family_id} has no source-native expression")
        if any(len(expression) > 1000 for expression in self.source_native.values()):
            raise ValueError(f"{self.family_id} contains an unbounded giant query")
        return self


class QueryPortfolioDocumentV3(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    portfolio_id: str
    activation: str
    families: tuple[QueryFamilyV3, ...]

    @model_validator(mode="after")
    def _family_ids_are_unique(self) -> "QueryPortfolioDocumentV3":
        family_ids = [family.family_id for family in self.families]
        if len(set(family_ids)) != len(family_ids):
            raise ValueError("V3 query family IDs must be unique")
        if self.activation not in {"shadow", "active"}:
            raise ValueError("query portfolio activation must be shadow or active")
        return self


class CompiledQueryV3(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    query_id: str
    family_id: str
    source: str
    intent: str
    native_semantics: str
    concept_ids: tuple[str, ...]
    relation_types: tuple[RelationType, ...]
    expected_positives: tuple[str, ...]
    required_coanchors: tuple[str, ...]
    hard_negatives: tuple[str, ...]
    cost_class: str
    expected_recall_contribution: str
    expected_precision_risk: str
    budget: int
    cadence: str


class QueryPortfolioV3:
    def __init__(self, document: QueryPortfolioDocumentV3) -> None:
        self.document = document

    @property
    def production_active(self) -> bool:
        return self.document.activation == "active"

    def compile_for_sources(self, sources: Iterable[str]) -> tuple[CompiledQueryV3, ...]:
        allowed = set(sources)
        queries: list[CompiledQueryV3] = []
        for family in self.document.families:
            for source, expression in family.source_native.items():
                if source not in allowed:
                    continue
                queries.append(
                    CompiledQueryV3(
                        query_id=f"{family.family_id}:{source}:v3",
                        family_id=family.family_id,
                        source=source,
                        intent=family.intent,
                        native_semantics=expression,
                        concept_ids=family.concept_ids,
                        relation_types=family.relation_types,
                        expected_positives=family.expected_positives,
                        required_coanchors=family.required_coanchors,
                        hard_negatives=family.hard_negatives,
                        cost_class=family.cost_class,
                        expected_recall_contribution=family.expected_recall_contribution,
                        expected_precision_risk=family.expected_precision_risk,
                        budget=family.budget,
                        cadence=family.cadence,
                    )
                )
        return tuple(queries)

    def fair_schedule(
        self,
        sources: Iterable[str],
        *,
        global_budget: int,
        per_source_budget: int,
    ) -> tuple[CompiledQueryV3, ...]:
        compiled = self.compile_for_sources(sources)
        by_family: dict[str, deque[CompiledQueryV3]] = defaultdict(deque)
        for query in compiled:
            by_family[query.family_id].append(query)
        source_counts: dict[str, int] = defaultdict(int)
        family_counts: dict[str, int] = defaultdict(int)
        scheduled: list[CompiledQueryV3] = []
        family_order = deque(sorted(by_family))
        while family_order and len(scheduled) < max(0, global_budget):
            progress = False
            round_size = len(family_order)
            for _ in range(round_size):
                family_id = family_order.popleft()
                queue = by_family[family_id]
                selected = None
                rotations = len(queue)
                for _ in range(rotations):
                    candidate = queue.popleft()
                    if source_counts[candidate.source] < per_source_budget and family_counts[family_id] < candidate.budget:
                        selected = candidate
                        break
                    queue.append(candidate)
                if selected is not None:
                    scheduled.append(selected)
                    source_counts[selected.source] += 1
                    family_counts[family_id] += 1
                    progress = True
                if queue and family_counts[family_id] < max(item.budget for item in queue):
                    family_order.append(family_id)
                if len(scheduled) >= max(0, global_budget):
                    break
            if not progress:
                break
        return tuple(scheduled)


def load_query_portfolio_v3(path: Path | None = None) -> QueryPortfolioV3:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "query_portfolio_v3.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return QueryPortfolioV3(QueryPortfolioDocumentV3.model_validate(payload))
