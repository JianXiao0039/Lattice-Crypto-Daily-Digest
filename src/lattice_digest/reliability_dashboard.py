from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lattice_digest import __version__


SCHEMA_VERSION = 1
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_AUTOMATION_MODULES = ["Daily Public Digest Run", "Weekly Public Synthesis Run"]
PAUSED_AUTOMATION_MODULES = ["Full Manual Quality Run"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_file(directory: Path, pattern: str) -> Path | None:
    matches = sorted(directory.glob(pattern))
    return matches[-1] if matches else None


def _portable_relative_path(path: Path | None, project_root: Path) -> str | None:
    if path is None:
        return None
    return path.relative_to(project_root).as_posix()


def source_status(entry: dict[str, Any]) -> str:
    return str(entry.get("health_status") or entry.get("status") or "unknown")


def count_source_statuses(source_health: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"green": 0, "yellow": 0, "red": 0, "unknown": 0}
    for entry in source_health:
        status = source_status(entry)
        if status not in counts:
            counts["unknown"] += 1
            continue
        counts[status] += 1
    return counts


def count_high_priority(records: list[dict[str, Any]]) -> int:
    total = 0
    for record in records:
        if record.get("relevance_label") == "A":
            total += 1
            continue
        if record.get("reading_priority") == 1 or record.get("priority") == 1:
            total += 1
            continue
        label = str(record.get("priority_label") or "")
        if "精读" in label:
            total += 1
    return total


def corresponding_markdown_path(json_path: Path, project_root: Path) -> Path:
    return project_root / "digests" / f"{json_path.stem}.md"


def safe_semantic_scholar_key_state(env: dict[str, str] | None = None) -> dict[str, Any]:
    source = env if env is not None else os.environ
    value = (source.get("SEMANTIC_SCHOLAR_API_KEY") or "").strip()
    return {
        "present": bool(value),
        "length": len(value) if value else 0,
    }


def probe_for_source(probe_payload: dict[str, Any] | None, source_name: str) -> dict[str, Any] | None:
    if not probe_payload:
        return None
    for probe in probe_payload.get("probes") or []:
        if probe.get("source") == source_name:
            return probe
    return None


def daily_source_entry(daily_payload: dict[str, Any], source_name: str) -> dict[str, Any] | None:
    for entry in daily_payload.get("source_health") or []:
        if entry.get("source") == source_name:
            return entry
    return None


def classify_empty_digest_reason(
    records: list[dict[str, Any]],
    source_health: list[dict[str, Any]],
    probe_payload: dict[str, Any] | None,
) -> str:
    if records:
        return "non_empty"
    if not source_health:
        return "missing_source_health"
    status_counts = count_source_statuses(source_health)
    total = len(source_health)
    if total and status_counts["red"] == total:
        return "all_red_sources"
    probes = (probe_payload or {}).get("probes") or []
    if probes and all(not probe.get("reachable") for probe in probes):
        return "all_probes_unreachable"
    if status_counts["green"] == 0 and status_counts["yellow"] > 0:
        return "degraded_sources_no_records"
    return "no_records_without_full_source_failure"


def classify_source_starved(
    records: list[dict[str, Any]],
    source_health: list[dict[str, Any]],
    probe_payload: dict[str, Any] | None,
) -> bool:
    if records:
        return False
    if not source_health:
        return False
    return classify_empty_digest_reason(records, source_health, probe_payload) in {
        "all_red_sources",
        "all_probes_unreachable",
    }


def classify_semantic_scholar_enrichment_status(
    daily_payload: dict[str, Any],
    probe_payload: dict[str, Any] | None,
    env: dict[str, str] | None = None,
) -> str:
    key_state = safe_semantic_scholar_key_state(env)
    if not key_state["present"]:
        return "missing_key"

    probe = probe_for_source(probe_payload, "semantic_scholar")
    if probe:
        if probe.get("status_code") == 429 or probe.get("error_type") == "rate_limit":
            return "rate_limit"
        if probe.get("status_code") in {401, 403} or probe.get("failure_class") == "api_key_or_auth":
            return "auth_failure"
        if probe.get("reachable") is False:
            return "network_failure"

    records = daily_payload.get("records") or []
    for record in records:
        if record.get("semantic_scholar_metadata") or record.get("semantic_scholar_enrichment"):
            return "enrichment_successful"

    source_entry = daily_source_entry(daily_payload, "semantic_scholar") or {}
    if source_entry.get("api_key_used"):
        return "no_candidates_to_enrich"
    return "key_present"


def classify_weekly_handoff_source_starved(handoff_payload: dict[str, Any]) -> bool:
    packets = handoff_payload.get("packets") or []
    if packets:
        return False
    summary = handoff_payload.get("source_health_summary") or {}
    counts = summary.get("status_counts") or {}
    total = sum(int(counts.get(name, 0)) for name in ("green", "yellow", "red"))
    if total <= 0:
        return False
    return int(counts.get("green", 0)) == 0 and int(counts.get("red", 0)) > 0


def run_probe_script(project_root: Path, probe_script: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not probe_script.exists():
        return None, f"missing probe script: {probe_script}"
    result = subprocess.run(
        [sys.executable, str(probe_script)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        return None, result.stderr.strip() or result.stdout.strip() or f"probe exited with {result.returncode}"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"probe produced non-JSON output: {exc}"


def build_reliability_dashboard(
    *,
    project_root: Path = PROJECT_ROOT,
    probe_payload: dict[str, Any] | None = None,
    probe_error: str | None = None,
    run_id: str | None = None,
    run_type: str = "daily_reliability_dashboard",
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    data_dir = project_root / "data"
    weekly_dir = data_dir / "weekly"
    handoff_dir = project_root / "handoffs" / "weekly"

    daily_json = latest_file(data_dir, "*.json")
    weekly_json = latest_file(weekly_dir, "*.json")
    handoff_json = latest_file(handoff_dir, "*-handoff-packets.json")

    daily_payload = load_json(daily_json) if daily_json else {"records": [], "source_health": [], "metadata": {}}
    weekly_payload = load_json(weekly_json) if weekly_json else {}
    handoff_payload = load_json(handoff_json) if handoff_json else {"packets": [], "excluded": [], "todo_verify": []}

    records = list(daily_payload.get("records") or [])
    source_health = list(daily_payload.get("source_health") or [])
    status_counts = count_source_statuses(source_health)
    total_sources = len(source_health)

    probe_sources = (probe_payload or {}).get("probes") or []
    reachable_count = sum(1 for probe in probe_sources if probe.get("reachable"))
    probe_retryable = sum(1 for probe in probe_sources if probe.get("retryable"))
    probe_non_retryable = sum(
        1 for probe in probe_sources if probe.get("reachable") is False and not probe.get("retryable")
    )

    source_reachability_rate = None
    if probe_sources:
        source_reachability_rate = round(reachable_count / len(probe_sources), 3)

    metadata = daily_payload.get("metadata") or {}
    final_record_count = int(metadata.get("total_records") or len(records))
    high_priority_count = count_high_priority(records)
    empty_digest_reason = classify_empty_digest_reason(records, source_health, probe_payload)
    source_starved = classify_source_starved(records, source_health, probe_payload)

    iacr_entry = daily_source_entry(daily_payload, "iacr_eprint") or {}
    iacr_latest_status = iacr_entry.get("latest_feed_status") or "unknown"
    iacr_latest_records = int(iacr_entry.get("latest_feed_records") or 0)

    semantic_key_state = safe_semantic_scholar_key_state(env)
    semantic_status = classify_semantic_scholar_enrichment_status(daily_payload, probe_payload, env=env)

    packets = list(handoff_payload.get("packets") or [])
    excluded = list(handoff_payload.get("excluded") or [])
    todo_verify = list(handoff_payload.get("todo_verify") or [])
    weekly_handoff_source_starved = classify_weekly_handoff_source_starved(handoff_payload)

    daily_markdown_exists = False
    if daily_json:
        daily_markdown_exists = corresponding_markdown_path(daily_json, project_root).exists()

    generated_artifacts_present = bool(daily_json and daily_markdown_exists)
    validation_passed = bool(daily_json and handoff_json and (probe_error is None))
    manual_recovery_needed = bool(
        not generated_artifacts_present
        or source_starved
        or (not records and probe_retryable > 0)
        or empty_digest_reason in {"all_red_sources", "all_probes_unreachable", "degraded_sources_no_records"}
    )

    notes: list[str] = []
    todo_items: list[str] = []

    if probe_error:
        notes.append(probe_error)
        todo_items.append("probe output could not be parsed; rerun the connectivity probe manually")
    if status_counts["yellow"] > 0:
        notes.append(f"latest daily artifact is degraded: {status_counts['yellow']} yellow sources")
    if status_counts["red"] > 0:
        notes.append(f"latest daily artifact still contains {status_counts['red']} red sources")
    if weekly_payload:
        coverage = weekly_payload.get("coverage") or {}
        missing_days = coverage.get("missing_days") or []
        if missing_days:
            notes.append(f"weekly coverage missing days: {', '.join(missing_days)}")
    if not (project_root / "scripts" / "generate_weekly_handoff.py").exists():
        notes.append("scripts/generate_weekly_handoff.py is missing; use scripts/run_weekly_handoff.bat or python -m lattice_digest.weekly_handoff --latest")
    if semantic_status == "rate_limit":
        notes.append("Semantic Scholar probe is rate-limited; treat enrichment as advisory-only")
    if source_starved:
        todo_items.append("latest daily artifact is source-starved; run bounded manual recovery")
    if semantic_status in {"rate_limit", "network_failure", "auth_failure"}:
        todo_items.append("recheck Semantic Scholar enrichment status on the next manual run")
    if iacr_latest_status == "unknown":
        todo_items.append("verify IACR latest status from source health or probe output")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id or f"RDD-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "run_type": run_type,
        "run_time": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "package_version": __version__,
        "source_total_count": total_sources,
        "source_green_count": status_counts["green"],
        "source_yellow_count": status_counts["yellow"],
        "source_red_count": status_counts["red"],
        "source_reachability_rate": source_reachability_rate,
        "retryable_error_count": probe_retryable if probe_sources else sum(1 for entry in source_health if entry.get("retryable")),
        "non_retryable_error_count": probe_non_retryable,
        "digest_record_count": len(records),
        "final_record_count": final_record_count,
        "high_priority_count": high_priority_count,
        "iacr_latest_status": iacr_latest_status,
        "iacr_latest_records": iacr_latest_records,
        "semantic_scholar_key_present_boolean": semantic_key_state["present"],
        "semantic_scholar_key_length_only_if_safe": semantic_key_state["length"],
        "semantic_scholar_enrichment_status": semantic_status,
        "source_starved_true_false": source_starved,
        "empty_digest_reason": empty_digest_reason,
        "weekly_handoff_candidate_count": len(packets),
        "weekly_handoff_source_starved_true_false": weekly_handoff_source_starved,
        "generated_artifacts_present": generated_artifacts_present,
        "validation_passed": validation_passed,
        "manual_recovery_needed": manual_recovery_needed,
        "notes": notes,
        "TODO_VERIFY": todo_items,
        "artifacts": {
            "daily_json": _portable_relative_path(daily_json, project_root),
            "daily_markdown": _portable_relative_path(
                corresponding_markdown_path(daily_json, project_root),
                project_root,
            )
            if daily_json and daily_markdown_exists
            else None,
            "weekly_json": _portable_relative_path(weekly_json, project_root),
            "weekly_handoff_json": _portable_relative_path(handoff_json, project_root),
        },
        "probe_summary": {
            "probe_available": bool(probe_payload),
            "probe_error": probe_error,
            "reachable_count": reachable_count,
            "probe_total_count": len(probe_sources),
        },
        "weekly_handoff_summary": {
            "packets": len(packets),
            "excluded": len(excluded),
            "todo_verify": len(todo_verify),
        },
    }
    return payload


def render_markdown_dashboard(payload: dict[str, Any]) -> str:
    lines = [
        "# Daily Digest Reliability Dashboard",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- run_type: `{payload['run_type']}`",
        f"- run_time: `{payload['run_time']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    ordered_metrics = [
        "python_version",
        "package_version",
        "source_total_count",
        "source_green_count",
        "source_yellow_count",
        "source_red_count",
        "source_reachability_rate",
        "retryable_error_count",
        "non_retryable_error_count",
        "digest_record_count",
        "final_record_count",
        "high_priority_count",
        "iacr_latest_status",
        "iacr_latest_records",
        "semantic_scholar_key_present_boolean",
        "semantic_scholar_key_length_only_if_safe",
        "semantic_scholar_enrichment_status",
        "source_starved_true_false",
        "empty_digest_reason",
        "weekly_handoff_candidate_count",
        "weekly_handoff_source_starved_true_false",
        "generated_artifacts_present",
        "validation_passed",
        "manual_recovery_needed",
    ]
    for key in ordered_metrics:
        lines.append(f"| `{key}` | `{payload.get(key)}` |")

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- daily_json: `{payload['artifacts']['daily_json']}`",
            f"- daily_markdown: `{payload['artifacts']['daily_markdown']}`",
            f"- weekly_json: `{payload['artifacts']['weekly_json']}`",
            f"- weekly_handoff_json: `{payload['artifacts']['weekly_handoff_json']}`",
            "",
            "## Notes",
            "",
        ]
    )
    notes = payload.get("notes") or []
    if notes:
        lines.extend(f"- {note}" for note in notes)
    else:
        lines.append("- none")

    lines.extend(["", "## TODO_VERIFY", ""])
    todo_items = payload.get("TODO_VERIFY") or []
    if todo_items:
        lines.extend(f"- {item}" for item in todo_items)
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def build_reliability_baseline(
    *,
    project_root: Path = PROJECT_ROOT,
    probe_payload: dict[str, Any] | None = None,
    probe_error: str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    dashboard = build_reliability_dashboard(
        project_root=project_root,
        probe_payload=probe_payload,
        probe_error=probe_error,
        run_type="daily_reliability_baseline",
        env=env,
    )
    source_reachability_rate = dashboard["source_reachability_rate"]
    if source_reachability_rate is None:
        total = int(dashboard["source_total_count"] or 0)
        if total > 0:
            reachable_like = int(dashboard["source_green_count"] or 0) + int(dashboard["source_yellow_count"] or 0)
            source_reachability_rate = round(reachable_like / total, 3)

    retryable_error_count = dashboard["retryable_error_count"]
    if probe_payload is None:
        retryable_error_count = retryable_error_count or 0

    baseline = {
        "baseline_date": datetime.now(timezone.utc).date().isoformat(),
        "python_version": dashboard["python_version"],
        "package_version": dashboard["package_version"],
        "active_automation_modules": ACTIVE_AUTOMATION_MODULES,
        "paused_automation_modules": PAUSED_AUTOMATION_MODULES,
        "latest_daily_artifact": dashboard["artifacts"]["daily_json"],
        "latest_weekly_artifact": dashboard["artifacts"]["weekly_json"],
        "latest_handoff_artifact": dashboard["artifacts"]["weekly_handoff_json"],
        "source_total_count": dashboard["source_total_count"],
        "source_green_count": dashboard["source_green_count"],
        "source_yellow_count": dashboard["source_yellow_count"],
        "source_red_count": dashboard["source_red_count"],
        "source_reachability_rate": source_reachability_rate,
        "retryable_error_count": retryable_error_count,
        "digest_record_count": dashboard["digest_record_count"],
        "final_record_count": dashboard["final_record_count"],
        "high_priority_count": dashboard["high_priority_count"],
        "iacr_latest_status": dashboard["iacr_latest_status"],
        "iacr_latest_records": dashboard["iacr_latest_records"],
        "semantic_scholar_key_present_boolean": dashboard["semantic_scholar_key_present_boolean"],
        "semantic_scholar_key_length_only_if_safe": dashboard["semantic_scholar_key_length_only_if_safe"],
        "semantic_scholar_enrichment_status": dashboard["semantic_scholar_enrichment_status"],
        "source_starved_true_false": dashboard["source_starved_true_false"],
        "empty_digest_reason": dashboard["empty_digest_reason"],
        "weekly_handoff_candidate_count": dashboard["weekly_handoff_candidate_count"],
        "weekly_handoff_source_starved_true_false": dashboard["weekly_handoff_source_starved_true_false"],
        "validation_passed": dashboard["validation_passed"],
        "manual_recovery_needed": dashboard["manual_recovery_needed"],
        "TODO_VERIFY": dashboard["TODO_VERIFY"],
        "notes": dashboard["notes"] + (["baseline frozen from persisted artifacts without live probe"] if probe_payload is None else []),
    }
    return baseline


def render_markdown_baseline(payload: dict[str, Any]) -> str:
    lines = [
        "# Current Reliability Baseline",
        "",
        f"- baseline_date: `{payload['baseline_date']}`",
        "",
        "## Modules",
        "",
        f"- active: {', '.join(payload['active_automation_modules'])}",
        f"- paused: {', '.join(payload['paused_automation_modules'])}",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    ordered = [
        "python_version",
        "package_version",
        "latest_daily_artifact",
        "latest_weekly_artifact",
        "latest_handoff_artifact",
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
        "semantic_scholar_key_present_boolean",
        "semantic_scholar_key_length_only_if_safe",
        "semantic_scholar_enrichment_status",
        "source_starved_true_false",
        "empty_digest_reason",
        "weekly_handoff_candidate_count",
        "weekly_handoff_source_starved_true_false",
        "validation_passed",
        "manual_recovery_needed",
    ]
    for key in ordered:
        lines.append(f"| `{key}` | `{payload.get(key)}` |")
    lines.extend(["", "## Notes", ""])
    for note in payload.get("notes") or ["none"]:
        lines.append(f"- {note}")
    lines.extend(["", "## TODO_VERIFY", ""])
    for item in payload.get("TODO_VERIFY") or ["none"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a manual daily digest reliability dashboard.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--skip-probe", action="store_true", help="Do not run the connectivity probe script.")
    parser.add_argument(
        "--probe-script",
        type=Path,
        default=PROJECT_ROOT / "scripts" / "probe_source_connectivity.py",
        help="Path to the connectivity probe script.",
    )
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)

    probe_payload: dict[str, Any] | None = None
    probe_error: str | None = None
    if not args.skip_probe:
        probe_payload, probe_error = run_probe_script(args.project_root, args.probe_script)

    payload = build_reliability_dashboard(
        project_root=args.project_root,
        probe_payload=probe_payload,
        probe_error=probe_error,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_markdown_dashboard(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
