from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADJUDICATED = PROJECT_ROOT / "docs/research_tracks/v0.5_human_annotation_adjudicated_v0.1.json"
DEFAULT_RULES = PROJECT_ROOT / "experiments/v0_5_shadow_track_rules.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs/research_tracks"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


SHADOW = _load_module("v0_5_shadow_for_pilot", PROJECT_ROOT / "scripts/run_v0_5_shadow_track_classifier.py")
SAMPLE = _load_module("v0_5_sample_for_pilot", PROJECT_ROOT / "scripts/evaluate_v0_5_track_precision.py")

TRACKS = SHADOW.TRACKS


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _label_set(primary: str | None, secondary: list[str] | None) -> set[str]:
    return {label for label in [primary, *(secondary or [])] if label in TRACKS}


def _score(truth: list[bool], predicted: list[bool]) -> dict[str, float | int | None]:
    tp = sum(t and p for t, p in zip(truth, predicted))
    fp = sum(not t and p for t, p in zip(truth, predicted))
    fn = sum(t and not p for t, p in zip(truth, predicted))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def _gold_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gold = [row for row in rows if row.get("valid_human_gold")]
    if not gold:
        return {
            "eligible": False,
            "valid_gold_count": 0,
            "per_track": None,
            "macro_f1": None,
            "false_positive_rate": None,
            "false_negative_rate": None,
        }
    per_track = {}
    all_fp = all_fn = all_negative = all_positive = 0
    for track in TRACKS:
        truth = [track in _label_set(row.get("human_gold_primary_track"), row.get("human_gold_secondary_tracks")) for row in gold]
        pred = [track in _label_set(row.get("shadow_primary_track"), row.get("shadow_secondary_tracks")) for row in gold]
        per_track[track] = _score(truth, pred)
        all_fp += per_track[track]["fp"]
        all_fn += per_track[track]["fn"]
        all_negative += sum(not value for value in truth)
        all_positive += sum(truth)
    f1_values = [value["f1"] for value in per_track.values() if value["f1"] is not None]
    return {
        "eligible": True,
        "valid_gold_count": len(gold),
        "per_track": per_track,
        "macro_f1": sum(f1_values) / len(f1_values) if f1_values else None,
        "false_positive_rate": all_fp / all_negative if all_negative else None,
        "false_negative_rate": all_fn / all_positive if all_positive else None,
    }


def _metadata_insufficient(record: dict[str, Any]) -> bool:
    evidence = record.get("available_evidence") or {}
    return not str(record.get("title") or "").strip() or not any(
        [
            str(evidence.get("abstract") or "").strip(),
            evidence.get("taxonomy_tags"),
            evidence.get("keywords_matched"),
        ]
    )


def run_pilot(
    broad_sample: dict[str, Any], adjudicated: dict[str, Any], rules: dict[str, Any]
) -> dict[str, Any]:
    shadow_payload = SHADOW.classify_sample(broad_sample, rules)
    sample_by_id = {row["sample_id"]: row for row in broad_sample.get("records") or []}
    human_by_record = {row["repository_record_id"]: row for row in adjudicated.get("records") or []}
    selected_ids = set(human_by_record)
    rows: list[dict[str, Any]] = []

    for prediction in shadow_payload["records"]:
        sample = sample_by_id[prediction["sample_id"]]
        human = human_by_record.get(sample["repository_record_id"], {})
        row = {
            **prediction,
            "selected_annotation_pack": sample["repository_record_id"] in selected_ids,
            "codex_reviewed_primary_track": sample.get("codex_reviewed_primary_track"),
            "codex_reviewed_secondary_tracks": sample.get("codex_reviewed_secondary_tracks") or [],
            "human_gold_primary_track": human.get("human_gold_primary_track"),
            "human_gold_secondary_tracks": human.get("human_gold_secondary_tracks") or [],
            "human_review_status": human.get("human_review_status", "not_reviewed"),
            "valid_human_gold": bool(human.get("valid_human_gold")),
            "metadata_insufficient": _metadata_insufficient(sample),
            "available_evidence": sample.get("available_evidence") or {},
            "source_provenance": sample.get("source_provenance") or [],
        }
        rows.append(row)

    disagreements = Counter(row["disagreement_category"] for row in rows)
    exact = disagreements["exact_match"]
    explanation_complete = sum(bool(row.get("explanation")) for row in rows)
    metadata_insufficient = sum(row["metadata_insufficient"] for row in rows)
    error_taxonomy = Counter()
    for row in rows:
        if row["shadow_primary_track"] == TRACKS[3] and row["codex_reviewed_primary_track"] != TRACKS[3]:
            error_taxonomy["track_d_bucket_drift"] += 1
        if row["codex_reviewed_primary_track"] == TRACKS[1] and row["shadow_primary_track"] != TRACKS[1]:
            error_taxonomy["track_b_undercoverage"] += 1
        if row["disagreement_category"] == "production_labeled_shadow_irrelevant":
            error_taxonomy["shadow_undercoverage"] += 1
        if row["metadata_insufficient"]:
            error_taxonomy["insufficient_metadata"] += 1

    false_positives: list[dict[str, Any]] = []
    false_negatives: list[dict[str, Any]] = []
    confusion: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        truth = _label_set(row["codex_reviewed_primary_track"], row["codex_reviewed_secondary_tracks"])
        pred = _label_set(row["shadow_primary_track"], row["shadow_secondary_tracks"])
        confusion[row["codex_reviewed_primary_track"]][row["shadow_primary_track"]] += 1
        for track in sorted(pred - truth):
            false_positives.append({"sample_id": row["sample_id"], "track": track, "title": row["title"]})
        for track in sorted(truth - pred):
            false_negatives.append({"sample_id": row["sample_id"], "track": track, "title": row["title"]})

    gold_metrics = _gold_metrics(rows)
    return {
        "schema_version": 1,
        "pilot_type": "manual_offline_non_production",
        "production_logic_changed": False,
        "selected_sample_count": len(selected_ids),
        "broader_candidate_pool_count": len(rows),
        "human_gold_count": gold_metrics["valid_gold_count"],
        "human_gold_metrics": gold_metrics,
        "production_shadow_agreement_count": exact,
        "production_shadow_disagreement_count": len(rows) - exact,
        "production_shadow_agreement_rate": exact / len(rows) if rows else None,
        "disagreement_counts": dict(sorted(disagreements.items())),
        "explanation_completeness_rate": explanation_complete / len(rows) if rows else 1.0,
        "metadata_insufficiency_rate": metadata_insufficient / len(rows) if rows else 0.0,
        "error_taxonomy": dict(sorted(error_taxonomy.items())),
        "codex_review_confusion_matrix_not_gold": {key: dict(value) for key, value in sorted(confusion.items())},
        "false_positive_cases_not_gold": false_positives,
        "false_negative_cases_not_gold": false_negatives,
        "ambiguous_cases": [
            {"sample_id": row["sample_id"], "title": row["title"], "shadow": row["shadow_primary_track"]}
            for row in rows
            if row["codex_reviewed_primary_track"] == "ambiguous" or row["shadow_primary_track"] == "ambiguous"
        ],
        "shadow_pilot_status": "shadow_pilot_complete" if gold_metrics["eligible"] else "shadow_pilot_complete_without_gold_metrics",
        "shadow_mode_gate": "manual_shadow_pilot_only_pending_user_annotation",
        "production_gate": "blocked_by_multiple_conditions",
        "records": rows,
    }


def _case_lines(title: str, cases: list[dict[str, Any]]) -> list[str]:
    lines = [f"# {title}", "", "> Diagnostic against Codex-reviewed labels; not human-gold error measurement.", ""]
    for case in cases:
        lines.append(f"- `{case['sample_id']}` `{case['track']}`: {case['title']}")
    if not cases:
        lines.append("- None observed.")
    return lines


def write_outputs(payload: dict[str, Any], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "predictions": output_dir / "v0.5_shadow_pilot_predictions_v0.1.json",
        "results": output_dir / "v0.5_shadow_pilot_results_v0.1.md",
        "confusion": output_dir / "v0.5_shadow_pilot_confusion_matrix_v0.1.md",
        "taxonomy": output_dir / "v0.5_shadow_pilot_error_taxonomy_v0.1.md",
        "fp": output_dir / "v0.5_shadow_pilot_false_positive_cases_v0.1.md",
        "fn": output_dir / "v0.5_shadow_pilot_false_negative_cases_v0.1.md",
        "ambiguous": output_dir / "v0.5_shadow_pilot_ambiguous_cases_v0.1.md",
        "rules": output_dir / "v0.5_shadow_rule_revision_candidates_v0.1.md",
        "gate": output_dir / "v0.5_shadow_mode_pilot_gate_v0.1.md",
    }
    paths["predictions"].write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    results = [
        "# v0.5 Shadow Pilot Results v0.1",
        "",
        f"- Status: `{payload['shadow_pilot_status']}`",
        f"- Selected annotation sample: {payload['selected_sample_count']}",
        f"- Broader repository pool: {payload['broader_candidate_pool_count']}",
        f"- Human gold: {payload['human_gold_count']}",
        f"- Production-shadow agreement: {payload['production_shadow_agreement_count']}",
        f"- Production-shadow disagreement: {payload['production_shadow_disagreement_count']}",
        f"- Explanation completeness: {payload['explanation_completeness_rate']:.2%}",
        f"- Metadata insufficiency: {payload['metadata_insufficiency_rate']:.2%}",
        "",
        "No final accuracy metric is reported without explicit human gold labels.",
    ]
    paths["results"].write_text("\n".join(results) + "\n", encoding="utf-8")
    confusion = [
        "# v0.5 Shadow Pilot Confusion Matrix v0.1",
        "",
        "> Matrix uses Codex-reviewed labels only and is not a human-gold confusion matrix.",
        "",
    ]
    for truth, predictions in payload["codex_review_confusion_matrix_not_gold"].items():
        confusion.append(f"- `{truth}`: {json.dumps(predictions, ensure_ascii=False, sort_keys=True)}")
    paths["confusion"].write_text("\n".join(confusion) + "\n", encoding="utf-8")
    taxonomy = ["# v0.5 Shadow Pilot Error Taxonomy v0.1", ""]
    for name, count in payload["error_taxonomy"].items():
        taxonomy.append(f"- `{name}`: {count}")
    taxonomy.extend(["", "Counts are review signals, not human-gold error rates."])
    paths["taxonomy"].write_text("\n".join(taxonomy) + "\n", encoding="utf-8")
    paths["fp"].write_text("\n".join(_case_lines("v0.5 Shadow Pilot False Positive Cases v0.1", payload["false_positive_cases_not_gold"])) + "\n", encoding="utf-8")
    paths["fn"].write_text("\n".join(_case_lines("v0.5 Shadow Pilot False Negative Cases v0.1", payload["false_negative_cases_not_gold"])) + "\n", encoding="utf-8")
    ambiguous = ["# v0.5 Shadow Pilot Ambiguous Cases v0.1", ""]
    for case in payload["ambiguous_cases"]:
        ambiguous.append(f"- `{case['sample_id']}` shadow `{case['shadow']}`: {case['title']}")
    if not payload["ambiguous_cases"]:
        ambiguous.append("- None observed.")
    paths["ambiguous"].write_text("\n".join(ambiguous) + "\n", encoding="utf-8")
    paths["rules"].write_text(
        "# v0.5 Shadow Rule Revision Candidates v0.1\n\n"
        "- Reduce Track D bucket drift by distinguishing scheme mentions from paper centrality.\n"
        "- Add technically anchored Track B patterns without author-name features.\n"
        "- Preserve Track C attack anchors and reject generic ML/CV terms.\n"
        "- Require explicit Module-SIS/lattice construction evidence for generic signature/commitment terms.\n\n"
        "These are candidates for later controlled testing, not production changes.\n",
        encoding="utf-8",
    )
    paths["gate"].write_text(
        "# v0.5 Shadow Mode Pilot Gate v0.1\n\n"
        f"- Pilot status: `{payload['shadow_pilot_status']}`\n"
        f"- Shadow-mode gate: `{payload['shadow_mode_gate']}`\n"
        f"- Production gate: `{payload['production_gate']}`\n\n"
        "Future manual shadow evaluation may continue. Automatic or production integration remains blocked until user annotation, valid metrics, CI, and durable-run gates are satisfied.\n",
        encoding="utf-8",
    )
    return list(paths.values())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the manual, offline v0.5 shadow classifier pilot.")
    parser.add_argument("--adjudicated", type=Path, default=DEFAULT_ADJUDICATED)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    broad_sample = SAMPLE.build_sample(PROJECT_ROOT)
    payload = run_pilot(broad_sample, _load_json(args.adjudicated), _load_json(args.rules))
    write_outputs(payload, args.output_dir)
    print(f"shadow pilot records: {payload['broader_candidate_pool_count']}")
    print(f"agreement: {payload['production_shadow_agreement_count']}")
    print(f"disagreement: {payload['production_shadow_disagreement_count']}")
    print(f"human gold: {payload['human_gold_count']}")
    print(f"status: {payload['shadow_pilot_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
