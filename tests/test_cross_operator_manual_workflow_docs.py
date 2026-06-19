from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "docs" / "operations"


REQUIRED = [
    "cross_operator_manual_workflow_parity_v0.1.md",
    "codex_deepseek_kimi_command_matrix_v0.1.md",
    "manual_full_run_sop_v0.1.md",
    "manual_specific_date_and_range_sop_v0.1.md",
    "source_health_long_run_stability_sop_v0.1.md",
    "source_health_failure_interpretation_table_v0.1.md",
    "manual_operator_report_template_v0.1.md",
]


def _read(name: str) -> str:
    return (OPS / name).read_text(encoding="utf-8")


def test_cross_operator_docs_exist() -> None:
    missing = [name for name in REQUIRED if not (OPS / name).exists()]
    assert missing == []


def test_command_matrix_covers_public_manual_workflows() -> None:
    matrix = _read("codex_deepseek_kimi_command_matrix_v0.1.md")
    required_phrases = [
        "Daily latest",
        "Daily specific-date backfill",
        "Specific time range",
        "Weekly dry-run",
        "Weekly execute",
        "Monthly run",
        "Full manual run",
        "Source-health probe",
        "Durable verification",
        "Reading queue export",
        "Obsidian export",
        "Monthly quality audit",
        "Bilingual rationale quality audit",
        "Final report",
    ]
    for phrase in required_phrases:
        assert phrase in matrix
    assert "python -m lattice_digest.run --since 36h" in matrix
    assert "python -m lattice_digest.run --date YYYY-MM-DD" in matrix
    assert "python -m lattice_digest.monthly_synthesis --month YYYY-MM" in matrix


def test_report_template_has_required_safety_sections() -> None:
    text = _read("manual_operator_report_template_v0.1.md")
    for phrase in [
        "PhD_Application read/write: no",
        "ResearchArtifacts read/write: no",
        "ResearchOS write: no",
        "git add/commit/push/tag: no",
        "automation created: no",
        "anti-bot bypass used: no",
        "Codex review required: yes/no",
    ]:
        assert phrase in text
