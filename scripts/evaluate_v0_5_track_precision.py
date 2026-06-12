from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRACKS = (
    "module_sis_sanitizable_signatures",
    "xingye_lu_bridge",
    "ai4lattice_cryptanalysis",
    "core_pqc_and_implementation",
)
VALID_RELEVANCE = {"yes", "no", "ambiguous"}
VALID_REVIEW_STATUS = {
    "not_reviewed",
    "needs_user_review",
    "user_confirmed",
    "user_corrected",
    "excluded_due_to_insufficient_metadata",
}


@dataclass(frozen=True)
class TrackRule:
    name: str
    terms: tuple[str, ...]


MACHINE_RULES = (
    TrackRule(
        TRACKS[0],
        (
            "module-sis",
            "module sis",
            "ring sis",
            "chameleon hash",
            "sanitizable signature",
            "sanitisable signature",
            "commitment",
            "trapdoor",
            "preimage sampleable",
            "exposure model",
            "accountable sanitization",
        ),
    ),
    TrackRule(
        TRACKS[1],
        (
            "linkable ring signature",
            "ring signature",
            "blind lattice signature",
            "blind signature",
            "programmable hash",
            "hash-then-one-way",
            "message franking",
            "proxy re-encryption",
            "attribute-based encryption",
            "private information retrieval",
            "traitor tracing",
            "privacy-preserving",
            "anonymous",
        ),
    ),
    TrackRule(
        TRACKS[2],
        (
            "lattice cryptanalysis",
            "bkz",
            "lattice reduction",
            "dual attack",
            "primal attack",
            "hybrid attack",
            "secret recovery",
            "security estimator",
            "low hamming weight",
            "trapdoor sampling",
            "coordinate selection",
            "sparse lwe",
            "salsa",
            "cool-and-cruel",
        ),
    ),
    TrackRule(
        TRACKS[3],
        (
            "ml-kem",
            "ml-dsa",
            "kyber",
            "dilithium",
            "hawk",
            "ntru",
            "fully homomorphic",
            "homomorphic encryption",
            "fhe",
            "ckks",
            "tfhe",
            "bgv",
            "ntt",
            "side-channel",
            "fault",
            "risc-v",
            "gpu acceleration",
            "implementation",
            "parameterization",
        ),
    ),
)


CODEX_PRIMARY: dict[str, str] = {
    # Track A: direct commitment/trapdoor/SIS adjacency.
    "1c973def72854d32a7bca035be36020faad78299": TRACKS[0],
    "iacr:2026/1079": TRACKS[0],
    "iacr:2026/1196": TRACKS[0],
    "iacr:2026/1208": TRACKS[0],
    # Track B: lattice privacy/signature/protocol bridge candidates.
    "iacr:2026/1045": TRACKS[1],
    "iacr:2026/1076": TRACKS[1],
    "iacr:2026/1077": TRACKS[1],
    "iacr:2026/1084": TRACKS[1],
    "iacr:2026/1094": TRACKS[1],
    "iacr:2026/1113": TRACKS[1],
    # Track C: classical or learning-adjacent attack and reduction baselines.
    "4c2fcd42aa91a63fe7528e15a1fed4b2b425167a": TRACKS[2],
    "902f7237543d1d63ea289b1b943ff3d4a677c49c": TRACKS[2],
    "9f33e1b9547d554accbf11c71f30fcb4b621e7c2": TRACKS[2],
    "arxiv:2604.22900": TRACKS[2],
    "arxiv:2605.17412": TRACKS[2],
    "arxiv:2605.24798": TRACKS[2],
    "iacr:2026/1041": TRACKS[2],
    "iacr:2026/1048": TRACKS[2],
    "iacr:2026/1081": TRACKS[2],
}

AMBIGUOUS_IDS = {
    "arxiv:2606.03611",
    "iacr:2026/1017",
    "iacr:2026/1088",
    "iacr:2026/1107",
    "iacr:2026/1111",
    "iacr:2026/1124",
    "iacr:2026/1179",
}

IRRELEVANT_IDS = {
    "arxiv:2605.27286",
    "arxiv:2606.05834",
    "iacr:2026/1015",
    "iacr:2026/1042",
    "iacr:2026/1053",
    "iacr:2026/1122",
    "iacr:2026/1181",
    "iacr:2026/1182",
    "iacr:2026/1199",
    "iacr:2026/1219",
    "iacr:2026/1221",
}

SECONDARY_OVERRIDES: dict[str, list[str]] = {
    "arxiv:2605.24798": [TRACKS[0]],
    "iacr:2026/1079": [TRACKS[1]],
    "iacr:2026/1084": [TRACKS[0]],
    "iacr:2026/1188": [TRACKS[2]],
    "iacr:2026/1196": [TRACKS[3]],
    "iacr:2026/1208": [TRACKS[2]],
}


def _record_identifier(record: dict[str, Any]) -> str:
    return str(
        record.get("paper_id")
        or record.get("doi")
        or record.get("id")
        or record.get("url")
        or record.get("title")
    )


def load_repository_records(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    """Load and deduplicate existing records without modifying source artifacts."""
    paths = sorted((project_root / "data").glob("????-??-??.json"))
    paths += sorted((project_root / "data" / "weekly").glob("*.json"))
    records: dict[str, dict[str, Any]] = {}
    provenance: defaultdict[str, list[str]] = defaultdict(list)

    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload if isinstance(payload, list) else payload.get("records") or []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict) or not row.get("title"):
                continue
            identifier = _record_identifier(row)
            provenance[identifier].append(path.relative_to(project_root).as_posix())
            current = records.get(identifier)
            if current is None or (not current.get("abstract") and row.get("abstract")):
                records[identifier] = dict(row)

    result = []
    for identifier in sorted(records):
        result.append(
            {
                **records[identifier],
                "repository_record_id": identifier,
                "source_provenance": provenance[identifier],
            }
        )
    return result


def _evidence_text(record: dict[str, Any]) -> str:
    fields: Iterable[Any] = (
        record.get("title"),
        record.get("abstract"),
        " ".join(map(str, record.get("taxonomy_tags") or [])),
        " ".join(map(str, record.get("keywords_matched") or [])),
        record.get("reason"),
    )
    return " ".join(str(value or "") for value in fields).lower()


def machine_proposal(record: dict[str, Any]) -> tuple[str | None, list[str], dict[str, list[str]]]:
    text = _evidence_text(record)
    matches: dict[str, list[str]] = {}
    for rule in MACHINE_RULES:
        found = sorted({term for term in rule.terms if term in text})
        if found:
            matches[rule.name] = found
    ordered = [track for track in TRACKS if track in matches]
    primary = ordered[0] if ordered else None
    return primary, ordered[1:], matches


def _default_codex_primary(
    record: dict[str, Any], proposed: str | None, matches: dict[str, list[str]]
) -> str:
    identifier = record["repository_record_id"]
    if identifier in IRRELEVANT_IDS:
        return "irrelevant"
    if identifier in AMBIGUOUS_IDS:
        return "ambiguous"
    if identifier in CODEX_PRIMARY:
        return CODEX_PRIMARY[identifier]
    if proposed == TRACKS[1]:
        # Track B is intentionally narrow. Generic privacy/FHE terms do not
        # establish a technical bridge to lattice authentication or signatures.
        if TRACKS[3] in matches:
            return TRACKS[3]
        return "ambiguous"
    if proposed in TRACKS:
        return proposed
    return "ambiguous"


def _positive_evidence(record: dict[str, Any], matches: dict[str, list[str]], primary: str) -> str:
    title = str(record.get("title") or "")
    if primary in TRACKS and matches.get(primary):
        terms = ", ".join(matches[primary][:6])
        return f"Repository title/abstract/metadata match the proposed track through: {terms}. Title: {title}"
    if primary == "irrelevant":
        return "No sufficiently specific lattice/PQC track evidence was found in the retained repository metadata."
    return f"Repository metadata suggests possible relevance, but the available evidence is not specific enough to select one track. Title: {title}"


def _exclusion_evidence(identifier: str, primary: str) -> str:
    if identifier == "arxiv:2605.27286":
        return "Falcon is a time-series model name here, not the Falcon lattice signature."
    if identifier == "iacr:2026/1199":
        return "The commitment is isogeny-based rather than lattice/SIS/Module-SIS based."
    if identifier == "iacr:2026/1111":
        return "The ring-signature metadata does not establish a lattice, SIS, LWE, or PQC anchor."
    if primary == "irrelevant":
        return "The record is non-lattice, generic cryptography, another PQC family, or a keyword/taxonomy collision."
    if primary == "ambiguous":
        return "Technical centrality or a required lattice/PQC anchor remains unverified from repository metadata."
    return "No exclusion overrides the positive evidence; exact paper claims still require human review."


def build_sample(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    rows = []
    for index, record in enumerate(load_repository_records(project_root), start=1):
        identifier = record["repository_record_id"]
        machine_primary, machine_secondary, matches = machine_proposal(record)
        codex_primary = _default_codex_primary(record, machine_primary, matches)
        codex_secondary = SECONDARY_OVERRIDES.get(identifier, [])
        relevance = "no" if codex_primary == "irrelevant" else "ambiguous" if codex_primary == "ambiguous" else "yes"
        control_label = (
            "irrelevant"
            if relevance == "no"
            else "ambiguous"
            if relevance == "ambiguous"
            else "multi_track"
            if codex_secondary
            else None
        )
        evidence_fields = {
            "abstract": record.get("abstract"),
            "taxonomy_tags": record.get("taxonomy_tags") or [],
            "keywords_matched": record.get("keywords_matched") or [],
            "relevance_label": record.get("relevance_label"),
            "relevance_score": record.get("relevance_score"),
        }
        rows.append(
            {
                "sample_id": f"v05-{index:04d}",
                "repository_record_id": identifier,
                "title": record.get("title"),
                "source": record.get("source"),
                "publication_date": record.get("publication_date") or record.get("date"),
                "available_evidence": evidence_fields,
                "machine_proposed_primary_track": machine_primary,
                "machine_proposed_secondary_tracks": machine_secondary,
                "codex_reviewed_primary_track": codex_primary,
                "codex_reviewed_secondary_tracks": codex_secondary,
                "human_gold_primary_track": None,
                "human_gold_secondary_tracks": [],
                "human_review_status": "needs_user_review",
                "relevance_status": relevance,
                "control_label": control_label,
                "positive_evidence": _positive_evidence(record, matches, codex_primary),
                "exclusion_evidence": _exclusion_evidence(identifier, codex_primary),
                "ambiguity_reason": (
                    "A required anchor or technical-centrality judgment needs user review."
                    if relevance == "ambiguous"
                    else None
                ),
                "explanation": (
                    "Codex-reviewed offline label based only on retained repository title, abstract, taxonomy, keywords, and notes; not a human gold label."
                ),
                "source_provenance": record["source_provenance"],
                "TODO_VERIFY": [
                    "user confirmation or correction is required before this record counts as gold",
                    "original-paper claims are outside this repository-only evaluation unless already retained",
                ],
            }
        )

    distribution = Counter(row["codex_reviewed_primary_track"] for row in rows)
    return {
        "schema_version": 2,
        "sample_type": "repository_grounded_offline_annotation_queue",
        "production_logic_changed": False,
        "target_sample_size": 80,
        "minimum_acceptable_size": 60,
        "sample_size": len(rows),
        "human_gold_count": 0,
        "records": rows,
        "distribution": dict(sorted(distribution.items())),
        "coverage_gaps": _coverage_gaps(distribution, len(rows)),
    }


def _coverage_gaps(distribution: Counter[str], sample_size: int) -> list[str]:
    gaps = []
    if sample_size < 80:
        gaps.append(f"Repository contains {sample_size} unique usable records, below the target of 80.")
    for track in TRACKS:
        if distribution[track] < 16:
            gaps.append(f"{track} has {distribution[track]} reviewed candidates, below the recommended 16.")
    if distribution["irrelevant"] < 8:
        gaps.append(f"Hard-negative coverage is {distribution['irrelevant']}, below the recommended 8.")
    if distribution["ambiguous"] < 8:
        gaps.append(f"Ambiguous coverage is {distribution['ambiguous']}, below the recommended 8.")
    return gaps


def _track_set(row: dict[str, Any], prefix: str) -> set[str]:
    primary = row.get(f"{prefix}_primary_track")
    secondary = row.get(f"{prefix}_secondary_tracks") or []
    return {track for track in [primary, *secondary] if track in TRACKS}


def _score(binary_truth: list[bool], binary_pred: list[bool]) -> dict[str, float | int | None]:
    tp = sum(t and p for t, p in zip(binary_truth, binary_pred))
    fp = sum(not t and p for t, p in zip(binary_truth, binary_pred))
    fn = sum(t and not p for t, p in zip(binary_truth, binary_pred))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def evaluate_sample(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["records"]
    valid_gold = [
        row
        for row in rows
        if row["human_review_status"] in {"user_confirmed", "user_corrected"}
        and row.get("human_gold_primary_track")
    ]

    diagnostic = {}
    for track in TRACKS:
        truth = [track in _track_set(row, "codex_reviewed") for row in rows]
        pred = [track in _track_set(row, "machine_proposed") for row in rows]
        diagnostic[track] = _score(truth, pred)

    precision_values = [m["precision"] for m in diagnostic.values() if m["precision"] is not None]
    recall_values = [m["recall"] for m in diagnostic.values() if m["recall"] is not None]
    f1_values = [m["f1"] for m in diagnostic.values() if m["f1"] is not None]
    all_tp = sum(m["tp"] for m in diagnostic.values())
    all_fp = sum(m["fp"] for m in diagnostic.values())
    all_fn = sum(m["fn"] for m in diagnostic.values())
    micro_precision = all_tp / (all_tp + all_fp) if all_tp + all_fp else None
    micro_recall = all_tp / (all_tp + all_fn) if all_tp + all_fn else None
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if micro_precision is not None and micro_recall is not None and micro_precision + micro_recall
        else None
    )

    irrelevant = [row for row in rows if row["relevance_status"] == "no"]
    ambiguous = [row for row in rows if row["relevance_status"] == "ambiguous"]
    multi = [row for row in rows if row["codex_reviewed_secondary_tracks"]]
    explanation_complete = [
        row
        for row in rows
        if row.get("positive_evidence")
        and row.get("exclusion_evidence")
        and row.get("explanation")
        and row.get("source_provenance")
    ]

    machine_primary = Counter(row.get("machine_proposed_primary_track") or "no_label" for row in rows)
    confusion: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        confusion[row["codex_reviewed_primary_track"]][row.get("machine_proposed_primary_track") or "no_label"] += 1

    false_positives = []
    false_negatives = []
    for row in rows:
        truth = _track_set(row, "codex_reviewed")
        pred = _track_set(row, "machine_proposed")
        for track in sorted(pred - truth):
            false_positives.append({"sample_id": row["sample_id"], "track": track, "title": row["title"]})
        for track in sorted(truth - pred):
            false_negatives.append({"sample_id": row["sample_id"], "track": track, "title": row["title"]})

    return {
        "sample_size": len(rows),
        "human_gold_metrics": {
            "valid_gold_count": len(valid_gold),
            "per_track_precision": None,
            "per_track_recall": None,
            "per_track_f1": None,
            "macro_precision": None,
            "macro_recall": None,
            "macro_f1": None,
            "micro_f1": None,
            "status": "insufficient_human_gold_labels",
        },
        "codex_review_diagnostic_not_gold": {
            "per_track": diagnostic,
            "macro_precision": sum(precision_values) / len(precision_values) if precision_values else None,
            "macro_recall": sum(recall_values) / len(recall_values) if recall_values else None,
            "macro_f1": sum(f1_values) / len(f1_values) if f1_values else None,
            "micro_f1": micro_f1,
        },
        "irrelevant_false_positive_rate": (
            sum(bool(_track_set(row, "machine_proposed")) for row in irrelevant) / len(irrelevant)
            if irrelevant
            else None
        ),
        "ambiguous_coverage": (
            sum(bool(_track_set(row, "machine_proposed")) for row in ambiguous) / len(ambiguous)
            if ambiguous
            else None
        ),
        "no_label_rate": machine_primary["no_label"] / len(rows) if rows else None,
        "multi_track_disagreement_rate": (
            sum(_track_set(row, "machine_proposed") != _track_set(row, "codex_reviewed") for row in multi) / len(multi)
            if multi
            else None
        ),
        "explanation_completeness_rate": len(explanation_complete) / len(rows) if rows else None,
        "annotation_coverage": len(valid_gold) / len(rows) if rows else None,
        "machine_primary_distribution": dict(machine_primary),
        "confusion_matrix": {key: dict(value) for key, value in sorted(confusion.items())},
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "ambiguous_records": [
            {"sample_id": row["sample_id"], "title": row["title"], "reason": row["ambiguity_reason"]}
            for row in ambiguous
        ],
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_sample_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# v0.5 Manual Precision Sample v0.2",
        "",
        f"- repository-grounded records: `{payload['sample_size']}`",
        f"- human-confirmed/corrected labels: `{payload['human_gold_count']}`",
        "- production logic changed: `false`",
        "- label status: all Codex labels are proposals pending user review",
        "",
        "| Sample | Repository ID | Title | Machine primary | Codex-reviewed primary | Secondary | Relevance | Human status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in payload["records"]:
        lines.append(
            "| {sample} | {record} | {title} | {machine} | {reviewed} | {secondary} | {relevance} | {status} |".format(
                sample=row["sample_id"],
                record=row["repository_record_id"],
                title=str(row["title"]).replace("|", "\\|"),
                machine=row["machine_proposed_primary_track"] or "none",
                reviewed=row["codex_reviewed_primary_track"],
                secondary=", ".join(row["codex_reviewed_secondary_tracks"]) or "none",
                relevance=row["relevance_status"],
                status=row["human_review_status"],
            )
        )
    lines += ["", "## Coverage Gaps"] + [f"- {gap}" for gap in payload["coverage_gaps"]]
    return "\n".join(lines) + "\n"


def _render_results(payload: dict[str, Any], result: dict[str, Any]) -> str:
    diag = result["codex_review_diagnostic_not_gold"]
    lines = [
        "# v0.5 Offline Precision Results v0.1",
        "",
        "## Human-Gold Metrics",
        "",
        "No human-gold precision, recall, or F1 is reported because no entry is `user_confirmed` or `user_corrected`.",
        "",
        f"- valid human-gold labels: `{result['human_gold_metrics']['valid_gold_count']}`",
        f"- annotation coverage: `{_fmt(result['annotation_coverage'])}`",
        "",
        "## Machine-to-Codex Diagnostic (Not Gold)",
        "",
        "These values compare deterministic machine proposals with Codex-reviewed provisional labels. They are debugging diagnostics, not model-quality or production metrics.",
        "",
        "| Track | Precision | Recall | F1 | TP | FP | FN |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for track in TRACKS:
        metric = diag["per_track"][track]
        lines.append(
            f"| {track} | {_fmt(metric['precision'])} | {_fmt(metric['recall'])} | {_fmt(metric['f1'])} | {metric['tp']} | {metric['fp']} | {metric['fn']} |"
        )
    lines += [
        "",
        f"- macro precision: `{_fmt(diag['macro_precision'])}`",
        f"- macro recall: `{_fmt(diag['macro_recall'])}`",
        f"- macro F1: `{_fmt(diag['macro_f1'])}`",
        f"- micro F1: `{_fmt(diag['micro_f1'])}`",
        f"- irrelevant false-positive rate: `{_fmt(result['irrelevant_false_positive_rate'])}`",
        f"- ambiguous coverage: `{_fmt(result['ambiguous_coverage'])}`",
        f"- no-label rate: `{_fmt(result['no_label_rate'])}`",
        f"- multi-track disagreement rate: `{_fmt(result['multi_track_disagreement_rate'])}`",
        f"- explanation completeness rate: `{_fmt(result['explanation_completeness_rate'])}`",
        "",
        "## Gate Interpretation",
        "",
        "Offline design gate: `sample_design_ready_with_coverage_gaps`.",
        "",
        "Production gate: `blocked_by_multiple_conditions` because human annotation, metric targets, CI recovery, and durable-run evidence remain incomplete.",
    ]
    return "\n".join(lines) + "\n"


def _render_queue(payload: dict[str, Any]) -> str:
    lines = [
        "# v0.5 Annotation Queue v0.1",
        "",
        "Only the user can promote a row to `user_confirmed` or `user_corrected`.",
        "",
        "| Sample | Title | Proposed label | Review status | Priority reason |",
        "|---|---|---|---|---|",
    ]
    ordered = sorted(
        payload["records"],
        key=lambda row: (row["relevance_status"] != "ambiguous", row["control_label"] != "multi_track", row["sample_id"]),
    )
    for row in ordered:
        reason = "ambiguous" if row["relevance_status"] == "ambiguous" else "multi-track" if row["control_label"] == "multi_track" else "stratum review"
        lines.append(
            f"| {row['sample_id']} | {str(row['title']).replace('|', '\\|')} | {row['codex_reviewed_primary_track']} | {row['human_review_status']} | {reason} |"
        )
    return "\n".join(lines) + "\n"


def _render_coverage(payload: dict[str, Any], result: dict[str, Any]) -> str:
    lines = [
        "# v0.5 Annotation Coverage v0.1",
        "",
        f"- total records: `{payload['sample_size']}`",
        "- user-confirmed: `0`",
        "- user-corrected: `0`",
        f"- needs user review: `{payload['sample_size']}`",
        f"- annotation coverage: `{_fmt(result['annotation_coverage'])}`",
        "",
        "## Distribution",
        "",
    ]
    lines.extend(f"- {label}: `{count}`" for label, count in payload["distribution"].items())
    lines += ["", "## Coverage Gaps"] + [f"- {gap}" for gap in payload["coverage_gaps"]]
    return "\n".join(lines) + "\n"


def _render_confusion(result: dict[str, Any]) -> str:
    labels = sorted({column for row in result["confusion_matrix"].values() for column in row})
    lines = [
        "# v0.5 Track Confusion Matrix v0.1",
        "",
        "Rows are Codex-reviewed provisional labels; columns are machine-proposed primary labels. This is not a human-gold confusion matrix.",
        "",
        "| Reviewed \\ Machine | " + " | ".join(labels) + " |",
        "|---|" + "---:|" * len(labels),
    ]
    for reviewed, counts in result["confusion_matrix"].items():
        lines.append("| " + reviewed + " | " + " | ".join(str(counts.get(label, 0)) for label in labels) + " |")
    return "\n".join(lines) + "\n"


def _render_error_review(title: str, entries: list[dict[str, Any]], kind: str) -> str:
    lines = [f"# {title}", "", f"Machine-to-Codex provisional {kind}; not human-gold errors.", ""]
    if not entries:
        lines.append("No cases observed.")
    else:
        lines += ["| Sample | Track | Title |", "|---|---|---|"]
        for entry in entries:
            lines.append(f"| {entry['sample_id']} | {entry['track']} | {str(entry['title']).replace('|', '\\|')} |")
    return "\n".join(lines) + "\n"


def _render_ambiguous(result: dict[str, Any]) -> str:
    lines = [
        "# v0.5 Ambiguous Case Review v0.1",
        "",
        "| Sample | Title | Reason |",
        "|---|---|---|",
    ]
    for entry in result["ambiguous_records"]:
        lines.append(f"| {entry['sample_id']} | {str(entry['title']).replace('|', '\\|')} | {entry['reason']} |")
    return "\n".join(lines) + "\n"


def _render_explanation_quality(payload: dict[str, Any], result: dict[str, Any]) -> str:
    return (
        "# v0.5 Track Explanation Quality v0.1\n\n"
        f"- explanation completeness rate: `{_fmt(result['explanation_completeness_rate'])}`\n"
        f"- evaluated records: `{payload['sample_size']}`\n"
        "- required evidence: positive evidence, exclusion evidence, explanation, and repository provenance\n"
        "- limitation: completeness does not imply factual correctness or human agreement\n"
        "- TODO_VERIFY: user review of explanation sufficiency and paper-level technical claims\n"
    )


def write_outputs(payload: dict[str, Any], result: dict[str, Any], project_root: Path = PROJECT_ROOT) -> None:
    output_dir = project_root / "docs" / "research_tracks"
    report_dir = project_root / "docs" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "v0.5_manual_precision_sample_v0.2.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "v0.5_manual_precision_sample_v0.2.md").write_text(render_sample_markdown(payload), encoding="utf-8")
    (output_dir / "v0.5_annotation_queue_v0.1.md").write_text(_render_queue(payload), encoding="utf-8")
    (output_dir / "v0.5_annotation_coverage_v0.1.md").write_text(_render_coverage(payload, result), encoding="utf-8")
    (output_dir / "v0.5_track_confusion_matrix_v0.1.md").write_text(_render_confusion(result), encoding="utf-8")
    (output_dir / "v0.5_false_positive_review_v0.1.md").write_text(
        _render_error_review("v0.5 False Positive Review v0.1", result["false_positives"], "false positives"), encoding="utf-8"
    )
    (output_dir / "v0.5_false_negative_review_v0.1.md").write_text(
        _render_error_review("v0.5 False Negative Review v0.1", result["false_negatives"], "false negatives"), encoding="utf-8"
    )
    (output_dir / "v0.5_ambiguous_case_review_v0.1.md").write_text(_render_ambiguous(result), encoding="utf-8")
    (output_dir / "v0.5_track_explanation_quality_v0.1.md").write_text(
        _render_explanation_quality(payload, result), encoding="utf-8"
    )
    (output_dir / "v0.5_offline_precision_results_v0.1.md").write_text(_render_results(payload, result), encoding="utf-8")
    (output_dir / "v0.5_offline_rule_candidates_v0.1.md").write_text(
        "# v0.5 Offline Rule Candidates v0.1\n\n"
        "These are shadow-mode design candidates only.\n\n"
        "- Require a lattice/PQC anchor before generic commitment, signature, privacy, AI, or implementation terms can assign a track.\n"
        "- Treat ring/linkable signatures without lattice/SIS/LWE evidence as ambiguous.\n"
        "- Treat generic ML model names such as Falcon as irrelevant unless cryptographic context is explicit.\n"
        "- Keep classical lattice attacks in Track C even when no machine learning is present; record AI assistance separately.\n"
        "- Prevent Track D from absorbing generic non-lattice PQC, generic FHE applications, and unrelated systems papers.\n\n"
        "No candidate is approved for production.\n",
        encoding="utf-8",
    )
    (output_dir / "v0.5_production_gate_after_offline_evaluation_v0.1.md").write_text(
        "# v0.5 Production Gate After Offline Evaluation v0.1\n\n"
        "Decision: `blocked_by_multiple_conditions`.\n\n"
        "Blockers:\n\n"
        "- zero user-confirmed or user-corrected gold labels;\n"
        "- human-gold precision/recall/F1 unavailable;\n"
        "- sample target and per-track balance not reached;\n"
        "- current CI recovery remains outside this offline evaluation;\n"
        "- durable post-tag run evidence remains absent.\n\n"
        "Experimental rules may be considered for a future shadow-mode design only after human annotation and engineering gates recover.\n",
        encoding="utf-8",
    )

    (report_dir / "phase-13b-gold-sample-provenance-log.md").write_text(
        "# Phase 13B Gold Sample Provenance Log\n\n"
        f"- unique repository records retained: `{payload['sample_size']}`\n"
        "- sources: existing `data/YYYY-MM-DD.json` and `data/weekly/*.json` only\n"
        "- deduplication: paper ID, DOI, record ID, URL, then title fallback\n"
        "- external paper lookup: none\n"
        "- invented metadata: none\n"
        "- production artifacts rewritten: none\n"
        "- human gold labels: zero\n\n"
        "Each JSON row retains all repository artifact paths in `source_provenance`.\n",
        encoding="utf-8",
    )
    (report_dir / "phase-13b-offline-evaluation-log.md").write_text(
        "# Phase 13B Offline Evaluation Log\n\n"
        "Command: `python scripts/evaluate_v0_5_track_precision.py`\n\n"
        f"- input records: `{payload['sample_size']}`\n"
        f"- output sample records: `{payload['sample_size']}`\n"
        f"- human-gold records: `{result['human_gold_metrics']['valid_gold_count']}`\n"
        "- human-gold metrics: not computed\n"
        "- diagnostic comparison: machine proposal versus Codex-reviewed provisional labels\n"
        "- production logic changed: no\n"
        "- design gate: `sample_design_ready_with_coverage_gaps`\n"
        "- production gate: `blocked_by_multiple_conditions`\n",
        encoding="utf-8",
    )


def main() -> int:
    payload = build_sample(PROJECT_ROOT)
    result = evaluate_sample(payload)
    write_outputs(payload, result, PROJECT_ROOT)
    print(json.dumps({
        "sample_size": payload["sample_size"],
        "distribution": payload["distribution"],
        "human_gold_count": result["human_gold_metrics"]["valid_gold_count"],
        "coverage_gaps": payload["coverage_gaps"],
        "design_gate": "sample_design_ready_with_coverage_gaps",
        "production_gate": "blocked_by_multiple_conditions",
    }, ensure_ascii=False, indent=2))
    return 0 if payload["sample_size"] >= payload["minimum_acceptable_size"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
