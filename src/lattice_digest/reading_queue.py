from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from lattice_digest.digest_sections import (
    AI_LATTICE,
    HIGH_PRIORITY,
    IDEA_BANK_CANDIDATES,
    IMPLEMENTATION_SYSTEMS,
    LATTICE_REDUCTION_ATTACKS,
    LWE_FAMILY,
    PAPER_PLAN_CANDIDATES,
    PQC_STANDARDS,
    SIS_NTRU_COMMITMENTS,
)
from lattice_digest.weekly_synthesis import build_weekly_synthesis, dedup_key


SCHEMA_VERSION = 1
DEFAULT_STATE_PATH = Path("state") / "reading-queue.json"
DEFAULT_EXPORT_DIR = Path("exports") / "reading-queue"

READING_STATUSES = ("TODO_READ", "TODO_SKIM", "READING", "SKIMMED", "READ", "IGNORED")
REVIEW_STATUSES = (
    "TODO_VERIFY",
    "VERIFIED",
    "NEEDS_REPLICATION",
    "NEEDS_MATH_CHECK",
    "NEEDS_CODE_CHECK",
    "NOT_RELEVANT",
)
QUEUE_PRIORITIES = ("HIGH", "MEDIUM", "LOW")

MAIN_RESEARCH_SECTIONS = (
    AI_LATTICE,
    LWE_FAMILY,
    SIS_NTRU_COMMITMENTS,
    LATTICE_REDUCTION_ATTACKS,
    PQC_STANDARDS,
    IMPLEMENTATION_SYSTEMS,
)
IMPORT_SECTIONS = (HIGH_PRIORITY, IDEA_BANK_CANDIDATES, PAPER_PLAN_CANDIDATES, *MAIN_RESEARCH_SECTIONS)
LABEL_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}
PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _date_range(start: date, end: date) -> list[date]:
    if end < start:
        raise ValueError("from-date must be on or before to-date")
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def _window(days: int | None, from_date: str | None, to_date: str | None) -> tuple[date, date]:
    if from_date and to_date:
        return _parse_date(from_date), _parse_date(to_date)
    end = _parse_date(to_date) if to_date else datetime.now().date()
    length = int(days or 7)
    return end - timedelta(days=length - 1), end


def _week_id(value: date) -> str:
    iso = value.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {"records": payload}
    if isinstance(payload, dict):
        return payload
    return {"records": []}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("contentReference", "").replace("oaicite", "").replace("id=", "")
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())


def normalize_title(value: str) -> str:
    text = value.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _record_key(record: dict[str, Any]) -> str:
    return str(record.get("dedup_key") or dedup_key(record))


def _publication_date(record: dict[str, Any]) -> str:
    return str(record.get("publication_date") or record.get("date") or record.get("update_date") or "")


def _date_rank(value: str) -> int:
    try:
        return -date.fromisoformat(value[:10]).toordinal()
    except ValueError:
        return 0


def queue_sort_key(record: dict[str, Any]) -> tuple[int, int, int, int, str]:
    priority = str(record.get("queue_priority") or "LOW")
    label = str(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or 0)
    return (
        PRIORITY_ORDER.get(priority, 9),
        LABEL_ORDER.get(label, 9),
        -score,
        _date_rank(_publication_date(record)),
        str(record.get("title") or "").lower(),
    )


def _stable_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted({str(value) for value in values if str(value)})


def _stable_sections(values: Any) -> list[str]:
    sections = _stable_list(values)
    order = {name: index for index, name in enumerate(IMPORT_SECTIONS)}
    return sorted(sections, key=lambda item: (order.get(item, 999), item.lower()))


def track_for_record(record: dict[str, Any]) -> str:
    sections = set(_stable_sections(record.get("research_sections")))
    for section in MAIN_RESEARCH_SECTIONS:
        if section in sections:
            return section
    return "Other"


def queue_priority_for_record(record: dict[str, Any]) -> str:
    sections = set(_stable_sections(record.get("research_sections")))
    main_match = bool(sections & set(MAIN_RESEARCH_SECTIONS))
    label = str(record.get("relevance_label") or "D")
    if label == "A" and main_match:
        return "HIGH"
    if label == "B" and main_match:
        return "MEDIUM"
    return "LOW"


def default_reading_status(priority: str) -> str:
    if priority == "HIGH":
        return "TODO_READ"
    return "TODO_SKIM"


def should_import_record(record: dict[str, Any]) -> bool:
    sections = set(_stable_sections(record.get("research_sections")))
    label = str(record.get("relevance_label") or "D")
    if label == "D" and PAPER_PLAN_CANDIDATES not in sections:
        return False
    return bool(sections & set(IMPORT_SECTIONS))


def _records_from_weekly_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records_by_key: dict[str, dict[str, Any]] = {}
    sections = payload.get("sections")
    if not isinstance(sections, dict):
        return []
    for section_name, section_records in sections.items():
        if not isinstance(section_records, list):
            continue
        for record in section_records:
            if not isinstance(record, dict):
                continue
            item = dict(record)
            existing_sections = _stable_sections(item.get("research_sections"))
            item["research_sections"] = _stable_sections([*existing_sections, str(section_name)])
            key = _record_key(item)
            if key in records_by_key:
                records_by_key[key] = _merge_candidate_records(records_by_key[key], item)
            else:
                records_by_key[key] = item
    return sorted(records_by_key.values(), key=queue_sort_key)


def _merge_candidate_records(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    merged["seen_dates"] = sorted({*_stable_list(base.get("seen_dates")), *_stable_list(incoming.get("seen_dates"))})
    merged["seen_sources"] = sorted({*_stable_list(base.get("seen_sources")), *_stable_list(incoming.get("seen_sources"))})
    merged["research_sections"] = _stable_sections([*_stable_list(base.get("research_sections")), *_stable_list(incoming.get("research_sections"))])
    incoming_score = int(incoming.get("relevance_score") or 0)
    base_score = int(base.get("relevance_score") or 0)
    if incoming_score > base_score:
        for key, value in incoming.items():
            if key not in {"seen_dates", "seen_sources", "research_sections"}:
                merged[key] = value
    return merged


def _daily_payload_records(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    raw_records = payload.get("records")
    day = path.stem
    records: list[dict[str, Any]] = []
    if not isinstance(raw_records, list):
        return records
    for record in raw_records:
        if not isinstance(record, dict):
            continue
        item = dict(record)
        item.setdefault("seen_dates", [day])
        item.setdefault("seen_sources", [str(item.get("source") or "unknown")])
        item.setdefault("dedup_key", _record_key(item))
        records.append(item)
    return records


def _default_weekly_json(data_dir: Path, end: date) -> Path:
    return data_dir / "weekly" / f"{_week_id(end)}.json"


def _default_artifact_manifest(end: date) -> Path:
    return Path("exports") / "research-artifacts" / end.isoformat() / "manifest.json"


def _records_from_manifest(path: Path) -> tuple[list[dict[str, Any]], list[Path], str]:
    manifest = _read_json(path)
    records: list[dict[str, Any]] = []
    source_files: list[Path] = []
    for raw in manifest.get("source_files", []):
        source_path = Path(str(raw))
        if not source_path.exists():
            continue
        source_files.append(source_path)
        payload = _read_json(source_path)
        if isinstance(payload.get("sections"), dict):
            records.extend(_records_from_weekly_payload(payload))
        else:
            records.extend(_daily_payload_records(source_path))
    return _dedup_candidates(records), source_files, "research_artifact_manifest"


def _dedup_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for record in records:
        key = _record_key(record)
        record = dict(record)
        record.setdefault("dedup_key", key)
        by_key[key] = _merge_candidate_records(by_key[key], record) if key in by_key else record
    return sorted(by_key.values(), key=queue_sort_key)


def load_import_candidates(
    *,
    days: int | None = 7,
    from_date: str | None = None,
    to_date: str | None = None,
    data_dir: Path = Path("data"),
    weekly_json: Path | None = None,
    artifact_manifest: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    start, end = _window(days, from_date, to_date)
    explicit_weekly = weekly_json
    default_weekly = _default_weekly_json(data_dir, end)
    weekly_path = explicit_weekly if explicit_weekly and explicit_weekly.exists() else default_weekly
    if weekly_path.exists():
        payload = _read_json(weekly_path)
        records = _records_from_weekly_payload(payload)
        return _dedup_candidates([record for record in records if should_import_record(record)]), {
            "input_mode": "weekly_json",
            "source_files": [str(weekly_path)],
            "from_date": start.isoformat(),
            "to_date": end.isoformat(),
        }

    manifest_path = artifact_manifest if artifact_manifest and artifact_manifest.exists() else _default_artifact_manifest(end)
    if manifest_path.exists():
        records, source_files, mode = _records_from_manifest(manifest_path)
        return _dedup_candidates([record for record in records if should_import_record(record)]), {
            "input_mode": mode,
            "source_files": [str(path) for path in source_files],
            "from_date": start.isoformat(),
            "to_date": end.isoformat(),
        }

    weekly_payload = build_weekly_synthesis(data_dir, start, end)
    records = _records_from_weekly_payload(weekly_payload)
    source_files = [
        data_dir / f"{day.isoformat()}.json"
        for day in _date_range(start, end)
        if (data_dir / f"{day.isoformat()}.json").exists()
    ]
    return _dedup_candidates([record for record in records if should_import_record(record)]), {
        "input_mode": "daily_json_fallback",
        "source_files": [str(path) for path in source_files],
        "from_date": start.isoformat(),
        "to_date": end.isoformat(),
    }


def empty_state() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "records": []}


def load_state(path: Path = DEFAULT_STATE_PATH) -> dict[str, Any]:
    if not path.exists():
        return empty_state()
    payload = _read_json(path)
    records = payload.get("records")
    if not isinstance(records, list):
        payload["records"] = []
    payload["schema_version"] = int(payload.get("schema_version") or SCHEMA_VERSION)
    return payload


def save_state(path: Path, state: dict[str, Any]) -> None:
    state = dict(state)
    state["records"] = sorted([record for record in state.get("records", []) if isinstance(record, dict)], key=queue_sort_key)
    state["schema_version"] = SCHEMA_VERSION
    _write_json(path, state)


def _history(action: str, timestamp: str, *, field: str | None = None, old: object = None, new: object = None) -> dict[str, Any]:
    item = {"timestamp": timestamp, "action": action}
    if field is not None:
        item["field"] = field
        item["old"] = old
        item["new"] = new
    return item


def _queue_record(record: dict[str, Any], timestamp: str) -> dict[str, Any]:
    sections = _stable_sections(record.get("research_sections"))
    item = {
        "schema_version": SCHEMA_VERSION,
        "dedup_key": _record_key(record),
        "title": _clean(record.get("title") or ""),
        "source_url": _clean(record.get("source_url") or record.get("url") or ""),
        "doi": _clean(record.get("doi") or ""),
        "arxiv_id": _clean(record.get("arxiv_id") or ""),
        "publication_date": _clean(_publication_date(record)),
        "relevance_label": _clean(record.get("relevance_label") or "D"),
        "relevance_score": int(record.get("relevance_score") or record.get("reading_priority_score") or 0),
        "research_sections": sections,
        "ranking_explanation": record.get("ranking_explanation") if isinstance(record.get("ranking_explanation"), dict) else {},
        "seen_dates": _stable_list(record.get("seen_dates")) or ([record.get("publication_date")] if record.get("publication_date") else []),
        "seen_sources": _stable_list(record.get("seen_sources")) or ([str(record.get("source"))] if record.get("source") else []),
        "queue_priority": queue_priority_for_record(record),
        "track": track_for_record(record),
        "reading_status": "",
        "review_status": "TODO_VERIFY",
        "zotero_key": "",
        "obsidian_note_path": "",
        "personal_notes_path": "",
        "added_at": timestamp,
        "updated_at": timestamp,
        "status_history": [_history("imported", timestamp)],
    }
    item["reading_status"] = default_reading_status(item["queue_priority"])
    return item


def _merge_queue_record(existing: dict[str, Any], incoming: dict[str, Any], timestamp: str) -> dict[str, Any]:
    merged = dict(existing)
    manual_fields = {
        "reading_status",
        "review_status",
        "zotero_key",
        "obsidian_note_path",
        "personal_notes_path",
        "status_history",
        "added_at",
    }
    for key, value in incoming.items():
        if key in manual_fields:
            continue
        if key == "relevance_score":
            if int(value or 0) > int(merged.get("relevance_score") or 0):
                merged[key] = value
            continue
        if key == "relevance_label":
            if LABEL_ORDER.get(str(value), 9) < LABEL_ORDER.get(str(merged.get(key)), 9):
                merged[key] = value
            continue
        if key == "queue_priority":
            if PRIORITY_ORDER.get(str(value), 9) < PRIORITY_ORDER.get(str(merged.get(key)), 9):
                merged[key] = value
            continue
        if key == "seen_dates":
            merged[key] = sorted({*_stable_list(merged.get(key)), *_stable_list(value)})
            continue
        if key == "seen_sources":
            merged[key] = sorted({*_stable_list(merged.get(key)), *_stable_list(value)})
            continue
        if key == "research_sections":
            merged[key] = _stable_sections([*_stable_list(merged.get(key)), *_stable_list(value)])
            continue
        if value and not merged.get(key):
            merged[key] = value
    merged["updated_at"] = timestamp
    return merged


def import_queue(
    state: dict[str, Any],
    candidates: list[dict[str, Any]],
    *,
    timestamp: str | None = None,
) -> tuple[dict[str, Any], dict[str, int]]:
    stamp = timestamp or now_iso()
    existing_records = [record for record in state.get("records", []) if isinstance(record, dict)]
    by_key = {str(record.get("dedup_key")): dict(record) for record in existing_records if record.get("dedup_key")}
    imported = 0
    updated = 0
    skipped = 0
    for candidate in candidates:
        if not should_import_record(candidate):
            skipped += 1
            continue
        incoming = _queue_record(candidate, stamp)
        key = incoming["dedup_key"]
        if key in by_key:
            by_key[key] = _merge_queue_record(by_key[key], incoming, stamp)
            updated += 1
        else:
            by_key[key] = incoming
            imported += 1
    new_state = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": stamp,
        "records": sorted(by_key.values(), key=queue_sort_key),
    }
    return new_state, {"imported": imported, "updated": updated, "skipped": skipped, "total": len(new_state["records"])}


def _find_record(state: dict[str, Any], key: str) -> dict[str, Any]:
    for record in state.get("records", []):
        if isinstance(record, dict) and str(record.get("dedup_key")) == key:
            return record
    raise KeyError(f"reading queue record not found: {key}")


def mark_status(
    state: dict[str, Any],
    *,
    key: str,
    reading_status: str | None = None,
    review_status: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    if reading_status and reading_status not in READING_STATUSES:
        raise ValueError(f"invalid reading_status: {reading_status}")
    if review_status and review_status not in REVIEW_STATUSES:
        raise ValueError(f"invalid review_status: {review_status}")
    if not reading_status and not review_status:
        raise ValueError("mark requires --reading-status or --review-status")
    stamp = timestamp or now_iso()
    record = _find_record(state, key)
    history = record.setdefault("status_history", [])
    if reading_status:
        old = record.get("reading_status")
        record["reading_status"] = reading_status
        history.append(_history("mark", stamp, field="reading_status", old=old, new=reading_status))
    if review_status:
        old = record.get("review_status")
        record["review_status"] = review_status
        history.append(_history("mark", stamp, field="review_status", old=old, new=review_status))
    record["updated_at"] = stamp
    state["updated_at"] = stamp
    state["records"] = sorted([item for item in state.get("records", []) if isinstance(item, dict)], key=queue_sort_key)
    return state


def link_record(
    state: dict[str, Any],
    *,
    key: str,
    zotero_key: str | None = None,
    obsidian_note: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    if not zotero_key and not obsidian_note:
        raise ValueError("link requires --zotero-key or --obsidian-note")
    stamp = timestamp or now_iso()
    record = _find_record(state, key)
    history = record.setdefault("status_history", [])
    if zotero_key is not None:
        old = record.get("zotero_key")
        record["zotero_key"] = zotero_key
        history.append(_history("link", stamp, field="zotero_key", old=old, new=zotero_key))
    if obsidian_note is not None:
        old = record.get("obsidian_note_path")
        record["obsidian_note_path"] = obsidian_note
        history.append(_history("link", stamp, field="obsidian_note_path", old=old, new=obsidian_note))
    record["updated_at"] = stamp
    state["updated_at"] = stamp
    return state


def _frontmatter(title: str) -> str:
    return "\n".join(["---", "type: reading_queue_dashboard", f"title: \"{title}\"", "status: local", "---", ""])


def _record_line(record: dict[str, Any]) -> str:
    title = _clean(record.get("title") or "Untitled")
    key = _clean(record.get("dedup_key") or "")
    label = _clean(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or 0)
    status = _clean(record.get("reading_status") or "")
    review = _clean(record.get("review_status") or "")
    url = _clean(record.get("source_url") or "")
    return f"- {title}｜{label} / {score}｜{record.get('queue_priority')}｜{status}｜{review}｜key: {key}｜{url}"


def render_dashboard(state: dict[str, Any]) -> str:
    records = sorted([record for record in state.get("records", []) if isinstance(record, dict)], key=queue_sort_key)
    counts = Counter(str(record.get("queue_priority") or "LOW") for record in records)
    lines = [
        _frontmatter("Reading Dashboard"),
        "# Reading Dashboard",
        "",
        "## Summary",
        "",
        f"- Total records: {len(records)}",
        f"- Priority counts: {dict(sorted(counts.items()))}",
        "",
    ]
    for priority in QUEUE_PRIORITIES:
        lines.extend([f"## {priority}", ""])
        items = [record for record in records if record.get("queue_priority") == priority]
        lines.extend(_record_line(record) for record in items) if items else lines.append("- No records.")
        lines.append("")
    return "\n".join(lines)


def render_todo_read(state: dict[str, Any]) -> str:
    records = [
        record
        for record in state.get("records", [])
        if isinstance(record, dict) and record.get("reading_status") in {"TODO_READ", "READING"}
    ]
    lines = [_frontmatter("TODO Read"), "# TODO Read", ""]
    lines.extend(_record_line(record) for record in sorted(records, key=queue_sort_key)) if records else lines.append("- No records.")
    lines.append("")
    return "\n".join(lines)


def render_needs_replication(state: dict[str, Any]) -> str:
    records = [
        record
        for record in state.get("records", [])
        if isinstance(record, dict) and record.get("review_status") == "NEEDS_REPLICATION"
    ]
    lines = [_frontmatter("Needs Replication"), "# Needs Replication", ""]
    lines.extend(_record_line(record) for record in sorted(records, key=queue_sort_key)) if records else lines.append("- No records.")
    lines.append("")
    return "\n".join(lines)


def export_obsidian(state: dict[str, Any], output_dir: Path, *, dry_run: bool = False) -> list[Path]:
    targets = [
        (output_dir / "reading-dashboard.md", render_dashboard(state)),
        (output_dir / "todo-read.md", render_todo_read(state)),
        (output_dir / "needs-replication.md", render_needs_replication(state)),
    ]
    if dry_run:
        return [path for path, _ in targets]
    written: list[Path] = []
    for path, content in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def audit_state(state: dict[str, Any]) -> dict[str, Any]:
    records = [record for record in state.get("records", []) if isinstance(record, dict)]
    seen: set[str] = set()
    duplicate_keys: list[str] = []
    invalid_statuses: list[dict[str, str]] = []
    missing_title: list[str] = []
    missing_source_url: list[str] = []
    missing_seen_dates: list[str] = []
    for record in records:
        key = str(record.get("dedup_key") or "")
        if key in seen:
            duplicate_keys.append(key)
        seen.add(key)
        if record.get("reading_status") not in READING_STATUSES:
            invalid_statuses.append({"dedup_key": key, "field": "reading_status", "value": str(record.get("reading_status"))})
        if record.get("review_status") not in REVIEW_STATUSES:
            invalid_statuses.append({"dedup_key": key, "field": "review_status", "value": str(record.get("review_status"))})
        if not record.get("title"):
            missing_title.append(key)
        if not record.get("source_url"):
            missing_source_url.append(key)
        if not record.get("seen_dates"):
            missing_seen_dates.append(key)
    critical_errors = len(duplicate_keys) + len(invalid_statuses) + len(missing_title)
    warnings = len(missing_source_url) + len(missing_seen_dates)
    return {
        "schema_version": SCHEMA_VERSION,
        "records": len(records),
        "critical_errors": critical_errors,
        "warnings": warnings,
        "duplicate_keys": sorted(duplicate_keys),
        "invalid_statuses": invalid_statuses,
        "missing_title": sorted(missing_title),
        "missing_source_url": sorted(missing_source_url),
        "missing_seen_dates": sorted(missing_seen_dates),
    }


def _print_records(state: dict[str, Any]) -> None:
    records = sorted([record for record in state.get("records", []) if isinstance(record, dict)], key=queue_sort_key)
    for record in records:
        print(_record_line(record))


def _cmd_import(args: argparse.Namespace) -> int:
    state = load_state(args.state_path)
    candidates, metadata = load_import_candidates(
        days=args.days,
        from_date=args.from_date,
        to_date=args.to_date,
        data_dir=args.data_dir,
        weekly_json=args.weekly_json,
        artifact_manifest=args.artifact_manifest,
    )
    new_state, summary = import_queue(state, candidates)
    print(
        "Reading queue import: imported={imported}, updated={updated}, skipped={skipped}, total={total}, input={input_mode}".format(
            **summary,
            input_mode=metadata["input_mode"],
        )
    )
    if args.dry_run:
        print("DRY RUN: no state file written.")
        return 0
    new_state["last_import"] = metadata
    save_state(args.state_path, new_state)
    print(f"wrote: {args.state_path}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    _print_records(load_state(args.state_path))
    return 0


def _cmd_mark(args: argparse.Namespace) -> int:
    state = load_state(args.state_path)
    try:
        new_state = mark_status(
            state,
            key=args.key,
            reading_status=args.reading_status,
            review_status=args.review_status,
        )
    except (KeyError, ValueError) as exc:
        print(f"reading queue mark failed: {exc}", file=sys.stderr)
        return 1
    save_state(args.state_path, new_state)
    print(f"updated: {args.key}")
    return 0


def _cmd_link(args: argparse.Namespace) -> int:
    state = load_state(args.state_path)
    try:
        new_state = link_record(state, key=args.key, zotero_key=args.zotero_key, obsidian_note=args.obsidian_note)
    except (KeyError, ValueError) as exc:
        print(f"reading queue link failed: {exc}", file=sys.stderr)
        return 1
    save_state(args.state_path, new_state)
    print(f"linked: {args.key}")
    return 0


def _cmd_export_obsidian(args: argparse.Namespace) -> int:
    state = load_state(args.state_path)
    targets = export_obsidian(state, args.output_dir, dry_run=args.dry_run)
    if args.dry_run:
        print("DRY RUN: no Obsidian files written.")
        for path in targets:
            print(f"would write: {path}")
        return 0
    for path in targets:
        print(f"wrote: {path}")
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    result = audit_state(load_state(args.state_path))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.strict and result["critical_errors"]:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage local lattice digest reading queue state.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common_state = argparse.ArgumentParser(add_help=False)
    common_state.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)

    import_parser = subparsers.add_parser("import", parents=[common_state], help="Import candidates into the local reading queue.")
    import_parser.add_argument("--days", type=int, default=7)
    import_parser.add_argument("--from-date", default=None)
    import_parser.add_argument("--to-date", default=None)
    import_parser.add_argument("--data-dir", type=Path, default=Path("data"))
    import_parser.add_argument("--weekly-json", type=Path, default=None)
    import_parser.add_argument("--artifact-manifest", type=Path, default=None)
    import_parser.add_argument("--dry-run", action="store_true")
    import_parser.set_defaults(func=_cmd_import)

    list_parser = subparsers.add_parser("list", parents=[common_state], help="List reading queue records.")
    list_parser.set_defaults(func=_cmd_list)

    mark_parser = subparsers.add_parser("mark", parents=[common_state], help="Update reading or review status.")
    mark_parser.add_argument("--key", required=True)
    mark_parser.add_argument("--reading-status", choices=READING_STATUSES)
    mark_parser.add_argument("--review-status", choices=REVIEW_STATUSES)
    mark_parser.set_defaults(func=_cmd_mark)

    link_parser = subparsers.add_parser("link", parents=[common_state], help="Attach Zotero and Obsidian links.")
    link_parser.add_argument("--key", required=True)
    link_parser.add_argument("--zotero-key")
    link_parser.add_argument("--obsidian-note")
    link_parser.set_defaults(func=_cmd_link)

    export_parser = subparsers.add_parser("export-obsidian", parents=[common_state], help="Export Obsidian dashboards.")
    export_parser.add_argument("--output-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    export_parser.add_argument("--dry-run", action="store_true")
    export_parser.set_defaults(func=_cmd_export_obsidian)

    audit_parser = subparsers.add_parser("audit", parents=[common_state], help="Audit reading queue state.")
    audit_parser.add_argument("--strict", action="store_true")
    audit_parser.set_defaults(func=_cmd_audit)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
