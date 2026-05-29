from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.paper_plans import (
    create_paper_plan,
    generate_paper_plans,
    render_markdown,
    write_plan,
)


def _idea(
    title: str,
    *,
    track: str = "AI4Lattice",
    score: int = 90,
    maturity: str = "experiment_ready",
    source_papers: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "idea_id": "idea-" + title.lower().replace(" ", "-"),
        "title": title,
        "track": track,
        "subtracks": ["test subtrack"],
        "idea_priority_score": score,
        "maturity": maturity,
        "core_question": "如何把该线索转化为可验证的格密码研究计划？",
        "intuition": "保守测试 intuition。",
        "minimum_viable_project": "实现最小 MVP 并比较 baseline。",
        "experiments_needed": ["toy benchmark", "baseline comparison"],
        "proof_or_security_analysis_needed": ["需要分析安全目标和参数边界。"],
        "implementation_artifact": "最小 Python/Sage artifact。",
        "risks": ["toy phenomenon 风险。"],
        "advisor_questions": ["这个 MVP 是否足以支撑组会？"],
        "source_papers": source_papers
        if source_papers is not None
        else [
            {
                "title": "Source Paper",
                "url": "https://example.test/paper",
                "source_digest_date": "2026-05-29",
                "priority_label": "必须精读",
                "reading_priority_score": 90,
            }
        ],
    }


def _write_bank(path: Path, ideas: list[dict[str, object]]) -> Path:
    path.write_text(json.dumps({"ideas": ideas}, ensure_ascii=False), encoding="utf-8")
    return path


def test_generate_paper_plan_from_idea_bank_and_filters() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        bank = _write_bank(
            root / "idea-bank.json",
            [
                _idea("AI LWE plan", track="AI4Lattice", score=95),
                _idea("Module SIS plan", track="Module-SIS Primitive", score=86),
                _idea("Low plan", track="PQC Systems", score=40),
            ],
        )

        result = generate_paper_plans(bank, root / "plans", root / "obsidian", top=1, min_idea_score=70)
        module_only = generate_paper_plans(
            bank,
            root / "plans2",
            root / "obsidian2",
            tracks={"Module-SIS Primitive"},
            min_idea_score=70,
            dry_run=True,
        )

        assert len(result.plans) == 1
        assert result.json_paths and result.markdown_paths and result.obsidian_paths
        payload = json.loads(result.json_paths[0].read_text(encoding="utf-8"))
        assert "paper_plan_score" in payload
        assert payload["source_idea_id"] == "idea-ai-lwe-plan"
        assert len(module_only.plans) == 1
        assert module_only.plans[0]["track"] == "Module-SIS Primitive"


def test_min_score_and_dry_run_do_not_write_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        bank = _write_bank(root / "idea-bank.json", [_idea("Low plan", score=60), _idea("High plan", score=90)])

        result = generate_paper_plans(
            bank,
            root / "plans",
            root / "obsidian",
            min_idea_score=80,
            dry_run=True,
        )

        assert len(result.plans) == 1
        assert result.plans[0]["title"] == "High plan"
        assert not (root / "plans").exists()
        assert not (root / "obsidian").exists()


def test_markdown_contains_16_sections_and_is_clean() -> None:
    plan = create_paper_plan(_idea("AI4Lattice <b>bad</b> contentReference oaicite id=abc", track="AI4Lattice"))
    markdown = render_markdown(plan, obsidian=True)

    for section in [
        "## 1. 计划摘要",
        "## 2. 核心研究问题",
        "## 3. 为什么不是平庸拼接",
        "## 4. 最低可做版本",
        "## 5. 预期贡献点",
        "## 6. 技术路线",
        "## 7. 实验路线",
        "## 8. 证明或安全分析路线",
        "## 9. Artifact 与代码目录",
        "## 10. 相关论文阅读清单",
        "## 11. 3 个月执行计划",
        "## 12. 风险与降级方案",
        "## 13. 导师讨论问题",
        "## 14. 模拟审稿人质疑",
        "## 15. PhD 与长期研究规划连接",
        "## 16. 下一步行动清单",
    ]:
        assert section in markdown
    assert "[[AI4Lattice]]" in markdown
    assert "<b>" not in markdown
    assert "contentReference" not in markdown
    assert "oaicite" not in markdown
    assert "id=" not in markdown


def test_track_specific_content_is_conservative() -> None:
    ai_plan = create_paper_plan(_idea("Transformer LWE coordinate selection", track="AI4Lattice"))
    ai_md = render_markdown(ai_plan)
    assert "classical attack pipeline" in ai_md
    assert "不是声称端到端破解 LWE" in ai_md

    sis_plan = create_paper_plan(_idea("Module-SIS chameleon hash", track="Module-SIS Primitive"))
    sis_md = render_markdown(sis_plan)
    assert "correctness" in sis_md
    assert "安全目标" in sis_md
    assert "参数" in sis_md
    assert "artifact" in sis_md

    kem_plan = create_paper_plan(_idea("ML-KEM implementation audit", track="ML-KEM / ML-DSA Implementation Security"))
    kem_md = render_markdown(kem_plan)
    assert "side-channel" in kem_md
    assert "fault" in kem_md
    assert "constant-time" in kem_md
    assert "audit" in kem_md

    bkz_plan = create_paper_plan(_idea("BKZ lattice reduction plan", track="BKZ / Lattice Reduction"))
    bkz_md = render_markdown(bkz_plan)
    assert "BKZ" in bkz_md
    assert "fplll" in bkz_md
    assert "G6K" in bkz_md


def test_zk_privacy_plan_is_long_term_research_not_application_packaging() -> None:
    plan = create_paper_plan(_idea("ZK-friendly lattice credential", track="ZK-friendly PQ Privacy", score=88))
    markdown = render_markdown(plan)

    assert "不只是申请材料中的叙事点" in markdown
    assert "post-quantum anonymous credentials" in markdown
    assert "小原语、小 benchmark 或小实现 artifact" in markdown
    assert plan["plan_type"] == "long_term_phd_direction"


def test_force_overwrite_and_default_unique_paths() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = create_paper_plan(_idea("Force overwrite plan"))
        first_md, _, _ = write_plan(plan, root / "plans", root / "obsidian")
        first_md.write_text("manual note", encoding="utf-8")

        second_md, _, _ = write_plan(plan, root / "plans", root / "obsidian", force=False)
        assert second_md != first_md
        assert first_md.read_text(encoding="utf-8") == "manual note"

        forced_md, _, _ = write_plan(plan, root / "plans", root / "obsidian", force=True)
        assert forced_md == first_md
        assert "Paper Plan" in forced_md.read_text(encoding="utf-8")


def test_missing_source_papers_uses_todo_verify() -> None:
    plan = create_paper_plan(_idea("No source paper plan", source_papers=[]))
    markdown = render_markdown(plan)

    assert "TODO_VERIFY" in markdown
    assert plan["related_work_to_read"][0]["title"] == "TODO_VERIFY"
