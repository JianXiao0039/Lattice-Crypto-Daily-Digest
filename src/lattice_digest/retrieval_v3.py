from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Iterable, Sequence

from lattice_digest.consequence_graph_v3 import (
    ConsequenceGraph,
    EdgeEvidenceState,
    SOURCE_GROUNDED_STATES,
    extract_record_edges,
)
from lattice_digest.enrichment_v3 import EnrichmentResult, SelectiveEnrichmentCoordinator
from lattice_digest.identity_v3 import IdentityResolution, resolve_identity_and_merge
from lattice_digest.models import PaperRecord, copy_record
from lattice_digest.ontology_v3 import OntologyRegistry, load_ontology_v3


CORE_PREFIXES = ("FND.", "HARD.", "ATTACK.", "PRIM.", "PROOF.", "FHE.", "IMPL.", "AI4LC.", "STD.")


@dataclass(frozen=True)
class RetrievalPreparationV3:
    identity: IdentityResolution
    enrichment: EnrichmentResult
    records: tuple[PaperRecord, ...]


def prepare_for_semantic_analysis_v3(
    records: Sequence[PaperRecord],
    *,
    enrichment: SelectiveEnrichmentCoordinator | None = None,
) -> RetrievalPreparationV3:
    identity = resolve_identity_and_merge(records)
    coordinator = enrichment or SelectiveEnrichmentCoordinator()
    enriched = coordinator.run(identity.canonical_records)
    return RetrievalPreparationV3(identity=identity, enrichment=enriched, records=enriched.records)


def apply_semantic_consequence_analysis_v3(
    records: Iterable[PaperRecord],
    ontology: OntologyRegistry | None = None,
) -> list[PaperRecord]:
    registry = ontology or load_ontology_v3()
    output: list[PaperRecord] = []
    for source_record in records:
        record = copy_record(source_record)
        analysis = registry.analyze_fields(
            title=record.title,
            abstract=record.abstract,
            keywords=[*record.categories, *record.keywords_matched],
            conclusion=record.conclusion,
        )
        paper_node = "paper:" + hashlib.sha256(
            (record.paper_id or record.source_url or record.normalized_title or record.title).encode("utf-8")
        ).hexdigest()[:24]
        edges = extract_record_edges(
            paper_node=paper_node,
            title=record.title,
            abstract=record.abstract,
            conclusion=record.conclusion,
            source_url=record.source_url,
            source_concept_ids=analysis.source_concept_ids,
        )
        record.source_evidence_terms = list(
            dict.fromkeys([*record.source_evidence_terms, *(match.source_term for match in analysis.source_evidence)])
        )
        existing_inference = [
            tag if tag.startswith("inferred:") else f"inferred:{tag}"
            for tag in record.inferred_topic_tags
        ]
        record.inferred_topic_tags = list(
            dict.fromkeys([*existing_inference, *(f"inferred:{tag}" for tag in analysis.inferred_tags)])
        )
        record.consequence_edges = [edge.model_dump(mode="json") for edge in edges]
        source_concepts = set(analysis.source_concept_ids)
        core_concepts = {concept_id for concept_id in source_concepts if concept_id.startswith(CORE_PREFIXES)}
        normalized_evidence = f" {record.title} {record.abstract} {record.conclusion} ".lower()
        explicit_lattice_reduction = (
            any(concept_id.startswith("RED.") for concept_id in source_concepts)
            and "lattice problem" in normalized_evidence
            and any(term in normalized_evidence for term in (" reduce", "reduction"))
        )
        if explicit_lattice_reduction:
            core_concepts.update(concept_id for concept_id in source_concepts if concept_id.startswith("RED."))
        typed_relation_evidence = {
            edge.target_node
            for edge in edges
            if edge.evidence_state in SOURCE_GROUNDED_STATES
        }
        typed_core_targets = {
            target for target in typed_relation_evidence if target.startswith(CORE_PREFIXES)
        }
        hard_negative_without_core = bool(analysis.hard_negative_matches) and not core_concepts
        if hard_negative_without_core:
            record.relevance_label = "D"
            record.relevance_score = min(record.relevance_score, 20)
            record.reason = "V3 hard negative without a source-grounded cryptographic consequence: " + ", ".join(
                analysis.hard_negative_matches
            )
        elif core_concepts or typed_core_targets:
            title_evidence = any(match.source_field == "title" for match in analysis.source_evidence)
            abstract_evidence = any(match.source_field == "abstract" for match in analysis.source_evidence)
            if record.relevance_label == "D":
                record.relevance_label = "B" if not title_evidence and abstract_evidence else "A"
            v3_floor = 70 if abstract_evidence and not title_evidence else 80
            if any(concept.startswith(("ATTACK.", "PRIM.", "PROOF.", "FHE.")) for concept in core_concepts):
                v3_floor = max(v3_floor, 80)
            record.relevance_score = max(record.relevance_score, v3_floor)
            record.reading_priority = min(record.reading_priority, 1 if record.relevance_score >= 80 else 2)
            record.reason = _append_reason(
                record.reason,
                "V3 source-grounded concepts/typed targets: " + ", ".join(sorted(core_concepts | typed_core_targets)),
            )
        elif record.relevance_label != "D":
            # Legacy keyword scores are not sufficient V3 evidence. Retaining
            # them would reintroduce generic signatures, side channels,
            # quantum algorithms, and homomorphism false positives.
            record.relevance_label = "D"
            record.relevance_score = min(record.relevance_score, 20)
            record.reading_priority = 99
            record.reason = _append_reason(
                record.reason,
                "V3 rejected legacy-only relevance: no source-grounded ontology concept or typed lattice consequence.",
            )

        critical_edges = [
            edge
            for edge in edges
            if edge.critical_eligible and edge.evidence_state in SOURCE_GROUNDED_STATES
        ]
        if critical_edges:
            graph = ConsequenceGraph(edges)
            target_nodes = {edge.target_node for edge in critical_edges}
            paths = graph.paths_from({paper_node}, target_nodes, critical=True, max_hops=3)
            if paths:
                record.security_impact_severity = "CRITICAL"
                record.evidence_confidence = "TODO_VERIFY"
                record.document_maturity = "preliminary" if any(
                    edge.claim_status.value == "PRELIMINARY" for edge in critical_edges
                ) else record.document_maturity
                record.critical_signal_explanation = _append_reason(
                    record.critical_signal_explanation,
                    "Source-grounded bounded consequence path; does not establish a standardized-PQC break.",
                )
                record.TODO_VERIFY_flags = list(
                    dict.fromkeys([*record.TODO_VERIFY_flags, "verify reduction direction, parameters, proof, and standardized-scheme applicability"])
                )
        elif record.security_impact_severity == "CRITICAL":
            # Legacy phrase matching may nominate a signal, but V3 does not
            # permit CRITICAL without a source-grounded typed consequence edge.
            record.security_impact_severity = "HIGH"
            record.evidence_confidence = "TODO_VERIFY"
            record.critical_signal_explanation = _append_reason(
                record.critical_signal_explanation,
                "V3 withheld CRITICAL: no source-grounded typed critical consequence edge was established.",
            )
        output.append(record)
    return output


def evidence_inference_leak_count(records: Iterable[PaperRecord]) -> int:
    leaks = 0
    for record in records:
        inferred = set(record.inferred_topic_tags)
        source = set(record.source_evidence_terms)
        leaks += len(inferred.intersection(source))
        for edge in record.consequence_edges:
            if edge.get("evidence_state") == EdgeEvidenceState.INFERRED_HYPOTHESIS.value and edge.get("evidence_source") not in {"", "model_inference"}:
                leaks += 1
    return leaks


def _append_reason(existing: str, addition: str) -> str:
    existing = str(existing or "").strip()
    if not existing:
        return addition
    if addition in existing:
        return existing
    return f"{existing}; {addition}"
