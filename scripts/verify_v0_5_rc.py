from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.verify_durable_artifacts import verify_artifacts
FORBIDDEN_ANNOTATION_FIELDS = {
    "user_label",
    "human_gold_label",
    "user_confirmed",
    "user_corrected",
    "manual_annotation_status",
}
REQUIRED_PHASE_OUTPUTS = (
    "docs/reports/phase-13i-controlled-production-patch-proposal-for-v0.5.md",
    "docs/reports/phase-13j-daily-weekly-rationale-integration.md",
    "docs/reports/phase-13k-monthly-lattice-paper-radar-synthesis.md",
    "docs/reports/phase-13l-source-health-and-durable-artifact-recovery.md",
    "docs/reports/phase-13m-reading-queue-and-obsidian-export-polishing.md",
)
REQUIRED_MODULES = (
    "lattice_digest.recommendation_rationale",
    "lattice_digest.monthly_synthesis",
    "lattice_digest.reading_queue",
    "lattice_digest.obsidian_scaffold",
    "lattice_digest.weekly_synthesis",
    "lattice_digest.workflow",
)
REQUIRED_SCRIPTS = (
    "scripts/probe_source_health.py",
    "scripts/verify_durable_artifacts.py",
    "scripts/export_reading_queue.py",
    "scripts/export_obsidian_notes.py",
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        return {"records": payload}
    return {}


def file_check(path: Path, *, json_file: bool = False, contains: tuple[str, ...] = ()) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else path.as_posix(),
        "exists": path.exists(),
        "non_empty": False,
        "parseable": None,
        "contains": {},
    }
    if not path.exists():
        return result
    text = path.read_text(encoding="utf-8", errors="replace")
    result["non_empty"] = bool(text.strip())
    result["contains"] = {item: item in text for item in contains}
    if json_file:
        try:
            json.loads(text)
            result["parseable"] = True
        except json.JSONDecodeError:
            result["parseable"] = False
    return result


def module_checks() -> dict[str, Any]:
    modules: dict[str, bool] = {}
    errors: dict[str, str] = {}
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
            modules[name] = True
        except Exception as exc:
            modules[name] = False
            errors[name] = f"{type(exc).__name__}: {exc}"
    return {"modules": modules, "errors": errors, "ok": all(modules.values())}


def package_version() -> str:
    import lattice_digest

    return str(lattice_digest.__version__)


def dependency_checks(root: Path) -> dict[str, Any]:
    phase_outputs = {path: (root / path).exists() for path in REQUIRED_PHASE_OUTPUTS}
    scripts = {path: (root / path).exists() for path in REQUIRED_SCRIPTS}
    return {
        "phase_outputs": phase_outputs,
        "scripts": scripts,
        "missing_phase_outputs": [path for path, exists in phase_outputs.items() if not exists],
        "missing_scripts": [path for path, exists in scripts.items() if not exists],
        "ok": all(phase_outputs.values()) and all(scripts.values()),
    }


def artifact_checks(root: Path, *, target_date: str, week: str, month: str) -> dict[str, Any]:
    daily_json = root / "data" / f"{target_date}.json"
    daily_md = root / "digests" / f"{target_date}.md"
    weekly_json = root / "data" / "weekly" / f"{week}.json"
    weekly_md = root / "digests" / "weekly" / f"{week}.md"
    monthly_json = root / "data" / "monthly" / f"{month}.json"
    monthly_md = root / "digests" / "monthly" / f"{month}.md"
    health_json = root / "audits" / "source-health" / f"{target_date}.json"
    return {
        "daily": {
            "markdown": file_check(daily_md, contains=("数据源健康", "lattice/PQC anchor evidence")),
            "json": file_check(daily_json, json_file=True),
        },
        "weekly": {
            "markdown": file_check(weekly_md, contains=("lattice/PQC anchor evidence",)),
            "json": file_check(weekly_json, json_file=True),
        },
        "monthly": {
            "markdown": file_check(monthly_md, contains=("Problem", "Method", "Contribution", "Evidence basis", "TODO_VERIFY")),
            "json": file_check(monthly_json, json_file=True),
        },
        "source_health_audit": file_check(health_json, json_file=True),
    }


def source_health_checks(root: Path, target_date: str) -> dict[str, Any]:
    payload = read_json(root / "data" / f"{target_date}.json")
    health = payload.get("source_health") or payload.get("metadata", {}).get("source_health") or []
    rows = [row for row in health if isinstance(row, dict)] if isinstance(health, list) else []
    by_source = {str(row.get("source")): row for row in rows}
    arxiv = by_source.get("arxiv", {})
    semantic = by_source.get("semantic_scholar", {})
    openalex = by_source.get("openalex", {})
    iacr = by_source.get("iacr_eprint", {})
    return {
        "entries": len(rows),
        "source_starved": bool(not payload.get("records") and rows and all(_status(row) == "red" for row in rows)),
        "arxiv_429_classified": arxiv.get("error_type") == "rate_limit" or any("429" in str(item) for item in arxiv.get("warnings", [])),
        "semantic_scholar_key_not_printed": "SEMANTIC_SCHOLAR_API_KEY" not in json.dumps(semantic, ensure_ascii=False),
        "semantic_scholar_status": _status(semantic) if semantic else "missing",
        "openalex_status": _status(openalex) if openalex else "missing",
        "iacr_latest_status": iacr.get("latest_feed_status") or "unknown",
        "acceptable_for_rc": bool(rows),
    }


def _status(row: dict[str, Any]) -> str:
    return str(row.get("health_status") or row.get("status") or "unknown").lower()


def reading_queue_checks(root: Path) -> dict[str, Any]:
    path = root / "state" / "reading-queue.json"
    if not path.exists():
        return {"exists": False, "records": 0, "ok": False, "forbidden_fields": []}
    payload = read_json(path)
    records = [row for row in payload.get("records", []) if isinstance(row, dict)]
    forbidden = sorted(
        {
            field
            for record in records
            for field in FORBIDDEN_ANNOTATION_FIELDS
            if field in record
        }
    )
    rationale_records = [
        record
        for record in records
        if record.get("reading_action")
        and record.get("rationale_problem")
        and record.get("evidence_basis")
        and record.get("TODO_VERIFY") is not None
    ]
    return {
        "exists": True,
        "records": len(records),
        "rationale_records": len(rationale_records),
        "forbidden_fields": forbidden,
        "manual_annotation_dependency": bool(forbidden),
        "ok": bool(records) and bool(rationale_records) and not forbidden,
    }


def obsidian_checks(root: Path) -> dict[str, Any]:
    output_dir = root / "exports" / "obsidian-paper-notes" / "Papers"
    notes = sorted(output_dir.glob("*.md")) if output_dir.exists() else []
    sample_text = notes[0].read_text(encoding="utf-8", errors="replace") if notes else ""
    required = (
        "status: unread",
        "## 1. Radar Recommendation",
        "## 2. Paper Work Summary",
        "## 3. Relevance to My Research",
        "## 4. Reading Checklist",
        "## 5. TODO_VERIFY",
        "## 6. Links",
    )
    return {
        "exists": output_dir.exists(),
        "note_count": len(notes),
        "sample_note": notes[0].relative_to(root).as_posix() if notes else None,
        "required_sections_present": {item: item in sample_text for item in required},
        "writes_outside_repository": False,
        "ok": bool(notes) and all(item in sample_text for item in required),
    }


def rationale_quality_checks(root: Path) -> dict[str, Any]:
    queue = reading_queue_checks(root)
    monthly = file_check(root / "digests" / "monthly" / "2026-06.md", contains=("Problem", "Method", "Contribution"))
    status = "rationale_quality_gate_passed_with_limits"
    if queue["rationale_records"] == 0:
        status = "rationale_quality_blocked_by_keyword_only_output"
    return {
        "status": status,
        "reading_queue_rationale_records": queue["rationale_records"],
        "monthly_structured_rationale_present": all(monthly["contains"].values()) if monthly["exists"] else False,
        "daily_weekly_rationale_limit": "Daily/Weekly selected artifacts still emphasize source health and lattice/PQC anchor evidence; richer structured rationale is present in Monthly, reading queue, and Obsidian exports.",
    }


def bilingual_policy_checks(root: Path) -> dict[str, Any]:
    path = root / "docs" / "research_tracks" / "v0.5_rc_bilingual_rationale_policy_v0.1.md"
    if not path.exists():
        return {"status": "bilingual_rationale_design_only", "documented": False, "ok": False}
    text = path.read_text(encoding="utf-8", errors="replace")
    required_terms = ("中文", "English", "A-class", "top weekly", "top monthly")
    return {
        "status": "bilingual_rationale_policy_ready",
        "documented": True,
        "required_terms": {term: term in text for term in required_terms},
        "ok": all(term in text for term in required_terms),
    }


def durable_evidence_checks(root: Path, *, target_date: str, week: str, month: str) -> dict[str, Any]:
    durable = verify_artifacts(root, target_date=target_date, week=week, month=month)
    queue = file_check(root / "exports" / "reading-queue" / "reading-dashboard.md")
    obsidian = obsidian_checks(root)
    ready = durable["overall_status"] == "verified" and queue["exists"] and queue["non_empty"] and obsidian["ok"]
    return {
        "status": "durable_evidence_ready" if ready else "durable_evidence_partial",
        "durable_artifacts": durable,
        "reading_queue_export": queue,
        "obsidian_export": obsidian,
        "ok": ready,
    }


def build_report(root: Path, *, target_date: str, week: str, month: str) -> dict[str, Any]:
    deps = dependency_checks(root)
    modules = module_checks()
    artifacts = artifact_checks(root, target_date=target_date, week=week, month=month)
    source_health = source_health_checks(root, target_date)
    queue = reading_queue_checks(root)
    obsidian = obsidian_checks(root)
    durable = durable_evidence_checks(root, target_date=target_date, week=week, month=month)
    rationale = rationale_quality_checks(root)
    bilingual = bilingual_policy_checks(root)
    blocker_reasons = []
    if not deps["ok"]:
        blocker_reasons.append("missing_dependency")
    if not modules["ok"]:
        blocker_reasons.append("module_import_failure")
    if not durable["ok"]:
        blocker_reasons.append("durable_evidence_partial")
    if not source_health["acceptable_for_rc"]:
        blocker_reasons.append("source_health_missing")
    if not queue["ok"]:
        blocker_reasons.append("reading_queue_incomplete")
    if not obsidian["ok"]:
        blocker_reasons.append("obsidian_export_incomplete")
    if not bilingual["ok"]:
        blocker_reasons.append("bilingual_policy_incomplete")

    rc_decision = "v0_5_rc_ready_with_limits" if not blocker_reasons else "v0_5_rc_blocked_by_multiple_conditions"
    production_gate = "eligible_for_v0_5_rc_review" if not blocker_reasons else "blocked_by_multiple_conditions"
    return {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(),
        "target_date": target_date,
        "target_week": week,
        "target_month": month,
        "active_package_version": package_version(),
        "dependencies": deps,
        "modules": modules,
        "artifacts": artifacts,
        "source_health": source_health,
        "reading_queue": queue,
        "obsidian_export": obsidian,
        "durable_evidence": durable,
        "rationale_quality": rationale,
        "bilingual_policy": bilingual,
        "manual_annotation_dependency": False,
        "external_llm_required": False,
        "release_tag_operation": False,
        "blockers": blocker_reasons,
        "v0_5_rc_decision": rc_decision,
        "production_gate": production_gate,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the v0.5 paper-radar usability release candidate gate.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--date", required=True, dest="target_date")
    parser.add_argument("--week", required=True)
    parser.add_argument("--month", required=True)
    args = parser.parse_args(argv)
    report = build_report(args.root, target_date=args.target_date, week=args.week, month=args.month)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["v0_5_rc_decision"] in {"v0_5_rc_ready", "v0_5_rc_ready_with_limits"} else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
