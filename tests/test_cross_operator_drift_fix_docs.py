from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_DOCS = [
    "docs/operations/cross_operator_drift_taxonomy_v0.1.md",
    "docs/operations/fallback_operator_paste_back_package_v0.1.md",
    "docs/operations/cross_operator_second_dry_run_plan_v0.1.md",
    "docs/reports/phase-14h-cross-operator-drift-fix-patch.md",
    "docs/reports/phase-14h-drift-taxonomy-and-remediation.md",
    "docs/reports/phase-14h-deepseek-claude-prompt-fix-review.md",
    "docs/reports/phase-14h-kimi-code-prompt-fix-review.md",
    "docs/reports/phase-14h-cross-operator-acceptance-gate-review.md",
    "docs/reports/phase-14h-paper-radar-core-invariant-audit.md",
]


def test_phase_14h_docs_exist() -> None:
    missing = [path for path in REQUIRED_DOCS if not (ROOT / path).exists()]
    assert missing == []


def test_drift_taxonomy_has_required_labels() -> None:
    text = (ROOT / "docs/operations/cross_operator_drift_taxonomy_v0.1.md").read_text(
        encoding="utf-8"
    )
    for label in [
        "not_run_drift",
        "command_drift",
        "artifact_drift",
        "source_health_interpretation_drift",
        "boundary_drift",
        "report_format_drift",
        "environment_drift",
        "quality_audit_drift",
    ]:
        assert label in text


def test_phase_14h_preserves_phase_14g_grounded_findings() -> None:
    text = (ROOT / "docs/reports/phase-14h-cross-operator-drift-fix-patch.md").read_text(
        encoding="utf-8"
    )
    assert "Codex ran successfully with degraded but explicit source health" in text
    assert "DeepSeek-Claude was not run" in text
    assert "Kimi Code was not run" in text
    assert "Full cross-operator parity cannot be claimed" in text

