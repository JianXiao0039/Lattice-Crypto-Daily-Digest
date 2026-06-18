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
    HIGH_PRIORITY,
    IDEA_BANK_CANDIDATES,
    LATTICE_REDUCTION_ATTACKS,
    LWE_FAMILY,
    PAPER_PLAN_CANDIDATES,
    PQC_STANDARDS,
    REPORT_BUCKET_ORDER,
    RESEARCH_SECTION_ORDER,
    SIS_NTRU_COMMITMENTS,
    TOPICAL_SECTION_ORDER,
    assign_report_buckets,
    assign_research_sections,
    candidate_reason,
)
from lattice_digest.models import make_paper_record
from lattice_digest.recommendation_rationale import build_recommendation_rationale
from lattice_digest.report_quality import (
    anchor_evidence_text,
    false_positive_risk_text,
    semantic_scholar_advisory_text,
    source_health_caveat_text,
)


SCHEMA_VERSION = 1
LABEL_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _date_range(start: date, end: date) -> list[date]:
    days = (end - start).days
    if days < 0:
        raise ValueError("from_date must be on or before to_date")
    return [start + timedelta(days=offset) for offset in range(days + 1)]


def _week_id(value: date) -> str:
    iso = value.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {"metadata": {}, "records": payload, "source_health": []}
    if isinstance(payload, dict):
        return payload
    return {"metadata": {}, "records": [], "source_health": []}


def _records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("records")
    return [item for item in records if isinstance(item, dict)] if isinstance(records, list) else []


def _normalize_title(value: str) -> str:
    text = value.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def dedup_key(record: dict[str, Any]) -> str:
    doi = str(record.get("doi") or "").strip().lower()
    if doi:
        return f"doi:{doi.removeprefix('https://doi.org/')}"
    arxiv_id = str(record.get("arxiv_id") or "").strip().lower()
    if arxiv_id:
        return f"arxiv:{re.sub('v[0-9]+$', '', arxiv_id)}"
    source_url = str(record.get("source_url") or record.get("url") or "").strip().lower()
    if source_url:
        return f"url:{source_url}"
    normalized_title = str(record.get("normalized_title") or "").strip().lower()
    title = normalized_title or _normalize_title(str(record.get("title") or "untitled"))
    return f"title:{title}"


def _publication_date(record: dict[str, Any]) -> str:
    return str(record.get("publication_date") or record.get("date") or record.get("update_date") or "")


def _date_rank(value: str) -> int:
    try:
        return -date.fromisoformat(value[:10]).toordinal()
    except ValueError:
        return 0


def _display_sort_key(record: dict[str, Any]) -> tuple[int, int, int, str]:
    label = str(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or 0)
    return (LABEL_ORDER.get(label, 9), -score, _date_rank(_publication_date(record)), str(record.get("title") or "").lower())


def _stable_sections(values: list[str]) -> list[str]:
    order = {name: index for index, name in enumerate(RESEARCH_SECTION_ORDER)}
    return sorted(
        {value for value in values if value in order},
        key=lambda value: (order.get(value, 999), value.lower()),
    )


def _stable_report_buckets(values: list[str]) -> list[str]:
    order = {name: index for index, name in enumerate(REPORT_BUCKET_ORDER)}
    return sorted(
        {value for value in values if value in order},
        key=lambda value: (order.get(value, 999), value.lower()),
    )


def _paper_record_from_dict(record: dict[str, Any]):
    return make_paper_record(
        title=str(record.get("title") or "untitled"),
        authors=[str(author) for author in record.get("authors", [])] if isinstance(record.get("authors"), list) else [],
        abstract=str(record.get("abstract") or ""),
        source=str(record.get("source") or "unknown"),
        source_url=str(record.get("source_url") or record.get("url") or ""),
        paper_id=record.get("paper_id"),
        arxiv_id=record.get("arxiv_id"),
        eprint_id=record.get("eprint_id"),
        doi=record.get("doi"),
        venue=record.get("venue"),
        publication_date=record.get("publication_date") or record.get("date"),
        update_date=record.get("update_date"),
        categories=[str(item) for item in record.get("categories", [])] if isinstance(record.get("categories"), list) else [],
        taxonomy_tags=[str(item) for item in record.get("taxonomy_tags", [])] if isinstance(record.get("taxonomy_tags"), list) else [],
        keywords_matched=[str(item) for item in record.get("keywords_matched", [])] if isinstance(record.get("keywords_matched"), list) else [],
        negative_keywords_matched=[str(item) for item in record.get("negative_keywords_matched", [])]
        if isinstance(record.get("negative_keywords_matched"), list)
        else [],
        relevance_score=int(record.get("relevance_score") or 0),
        relevance_label=str(record.get("relevance_label") or "D"),
        reason=str(record.get("reason") or record.get("reason_for_priority") or ""),
    )


def _research_sections(record: dict[str, Any]) -> list[str]:
    sections = record.get("research_sections")
    if isinstance(sections, list) and sections:
        topical = _stable_sections([str(section) for section in sections])
        if topical:
            return topical
    return assign_research_sections(_paper_record_from_dict(record))


def _report_buckets(record: dict[str, Any]) -> list[str]:
    buckets = record.get("report_buckets")
    if isinstance(buckets, list) and buckets:
        return _stable_report_buckets([str(bucket) for bucket in buckets])
    legacy_sections = record.get("research_sections")
    if isinstance(legacy_sections, list) and legacy_sections:
        legacy = _stable_report_buckets([str(section) for section in legacy_sections])
        if legacy:
            return legacy
    return assign_report_buckets(_paper_record_from_dict(record))


def _merge_record(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    seen_dates = sorted({*base.get("seen_dates", []), *incoming.get("seen_dates", [])})
    seen_sources = sorted({*base.get("seen_sources", []), *incoming.get("seen_sources", [])})
    merged["seen_dates"] = seen_dates
    merged["seen_sources"] = seen_sources
    merged["research_sections"] = _stable_sections(
        [*base.get("research_sections", []), *incoming.get("research_sections", [])]
    )
    merged["report_buckets"] = _stable_report_buckets(
        [*base.get("report_buckets", []), *incoming.get("report_buckets", [])]
    )
    if _display_sort_key(incoming) < _display_sort_key(base):
        for key, value in incoming.items():
            if key not in {"seen_dates", "seen_sources", "research_sections", "report_buckets"}:
                merged[key] = value
    return merged


def _source_health_summary(daily_payloads: list[tuple[date, dict[str, Any]]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for day, payload in daily_payloads:
        source_health = payload.get("source_health") or payload.get("metadata", {}).get("source_health")
        if isinstance(source_health, list):
            for item in source_health:
                if isinstance(item, dict):
                    rows.append(
                        {
                            "date": day.isoformat(),
                            "source": item.get("source"),
                            "status": item.get("health_status") or item.get("status"),
                            "final_count": item.get("final_count", item.get("final_records", 0)),
                            "error_type": item.get("error_type"),
                        }
                    )
    if not rows:
        return {"available": False, "sources": [], "note": "No source health data available in selected daily JSON files."}
    status_counts = Counter(str(row.get("status") or "unknown") for row in rows)
    sources = sorted({str(row.get("source") or "unknown") for row in rows})
    return {"available": True, "sources": sources, "status_counts": dict(sorted(status_counts.items())), "records": rows}


def load_daily_json(data_dir: Path, selected_days: list[date]) -> tuple[list[tuple[date, dict[str, Any]]], list[str]]:
    loaded: list[tuple[date, dict[str, Any]]] = []
    missing: list[str] = []
    for day in selected_days:
        path = data_dir / f"{day.isoformat()}.json"
        if not path.exists():
            missing.append(day.isoformat())
            continue
        loaded.append((day, _read_json(path)))
    return loaded, missing


def _prepare_record(record: dict[str, Any], day: date) -> dict[str, Any]:
    item = dict(record)
    item["seen_dates"] = [day.isoformat()]
    source = str(item.get("source") or "unknown")
    item["seen_sources"] = [source]
    item["research_sections"] = _research_sections(item)
    item["report_buckets"] = _report_buckets(item)
    item["dedup_key"] = dedup_key(item)
    return item


def aggregate_records(daily_payloads: list[tuple[date, dict[str, Any]]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for day, payload in daily_payloads:
        for record in _records(payload):
            item = _prepare_record(record, day)
            key = item["dedup_key"]
            by_key[key] = _merge_record(by_key[key], item) if key in by_key else item
    return sorted(by_key.values(), key=_display_sort_key)


def _section_map(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    sections = {name: [] for name in TOPICAL_SECTION_ORDER}
    for record in records:
        for section in record.get("research_sections", []):
            if section in sections:
                sections[section].append(record)
    return {name: sorted(items, key=_display_sort_key) for name, items in sections.items()}


def _report_bucket_map(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets = {name: [] for name in REPORT_BUCKET_ORDER}
    for record in records:
        for bucket in record.get("report_buckets", []):
            if bucket in buckets:
                buckets[bucket].append(record)
    return {name: sorted(items, key=_display_sort_key) for name, items in buckets.items()}


def _candidate_reason(record: dict[str, Any], section: str) -> str:
    paper = _paper_record_from_dict(record)
    paper.relevance_label = str(record.get("relevance_label") or "D")
    paper.relevance_score = int(record.get("relevance_score") or 0)
    paper.keywords_matched = [str(item) for item in record.get("keywords_matched", [])] if isinstance(record.get("keywords_matched"), list) else []
    paper.taxonomy_tags = [str(item) for item in record.get("taxonomy_tags", [])] if isinstance(record.get("taxonomy_tags"), list) else []
    return candidate_reason(paper, section)


def _idea_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        {
            "title": record.get("title"),
            "relevance_label": record.get("relevance_label"),
            "relevance_score": record.get("relevance_score"),
            "source_url": record.get("source_url") or record.get("url"),
            "research_sections": record.get("research_sections", []),
            "reason": _candidate_reason(record, IDEA_BANK_CANDIDATES),
        }
        for record in records
        if IDEA_BANK_CANDIDATES in record.get("report_buckets", [])
    ]
    return sorted(candidates, key=lambda item: (LABEL_ORDER.get(str(item.get("relevance_label")), 9), -int(item.get("relevance_score") or 0), str(item.get("title") or "").lower()))


def _paper_plan_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        {
            "title": record.get("title"),
            "relevance_label": record.get("relevance_label"),
            "relevance_score": record.get("relevance_score"),
            "source_url": record.get("source_url") or record.get("url"),
            "research_sections": record.get("research_sections", []),
            "reason": _candidate_reason(record, PAPER_PLAN_CANDIDATES),
        }
        for record in records
        if PAPER_PLAN_CANDIDATES in record.get("report_buckets", [])
    ]
    return sorted(candidates, key=lambda item: (LABEL_ORDER.get(str(item.get("relevance_label")), 9), -int(item.get("relevance_score") or 0), str(item.get("title") or "").lower()))


def build_weekly_synthesis(
    data_dir: Path,
    from_date: date,
    to_date: date,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    selected_days = _date_range(from_date, to_date)
    loaded_payloads, missing_days = load_daily_json(data_dir, selected_days)
    records = aggregate_records(loaded_payloads)
    sections = _section_map(records)
    report_buckets = _report_bucket_map(records)
    total_records = sum(len(_records(payload)) for _, payload in loaded_payloads)
    label_counts = Counter(str(record.get("relevance_label") or "D") for record in records)
    generated = generated_at or datetime.now(timezone.utc)
    return {
        "schema_version": 1,
        "week_id": _week_id(to_date),
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "generated_at": generated.isoformat(),
        "coverage": {
            "expected_days": len(selected_days),
            "loaded_days": [day.isoformat() for day, _ in loaded_payloads],
            "missing_days": missing_days,
            "total_records": total_records,
            "unique_records": len(records),
            "label_counts": dict(sorted(label_counts.items(), key=lambda item: LABEL_ORDER.get(item[0], 9))),
        },
        "label_counts": dict(sorted(label_counts.items(), key=lambda item: LABEL_ORDER.get(item[0], 9))),
        "sections": sections,
        "report_buckets": report_buckets,
        "idea_bank_candidates": _idea_candidates(records),
        "paper_plan_candidates": _paper_plan_candidates(records),
        "source_health_summary": _source_health_summary(loaded_payloads),
    }


def _record_line(record: dict[str, Any]) -> str:
    title = str(record.get("title") or "untitled")
    label = str(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or 0)
    url = str(record.get("source_url") or record.get("url") or "unknown")
    sources = ", ".join(record.get("seen_sources", [])) if isinstance(record.get("seen_sources"), list) else str(record.get("source") or "unknown")
    dates = ", ".join(record.get("seen_dates", [])) if isinstance(record.get("seen_dates"), list) else ""
    rationale = build_recommendation_rationale(record)
    todo_verify = "；".join(rationale.todo_verify) if rationale.todo_verify else rationale.caveat
    return (
        f"- {title}｜{label} / {score}｜sources: {sources}｜seen: {dates}｜{url}\n"
        f"  - {anchor_evidence_text(record)}\n"
        f"  - False-positive risk: {false_positive_risk_text(record)}\n"
        f"  - Semantic Scholar advisory: {semantic_scholar_advisory_text(record)}\n"
        f"  - Rationale: {rationale.problem_summary} {rationale.radar_relevance} {rationale.recommendation_reason}\n"
        f"  - Evidence basis: {', '.join(rationale.evidence_basis)}；confidence={rationale.confidence}；TODO_VERIFY: {todo_verify}"
    )


def render_markdown(payload: dict[str, Any]) -> str:
    coverage = payload["coverage"]
    lines = [
        f"# Weekly Research Synthesis - {payload['week_id']}",
        "",
        "## Executive Summary",
        "",
        f"- Window: {payload['from_date']} .. {payload['to_date']}",
        f"- Expected days: {coverage['expected_days']}",
        f"- Loaded days: {len(coverage['loaded_days'])}",
        f"- Missing days: {len(coverage['missing_days'])}",
        f"- Total records: {coverage['total_records']}",
        f"- Unique records: {coverage['unique_records']}",
        f"- Label counts: {payload['label_counts']}",
        "",
    ]
    section_titles = ["High-Priority Papers This Week", *TOPICAL_SECTION_ORDER]
    section_lookup = {"High-Priority Papers This Week": "High-Priority Papers", **{section: section for section in TOPICAL_SECTION_ORDER}}
    sections = payload.get("sections", {})
    report_buckets = payload.get("report_buckets", {})
    top_a = [
        record
        for bucket_records in (report_buckets.values() if isinstance(report_buckets, dict) else [])
        for record in (bucket_records if isinstance(bucket_records, list) else [])
        if str(record.get("relevance_label") or "D") == "A"
    ]
    top_a = sorted({dedup_key(record): record for record in top_a}.values(), key=_display_sort_key)[:5]
    lines.extend(["## Top A-level Papers", ""])
    if top_a:
        lines.append("- These are surfaced for manual inspection; citation metadata is advisory only.")
        for record in top_a:
            lines.append(_record_line(record))
        lines.append("")
    else:
        lines.extend(["- No A-level papers in the selected window.", ""])
    for title in section_titles:
        lines.extend([f"## {title}", ""])
        if title == "High-Priority Papers This Week":
            records = report_buckets.get(HIGH_PRIORITY, []) if isinstance(report_buckets, dict) else []
        else:
            records = sections.get(section_lookup[title], []) if isinstance(sections, dict) else []
        if not records:
            lines.extend(["- No matching records.", ""])
            continue
        for record in records:
            lines.append(_record_line(record))
        lines.append("")

    for title, key in [("Idea Bank Candidates", "idea_bank_candidates"), ("Paper Plan Candidates", "paper_plan_candidates")]:
        lines.extend([f"## {title}", ""])
        candidates = payload.get(key, [])
        if not candidates:
            lines.extend(["- No candidates.", ""])
            continue
        for item in candidates:
            lines.append(
                f"- {item.get('title')}｜{item.get('relevance_label')} / {item.get('relevance_score')}｜{item.get('reason')}"
            )
        lines.append("")

    lines.extend(["## Source Health Summary", ""])
    health = payload.get("source_health_summary", {})
    if not isinstance(health, dict) or not health.get("available"):
        lines.extend(["- No source health data available.", ""])
    else:
        lines.append(f"- Sources: {', '.join(health.get('sources', []))}")
        lines.append(f"- Status counts: {health.get('status_counts', {})}")
        lines.append(f"- Caveat: {source_health_caveat_text(health)}")
        lines.append("")

    lines.extend(
        [
            "## Coverage Notes",
            "",
            f"- expected_days: {coverage['expected_days']}",
            f"- loaded_days: {coverage['loaded_days']}",
            f"- missing_days: {coverage['missing_days']}",
            f"- total_records: {coverage['total_records']}",
            f"- unique_records: {coverage['unique_records']}",
            f"- label_counts: {coverage['label_counts']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_weekly_outputs(payload: dict[str, Any], json_output_dir: Path, digest_output_dir: Path) -> tuple[Path, Path]:
    json_output_dir.mkdir(parents=True, exist_ok=True)
    digest_output_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_output_dir / f"{payload['week_id']}.json"
    markdown_path = digest_output_dir / f"{payload['week_id']}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, markdown_path


def _window_from_args(args: argparse.Namespace) -> tuple[date, date]:
    if args.from_date and args.to_date:
        return _parse_date(args.from_date), _parse_date(args.to_date)
    to_date = _parse_date(args.to_date) if args.to_date else datetime.now().date()
    days = int(args.days or 7)
    return to_date - timedelta(days=days - 1), to_date


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly research synthesis from daily digest JSON files.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--from-date", default=None)
    parser.add_argument("--to-date", default=None)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--json-output-dir", type=Path, default=Path("data") / "weekly")
    parser.add_argument("--digest-output-dir", type=Path, default=Path("digests") / "weekly")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from_date, to_date = _window_from_args(args)
    payload = build_weekly_synthesis(args.data_dir, from_date, to_date)
    print(
        "Weekly synthesis {week}: {unique} unique records, missing_days={missing}".format(
            week=payload["week_id"],
            unique=payload["coverage"]["unique_records"],
            missing=len(payload["coverage"]["missing_days"]),
        )
    )
    if args.dry_run:
        print("DRY RUN: no weekly output files were written.")
        print(f"JSON target: {args.json_output_dir / (payload['week_id'] + '.json')}")
        print(f"Markdown target: {args.digest_output_dir / (payload['week_id'] + '.md')}")
        return 0
    json_path, markdown_path = write_weekly_outputs(payload, args.json_output_dir, args.digest_output_dir)
    print(json_path)
    print(markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
