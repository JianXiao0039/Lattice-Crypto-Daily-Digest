from __future__ import annotations

from collections import defaultdict, deque
from enum import StrEnum
import re
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RelationType(StrEnum):
    MENTIONS = "MENTIONS"
    SOLVES = "SOLVES"
    REDUCES_TO = "REDUCES_TO"
    ATTACKS = "ATTACKS"
    IMPROVES = "IMPROVES"
    INSTANTIATES = "INSTANTIATES"
    USES_ASSUMPTION = "USES_ASSUMPTION"
    TARGETS_SCHEME = "TARGETS_SCHEME"
    AFFECTS_SECURITY = "AFFECTS_SECURITY"
    IMPLEMENTS = "IMPLEMENTS"
    ACCELERATES = "ACCELERATES"
    PROVES_HARDNESS = "PROVES_HARDNESS"
    PROVES_REDUCTION = "PROVES_REDUCTION"
    VERSION_OF = "VERSION_OF"
    SPECIALIZES = "SPECIALIZES"
    GENERALIZES = "GENERALIZES"


class EdgeEvidenceState(StrEnum):
    SOURCE_ASSERTED = "SOURCE_ASSERTED"
    SOURCE_CITED = "SOURCE_CITED"
    INFERRED_HYPOTHESIS = "INFERRED_HYPOTHESIS"
    INDEPENDENTLY_VERIFIED = "INDEPENDENTLY_VERIFIED"


class ClaimStatus(StrEnum):
    PAPER_FACT = "PAPER_FACT"
    PRELIMINARY = "PRELIMINARY"
    PROVED = "PROVED"
    PROVED_UNDER_CONDITIONS = "PROVED_UNDER_CONDITIONS"
    EMPIRICAL = "EMPIRICAL"
    TODO_VERIFY = "TODO_VERIFY"
    MODEL_INFERENCE = "MODEL_INFERENCE"


SOURCE_GROUNDED_STATES = {
    EdgeEvidenceState.SOURCE_ASSERTED,
    EdgeEvidenceState.SOURCE_CITED,
    EdgeEvidenceState.INDEPENDENTLY_VERIFIED,
}


class ConsequenceEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_node: str
    relation_type: RelationType
    target_node: str
    direction: str = "source_to_target"
    evidence_state: EdgeEvidenceState
    evidence_source: str
    evidence_span: str
    source_url: str
    confidence: float = Field(ge=0.0, le=1.0)
    qualifier: str = ""
    claim_status: ClaimStatus = ClaimStatus.PAPER_FACT
    critical_eligible: bool = False

    @model_validator(mode="after")
    def _critical_edges_require_source_evidence(self) -> "ConsequenceEdge":
        if self.critical_eligible and self.evidence_state not in SOURCE_GROUNDED_STATES:
            raise ValueError("critical consequence edge must be source-grounded or independently verified")
        if self.evidence_state in SOURCE_GROUNDED_STATES:
            if not self.evidence_span or not self.source_url or not self.evidence_source:
                raise ValueError("source-grounded edge requires source URL, field/page, and evidence span")
        if self.evidence_state == EdgeEvidenceState.INFERRED_HYPOTHESIS and self.claim_status != ClaimStatus.MODEL_INFERENCE:
            raise ValueError("inferred graph edges must carry MODEL_INFERENCE claim status")
        return self


class ConsequencePath(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    nodes: tuple[str, ...]
    edges: tuple[ConsequenceEdge, ...]
    critical: bool


class ConsequenceGraph:
    def __init__(self, edges: Iterable[ConsequenceEdge] = ()) -> None:
        self.edges = tuple(edges)
        self._outgoing: dict[str, list[ConsequenceEdge]] = defaultdict(list)
        for edge in self.edges:
            self._outgoing[edge.source_node].append(edge)

    def paths_from(
        self,
        start_nodes: Iterable[str],
        target_nodes: set[str],
        *,
        critical: bool = False,
        max_hops: int | None = None,
    ) -> tuple[ConsequencePath, ...]:
        hop_limit = 3 if critical else 2
        if max_hops is not None:
            hop_limit = min(hop_limit, max_hops)
        queue: deque[tuple[str, tuple[str, ...], tuple[ConsequenceEdge, ...]]] = deque(
            (node, (node,), ()) for node in dict.fromkeys(start_nodes)
        )
        results: list[ConsequencePath] = []
        visited: set[tuple[str, int]] = set()
        while queue:
            node, nodes, edges = queue.popleft()
            if edges and node in target_nodes:
                if not critical or all(edge.critical_eligible and edge.evidence_state in SOURCE_GROUNDED_STATES for edge in edges):
                    results.append(ConsequencePath(nodes=nodes, edges=edges, critical=critical))
            if len(edges) >= hop_limit:
                continue
            state = (node, len(edges))
            if state in visited:
                continue
            visited.add(state)
            for edge in self._outgoing.get(node, []):
                if edge.target_node in nodes:
                    continue
                if critical and (not edge.critical_eligible or edge.evidence_state not in SOURCE_GROUNDED_STATES):
                    continue
                queue.append((edge.target_node, (*nodes, edge.target_node), (*edges, edge)))
        return tuple(results)


def extract_record_edges(
    *,
    paper_node: str,
    title: str,
    abstract: str,
    conclusion: str,
    source_url: str,
    source_concept_ids: Iterable[str],
) -> tuple[ConsequenceEdge, ...]:
    """Extract conservative typed edges from paper-supplied evidence.

    The extractor never reverses a reduction and never upgrades an inferred
    neighboring topic into source evidence. It deliberately emits
    MODEL_INFERENCE for unsupported relation hypotheses.
    """

    fields = {"title": title or "", "abstract": abstract or "", "conclusion": conclusion or ""}
    text = " ".join(fields.values())
    normalized = _normal(text)
    edges: list[ConsequenceEdge] = []

    for concept_id in dict.fromkeys(source_concept_ids):
        span, field = _first_span(fields, _concept_anchor(concept_id))
        if not span:
            span, field = _first_nonempty(fields)
        edges.append(
            ConsequenceEdge(
                source_node=paper_node,
                relation_type=_direct_relation(concept_id),
                target_node=concept_id,
                evidence_state=EdgeEvidenceState.SOURCE_ASSERTED,
                evidence_source=field,
                evidence_span=span,
                source_url=source_url,
                confidence=0.92,
                qualifier="direct source-grounded concept occurrence",
                claim_status=ClaimStatus.PAPER_FACT,
                critical_eligible=False,
            )
        )

    if _all(normalized, "quaternion", ("bkz", "lll", "lattice reduction"), ("mlip", "module lip", "module lattice isomorphism")):
        edges.extend(
            _source_edges(
                paper_node,
                fields,
                source_url,
                [(RelationType.IMPROVES, "ATTACK.QUATERNION"), (RelationType.ATTACKS, "FND.MLIP")],
                qualifier="quaternion reduction to MLIP relevance; does not by itself establish a HAWK attack",
            )
        )
    if _all(normalized, ("principal", "ideal", "cyclotomic"), ("cvp", "closest vector"), ("hardness", "hard", "np")):
        edges.extend(
            _source_edges(
                paper_node,
                fields,
                source_url,
                [(RelationType.PROVES_HARDNESS, "HARD.STRUCTURED_CVP")],
                qualifier="hardness claim preserved at the structured-CVP scope",
                claim_status=ClaimStatus.PAPER_FACT,
            )
        )
    if _all(normalized, ("threshold", "distributed"), ("zero knowledge", "commit and prove", "exact relation"), ("hint mlwe", "module lwe", "lattice")):
        edges.extend(
            _source_edges(
                paper_node,
                fields,
                source_url,
                [
                    (RelationType.USES_ASSUMPTION, "FND.MLWE"),
                    (RelationType.INSTANTIATES, "PROOF.THRESHOLD_ZK"),
                ],
                qualifier="threshold/exact proof relation with an explicit lattice assumption",
            )
        )
    if _all(normalized, ("rejection sampling", "iterative rejection"), ("fiat shamir", "lattice signature", "ml dsa", "dilithium")):
        edges.extend(
            _source_edges(
                paper_node,
                fields,
                source_url,
                [
                    (RelationType.ACCELERATES, "PROOF.FIAT_SHAMIR"),
                    (RelationType.IMPLEMENTS, "PRIM.LATTICE_SIGNATURE"),
                ],
                qualifier="sampling contribution is scoped to the stated signature/proof target",
            )
        )
    if _all(normalized, ("module ntru", "ntru variant"), ("encryption", "cryptanalysis", "problem")):
        edges.extend(
            _source_edges(
                paper_node,
                fields,
                source_url,
                [(RelationType.USES_ASSUMPTION, "FND.NTRU"), (RelationType.VERSION_OF, "FND.NTRU")],
                qualifier="Module-NTRU is preserved as an explicit NTRU-family specialization/version relation.",
            )
        )
    if _all(normalized, ("algebraic lattice reduction", "module lattice reduction"), ("ntru", "module lattice", "mlip", "submodule")):
        relations = [(RelationType.IMPROVES, "ATTACK.LATTICE_REDUCTION")]
        if _any(normalized, "ntru"):
            relations.append((RelationType.ATTACKS if _any(normalized, 'ntru cryptanalysis', 'attack on ntru', 'attacks on ntru') else RelationType.MENTIONS, "FND.NTRU"))
        edges.extend(
            _source_edges(
                paper_node,
                fields,
                source_url,
                relations,
                qualifier="Algebraic/module reduction relevance is limited to the explicit lattice structure or scheme target; a discussed cryptanalytic relation does not establish a concrete attack result.",
            )
        )
    if _all(normalized, ("blind signature", "adaptor signature", "ring signature", "anonymous authentication"), ("lwe", "sis", "lattice", "ntru")):
        edges.extend(
            _source_edges(
                paper_node,
                fields,
                source_url,
                [(RelationType.INSTANTIATES, "PRIM.PRIVACY_SIGNATURE")],
                qualifier="privacy-signature relevance requires the explicit lattice co-anchor",
            )
        )
    if _all(normalized, ("authenticated key exchange", "ake"), ("lwe", "rlwe", "mlwe", "lattice", "lattices", "ml kem", "kyber")):
        edges.extend(
            _source_edges(
                paper_node,
                fields,
                source_url,
                [(RelationType.INSTANTIATES, "PRIM.AKE")],
                qualifier="AKE relevance is limited to the explicit lattice/PQC construction",
            )
        )
        if _any(normalized, 'from lwe', 'based on lwe', 'lwe based lattice assumptions'):
            edges.extend(_source_edges(paper_node, fields, source_url,
                [(RelationType.USES_ASSUMPTION, 'FND.LWE')],
                qualifier='Source explicitly states the LWE assumption for this construction.'))

    dcp = _any(normalized, "dihedral coset problem", " edcp ")
    # A generic polynomial-time quantum algorithm near a DCP citation is not a
    # critical signal. Require a source assertion whose grammar actually makes
    # DCP the solved target.
    claims_algorithm = _any(
        normalized,
        "polynomial time quantum algorithm for the dihedral coset problem",
        "polynomial time algorithm for the dihedral coset problem",
        "solves the dihedral coset problem in polynomial time",
        "polynomial time algorithm for dcp",
        "solves dcp in polynomial time",
    )
    lattice_consequence = _all(normalized, ("reduction", "reduces", "combined with"), ("svp", "lwe", "lattice"))
    if dcp and claims_algorithm:
        preliminary = _any(normalized, "preliminary", "draft", "claim")
        status = ClaimStatus.PRELIMINARY if preliminary else ClaimStatus.PAPER_FACT
        edges.extend(
            _source_edges(
                paper_node,
                fields,
                source_url,
                [(RelationType.SOLVES, "RED.QUANTUM_DCP")],
                qualifier="polynomial-time DCP algorithm claim; verification and parameter scope remain required",
                claim_status=status,
                critical_eligible=lattice_consequence,
            )
        )
        if lattice_consequence:
            targets = []
            if _any(normalized, "svp", "shortest vector"):
                targets.append((RelationType.AFFECTS_SECURITY, "HARD.SVP"))
            if _any(normalized, "lwe", "learning with errors"):
                targets.append((RelationType.AFFECTS_SECURITY, "FND.LWE"))
            edges.extend(
                _source_edges(
                    paper_node,
                    fields,
                    source_url,
                    targets,
                    qualifier="conditional lattice consequence; not a standardized-PQC break claim",
                    claim_status=ClaimStatus.TODO_VERIFY,
                    critical_eligible=True,
                )
            )
    if _all(normalized, ("discrete gaussian sampling", "gaussian sampling"), ("quantum algorithm", "quantum"), ("sis", "dual attack", "lattice")):
        relations = [(RelationType.ACCELERATES, "ATTACK.PRIMAL_DUAL_HYBRID")]
        if _any(normalized, "sis", "short integer solution"):
            relations.append((RelationType.AFFECTS_SECURITY, "FND.SIS"))
        edges.extend(
            _source_edges(
                paper_node,
                fields,
                source_url,
                relations,
                qualifier="Quantum sampling consequence is scoped to the explicitly stated lattice attack/assumption relation.",
                claim_status=ClaimStatus.TODO_VERIFY,
            )
        )
    return tuple(_deduplicate_edges(edges))


def _source_edges(
    source_node: str,
    fields: dict[str, str],
    source_url: str,
    relations: Iterable[tuple[RelationType, str]],
    *,
    qualifier: str,
    claim_status: ClaimStatus = ClaimStatus.PAPER_FACT,
    critical_eligible: bool = False,
) -> list[ConsequenceEdge]:
    span, field = _first_nonempty(fields)
    return [
        ConsequenceEdge(
            source_node=source_node,
            relation_type=relation,
            target_node=target,
            evidence_state=EdgeEvidenceState.SOURCE_ASSERTED,
            evidence_source=field,
            evidence_span=span,
            source_url=source_url,
            confidence=0.88 if not critical_eligible else 0.75,
            qualifier=qualifier,
            claim_status=claim_status,
            critical_eligible=critical_eligible,
        )
        for relation, target in relations
    ]


def _deduplicate_edges(edges: Iterable[ConsequenceEdge]) -> list[ConsequenceEdge]:
    result: list[ConsequenceEdge] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        key = (edge.source_node, edge.relation_type.value, edge.target_node)
        if key not in seen:
            seen.add(key)
            result.append(edge)
    return result


def _concept_anchor(concept_id: str) -> str:
    return concept_id.split(".", 1)[-1].replace("_", " ")


def _direct_relation(concept_id: str) -> RelationType:
    # A concept occurrence establishes a mention, not a contribution or proof.
    return RelationType.MENTIONS


def _normal(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", str(value).lower())
    return f" {re.sub(r'\s+', ' ', normalized).strip()} "


def _any(text: str, *options: str) -> bool:
    return any(_normal(option) in text or (
        _normal(option).strip().endswith(('signature','lattice','trapdoor')) and
        (' ' + _normal(option).strip() + 's ') in text) for option in options)


def _all(text: str, *groups: str | tuple[str, ...]) -> bool:
    return all(
        _any(text, *(group if isinstance(group, tuple) else (group,)))
        for group in groups
    )


def _first_span(fields: dict[str, str], term: str) -> tuple[str, str]:
    wanted = _normal(term)
    for name, value in fields.items():
        normalized = _normal(value)
        if wanted and wanted in normalized:
            return _bounded_span(value), name
    return "", ""


def _first_nonempty(fields: dict[str, str]) -> tuple[str, str]:
    for name in ("abstract", "conclusion", "title"):
        value = fields.get(name, "").strip()
        if value:
            return _bounded_span(value), name
    return "unknown source span", "unknown"


def _bounded_span(value: str, limit: int = 500) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned[:limit]
