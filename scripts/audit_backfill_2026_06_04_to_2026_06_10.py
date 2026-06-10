from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATES = [
    "2026-06-04",
    "2026-06-05",
    "2026-06-06",
    "2026-06-07",
    "2026-06-08",
    "2026-06-09",
    "2026-06-10",
]


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {"records": payload}


def source_status(entry: dict[str, Any]) -> str:
    return str(entry.get("health_status") or entry.get("status") or "unknown")


def source_counts(source_health: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"green": 0, "yellow": 0, "red": 0, "unknown": 0}
    for entry in source_health:
        status = source_status(entry)
        counts[status if status in counts else "unknown"] += 1
    return counts


def high_priority_count(records: list[dict[str, Any]]) -> int:
    total = 0
    for record in records:
        if record.get("relevance_label") == "A":
            total += 1
            continue
        if record.get("reading_priority") == 1 or record.get("priority") == 1:
            total += 1
            continue
        if "精读" in str(record.get("priority_label") or ""):
            total += 1
    return total


def find_source(source_health: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for entry in source_health:
        if entry.get("source") == name:
            return entry
    return {}


def semantic_status(source_health: list[dict[str, Any]]) -> str:
    entry = find_source(source_health, "semantic_scholar")
    if not entry:
        return "missing"
    status = source_status(entry)
    if status == "red":
        return "source_red"
    if entry.get("api_key_used"):
        return "key_used"
    return status


def git_log_for_path(project_root: Path, relative_path: str) -> list[str]:
    result = subprocess.run(
        ["git", "log", "--oneline", "--", relative_path],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def audit_date(project_root: Path, date: str) -> dict[str, Any]:
    json_path = project_root / "data" / f"{date}.json"
    md_path = project_root / "digests" / f"{date}.md"
    payload = load_json(json_path)
    records = list((payload or {}).get("records") or [])
    metadata = (payload or {}).get("metadata") or {}
    source_health = list((payload or {}).get("source_health") or metadata.get("source_health") or [])
    counts = source_counts(source_health)
    iacr = find_source(source_health, "iacr_eprint")
    source_starved = bool(not records and source_health and counts["red"] == len(source_health))
    todo_verify: list[str] = []
    if not json_path.exists():
        todo_verify.append("data JSON missing")
    if not md_path.exists():
        todo_verify.append("digest Markdown missing")
    if not source_health and json_path.exists():
        todo_verify.append("source health missing")
    if source_starved:
        todo_verify.append("source-starved run; do not interpret as no relevant papers")

    digest_commits = git_log_for_path(project_root, f"digests/{date}.md") if md_path.exists() else []
    data_commits = git_log_for_path(project_root, f"data/{date}.json") if json_path.exists() else []
    commit_status = "tracked_or_committed" if digest_commits or data_commits else "untracked_or_not_committed"
    if not json_path.exists() and not md_path.exists():
        commit_status = "missing"

    return {
        "date": date,
        "digest_markdown_exists": md_path.exists(),
        "data_json_exists": json_path.exists(),
        "digest_record_count": len(records) if payload is not None else None,
        "final_record_count": int(metadata.get("total_records") or len(records)) if payload is not None else None,
        "high_priority_count": high_priority_count(records) if payload is not None else None,
        "source_health_visible": bool(source_health),
        "source_green_count": counts["green"],
        "source_yellow_count": counts["yellow"],
        "source_red_count": counts["red"],
        "source_starved": source_starved,
        "iacr_latest_status": iacr.get("latest_feed_status") or "missing",
        "iacr_latest_records": int(iacr.get("latest_feed_records") or 0),
        "semantic_scholar_status": semantic_status(source_health),
        "commit_status": commit_status,
        "latest_digest_commit": digest_commits[0] if digest_commits else None,
        "latest_data_commit": data_commits[0] if data_commits else None,
        "TODO_VERIFY": todo_verify,
    }


def summarize_decision(rows: list[dict[str, Any]]) -> dict[str, Any]:
    existing = [row for row in rows if row["data_json_exists"] and row["digest_markdown_exists"]]
    missing = [row["date"] for row in rows if not (row["data_json_exists"] and row["digest_markdown_exists"])]
    source_starved = [row["date"] for row in rows if row["source_starved"]]
    latest = rows[-1]

    if missing:
        daily_decision = "insufficient_evidence"
    elif source_starved and latest["source_starved"]:
        daily_decision = "source_starved"
    elif source_starved:
        daily_decision = "mostly_stable"
    elif all(row["source_red_count"] == 0 for row in rows):
        daily_decision = "stable"
    else:
        daily_decision = "unstable"

    weekly_decision = "keep_active_with_source_starved_warning" if source_starved or missing else "keep_active"
    full_decision = "keep_paused" if latest["data_json_exists"] and not latest["source_starved"] else "run_once_manually_for_validation"

    return {
        "window_complete": not missing,
        "existing_artifact_days": [row["date"] for row in existing],
        "missing_artifact_days": missing,
        "source_starved_days": source_starved,
        "daily_decision": daily_decision,
        "weekly_decision": weekly_decision,
        "full_manual_quality_run_decision": full_decision,
    }


def build_audit(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    rows = [audit_date(project_root, date) for date in DATES]
    return {
        "schema_version": 1,
        "window": "2026-06-04..2026-06-10",
        "rows": rows,
        "decision": summarize_decision(rows),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Backfill Audit 2026-06-04 to 2026-06-10",
        "",
        f"- window_complete: `{payload['decision']['window_complete']}`",
        f"- daily_decision: `{payload['decision']['daily_decision']}`",
        f"- weekly_decision: `{payload['decision']['weekly_decision']}`",
        f"- full_manual_quality_run_decision: `{payload['decision']['full_manual_quality_run_decision']}`",
        "",
        "| date | digest MD | data JSON | records | final | high | source health | green/yellow/red | source-starved | IACR latest | Semantic Scholar | commit status | TODO_VERIFY |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {date} | {md} | {json} | {records} | {final} | {high} | {health} | {g}/{y}/{r} | {starved} | {iacr}/{iacr_records} | {semantic} | {commit} | {todo} |".format(
                date=row["date"],
                md="yes" if row["digest_markdown_exists"] else "no",
                json="yes" if row["data_json_exists"] else "no",
                records=row["digest_record_count"] if row["digest_record_count"] is not None else "n/a",
                final=row["final_record_count"] if row["final_record_count"] is not None else "n/a",
                high=row["high_priority_count"] if row["high_priority_count"] is not None else "n/a",
                health="yes" if row["source_health_visible"] else "no",
                g=row["source_green_count"],
                y=row["source_yellow_count"],
                r=row["source_red_count"],
                starved=str(row["source_starved"]).lower(),
                iacr=row["iacr_latest_status"],
                iacr_records=row["iacr_latest_records"],
                semantic=row["semantic_scholar_status"],
                commit=row["commit_status"],
                todo=", ".join(row["TODO_VERIFY"]) or "none",
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    payload = build_audit()
    print(render_markdown(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
