from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "docs" / "operations"


def _read(name: str) -> str:
    return (OPS / name).read_text(encoding="utf-8")


def test_backup_operator_policies_forbid_private_paths_and_release_ops():
    for name in [
        "deepseek_claude_operator_policy_v0.1.md",
        "kimi_code_operator_policy_v0.1.md",
    ]:
        text = _read(name).lower()
        assert "private phd application" in text
        assert "researchartifacts" in text
        assert "researchos" in text
        assert "commit, push, or tag" in text
        assert "release operations" in text or "release owner" in text


def test_handoff_template_records_safety_and_git_status():
    text = _read("operator_handoff_template_v0.1.md")
    assert "`git status -sb`" in text
    assert "Private paths accessed: no" in text
    assert "Background automation created: no" in text
    assert "Git write operations executed: no" in text


def test_no_manual_annotation_dependency_in_runbooks():
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in OPS.glob("*.md"))
    assert "do not create manual annotation" in combined
    assert "does not require manual annotation" in combined
    assert "human-gold" in combined
