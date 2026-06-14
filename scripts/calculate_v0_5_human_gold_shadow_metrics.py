from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PACK = PROJECT_ROOT / "docs/research_tracks/v0.5_human_annotation_pack_v0.1.json"
DEFAULT_ANNOTATIONS = PROJECT_ROOT / "docs/research_tracks/v0.5_human_annotation_pack_v0.1.csv"
DEFAULT_SHADOW = PROJECT_ROOT / "docs/research_tracks/v0.5_shadow_pilot_predictions_v0.1.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs/research_tracks"
PROTECTED_OUTPUT_ROOTS = tuple(
    PROJECT_ROOT / name for name in ("data", "digests", "handoffs", "src", "lattice_digest")
)

TRACKS = (
    "module_sis_sanitizable_signatures",
    "xingye_lu_bridge",
    "ai4lattice_cryptanalysis",
    "core_pqc_and_implementation",
)
CONTROL_LABELS = {"irrelevant", "ambiguous", "multi_track"}
ALLOWED_LABELS = set(TRACKS) | CONTROL_LABELS
GOLD_STATES = {"user_confirmed", "user_corrected"}
ADJUDICATOR_PATH = PROJECT_ROOT / "scripts/adjudicate_v0_5_human_annotations.py"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _load_adjudicator():
    spec = importlib.util.spec_from_file_location("v0_5_annotation_adjudicator", ADJUDICATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load annotation adjudicator: {ADJUDICATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_current_adjudication(source_pack: Path, annotations: Path) -> dict[str, Any]:
    adjudicator = _load_adjudicator()
    rows, errors = adjudicator.load_annotation_rows(annotations)
    return adjudicator.adjudicate(adjudicator._load_json(source_pack), rows, errors)


def _labels(primary: Any, secondary: Any) -> set[str]:
    primary_label = str(primary or "").strip()
    secondary_labels = {
        str(label).strip() for label in (secondary or []) if str(label).strip() in ALLOWED_LABELS
    }
    if primary_label == "multi_track":
        return secondary_labels
    if primary_label in ALLOWED_LABELS:
        secondary_labels.add(primary_label)
    return secondary_labels


def _validate_gold_rows(adjudicated: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    valid: list[dict[str, Any]] = []
    issues = [dict(issue) for issue in adjudicated.get("malformed_rows") or []]
    for row in adjudicated.get("records") or []:
        sample_id = str(row.get("sample_id") or "")
        status = str(row.get("human_review_status") or "")
        primary = row.get("human_gold_primary_track")
        secondary = row.get("human_gold_secondary_tracks") or []
        if primary and primary not in ALLOWED_LABELS:
            issues.append({"sample_id": sample_id, "field": "human_gold_primary_track", "error": "invalid label"})
            continue
        if any(label not in ALLOWED_LABELS for label in secondary):
            issues.append({"sample_id": sample_id, "field": "human_gold_secondary_tracks", "error": "invalid label"})
            continue
        if status not in GOLD_STATES:
            if primary or secondary:
                issues.append(
                    {
                        "sample_id": sample_id,
                        "field": "human_review_status",
                        "error": "gold label is ignored without user_confirmed or user_corrected",
                    }
                )
            continue
        if not primary:
            issues.append(
                {
                    "sample_id": sample_id,
                    "field": "human_gold_primary_track",
                    "error": "required for user-confirmed gold row",
                }
            )
            continue
        if primary == "multi_track" and len(_labels(primary, secondary)) < 2:
            issues.append(
                {
                    "sample_id": sample_id,
                    "field": "human_gold_secondary_tracks",
                    "error": "multi_track requires at least two concrete labels",
                }
            )
            continue
        if not row.get("valid_human_gold", True):
            issues.append({"sample_id": sample_id, "field": "valid_human_gold", "error": "adjudication rejected row"})
            continue
        valid.append(row)
    return valid, issues


def _binary_metric(truth: list[bool], predicted: list[bool]) -> dict[str, Any]:
    tp = sum(expected and actual for expected, actual in zip(truth, predicted, strict=True))
    fp = sum(not expected and actual for expected, actual in zip(truth, predicted, strict=True))
    fn = sum(expected and not actual for expected, actual in zip(truth, predicted, strict=True))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "support": sum(truth),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _model_metrics(rows: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    per_track: dict[str, dict[str, Any]] = {}
    all_tp = all_fp = all_fn = 0
    for track in TRACKS:
        truth = [track in row["gold_labels"] for row in rows]
        predicted = [track in row[f"{prefix}_labels"] for row in rows]
        metric = _binary_metric(truth, predicted)
        per_track[track] = metric
        all_tp += metric["tp"]
        all_fp += metric["fp"]
        all_fn += metric["fn"]

    evaluated = [metric for metric in per_track.values() if metric["support"] or metric["tp"] + metric["fp"]]
    precision_values = [metric["precision"] for metric in evaluated if metric["precision"] is not None]
    recall_values = [metric["recall"] for metric in evaluated if metric["recall"] is not None]
    f1_values = [metric["f1"] for metric in evaluated if metric["f1"] is not None]
    micro_precision = all_tp / (all_tp + all_fp) if all_tp + all_fp else None
    micro_recall = all_tp / (all_tp + all_fn) if all_tp + all_fn else None
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if micro_precision is not None and micro_recall is not None and micro_precision + micro_recall
        else None
    )
    confusion: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        confusion[row["gold_primary"]][row[f"{prefix}_primary"]] += 1
    return {
        "evaluated_rows": len(rows),
        "per_track": per_track,
        "macro_precision": sum(precision_values) / len(precision_values) if precision_values else None,
        "macro_recall": sum(recall_values) / len(recall_values) if recall_values else None,
        "macro_f1": sum(f1_values) / len(f1_values) if f1_values else None,
        "micro_f1": micro_f1,
        "false_positive_count": all_fp,
        "false_negative_count": all_fn,
        "confusion_matrix": {label: dict(sorted(values.items())) for label, values in sorted(confusion.items())},
    }


def evaluate(adjudicated: dict[str, Any], shadow_snapshot: dict[str, Any]) -> dict[str, Any]:
    gold_rows, issues = _validate_gold_rows(adjudicated)
    predictions = {
        str(row.get("sample_id")): row
        for row in shadow_snapshot.get("records") or []
        if row.get("sample_id")
    }
    evaluation_rows: list[dict[str, Any]] = []
    missing_predictions: list[str] = []
    for gold in gold_rows:
        sample_id = str(gold.get("sample_id"))
        prediction = predictions.get(sample_id)
        if prediction is None:
            missing_predictions.append(sample_id)
            continue
        evaluation_rows.append(
            {
                "sample_id": sample_id,
                "gold_primary": str(gold["human_gold_primary_track"]),
                "gold_labels": _labels(gold["human_gold_primary_track"], gold.get("human_gold_secondary_tracks")),
                "shadow_primary": str(prediction.get("shadow_primary_track") or "irrelevant"),
                "shadow_labels": _labels(prediction.get("shadow_primary_track"), prediction.get("shadow_secondary_tracks")),
                "production_primary": str(prediction.get("production_primary_track") or "irrelevant"),
                "production_labels": _labels(
                    prediction.get("production_primary_track"), prediction.get("production_secondary_tracks")
                ),
            }
        )

    valid_gold_count = len(gold_rows)
    metrics_available = bool(evaluation_rows)
    gold_ids = {str(row.get("sample_id")) for row in gold_rows}
    unreviewed = [
        row for row in shadow_snapshot.get("records") or [] if str(row.get("sample_id") or "") not in gold_ids
    ]
    disagreements = Counter(str(row.get("disagreement_category") or "unknown") for row in unreviewed)
    annotation_total = len(adjudicated.get("records") or [])
    invalid_ids = {str(issue.get("sample_id") or "<global>") for issue in issues}
    result: dict[str, Any] = {
        "schema_version": 1,
        "human_gold_metrics_available": metrics_available,
        "human_gold_count": valid_gold_count,
        "human_gold_rows_with_predictions": len(evaluation_rows),
        "missing_prediction_count": len(missing_predictions),
        "missing_prediction_sample_ids": missing_predictions,
        "invalid_annotation_count": len(invalid_ids),
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "annotation_row_count": annotation_total,
        "annotation_coverage": valid_gold_count / annotation_total if annotation_total else 0.0,
        "review_queue_count": sum(
            str(row.get("human_review_status") or "") not in GOLD_STATES
            for row in adjudicated.get("records") or []
        ),
        "unreviewed_shadow_record_count": len(unreviewed),
        "shadow_production_disagreement_counts_without_gold": dict(sorted(disagreements.items())),
        "human_gold_metric_status": (
            "invalid_human_gold_annotations"
            if issues and not valid_gold_count
            else "no_human_gold_labels"
            if not valid_gold_count
            else "partial_human_gold_metrics_ready"
            if valid_gold_count < annotation_total or missing_predictions
            else "human_gold_metrics_ready"
        ),
        "shadow_mode_metric_status": (
            "shadow_metrics_validated_against_gold"
            if metrics_available and not missing_predictions
            else "shadow_metrics_partial"
            if metrics_available
            else "blocked_by_annotation_quality"
            if issues
            else "shadow_metrics_not_available_no_gold"
        ),
        "metric_gate": "blocked_until_user_annotation" if not metrics_available else "blocked_until_metric_target",
        "production_gate": "blocked_by_multiple_conditions",
    }
    if metrics_available:
        result["shadow_vs_human_gold"] = _model_metrics(evaluation_rows, "shadow")
        result["production_vs_human_gold"] = _model_metrics(evaluation_rows, "production")
    else:
        result["shadow_vs_human_gold"] = None
        result["production_vs_human_gold"] = None
    return result


def _fmt(value: Any) -> str:
    return "TODO_VERIFY" if value is None else f"{value:.4f}" if isinstance(value, float) else str(value)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def validate_output_directory(output_dir: Path) -> Path:
    resolved = output_dir.resolve()
    if any(_is_relative_to(resolved, root.resolve()) for root in PROTECTED_OUTPUT_ROOTS):
        raise ValueError("Human-gold metric outputs cannot be written to a production path")
    return resolved


def _metric_document(title: str, metrics: dict[str, Any] | None) -> str:
    lines = [f"# {title}", ""]
    if metrics is None:
        lines.extend(
            [
                "Status: `not_available`.",
                "",
                "No final precision, recall, or F1 is reported because no valid explicit human-gold row is available.",
            ]
        )
        return "\n".join(lines) + "\n"
    lines.extend(
        [
            f"- Evaluated rows: {metrics['evaluated_rows']}",
            f"- Macro precision: `{_fmt(metrics['macro_precision'])}`",
            f"- Macro recall: `{_fmt(metrics['macro_recall'])}`",
            f"- Macro F1: `{_fmt(metrics['macro_f1'])}`",
            f"- Micro F1: `{_fmt(metrics['micro_f1'])}`",
            f"- False positives: {metrics['false_positive_count']}",
            f"- False negatives: {metrics['false_negative_count']}",
            "",
            "| Track | Precision | Recall | F1 | Support | TP | FP | FN |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for track, metric in metrics["per_track"].items():
        lines.append(
            f"| `{track}` | {_fmt(metric['precision'])} | {_fmt(metric['recall'])} | "
            f"{_fmt(metric['f1'])} | {metric['support']} | {metric['tp']} | {metric['fp']} | {metric['fn']} |"
        )
    return "\n".join(lines) + "\n"


def write_outputs(result: dict[str, Any], output_dir: Path) -> list[Path]:
    output_dir = validate_output_directory(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": output_dir / "v0.5_human_gold_metrics_v0.1.json",
        "summary": output_dir / "v0.5_human_gold_metrics_v0.1.md",
        "confusion": output_dir / "v0.5_human_gold_confusion_matrix_v0.1.md",
        "shadow": output_dir / "v0.5_shadow_vs_human_gold_metrics_v0.1.md",
        "production": output_dir / "v0.5_production_vs_human_gold_metrics_v0.1.md",
        "validation": output_dir / "v0.5_human_gold_label_validation_v0.1.md",
        "no_gold": output_dir / "v0.5_no_gold_label_status_v0.1.md",
        "queue": output_dir / "v0.5_annotation_queue_after_metrics_v0.1.md",
        "boundaries": output_dir / "v0.5_metric_interpretation_boundaries_v0.1.md",
        "disagreement": output_dir / "v0.5_shadow_production_disagreement_without_gold_v0.1.md",
        "gold_gate": output_dir / "v0.5_gold_required_before_production_patch_v0.1.md",
        "blockers": output_dir / "v0.5_shadow_metric_blockers_v0.1.md",
        "production_gate": output_dir / "v0.5_production_gate_after_human_gold_metrics_v0.1.md",
        "release_relation": output_dir / "v0.4.1_release_relation_to_v0.5_metrics_v0.1.md",
    }
    paths["json"].write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = [
        "# v0.5 Human Gold Metrics v0.1",
        "",
        f"- Status: `{result['human_gold_metric_status']}`",
        f"- Human-gold rows: {result['human_gold_count']}",
        f"- Metrics available: `{str(result['human_gold_metrics_available']).lower()}`",
        f"- Invalid annotations: {result['invalid_annotation_count']}",
        f"- Review queue: {result['review_queue_count']}",
        f"- Annotation coverage: `{_fmt(result['annotation_coverage'])}`",
    ]
    if not result["human_gold_metrics_available"]:
        summary.extend(["", "No final precision, recall, or F1 is computed."])
    paths["summary"].write_text("\n".join(summary) + "\n", encoding="utf-8")
    paths["shadow"].write_text(
        _metric_document("v0.5 Shadow vs Human Gold Metrics v0.1", result["shadow_vs_human_gold"]),
        encoding="utf-8",
    )
    paths["production"].write_text(
        _metric_document("v0.5 Production vs Human Gold Metrics v0.1", result["production_vs_human_gold"]),
        encoding="utf-8",
    )
    confusion = ["# v0.5 Human Gold Confusion Matrix v0.1", ""]
    if not result["human_gold_metrics_available"]:
        confusion.append("Unavailable: no valid explicit human-gold rows.")
    else:
        for name in ("shadow_vs_human_gold", "production_vs_human_gold"):
            confusion.extend([f"## {name}", "", "```json", json.dumps(result[name]["confusion_matrix"], ensure_ascii=False, indent=2), "```", ""])
    paths["confusion"].write_text("\n".join(confusion).rstrip() + "\n", encoding="utf-8")
    validation = [
        "# v0.5 Human Gold Label Validation v0.1",
        "",
        f"- Invalid annotation rows: {result['invalid_annotation_count']}",
        f"- Validation issues: {result['validation_issue_count']}",
    ]
    validation.extend(
        f"- `{issue.get('sample_id')}` `{issue.get('field')}`: {issue.get('error')}"
        for issue in result["validation_issues"]
    )
    paths["validation"].write_text("\n".join(validation) + "\n", encoding="utf-8")
    paths["no_gold"].write_text(
        "# v0.5 No Gold Label Status v0.1\n\n"
        + (
            "Status: `no_human_gold_labels`. Final precision, recall, and F1 are intentionally unavailable.\n"
            if not result["human_gold_count"]
            else "Status: `not_applicable`; at least one valid human-gold row exists.\n"
        ),
        encoding="utf-8",
    )
    paths["queue"].write_text(
        "# v0.5 Annotation Queue After Metrics v0.1\n\n"
        f"Remaining user-review rows: {result['review_queue_count']}.\n",
        encoding="utf-8",
    )
    paths["boundaries"].write_text(
        "# v0.5 Metric Interpretation Boundaries v0.1\n\n"
        "Only explicit `user_confirmed` and `user_corrected` rows contribute to gold metrics. "
        "Unreviewed shadow-production agreement is diagnostic, not accuracy. Macro values cover only research tracks "
        "with observed gold or predicted positives; control labels remain visible in the primary confusion matrix.\n",
        encoding="utf-8",
    )
    disagreement = [
        "# v0.5 Shadow Production Disagreement Without Gold v0.1",
        "",
        f"Unreviewed records: {result['unreviewed_shadow_record_count']}.",
        "",
    ]
    disagreement.extend(
        f"- `{name}`: {count}"
        for name, count in result["shadow_production_disagreement_counts_without_gold"].items()
    )
    disagreement.append("\nThese counts do not establish precision or recall.")
    paths["disagreement"].write_text("\n".join(disagreement) + "\n", encoding="utf-8")
    paths["gold_gate"].write_text(
        "# v0.5 Gold Required Before Production Patch v0.1\n\n"
        "Production classifier changes remain blocked until explicit user labels support reproducible metrics and error review.\n",
        encoding="utf-8",
    )
    blockers = [
        "# v0.5 Shadow Metric Blockers v0.1",
        "",
        f"- Human-gold rows: {result['human_gold_count']}",
        f"- Missing prediction rows: {result['missing_prediction_count']}",
        f"- Invalid annotation rows: {result['invalid_annotation_count']}",
        "- Existing v0.4.1 CI and durable-run gates remain separate blockers.",
    ]
    paths["blockers"].write_text("\n".join(blockers) + "\n", encoding="utf-8")
    paths["production_gate"].write_text(
        "# v0.5 Production Gate After Human Gold Metrics v0.1\n\n"
        f"Decision: `{result['production_gate']}`.\n\n"
        f"Metric-specific gate: `{result['metric_gate']}`. Production readiness is not established.\n",
        encoding="utf-8",
    )
    paths["release_relation"].write_text(
        "# v0.4.1 Release Relation to v0.5 Metrics v0.1\n\n"
        "Phase 13H metrics cannot unblock v0.4.1. CI, durable Daily evidence, release hygiene, and the historical tag state "
        "remain independent release evidence. The existing v0.4.1 tag is not modified.\n",
        encoding="utf-8",
    )
    return list(paths.values())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calculate v0.5 metrics only from explicit human-gold labels.")
    parser.add_argument("--source-pack", type=Path, default=DEFAULT_SOURCE_PACK)
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--shadow", type=Path, default=DEFAULT_SHADOW)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    adjudicated = load_current_adjudication(args.source_pack, args.annotations)
    result = evaluate(adjudicated, _load_json(args.shadow))
    write_outputs(result, args.output_dir)
    print(f"human gold rows: {result['human_gold_count']}")
    print(f"invalid annotations: {result['invalid_annotation_count']}")
    print(f"metrics available: {result['human_gold_metrics_available']}")
    print(f"review queue: {result['review_queue_count']}")
    print(f"production gate: {result['production_gate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
