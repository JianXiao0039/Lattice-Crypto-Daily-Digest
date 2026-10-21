from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_daily_workflow_exports_only_public_candidates() -> None:
    workflow = (ROOT / ".github/workflows/daily.yml").read_text(encoding="utf-8")
    assert "lattice_digest.cloud_daily" in workflow
    assert "contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "git add" not in workflow and "git push" not in workflow
    assert "${{ runner.temp }}/public-candidate/" in workflow
    assert "papers.db" not in workflow


def test_daily_workflow_has_no_broad_force_add() -> None:
    workflow = (ROOT / ".github" / "workflows" / "daily.yml").read_text(encoding="utf-8")

    forbidden = (
        "git add -f .",
        "git add -f -A",
        "git add -f --all",
        "git add -f -- digests/*.md",
        "git add -f -- data/*.json",
        "git add -f -- papers.db",
    )
    for command in forbidden:
        assert command not in workflow


def test_daily_workflow_validates_before_upload() -> None:
    workflow = (ROOT / ".github/workflows/daily.yml").read_text(encoding="utf-8")
    assert workflow.index("Independent production report and public privacy gates") < workflow.index("actions/upload-artifact@v4")
    assert "verify(root/'cloud-canonical', 'daily', context['target_date'])" in workflow
    assert "inspect_tree(root/'public-candidate')" in workflow
    assert "date +" not in workflow and "grep -q" not in workflow
