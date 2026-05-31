from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


def _as_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value in (None, ""):
        return []
    return [str(value)]


def _field(item: dict[str, object], *names: str, default: object = 0) -> object:
    for name in names:
        if name in item:
            return item[name]
    return default


def normalize_source_health(source_health: list[dict[str, object]] | None) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for item in source_health or []:
        warnings = _as_list(item.get("warnings"))
        errors = _as_list(item.get("errors"))
        normalized.append(
            {
                "source": str(item.get("source") or "unknown"),
                "status": str(item.get("health_status") or item.get("status") or "unknown"),
                "raw_count": _as_int(_field(item, "raw_count", "raw_candidates")),
                "normalized_count": _as_int(_field(item, "normalized_count", "normalized_candidates")),
                "date_filtered_count": _as_int(
                    _field(item, "date_filtered_count", "date_filtered_candidates")
                ),
                "deduped_count": _as_int(_field(item, "deduped_count", "deduped_candidates")),
                "relevance_filtered_count": _as_int(
                    _field(item, "relevance_filtered_count", "relevance_filtered_candidates")
                ),
                "threshold_count": _as_int(_field(item, "threshold_count", "scoring_threshold_candidates")),
                "final_count": _as_int(_field(item, "final_count", "final_records")),
                "warnings_count": _as_int(item.get("warnings_count"), len(warnings)),
                "errors_count": _as_int(item.get("errors_count"), len(errors)),
                "error_type": item.get("error_type"),
                "retryable": bool(item.get("retryable")),
                "warnings": warnings,
                "errors": errors,
            }
        )
    return sorted(normalized, key=lambda row: str(row["source"]).lower())


def build_source_health_payload(
    source_health: list[dict[str, object]] | None,
    run_date: date,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    generated = generated_at or datetime.now(timezone.utc)
    return {
        "schema_version": SCHEMA_VERSION,
        "run_date": run_date.isoformat(),
        "generated_at": generated.isoformat(),
        "sources": normalize_source_health(source_health),
    }


def _escape_table_text(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("\n", " ").replace("|", "\\|")


def render_source_health_markdown(payload: dict[str, object]) -> str:
    run_date = str(payload.get("run_date") or "")
    generated_at = str(payload.get("generated_at") or "")
    sources = payload.get("sources")
    rows = sources if isinstance(sources, list) else []

    lines = [
        f"# Source Health Ledger - {run_date}",
        "",
        f"- generated_at: {generated_at}",
        "",
    ]
    if not rows:
        lines.append("No source health data.")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            "| Source | Status | Raw | Normalized | Final | Error Type | Retryable | Warnings | Errors |",
            "|---|---:|---:|---:|---:|---|---:|---:|---:|",
        ]
    )
    for item in rows:
        if not isinstance(item, dict):
            continue
        lines.append(
            "| {source} | {status} | {raw} | {normalized} | {final} | {error_type} | {retryable} | {warnings} | {errors} |".format(
                source=_escape_table_text(item.get("source")),
                status=_escape_table_text(item.get("status")),
                raw=_escape_table_text(item.get("raw_count", 0)),
                normalized=_escape_table_text(item.get("normalized_count", 0)),
                final=_escape_table_text(item.get("final_count", 0)),
                error_type=_escape_table_text(item.get("error_type") or "none"),
                retryable=_escape_table_text(item.get("retryable")),
                warnings=_escape_table_text(item.get("warnings_count", 0)),
                errors=_escape_table_text(item.get("errors_count", 0)),
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_source_health_ledger(
    source_health: list[dict[str, object]] | None,
    root: Path,
    run_date: date,
    generated_at: datetime | None = None,
) -> tuple[Path, Path]:
    payload = build_source_health_payload(source_health, run_date, generated_at)
    output_dir = root / "audits" / "source-health"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"{run_date.isoformat()}.json"
    markdown_path = output_dir / f"{run_date.isoformat()}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_source_health_markdown(payload), encoding="utf-8")
    return json_path, markdown_path
