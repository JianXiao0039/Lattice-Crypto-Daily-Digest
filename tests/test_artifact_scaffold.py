from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.artifact_scaffold import create_artifact_scaffold, render_project_brief, render_readme


def _plan(track: str, title: str = "Test Paper Plan") -> dict[str, object]:
    return {
        "plan_id": "plan-test",
        "title": title,
        "track": track,
        "paper_plan_score": 90,
        "core_research_question": "如何把该计划转化为可复现实验？",
        "why_this_is_not_trivial": "该计划要求明确技术接口和失败边界。",
        "why_this_is_not_blind_combination": "必须说明不是关键词拼接，而是可验证 MVP。",
        "minimum_viable_paper": "实现最小实验或构造，并比较 baseline。",
        "expected_contributions": {
            "理论贡献": "不作为当前 MVP 贡献。",
            "实验贡献": "最小可复现实验。",
            "artifact 贡献": "代码、配置和 README。",
        },
        "experiment_plan": ["跑 toy benchmark", "比较 baseline"],
        "proof_or_security_analysis_plan": ["需要分析安全目标和参数边界。"],
        "evaluation_metrics": ["success rate", "runtime"],
        "three_month_execution_plan": {
            "Week 1-2": ["补 related work", "写 MVP spec"],
            "Month 2": ["跑 baseline"],
        },
        "next_7_days": ["核对来源论文", "写配置模板"],
        "advisor_questions": ["这个 MVP 是否值得推进？"],
        "risks": ["实验不显著风险", "与已有工作重复风险"],
        "source_papers": [{"title": "Source Paper", "url": "https://example.test/paper"}],
    }


def _write_plan(root: Path, plan: dict[str, object]) -> Path:
    path = root / "plan.json"
    path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    return path


def test_create_artifact_from_paper_plan_json() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan_path = _write_plan(root, _plan("AI4Lattice"))

        result = create_artifact_scaffold(plan_path, root / "research_artifacts")

        assert result.artifact_dir.exists()
        assert (result.artifact_dir / "README.md").exists()
        assert (result.artifact_dir / "TODO.md").exists()
        assert (result.artifact_dir / "PROJECT_BRIEF.md").exists()
        assert (result.artifact_dir / "paper" / "outline.md").exists()


def test_dry_run_does_not_write_and_default_no_overwrite() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan_path = _write_plan(root, _plan("AI4Lattice"))

        dry = create_artifact_scaffold(plan_path, root / "artifacts", dry_run=True)
        assert not dry.artifact_dir.exists()

        create_artifact_scaffold(plan_path, root / "artifacts")
        try:
            create_artifact_scaffold(plan_path, root / "artifacts")
        except FileExistsError:
            pass
        else:
            raise AssertionError("expected FileExistsError for existing artifact without force")


def test_force_backs_up_existing_directory() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan_path = _write_plan(root, _plan("AI4Lattice"))
        first = create_artifact_scaffold(plan_path, root / "artifacts")
        (first.artifact_dir / "manual.txt").write_text("manual note", encoding="utf-8")

        forced = create_artifact_scaffold(plan_path, root / "artifacts", force=True)

        assert forced.backup_dir is not None
        assert (forced.backup_dir / "manual.txt").read_text(encoding="utf-8") == "manual note"
        assert not (forced.artifact_dir / "manual.txt").exists()


def test_track_specific_directories_and_files() -> None:
    checks = [
        (
            "Module-SIS Primitive",
            ["src/primitives", "src/params", "src/benchmark", "experiments/parameter_estimation", "paper/security_analysis.md"],
        ),
        (
            "AI4Lattice",
            ["src/datasets", "src/models", "src/attacks", "src/baselines", "configs/model/toy_transformer.yaml"],
        ),
        (
            "BKZ / Lattice Reduction",
            ["src/fplll_bridge", "src/g6k_bridge", "src/estimators", "configs/reduction/bkz_sweep.yaml"],
        ),
        (
            "ML-KEM / ML-DSA Implementation Security",
            ["src/audit", "src/ct_checks", "src/test_vectors", "docs/audit_checklist.md"],
        ),
        (
            "ZK-friendly PQ Privacy",
            ["src/commitments", "src/encodings", "src/protocols", "docs/privacy_model.md"],
        ),
    ]
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        for index, (track, expected) in enumerate(checks):
            case_dir = root / f"case-{index}"
            case_dir.mkdir(parents=True)
            plan_path = _write_plan(case_dir, _plan(track))
            result = create_artifact_scaffold(plan_path, root / "artifacts")
            for rel_path in expected:
                assert (result.artifact_dir / rel_path).exists(), rel_path


def test_readme_and_project_brief_are_conservative_and_clean() -> None:
    plan = _plan("AI4Lattice", title="<b>bad</b> contentReference oaicite id=abc")
    readme = render_readme(plan)
    brief = render_project_brief(plan)
    combined = readme + brief

    assert "Minimum viable paper" in readme
    assert "风险" in readme
    assert "需要导师拍板的问题" in brief
    assert "尚无实验结果" in combined
    assert "尚无安全证明" in combined
    assert "<b>" not in combined
    assert "contentReference" not in combined
    assert "oaicite" not in combined
    assert "id=" not in combined
    assert "实验结果表明" not in combined
    assert "已经证明安全" not in combined
