from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from lattice_digest.digest_sections import (
    AI_LATTICE,
    IDEA_BANK_CANDIDATES,
    LATTICE_REDUCTION_ATTACKS,
    LATTICE_ADVANCED_PRIMITIVES,
    LATTICE_ISOMORPHISM,
    LATTICE_PRIVACY_FL,
    LWE_FAMILY,
    PAPER_PLAN_CANDIDATES,
    SIS_NTRU_COMMITMENTS,
    REGISTRATION_ENCRYPTION,
)
from lattice_digest.weekly_synthesis import build_weekly_synthesis, dedup_key
from lattice_digest.zotero_compat import record_to_zotero_item, render_bibtex, render_ris


SCHEMA_VERSION = 1
LABEL_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}
TRACK_PRIORITY = {
    AI_LATTICE: 0,
    LWE_FAMILY: 1,
    LATTICE_REDUCTION_ATTACKS: 2,
    SIS_NTRU_COMMITMENTS: 3,
    LATTICE_ADVANCED_PRIMITIVES: 4,
    REGISTRATION_ENCRYPTION: 5,
    LATTICE_PRIVACY_FL: 6,
    LATTICE_ISOMORPHISM: 7,
    "PQC Standards / ML-KEM / ML-DSA / Falcon": 8,
    "Implementation / Side-channel / Systems": 9,
}
DEFAULT_FORMATS = ("obsidian", "advisor", "backlog", "zotero")


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _week_id(value: date) -> str:
    iso = value.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _window(days: int | None, from_date: str | None, to_date: str | None) -> tuple[date, date]:
    if from_date and to_date:
        return _parse_date(from_date), _parse_date(to_date)
    end = _parse_date(to_date) if to_date else datetime.now().date()
    length = int(days or 7)
    return end - timedelta(days=length - 1), end


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _default_weekly_path(daily_data_dir: Path, to_date: date) -> Path:
    return daily_data_dir / "weekly" / f"{_week_id(to_date)}.json"


def _load_weekly_payload(
    *,
    weekly_json: Path | None,
    daily_data_dir: Path,
    from_date: date,
    to_date: date,
) -> tuple[dict[str, Any], list[Path], str]:
    candidates = []
    if weekly_json:
        candidates.append(weekly_json)
    candidates.append(_default_weekly_path(daily_data_dir, to_date))
    for path in candidates:
        if path and path.exists():
            return _read_json(path), [path], "weekly_json"
    payload = build_weekly_synthesis(daily_data_dir, from_date, to_date)
    source_files = [
        daily_data_dir / f"{(from_date + timedelta(days=offset)).isoformat()}.json"
        for offset in range((to_date - from_date).days + 1)
        if (daily_data_dir / f"{(from_date + timedelta(days=offset)).isoformat()}.json").exists()
    ]
    return payload, source_files, "daily_json_fallback"


def _records_from_weekly(payload: dict[str, Any]) -> list[dict[str, Any]]:
    sections = payload.get("sections")
    records: dict[str, dict[str, Any]] = {}
    if isinstance(sections, dict):
        for section_records in sections.values():
            if not isinstance(section_records, list):
                continue
            for record in section_records:
                if not isinstance(record, dict):
                    continue
                key = str(record.get("dedup_key") or dedup_key(record))
                records[key] = record
    report_buckets = payload.get("report_buckets")
    if isinstance(report_buckets, dict):
        for bucket_name, bucket_records in report_buckets.items():
            if not isinstance(bucket_records, list):
                continue
            for record in bucket_records:
                if not isinstance(record, dict):
                    continue
                key = str(record.get("dedup_key") or dedup_key(record))
                merged = dict(records.get(key, record))
                existing = merged.get("report_buckets") if isinstance(merged.get("report_buckets"), list) else []
                merged["report_buckets"] = sorted({*existing, str(bucket_name)})
                records[key] = merged
    return sorted(records.values(), key=reading_sort_key)


def _date_rank(record: dict[str, Any]) -> int:
    raw = str(record.get("publication_date") or record.get("date") or record.get("update_date") or "")
    try:
        return -date.fromisoformat(raw[:10]).toordinal()
    except ValueError:
        return 0


def _track_rank(record: dict[str, Any]) -> int:
    sections = record.get("research_sections")
    values = [str(item) for item in sections] if isinstance(sections, list) else []
    if not values:
        return 99
    return min(TRACK_PRIORITY.get(value, 99) for value in values)


def reading_sort_key(record: dict[str, Any]) -> tuple[int, int, int, int, str]:
    label = str(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or record.get("reading_priority_score") or 0)
    return (LABEL_ORDER.get(label, 9), -score, _track_rank(record), _date_rank(record), str(record.get("title") or "").lower())


def _status_for(record: dict[str, Any]) -> str:
    label = str(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or record.get("reading_priority_score") or 0)
    if label == "A" and score >= 80:
        return "Worth reading"
    if label in {"A", "B"} and score >= 60:
        return "Candidate"
    if label == "C":
        return "Potentially relevant"
    return "IGNORE_FOR_NOW"


def _action_for(record: dict[str, Any]) -> str:
    label = str(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or record.get("reading_priority_score") or 0)
    if label == "A" and score >= 80:
        return "TODO_READ"
    if label in {"A", "B", "C"}:
        return "TODO_SKIM"
    return "TODO_VERIFY"


def _clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("contentReference", "").replace("oaicite", "").replace("id=", "")
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())


def _record_line(record: dict[str, Any]) -> str:
    title = _clean(record.get("title") or "Untitled")
    label = _clean(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or record.get("reading_priority_score") or 0)
    seen_sources = record.get("seen_sources")
    source = _clean(
        record.get("source")
        or (", ".join(str(item) for item in seen_sources) if isinstance(seen_sources, list) else "")
        or "unknown"
    )
    url = _clean(record.get("source_url") or record.get("url") or "unknown")
    return f"- [{_action_for(record)}] {title}｜{label} / {score}｜{source}｜{url}"


def _frontmatter(title: str, from_date: date, to_date: date) -> str:
    return "\n".join(
        [
            "---",
            "type: research_artifact_export",
            f"title: \"{title}\"",
            f"from_date: \"{from_date.isoformat()}\"",
            f"to_date: \"{to_date.isoformat()}\"",
            "status: draft",
            "---",
            "",
        ]
    )


def render_obsidian_weekly(payload: dict[str, Any], records: list[dict[str, Any]], from_date: date, to_date: date) -> str:
    lines = [
        _frontmatter("Weekly Research Synthesis", from_date, to_date),
        "# Weekly Research Synthesis",
        "",
        "## 1. Scope",
        "",
        f"- Window: {from_date.isoformat()} .. {to_date.isoformat()}",
        f"- Unique records: {len(records)}",
        "- This note repackages existing digest metadata only.",
        "",
        "## 2. High Priority",
        "",
    ]
    high = [record for record in records if str(record.get("relevance_label")) == "A"][:10]
    lines.extend(_record_line(record) for record in high) if high else lines.append("- No high-priority records.")
    lines.extend(["", "## 3. Research Tracks", ""])
    for section in [AI_LATTICE, LWE_FAMILY, LATTICE_REDUCTION_ATTACKS, SIS_NTRU_COMMITMENTS]:
        lines.append(f"### {section}")
        matches = [record for record in records if section in record.get("research_sections", [])][:8]
        lines.extend(_record_line(record) for record in matches) if matches else lines.append("- No matching records.")
        lines.append("")
    return "\n".join(lines)


def render_reading_queue(records: list[dict[str, Any]], from_date: date, to_date: date) -> str:
    lines = [_frontmatter("Reading Queue", from_date, to_date), "# Reading Queue", ""]
    for record in records:
        lines.append(_record_line(record))
        lines.append(f"  - Status: {_status_for(record)}")
        lines.append(f"  - Sections: {', '.join(record.get('research_sections', [])) if isinstance(record.get('research_sections'), list) else 'unknown'}")
        lines.append(f"  - Report buckets: {', '.join(record.get('report_buckets', [])) if isinstance(record.get('report_buckets'), list) else 'none'}")
    lines.append("")
    return "\n".join(lines)


def render_candidate_note(title: str, candidates: list[dict[str, Any]], from_date: date, to_date: date) -> str:
    lines = [_frontmatter(title, from_date, to_date), f"# {title}", ""]
    if not candidates:
        lines.append("- No candidates.")
    for item in candidates:
        lines.append(f"- {_clean(item.get('title'))}｜{item.get('relevance_label')} / {item.get('relevance_score')}")
        lines.append(f"  - Candidate reason: {_clean(item.get('reason')) or 'Needs verification'}")
        lines.append(f"  - URL: {_clean(item.get('source_url')) or 'unknown'}")
    lines.append("")
    return "\n".join(lines)


def render_advisor_update(payload: dict[str, Any], records: list[dict[str, Any]], from_date: date, to_date: date) -> str:
    top = records[:5]
    lines = [
        "# Advisor Weekly Update Draft",
        "",
        "> Draft only. This update is generated from unread or partially reviewed digest metadata. It does not claim that any paper proves a result.",
        "",
        "## 1. Window",
        "",
        f"- {from_date.isoformat()} .. {to_date.isoformat()}",
        f"- Unique records considered: {len(records)}",
        "",
        "## 2. Potentially Worth Discussing",
        "",
    ]
    if not top:
        lines.append("- No records selected for discussion.")
    for record in top:
        lines.append(_record_line(record))
        lines.append("  - Cautious note: Needs verification before claiming novelty, correctness, or security implications.")
    lines.extend(
        [
            "",
            "## 3. Questions For Discussion",
            "",
            "- Which candidates are worth reading first?",
            "- Are any Module-SIS / commitment / chameleon-hash items close enough to short-term paper planning?",
            "- Are any AI4Lattice items useful as classical attack subroutines rather than end-to-end claims?",
            "- Should any item be ignored for now because it is only tangentially related?",
            "",
        ]
    )
    return "\n".join(lines)


def render_backlog(records: list[dict[str, Any]], from_date: date, to_date: date) -> str:
    lines = [
        "# Paper Reading Backlog",
        "",
        f"- Window: {from_date.isoformat()} .. {to_date.isoformat()}",
        "- Ordering: label, score, research track, publication date, title.",
        "",
    ]
    lines.extend(_record_line(record) for record in records) if records else lines.append("- No records.")
    lines.append("")
    return "\n".join(lines)


def _zotero_record(record: dict[str, Any]) -> dict[str, Any]:
    item = dict(record)
    item["url"] = item.get("source_url") or item.get("url")
    item["date"] = item.get("publication_date") or item.get("date") or item.get("update_date")
    item["reading_priority_score"] = int(item.get("reading_priority_score") or item.get("relevance_score") or 0)
    item["priority_label"] = item.get("priority_label") or item.get("relevance_label")
    item["reason_for_priority"] = item.get("reason_for_priority") or "Needs verification from original paper."
    return item


def _write(path: Path, content: str, written: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    written.append(path)


def _write_json(path: Path, payload: object, written: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(path)


def parse_formats(raw: str | None) -> list[str]:
    values = raw or ",".join(DEFAULT_FORMATS)
    result: list[str] = []
    for part in values.split(","):
        value = part.strip().lower()
        if value:
            result.append(value)
    return list(dict.fromkeys(result))


def build_export_plan(
    *,
    weekly_json: Path | None,
    daily_data_dir: Path,
    output_dir: Path,
    from_date: date,
    to_date: date,
    formats: list[str],
    generated_at: datetime | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    payload, source_files, input_mode = _load_weekly_payload(
        weekly_json=weekly_json,
        daily_data_dir=daily_data_dir,
        from_date=from_date,
        to_date=to_date,
    )
    records = _records_from_weekly(payload)
    export_date = to_date.isoformat()
    export_root = output_dir / export_date
    generated = generated_at or datetime.now(timezone.utc)
    requested = set(formats)
    output_files: list[str] = [
        str(export_root / "manifest.json"),
        str(export_root / "README.md"),
    ]
    if "obsidian" in requested:
        output_files.extend(
            str(export_root / relative)
            for relative in [
                Path("obsidian") / "weekly-research-synthesis.md",
                Path("obsidian") / "reading-queue.md",
                Path("obsidian") / "idea-bank-candidates.md",
                Path("obsidian") / "paper-plan-candidates.md",
            ]
        )
    if "advisor" in requested:
        output_files.append(str(export_root / "advisor" / "weekly-update-draft.md"))
    if "backlog" in requested:
        output_files.append(str(export_root / "backlog" / "paper-reading-backlog.md"))
    if "zotero" in requested:
        output_files.extend(
            str(export_root / relative)
            for relative in [
                Path("zotero") / "reading-queue.json",
                Path("zotero") / "reading-queue.bib",
                Path("zotero") / "reading-queue.ris",
            ]
        )
    counts = {
        "records": len(records),
        "idea_bank_candidates": len(payload.get("idea_bank_candidates", [])),
        "paper_plan_candidates": len(payload.get("paper_plan_candidates", [])),
        "formats": len(formats),
    }
    manifest = {
        "schema_version": 1,
        "export_date": export_date,
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "generated_at": generated.isoformat(),
        "source_files": [str(path) for path in source_files],
        "input_mode": input_mode,
        "output_files": output_files,
        "counts": counts,
        "dry_run": dry_run,
    }
    return {"payload": payload, "records": records, "export_root": export_root, "manifest": manifest, "formats": formats}


def write_export_pack(plan: dict[str, Any]) -> list[Path]:
    payload = plan["payload"]
    records = plan["records"]
    export_root: Path = plan["export_root"]
    manifest = plan["manifest"]
    formats = set(plan["formats"])
    from_date = date.fromisoformat(manifest["from_date"])
    to_date = date.fromisoformat(manifest["to_date"])
    written: list[Path] = []
    _write_json(export_root / "manifest.json", manifest, written)
    _write(
        export_root / "README.md",
        "\n".join(
            [
                "# Research Artifact Export Pack",
                "",
                f"- Window: {manifest['from_date']} .. {manifest['to_date']}",
                f"- Records: {manifest['counts']['records']}",
                "- This pack repackages existing digest metadata. It does not add new claims.",
                "",
            ]
        ),
        written,
    )
    if "obsidian" in formats:
        _write(export_root / "obsidian" / "weekly-research-synthesis.md", render_obsidian_weekly(payload, records, from_date, to_date), written)
        _write(export_root / "obsidian" / "reading-queue.md", render_reading_queue(records, from_date, to_date), written)
        _write(
            export_root / "obsidian" / "idea-bank-candidates.md",
            render_candidate_note("Idea Bank Candidates", payload.get("idea_bank_candidates", []), from_date, to_date),
            written,
        )
        _write(
            export_root / "obsidian" / "paper-plan-candidates.md",
            render_candidate_note("Paper Plan Candidates", payload.get("paper_plan_candidates", []), from_date, to_date),
            written,
        )
    if "advisor" in formats:
        _write(export_root / "advisor" / "weekly-update-draft.md", render_advisor_update(payload, records, from_date, to_date), written)
    if "backlog" in formats:
        _write(export_root / "backlog" / "paper-reading-backlog.md", render_backlog(records, from_date, to_date), written)
    if "zotero" in formats:
        zotero_records = [_zotero_record(record) for record in records if str(record.get("relevance_label") or "D") in {"A", "B"}]
        _write_json(export_root / "zotero" / "reading-queue.json", [record_to_zotero_item(record) for record in zotero_records], written)
        _write(export_root / "zotero" / "reading-queue.bib", render_bibtex(zotero_records), written)
        _write(export_root / "zotero" / "reading-queue.ris", render_ris(zotero_records), written)
    return written


def generate_research_artifact_export(
    *,
    days: int | None = 7,
    from_date: str | None = None,
    to_date: str | None = None,
    weekly_json: Path | None = None,
    daily_data_dir: Path = Path("data"),
    output_dir: Path = Path("exports") / "research-artifacts",
    formats: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    start, end = _window(days, from_date, to_date)
    parsed_formats = parse_formats(formats)
    plan = build_export_plan(
        weekly_json=weekly_json,
        daily_data_dir=daily_data_dir,
        output_dir=output_dir,
        from_date=start,
        to_date=end,
        formats=parsed_formats,
        dry_run=dry_run,
    )
    if dry_run:
        return {**plan, "written_paths": []}
    written = write_export_pack(plan)
    return {**plan, "written_paths": written}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a research artifact export pack from existing daily/weekly JSON.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--from-date", default=None)
    parser.add_argument("--to-date", default=None)
    parser.add_argument("--weekly-json", type=Path, default=None)
    parser.add_argument("--daily-data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("exports") / "research-artifacts")
    parser.add_argument("--formats", default="obsidian,advisor,backlog,zotero")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = generate_research_artifact_export(
        days=args.days,
        from_date=args.from_date,
        to_date=args.to_date,
        weekly_json=args.weekly_json,
        daily_data_dir=args.daily_data_dir,
        output_dir=args.output_dir,
        formats=args.formats,
        dry_run=args.dry_run,
    )
    manifest = result["manifest"]
    print(
        "Research artifact export {date}: {records} records, formats={formats}".format(
            date=manifest["export_date"],
            records=manifest["counts"]["records"],
            formats=", ".join(result["formats"]),
        )
    )
    print(f"output dir: {result['export_root']}")
    if args.dry_run:
        print("DRY RUN: no files written")
    else:
        for path in result["written_paths"]:
            print(f"wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
