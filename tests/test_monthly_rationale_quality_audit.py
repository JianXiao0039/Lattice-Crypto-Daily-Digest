import json
from pathlib import Path

from scripts.audit_monthly_rationale_quality import build_audit


def _write_fixture(root: Path, *, rationale: dict | None = None) -> None:
    (root / "data" / "monthly").mkdir(parents=True)
    (root / "digests" / "monthly").mkdir(parents=True)
    (root / "data").mkdir(exist_ok=True)
    record = {
        "title": "Efficient LWE Secret Recovery",
        "abstract": "The Learning With Errors problem is central. We present a lattice attack method and improve recovery from hints.",
        "relevance_label": "A",
        "relevance_score": 100,
        "reading_priority_score": 90,
        "source": "fixture",
        "keywords_matched": ["LWE", "lattice"],
    }
    monthly_rationale = rationale or {
        "problem": "从摘要看，论文关注 LWE secret recovery.",
        "method": "We present a lattice attack method.",
        "contribution": "It improves recovery from hints.",
        "radar_relevance": "与格密码/PQC 雷达相关：LWE.",
        "reading_action": "精读：direct LWE attack relevance.",
        "evidence_basis": ["abstract-derived"],
        "confidence": "abstract_supported",
        "todo_verify": ["TODO_VERIFY: proof details."],
        "caveat": "TODO_VERIFY: verify full paper.",
    }
    daily = {"records": [record], "source_health": []}
    monthly = {
        "month": "2026-06",
        "input_daily_files": ["data/2026-06-01.json"],
        "source_health_summary": {"source_starved": False, "source_starved_days": []},
        "core_papers": [{**record, "direction": "LWE / RLWE / MLWE", "rationale": monthly_rationale}],
        "reading_priority": {
            "Must Read": [{"title": record["title"], "relevance_label": "A", "relevance_score": 100, "reading_priority_score": 90, "direction": "LWE / RLWE / MLWE", "reason": monthly_rationale["reading_action"]}],
            "Should Skim": [],
            "Track Later": [],
            "Ignore / Peripheral": [],
        },
    }
    (root / "data" / "2026-06-01.json").write_text(json.dumps(daily), encoding="utf-8")
    (root / "data" / "monthly" / "2026-06.json").write_text(json.dumps(monthly), encoding="utf-8")
    (root / "digests" / "monthly" / "2026-06.md").write_text("Problem\nMethod\nContribution\nEvidence basis\nTODO_VERIFY\n", encoding="utf-8")


def test_audit_accepts_abstract_supported_rationale(tmp_path):
    _write_fixture(tmp_path)
    audit = build_audit(tmp_path, "2026-06")
    assert audit["decision"] in {"monthly_rationale_quality_passed", "monthly_rationale_quality_passed_with_limits"}
    assert audit["sample"][0]["evidence_status"] == "abstract_supported"
    assert audit["sample"][0]["rationale_quality_score"] >= 4
    assert audit["sample"][0]["todo_verify_present"] is True


def test_audit_does_not_require_manual_annotation_fields(tmp_path):
    _write_fixture(tmp_path)
    audit = build_audit(tmp_path, "2026-06")
    serialized = json.dumps(audit, ensure_ascii=False)
    assert "human_gold" not in serialized
    assert "user_confirmed" not in serialized
