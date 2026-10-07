"""Exact historical windows; no calendar or wall-clock substitution."""
from __future__ import annotations

from datetime import date, datetime


def aware_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("coverage timestamps must have an explicit timezone offset")
    return parsed


def exact_window(start: str, end: str, target: str, *, run_mode: str,
                 since_hours: float | None = None) -> tuple[datetime, datetime]:
    if run_mode != "backfill":
        raise ValueError("exact coverage requires --run-mode backfill")
    if not target:
        raise ValueError("exact coverage requires explicit --target-date")
    date.fromisoformat(target)
    lower, upper = aware_timestamp(start), aware_timestamp(end)
    if lower >= upper:
        raise ValueError("coverage_start must precede coverage_end")
    if since_hours is not None and (upper - lower).total_seconds() != since_hours * 3600:
        raise ValueError("--since must equal the exact coverage duration")
    return lower, upper


def recovery_metadata(target: date, start: datetime, end: datetime, executed_at: datetime,
                      original_missing_reason: str | None) -> dict:
    return {"recovery_of_target_date": target.isoformat(),
            "recovery_requested_window": {"coverage_start": start.isoformat(), "coverage_end": end.isoformat()},
            "actual_recovery_run_time": executed_at.isoformat(),
            "recovery_executed_at": executed_at.isoformat(), "trigger_kind": "BACKFILL",
            "original_missing_reason": original_missing_reason or "UNKNOWN",
            "coverage_duration_seconds": (end - start).total_seconds()}


def validate_recovery_metadata(metadata: dict, target: date) -> None:
    requested = metadata.get("recovery_requested_window")
    if not isinstance(requested, dict):
        raise ValueError("missing exact recovery window")
    lower, upper = exact_window(requested["coverage_start"], requested["coverage_end"],
                               metadata["recovery_of_target_date"], run_mode=metadata["run_mode"])
    if (metadata.get("target_date") != target.isoformat()
            or metadata.get("recovery_of_target_date") != target.isoformat()
            or metadata.get("coverage_start") != lower.isoformat()
            or metadata.get("coverage_end") != upper.isoformat()
            or metadata.get("coverage_duration_seconds") != (upper - lower).total_seconds()
            or metadata.get("trigger_kind") not in {"BACKFILL", "RECOVERY"}):
        raise ValueError("exact recovery window/provenance mismatch")
