from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "docs/research_tracks/v0.5_shadow_pilot_predictions_v0.1.json"
DEFAULT_RULES = PROJECT_ROOT / "experiments/v0_5_shadow_track_rules_v0.2.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "audits/shadow/v0_5_controlled_pilot"
ALLOWED_REPOSITORY_OUTPUT_ROOTS = (
    PROJECT_ROOT / "audits/shadow",
    PROJECT_ROOT / "docs/research_tracks",
)
PROTECTED_REPOSITORY_ROOTS = (
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "digests",
    PROJECT_ROOT / "handoffs",
    PROJECT_ROOT / "src",
    PROJECT_ROOT / "lattice_digest",
)
TRACKS = (
    "module_sis_sanitizable_signatures",
    "xingye_lu_bridge",
    "ai4lattice_cryptanalysis",
    "core_pqc_and_implementation",
)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def validate_output_directory(output_dir: Path, project_root: Path = PROJECT_ROOT) -> Path:
    resolved = output_dir.resolve()
    root = project_root.resolve()
    protected = tuple(path.resolve() for path in PROTECTED_REPOSITORY_ROOTS)
    if any(_is_relative_to(resolved, path) for path in protected):
        raise ValueError("Shadow-mode output cannot be written to a production path")
    if _is_relative_to(resolved, root):
        allowed = tuple(path.resolve() for path in ALLOWED_REPOSITORY_OUTPUT_ROOTS)
        if not any(_is_relative_to(resolved, path) for path in allowed):
            raise ValueError("Repository shadow-mode output must be under audits/shadow or docs/research_tracks")
    return resolved


def _evidence_text(record: dict[str, Any]) -> tuple[str, str]:
    evidence = record.get("available_evidence") or {}
    primary = " ".join(
        str(value or "") for value in (record.get("title"), evidence.get("abstract"))
    ).lower()
    support = " ".join(
        (
            " ".join(map(str, evidence.get("taxonomy_tags") or [])),
            " ".join(map(str, evidence.get("keywords_matched") or [])),
        )
    ).lower()
    return primary, support


def shadow_prediction(record: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    if rules.get("schema_version") != 2:
        raise ValueError("Controlled shadow mode requires the v0.2 experimental rule schema")
    if rules.get("status") != "candidate_not_promoted":
        raise ValueError("Controlled shadow rules must remain candidate_not_promoted")
    if not rules.get("experimental_only") or rules.get("production_consumption_allowed") is not False:
        raise ValueError("Controlled shadow rules must forbid production consumption")

    primary_text, support_text = _evidence_text(record)
    combined = f"{primary_text} {support_text}"
    precedence = rules.get("track_precedence") or list(TRACKS)
    scored: list[tuple[int, int, str, list[str], list[str], list[str]]] = []

    for track in TRACKS:
        rule = rules["tracks"][track]
        required = sorted({term for term in rule.get("required_primary_terms") or [] if term in primary_text})
        support = sorted({term for term in rule.get("support_terms") or [] if term in support_text})
        exclusions = sorted({term for term in rule.get("exclusion_terms") or [] if term in combined})
        deprioritized = sorted(
            {term for term in rule.get("deprioritize_when_primary_contains") or [] if term in primary_text}
        )
        if not required:
            continue
        score = (4 * len(required)) + len(support) - (3 * len(exclusions)) - (2 * len(deprioritized))
        if score > 0:
            scored.append((score, precedence.index(track), track, required, support, exclusions + deprioritized))

    scored.sort(key=lambda item: (-item[0], item[1]))
    if not scored:
        return {
            "primary": "irrelevant" if len(primary_text.strip()) >= 20 else "ambiguous",
            "secondary": [],
            "confidence": 0.35 if len(primary_text.strip()) >= 20 else 0.1,
            "matched_primary_rules": [],
            "matched_support_rules": [],
            "matched_exclusion_rules": [],
            "explanation": "No v0.2 rule had a required title/abstract match.",
        }

    best_score, _, primary, required, support, excluded = scored[0]
    secondary = [track for score, _, track, _, _, _ in scored[1:] if score >= max(4, best_score - 3)]
    confidence = min(0.95, 0.5 + (0.08 * len(required)) + (0.03 * len(support)))
    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": round(confidence, 2),
        "matched_primary_rules": [f"{primary}:{term}" for term in required],
        "matched_support_rules": [f"{primary}:{term}" for term in support],
        "matched_exclusion_rules": [f"{primary}:{term}" for term in excluded],
        "explanation": (
            f"Experimental v0.2 match for {primary} from title/abstract evidence: "
            f"{', '.join(required)}. Support-only evidence cannot create a track."
        ),
    }


def disagreement_category(production: str, shadow: str) -> str:
    if production == shadow:
        return "exact_match"
    if production == "irrelevant" and shadow not in {"irrelevant", "ambiguous"}:
        return "production_unlabeled_shadow_labeled"
    if production not in {"irrelevant", "ambiguous"} and shadow == "irrelevant":
        return "production_labeled_shadow_irrelevant"
    if "ambiguous" in {production, shadow}:
        return "ambiguous_disagreement"
    return "primary_track_disagreement"


def build_controlled_pilot(
    snapshot: dict[str, Any],
    rules: dict[str, Any],
    *,
    run_id: str,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for source in snapshot.get("records") or []:
        shadow = shadow_prediction(source, rules)
        production = str(source.get("production_primary_track") or "irrelevant")
        category = disagreement_category(production, shadow["primary"])
        records.append(
            {
                "record_id": source.get("record_id"),
                "sample_id": source.get("sample_id"),
                "title": source.get("title"),
                "source": source.get("source"),
                "production_primary_track": production,
                "shadow_primary_track": shadow["primary"],
                "shadow_secondary_tracks": shadow["secondary"],
                "confidence": shadow["confidence"],
                "explanation": shadow["explanation"],
                "matched_primary_rules": shadow["matched_primary_rules"],
                "matched_support_rules": shadow["matched_support_rules"],
                "matched_exclusion_rules": shadow["matched_exclusion_rules"],
                "disagreement_category": category,
                "human_review_status": source.get("human_review_status") or "not_reviewed",
                "valid_human_gold": bool(source.get("valid_human_gold")),
                "source_provenance": source.get("source_provenance") or [],
                "TODO_VERIFY": "User adjudication is required before this prediction contributes to gold metrics.",
            }
        )

    counts = Counter(row["disagreement_category"] for row in records)
    gold_count = sum(row["valid_human_gold"] for row in records)
    return {
        "schema_version": 1,
        "run_id": run_id,
        "run_mode": "manual_only",
        "pilot_type": "controlled_shadow_non_production",
        "experimental_rule_version": "v0.2",
        "production_logic_changed": False,
        "production_outputs_written": False,
        "record_count": len(records),
        "human_gold_count": gold_count,
        "human_gold_metrics_eligible": gold_count > 0,
        "agreement_count": counts.get("exact_match", 0),
        "disagreement_count": len(records) - counts.get("exact_match", 0),
        "disagreement_counts": dict(sorted(counts.items())),
        "status": (
            "controlled_pilot_complete" if gold_count else "controlled_pilot_complete_without_gold_metrics"
        ),
        "records": records,
    }


def write_outputs(
    payload: dict[str, Any],
    output_dir: Path,
    *,
    snapshot_path: Path,
    rules_path: Path,
    project_root: Path = PROJECT_ROOT,
) -> list[Path]:
    target = validate_output_directory(output_dir, project_root)
    target.mkdir(parents=True, exist_ok=True)
    paths = {
        "manifest": target / "manifest.json",
        "predictions": target / "predictions.json",
        "disagreements": target / "disagreements.json",
        "summary": target / "summary.md",
    }
    disagreements = [row for row in payload["records"] if row["disagreement_category"] != "exact_match"]
    manifest = {
        key: value for key, value in payload.items() if key != "records"
    }
    manifest.update(
        {
            "run_time_utc": datetime.now(timezone.utc).isoformat(),
            "input_snapshot": snapshot_path.resolve().relative_to(project_root.resolve()).as_posix(),
            "experimental_rules": rules_path.resolve().relative_to(project_root.resolve()).as_posix(),
            "output_directory": target.relative_to(project_root.resolve()).as_posix()
            if _is_relative_to(target, project_root.resolve())
            else str(target),
            "generated_files": [path.name for path in paths.values()],
        }
    )
    paths["manifest"].write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["predictions"].write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["disagreements"].write_text(
        json.dumps({"schema_version": 1, "records": disagreements}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# v0.5 Controlled Shadow-Mode Pilot",
        "",
        "> Manual-only, experimental, and non-production. No human-gold accuracy claim is made.",
        "",
        f"- Run ID: `{payload['run_id']}`",
        f"- Status: `{payload['status']}`",
        f"- Records: {payload['record_count']}",
        f"- Human-gold records: {payload['human_gold_count']}",
        f"- Production-shadow agreements: {payload['agreement_count']}",
        f"- Production-shadow disagreements: {payload['disagreement_count']}",
        "- Production outputs written: no",
        "",
        "## Disagreement Summary",
        "",
    ]
    lines.extend(f"- `{name}`: {count}" for name, count in payload["disagreement_counts"].items())
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "The pilot is suitable only for continued manual shadow review. Production promotion remains blocked.",
        ]
    )
    paths["summary"].write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return list(paths.values())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the manual-only v0.5 controlled shadow-mode pilot.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--run-id", default="phase-13f-manual")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = build_controlled_pilot(load_json(args.input), load_json(args.rules), run_id=args.run_id)
    paths = write_outputs(
        payload,
        args.output_dir,
        snapshot_path=args.input,
        rules_path=args.rules,
    )
    print(f"shadow-mode records: {payload['record_count']}")
    print(f"agreements: {payload['agreement_count']}")
    print(f"disagreements: {payload['disagreement_count']}")
    print(f"human gold: {payload['human_gold_count']}")
    print(f"status: {payload['status']}")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
