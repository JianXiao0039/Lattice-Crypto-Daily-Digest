from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
from typing import Iterable, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


EvidencePolicy = Literal[
    "SOURCE_TERM_OR_TYPED_EDGE",
    "SOURCE_TERM_WITH_COANCHOR_FOR_ACRONYM",
    "SOURCE_TERM_WITH_COANCHOR_FOR_AMBIGUOUS_ALIAS",
    "TYPED_REDUCTION_PATH_REQUIRED",
    "TARGET_COANCHOR_REQUIRED_FOR_GENERIC_METHOD",
    "LATTICE_COANCHOR_REQUIRED",
    "LATTICE_ASSUMPTION_EDGE_REQUIRED",
    "LATTICE_SCHEME_COANCHOR_REQUIRED",
    "CRYPTOGRAPHIC_CONTRIBUTION_REQUIRED",
    "LATTICE_SIGNATURE_COANCHOR_REQUIRED",
    "LATTICE_ATTACK_COANCHOR_REQUIRED",
    "OFFICIAL_SOURCE_OR_SCHEME_COANCHOR_REQUIRED",
]


class OntologyConcept(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    concept_id: str
    canonical_name: str
    domain: str
    aliases: tuple[str, ...] = ()
    source_grounded_terms: tuple[str, ...] = ()
    inferred_tags: tuple[str, ...] = ()
    parents: tuple[str, ...] = ()
    children: tuple[str, ...] = ()
    consequence_relations: tuple[str, ...] = ()
    neighboring_topics: tuple[str, ...] = ()
    hard_negatives: tuple[str, ...] = ()
    evidence_policy: EvidencePolicy

    @model_validator(mode="after")
    def _evidence_and_inference_are_disjoint(self) -> "OntologyConcept":
        evidence = {_normal(term) for term in self.source_grounded_terms}
        inferred = {_normal(term) for term in self.inferred_tags}
        overlap = evidence.intersection(inferred)
        if overlap:
            raise ValueError(f"source evidence and inferred tags overlap for {self.concept_id}: {sorted(overlap)}")
        if not self.concept_id or "." not in self.concept_id:
            raise ValueError("concept_id must be a namespaced identifier")
        return self


class OntologyDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    ontology_id: str
    concepts: tuple[OntologyConcept, ...]

    @model_validator(mode="after")
    def _validate_graph_references(self) -> "OntologyDocument":
        identifiers = [concept.concept_id for concept in self.concepts]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("ontology concept IDs must be unique")
        known = set(identifiers)
        for concept in self.concepts:
            missing = set(concept.parents + concept.children + concept.neighboring_topics) - known
            if missing:
                raise ValueError(f"unknown concept reference from {concept.concept_id}: {sorted(missing)}")
        return self


class SourceEvidenceMatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    concept_id: str
    source_field: Literal["title", "abstract", "keywords", "conclusion"]
    source_term: str
    source_span: str


class OntologyAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_evidence: tuple[SourceEvidenceMatch, ...] = ()
    inferred_tags: tuple[str, ...] = ()
    hard_negative_matches: tuple[str, ...] = ()

    @property
    def source_concept_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(match.concept_id for match in self.source_evidence))


class OntologyRegistry:
    def __init__(self, document: OntologyDocument) -> None:
        self.document = document
        self.by_id = {concept.concept_id: concept for concept in document.concepts}
        self.by_domain: dict[str, tuple[OntologyConcept, ...]] = {
            domain: tuple(items)
            for domain, items in _group_by_domain(document.concepts).items()
        }

    def analyze_fields(
        self,
        *,
        title: str,
        abstract: str = "",
        keywords: Iterable[str] = (),
        conclusion: str = "",
    ) -> OntologyAnalysis:
        fields = {
            "title": str(title or ""),
            "abstract": str(abstract or ""),
            "keywords": " ".join(str(item) for item in keywords),
            "conclusion": str(conclusion or ""),
        }
        crypto_context = _has_crypto_context(" ".join(fields.values()))
        evidence: list[SourceEvidenceMatch] = []
        hard_negatives: set[str] = set()
        source_concepts: set[str] = set()
        for concept in self.document.concepts:
            matched_negative = {
                negative
                for negative in concept.hard_negatives
                if _contains_phrase(" ".join(fields.values()), negative)
            }
            hard_negatives.update(matched_negative)
            for field_name, text in fields.items():
                for term in concept.source_grounded_terms:
                    span = _matching_span(text, term)
                    if not span:
                        continue
                    if not _policy_allows_source_match(concept, term, fields, crypto_context):
                        continue
                    evidence.append(
                        SourceEvidenceMatch(
                            concept_id=concept.concept_id,
                            source_field=field_name,
                            source_term=term,
                            source_span=span,
                        )
                    )
                    source_concepts.add(concept.concept_id)
        inferred: list[str] = []
        for concept_id in sorted(source_concepts):
            concept = self.by_id[concept_id]
            inferred.extend(concept.inferred_tags)
            inferred.extend(f"parent:{item}" for item in concept.parents)
            inferred.extend(f"neighbor:{item}" for item in concept.neighboring_topics)
        return OntologyAnalysis(
            source_evidence=tuple(evidence),
            inferred_tags=tuple(dict.fromkeys(inferred)),
            hard_negative_matches=tuple(sorted(hard_negatives, key=str.lower)),
        )


def load_ontology_v3(path: Path | None = None) -> OntologyRegistry:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "retrieval_ontology_v3.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return OntologyRegistry(OntologyDocument.model_validate(payload))


def _group_by_domain(concepts: Iterable[OntologyConcept]) -> dict[str, list[OntologyConcept]]:
    grouped: dict[str, list[OntologyConcept]] = defaultdict(list)
    for concept in concepts:
        grouped[concept.domain].append(concept)
    return grouped


def _normal(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    return bool(_matching_span(text, phrase))


def _matching_span(text: str, phrase: str) -> str:
    normalized_phrase = _normal(phrase)
    if not normalized_phrase:
        return ""
    normalized_text = _normal(text)
    pattern = r"(?<![a-z0-9])" + re.escape(normalized_phrase).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
    match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
    return match.group(0) if match else ""


def _has_crypto_context(text: str) -> bool:
    anchors = (
        "cryptograph", "cryptanalysis", "post quantum", "lwe", "rlwe", "mlwe", "sis", "ntru",
        "svp", "cvp", "lattice reduction", "bkz", "kem", "signature", "zero knowledge", "fhe",
        "homomorphic encryption", "ml kem", "ml dsa", "falcon", "hawk",
    )
    normalized = _normal(text)
    return any(anchor in normalized for anchor in anchors)


def _policy_allows_source_match(
    concept: OntologyConcept,
    term: str,
    fields: dict[str, str],
    crypto_context: bool,
) -> bool:
    all_text = " ".join(fields.values())
    policy = concept.evidence_policy
    if policy == "SOURCE_TERM_OR_TYPED_EDGE":
        return True
    if policy == "TYPED_REDUCTION_PATH_REQUIRED":
        return True
    if policy in {
        "SOURCE_TERM_WITH_COANCHOR_FOR_ACRONYM",
        "SOURCE_TERM_WITH_COANCHOR_FOR_AMBIGUOUS_ALIAS",
    }:
        return len(_normal(term)) > 8 or crypto_context
    if policy == "TARGET_COANCHOR_REQUIRED_FOR_GENERIC_METHOD":
        return crypto_context
    if policy in {
        "LATTICE_COANCHOR_REQUIRED",
        "LATTICE_ASSUMPTION_EDGE_REQUIRED",
        "LATTICE_SCHEME_COANCHOR_REQUIRED",
        "LATTICE_SIGNATURE_COANCHOR_REQUIRED",
        "LATTICE_ATTACK_COANCHOR_REQUIRED",
    }:
        return crypto_context
    if policy == "CRYPTOGRAPHIC_CONTRIBUTION_REQUIRED":
        contribution = _normal(all_text)
        return crypto_context and any(
            token in contribution
            for token in (
                "security", "scheme", "protocol", "algorithm", "bootstrap", "implementation", "attack",
                "construction", "improve", "performance",
            )
        )
    if policy == "OFFICIAL_SOURCE_OR_SCHEME_COANCHOR_REQUIRED":
        return crypto_context
    return False
