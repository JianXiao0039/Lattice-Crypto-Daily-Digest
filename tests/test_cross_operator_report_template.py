from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cross_operator_comparison_template_has_required_columns() -> None:
    text = (ROOT / "docs/operations/cross_operator_output_comparison_template_v0.1.md").read_text(
        encoding="utf-8"
    )
    for column in [
        "Check item",
        "Codex result",
        "DeepSeek-Claude result",
        "Kimi Code result",
        "Match?",
        "Required fix",
        "Responsible operator",
    ]:
        assert column in text


def test_cross_operator_report_template_has_common_final_sections() -> None:
    text = (ROOT / "docs/operations/cross_operator_output_comparison_template_v0.1.md").read_text(
        encoding="utf-8"
    )
    for section in [
        "Operator",
        "Boundaries",
        "Commands Run",
        "Artifacts Generated",
        "Source Health",
        "Radar Output Quality",
        "Durable Artifact Status",
        "Failures / Warnings",
        "Next Recommended Operator",
        "Final Status",
    ]:
        assert section in text

