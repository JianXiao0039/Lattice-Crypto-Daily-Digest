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
from lattice_digest.evidence_contract import analyze_source, bind_source_evidence, positive_source_fields, score_to_label




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
        analysis = analyze_source(record, registry)
        source_fields = positive_source_fields(record)
        paper_node = "paper:" + hashlib.sha256(
            (record.paper_id or record.source_url or record.normalized_title or record.title).encode("utf-8")
        ).hexdigest()[:24]
        edges = extract_record_edges(
            paper_node=paper_node,
            title=source_fields["title"],
            abstract=source_fields["abstract"],
            conclusion=source_fields["conclusion"],
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
        record = bind_source_evidence(record, analysis, record.consequence_edges)
        record.reason = "Evidence-bound source scope: " + record.relevance_scope + "; source concepts: " + ", ".join(record.source_concept_ids)

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
