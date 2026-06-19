from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "docs" / "operations"


def _read(name: str) -> str:
    return (OPS / name).read_text(encoding="utf-8").lower()


def test_deepseek_and_kimi_fallback_policies_exist() -> None:
    assert (OPS / "deepseek_claude_emergency_fallback_v0.1.md").exists()
    assert (OPS / "kimi_code_emergency_fallback_v0.1.md").exists()
    assert (OPS / "operator_parity_no_release_owner_policy_v0.1.md").exists()


def test_backup_operators_are_not_release_owners_and_cannot_tag() -> None:
    for name in [
        "deepseek_claude_emergency_fallback_v0.1.md",
        "kimi_code_emergency_fallback_v0.1.md",
        "operator_parity_no_release_owner_policy_v0.1.md",
    ]:
        text = _read(name)
        assert "release owner" in text or "release ownership" in text
        assert "git add, git commit, git push, or git tag" in text
        assert "tag creation" in text
        assert "private path access" in text
        assert "background automation" in text


def test_codex_review_required_for_code_or_verifier_changes() -> None:
    combined = "\n".join(
        _read(name)
        for name in [
            "deepseek_claude_emergency_fallback_v0.1.md",
            "kimi_code_emergency_fallback_v0.1.md",
            "operator_parity_no_release_owner_policy_v0.1.md",
        ]
    )
    assert "codex review is required" in combined
    assert "code" in combined
    assert "test" in combined
    assert "verifier" in combined
    assert "source-health classification" in combined or "source-health" in combined
