from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PACK = PROJECT_ROOT / "docs/research_tracks/v0.5_human_annotation_pack_v0.1.json"
DEFAULT_ANNOTATIONS = PROJECT_ROOT / "docs/research_tracks/v0.5_human_annotation_pack_v0.1.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs/research_tracks"

TRACKS = {
    "module_sis_sanitizable_signatures",
    "xingye_lu_bridge",
    "ai4lattice_cryptanalysis",
    "core_pqc_and_implementation",
}
PRIMARY_LABELS = TRACKS | {"irrelevant", "ambiguous", "multi_track"}
REVIEW_STATES = {
    "not_reviewed",
    "queued_for_user",
    "user_confirmed",
    "user_corrected",
    "excluded_insufficient_metadata",
    "conflict_requires_adjudication",
}
GOLD_STATES = {"user_confirmed", "user_corrected"}
DECISION_FIELDS = {
    "human_gold_primary_track",
    "human_gold_secondary_tracks",
    "human_review_status",
    "reviewer_note",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _parse_list(value: str, field: str, sample_id: str, errors: list[dict[str, str]]) -> list[str]:
    text = (value or "").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = [item.strip() for item in text.split(",") if item.strip()]
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        errors.append({"sample_id": sample_id, "field": field, "error": "expected a JSON string list"})
        return []
    return [item.strip() for item in parsed if item.strip()]


def load_annotation_rows(path: Path) -> tuple[dict[str, dict[str, str]], list[dict[str, str]]]:
    rows: dict[str, dict[str, str]] = {}
    errors: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = DECISION_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Annotation CSV missing decision fields: {sorted(missing)}")
        for line_number, row in enumerate(reader, start=2):
            sample_id = (row.get("sample_id") or "").strip()
            if not sample_id:
                errors.append({"sample_id": "", "field": "sample_id", "error": f"missing at line {line_number}"})
                continue
            if sample_id in rows:
                errors.append({"sample_id": sample_id, "field": "sample_id", "error": "duplicate row"})
                continue
            rows[sample_id] = row
    return rows, errors


def _validate_decision(
    source: dict[str, Any], annotation: dict[str, str] | None, errors: list[dict[str, str]]
) -> dict[str, Any]:
    sample_id = source["sample_id"]
    if annotation is None:
        return {
            "primary": None,
            "secondary": [],
            "status": "queued_for_user",
            "reviewer_note": "",
            "valid_gold": False,
        }

    for immutable in ("repository_record_id", "title"):
        supplied = (annotation.get(immutable) or "").strip()
        expected = str(source.get(immutable) or "").strip()
        if supplied and supplied != expected:
            errors.append({"sample_id": sample_id, "field": immutable, "error": "does not match source pack"})

    status = (annotation.get("human_review_status") or "queued_for_user").strip()
    primary = (annotation.get("human_gold_primary_track") or "").strip() or None
    secondary = _parse_list(
        annotation.get("human_gold_secondary_tracks") or "", "human_gold_secondary_tracks", sample_id, errors
    )
    note = (annotation.get("reviewer_note") or "").strip()

    if status not in REVIEW_STATES:
        errors.append({"sample_id": sample_id, "field": "human_review_status", "error": f"invalid status: {status}"})
        status = "queued_for_user"
    if primary is not None and primary not in PRIMARY_LABELS:
        errors.append({"sample_id": sample_id, "field": "human_gold_primary_track", "error": f"invalid label: {primary}"})
    invalid_secondary = [label for label in secondary if label not in TRACKS]
    if invalid_secondary:
        errors.append(
            {"sample_id": sample_id, "field": "human_gold_secondary_tracks", "error": f"invalid labels: {invalid_secondary}"}
        )
    if primary in secondary:
        errors.append({"sample_id": sample_id, "field": "human_gold_secondary_tracks", "error": "duplicates primary"})
    if primary == "multi_track" and len(set(secondary)) < 2:
        errors.append(
            {
                "sample_id": sample_id,
                "field": "human_gold_secondary_tracks",
                "error": "multi_track requires at least two concrete labels",
            }
        )

    row_errors = [error for error in errors if error["sample_id"] == sample_id]
    if status in GOLD_STATES and primary is None:
        errors.append({"sample_id": sample_id, "field": "human_gold_primary_track", "error": "required for gold state"})
    if status not in GOLD_STATES and (primary is not None or secondary):
        errors.append({"sample_id": sample_id, "field": "human_review_status", "error": "gold label requires user_confirmed or user_corrected"})
    row_errors = [error for error in errors if error["sample_id"] == sample_id]
    valid_gold = status in GOLD_STATES and primary in PRIMARY_LABELS and not row_errors
    if not valid_gold and status in GOLD_STATES:
        status = "conflict_requires_adjudication"
        primary = None
        secondary = []
    elif status not in GOLD_STATES:
        primary = None
        secondary = []

    return {"primary": primary, "secondary": secondary, "status": status, "reviewer_note": note, "valid_gold": valid_gold}


def _conflict_type(row: dict[str, Any]) -> str:
    if not row["valid_human_gold"]:
        return "awaiting_user"
    gold = row["human_gold_primary_track"]
    production = row["current_production_primary_track"]
    shadow = row["shadow_proposed_primary_track"]
    if production == shadow == gold:
        return "all_agree"
    if gold == production != shadow:
        return "user_agrees_production"
    if gold == shadow != production:
        return "user_agrees_shadow"
    if production == shadow != gold:
        return "user_corrects_both"
    return "three_way_conflict"


def adjudicate(source_pack: dict[str, Any], annotations: dict[str, dict[str, str]], initial_errors: list[dict[str, str]]) -> dict[str, Any]:
    errors = list(initial_errors)
    source_ids = {row["sample_id"] for row in source_pack.get("records") or []}
    for unknown in sorted(set(annotations) - source_ids):
        errors.append({"sample_id": unknown, "field": "sample_id", "error": "not present in source pack"})

    rows: list[dict[str, Any]] = []
    for source in source_pack.get("records") or []:
        decision = _validate_decision(source, annotations.get(source["sample_id"]), errors)
        row = dict(source)
        row.update(
            {
                "human_gold_primary_track": decision["primary"],
                "human_gold_secondary_tracks": decision["secondary"],
                "human_review_status": decision["status"],
                "reviewer_note": decision["reviewer_note"],
                "valid_human_gold": decision["valid_gold"],
            }
        )
        row["conflict_resolution"] = _conflict_type(row)
        rows.append(row)

    statuses = Counter(row["human_review_status"] for row in rows)
    conflicts = Counter(row["conflict_resolution"] for row in rows)
    valid_gold = sum(row["valid_human_gold"] for row in rows)
    return {
        "schema_version": 1,
        "source_pack_size": len(source_pack.get("records") or []),
        "annotation_rows_processed": len(annotations),
        "user_confirmed_count": statuses["user_confirmed"],
        "user_corrected_count": statuses["user_corrected"],
        "queued_count": statuses["queued_for_user"] + statuses["not_reviewed"],
        "conflict_count": statuses["conflict_requires_adjudication"],
        "valid_human_gold_count": valid_gold,
        "gold_metrics_eligible": valid_gold > 0,
        "annotation_status": (
            "blocked_by_invalid_annotations"
            if errors
            else "human_gold_ready"
            if valid_gold == len(rows) and rows
            else "partial_human_gold_ready"
            if valid_gold
            else "queued_for_user_review"
        ),
        "status_counts": dict(sorted(statuses.items())),
        "conflict_resolution_counts": dict(sorted(conflicts.items())),
        "malformed_rows": errors,
        "records": rows,
    }


def write_outputs(payload: dict[str, Any], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "v0.5_human_annotation_adjudicated_v0.1.json"
    md_path = output_dir / "v0.5_human_annotation_adjudicated_v0.1.md"
    log_path = output_dir / "v0.5_human_annotation_adjudication_log_v0.1.md"
    validation_path = output_dir / "v0.5_user_label_validation_report_v0.1.md"
    conflict_path = output_dir / "v0.5_annotation_conflict_resolution_v0.1.md"
    scope_path = output_dir / "v0.5_human_gold_metrics_scope_v0.1.md"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = [
        "# v0.5 Human Annotation Adjudicated v0.1",
        "",
        f"- Status: `{payload['annotation_status']}`",
        f"- Rows processed: {payload['annotation_rows_processed']}",
        f"- User confirmed: {payload['user_confirmed_count']}",
        f"- User corrected: {payload['user_corrected_count']}",
        f"- Queued: {payload['queued_count']}",
        f"- Conflicts: {payload['conflict_count']}",
        f"- Gold metrics eligible: `{str(payload['gold_metrics_eligible']).lower()}`",
        "",
        "No missing decision was inferred. Only explicit valid user decisions count as human gold.",
        "",
        "## Records",
        "",
    ]
    for row in payload["records"]:
        summary.append(
            f"- `{row['sample_id']}` `{row['human_review_status']}` "
            f"gold=`{row['human_gold_primary_track'] or ''}` conflict=`{row['conflict_resolution']}`: {row['title']}"
        )
    md_path.write_text("\n".join(summary) + "\n", encoding="utf-8")
    log_path.write_text(
        "# v0.5 Human Annotation Adjudication Log v0.1\n\n"
        f"Processed {payload['annotation_rows_processed']} CSV rows against {payload['source_pack_size']} preserved source rows. "
        f"Valid human-gold rows: {payload['valid_human_gold_count']}.\n",
        encoding="utf-8",
    )
    validation_lines = [
        "# v0.5 User Label Validation Report v0.1",
        "",
        f"- Malformed rows: {len(payload['malformed_rows'])}",
        f"- Valid human-gold rows: {payload['valid_human_gold_count']}",
    ]
    for error in payload["malformed_rows"]:
        validation_lines.append(f"- `{error['sample_id']}` `{error['field']}`: {error['error']}")
    validation_path.write_text("\n".join(validation_lines) + "\n", encoding="utf-8")
    conflict_lines = ["# v0.5 Annotation Conflict Resolution v0.1", ""]
    for name, count in payload["conflict_resolution_counts"].items():
        conflict_lines.append(f"- `{name}`: {count}")
    conflict_lines.append("\nModel-model disagreement remains diagnostic until a user label exists.")
    conflict_path.write_text("\n".join(conflict_lines) + "\n", encoding="utf-8")
    scope_path.write_text(
        "# v0.5 Human Gold Metrics Scope v0.1\n\n"
        "Precision, recall, F1, false-positive rate, and false-negative rate may be computed only on rows with "
        "`user_confirmed` or `user_corrected` and a valid explicit gold label. "
        f"Current eligible rows: {payload['valid_human_gold_count']}.\n",
        encoding="utf-8",
    )
    return [json_path, md_path, log_path, validation_path, conflict_path, scope_path]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and adjudicate explicit v0.5 human annotations.")
    parser.add_argument("--source-pack", type=Path, default=DEFAULT_SOURCE_PACK)
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rows, errors = load_annotation_rows(args.annotations)
    payload = adjudicate(_load_json(args.source_pack), rows, errors)
    write_outputs(payload, args.output_dir)
    print(f"annotation rows processed: {payload['annotation_rows_processed']}")
    print(f"user confirmed: {payload['user_confirmed_count']}")
    print(f"user corrected: {payload['user_corrected_count']}")
    print(f"queued: {payload['queued_count']}")
    print(f"conflicts: {payload['conflict_count']}")
    print(f"gold metrics eligible: {payload['gold_metrics_eligible']}")
    return 0 if not payload["malformed_rows"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
