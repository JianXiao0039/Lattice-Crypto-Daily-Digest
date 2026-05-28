from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from lattice_digest.config import project_root


SOURCE_ORDER = ["iacr_eprint", "arxiv", "dblp", "openalex", "crossref", "semantic_scholar"]
HIGH_PRIORITY_LABELS = {"必须精读", "建议精读"}


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def normalized_title_hash(title: str) -> str:
    normalized = re.sub(r"[^\w\s-]", "", title.lower(), flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"title_hash:{digest}"


def stable_id(record: dict[str, Any]) -> str:
    for field, prefix in [
        ("eprint_id", "eprint"),
        ("arxiv_id", "arxiv"),
        ("doi", "doi"),
        ("semantic_scholar_id", "semantic_scholar"),
        ("semanticScholarId", "semantic_scholar"),
    ]:
        value = str(record.get(field) or "").strip()
        if value:
            return f"{prefix}:{value.lower()}"
    paper_id = str(record.get("paper_id") or "").strip()
    source = str(record.get("source") or "").lower()
    if paper_id and "semantic" in source:
        return f"semantic_scholar:{paper_id.lower()}"
    url = str(record.get("url") or record.get("source_url") or "").strip()
    if url:
        return f"url:{url.lower()}"
    return normalized_title_hash(str(record.get("title") or "unknown"))


def record_summary(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": record.get("title") or "unknown",
        "source": record.get("source") or "unknown",
        "url": record.get("url") or record.get("source_url") or "",
        "reading_priority_score": int(record.get("reading_priority_score") or record.get("relevance_score") or 0),
        "priority_label": record.get("priority_label") or "unknown",
        "reason_for_priority": record.get("reason_for_priority") or "",
    }


def _record_map(payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not payload:
        return {}
    records = payload.get("records")
    if not isinstance(records, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        if isinstance(record, dict):
            result[stable_id(record)] = record
    return result


def _metadata(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    metadata = payload.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _source_health_map(payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not payload:
        return {}
    health = payload.get("source_health")
    if not isinstance(health, list):
        health = _metadata(payload).get("source_health")
    if not isinstance(health, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in health:
        if isinstance(item, dict):
            source = str(item.get("source") or "unknown")
            result[source] = item
    return result


def _count(item: dict[str, Any] | None, *names: str) -> int:
    if not item:
        return 0
    for name in names:
        value = item.get(name)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return 0


def _status(item: dict[str, Any] | None) -> str:
    if not item:
        return "missing"
    return str(item.get("health_status") or item.get("status") or "unknown")


def _source_health_comparison(
    provisional: dict[str, Any] | None,
    authoritative: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    provisional_health = _source_health_map(provisional)
    authoritative_health = _source_health_map(authoritative)
    sources = [*SOURCE_ORDER]
    for source in sorted(set(provisional_health) | set(authoritative_health)):
        if source not in sources:
            sources.append(source)
    rows: list[dict[str, Any]] = []
    for source in sources:
        p_item = provisional_health.get(source)
        a_item = authoritative_health.get(source)
        p_raw = _count(p_item, "raw_count", "raw_candidates")
        a_raw = _count(a_item, "raw_count", "raw_candidates")
        p_date = _count(p_item, "date_filtered_count", "date_filtered_candidates")
        a_date = _count(a_item, "date_filtered_count", "date_filtered_candidates")
        p_final = _count(p_item, "final_count", "final_records")
        a_final = _count(a_item, "final_count", "final_records")
        p_status = _status(p_item)
        a_status = _status(a_item)
        rows.append(
            {
                "source": source,
                "provisional_raw": p_raw,
                "authoritative_raw": a_raw,
                "provisional_date_filtered": p_date,
                "authoritative_date_filtered": a_date,
                "provisional_final": p_final,
                "authoritative_final": a_final,
                "provisional_status": p_status,
                "authoritative_status": a_status,
                "delta_raw": a_raw - p_raw,
                "delta_date_filtered": a_date - p_date,
                "delta_final": a_final - p_final,
                "status_change": "same" if p_status == a_status else f"{p_status}->{a_status}",
            }
        )
    return rows


def _green_count(rows: list[dict[str, Any]], prefix: str) -> int:
    return sum(1 for row in rows if row.get(f"{prefix}_status") == "green")


def _red_count(rows: list[dict[str, Any]], prefix: str) -> int:
    return sum(1 for row in rows if row.get(f"{prefix}_status") == "red")


def quality_judgment(
    *,
    provisional_available: bool,
    authoritative_available: bool,
    counts: dict[str, int],
    source_health_comparison: list[dict[str, Any]],
) -> dict[str, Any]:
    risk_notes: list[str] = []
    if not authoritative_available:
        return {
            "replacement_recommended": False,
            "reason": "authoritative 报告不存在，无法建议替换。",
            "risk_notes": ["缺少本地 authoritative_backfill 输入。"],
        }
    if not provisional_available:
        return {
            "replacement_recommended": True,
            "reason": "没有找到 provisional 快照，无法做完整对比；可将 authoritative 作为当前自检结果。",
            "risk_notes": ["没有找到 provisional 快照，无法做完整对比。"],
        }

    if counts["high_priority_missing_count"] > 0:
        risk_notes.append("authoritative 缺失 GitHub provisional 中的高优先级论文。")
    if counts["missing_from_backfill_count"] > 0:
        risk_notes.append("存在 GitHub provisional 独有论文，替换前应人工检查。")
    if counts["authoritative_count"] < counts["provisional_count"]:
        risk_notes.append("authoritative_count 少于 provisional_count。")

    provisional_green = _green_count(source_health_comparison, "provisional")
    authoritative_green = _green_count(source_health_comparison, "authoritative")
    provisional_red = _red_count(source_health_comparison, "provisional")
    authoritative_red = _red_count(source_health_comparison, "authoritative")
    if authoritative_green < provisional_green:
        risk_notes.append("authoritative 的绿色数据源数量少于 provisional。")
    if authoritative_red > provisional_red:
        risk_notes.append("authoritative 的红色失败数据源数量多于 provisional。")

    positive = [
        counts["authoritative_count"] > counts["provisional_count"],
        counts["high_priority_added_count"] > 0,
        authoritative_green > provisional_green,
        provisional_red > authoritative_red,
    ]
    negative = [
        counts["authoritative_count"] < counts["provisional_count"],
        counts["high_priority_missing_count"] > 0,
        authoritative_green < provisional_green,
        authoritative_red > provisional_red,
    ]
    replacement_recommended = any(positive) and not any(negative)
    reason = (
        "本地回填补充了更多记录、高优先级论文或更好的 source health。"
        if replacement_recommended
        else "本地回填未明显优于 provisional，或存在缺失/健康状态风险，建议人工检查。"
    )
    return {
        "replacement_recommended": replacement_recommended,
        "reason": reason,
        "risk_notes": risk_notes,
    }


def audit_payload(
    target_date: str,
    provisional: dict[str, Any] | None,
    authoritative: dict[str, Any] | None,
) -> dict[str, Any]:
    p_records = _record_map(provisional)
    a_records = _record_map(authoritative)
    p_keys = set(p_records)
    a_keys = set(a_records)
    added_keys = sorted(a_keys - p_keys)
    missing_keys = sorted(p_keys - a_keys)
    common_keys = sorted(p_keys & a_keys)

    added = [record_summary(a_records[key]) for key in added_keys]
    missing = [record_summary(p_records[key]) for key in missing_keys]
    common = [record_summary(a_records[key]) for key in common_keys]
    high_added = [item for item in added if item.get("priority_label") in HIGH_PRIORITY_LABELS]
    high_missing = [item for item in missing if item.get("priority_label") in HIGH_PRIORITY_LABELS]

    source_comparison = _source_health_comparison(provisional, authoritative)
    p_metadata = _metadata(provisional)
    a_metadata = _metadata(authoritative)
    counts = {
        "provisional_count": len(p_records),
        "authoritative_count": len(a_records),
        "common_count": len(common_keys),
        "added_by_backfill_count": len(added),
        "missing_from_backfill_count": len(missing),
        "high_priority_added_count": len(high_added),
        "high_priority_missing_count": len(high_missing),
    }
    metadata = {
        "target_date": target_date,
        "audit_run_date": date.today().isoformat(),
        "provisional_available": provisional is not None,
        "authoritative_available": authoritative is not None,
        "provisional_collector": p_metadata.get("collector"),
        "authoritative_collector": a_metadata.get("collector"),
        "provisional_quality_status": p_metadata.get("quality_status"),
        "authoritative_quality_status": a_metadata.get("quality_status"),
    }
    judgment = quality_judgment(
        provisional_available=provisional is not None,
        authoritative_available=authoritative is not None,
        counts=counts,
        source_health_comparison=source_comparison,
    )
    return {
        "metadata": metadata,
        "counts": counts,
        "added_by_backfill": added,
        "missing_from_backfill": missing,
        "common_records": common,
        "high_priority_added_by_backfill": high_added,
        "high_priority_missing_from_backfill": high_missing,
        "source_health_comparison": source_comparison,
        "quality_judgment": judgment,
    }


def _paper_list(items: list[dict[str, Any]], empty: str) -> list[str]:
    if not items:
        return [empty, ""]
    lines: list[str] = []
    for item in items:
        url = item.get("url") or ""
        link = f"，[link]({url})" if url else ""
        lines.append(
            "- {title}（{source}，{score} / {label}{link}）：{reason}".format(
                title=item.get("title", "unknown"),
                source=item.get("source", "unknown"),
                score=item.get("reading_priority_score", 0),
                label=item.get("priority_label", "unknown"),
                link=link,
                reason=item.get("reason_for_priority") or "暂无原因",
            )
        )
    lines.append("")
    return lines


def audit_markdown(result: dict[str, Any]) -> str:
    metadata = result["metadata"]
    counts = result["counts"]
    judgment = result["quality_judgment"]
    target_date = metadata["target_date"]
    lines = [
        f"# Backfill Quality Audit - {target_date}",
        "",
        "## 1. 审计结论",
        "",
        f"- replacement_recommended：{str(judgment['replacement_recommended']).lower()}",
        f"- reason：{judgment['reason']}",
        f"- 本地新增论文数：{counts['added_by_backfill_count']}",
        f"- GitHub 独有论文数：{counts['missing_from_backfill_count']}",
        f"- 本地新增高优先级论文数：{counts['high_priority_added_count']}",
        f"- provisional_available：{str(metadata['provisional_available']).lower()}",
        f"- authoritative_available：{str(metadata['authoritative_available']).lower()}",
        "",
        "## 2. 数量对比",
        "",
        "| metric | value |",
        "| --- | ---: |",
    ]
    for key in [
        "provisional_count",
        "authoritative_count",
        "common_count",
        "added_by_backfill_count",
        "missing_from_backfill_count",
        "high_priority_added_count",
        "high_priority_missing_count",
    ]:
        lines.append(f"| {key} | {counts[key]} |")
    lines.extend(["", "## 3. 本地回填新增论文", ""])
    lines.extend(_paper_list(result["added_by_backfill"], "没有本地新增论文。"))
    lines.extend(["## 4. GitHub provisional 独有论文", ""])
    lines.extend(_paper_list(result["missing_from_backfill"], "没有 GitHub provisional 独有论文。"))
    lines.extend(["## 5. 高优先级差异", "", "### 本地新增高优先级", ""])
    lines.extend(_paper_list(result["high_priority_added_by_backfill"], "没有本地新增的必须精读 / 建议精读论文。"))
    lines.extend(["### GitHub 独有高优先级", ""])
    lines.extend(_paper_list(result["high_priority_missing_from_backfill"], "没有 GitHub 独有的必须精读 / 建议精读论文。"))
    lines.extend(
        [
            "## 6. Source Health 差异",
            "",
            "| Source | Provisional raw/date/final/status | Authoritative raw/date/final/status | Delta raw/date/final | Status change |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in result["source_health_comparison"]:
        lines.append(
            "| {source} | {p_raw}/{p_date}/{p_final}/{p_status} | {a_raw}/{a_date}/{a_final}/{a_status} | {d_raw}/{d_date}/{d_final} | {change} |".format(
                source=row["source"],
                p_raw=row["provisional_raw"],
                p_date=row["provisional_date_filtered"],
                p_final=row["provisional_final"],
                p_status=row["provisional_status"],
                a_raw=row["authoritative_raw"],
                a_date=row["authoritative_date_filtered"],
                a_final=row["authoritative_final"],
                a_status=row["authoritative_status"],
                d_raw=row["delta_raw"],
                d_date=row["delta_date_filtered"],
                d_final=row["delta_final"],
                change=row["status_change"],
            )
        )
    lines.extend(["", "## 7. 风险与处理建议", ""])
    risk_notes = judgment.get("risk_notes") or []
    if not metadata["provisional_available"]:
        lines.append("- 没有找到 provisional 快照，无法做完整对比；本报告仅能做 authoritative 自检。")
    if risk_notes:
        for note in risk_notes:
            lines.append(f"- {note}")
    else:
        lines.append("- 未发现明显替换风险。")
    lines.append("- 如果 GitHub 独有论文存在，请人工检查是否由 API 限流、dedup/filter 差异或时间窗口差异导致。")
    lines.append("- 如果 source health 明显变差，建议重新运行 backfill 或扩大窗口。")
    lines.append("")
    return "\n".join(lines)


def write_audit(root: Path, target_date: str) -> tuple[Path, Path, dict[str, Any]]:
    provisional = load_json(root / "archive" / "provisional" / f"{target_date}.json")
    authoritative = load_json(root / "data" / f"{target_date}.json")
    result = audit_payload(target_date, provisional, authoritative)
    output_dir = root / "audits" / "backfill"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{target_date}.json"
    markdown_path = output_dir / f"{target_date}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(audit_markdown(result), encoding="utf-8")
    return json_path, markdown_path, result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit provisional vs authoritative backfill digest quality.")
    parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD format.")
    parser.add_argument("--root", type=Path, default=None, help="Override project root.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root or project_root()
    json_path, markdown_path, result = write_audit(root, args.date)
    if not result["metadata"]["provisional_available"]:
        print("没有找到 provisional 快照，无法做完整对比；已输出 authoritative 自检摘要。")
    print(json_path)
    print(markdown_path)
    print(f"replacement_recommended={str(result['quality_judgment']['replacement_recommended']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
