from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from lattice_digest.report_quality import anchor_evidence_text, false_positive_risk_text, semantic_scholar_advisory_text

from lattice_digest.digest_sections import HIGH_PRIORITY
from lattice_digest.weekly_synthesis import dedup_key


SCHEMA_VERSION = 1
DEFAULT_OUTPUT_DIR = Path("exports") / "research-progress"
UNSAFE_PHRASES = (
    "this proves",
    "this breaks",
    "this shows that kyber is insecure",
    "confirmed improvement",
    "guaranteed attack",
    "verified result",
)
VERIFY_STATUSES = {"NEEDS_MATH_CHECK", "NEEDS_CODE_CHECK", "NEEDS_REPLICATION", "TODO_VERIFY"}
EXPERIMENT_SECTIONS = {
    "Implementation / Side-channel / Systems",
    "BKZ / LLL / G6K / Lattice Reduction / Attacks",
    "AI-assisted Lattice Cryptanalysis",
    "Lattice + Privacy / FL / LLM Fine-tuning",
    "Lattice Isomorphism / Advanced Lattice Assumptions",
    "Registration-Based Encryption / Advanced Encryption Primitives",
    "Lattice Advanced Primitives",
}


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _week_id(value: date) -> str:
    iso = value.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _week_window(week_id: str) -> tuple[date, date]:
    match = re.fullmatch(r"([0-9]{4})-W([0-9]{2})", week_id)
    if not match:
        raise ValueError("week-id must look like YYYY-Www")
    year = int(match.group(1))
    week = int(match.group(2))
    start = date.fromisocalendar(year, week, 1)
    return start, start + timedelta(days=6)


def _window(days: int | None, from_date: str | None, to_date: str | None, week_id: str | None) -> tuple[date, date, str]:
    if from_date and to_date:
        start, end = _parse_date(from_date), _parse_date(to_date)
        return start, end, week_id or _week_id(end)
    if week_id:
        start, end = _week_window(week_id)
        return start, end, week_id
    end = _parse_date(to_date) if to_date else datetime.now().date()
    length = int(days or 7)
    start = end - timedelta(days=length - 1)
    return start, end, _week_id(end)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("contentReference", "").replace("oaicite", "").replace("id=", "")
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())


def _date_range(start: date, end: date) -> list[date]:
    if end < start:
        raise ValueError("from-date must be on or before to-date")
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def _sort_record(record: dict[str, Any]) -> tuple[int, int, str]:
    label_order = {"A": 0, "B": 1, "C": 2, "D": 3}
    label = str(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or 0)
    return (label_order.get(label, 9), -score, str(record.get("title") or "").lower())


def _record_line(record: dict[str, Any]) -> str:
    title = _clean(record.get("title") or "Untitled")
    label = _clean(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or 0)
    url = _clean(record.get("source_url") or record.get("url") or "unknown")
    sections = record.get("research_sections") if isinstance(record.get("research_sections"), list) else []
    return (
        f"- {title}｜{label} / {score}｜{', '.join(str(item) for item in sections) or 'unclassified'}｜{url}\n"
        f"  - Anchor evidence: {anchor_evidence_text(record)}\n"
        f"  - False-positive risk: {false_positive_risk_text(record)}\n"
        f"  - Semantic Scholar advisory: {semantic_scholar_advisory_text(record)}"
    )


def _queue_line(record: dict[str, Any]) -> str:
    title = _clean(record.get("title") or "Untitled")
    key = _clean(record.get("dedup_key") or "")
    priority = _clean(record.get("queue_priority") or "")
    reading = _clean(record.get("reading_status") or "")
    review = _clean(record.get("review_status") or "")
    note = _clean(record.get("obsidian_note_path") or "no note linked")
    return f"- {title}｜{priority}｜{reading}｜{review}｜{note}｜key: {key}"


def _source_health_line(item: dict[str, Any]) -> str:
    source = _clean(item.get("source") or "unknown")
    status = _clean(item.get("status") or item.get("health_status") or "unknown")
    error_type = _clean(item.get("error_type") or "none")
    return f"- {source}｜{status}｜error_type: {error_type}"


def _unique_records_from_weekly(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for container_key in ("report_buckets", "sections"):
        container = payload.get(container_key)
        if not isinstance(container, dict):
            continue
        for values in container.values():
            if not isinstance(values, list):
                continue
            for record in values:
                if not isinstance(record, dict):
                    continue
                key = str(record.get("dedup_key") or dedup_key(record))
                records.setdefault(key, record)
    return sorted(records.values(), key=_sort_record)


def load_weekly_payload(weekly_json: Path | None, week_id: str) -> tuple[dict[str, Any], list[Path], str]:
    candidates: list[Path] = []
    if weekly_json:
        candidates.append(weekly_json)
    candidates.append(Path("data") / "weekly" / f"{week_id}.json")
    for path in candidates:
        if path.exists():
            return _read_json(path), [path], "weekly_json"
    return {
        "schema_version": 1,
        "week_id": week_id,
        "sections": {},
        "report_buckets": {},
        "coverage": {"missing_weekly_json": True},
        "source_health_summary": {"available": False, "note": "Weekly JSON was not found."},
    }, [], "missing_weekly_json"


def load_reading_queue(path: Path) -> tuple[dict[str, Any], list[Path], str]:
    if not path.exists():
        return {"schema_version": 1, "records": []}, [], "missing_reading_queue"
    return _read_json(path), [path], "reading_queue"


def load_source_health(source_health_dir: Path, start: date, end: date) -> tuple[list[dict[str, Any]], list[Path]]:
    rows: list[dict[str, Any]] = []
    files: list[Path] = []
    for day in _date_range(start, end):
        path = source_health_dir / f"{day.isoformat()}.json"
        if not path.exists():
            continue
        payload = _read_json(path)
        files.append(path)
        for item in payload.get("sources", []):
            if isinstance(item, dict):
                row = dict(item)
                row.setdefault("date", day.isoformat())
                rows.append(row)
    return sorted(rows, key=lambda item: (str(item.get("date")), str(item.get("source")))), files


def load_note_paths(notes_dir: Path) -> tuple[list[Path], list[Path]]:
    if not notes_dir.exists():
        return [], []
    notes = sorted(path for path in notes_dir.rglob("*.md") if path.is_file())
    return notes, notes


def load_artifact_manifests(artifact_dir: Path) -> tuple[list[dict[str, Any]], list[Path]]:
    if not artifact_dir.exists():
        return [], []
    manifests = sorted(path for path in artifact_dir.glob("*/manifest.json") if path.is_file())
    payloads = []
    for path in manifests:
        try:
            payloads.append(_read_json(path))
        except json.JSONDecodeError:
            continue
    return payloads, manifests


def _high_priority_records(weekly_records: list[dict[str, Any]], queue_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for record in weekly_records:
        if str(record.get("relevance_label") or "") == "A" or HIGH_PRIORITY in record.get("report_buckets", []):
            by_key[str(record.get("dedup_key") or dedup_key(record))] = record
    for record in queue_records:
        if record.get("queue_priority") == "HIGH":
            by_key[str(record.get("dedup_key") or record.get("title"))] = record
    return sorted(by_key.values(), key=_sort_record)


def _must_read(queue_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [
            record
            for record in queue_records
            if record.get("queue_priority") == "HIGH" and record.get("reading_status") in {"TODO_READ", "READING"}
        ],
        key=_sort_record,
    )


def _must_verify(queue_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted([record for record in queue_records if record.get("review_status") in VERIFY_STATUSES], key=_sort_record)


def _candidate_experiments(queue_records: list[dict[str, Any]], weekly_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for record in [*queue_records, *weekly_records]:
        sections = set(record.get("research_sections", [])) if isinstance(record.get("research_sections"), list) else set()
        if record.get("review_status") == "NEEDS_REPLICATION" or sections & EXPERIMENT_SECTIONS:
            candidates.append(record)
    by_key: dict[str, dict[str, Any]] = {}
    for record in candidates:
        key = str(record.get("dedup_key") or dedup_key(record))
        by_key.setdefault(key, record)
    return sorted(by_key.values(), key=_sort_record)


def _red_yellow_health(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if str(row.get("status") or row.get("health_status") or "").lower() in {"red", "yellow", "failed", "degraded"}
    ]


def _list_or_empty(lines: list[str], values: list[str], empty: str = "- No matching items.") -> None:
    if values:
        lines.extend(values)
    else:
        lines.append(empty)


def render_advisor_update(context: dict[str, Any]) -> str:
    high = context["high_priority_records"][:8]
    queue = context["queue_records"]
    notes = context["note_paths"][:8]
    verify = context["must_verify"][:8]
    health = context["red_yellow_health"][:8]
    lines = [
        f"# Weekly Advisor Update Draft - {context['week_id']}",
        "",
        "## Monitoring Scope",
        "",
        f"- Window: {context['from_date']} .. {context['to_date']}",
        "- This draft is generated from existing digest metadata and local reading status only.",
        "- All candidate directions below are not yet verified.",
        "- Semantic Scholar citation metadata, if present, is advisory only and does not override relevance ranking.",
        "",
        "## High-Priority Papers Found",
        "",
    ]
    _list_or_empty(lines, [_record_line(record) for record in high])
    lines.extend(["", "## Reading Queue Changes", ""])
    _list_or_empty(lines, [_queue_line(record) for record in queue[:10]])
    lines.extend(["", "## Notes Created", ""])
    _list_or_empty(lines, [f"- {path}" for path in notes])
    lines.extend(["", "## Verification Backlog", ""])
    _list_or_empty(lines, [_queue_line(record) for record in verify])
    lines.extend(["", "## Candidate Directions, Not Claims", ""])
    _list_or_empty(
        lines,
        [
            f"- Candidate: {_clean(record.get('title'))}｜Suggested next action: read and verify original paper before using it."
            for record in high[:5]
        ],
    )
    lines.extend(["", "## Questions for Advisor", ""])
    _list_or_empty(
        lines,
        [
            f"- For {_clean(record.get('title'))}: is this worth prioritizing for reading or verification?"
            for record in high[:5]
        ],
    )
    lines.extend(["", "## Plan for Next Week", ""])
    _list_or_empty(lines, [f"- Address source health issue: {_source_health_line(row)[2:]}" for row in health])
    if not health:
        lines.append("- Continue reading high-priority papers and update verification status.")
    lines.append("")
    return "\n".join(lines)


def render_progress_log(context: dict[str, Any]) -> str:
    coverage = context["weekly_payload"].get("coverage", {}) if isinstance(context["weekly_payload"], dict) else {}
    queue = context["queue_records"]
    moved = [record for record in queue if record.get("status_history")]
    health = context["red_yellow_health"]
    lines = [
        f"# Research Progress Log - {context['week_id']}",
        "",
        "## Weekly Inputs",
        "",
        f"- Weekly input mode: {context['weekly_input_mode']}",
        f"- Reading queue input mode: {context['reading_queue_mode']}",
        f"- Source files: {len(context['source_files'])}",
        "",
        "## Digest Coverage",
        "",
        f"- expected_days: {coverage.get('expected_days', 'unknown')}",
        f"- loaded_days: {coverage.get('loaded_days', [])}",
        f"- missing_days: {coverage.get('missing_days', [])}",
        f"- unique_records: {coverage.get('unique_records', len(context['weekly_records']))}",
        "",
        "## Reading Queue Delta",
        "",
        f"- Queue records loaded: {len(queue)}",
        f"- Must read: {len(context['must_read'])}",
        f"- Must verify: {len(context['must_verify'])}",
        "",
        "## Obsidian Notes Created",
        "",
    ]
    _list_or_empty(lines, [f"- {path}" for path in context["note_paths"][:20]])
    lines.extend(["", "## Papers Moved Across Statuses", ""])
    _list_or_empty(lines, [_queue_line(record) for record in moved[:20]])
    lines.extend(["", "## Verification Tasks", ""])
    _list_or_empty(lines, [_queue_line(record) for record in context["must_verify"][:20]])
    lines.extend(["", "## Research Threads", ""])
    section_counts: dict[str, int] = {}
    for record in context["weekly_records"]:
        for section in record.get("research_sections", []) if isinstance(record.get("research_sections"), list) else []:
            section_counts[str(section)] = section_counts.get(str(section), 0) + 1
    _list_or_empty(lines, [f"- {section}: {count}" for section, count in sorted(section_counts.items())])
    lines.extend(["", "## Risks / Noise / False Positives", ""])
    _list_or_empty(lines, [_source_health_line(row) for row in health], "- No red/yellow source health items in available ledgers.")
    lines.extend(["", "## Next Actions", "", "- Keep claims cautious until original papers are checked.", ""])
    return "\n".join(lines)


def render_next_week_plan(context: dict[str, Any]) -> str:
    lines = [
        f"# Next Week Plan - {context['week_id']}",
        "",
        "## Must Read",
        "",
    ]
    _list_or_empty(lines, [_queue_line(record) for record in context["must_read"][:10]])
    lines.extend(["", "## Must Verify", ""])
    _list_or_empty(lines, [_queue_line(record) for record in context["must_verify"][:10]])
    lines.extend(["", "## Candidate Experiments", ""])
    _list_or_empty(lines, [_record_line(record) for record in context["candidate_experiments"][:10]])
    lines.extend(["", "## Advisor Questions", ""])
    _list_or_empty(
        lines,
        [
            f"- Should {_clean(record.get('title'))} be read as a core paper, related work, or ignored for now?"
            for record in context["high_priority_records"][:5]
        ],
    )
    lines.extend(["", "## Engineering Maintenance", ""])
    _list_or_empty(
        lines,
        [f"- Check source health: {_source_health_line(row)[2:]}" for row in context["red_yellow_health"][:10]],
        "- No engineering maintenance items detected from available source health ledgers.",
    )
    lines.append("")
    return "\n".join(lines)


def render_verification_backlog(context: dict[str, Any]) -> str:
    queue = context["queue_records"]
    needs_original = [record for record in queue if record.get("review_status") == "TODO_VERIFY"]
    needs_math = [record for record in queue if record.get("review_status") == "NEEDS_MATH_CHECK"]
    needs_code = [record for record in queue if record.get("review_status") in {"NEEDS_CODE_CHECK", "NEEDS_REPLICATION"}]
    missing_url = [record for record in queue if not record.get("source_url")]
    false_positive = [record for record in queue if record.get("reading_status") == "IGNORED" or record.get("review_status") == "NOT_RELEVANT"]
    sections = [
        ("Needs Original Paper Check", needs_original),
        ("Needs Math Check", needs_math),
        ("Needs Code / Artifact Check", needs_code),
        ("Needs Source Metadata Check", missing_url),
        ("Potential False Positives", false_positive),
    ]
    lines = [f"# Verification Backlog - {context['week_id']}", ""]
    for title, records in sections:
        lines.extend([f"## {title}", ""])
        _list_or_empty(lines, [_queue_line(record) for record in sorted(records, key=_sort_record)])
        lines.append("")
    return "\n".join(lines)


def _assert_cautious(text: str) -> None:
    lowered = text.lower()
    for phrase in UNSAFE_PHRASES:
        if phrase in lowered:
            raise ValueError(f"unsafe phrase in generated research progress output: {phrase}")


def build_context(
    *,
    days: int | None = 7,
    from_date: str | None = None,
    to_date: str | None = None,
    week_id: str | None = None,
    weekly_json: Path | None = None,
    reading_queue: Path = Path("state") / "reading-queue.json",
    source_health_dir: Path = Path("audits") / "source-health",
    obsidian_notes_dir: Path = Path("exports") / "obsidian-paper-notes" / "Papers",
    artifact_dir: Path = Path("exports") / "research-artifacts",
) -> dict[str, Any]:
    start, end, resolved_week = _window(days, from_date, to_date, week_id)
    weekly_payload, weekly_files, weekly_mode = load_weekly_payload(weekly_json, resolved_week)
    weekly_records = _unique_records_from_weekly(weekly_payload)
    queue_payload, queue_files, queue_mode = load_reading_queue(reading_queue)
    queue_records = sorted(
        [record for record in queue_payload.get("records", []) if isinstance(record, dict)],
        key=_sort_record,
    )
    health_rows, health_files = load_source_health(source_health_dir, start, end)
    note_paths, note_files = load_note_paths(obsidian_notes_dir)
    artifact_payloads, artifact_files = load_artifact_manifests(artifact_dir)
    source_files = [*weekly_files, *queue_files, *health_files, *note_files, *artifact_files]
    context = {
        "schema_version": SCHEMA_VERSION,
        "week_id": resolved_week,
        "from_date": start.isoformat(),
        "to_date": end.isoformat(),
        "weekly_payload": weekly_payload,
        "weekly_input_mode": weekly_mode,
        "weekly_records": weekly_records,
        "reading_queue_mode": queue_mode,
        "queue_records": queue_records,
        "source_health_rows": health_rows,
        "red_yellow_health": _red_yellow_health(health_rows),
        "note_paths": note_paths,
        "artifact_manifests": artifact_payloads,
        "source_files": source_files,
    }
    context["high_priority_records"] = _high_priority_records(weekly_records, queue_records)
    context["must_read"] = _must_read(queue_records)
    context["must_verify"] = _must_verify(queue_records)
    context["candidate_experiments"] = _candidate_experiments(queue_records, weekly_records)
    return context


def build_outputs(context: dict[str, Any], output_dir: Path, *, dry_run: bool = False) -> dict[str, Any]:
    run_dir = output_dir / context["week_id"]
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    files = {
        "advisor-update-draft.md": render_advisor_update(context),
        "research-progress-log.md": render_progress_log(context),
        "next-week-plan.md": render_next_week_plan(context),
        "verification-backlog.md": render_verification_backlog(context),
    }
    output_files = [str(run_dir / "manifest.json"), *[str(run_dir / name) for name in files]]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "week_id": context["week_id"],
        "from_date": context["from_date"],
        "to_date": context["to_date"],
        "generated_at": generated_at,
        "source_files": [str(path) for path in context["source_files"]],
        "output_files": output_files,
        "counts": {
            "weekly_records": len(context["weekly_records"]),
            "queue_records": len(context["queue_records"]),
            "high_priority": len(context["high_priority_records"]),
            "must_read": len(context["must_read"]),
            "must_verify": len(context["must_verify"]),
            "notes": len(context["note_paths"]),
            "source_health_rows": len(context["source_health_rows"]),
            "red_yellow_health": len(context["red_yellow_health"]),
            "artifact_manifests": len(context["artifact_manifests"]),
        },
        "dry_run": dry_run,
    }
    for content in files.values():
        _assert_cautious(content)
    return {"run_dir": run_dir, "manifest": manifest, "files": files}


def write_outputs(plan: dict[str, Any]) -> list[Path]:
    run_dir: Path = plan["run_dir"]
    run_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(plan["manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(manifest_path)
    for name, content in plan["files"].items():
        path = run_dir / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def generate_research_progress(
    *,
    days: int | None = 7,
    from_date: str | None = None,
    to_date: str | None = None,
    week_id: str | None = None,
    weekly_json: Path | None = None,
    reading_queue: Path = Path("state") / "reading-queue.json",
    source_health_dir: Path = Path("audits") / "source-health",
    obsidian_notes_dir: Path = Path("exports") / "obsidian-paper-notes" / "Papers",
    artifact_dir: Path = Path("exports") / "research-artifacts",
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dry_run: bool = False,
) -> dict[str, Any]:
    context = build_context(
        days=days,
        from_date=from_date,
        to_date=to_date,
        week_id=week_id,
        weekly_json=weekly_json,
        reading_queue=reading_queue,
        source_health_dir=source_health_dir,
        obsidian_notes_dir=obsidian_notes_dir,
        artifact_dir=artifact_dir,
    )
    plan = build_outputs(context, output_dir, dry_run=dry_run)
    written = [] if dry_run else write_outputs(plan)
    return {**plan, "context": context, "written": written}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate advisor update and research progress logs from existing artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate", help="Generate weekly advisor/progress documents.")
    generate.add_argument("--days", type=int, default=7)
    generate.add_argument("--from-date")
    generate.add_argument("--to-date")
    generate.add_argument("--week-id")
    generate.add_argument("--weekly-json", type=Path)
    generate.add_argument("--reading-queue", type=Path, default=Path("state") / "reading-queue.json")
    generate.add_argument("--source-health-dir", type=Path, default=Path("audits") / "source-health")
    generate.add_argument("--obsidian-notes-dir", type=Path, default=Path("exports") / "obsidian-paper-notes" / "Papers")
    generate.add_argument("--artifact-dir", type=Path, default=Path("exports") / "research-artifacts")
    generate.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    generate.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = generate_research_progress(
        days=args.days,
        from_date=args.from_date,
        to_date=args.to_date,
        week_id=args.week_id,
        weekly_json=args.weekly_json,
        reading_queue=args.reading_queue,
        source_health_dir=args.source_health_dir,
        obsidian_notes_dir=args.obsidian_notes_dir,
        artifact_dir=args.artifact_dir,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
    )
    manifest = result["manifest"]
    print(
        "Research progress {week}: high_priority={high}, must_verify={verify}, notes={notes}".format(
            week=manifest["week_id"],
            high=manifest["counts"]["high_priority"],
            verify=manifest["counts"]["must_verify"],
            notes=manifest["counts"]["notes"],
        )
    )
    print(f"output dir: {result['run_dir']}")
    if args.dry_run:
        print("DRY RUN: no files written.")
    else:
        for path in result["written"]:
            print(f"wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
