from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLE = PROJECT_ROOT / "docs/research_tracks/v0.5_manual_precision_sample_v0.2.json"
DEFAULT_RULES = PROJECT_ROOT / "experiments/v0_5_shadow_track_rules.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs/research_tracks"
DEFAULT_PACK_SIZE = 25

SHADOW_SCRIPT = PROJECT_ROOT / "scripts/run_v0_5_shadow_track_classifier.py"
SPEC = importlib.util.spec_from_file_location("v0_5_shadow_for_pack", SHADOW_SCRIPT)
SHADOW = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SHADOW)

VALID_HUMAN_STATES = {
    "not_reviewed",
    "queued_for_user",
    "user_confirmed",
    "user_corrected",
    "excluded_insufficient_metadata",
    "conflict_requires_adjudication",
}

DISAGREEMENT_PRIORITY = {
    "primary_track_disagreement": 100,
    "production_labeled_shadow_irrelevant": 95,
    "production_unlabeled_shadow_labeled": 90,
    "ambiguous_disagreement": 85,
    "insufficient_metadata": 80,
    "secondary_track_disagreement": 70,
    "exact_match": 10,
}


def _review_priority(record: dict[str, Any], shadow: dict[str, Any]) -> tuple[float, list[str]]:
    category = shadow["disagreement_category"]
    score = float(DISAGREEMENT_PRIORITY[category])
    reasons = [category]
    score += (1.0 - float(shadow["confidence"])) * 30

    codex_primary = str(record.get("codex_reviewed_primary_track") or "ambiguous")
    if codex_primary != shadow["shadow_primary_track"]:
        score += 25
        reasons.append("codex_shadow_disagreement")
    if record.get("control_label") in {"ambiguous", "multi_track"}:
        score += 15
        reasons.append("ambiguous_or_multi_track")

    text = SHADOW.evidence_text(record)
    risk_checks = {
        "track_b_identity_or_generic_privacy": ("xingye", "privacy-preserving", "anonymous"),
        "track_c_generic_ml": ("machine learning", "transformer", "neural", "time series"),
        "track_a_generic_signature_commitment": ("signature", "commitment"),
        "track_d_miscellaneous_bucket": ("implementation", "post-quantum", "pqc"),
    }
    for reason, terms in risk_checks.items():
        if any(term in text for term in terms):
            score += 4
            reasons.append(reason)
    return round(score, 2), reasons


def _suggested_decision(record: dict[str, Any], shadow: dict[str, Any]) -> str:
    if shadow["disagreement_category"] == "insufficient_metadata":
        return "exclude_or_request_metadata"
    if record.get("control_label") == "ambiguous":
        return "adjudicate_ambiguous"
    if shadow["disagreement_category"] == "exact_match":
        return "confirm_or_correct_after_evidence_review"
    return "choose_primary_track_or_irrelevant"


def build_pack(
    sample: dict[str, Any], shadow_payload: dict[str, Any], pack_size: int = DEFAULT_PACK_SIZE
) -> dict[str, Any]:
    sample_by_id = {row["sample_id"]: row for row in sample.get("records") or []}
    candidates: list[dict[str, Any]] = []

    for shadow in shadow_payload.get("records") or []:
        record = sample_by_id[shadow["sample_id"]]
        priority, reasons = _review_priority(record, shadow)
        evidence = record.get("available_evidence") or {}
        candidates.append(
            {
                "sample_id": record["sample_id"],
                "repository_record_id": record["repository_record_id"],
                "title": record["title"],
                "source": record.get("source"),
                "available_abstract_or_evidence": evidence,
                "current_production_primary_track": shadow["production_primary_track"],
                "current_production_secondary_tracks": shadow["production_secondary_tracks"],
                "shadow_proposed_primary_track": shadow["shadow_primary_track"],
                "shadow_proposed_secondary_tracks": shadow["shadow_secondary_tracks"],
                "codex_reviewed_primary_track": record.get("codex_reviewed_primary_track"),
                "codex_reviewed_secondary_tracks": record.get("codex_reviewed_secondary_tracks") or [],
                "disagreement_type": shadow["disagreement_category"],
                "review_priority_score": priority,
                "review_priority_reasons": reasons,
                "positive_evidence": record.get("positive_evidence"),
                "exclusion_evidence": record.get("exclusion_evidence"),
                "suggested_user_decision": _suggested_decision(record, shadow),
                "human_gold_primary_track": None,
                "human_gold_secondary_tracks": [],
                "human_review_status": "queued_for_user",
                "reviewer_note": "",
                "TODO_VERIFY": record.get("TODO_VERIFY") or ["user decision required"],
            }
        )

    candidates.sort(key=lambda row: (-row["review_priority_score"], row["sample_id"]))
    selected = candidates[: min(pack_size, len(candidates))]
    counts = Counter(row["disagreement_type"] for row in selected)
    return {
        "schema_version": 1,
        "pack_type": "human_annotation_review_queue",
        "source_sample_size": sample.get("sample_size", len(sample_by_id)),
        "requested_pack_size": pack_size,
        "annotation_pack_size": len(selected),
        "queued_user_review_count": len(selected),
        "user_confirmed_count": 0,
        "user_corrected_count": 0,
        "coverage_limited": len(candidates) < pack_size,
        "disagreement_counts": dict(sorted(counts.items())),
        "records": selected,
    }


def _csv_value(value: Any) -> str:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return "" if value is None else str(value)


def _write_csv(records: list[dict[str, Any]], path: Path) -> None:
    if not records:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(records[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {key: _csv_value(value) for key, value in row.items()}
            for row in records
        )


def write_pack(payload: dict[str, Any], output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = "v0.5_human_annotation_pack_v0.1"
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"
    md_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_csv(payload["records"], csv_path)

    lines = [
        "# v0.5 Human Annotation Pack v0.1",
        "",
        "> This is a user review queue. Codex and the shadow classifier do not create human gold labels.",
        "",
        f"- Pack size: {payload['annotation_pack_size']}",
        f"- Queued for user: {payload['queued_user_review_count']}",
        f"- User confirmed: {payload['user_confirmed_count']}",
        "",
    ]
    for index, row in enumerate(payload["records"], start=1):
        lines.extend(
            [
                f"## {index}. {row['sample_id']} - {row['title']}",
                "",
                f"- Repository record: `{row['repository_record_id']}`",
                f"- Source: `{row['source']}`",
                f"- Production: `{row['current_production_primary_track']}`",
                f"- Shadow proposal: `{row['shadow_proposed_primary_track']}`",
                f"- Codex review: `{row['codex_reviewed_primary_track']}`",
                f"- Disagreement: `{row['disagreement_type']}`",
                f"- Positive evidence: {row['positive_evidence']}",
                f"- Exclusion evidence: {row['exclusion_evidence']}",
                f"- Suggested decision: `{row['suggested_user_decision']}`",
                "- Human gold primary track: ` `",
                "- Human gold secondary tracks: ` `",
                "- Reviewer note: ` `",
                "- Status: `queued_for_user`",
                "",
            ]
        )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return json_path, csv_path, md_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the v0.5 human annotation review pack.")
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--pack-size", type=int, default=DEFAULT_PACK_SIZE)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    sample = SHADOW.load_json(args.sample)
    rules = SHADOW.load_json(args.rules)
    shadow_payload = SHADOW.classify_sample(sample, rules)
    payload = build_pack(sample, shadow_payload, args.pack_size)
    paths = write_pack(payload, args.output_dir)
    print(f"annotation pack: {payload['annotation_pack_size']}")
    print(f"queued for user: {payload['queued_user_review_count']}")
    print(f"user confirmed: {payload['user_confirmed_count']}")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
