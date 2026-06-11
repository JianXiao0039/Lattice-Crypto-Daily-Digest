from __future__ import annotations

import json
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_daily(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {"records": payload, "metadata": {}, "source_health": []}
    if not isinstance(payload, dict):
        raise ValueError(f"unsupported JSON root in {path}")
    return payload


def source_status(entry: dict[str, Any]) -> str:
    return str(entry.get("health_status") or entry.get("status") or "unknown")


def find_source(source_health: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next((entry for entry in source_health if entry.get("source") == name), {})


def high_priority_count(records: list[dict[str, Any]]) -> int:
    return sum(
        1
        for record in records
        if record.get("relevance_label") == "A"
        or record.get("reading_priority") == 1
        or record.get("priority") == 1
        or "精读" in str(record.get("priority_label") or "")
    )


def semantic_status(entry: dict[str, Any]) -> tuple[str, bool, bool]:
    if not entry:
        return "unknown", False, False
    key_present = bool(entry.get("api_key_used"))
    error_type = str(entry.get("error_type") or "").lower()
    text = " ".join(
        [str(entry.get("error_message") or "")]
        + [str(item) for item in entry.get("warnings") or []]
        + [str(item) for item in entry.get("errors") or []]
    ).lower()
    if "401" in text or "403" in text or "auth" in error_type:
        return "authentication_failure", key_present, False
    if "429" in text or "rate_limit" in error_type:
        return "rate_limit", key_present, False
    if "urlerror" in text or error_type in {"network_error", "ssl_error", "timeout", "warning"}:
        return "network_failure", key_present, False
    if int(entry.get("raw_count") or entry.get("raw_candidates") or 0) > 0:
        return "enrichment_success", key_present, True
    if key_present:
        return "no_candidates_to_enrich", True, False
    return "no_key", False, False


def tag_date(project_root: Path, tag: str = "v0.4.0") -> date | None:
    result = subprocess.run(
        ["git", "show", "-s", "--format=%aI", tag],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return datetime.fromisoformat(result.stdout.strip()).date()


def latest_daily_paths(project_root: Path, limit: int = 7) -> list[Path]:
    return sorted((project_root / "data").glob("????-??-??.json"))[-limit:]


def audit_daily(project_root: Path, json_path: Path, release_date: date | None) -> dict[str, Any]:
    payload = load_daily(json_path)
    records = list(payload.get("records") or [])
    metadata = payload.get("metadata") or {}
    source_health = list(payload.get("source_health") or metadata.get("source_health") or [])
    statuses = [source_status(entry) for entry in source_health]
    counts = {name: statuses.count(name) for name in ("green", "yellow", "red")}
    total = len(source_health)
    retryable = sum(1 for entry in source_health if entry.get("retryable"))
    non_retryable = sum(
        1
        for entry in source_health
        if (entry.get("error_type") or entry.get("error_message")) and not entry.get("retryable")
    )
    raw_count = sum(int(entry.get("raw_count") or entry.get("raw_candidates") or 0) for entry in source_health)
    normalized_count = sum(
        int(entry.get("normalized_count") or entry.get("normalized_candidates") or 0) for entry in source_health
    )
    source_starved = bool(not records and total and counts["red"] == total)
    if records:
        empty_reason = "non_empty"
    elif source_starved:
        empty_reason = "all_red_sources"
    elif not source_health:
        empty_reason = "missing_source_health"
    else:
        empty_reason = "no_records_without_full_source_failure"

    run_date = date.fromisoformat(json_path.stem)
    if release_date is None:
        origin = "TODO_VERIFY"
    else:
        origin = "post_tag" if run_date >= release_date else "pre_tag_baseline"

    iacr = find_source(source_health, "iacr_eprint")
    iacr_status = iacr.get("latest_feed_status") or "latest_feed_not_included"
    semantic = find_source(source_health, "semantic_scholar")
    semantic_state, key_present, enrichment_available = semantic_status(semantic)
    markdown_path = project_root / "digests" / f"{json_path.stem}.md"
    todo: list[str] = []
    if origin != "post_tag":
        todo.append("not a post-tag observation")
    if not markdown_path.exists():
        todo.append("daily Markdown missing")
    if not source_health:
        todo.append("source health missing")
    if source_starved:
        todo.append("source-starved; not evidence of no relevant papers")

    return {
        "date": json_path.stem,
        "artifact_origin": origin,
        "markdown_exists": markdown_path.exists(),
        "json_exists": True,
        "raw_candidate_count": raw_count,
        "normalized_count": normalized_count,
        "final_record_count": int(metadata.get("total_records") or len(records)),
        "high_priority_count": high_priority_count(records),
        "source_total": total,
        "source_green": counts["green"],
        "source_yellow": counts["yellow"],
        "source_red": counts["red"],
        "source_reachability_rate": round((counts["green"] + counts["yellow"]) / total, 4) if total else None,
        "retryable_error_count": retryable,
        "non_retryable_error_count": non_retryable,
        "source_starved": source_starved,
        "empty_digest_reason": empty_reason,
        "iacr_latest_status": iacr_status,
        "iacr_latest_records": int(iacr.get("latest_feed_records") or 0),
        "semantic_scholar_status": semantic_state,
        "semantic_scholar_key_present_boolean": key_present,
        "semantic_scholar_enrichment_available": enrichment_available,
        "workflow_validation_status": "artifact_complete" if markdown_path.exists() and source_health else "incomplete",
        "github_actions_status": "TODO_VERIFY",
        "TODO_VERIFY": todo,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_runs = len(rows)
    source_total = sum(row["source_total"] for row in rows)
    reachable = sum(row["source_green"] + row["source_yellow"] for row in rows)
    complete = sum(1 for row in rows if row["markdown_exists"] and row["json_exists"])
    all_red = sum(1 for row in rows if row["source_total"] and row["source_red"] == row["source_total"])
    source_starved = sum(1 for row in rows if row["source_starved"])
    iacr_success = sum(1 for row in rows if row["iacr_latest_status"] in {"fetched", "cache_hit"})
    semantic_usable = sum(1 for row in rows if row["semantic_scholar_enrichment_available"])
    post_tag = sum(1 for row in rows if row["artifact_origin"] == "post_tag")
    retryable = sum(row["retryable_error_count"] for row in rows)
    non_retryable = sum(row["non_retryable_error_count"] for row in rows)

    if post_tag == 0:
        verdict = "insufficient_evidence"
        transition = "insufficient_evidence"
    elif source_starved == 0 and complete == total_runs:
        verdict = "mostly_stable" if retryable else "stable"
        transition = "proceed_with_source_monitoring"
    elif source_starved < total_runs:
        verdict = "degraded_but_usable"
        transition = "proceed_with_source_monitoring"
    else:
        verdict = "source_starved"
        transition = "hold_v0.5_until_source_recovery"

    return {
        "observed_run_count": total_runs,
        "post_tag_run_count": post_tag,
        "complete_artifact_rate": round(complete / total_runs, 4) if total_runs else 0.0,
        "source_reachability_rate": round(reachable / source_total, 4) if source_total else 0.0,
        "all_red_run_count": all_red,
        "source_starved_run_count": source_starved,
        "retryable_failure_count": retryable,
        "non_retryable_failure_count": non_retryable,
        "iacr_latest_success_rate": round(iacr_success / total_runs, 4) if total_runs else 0.0,
        "semantic_scholar_usable_run_rate": round(semantic_usable / total_runs, 4) if total_runs else 0.0,
        "reliability_verdict": verdict,
        "v0_5_transition_decision": transition,
    }


def build_audit(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    release_date = tag_date(project_root)
    paths = latest_daily_paths(project_root)
    rows = [audit_daily(project_root, path, release_date) for path in paths]
    return {
        "schema_version": 1,
        "tag": "v0.4.0",
        "tag_date": release_date.isoformat() if release_date else None,
        "observation_dates": [row["date"] for row in rows],
        "rows": rows,
        "summary": summarize(rows),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Seven-Day Source Reliability Audit",
        "",
        f"- tag_date: `{payload['tag_date']}`",
        f"- observation_dates: `{', '.join(payload['observation_dates'])}`",
        f"- post_tag_run_count: `{summary['post_tag_run_count']}`",
        f"- reliability_verdict: `{summary['reliability_verdict']}`",
        f"- complete_artifact_rate: `{summary['complete_artifact_rate']:.2%}`",
        f"- source_reachability_rate: `{summary['source_reachability_rate']:.2%}`",
        f"- source_starved_run_count: `{summary['source_starved_run_count']}`",
        f"- iacr_latest_success_rate: `{summary['iacr_latest_success_rate']:.2%}`",
        f"- semantic_scholar_usable_run_rate: `{summary['semantic_scholar_usable_run_rate']:.2%}`",
        "",
        "| date | origin | MD | JSON | raw | normalized | final | high | G/Y/R | reachability | retryable | starved | IACR | Semantic Scholar | TODO_VERIFY |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        reachability = row["source_reachability_rate"]
        lines.append(
            "| {date} | {origin} | {md} | {js} | {raw} | {norm} | {final} | {high} | {g}/{y}/{r} | {reach} | {retry} | {starved} | {iacr}/{iacr_n} | {semantic} | {todo} |".format(
                date=row["date"],
                origin=row["artifact_origin"],
                md="yes" if row["markdown_exists"] else "no",
                js="yes" if row["json_exists"] else "no",
                raw=row["raw_candidate_count"],
                norm=row["normalized_count"],
                final=row["final_record_count"],
                high=row["high_priority_count"],
                g=row["source_green"],
                y=row["source_yellow"],
                r=row["source_red"],
                reach=f"{reachability:.0%}" if reachability is not None else "n/a",
                retry=row["retryable_error_count"],
                starved=str(row["source_starved"]).lower(),
                iacr=row["iacr_latest_status"],
                iacr_n=row["iacr_latest_records"],
                semantic=row["semantic_scholar_status"],
                todo="; ".join(row["TODO_VERIFY"]) or "none",
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    print(render_markdown(build_audit()), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
