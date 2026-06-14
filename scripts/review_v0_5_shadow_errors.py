from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREDICTIONS = PROJECT_ROOT / "docs/research_tracks/v0.5_shadow_pilot_predictions_v0.1.json"
DEFAULT_SAMPLE = PROJECT_ROOT / "docs/research_tracks/v0.5_manual_precision_sample_v0.2.json"
DEFAULT_RULES = PROJECT_ROOT / "experiments/v0_5_shadow_track_rules_v0.2.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs/research_tracks"

TRACKS = (
    "module_sis_sanitizable_signatures",
    "xingye_lu_bridge",
    "ai4lattice_cryptanalysis",
    "core_pqc_and_implementation",
)
CONTROL_LABELS = {"irrelevant", "ambiguous"}
CAUSE_PRIORITY = (
    "insufficient_metadata",
    "author_name_leakage",
    "ambiguous_paper",
    "production_label_limitation",
    "generic_keyword_false_positive",
    "shadow_overreach",
    "bad_rule",
    "bad_track_definition",
)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _evidence_parts(record: dict[str, Any]) -> tuple[str, str]:
    evidence = record.get("available_evidence") or {}
    primary = " ".join(
        str(value or "") for value in (record.get("title"), evidence.get("abstract"))
    ).lower()
    support = " ".join(
        str(value or "")
        for value in (
            " ".join(map(str, evidence.get("taxonomy_tags") or [])),
            " ".join(map(str, evidence.get("keywords_matched") or [])),
        )
    ).lower()
    return primary, support


def _matched_terms(row: dict[str, Any]) -> list[str]:
    terms = []
    for item in row.get("matched_positive_rules") or []:
        _, _, term = str(item).partition(":")
        if term:
            terms.append(term.lower())
    return terms


def _classify_causes(row: dict[str, Any], sample: dict[str, Any]) -> tuple[str, list[str], str]:
    production = row.get("production_primary_track")
    shadow = row.get("shadow_primary_track")
    codex = row.get("codex_reviewed_primary_track")
    category = row.get("disagreement_category")
    primary_text, support_text = _evidence_parts(sample)
    matched = _matched_terms(row)
    support_only_matches = sorted({term for term in matched if term in support_text and term not in primary_text})
    causes: set[str] = set()

    if row.get("metadata_insufficient"):
        causes.add("insufficient_metadata")
    if codex == "ambiguous":
        causes.add("ambiguous_paper")
    if category == "secondary_track_disagreement":
        causes.add("bad_track_definition")
    if shadow == codex and production != shadow:
        causes.add("production_label_limitation")
    if any(term in {"xingye lu", "author name only"} for term in matched):
        causes.add("author_name_leakage")
    if shadow == TRACKS[3] and codex != TRACKS[3] and support_only_matches:
        causes.add("generic_keyword_false_positive")
    if shadow not in CONTROL_LABELS and codex == "irrelevant":
        causes.add("shadow_overreach")
    if shadow != codex and codex != "ambiguous":
        causes.add("bad_rule")
    if not causes:
        causes.add("bad_track_definition")

    ordered = [cause for cause in CAUSE_PRIORITY if cause in causes]
    detail = (
        f"production={production}; shadow={shadow}; codex_reviewed={codex}; "
        f"support_only_matches={support_only_matches or 'none'}"
    )
    return ordered[0], ordered, detail


def review_errors(
    predictions: dict[str, Any], sample_payload: dict[str, Any], candidate_rules: dict[str, Any]
) -> dict[str, Any]:
    if candidate_rules.get("status") != "candidate_not_promoted":
        raise ValueError("Rule revision file must remain candidate_not_promoted")
    if not candidate_rules.get("experimental_only") or candidate_rules.get("production_consumption_allowed") is not False:
        raise ValueError("Rule revision file must be experimental and forbidden to production consumers")

    sample_by_id = {row["sample_id"]: row for row in sample_payload.get("records") or []}
    reviewed: list[dict[str, Any]] = []
    cause_counts: Counter[str] = Counter()
    contributing_counts: Counter[str] = Counter()
    track_stats: defaultdict[str, Counter[str]] = defaultdict(Counter)

    for row in predictions.get("records") or []:
        sample = sample_by_id.get(row["sample_id"], row)
        codex = row.get("codex_reviewed_primary_track")
        shadow = row.get("shadow_primary_track")
        production_disagreement = row.get("disagreement_category") != "exact_match"
        codex_disagreement = codex != shadow

        if codex in TRACKS:
            track_stats[codex]["codex_reviewed_total"] += 1
            if codex == shadow:
                track_stats[codex]["shadow_exact"] += 1
            else:
                track_stats[codex]["shadow_missed"] += 1
        if shadow in TRACKS:
            track_stats[shadow]["shadow_selected"] += 1

        if not (production_disagreement or codex_disagreement):
            continue
        primary_cause, contributing, detail = _classify_causes(row, sample)
        cause_counts[primary_cause] += 1
        contributing_counts.update(contributing)
        reviewed.append(
            {
                "sample_id": row["sample_id"],
                "record_id": row.get("record_id"),
                "title": row.get("title"),
                "production_primary_track": row.get("production_primary_track"),
                "shadow_primary_track": shadow,
                "codex_reviewed_primary_track": codex,
                "human_review_status": row.get("human_review_status"),
                "production_shadow_disagreement": production_disagreement,
                "codex_shadow_disagreement": codex_disagreement,
                "primary_cause": primary_cause,
                "contributing_causes": contributing,
                "diagnostic_detail": detail,
                "source_provenance": row.get("source_provenance") or [],
                "TODO_VERIFY": "User adjudication is required before this diagnostic cause is treated as a measured error.",
            }
        )

    human_gold_count = int(predictions.get("human_gold_count") or 0)
    return {
        "schema_version": 1,
        "review_type": "offline_non_production_diagnostic",
        "production_logic_changed": False,
        "candidate_rule_status": candidate_rules["status"],
        "pilot_record_count": int(predictions.get("broader_candidate_pool_count") or len(predictions.get("records") or [])),
        "human_gold_count": human_gold_count,
        "human_gold_metrics_eligible": human_gold_count > 0,
        "production_shadow_disagreement_count": int(predictions.get("production_shadow_disagreement_count") or 0),
        "codex_shadow_disagreement_count": sum(
            row.get("codex_reviewed_primary_track") != row.get("shadow_primary_track")
            for row in predictions.get("records") or []
        ),
        "reviewed_union_count": len(reviewed),
        "primary_cause_counts": dict(sorted(cause_counts.items())),
        "contributing_cause_counts": dict(sorted(contributing_counts.items())),
        "per_track": {track: dict(track_stats[track]) for track in TRACKS},
        "error_review_status": (
            "error_review_complete" if human_gold_count else "error_review_complete_without_gold_metrics"
        ),
        "shadow_mode_gate": "blocked_until_user_annotation",
        "production_gate": "blocked_by_multiple_conditions",
        "records": reviewed,
    }


def _write(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_outputs(payload: dict[str, Any], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "review": output_dir / "v0.5_shadow_error_review_v0.1.md",
        "priority": output_dir / "v0.5_shadow_error_priority_table_v0.1.md",
        "a": output_dir / "v0.5_shadow_track_a_error_review_v0.1.md",
        "b": output_dir / "v0.5_shadow_track_b_error_review_v0.1.md",
        "c": output_dir / "v0.5_shadow_track_c_error_review_v0.1.md",
        "d": output_dir / "v0.5_shadow_track_d_error_review_v0.1.md",
        "revision": output_dir / "v0.5_shadow_rule_revision_plan_v0.1.md",
        "reject": output_dir / "v0.5_shadow_rule_do_not_promote_list_v0.1.md",
        "backlog": output_dir / "v0.5_shadow_rule_candidate_backlog_v0.1.md",
    }

    review_lines = [
        "# v0.5 Shadow Error Review v0.1",
        "",
        f"- Status: `{payload['error_review_status']}`",
        f"- Pilot records: {payload['pilot_record_count']}",
        f"- Human-gold records: {payload['human_gold_count']}",
        f"- Production-shadow disagreements: {payload['production_shadow_disagreement_count']}",
        f"- Codex-review-shadow disagreements: {payload['codex_shadow_disagreement_count']}",
        f"- Reviewed union: {payload['reviewed_union_count']}",
        "",
        "> Causes are diagnostic hypotheses against production and Codex-reviewed labels. They are not human-gold error rates.",
        "",
        "## Primary Causes",
        "",
    ]
    review_lines.extend(f"- `{name}`: {count}" for name, count in payload["primary_cause_counts"].items())
    _write(paths["review"], review_lines)

    priority_rows = [
        ("P0", "Track B undercoverage", "All six Codex-reviewed Track B records are missed; add technical bridge anchors without author features."),
        ("P0", "Track D bucket drift", "Support metadata and broad scheme terms can dominate the central paper topic."),
        ("P1", "Track C undercoverage", "Attack/reduction centrality must outrank incidental scheme mentions."),
        ("P1", "Track A undercoverage", "Require explicit Module-SIS/chameleon/sanitizable anchors while retaining nearby primitives for review."),
        ("P2", "Ambiguous cases", "Keep queued for user adjudication; do not tune rules against unresolved labels."),
    ]
    priority_lines = ["# v0.5 Shadow Error Priority Table v0.1", "", "| Priority | Area | Action |", "|---|---|---|"]
    priority_lines.extend(f"| {priority} | {area} | {action} |" for priority, area, action in priority_rows)
    _write(paths["priority"], priority_lines)

    track_titles = {
        "a": (TRACKS[0], "Track A", "Generic signature, commitment, and ZK terms remain excluded unless a Module-SIS, chameleon-hash, sanitizable-signature, exposure, or lattice-trapdoor anchor is central."),
        "b": (TRACKS[1], "Track B", "Technical bridge evidence is required. Author names are never positive features; no author-name leakage was observed in the current pilot."),
        "c": (TRACKS[2], "Track C", "Generic AI/ML/CV is excluded. Cryptanalysis, LWE/RLWE/MLWE, reduction, BKZ, or attack evidence must be central."),
        "d": (TRACKS[3], "Track D", "Track D must not absorb attacks, advanced protocols, or generic PQC merely because support metadata mentions a scheme."),
    }
    for key, (track, title, finding) in track_titles.items():
        stats = payload["per_track"][track]
        _write(
            paths[key],
            [
                f"# v0.5 Shadow {title} Error Review v0.1",
                "",
                f"- Codex-reviewed total: {stats.get('codex_reviewed_total', 0)}",
                f"- Shadow exact against Codex review: {stats.get('shadow_exact', 0)}",
                f"- Shadow missed: {stats.get('shadow_missed', 0)}",
                f"- Shadow selected: {stats.get('shadow_selected', 0)}",
                "",
                finding,
                "",
                "TODO_VERIFY: user annotation is required before treating these counts as precision or recall.",
            ],
        )

    _write(
        paths["revision"],
        [
            "# v0.5 Shadow Rule Revision Plan v0.1",
            "",
            "1. Separate title/abstract primary evidence from taxonomy/keyword support evidence.",
            "2. Forbid support-only fields from creating a track assignment.",
            "3. Apply Track A/B/C central-topic precedence before Track D scheme/implementation matching.",
            "4. Keep author names and prior labels out of features.",
            "5. Evaluate v0.2 only on a held-out, user-adjudicated sample.",
            "6. Preserve v0.1 production and shadow outputs until the explicit promotion gate is satisfied.",
            "",
            "The machine-readable candidate is `experiments/v0_5_shadow_track_rules_v0.2.json`; it is not consumed automatically.",
        ],
    )
    _write(
        paths["reject"],
        [
            "# v0.5 Shadow Rule Do Not Promote List v0.1",
            "",
            "- Author-name matching for Track B.",
            "- Generic signature, commitment, privacy, ZK, AI, ML, CV, optimization, blockchain, or PQC terms without lattice/PQC technical anchors.",
            "- Taxonomy tags or matched keywords as sufficient evidence by themselves.",
            "- Track D as a fallback for every lattice or post-quantum paper.",
            "- Rules tuned against Codex-reviewed labels while presented as human-gold accuracy improvements.",
            "- Any automatic import from Daily, Weekly, ranking, handoff, or source-health workflows.",
        ],
    )
    _write(
        paths["backlog"],
        [
            "# v0.5 Shadow Rule Candidate Backlog v0.1",
            "",
            "- Build a user-adjudicated held-out set before quantitative tuning.",
            "- Test field-aware evidence weighting in an offline v0.2 runner.",
            "- Add central-topic precedence tests for attacks and advanced lattice protocols.",
            "- Add hard negatives for Falcon-as-model-name, isogeny-only PQC, generic FHE applications, and generic ML.",
            "- Review multi-track handling after human annotation exists.",
            "- Re-run Windows and Ubuntu CI after publication of the isolated tests.",
        ],
    )
    return list(paths.values())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review v0.5 shadow errors without changing production classification.")
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = review_errors(load_json(args.predictions), load_json(args.sample), load_json(args.rules))
    write_outputs(payload, args.output_dir)
    print(f"pilot records: {payload['pilot_record_count']}")
    print(f"human gold: {payload['human_gold_count']}")
    print(f"production-shadow disagreements: {payload['production_shadow_disagreement_count']}")
    print(f"reviewed union: {payload['reviewed_union_count']}")
    print(f"status: {payload['error_review_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
