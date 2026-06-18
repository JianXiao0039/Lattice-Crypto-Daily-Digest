from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

import sys

if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lattice_digest.recommendation_rationale import build_recommendation_rationale


ACTION_STRENGTH = {"忽略": 0, "暂存": 1, "扫读": 2, "精读": 3}
EXPECTED_ACTION = {
    "Top / A-class": "精读",
    "Must Read": "精读",
    "Should Skim": "扫读",
    "Track Later": "暂存",
    "Ignore / Peripheral": "忽略",
}
KEYWORD_ONLY_MARKERS = ("matched keywords", "关键词", "keyword-only")


@dataclass(frozen=True)
class AuditPaths:
    root: Path
    month: str
    monthly_json: Path
    monthly_markdown: Path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _text(value: Any) -> str:
    return str(value or "").strip()


def _load_daily_records(root: Path, monthly_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_title: dict[str, dict[str, Any]] = {}
    for raw_path in monthly_payload.get("input_daily_files", []):
        path = root / str(raw_path)
        if not path.exists():
            continue
        payload = read_json(path)
        records = payload.get("records") if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            title = _text(record.get("title"))
            if title and title not in by_title:
                by_title[title] = record
    return by_title


def _rationale_from_record(record: dict[str, Any]) -> dict[str, Any]:
    rationale = build_recommendation_rationale(record).to_dict()
    return {
        "problem": rationale["problem_summary"],
        "method": rationale["method_summary"],
        "contribution": rationale["contribution_summary"],
        "radar_relevance": rationale["radar_relevance"],
        "reading_action": rationale["recommendation_reason"],
        "evidence_basis": rationale["evidence_basis"],
        "confidence": rationale["confidence"],
        "todo_verify": rationale["todo_verify"],
        "caveat": rationale["caveat"],
    }


def _action_label(text: str) -> str:
    stripped = text.strip()
    for action in ("精读", "扫读", "暂存", "忽略"):
        if stripped.startswith(action) or f"{action}：" in stripped or f"{action}:" in stripped:
            return action
    return "unknown"


def _reading_action_quality(bucket: str, action: str) -> str:
    expected = EXPECTED_ACTION.get(bucket)
    if action == "unknown" or not expected:
        return "unclear"
    delta = ACTION_STRENGTH[action] - ACTION_STRENGTH[expected]
    if delta == 0:
        return "correct"
    if delta > 0:
        return "too_strong"
    return "too_weak"


def _contains_keyword_only_text(*parts: str) -> bool:
    combined = " ".join(parts).lower()
    if any(marker in combined for marker in KEYWORD_ONLY_MARKERS):
        return True
    substantive_markers = ("problem", "method", "contribution", "从摘要看", "propose", "present", "attack", "implementation")
    return ("lwe" in combined or "lattice" in combined) and not any(marker in combined for marker in substantive_markers)


def _field_quality(value: str) -> bool:
    if not value:
        return False
    weak_fragments = (
        "证据不足",
        "不能可靠判断",
        "可用元数据未明确",
        "仅有标题/关键词",
    )
    return not any(fragment in value for fragment in weak_fragments)


def _overclaim_risk(rationale: dict[str, Any], record: dict[str, Any]) -> str:
    text = " ".join(
        [
            _text(rationale.get("problem")),
            _text(rationale.get("method")),
            _text(rationale.get("contribution")),
            _text(rationale.get("reading_action")),
        ]
    ).lower()
    todo = rationale.get("todo_verify") or []
    has_todo = bool(todo) or "todo_verify" in _text(rationale.get("caveat")).lower()
    strong_claims = ("proves", "prove ", "secure", "security", "demonstrate", "benchmark", "latency", "reduces", "accelerates")
    if any(claim in text for claim in strong_claims) and not has_todo:
        return "high"
    if any(claim in text for claim in strong_claims):
        return "low"
    if not record.get("abstract") and not record.get("conclusion"):
        return "medium"
    return "none"


def _quality_score(rationale: dict[str, Any], reading_quality: str, keyword_only: bool) -> int:
    if keyword_only:
        return 0
    score = 0
    if _field_quality(_text(rationale.get("problem"))):
        score += 1
    if _field_quality(_text(rationale.get("method"))):
        score += 1
    if _field_quality(_text(rationale.get("contribution"))):
        score += 1
    if rationale.get("evidence_basis"):
        score += 1
    if rationale.get("todo_verify") or "TODO_VERIFY" in _text(rationale.get("caveat")):
        score += 1
    if reading_quality in {"too_strong", "too_weak", "unclear"}:
        score = max(0, score - 1)
    return min(score, 5)


def _bucket_items(monthly_payload: dict[str, Any], bucket: str) -> list[dict[str, Any]]:
    reading_priority = monthly_payload.get("reading_priority")
    if not isinstance(reading_priority, dict):
        return []
    items = reading_priority.get(bucket)
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def select_sample(monthly_payload: dict[str, Any]) -> list[dict[str, Any]]:
    sample: list[dict[str, Any]] = []
    seen: set[str] = set()
    for paper in monthly_payload.get("core_papers", [])[:3]:
        if not isinstance(paper, dict):
            continue
        title = _text(paper.get("title"))
        if not title:
            continue
        selected = {
            "title": title,
            "relevance_label": paper.get("relevance_label"),
            "relevance_score": paper.get("relevance_score"),
            "reading_priority_score": paper.get("reading_priority_score"),
            "direction": paper.get("direction"),
            "reason": (paper.get("rationale") or {}).get("reading_action") if isinstance(paper.get("rationale"), dict) else "",
            "bucket": "Top / A-class",
        }
        sample.append(selected)
        seen.add(title)
    plan = [
        ("Should Skim", 2),
        ("Track Later", 2),
        ("Ignore / Peripheral", 1),
    ]
    for bucket, count in plan:
        added = 0
        for item in _bucket_items(monthly_payload, bucket):
            title = _text(item.get("title"))
            if not title or title in seen:
                continue
            selected = dict(item)
            selected["bucket"] = bucket
            sample.append(selected)
            seen.add(title)
            added += 1
            if added >= count:
                break
    return sample


def _core_rationale_map(monthly_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for paper in monthly_payload.get("core_papers", []):
        if not isinstance(paper, dict):
            continue
        title = _text(paper.get("title"))
        rationale = paper.get("rationale")
        if title and isinstance(rationale, dict):
            result[title] = rationale
    return result


def audit_case(item: dict[str, Any], record: dict[str, Any], rationale: dict[str, Any]) -> dict[str, Any]:
    reason = _text(item.get("reason") or rationale.get("reading_action"))
    action = _action_label(reason)
    reading_quality = _reading_action_quality(_text(item.get("bucket")), action)
    keyword_only = _contains_keyword_only_text(
        _text(rationale.get("problem")),
        _text(rationale.get("method")),
        _text(rationale.get("contribution")),
        _text(rationale.get("radar_relevance")),
        reason,
    )
    score = _quality_score(rationale, reading_quality, keyword_only)
    evidence_status = _text(rationale.get("confidence")) or "insufficient_evidence"
    overclaim = _overclaim_risk(rationale, record)
    return {
        "title": _text(item.get("title")),
        "bucket": _text(item.get("bucket")),
        "relevance_label": _text(item.get("relevance_label") or record.get("relevance_label")),
        "relevance_score": int(item.get("relevance_score") or record.get("relevance_score") or 0),
        "reading_priority_score": int(item.get("reading_priority_score") or record.get("reading_priority_score") or 0),
        "direction": _text(item.get("direction")),
        "rationale_quality_score": score,
        "evidence_status": evidence_status,
        "evidence_basis": rationale.get("evidence_basis") or [],
        "reading_action": action,
        "reading_action_quality": reading_quality,
        "keyword_only_risk": "high" if keyword_only else "none",
        "overclaim_risk": overclaim,
        "todo_verify_present": bool(rationale.get("todo_verify")) or "TODO_VERIFY" in _text(rationale.get("caveat")),
        "problem_present": bool(_text(rationale.get("problem"))),
        "method_present": bool(_text(rationale.get("method"))),
        "contribution_present": bool(_text(rationale.get("contribution"))),
        "radar_relevance_present": bool(_text(rationale.get("radar_relevance"))),
        "abstract_present": bool(record.get("abstract")),
        "conclusion_present": bool(record.get("conclusion")),
        "recommended_fix": _recommended_fix(score, reading_quality, evidence_status, overclaim),
    }


def _recommended_fix(score: int, reading_quality: str, evidence_status: str, overclaim: str) -> str:
    fixes: list[str] = []
    if score < 3:
        fixes.append("strengthen paper-work summary")
    if reading_quality != "correct":
        fixes.append("align rendered reading action with monthly bucket")
    if evidence_status in {"title_only", "metadata_supported", "insufficient_evidence"}:
        fixes.append("keep low-confidence caveat visible")
    if overclaim in {"medium", "high"}:
        fixes.append("tighten TODO_VERIFY around proof/security/benchmark claims")
    return "; ".join(fixes) if fixes else "none"


def build_audit(root: Path, month: str) -> dict[str, Any]:
    paths = AuditPaths(
        root=root,
        month=month,
        monthly_json=root / "data" / "monthly" / f"{month}.json",
        monthly_markdown=root / "digests" / "monthly" / f"{month}.md",
    )
    if not paths.monthly_json.exists() or not paths.monthly_markdown.exists():
        return {
            "schema_version": 1,
            "month": month,
            "decision": "monthly_rationale_quality_blocked_by_missing_monthly_artifact",
            "monthly_json_exists": paths.monthly_json.exists(),
            "monthly_markdown_exists": paths.monthly_markdown.exists(),
            "sample": [],
            "TODO_VERIFY": ["monthly JSON or Markdown artifact missing"],
        }
    monthly_payload = read_json(paths.monthly_json)
    monthly_markdown = paths.monthly_markdown.read_text(encoding="utf-8")
    daily_records = _load_daily_records(root, monthly_payload)
    core_rationales = _core_rationale_map(monthly_payload)
    cases: list[dict[str, Any]] = []
    for item in select_sample(monthly_payload):
        title = _text(item.get("title"))
        record = daily_records.get(title, item)
        rationale = core_rationales.get(title) or _rationale_from_record(record)
        cases.append(audit_case(item, record, rationale))
    keyword_risks = [case for case in cases if case["keyword_only_risk"] != "none"]
    action_mismatches = [case for case in cases if case["reading_action_quality"] != "correct"]
    missing_todo = [case for case in cases if not case["todo_verify_present"]]
    average_score = round(sum(case["rationale_quality_score"] for case in cases) / len(cases), 2) if cases else 0
    bilingual_present = "English:" in monthly_markdown and "中文" in monthly_markdown
    bilingual_status = "bilingual_top_paper_rationale_present" if bilingual_present else "bilingual_policy_documented_but_not_rendered"
    decision = "monthly_rationale_quality_passed"
    if not cases:
        decision = "insufficient_evidence"
    elif keyword_risks:
        decision = "monthly_rationale_quality_blocked_by_keyword_only_output"
    elif any(case["rationale_quality_score"] < 3 for case in cases):
        decision = "monthly_rationale_quality_passed_with_limits"
    elif action_mismatches or bilingual_status != "bilingual_top_paper_rationale_present":
        decision = "monthly_rationale_quality_passed_with_limits"
    source_health = monthly_payload.get("source_health_summary") if isinstance(monthly_payload, dict) else {}
    return {
        "schema_version": 1,
        "month": month,
        "monthly_json": str(paths.monthly_json.relative_to(root).as_posix()),
        "monthly_markdown": str(paths.monthly_markdown.relative_to(root).as_posix()),
        "decision": decision,
        "real_case_audit": "real_case_audit_completed_with_limited_sample" if len(cases) < 8 else "real_case_audit_completed",
        "sample_size": len(cases),
        "average_rationale_quality_score": average_score,
        "keyword_only_regression": "failed" if keyword_risks else "passed",
        "bilingual_rationale": bilingual_status,
        "reading_decision_usefulness": "reading_decision_useful_with_limits" if action_mismatches else "reading_decision_useful",
        "source_starved": bool(isinstance(source_health, dict) and source_health.get("source_starved")),
        "source_starved_days": source_health.get("source_starved_days", []) if isinstance(source_health, dict) else [],
        "action_mismatch_count": len(action_mismatches),
        "missing_todo_count": len(missing_todo),
        "sample": cases,
        "fix_list": sorted({case["recommended_fix"] for case in cases if case["recommended_fix"] != "none"}),
        "TODO_VERIFY": ["CI/release gates are outside monthly rationale quality audit"],
    }


def render_markdown(audit: dict[str, Any]) -> str:
    lines = [
        f"# Monthly Rationale Quality Audit — {audit['month']}",
        "",
        f"- Decision: `{audit['decision']}`",
        f"- Sample size: {audit['sample_size']}",
        f"- Average score: {audit['average_rationale_quality_score']}",
        f"- Keyword-only regression: {audit['keyword_only_regression']}",
        f"- Bilingual rationale: `{audit['bilingual_rationale']}`",
        f"- Reading decision usefulness: `{audit['reading_decision_usefulness']}`",
        f"- Source-starved month: {audit['source_starved']}",
        "",
        "## Sample Scorecard",
        "",
        "| Title | Bucket | Score | Evidence | Action Quality | Keyword Risk | Overclaim | Fix |",
        "| --- | --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for case in audit["sample"]:
        title = _text(case["title"]).replace("|", "\\|")
        fix = _text(case["recommended_fix"]).replace("|", "\\|")
        lines.append(
            f"| {title} | {case['bucket']} | {case['rationale_quality_score']} | "
            f"{case['evidence_status']} | {case['reading_action_quality']} | "
            f"{case['keyword_only_risk']} | {case['overclaim_risk']} | {fix} |"
        )
    lines.extend(["", "## Fix List", ""])
    fixes = audit.get("fix_list") or []
    if fixes:
        for fix in fixes:
            lines.append(f"- {fix}")
    else:
        lines.append("- none")
    lines.extend(["", "## TODO_VERIFY", ""])
    for item in audit.get("TODO_VERIFY", []):
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def write_outputs(audit: dict[str, Any], root: Path, output_dir: Path, track_output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    track_output_dir.mkdir(parents=True, exist_ok=True)
    markdown = render_markdown(audit)
    (output_dir / "phase-13r-rationale-quality-scorecard.md").write_text(markdown, encoding="utf-8")
    (track_output_dir / "v0.5_monthly_real_case_quality_audit_v0.1.md").write_text(markdown, encoding="utf-8")
    (output_dir / "phase-13r-real-paper-case-audit-log.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit real monthly recommendation rationale quality.")
    parser.add_argument("--month", required=True, help="Target month in YYYY-MM format.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=Path("docs") / "reports")
    parser.add_argument("--track-output-dir", type=Path, default=Path("docs") / "research_tracks")
    parser.add_argument("--no-write", action="store_true", help="Print JSON without writing audit reports.")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    audit = build_audit(root, args.month)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    if not args.no_write:
        output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
        track_output_dir = args.track_output_dir if args.track_output_dir.is_absolute() else root / args.track_output_dir
        write_outputs(audit, root, output_dir, track_output_dir)
    return 0 if audit["decision"] != "monthly_rationale_quality_blocked_by_missing_monthly_artifact" else 1


if __name__ == "__main__":
    raise SystemExit(main())
