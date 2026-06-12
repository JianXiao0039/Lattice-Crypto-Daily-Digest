from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = PROJECT_ROOT / "docs" / "research_tracks" / "v0.5_manual_precision_gold_sample_v0.1.json"
OUTPUT_MD = PROJECT_ROOT / "docs" / "research_tracks" / "v0.5_manual_precision_gold_sample_v0.1.md"


ANNOTATIONS: dict[str, dict[str, Any]] = {
    "iacr:2026/1196": {
        "candidate_tracks": ["module_sis_sanitizable_signature", "core_pqc_background"],
        "primary_track": "module_sis_sanitizable_signature",
        "secondary_track": "core_pqc_background",
        "relevant": "yes",
        "positive_evidence": "Title states polynomial commitments over lattices; repository keywords include Short Integer Solution.",
        "exclusion_evidence": "No chameleon-hash or sanitizable-signature claim is verified.",
        "expected_handoff_destination": "Module-SIS related-work and commitment queue",
        "annotation_confidence": "high",
        "annotator_note": "Construction-adjacent commitment evidence.",
        "TODO_VERIFY": ["verify exact SIS/Module-SIS assumption and exposure model from paper"],
    },
    "iacr:2026/1208": {
        "candidate_tracks": ["module_sis_sanitizable_signature"],
        "primary_track": "module_sis_sanitizable_signature",
        "secondary_track": None,
        "relevant": "ambiguous",
        "positive_evidence": "Repository record is tagged SIS and the title concerns preimage-sampleable function families.",
        "exclusion_evidence": "No chameleon collision, commitment, or sanitization property is established by metadata.",
        "expected_handoff_destination": "Trapdoor and primitive-adjacency review",
        "annotation_confidence": "medium",
        "annotator_note": "Potential trapdoor primitive bridge only.",
        "TODO_VERIFY": ["read abstract and construction definitions"],
    },
    "arxiv:2605.24798": {
        "candidate_tracks": ["ai4lattice_longline", "module_sis_sanitizable_signature"],
        "primary_track": "ai4lattice_longline",
        "secondary_track": "module_sis_sanitizable_signature",
        "relevant": "yes",
        "positive_evidence": "Title and keywords explicitly mention dual attack, trapdoor sampling, and rejection sampling.",
        "exclusion_evidence": "No learning-guided component is shown by metadata.",
        "expected_handoff_destination": "Classical attack and trapdoor background",
        "annotation_confidence": "high",
        "annotator_note": "Classical baseline and primitive background, not an AI paper.",
        "TODO_VERIFY": ["verify cryptographic parameter implications"],
    },
    "iacr:2026/1084": {
        "candidate_tracks": ["xingye_lu_bridge", "module_sis_sanitizable_signature"],
        "primary_track": "xingye_lu_bridge",
        "secondary_track": "module_sis_sanitizable_signature",
        "relevant": "yes",
        "positive_evidence": "Title and repository metadata explicitly identify blind lattice signatures and commitments.",
        "exclusion_evidence": "No linkability, programmable hash, or professor-specific relation is verified.",
        "expected_handoff_destination": "Lattice privacy/signature bridge queue",
        "annotation_confidence": "high",
        "annotator_note": "Technical bridge only; not a claim about Xingye Lu.",
        "TODO_VERIFY": ["verify commitment role and signature security model"],
    },
    "iacr:2026/1111": {
        "candidate_tracks": ["xingye_lu_bridge"],
        "primary_track": "xingye_lu_bridge",
        "secondary_track": None,
        "relevant": "ambiguous",
        "positive_evidence": "Title explicitly states linkable ring signature.",
        "exclusion_evidence": "Repository metadata provides no lattice/PQC/SIS/LWE anchor.",
        "expected_handoff_destination": "TODO_VERIFY bridge queue",
        "annotation_confidence": "high",
        "annotator_note": "Should not enter the lattice track until an anchor is verified.",
        "TODO_VERIFY": ["verify construction assumptions before inclusion"],
    },
    "iacr:2026/1117": {
        "candidate_tracks": ["core_pqc_background"],
        "primary_track": "core_pqc_background",
        "secondary_track": None,
        "relevant": "yes",
        "positive_evidence": "Title explicitly names ML-KEM; repository metadata includes FIPS 203.",
        "exclusion_evidence": "Not directly a Module-SIS or AI4Lattice item.",
        "expected_handoff_destination": "ML-KEM security background",
        "annotation_confidence": "high",
        "annotator_note": "Standard-facing background asset.",
        "TODO_VERIFY": ["verify original paper claims before technical summary"],
    },
    "iacr:2026/1032": {
        "candidate_tracks": ["core_pqc_background"],
        "primary_track": "core_pqc_background",
        "secondary_track": None,
        "relevant": "yes",
        "positive_evidence": "Title explicitly names production ML-DSA implementations.",
        "exclusion_evidence": "No direct chameleon-hash or learning-guided attack relation.",
        "expected_handoff_destination": "ML-DSA implementation and reproducibility queue",
        "annotation_confidence": "high",
        "annotator_note": "Implementation-quality background.",
        "TODO_VERIFY": ["verify audited implementations and reduction-placement findings"],
    },
    "iacr:2026/1188": {
        "candidate_tracks": ["core_pqc_background", "ai4lattice_longline"],
        "primary_track": "core_pqc_background",
        "secondary_track": "ai4lattice_longline",
        "relevant": "yes",
        "positive_evidence": "Metadata explicitly anchors ML-KEM, ML-DSA, NTT, and fault attacks.",
        "exclusion_evidence": "No learning-guided attack is indicated.",
        "expected_handoff_destination": "PQC implementation/fault-analysis queue",
        "annotation_confidence": "high",
        "annotator_note": "Useful implementation-security background.",
        "TODO_VERIFY": ["verify schemes and fault model in the original paper"],
    },
    "iacr:2026/1081": {
        "candidate_tracks": ["ai4lattice_longline"],
        "primary_track": "ai4lattice_longline",
        "secondary_track": None,
        "relevant": "yes",
        "positive_evidence": "Title explicitly concerns LWE secret recovery using low Hamming weight hints.",
        "exclusion_evidence": "Metadata does not establish machine-learning assistance.",
        "expected_handoff_destination": "Sparse/hinted LWE attack baseline",
        "annotation_confidence": "high",
        "annotator_note": "Classical sparse/hint baseline for later learned ranking comparison.",
        "TODO_VERIFY": ["verify attack model and parameters"],
    },
    "arxiv:2604.22900": {
        "candidate_tracks": ["ai4lattice_longline"],
        "primary_track": "ai4lattice_longline",
        "secondary_track": None,
        "relevant": "yes",
        "positive_evidence": "Title and keywords explicitly state module-lattice reduction and MLWE.",
        "exclusion_evidence": "No AI component is established.",
        "expected_handoff_destination": "Lattice-reduction baseline queue",
        "annotation_confidence": "high",
        "annotator_note": "Classical interface/baseline candidate.",
        "TODO_VERIFY": ["verify reduction objective and cryptanalytic relevance"],
    },
    "iacr:2026/1041": {
        "candidate_tracks": ["ai4lattice_longline"],
        "primary_track": "ai4lattice_longline",
        "secondary_track": None,
        "relevant": "ambiguous",
        "positive_evidence": "Title states a structure-aware framework for lattice cryptanalysis.",
        "exclusion_evidence": "Metadata does not prove that the framework uses machine learning or coordinate ranking.",
        "expected_handoff_destination": "AI4Lattice TODO_VERIFY queue",
        "annotation_confidence": "medium",
        "annotator_note": "Potential longline item requiring original-paper review.",
        "TODO_VERIFY": ["verify method class, baselines, and attack target"],
    },
    "arxiv:2605.27286": {
        "candidate_tracks": ["excluded_noise"],
        "primary_track": "excluded_noise",
        "secondary_track": None,
        "relevant": "no",
        "positive_evidence": "None for lattice cryptography.",
        "exclusion_evidence": "Falcon is a model name; title is time-series modeling, not the Falcon lattice signature.",
        "expected_handoff_destination": "exclude",
        "annotation_confidence": "high",
        "annotator_note": "Clear scheme-name collision false positive.",
        "TODO_VERIFY": [],
    },
    "arxiv:2606.03611": {
        "candidate_tracks": ["core_pqc_background", "excluded_noise"],
        "primary_track": "excluded_noise",
        "secondary_track": "core_pqc_background",
        "relevant": "ambiguous",
        "positive_evidence": "Title mentions PQC and metadata includes ML-KEM/Kyber terms.",
        "exclusion_evidence": "Primary framing is 6G, IoT, CSIDH, and federated learning; lattice contribution may be superficial.",
        "expected_handoff_destination": "manual false-positive review",
        "annotation_confidence": "medium",
        "annotator_note": "Hard ambiguous example for anchor-strength review.",
        "TODO_VERIFY": ["verify whether ML-KEM is technically central or only listed"],
    },
    "iacr:2026/1199": {
        "candidate_tracks": ["excluded_noise", "module_sis_sanitizable_signature"],
        "primary_track": "excluded_noise",
        "secondary_track": None,
        "relevant": "no",
        "positive_evidence": "Title concerns a post-quantum commitment.",
        "exclusion_evidence": "Construction is isogeny-based, not lattice/SIS/Module-SIS based.",
        "expected_handoff_destination": "exclude or C-class comparison background",
        "annotation_confidence": "high",
        "annotator_note": "Useful negative example for generic commitment filtering.",
        "TODO_VERIFY": [],
    },
    "arxiv:2510.10436": {
        "candidate_tracks": ["core_pqc_background"],
        "primary_track": "core_pqc_background",
        "secondary_track": None,
        "relevant": "yes",
        "positive_evidence": "Repository metadata includes ML-KEM, ML-DSA, deployment, implementation, and side-channel anchors.",
        "exclusion_evidence": "Broad survey; threshold-PQC coverage is not established by metadata.",
        "expected_handoff_destination": "PQC background and threshold-PQC TODO_VERIFY queue",
        "annotation_confidence": "medium",
        "annotator_note": "Used to represent broad PQC background; no threshold-specific claim.",
        "TODO_VERIFY": ["verify whether the survey contains substantive threshold-PQC coverage"],
    },
}


def record_index(project_root: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for path in sorted((project_root / "data").glob("????-??-??.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload if isinstance(payload, list) else payload.get("records") or []
        for record in records:
            identifier = record.get("paper_id") or record.get("doi") or record.get("title")
            if identifier and identifier not in index:
                index[str(identifier)] = {**record, "artifact_date": path.stem}
    return index


def build_sample(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    index = record_index(project_root)
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    for identifier, annotation in ANNOTATIONS.items():
        record = index.get(identifier)
        if not record:
            missing.append(identifier)
            continue
        rows.append(
            {
                "paper_identifier": identifier,
                "title": record.get("title"),
                "source": record.get("source"),
                **annotation,
                "repository_artifact_date": record.get("artifact_date"),
            }
        )
    return {
        "schema_version": 1,
        "sample_type": "offline_manual_annotation",
        "production_logic_changed": False,
        "sample_size": len(rows),
        "records": rows,
        "missing_requested_records": missing,
        "coverage_notes": [
            "No verified threshold-PQC-specific record was found; the broad PQC survey is marked TODO_VERIFY.",
            "No record is treated as evidence of Xingye Lu authorship or current research activity.",
            "Ambiguous and negative examples are intentionally retained for precision review.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# v0.5 Manual Precision Gold Sample v0.1",
        "",
        f"- sample size: `{payload['sample_size']}`",
        "- sample type: `offline_manual_annotation`",
        "- production logic changed: `false`",
        "",
        "| ID | Title | Primary track | Relevant | Confidence | Positive evidence | Exclusion evidence | TODO_VERIFY |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in payload["records"]:
        lines.append(
            "| {id} | {title} | {track} | {relevant} | {confidence} | {positive} | {negative} | {todo} |".format(
                id=row["paper_identifier"],
                title=str(row["title"]).replace("|", "\\|"),
                track=row["primary_track"],
                relevant=row["relevant"],
                confidence=row["annotation_confidence"],
                positive=str(row["positive_evidence"]).replace("|", "\\|"),
                negative=str(row["exclusion_evidence"]).replace("|", "\\|"),
                todo="; ".join(row["TODO_VERIFY"]) or "none",
            )
        )
    lines.extend(["", "## Coverage Notes"])
    lines.extend(f"- {note}" for note in payload["coverage_notes"])
    return "\n".join(lines) + "\n"


def write_sample(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    payload = build_sample(project_root)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def main() -> int:
    payload = write_sample()
    print(f"Wrote {OUTPUT_JSON.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {OUTPUT_MD.relative_to(PROJECT_ROOT)}")
    print(f"Sample size: {payload['sample_size']}")
    if payload["missing_requested_records"]:
        print("Missing records: " + ", ".join(payload["missing_requested_records"]))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
