from pathlib import Path

from scripts.audit_monthly_rationale_quality import build_audit
from tests.test_monthly_rationale_quality_audit import _write_fixture


def test_audit_detects_keyword_only_rationale(tmp_path: Path):
    _write_fixture(
        tmp_path,
        rationale={
            "problem": "Matched keywords: LWE, lattice.",
            "method": "",
            "contribution": "",
            "radar_relevance": "Matched keywords: LWE, lattice.",
            "reading_action": "精读：Matched keywords: LWE, lattice.",
            "evidence_basis": ["metadata-derived"],
            "confidence": "metadata_supported",
            "todo_verify": ["TODO_VERIFY: metadata only."],
            "caveat": "TODO_VERIFY",
        },
    )
    audit = build_audit(tmp_path, "2026-06")
    assert audit["decision"] == "monthly_rationale_quality_blocked_by_keyword_only_output"
    assert audit["sample"][0]["keyword_only_risk"] == "high"
    assert audit["sample"][0]["rationale_quality_score"] == 0


def test_audit_detects_missing_todo_verify_for_title_only_record(tmp_path: Path):
    _write_fixture(
        tmp_path,
        rationale={
            "problem": "仅根据标题可确认主题为：LWE paper",
            "method": "仅有标题/关键词，不能可靠判断具体方法。",
            "contribution": "仅有标题/关键词，不能可靠判断贡献。",
            "radar_relevance": "与格密码/PQC 雷达相关：LWE.",
            "reading_action": "暂存：title-only.",
            "evidence_basis": ["title-derived"],
            "confidence": "title_only",
            "todo_verify": [],
            "caveat": "",
        },
    )
    audit = build_audit(tmp_path, "2026-06")
    assert audit["sample"][0]["evidence_status"] == "title_only"
    assert audit["sample"][0]["todo_verify_present"] is False
    assert audit["missing_todo_count"] == 1
