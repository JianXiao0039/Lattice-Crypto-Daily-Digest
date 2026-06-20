from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_paste_back_package_exists_and_has_required_fields() -> None:
    text = (ROOT / "docs/operations/fallback_operator_paste_back_package_v0.1.md").read_text(
        encoding="utf-8"
    )
    assert "BEGIN FALLBACK_OPERATOR_PASTE_BACK" in text
    assert "END FALLBACK_OPERATOR_PASTE_BACK" in text
    for field in [
        "## Operator",
        "## Tool / model",
        "## Date/time",
        "## Working directory",
        "## Boundary self-check",
        "## Commands run",
        "## Commands unavailable",
        "## Artifacts generated",
        "## Source-health table",
        "## Monthly audit result",
        "## Reading queue / Obsidian result",
        "## Failures / warnings",
        "## Git status before",
        "## Git status after",
        "## Final status",
        "## Request for Codex review",
    ]:
        assert field in text


def test_second_dry_run_plan_requires_paste_back_and_codex_comparison() -> None:
    text = (ROOT / "docs/operations/cross_operator_second_dry_run_plan_v0.1.md").read_text(
        encoding="utf-8"
    )
    assert "DeepSeek-Claude" in text
    assert "Kimi Code" in text
    assert "BEGIN FALLBACK_OPERATOR_PASTE_BACK" in text
    assert "Codex compares all outputs" in text
    assert "Stop and require Codex review" in text

