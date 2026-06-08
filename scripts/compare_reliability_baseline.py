from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lattice_digest.reliability_dashboard import build_reliability_dashboard, run_probe_script


DEFAULT_BASELINE_REPORT = PROJECT_ROOT / "docs" / "reports" / "phase-12n-reliability-baseline-freeze.md"
DEFAULT_PROBE_SCRIPT = PROJECT_ROOT / "scripts" / "probe_source_connectivity.py"

METRICS = [
    "source_total_count",
    "source_green_count",
    "source_yellow_count",
    "source_red_count",
    "source_reachability_rate",
    "retryable_error_count",
    "digest_record_count",
    "final_record_count",
    "high_priority_count",
    "iacr_latest_status",
    "iacr_latest_records",
    "semantic_scholar_enrichment_status",
    "source_starved_true_false",
    "empty_digest_reason",
    "weekly_handoff_candidate_count",
    "weekly_handoff_source_starved_true_false",
    "generated_artifacts_present",
    "validation_passed",
    "manual_recovery_needed",
]

HIGHER_BETTER = {
    "source_green_count",
    "source_reachability_rate",
    "iacr_latest_records",
}

LOWER_BETTER = {
    "source_yellow_count",
    "source_red_count",
    "retryable_error_count",
}

BOOL_TRUE_BETTER = {
    "generated_artifacts_present",
    "validation_passed",
}

BOOL_FALSE_BETTER = {
    "source_starved_true_false",
    "weekly_handoff_source_starved_true_false",
    "manual_recovery_needed",
}

STATUS_RANKS = {
    "iacr_latest_status": {
        "manual_retry_success": 4,
        "fetched": 3,
        "cache_hit": 3,
        "latest_feed_has_records": 3,
        "latest_feed_has_0_records": 2,
        "unknown": 1,
        "failed_attempt_guard": 1,
        "parser_failure": 0,
        "network_unreachable": 0,
        "failed/0": 0,
    },
    "semantic_scholar_enrichment_status": {
        "enrichment_successful": 5,
        "no_candidates_to_enrich": 4,
        "key_present": 3,
        "missing_key": 2,
        "rate_limit": 1,
        "network_failure": 1,
        "auth_failure": 0,
    },
    "empty_digest_reason": {
        "non_empty": 5,
        "no_records_without_full_source_failure": 3,
        "degraded_sources_no_records": 2,
        "missing_source_health": 1,
        "all_red_sources": 0,
        "all_probes_unreachable": 0,
    },
}


def load_frozen_baseline_from_text(text: str) -> dict[str, Any]:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if not match:
        raise ValueError("baseline report does not contain a fenced JSON block")
    return json.loads(match.group(1))


def load_frozen_baseline(path: Path) -> dict[str, Any]:
    return load_frozen_baseline_from_text(path.read_text(encoding="utf-8"))


def build_current_dashboard(project_root: Path, use_probe: bool) -> tuple[dict[str, Any], str | None]:
    probe_payload = None
    probe_error = None
    if use_probe:
        probe_payload, probe_error = run_probe_script(project_root, DEFAULT_PROBE_SCRIPT)
    payload = build_reliability_dashboard(
        project_root=project_root,
        probe_payload=probe_payload,
        probe_error=probe_error,
    )
    return payload, probe_error


def compare_metric(name: str, baseline_value: Any, current_value: Any) -> tuple[str, str]:
    if baseline_value is None:
        return "unknown_due_to_missing_artifacts", "frozen baseline missing this metric"
    if current_value is None:
        return "unknown_due_to_missing_artifacts", "current artifacts do not expose this metric"

    if name == "source_starved_true_false":
        if current_value and not baseline_value:
            return "source_starved", "current run is source-starved while frozen baseline was not"
        if current_value == baseline_value:
            return "unchanged", "source-starved state is unchanged"
        return "improved", "current run is no longer source-starved"

    if baseline_value == current_value:
        return "unchanged", "metric matches the frozen baseline"

    if name in STATUS_RANKS:
        ranks = STATUS_RANKS[name]
        baseline_rank = ranks.get(str(baseline_value), -1)
        current_rank = ranks.get(str(current_value), -1)
        if baseline_rank == -1 or current_rank == -1:
            return "TODO_VERIFY", "status value is outside the known comparison table"
        if current_rank > baseline_rank:
            return "improved", "current status is stronger than the frozen baseline"
        if current_rank < baseline_rank:
            return "degraded", "current status is weaker than the frozen baseline"
        return "TODO_VERIFY", "status ranks tie but raw values differ"

    if name in HIGHER_BETTER:
        return (
            ("improved", "higher is better for this metric")
            if current_value > baseline_value
            else ("degraded", "lower is worse for this metric")
        )

    if name in LOWER_BETTER:
        return (
            ("improved", "lower is better for this metric")
            if current_value < baseline_value
            else ("degraded", "higher is worse for this metric")
        )

    if name in BOOL_TRUE_BETTER:
        return (
            ("improved", "current run satisfies this boolean quality gate")
            if current_value
            else ("degraded", "current run no longer satisfies this boolean quality gate")
        )

    if name in BOOL_FALSE_BETTER:
        return (
            ("improved", "current run cleared this risk flag")
            if not current_value
            else ("degraded", "current run now raises this risk flag")
        )

    if isinstance(baseline_value, (int, float)) and isinstance(current_value, (int, float)):
        if baseline_value == 0 and current_value > 0:
            return "improved", "metric moved from zero to non-zero"
        if baseline_value > 0 and current_value == 0:
            return "degraded", "metric dropped from non-zero to zero"
        return "TODO_VERIFY", "numeric change may reflect paper volume rather than reliability"

    return "TODO_VERIFY", "manual interpretation required"


def build_diff_rows(baseline: dict[str, Any], current: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in METRICS:
        baseline_value = baseline.get(metric)
        current_value = current.get(metric)
        status, interpretation = compare_metric(metric, baseline_value, current_value)
        rows.append(
            {
                "metric": metric,
                "baseline": baseline_value,
                "current": current_value,
                "status": status,
                "interpretation": interpretation,
            }
        )
    return rows


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Baseline vs Current Reliability Diff",
        "",
        f"- baseline_report: `{payload['baseline_report']}`",
        f"- comparison_mode: `{payload['comparison_mode']}`",
        "",
        "| Metric | Baseline | Current | Status | Interpretation |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["diff_rows"]:
        lines.append(
            f"| `{row['metric']}` | `{row['baseline']}` | `{row['current']}` | `{row['status']}` | {row['interpretation']} |"
        )
    if payload.get("probe_error"):
        lines.extend(["", "## Probe Error", "", f"- {payload['probe_error']}"])
    if payload.get("notes"):
        lines.extend(["", "## Notes", ""])
        for note in payload["notes"]:
            lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare the frozen daily reliability baseline against current artifacts.")
    parser.add_argument("--baseline-report", type=Path, default=DEFAULT_BASELINE_REPORT)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--with-probe", action="store_true", help="Run the live connectivity probe for the current side.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)

    baseline = load_frozen_baseline(args.baseline_report)
    current, probe_error = build_current_dashboard(args.project_root, use_probe=args.with_probe)
    diff_rows = build_diff_rows(baseline, current)

    notes = []
    if not args.with_probe:
        notes.append("current side was derived from persisted artifacts only; live probe was skipped")
    if probe_error:
        notes.append(probe_error)

    payload = {
        "baseline_report": str(args.baseline_report.relative_to(args.project_root)),
        "comparison_mode": "with_probe" if args.with_probe else "artifact_only",
        "baseline_date": baseline.get("baseline_date"),
        "current_run_time": current.get("run_time"),
        "probe_error": probe_error,
        "diff_rows": diff_rows,
        "notes": notes,
    }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
