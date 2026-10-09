from __future__ import annotations

from lattice_digest.publication_events import period_views, normalize_period_inputs

import argparse
import calendar
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from lattice_digest.recommendation_rationale import (
    build_bilingual_rationale,
    build_recommendation_rationale,
    format_bilingual_rationale_markdown,
)
from lattice_digest.artifact_paths import (
    daily_data_path,
    legacy_daily_data_candidates,
    legacy_weekly_data_candidates,
    monthly_data_path,
    monthly_digest_path,
    resolve_existing,
    weekly_data_path,
)
from lattice_digest.weekly_synthesis import LABEL_ORDER, dedup_key
from lattice_digest.reading_actions import ReadingAction, reading_action, has_source_content
from lattice_digest.daily_inputs import assess_daily_input, summarize_daily_inputs


SCHEMA_VERSION = 1
EXPECTED_SOURCES = ("arxiv", "iacr_eprint", "dblp", "crossref", "openalex", "semantic_scholar")

DIRECTION_RULES: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    (
        "LWE / RLWE / MLWE",
        ("lwe", "rlwe", "mlwe", "module-lwe", "module lwe", "ring-lwe", "ring lwe"),
        "core",
        "These papers affect lattice assumptions, parameter reasoning, and PQC security estimates.",
    ),
    (
        "SIS / Module-SIS",
        ("sis", "module-sis", "module sis", "msis", "commitment", "chameleon hash"),
        "core",
        "These papers are relevant to lattice commitments, signatures, trapdoors, and Module-SIS primitives.",
    ),
    (
        "lattice reduction / BKZ / attacks",
        ("bkz", "lll", "g6k", "sieving", "enumeration", "primal attack", "dual attack", "hybrid attack", "cryptanalysis"),
        "core",
        "These papers shape attack-cost models and reproducible lattice-cryptanalysis baselines.",
    ),
    (
        "ML-KEM / ML-DSA / PQC implementation",
        ("ml-kem", "kyber", "ml-dsa", "dilithium", "falcon", "pqc implementation", "side-channel", "fault attack"),
        "core",
        "These papers support PQC deployment, implementation security, and standard-scheme reading queues.",
    ),
    (
        "FHE / CKKS / lattice ZK / commitments",
        ("fhe", "fully homomorphic", "ckks", "bfv", "bgv", "tfhe", "zero-knowledge", "zk", "commitment"),
        "peripheral",
        "These papers may support FHE, lattice-ZK, and commitment background, but application papers need careful scoping.",
    ),
    (
        "AI-assisted lattice cryptanalysis",
        ("ai-assisted", "neural", "machine learning", "transformer", "swin", "learning-guided", "coordinate selection"),
        "core",
        "These papers can inform AI4Lattice experiments only when tied to LWE/RLWE/MLWE, BKZ, or cryptanalysis.",
    ),
    (
        "other PQC / adjacent crypto",
        ("post-quantum", "pqc", "quantum-safe", "cryptography", "signature", "encryption"),
        "background",
        "These papers are useful context when they connect back to lattice/PQC radar decisions.",
    ),
)


def parse_month(value: str) -> tuple[date, date]:
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ValueError("month must use YYYY-MM")
    year, month = (int(part) for part in value.split("-", 1))
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def month_days(start: date, end: date) -> list[date]:
    days = (end - start).days
    return [start + timedelta(days=offset) for offset in range(days + 1)]


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        return {"metadata": {}, "records": payload, "source_health": []}
    return {"metadata": {}, "records": [], "source_health": []}


def _records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("records")
    return [record for record in records if isinstance(record, dict)] if isinstance(records, list) else []


def _status(item: dict[str, Any]) -> str:
    raw = str(item.get("health_status") or item.get("status") or "").lower()
    if raw in {"green", "yellow", "red"}:
        return raw
    if item.get("errors") or item.get("error_type") or item.get("error_message"):
        return "red"
    if item.get("warnings"):
        return "yellow"
    if item.get("final_count") or item.get("final_records"):
        return "green"
    return "unknown"


def _display_sort_key(record: dict[str, Any]) -> tuple[int, int, int, int, str]:
    label = str(record.get("relevance_label") or "D")
    score = int(record.get("relevance_score") or 0)
    priority = int(record.get("reading_priority_score") or record.get("reading_priority") or 0)
    seen_dates = record.get("seen_dates") if isinstance(record.get("seen_dates"), list) else []
    seen_date = str(seen_dates[0] if seen_dates else record.get("publication_date") or record.get("date") or "")
    try:
        date_rank = -date.fromisoformat(seen_date[:10]).toordinal()
    except ValueError:
        date_rank = 0
    return (LABEL_ORDER.get(label, 9), -score, -priority, date_rank, str(record.get("title") or "").lower())


def _merge_record(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    merged["seen_dates"] = sorted({*base.get("seen_dates", []), *incoming.get("seen_dates", [])})
    merged["seen_sources"] = sorted({*base.get("seen_sources", []), *incoming.get("seen_sources", [])})
    if _display_sort_key(incoming) < _display_sort_key(base):
        for key, value in incoming.items():
            if key not in {"seen_dates", "seen_sources"}:
                merged[key] = value
    return merged


def _prepare_record(record: dict[str, Any], day: date) -> dict[str, Any]:
    item = dict(record)
    item["seen_dates"] = [day.isoformat()]
    item["seen_sources"] = [str(item.get("source") or "unknown")]
    return item


def aggregate_records(daily_payloads: list[tuple[date, dict[str, Any]]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for day, payload in daily_payloads:
        from lattice_digest.publication_events import period_event_rows
        for record in period_event_rows(payload):
            item = _prepare_record(record, day)
            key = dedup_key(item)
            by_key[key] = _merge_record(by_key[key], item) if key in by_key else item
    return sorted(by_key.values(), key=_display_sort_key)


def direction_for_record(record: dict[str, Any]) -> str:
    from lattice_digest.evidence_contract import positive_source_text, source_scope_score, Scope
    if source_scope_score(record)[0] in {Scope.OUT_OF_SCOPE,Scope.LATTICE_METHOD_IN_ADJACENT_CRYPTO,Scope.ADJACENT_PQC}:
        return 'other PQC / adjacent crypto'
    text = positive_source_text(record)
    for direction, terms, _, _ in DIRECTION_RULES:
        if any(_contains_term(text, term) for term in terms):
            return direction
    return "other PQC / adjacent crypto"


def _contains_term(text: str, term: str) -> bool:
    escaped = re.escape(term.lower())
    escaped = escaped.replace(r"\ ", r"[\s-]+")
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None


def build_source_health_summary(daily_payloads: list[tuple[date, dict[str, Any]]]) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {
        source: {
            "source": source,
            "green": 0,
            "yellow": 0,
            "red": 0,
            "unknown": 0,
            "retrieval_count": 0,
            "failure_types": {},
            "days_observed": 0,
            "impact": "no source-health records found for this month",
        }
        for source in EXPECTED_SOURCES
    }
    source_starved_days: list[str] = []
    for day, payload in daily_payloads:
        health = payload.get("source_health")
        if not isinstance(health, list):
            continue
        day_statuses: list[str] = []
        for item in health:
            if not isinstance(item, dict):
                continue
            source = str(item.get("source") or "unknown")
            rows.setdefault(
                source,
                {
                    "source": source,
                    "green": 0,
                    "yellow": 0,
                    "red": 0,
                    "unknown": 0,
                    "retrieval_count": 0,
                    "failure_types": {},
                    "days_observed": 0,
                    "impact": "",
                },
            )
            status = _status(item)
            day_statuses.append(status)
            rows[source][status] += 1
            rows[source]["days_observed"] += 1
            rows[source]["retrieval_count"] += int(item.get("final_count") or item.get("final_records") or 0)
            error_type = str(item.get("error_type") or "").strip()
            if error_type:
                failures = Counter(rows[source]["failure_types"])
                failures[error_type] += 1
                rows[source]["failure_types"] = dict(sorted(failures.items()))
        if day_statuses and all(status == "red" for status in day_statuses) and not _records(payload):
            source_starved_days.append(day.isoformat())
    for source, row in rows.items():
        if row["days_observed"] == 0:
            continue
        if row["red"]:
            row["impact"] = "degraded monthly evidence; verify missing papers before treating empty days as quiet"
        elif row["yellow"]:
            row["impact"] = "usable with degraded source-health caveats"
        else:
            row["impact"] = "usable monthly source evidence"
    return {
        "sources": [rows[source] for source in sorted(rows)],
        "source_starved_days": source_starved_days,
        "source_starved": bool(source_starved_days),
    }


def _reading_bucket(record: dict[str, Any]) -> str:
    from lattice_digest.evidence_contract import source_scope_score, Scope
    if has_source_content(record) and source_scope_score(record)[0]==Scope.OUT_OF_SCOPE:
        return ReadingAction.IGNORE.value
    return reading_action(record).value


def _rationale_payload(record: dict[str, Any]) -> dict[str, Any]:
    if not has_source_content(record):
        return {'problem': 'TODO_VERIFY: only bibliographic metadata is available.',
                'method': 'TODO_VERIFY: source method evidence unavailable.',
                'contribution': 'TODO_VERIFY: source contribution evidence unavailable.',
                'radar_relevance': 'Metadata navigation only; relevance requires source verification.',
                'reading_action': _reading_bucket(record), 'evidence_basis': ['METADATA_ONLY'],
                'confidence': 'METADATA_ONLY', 'todo_verify': ['Obtain source abstract or independent source excerpt.'],
                'caveat': 'Metadata and classifier keywords do not establish research claims.', 'bilingual': None}
    rationale = build_recommendation_rationale(record).to_dict()
    bilingual = build_bilingual_rationale(record, top_paper=True).to_dict()
    return {
        "problem": rationale["problem_summary"],
        "method": rationale["method_summary"],
        "contribution": rationale["contribution_summary"],
        "radar_relevance": rationale["radar_relevance"],
        "reading_action": _reading_bucket(record),
        "evidence_basis": rationale["evidence_basis"],
        "confidence": rationale["confidence"],
        "todo_verify": rationale["todo_verify"],
        "caveat": rationale["caveat"],
        "bilingual": bilingual,
    }


def build_core_paper(record: dict[str, Any]) -> dict[str, Any]:
    from lattice_digest.evidence_contract import source_scope_score, score_to_label
    scope,score=source_scope_score(record)
    return {
        'validated_label':score_to_label(score), 'validated_score':score, 'validated_scope':str(scope),
        "title": record.get("title") or "untitled",
        "source": record.get("source") or "unknown",
        "source_url": record.get("source_url") or record.get("url") or "",
        "relevance_label": record.get("relevance_label") or "D",
        "relevance_score": int(record.get("relevance_score") or 0),
        "reading_priority_score": int(record.get("reading_priority_score") or record.get("reading_priority") or 0),
        "direction": direction_for_record(record),
        "seen_dates": record.get("seen_dates", []),
        "seen_sources": record.get("seen_sources", []),
        "rationale": _rationale_payload(record),
        "reading_action": _reading_bucket(record),
        "evidence_status": 'SOURCE_CONTENT_AVAILABLE' if has_source_content(record) else 'METADATA_ONLY',
    }


def build_reading_priority(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {name: [] for name in ("Must Read", "Should Skim", "Track Later", "Ignore / Peripheral")}
    for record in records:
        bucket = _reading_bucket(record)
        buckets[bucket].append(
            {
                "title": record.get("title") or "untitled",
                "relevance_label": record.get("relevance_label") or "D",
                "relevance_score": int(record.get("relevance_score") or 0),
                "reading_priority_score": int(record.get("reading_priority_score") or record.get("reading_priority") or 0),
                "direction": direction_for_record(record),
                "reason": _reading_bucket(record) + (': TODO_VERIFY source content before interpreting claims.' if not has_source_content(record) else ': source content available; verify proof and experiment details.'),
                "reading_action": _reading_bucket(record),
                "evidence_status": 'SOURCE_CONTENT_AVAILABLE' if has_source_content(record) else 'METADATA_ONLY',
                "canonical_id": dedup_key(record),
                "source_url": record.get('source_url') or record.get('url') or '',
            }
        )
    return {name: sorted(items, key=_display_sort_key) for name, items in buckets.items()}


def build_trend_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[direction_for_record(record)].append(record)
    trends: list[dict[str, Any]] = []
    direction_meta = {name: (kind, why) for name, _, kind, why in DIRECTION_RULES}
    for direction, _, _, _ in DIRECTION_RULES:
        items = sorted(grouped.get(direction, []), key=_display_sort_key)
        kind, why = direction_meta[direction]
        trends.append(
            {
                "direction": direction,
                "count": len(items),
                "status": kind,
                "what_appeared": [str(item.get("title") or "untitled") for item in items[:5]],
                "why_it_matters": why,
            }
        )
    return trends


def _weekly_files_for_month(data_dir: Path, start: date, end: date) -> list[str]:
    candidate_roots = [data_dir / str(start.year) / "weekly", data_dir / str(end.year) / "weekly", data_dir / "weekly"]
    paths: list[str] = []
    seen: set[Path] = set()
    for weekly_dir in candidate_roots:
        if not weekly_dir.exists():
            continue
        for path in sorted(weekly_dir.glob("*.json")):
            if path in seen:
                continue
            seen.add(path)
            try:
                payload = read_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            from_date = str(payload.get("from_date") or "")
            to_date = str(payload.get("to_date") or "")
            try:
                week_start = date.fromisoformat(from_date[:10])
                week_end = date.fromisoformat(to_date[:10])
            except ValueError:
                continue
            if week_start <= end and week_end >= start:
                paths.append(path.as_posix())
    return paths


def build_monthly_synthesis(
    data_dir: Path,
    month: str,
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    start, end = parse_month(month)
    loaded: list[tuple[date, dict[str, Any]]] = []
    input_daily_files: list[str] = []
    missing_days: list[str] = []
    for day in month_days(start, end):
        path, used_legacy = resolve_existing(
            daily_data_path(day, data_dir),
            legacy_daily_data_candidates(day, data_dir),
        )
        if not path.exists():
            missing_days.append(day.isoformat())
            continue
        if used_legacy:
            print(f"Warning: using legacy daily JSON fallback: {path}")
        loaded.append((day, assess_daily_input(path, day, data_dir, used_legacy)))
        input_daily_files.append(path.as_posix())
    loaded = normalize_period_inputs(loaded)
    records = aggregate_records(loaded)
    from lattice_digest.evidence_contract import classification_summary
    classification = classification_summary(records)
    class_counts = Counter(str(record.get("relevance_label") or "D") for record in records)
    direction_counts = Counter(direction_for_record(record) for record in records)
    source_health = build_source_health_summary(loaded)
    from lattice_digest.evidence_contract import source_scope_score, score_to_label
    core_records = [record for record in records if score_to_label(source_scope_score(record)[1]) in {"A", "B"}]
    core_papers = [build_core_paper(record) for record in sorted(core_records, key=_display_sort_key)[:12]]
    title_only = [
        str(record.get("title") or "untitled")
        for record in records
        if build_recommendation_rationale(record).confidence in {"title_only", "metadata_supported", "insufficient_evidence"}
    ]
    missing_health = [
        day.isoformat()
        for day, payload in loaded
        if not isinstance(payload.get("source_health"), list) or not payload.get("source_health")
    ]
    generated = generated_at or datetime.now(timezone.utc)
    return {
        **classification,
        "publication_event_views": period_views(loaded),
        "schema_version": SCHEMA_VERSION,
        "month": month,
        "generated_at": generated.isoformat(),
        "input_daily_files": input_daily_files,
        "input_weekly_files": _weekly_files_for_month(data_dir, start, end),
        "missing_days": missing_days,
        "input_quality": summarize_daily_inputs(loaded, missing_days),
        "paper_index": [{**r, 'canonical_id': dedup_key(r), 'reading_action': _reading_bucket(r), 'evidence_status': 'SOURCE_CONTENT_AVAILABLE' if has_source_content(r) else 'METADATA_ONLY'} for r in records],
        "translation_status": 'TRANSLATION_BACKEND_SELECTION_REQUIRED',
        "bilingual_release_status": 'BILINGUAL_RELEASE_NOT_YET_AVAILABLE',
        "total_unique_records": len(records),
        "class_counts": dict(sorted(class_counts.items(), key=lambda item: LABEL_ORDER.get(item[0], 9))),
        "direction_counts": dict(sorted(direction_counts.items())),
        "source_health_summary": source_health,
        "core_papers": core_papers,
        "reading_priority": build_reading_priority(records),
        "trend_summary": build_trend_summary(records),
        "rationale_policy": {
            "source": "lattice_digest.recommendation_rationale",
            "json_schema": "monthly-only rationale payload; Daily/Weekly JSON remains unchanged",
            "no_external_llm": True,
            "keyword_only_is_insufficient": True,
        },
        "TODO_VERIFY": {
            "papers_lacking_abstract": [str(record.get("title") or "untitled") for record in records if not str(record.get("abstract") or "").strip()],
            "title_only_or_metadata_supported_rationales": title_only,
            "source_starved_days": source_health["source_starved_days"],
            "missing_daily_files": missing_days,
            "missing_source_health_records": missing_health,
        },
    }


def _core_paper_markdown(paper: dict[str, Any], *, bilingual: bool = False) -> list[str]:
    rationale = paper["rationale"]
    todo = "；".join(rationale.get("todo_verify") or []) or rationale.get("caveat") or "TODO_VERIFY"
    lines = [
        f"### {paper['title']}",
        "",
        f"- Source: {paper['source']}",
        f"- Rank/class/score (upstream/provenance): {paper['relevance_label']} / {paper['relevance_score']}；upstream reading_priority_score {paper['reading_priority_score']}",
        f"- Validated source classification: {paper.get('validated_label','UNKNOWN')} / {paper.get('validated_score','UNKNOWN')}；scope {paper.get('validated_scope','UNKNOWN')}",
        f"- Direction: {paper['direction']}",
        f"- Problem: {rationale['problem']}",
        f"- Method / construction / attack / implementation: {rationale['method']}",
        f"- Contribution: {rationale['contribution']}",
        f"- Radar relevance: {rationale['radar_relevance']}",
        f"- Reading action: {rationale['reading_action']}",
        f"- Evidence basis: {', '.join(rationale['evidence_basis'])}；confidence={rationale['confidence']}",
        f"- TODO_VERIFY: {todo}",
        "",
    ]
    if bilingual and isinstance(rationale.get("bilingual"), dict):
        lines.extend(format_bilingual_rationale_markdown(rationale["bilingual"]))
        lines.append("")
    return lines


def render_markdown(payload: dict[str, Any]) -> str:
    health = payload["source_health_summary"]
    trends = payload["trend_summary"]
    top_directions = sorted(payload["direction_counts"].items(), key=lambda item: (-int(item[1]), item[0]))[:3]
    must_read = payload["reading_priority"].get("Must Read", [])
    lines: list[str] = [
        f"# Monthly Lattice Paper Radar — {payload['month']}",
        "",
        "## Executive Summary",
        "",
        f"- total unique papers: {payload['total_unique_records']}",
        f"- Input authority: {payload.get('input_quality', {}).get('authority_state', 'UNKNOWN')}; fully valid Daily={len(payload.get('input_quality', {}).get('fully_valid_days', []))}",
        f"- Daily semantic failures: {payload.get('input_quality', {}).get('semantic_failed_days', [])}; unknown: {payload.get('input_quality', {}).get('semantic_unknown_days', [])}",
        '- Translation: TRANSLATION_BACKEND_SELECTION_REQUIRED; BILINGUAL_RELEASE_NOT_YET_AVAILABLE',
        f"- Upstream/provenance A/B/C class counts: {payload['class_counts']}; validated={payload.get('validated_label_counts', {})}; conflicts={payload.get('classification_conflict_count', 'unknown')}; classification quality={payload.get('classification_quality_state', 'UNKNOWN')}",
        f"- top directions: {', '.join(f'{name} ({count})' for name, count in top_directions) if top_directions else 'none'}",
        f"- source-health status: {'source-starved days present' if health['source_starved'] else 'usable with recorded caveats'}",
        f"- source-starved month: {str(health['source_starved']).lower()}",
        f"- most important papers to read: {', '.join(item['title'] for item in must_read[:5]) if must_read else 'none'}",
        "",
        "## Core Papers of the Month",
        "",
    ]
    if not payload["core_papers"]:
        lines.extend(["- No A/B core papers found for this month.", ""])
    for index, paper in enumerate(payload["core_papers"]):
        render_bilingual = index < 5 or str(paper.get("relevance_label") or "") == "A"
        lines.extend(_core_paper_markdown(paper, bilingual=render_bilingual))

    lines.extend(["## Direction Trends", ""])
    for trend in trends:
        appeared = ", ".join(trend["what_appeared"]) if trend["what_appeared"] else "none"
        lines.extend(
            [
                f"### {trend['direction']}",
                f"- count: {trend['count']}",
                f"- status: {trend['status']}",
                f"- what appeared this month: {appeared}",
                f"- why it matters: {trend['why_it_matters']}",
                "",
            ]
        )

    lines.extend(["## Reading Priority", ""])
    for bucket in ("Must Read", "Should Skim", "Track Later", "Ignore / Peripheral"):
        lines.extend([f"### {bucket}", ""])
        items = payload["reading_priority"].get(bucket, [])
        if not items:
            lines.extend(["- none", ""])
            continue
        for item in items[:12]:
            lines.append(
                f"- {item['title']}｜upstream/provenance {item['relevance_label']} / {item['relevance_score']}｜"
                f"reading {item['reading_priority_score']}｜{item['direction']}｜{item['reason']}"
            )
        lines.append("")

    lines.extend(["## Source Health Summary", ""])
    lines.append("| Source | Green | Yellow | Red | Retrieval Count | Failure Types | Impact |")
    lines.append("| --- | ---: | ---: | ---: | ---: | --- | --- |")
    for row in payload["source_health_summary"]["sources"]:
        failures = ", ".join(f"{name}:{count}" for name, count in row["failure_types"].items()) or "none"
        lines.append(
            f"| {row['source']} | {row['green']} | {row['yellow']} | {row['red']} | "
            f"{row['retrieval_count']} | {failures} | {row['impact']} |"
        )
    lines.append("")

    lines.extend(["## TODO_VERIFY", ""])
    todo = payload["TODO_VERIFY"]
    for key, values in todo.items():
        lines.append(f"- {key}: {', '.join(values[:12]) if values else 'none'}")
    lines.append("")
    lines.extend(['## Complete canonical paper index', '', 'Detailed cards and reading lists above are bounded selections; this index contains every canonical indexed paper. The full machine-readable evidence is in paper_index in the matching Monthly JSON.', ''])
    for item in payload.get('paper_index', []):
        lines.append(f"- [{item.get('title', 'unknown')}]({item.get('source_url') or item.get('url') or ''}) | {item['canonical_id']} | {item['reading_action']} | {item['evidence_status']}")
    return "\n".join(lines)


def write_monthly_outputs(payload: dict[str, Any], json_output_dir: Path, digest_output_dir: Path) -> tuple[Path, Path]:
    json_path = monthly_data_path(str(payload["month"]), root=json_output_dir)
    markdown_path = monthly_digest_path(str(payload["month"]), root=digest_output_dir)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, markdown_path


def main(argv: list[str] | None = None) -> int:
    from lattice_digest.runtime_paths import legacy_cli_root
    parser = argparse.ArgumentParser(description="Generate a manual monthly lattice paper radar synthesis.")
    parser.add_argument("--month", required=True, help="Target month in YYYY-MM format.")
    parser.add_argument("--data-dir", type=Path, default=legacy_cli_root("data"))
    parser.add_argument("--json-output-dir", type=Path, default=legacy_cli_root("data"))
    parser.add_argument("--digest-output-dir", type=Path, default=legacy_cli_root("digests"))
    parser.add_argument("--dry-run", action="store_true", help="Build payload and print summary without writing files.")
    args = parser.parse_args(argv)

    payload = build_monthly_synthesis(args.data_dir, args.month)
    if args.dry_run:
        print(
            "Monthly synthesis {month}: {records} unique records, missing_days={missing}".format(
                month=payload["month"],
                records=payload["total_unique_records"],
                missing=len(payload["missing_days"]),
            )
        )
        print("DRY RUN: no monthly output files were written.")
        print(f"JSON target: {monthly_data_path(str(payload['month']), root=args.json_output_dir)}")
        print(f"Markdown target: {monthly_digest_path(str(payload['month']), root=args.digest_output_dir)}")
        return 0
    json_path, markdown_path = write_monthly_outputs(payload, args.json_output_dir, args.digest_output_dir)
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
