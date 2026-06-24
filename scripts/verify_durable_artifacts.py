from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lattice_digest.artifact_paths import (
    daily_data_path,
    daily_digest_path,
    legacy_daily_data_candidates,
    legacy_daily_digest_candidates,
    legacy_monthly_data_candidates,
    legacy_monthly_digest_candidates,
    legacy_weekly_data_candidates,
    legacy_weekly_digest_candidates,
    monthly_data_path,
    monthly_digest_path,
    resolve_existing,
    weekly_data_path,
    weekly_digest_path,
)


def _portable(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc.msg}"
    if isinstance(payload, dict):
        return payload, None
    if isinstance(payload, list):
        return {"records": payload, "metadata": {}, "source_health": []}, None
    return None, "json_root_not_object_or_list"


def _records(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    records = payload.get("records")
    return [record for record in records if isinstance(record, dict)] if isinstance(records, list) else []


def _source_health(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    health = payload.get("source_health")
    if not isinstance(health, list):
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        health = metadata.get("source_health")
    return [item for item in health if isinstance(item, dict)] if isinstance(health, list) else []


def _status(item: dict[str, Any]) -> str:
    value = str(item.get("health_status") or item.get("status") or "").lower()
    if value in {"green", "yellow", "red"}:
        return value
    if item.get("errors") or item.get("error_type") or item.get("failure_class"):
        return "red"
    if item.get("warnings"):
        return "yellow"
    return "unknown"


def _is_source_starved(payload: dict[str, Any] | None) -> bool:
    records = _records(payload)
    health = _source_health(payload)
    if records or not health:
        return False
    statuses = [_status(item) for item in health]
    return bool(statuses) and all(status == "red" for status in statuses)


def _markdown_info(path: Path, expected_heading: str) -> dict[str, Any]:
    info = {
        "path": path.as_posix(),
        "exists": path.exists(),
        "non_empty": False,
        "required_heading_present": False,
        "source_health_visible": False,
        "source_starved_visible": False,
    }
    if not path.exists():
        return info
    text = path.read_text(encoding="utf-8", errors="replace")
    info["non_empty"] = bool(text.strip())
    info["required_heading_present"] = expected_heading in text or text.lstrip().startswith("#")
    lower = text.lower()
    info["source_health_visible"] = "source health" in lower or "source-health" in lower or "数据源健康" in text
    info["source_starved_visible"] = "source-starved" in lower or "source_starved" in lower or "source-starved" in text
    return info


def _status_from_checks(checks: list[bool]) -> str:
    return "verified" if all(checks) else "incomplete"


def verify_daily(root: Path, target_date: str) -> dict[str, Any]:
    json_path, json_legacy = resolve_existing(
        daily_data_path(target_date, root / "data"),
        legacy_daily_data_candidates(target_date, root / "data"),
    )
    markdown_path, markdown_legacy = resolve_existing(
        daily_digest_path(target_date, root / "digests"),
        legacy_daily_digest_candidates(target_date, root / "digests"),
    )
    audit_json_path = root / "audits" / "source-health" / f"{target_date}.json"
    payload, json_error = _read_json(json_path)
    markdown = _markdown_info(markdown_path, target_date)
    health = _source_health(payload)
    source_starved = _is_source_starved(payload)
    explicit_source_starved = not source_starved or markdown["source_starved_visible"] or bool(
        payload and payload.get("source_starved")
    )
    result = {
        "kind": "daily",
        "target": target_date,
        "markdown_path": _portable(markdown_path, root),
        "json_path": _portable(json_path, root),
        "source_health_audit_path": _portable(audit_json_path, root),
        "markdown_exists": markdown_path.exists(),
        "json_exists": json_path.exists(),
        "json_parseable": json_error is None,
        "json_error": json_error,
        "legacy_fallback_used": json_legacy or markdown_legacy,
        "markdown_required_heading_present": markdown["required_heading_present"],
        "markdown_non_empty": markdown["non_empty"],
        "record_count": len(_records(payload)),
        "source_health_present": bool(health),
        "source_health_audit_exists": audit_json_path.exists(),
        "source_starved": source_starved,
        "source_starved_explicit": explicit_source_starved,
        "generated_or_target_date_present": _target_date_present(payload, target_date),
        "TODO_VERIFY": [],
    }
    if not result["source_health_present"]:
        result["TODO_VERIFY"].append("source health missing")
    if source_starved and not explicit_source_starved:
        result["TODO_VERIFY"].append("source-starved condition is not explicit")
    result["status"] = _status_from_checks(
        [
            result["markdown_exists"],
            result["json_exists"],
            result["json_parseable"],
            result["markdown_non_empty"],
            result["markdown_required_heading_present"],
            result["source_health_present"],
            result["generated_or_target_date_present"],
            result["source_starved_explicit"],
        ]
    )
    return result


def _target_date_present(payload: dict[str, Any] | None, target_date: str) -> bool:
    if not payload:
        return False
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    candidates = [
        payload.get("date"),
        payload.get("target_date"),
        metadata.get("date"),
        metadata.get("target_date"),
        metadata.get("generated_at"),
        payload.get("generated_at"),
    ]
    return any(target_date in str(value) for value in candidates if value)


def verify_weekly(root: Path, week: str) -> dict[str, Any]:
    json_path, json_legacy = resolve_existing(
        weekly_data_path(week, root=root / "data"),
        legacy_weekly_data_candidates(week, root=root / "data"),
    )
    markdown_path, markdown_legacy = resolve_existing(
        weekly_digest_path(week, root=root / "digests"),
        legacy_weekly_digest_candidates(week, root=root / "digests"),
    )
    payload, json_error = _read_json(json_path)
    markdown = _markdown_info(markdown_path, week)
    result = {
        "kind": "weekly",
        "target": week,
        "markdown_path": _portable(markdown_path, root),
        "json_path": _portable(json_path, root),
        "markdown_exists": markdown_path.exists(),
        "json_exists": json_path.exists(),
        "json_parseable": json_error is None,
        "json_error": json_error,
        "legacy_fallback_used": json_legacy or markdown_legacy,
        "markdown_required_heading_present": markdown["required_heading_present"],
        "markdown_non_empty": markdown["non_empty"],
        "source_health_summary_present": bool(payload and payload.get("source_health_summary")),
        "input_dates_or_coverage_present": bool(payload and (payload.get("coverage") or payload.get("input_dates"))),
        "generated_or_target_period_present": bool(payload and (week in str(payload) or payload.get("generated_at"))),
        "TODO_VERIFY": [],
    }
    if not result["source_health_summary_present"]:
        result["TODO_VERIFY"].append("weekly source health summary missing")
    if not result["input_dates_or_coverage_present"]:
        result["TODO_VERIFY"].append("weekly input coverage missing")
    result["status"] = _status_from_checks(
        [
            result["markdown_exists"],
            result["json_exists"],
            result["json_parseable"],
            result["markdown_non_empty"],
            result["markdown_required_heading_present"],
            result["source_health_summary_present"],
            result["input_dates_or_coverage_present"],
        ]
    )
    return result


def verify_monthly(root: Path, month: str) -> dict[str, Any]:
    json_path, json_legacy = resolve_existing(
        monthly_data_path(month, root=root / "data"),
        legacy_monthly_data_candidates(month, root=root / "data"),
    )
    markdown_path, markdown_legacy = resolve_existing(
        monthly_digest_path(month, root=root / "digests"),
        legacy_monthly_digest_candidates(month, root=root / "digests"),
    )
    payload, json_error = _read_json(json_path)
    markdown = _markdown_info(markdown_path, month)
    result = {
        "kind": "monthly",
        "target": month,
        "markdown_path": _portable(markdown_path, root),
        "json_path": _portable(json_path, root),
        "markdown_exists": markdown_path.exists(),
        "json_exists": json_path.exists(),
        "json_parseable": json_error is None,
        "json_error": json_error,
        "legacy_fallback_used": json_legacy or markdown_legacy,
        "markdown_required_heading_present": markdown["required_heading_present"],
        "markdown_non_empty": markdown["non_empty"],
        "source_health_summary_present": bool(payload and payload.get("source_health_summary")),
        "input_daily_files_present": bool(payload and isinstance(payload.get("input_daily_files"), list)),
        "missing_days_present": bool(payload and isinstance(payload.get("missing_days"), list)),
        "generated_or_target_period_present": bool(payload and payload.get("month") == month),
        "source_starved_explicit": bool(
            payload
            and isinstance(payload.get("source_health_summary"), dict)
            and "source_starved" in payload["source_health_summary"]
        ),
        "TODO_VERIFY": [],
    }
    for key, message in (
        ("source_health_summary_present", "monthly source health summary missing"),
        ("input_daily_files_present", "monthly input daily files missing"),
        ("missing_days_present", "monthly missing-days list missing"),
        ("source_starved_explicit", "monthly source-starved status missing"),
    ):
        if not result[key]:
            result["TODO_VERIFY"].append(message)
    result["status"] = _status_from_checks(
        [
            result["markdown_exists"],
            result["json_exists"],
            result["json_parseable"],
            result["markdown_non_empty"],
            result["markdown_required_heading_present"],
            result["source_health_summary_present"],
            result["input_daily_files_present"],
            result["missing_days_present"],
            result["generated_or_target_period_present"],
            result["source_starved_explicit"],
        ]
    )
    return result


def verify_artifacts(root: Path, *, target_date: str | None, week: str | None, month: str | None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    if target_date:
        checks.append(verify_daily(root, target_date))
    if week:
        checks.append(verify_weekly(root, week))
    if month:
        checks.append(verify_monthly(root, month))
    complete = all(check["status"] == "verified" for check in checks) if checks else False
    return {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_root": root.as_posix(),
        "overall_status": "verified" if complete else "partial_or_missing",
        "checks": checks,
        "TODO_VERIFY": [item for check in checks for item in check.get("TODO_VERIFY", [])],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify durable Daily/Weekly/Monthly radar artifacts.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--date", dest="target_date")
    parser.add_argument("--week")
    parser.add_argument("--month")
    args = parser.parse_args(argv)
    report = verify_artifacts(args.root, target_date=args.target_date, week=args.week, month=args.month)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
