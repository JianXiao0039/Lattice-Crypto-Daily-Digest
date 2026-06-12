from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_daily_workflow_force_adds_only_verified_dated_artifacts() -> None:
    workflow = (ROOT / ".github" / "workflows" / "daily.yml").read_text(encoding="utf-8")

    assert 'markdown_path="digests/${digest_date}.md"' in workflow
    assert 'json_path="data/${digest_date}.json"' in workflow
    assert 'git add -f -- "$markdown_path" "$json_path"' in workflow
    assert "git add -- papers.db" in workflow


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


def test_daily_workflow_validates_before_staging() -> None:
    workflow = (ROOT / ".github" / "workflows" / "daily.yml").read_text(encoding="utf-8")

    assert workflow.index("- name: Verify generated artifacts") < workflow.index("- name: Commit generated digest")
    assert 'test -f "$markdown_path"' in workflow
    assert 'test -f "$json_path"' in workflow
