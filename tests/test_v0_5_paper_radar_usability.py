from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_v0_5_rc import FORBIDDEN_ANNOTATION_FIELDS, reading_queue_checks, rationale_quality_checks


def test_top_paper_rationale_is_not_keyword_only(tmp_path: Path) -> None:
    queue = {
        "records": [
            {
                "title": "LWE attack paper",
                "reading_action": "精读",
                "rationale_problem": "从摘要看，论文关注 LWE attack cost.",
                "rationale_method": "It proposes an attack-cost benchmark.",
                "rationale_contribution": "It contributes a reproducible comparison.",
                "rationale_relevance": "与格密码/PQC 雷达相关。",
                "rationale_caveat": "TODO_VERIFY",
                "evidence_basis": ["abstract-derived"],
                "TODO_VERIFY": ["TODO_VERIFY"],
            }
        ]
    }
    path = tmp_path / "state/reading-queue.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    result = reading_queue_checks(tmp_path)

    assert result["ok"] is True
    assert result["rationale_records"] == 1


def test_reading_queue_requires_no_manual_annotation_fields(tmp_path: Path) -> None:
    queue = {"records": [{"title": "x", "reading_action": "暂存", "rationale_problem": "p", "evidence_basis": ["title-derived"], "TODO_VERIFY": []}]}
    path = tmp_path / "state/reading-queue.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    result = reading_queue_checks(tmp_path)

    assert result["forbidden_fields"] == []
    assert FORBIDDEN_ANNOTATION_FIELDS.isdisjoint(queue["records"][0])


def test_rationale_quality_reports_limits_when_monthly_missing(tmp_path: Path) -> None:
    queue = {"records": [{"title": "x", "reading_action": "精读", "rationale_problem": "p", "evidence_basis": ["abstract-derived"], "TODO_VERIFY": []}]}
    path = tmp_path / "state/reading-queue.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")

    result = rationale_quality_checks(tmp_path)

    assert result["status"] == "rationale_quality_gate_passed_with_limits"
    assert "Daily/Weekly" in result["daily_weekly_rationale_limit"]
