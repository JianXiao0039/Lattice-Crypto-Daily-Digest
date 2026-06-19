from pathlib import Path

from scripts.audit_monthly_rationale_quality import build_audit, find_latest_month, write_outputs
from tests.test_monthly_rationale_quality_audit import _write_fixture


def test_audit_fails_on_missing_evidence_basis_for_top_paper(tmp_path: Path) -> None:
    _write_fixture(
        tmp_path,
        rationale={
            "problem": "从摘要看，论文关注 LWE secret recovery.",
            "method": "It presents a lattice attack method.",
            "contribution": "It improves recovery from hints.",
            "radar_relevance": "与格密码/PQC 雷达相关：LWE.",
            "reading_action": "精读：direct LWE attack relevance.",
            "evidence_basis": [],
            "confidence": "abstract_supported",
            "todo_verify": ["TODO_VERIFY: proof details."],
            "caveat": "TODO_VERIFY: verify full paper.",
        },
    )

    audit = build_audit(tmp_path, "2026-06")

    assert audit["pass_fail"] == "fail"
    assert "missing evidence_basis for sampled papers" in audit["blockers"]
    assert audit["missing_evidence_basis_findings"] == ["Efficient LWE Secret Recovery"]


def test_audit_flags_conclusion_claim_without_conclusion_evidence(tmp_path: Path) -> None:
    _write_fixture(
        tmp_path,
        rationale={
            "problem": "从摘要看，论文关注 LWE secret recovery.",
            "method": "The conclusion says the attack is complete.",
            "contribution": "It improves recovery from hints.",
            "radar_relevance": "与格密码/PQC 雷达相关：LWE.",
            "reading_action": "精读：direct LWE attack relevance.",
            "evidence_basis": ["abstract-derived"],
            "confidence": "abstract_supported",
            "todo_verify": ["TODO_VERIFY: proof details."],
            "caveat": "TODO_VERIFY: verify full paper.",
        },
    )

    audit = build_audit(tmp_path, "2026-06")

    assert audit["pass_fail"] == "fail"
    assert "hallucinated conclusion claims" in audit["blockers"]
    assert audit["sample"][0]["hallucinated_conclusion_claim"] is True


def test_audit_flags_weak_relevance_overpromotion(tmp_path: Path) -> None:
    _write_fixture(
        tmp_path,
        rationale={
            "problem": "仅根据标题可确认主题为：generic lattice application.",
            "method": "A complete method is described.",
            "contribution": "A core contribution is claimed.",
            "radar_relevance": "Weak metadata-only relation.",
            "reading_action": "精读：core lattice/PQC paper.",
            "evidence_basis": ["metadata-derived"],
            "confidence": "metadata_supported",
            "todo_verify": ["TODO_VERIFY: metadata only."],
            "caveat": "TODO_VERIFY",
        },
    )

    audit = build_audit(tmp_path, "2026-06")

    assert "weak evidence paper over-promoted" in audit["warnings"]
    assert audit["weak_relevance_overpromotion_findings"] == ["Efficient LWE Secret Recovery"]


def test_audit_accepts_top_paper_bilingual_rationale(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    monthly_markdown = tmp_path / "digests" / "monthly" / "2026-06.md"
    monthly_markdown.write_text(
        "# Monthly Lattice Paper Radar - 2026-06\n"
        "## Core Papers of the Month\n"
        "中文：论文大致工作：LWE secret recovery.\n"
        "English: Paper work summary: LWE secret recovery.\n"
        "## Direction Trends\n"
        "## Reading Priority\n"
        "## Source Health Summary\n"
        "## TODO_VERIFY\n",
        encoding="utf-8",
    )

    audit = build_audit(tmp_path, "2026-06")

    assert audit["bilingual_rationale"] == "bilingual_top_paper_rationale_present"
    assert audit["bilingual_policy_findings"] == []


def test_latest_month_and_audit_outputs_are_deterministic(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    assert find_latest_month(tmp_path) == "2026-06"
    audit = build_audit(tmp_path, "2026-06")
    write_outputs(audit, tmp_path, tmp_path / "reports", tmp_path / "tracks")

    assert (tmp_path / "audits" / "monthly-quality" / "2026-06.json").is_file()
    assert (tmp_path / "audits" / "monthly-quality" / "2026-06.md").is_file()
