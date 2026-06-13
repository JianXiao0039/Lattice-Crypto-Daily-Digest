from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from lattice_digest.ideas import classify_track


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLE = PROJECT_ROOT / "docs/research_tracks/v0.5_manual_precision_sample_v0.2.json"
DEFAULT_RULES = PROJECT_ROOT / "experiments/v0_5_shadow_track_rules.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "audits/shadow"

TRACKS = (
    "module_sis_sanitizable_signatures",
    "xingye_lu_bridge",
    "ai4lattice_cryptanalysis",
    "core_pqc_and_implementation",
)

PRODUCTION_TRACK_MAP = {
    "Module-SIS Primitive": TRACKS[0],
    "ZK-friendly PQ Privacy": TRACKS[1],
    "AI4Lattice": TRACKS[2],
    "LWE/RLWE/MLWE Cryptanalysis": TRACKS[2],
    "BKZ / Lattice Reduction": TRACKS[2],
    "ML-KEM / ML-DSA Implementation Security": TRACKS[3],
    "PQC Systems": TRACKS[3],
    "FHE / Parameter Security": TRACKS[3],
    "Other": "irrelevant",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def evidence_text(record: dict[str, Any]) -> str:
    evidence = record.get("available_evidence") or {}
    values = [
        record.get("title"),
        evidence.get("abstract"),
        " ".join(map(str, evidence.get("taxonomy_tags") or [])),
        " ".join(map(str, evidence.get("keywords_matched") or [])),
    ]
    return " ".join(str(value or "") for value in values).lower()


def _production_record(record: dict[str, Any]) -> dict[str, Any]:
    evidence = record.get("available_evidence") or {}
    return {
        "title": record.get("title"),
        "abstract": evidence.get("abstract"),
        "research_tags": evidence.get("taxonomy_tags") or [],
        "research_hooks": evidence.get("keywords_matched") or [],
        "reason_for_priority": "",
    }


def production_prediction(record: dict[str, Any]) -> tuple[str, list[str], str]:
    raw_primary, raw_reasons = classify_track(_production_record(record))
    primary = PRODUCTION_TRACK_MAP.get(raw_primary, "irrelevant")
    return primary, [], f"{raw_primary}: {', '.join(raw_reasons)}".rstrip(": ")


def shadow_prediction(record: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    text = evidence_text(record)
    scored: list[tuple[int, str, list[str], list[str]]] = []
    all_exclusions: list[str] = []

    for track in TRACKS:
        rule = rules["tracks"][track]
        positives = sorted({term for term in rule["positive_terms"] if term in text})
        anchors = sorted({term for term in rule["anchor_terms"] if term in text})
        exclusions = sorted({term for term in rule["exclusion_terms"] if term in text})
        all_exclusions.extend(f"{track}:{term}" for term in exclusions)
        if positives and anchors:
            score = (2 * len(positives)) + len(anchors) - (2 * len(exclusions))
            if score > 0:
                scored.append((score, track, positives, anchors))

    scored.sort(key=lambda item: (-item[0], TRACKS.index(item[1])))
    if not scored:
        return {
            "primary": "irrelevant" if len(text.strip()) >= 20 else "ambiguous",
            "secondary": [],
            "confidence": 0.35 if len(text.strip()) >= 20 else 0.1,
            "positive_rules": [],
            "exclusion_rules": sorted(all_exclusions),
            "explanation": "No experimental rule had both a positive term and a lattice/PQC anchor.",
        }

    best_score, primary, positives, anchors = scored[0]
    secondary = [track for score, track, _, _ in scored[1:] if score >= max(2, best_score - 2)]
    confidence = min(0.95, 0.45 + (0.08 * len(positives)) + (0.05 * len(anchors)))
    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": round(confidence, 2),
        "positive_rules": [f"{primary}:{term}" for term in positives + anchors],
        "exclusion_rules": sorted(all_exclusions),
        "explanation": (
            f"Experimental match for {primary}; positive terms: {', '.join(positives)}; "
            f"anchors: {', '.join(anchors)}. This is not a production or human-gold label."
        ),
    }


def disagreement_category(
    production_primary: str,
    production_secondary: list[str],
    shadow_primary: str,
    shadow_secondary: list[str],
    record: dict[str, Any],
) -> str:
    if not str(record.get("title") or "").strip():
        return "insufficient_metadata"
    if production_primary == shadow_primary:
        return "exact_match" if set(production_secondary) == set(shadow_secondary) else "secondary_track_disagreement"
    if production_primary == "irrelevant" and shadow_primary not in {"irrelevant", "ambiguous"}:
        return "production_unlabeled_shadow_labeled"
    if production_primary not in {"irrelevant", "ambiguous"} and shadow_primary == "irrelevant":
        return "production_labeled_shadow_irrelevant"
    if "ambiguous" in {production_primary, shadow_primary}:
        return "ambiguous_disagreement"
    return "primary_track_disagreement"


def classify_sample(sample: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    if not rules.get("experimental_only") or rules.get("production_consumption_allowed") is not False:
        raise ValueError("Shadow rules must be explicitly experimental and forbidden to production consumers")

    rows: list[dict[str, Any]] = []
    for record in sample.get("records") or []:
        production_primary, production_secondary, production_detail = production_prediction(record)
        shadow = shadow_prediction(record, rules)
        category = disagreement_category(
            production_primary,
            production_secondary,
            shadow["primary"],
            shadow["secondary"],
            record,
        )
        rows.append(
            {
                "record_id": record.get("repository_record_id"),
                "sample_id": record.get("sample_id"),
                "title": record.get("title"),
                "source": record.get("source"),
                "production_primary_track": production_primary,
                "production_secondary_tracks": production_secondary,
                "production_detail": production_detail,
                "shadow_primary_track": shadow["primary"],
                "shadow_secondary_tracks": shadow["secondary"],
                "confidence": shadow["confidence"],
                "explanation": shadow["explanation"],
                "matched_positive_rules": shadow["positive_rules"],
                "matched_exclusion_rules": shadow["exclusion_rules"],
                "disagreement_category": category,
                "human_review_status": "queued_for_user",
                "TODO_VERIFY": [
                    "user review is required before any label counts as human gold",
                    "shadow output must not be consumed by Daily or Weekly production workflows",
                ],
            }
        )

    counts = Counter(row["disagreement_category"] for row in rows)
    return {
        "schema_version": 1,
        "experimental_only": True,
        "production_logic_changed": False,
        "record_count": len(rows),
        "human_gold_count": 0,
        "disagreement_counts": dict(sorted(counts.items())),
        "records": rows,
    }


def write_outputs(payload: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "v0.5_shadow_predictions.json"
    md_path = output_dir / "v0.5_shadow_predictions.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# v0.5 Shadow Track Predictions",
        "",
        "> Experimental only. These predictions do not change production classification or human gold labels.",
        "",
        f"- Records: {payload['record_count']}",
        f"- Human gold labels: {payload['human_gold_count']}",
        "",
        "## Disagreement Summary",
        "",
    ]
    for name, count in payload["disagreement_counts"].items():
        lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Records", ""])
    for row in payload["records"]:
        lines.extend(
            [
                f"### {row['sample_id']}: {row['title']}",
                "",
                f"- Production: `{row['production_primary_track']}`",
                f"- Shadow: `{row['shadow_primary_track']}`",
                f"- Disagreement: `{row['disagreement_category']}`",
                f"- Confidence: {row['confidence']}",
                f"- Explanation: {row['explanation']}",
                "- Human review: `queued_for_user`",
                "",
            ]
        )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return json_path, md_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the isolated v0.5 shadow track classifier.")
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = classify_sample(load_json(args.sample), load_json(args.rules))
    json_path, md_path = write_outputs(payload, args.output_dir)
    print(f"shadow records: {payload['record_count']}")
    print(f"human gold labels: {payload['human_gold_count']}")
    print(f"json: {json_path}")
    print(f"markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
