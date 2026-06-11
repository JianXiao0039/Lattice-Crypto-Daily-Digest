from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "audit_seven_day_source_reliability.py"


def load_audit_module() -> Any:
    spec = importlib.util.spec_from_file_location("seven_day_source_reliability", AUDIT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {AUDIT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {"records": payload}


def latest_file(directory: Path, pattern: str) -> Path | None:
    matches = sorted(directory.glob(pattern))
    return matches[-1] if matches else None


def weekly_metrics(project_root: Path) -> dict[str, Any]:
    weekly_path = latest_file(project_root / "data" / "weekly", "*.json")
    handoff_path = latest_file(project_root / "handoffs" / "weekly", "*-handoff-packets.json")
    weekly = load_json(weekly_path) if weekly_path else {}
    handoff = load_json(handoff_path) if handoff_path else {}
    coverage = weekly.get("coverage") or {}
    expected = int(coverage.get("expected_days") or 0)
    loaded = len(coverage.get("loaded_days") or [])
    traceable = bool(
        weekly_path
        and handoff_path
        and handoff.get("source_weekly_json")
        and Path(str(handoff["source_weekly_json"])).name == weekly_path.name
    )
    return {
        "weekly_json": weekly_path.relative_to(project_root).as_posix() if weekly_path else None,
        "handoff_json": handoff_path.relative_to(project_root).as_posix() if handoff_path else None,
        "weekly_coverage_completeness": round(loaded / expected, 4) if expected else None,
        "weekly_loaded_days": loaded,
        "weekly_expected_days": expected,
        "handoff_traceability": traceable,
        "handoff_packet_count": len(handoff.get("packets") or []),
    }


def classify_band(summary: dict[str, Any]) -> str:
    if int(summary.get("post_tag_run_count") or 0) == 0:
        return "insufficient_evidence"
    if int(summary.get("source_starved_run_count") or 0) > 0:
        return "source_starved_warning"
    if float(summary.get("source_reachability_rate") or 0.0) < 0.8:
        return "degraded_but_usable"
    return "healthy_observation"


def build_summary(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    audit_module = load_audit_module()
    audit = audit_module.build_audit(project_root)
    summary = dict(audit["summary"])
    weekly = weekly_metrics(project_root)
    band = classify_band(summary)
    return {
        "schema_version": 1,
        "policy_status": "provisional",
        "observation_period": {
            "dates": audit["observation_dates"],
            "tag_date": audit.get("tag_date"),
        },
        "evidence_type": "pre_tag_baseline" if summary.get("post_tag_run_count") == 0 else "post_tag_actual",
        "daily_artifact_completeness": summary["complete_artifact_rate"],
        "source_reachability": summary["source_reachability_rate"],
        "all_red_run_count": summary["all_red_run_count"],
        "source_starved_run_count": summary["source_starved_run_count"],
        "retryable_failure_count": summary["retryable_failure_count"],
        "non_retryable_failure_count": summary["non_retryable_failure_count"],
        "iacr_latest_usable_rate": summary["iacr_latest_success_rate"],
        "semantic_scholar_enrichment_usable_rate": summary["semantic_scholar_usable_run_rate"],
        "weekly_coverage_completeness": weekly["weekly_coverage_completeness"],
        "handoff_traceability": weekly["handoff_traceability"],
        "windows_ci_status": "TODO_VERIFY",
        "ubuntu_ci_status": "TODO_VERIFY",
        "confidence_level": "low" if summary.get("post_tag_run_count") == 0 else "provisional",
        "provisional_budget_band": band,
        "weekly": weekly,
        "TODO_VERIFY": [
            "collect multiple actual post-tag Daily runs",
            "collect at least one actual post-tag Weekly run",
            "record candidate-bearing Semantic Scholar behavior",
            "record current Windows and Ubuntu CI outside this local-only script",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    rows = [
        ("policy_status", payload["policy_status"]),
        ("evidence_type", payload["evidence_type"]),
        ("daily_artifact_completeness", f"{payload['daily_artifact_completeness']:.2%}"),
        ("source_reachability", f"{payload['source_reachability']:.2%}"),
        ("all_red_run_count", payload["all_red_run_count"]),
        ("source_starved_run_count", payload["source_starved_run_count"]),
        ("retryable_failure_count", payload["retryable_failure_count"]),
        ("non_retryable_failure_count", payload["non_retryable_failure_count"]),
        ("iacr_latest_usable_rate", f"{payload['iacr_latest_usable_rate']:.2%}"),
        (
            "semantic_scholar_enrichment_usable_rate",
            f"{payload['semantic_scholar_enrichment_usable_rate']:.2%}",
        ),
        (
            "weekly_coverage_completeness",
            f"{payload['weekly_coverage_completeness']:.2%}"
            if payload["weekly_coverage_completeness"] is not None
            else "unknown",
        ),
        ("handoff_traceability", payload["handoff_traceability"]),
        ("provisional_budget_band", payload["provisional_budget_band"]),
        ("confidence_level", payload["confidence_level"]),
    ]
    lines = [
        "# Provisional Source Failure Budget Summary",
        "",
        "> These values are observational and provisional. They are not production thresholds.",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines.extend(f"| `{key}` | `{value}` |" for key, value in rows)
    lines.extend(["", "## TODO_VERIFY"])
    lines.extend(f"- {item}" for item in payload["TODO_VERIFY"])
    return "\n".join(lines) + "\n"


def main() -> int:
    print(render_markdown(build_summary()), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
