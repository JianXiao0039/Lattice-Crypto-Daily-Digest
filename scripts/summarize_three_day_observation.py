from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAMES = [
    "arxiv",
    "crossref",
    "dblp",
    "iacr_eprint",
    "openalex",
    "semantic_scholar",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def daily_json_files(project_root: Path) -> list[Path]:
    return sorted((project_root / "data").glob("????-??-??.json"))


def status_counts(source_health: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"green": 0, "yellow": 0, "red": 0, "unknown": 0}
    for entry in source_health:
        status = str(entry.get("health_status") or entry.get("status") or "unknown")
        if status not in counts:
            status = "unknown"
        counts[status] += 1
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


def is_source_starved(records: list[dict[str, Any]], source_health: list[dict[str, Any]]) -> bool:
    if records or not source_health:
        return False
    counts = status_counts(source_health)
    return counts["red"] == len(source_health)


def source_entry(source_health: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for entry in source_health:
        if entry.get("source") == name:
            return entry
    return {}


def summarize_daily(path: Path, project_root: Path) -> dict[str, Any]:
    payload = load_json(path)
    records = list(payload.get("records") or [])
    metadata = payload.get("metadata") or {}
    source_health = list(payload.get("source_health") or metadata.get("source_health") or [])
    counts = status_counts(source_health)
    iacr = source_entry(source_health, "iacr_eprint")
    semantic = source_entry(source_health, "semantic_scholar")
    date = path.stem
    markdown_path = project_root / "digests" / f"{date}.md"

    retryable_errors = sum(1 for entry in source_health if entry.get("retryable"))
    semantic_status = "available_no_enrichment"
    if semantic.get("status") == "red" or semantic.get("health_status") == "red":
        semantic_status = "source_red"
    elif semantic.get("api_key_used"):
        semantic_status = "key_used"
    elif semantic:
        semantic_status = "source_present"

    source_starved = is_source_starved(records, source_health)
    verdict = "stable"
    notes: list[str] = []
    if source_starved:
        verdict = "source_starved"
        notes.append("0 records with all-red source health")
    elif not records:
        verdict = "empty_non_starved"
        notes.append("0 records without all-red source health")
    elif counts["red"] > 0:
        verdict = "degraded"
        notes.append(f"{counts['red']} red sources")
    elif counts["yellow"] > 0:
        verdict = "degraded_but_usable"
        notes.append(f"{counts['yellow']} yellow sources")

    return {
        "date": date,
        "daily_json": str(path.relative_to(project_root)),
        "daily_json_exists": path.exists(),
        "daily_markdown": str(markdown_path.relative_to(project_root)) if markdown_path.exists() else None,
        "daily_markdown_exists": markdown_path.exists(),
        "digest_record_count": len(records),
        "final_record_count": int(metadata.get("total_records") or len(records)),
        "high_priority_count": high_priority_count(records),
        "source_health_entries": len(source_health),
        "green_sources": counts["green"],
        "yellow_sources": counts["yellow"],
        "red_sources": counts["red"],
        "source_starved": source_starved,
        "iacr_latest_status": iacr.get("latest_feed_status") or "unknown",
        "iacr_latest_records": int(iacr.get("latest_feed_records") or 0),
        "semantic_scholar_status": semantic_status,
        "semantic_scholar_api_key_used": bool(semantic.get("api_key_used")),
        "retryable_errors": retryable_errors,
        "reliability_verdict": verdict,
        "notes": notes,
        "TODO_VERIFY": ["verify next actual post-update daily run"] if date < "2026-06-09" else [],
    }


def build_summary(project_root: Path = PROJECT_ROOT, count: int = 3) -> dict[str, Any]:
    files = daily_json_files(project_root)
    selected = files[-count:]
    observations = [summarize_daily(path, project_root) for path in selected]
    observed_dates = [entry["date"] for entry in observations]
    pending_dates = [date for date in ("2026-06-09", "2026-06-10") if date not in observed_dates]
    handoff_files = sorted((project_root / "handoffs" / "weekly").glob("*-handoff-packets.json"))
    handoff_summary: dict[str, Any] = {"available": False}
    if handoff_files:
        handoff_path = handoff_files[-1]
        handoff_payload = load_json(handoff_path)
        handoff_summary = {
            "available": True,
            "path": str(handoff_path.relative_to(project_root)),
            "week_id": handoff_payload.get("week_id"),
            "packet_count": len(handoff_payload.get("packets") or []),
            "excluded_count": len(handoff_payload.get("excluded") or []),
            "todo_verify_count": len(handoff_payload.get("todo_verify") or []),
        }
    return {
        "schema_version": 1,
        "observation_count": len(observations),
        "observed_dates": observed_dates,
        "pending_dates": pending_dates,
        "complete_three_actual_post_update_runs": not pending_dates and len(observations) >= 3,
        "observations": observations,
        "weekly_handoff": handoff_summary,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Three-Day Daily Observation Summary",
        "",
        f"- observation_count: `{payload['observation_count']}`",
        f"- observed_dates: `{', '.join(payload['observed_dates'])}`",
        f"- pending_dates: `{', '.join(payload['pending_dates']) or 'none'}`",
        f"- complete_three_actual_post_update_runs: `{payload['complete_three_actual_post_update_runs']}`",
        "",
        "| date | json | md | records | final | high-priority | green | yellow | red | source-starved | IACR latest | Semantic Scholar | verdict |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for entry in payload["observations"]:
        lines.append(
            "| {date} | {json} | {md} | {records} | {final} | {high} | {green} | {yellow} | {red} | {starved} | {iacr}/{iacr_records} | {semantic} | {verdict} |".format(
                date=entry["date"],
                json="yes" if entry["daily_json_exists"] else "no",
                md="yes" if entry["daily_markdown_exists"] else "no",
                records=entry["digest_record_count"],
                final=entry["final_record_count"],
                high=entry["high_priority_count"],
                green=entry["green_sources"],
                yellow=entry["yellow_sources"],
                red=entry["red_sources"],
                starved=str(entry["source_starved"]).lower(),
                iacr=entry["iacr_latest_status"],
                iacr_records=entry["iacr_latest_records"],
                semantic=entry["semantic_scholar_status"],
                verdict=entry["reliability_verdict"],
            )
        )
    handoff = payload["weekly_handoff"]
    lines.extend(["", "## Weekly Handoff", ""])
    if handoff.get("available"):
        lines.append(f"- path: `{handoff['path']}`")
        lines.append(f"- week_id: `{handoff.get('week_id')}`")
        lines.append(f"- packet_count: `{handoff.get('packet_count')}`")
    else:
        lines.append("- missing")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize the latest three daily digest artifacts.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)

    payload = build_summary(project_root=args.project_root, count=args.count)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
