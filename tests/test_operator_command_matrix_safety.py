from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs" / "operations" / "codex_deepseek_kimi_command_matrix_v0.1.md"
PARITY = ROOT / "docs" / "operations" / "cross_operator_manual_workflow_parity_v0.1.md"


def test_command_matrix_marks_codex_review_for_risky_changes() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    assert "Codex review" in text
    assert "yes if code changes" in text.lower()
    assert "yes if classification logic changes" in text.lower()
    assert "yes if verifier changes" in text.lower()
    assert "not release owners" in text.lower()


def test_command_matrix_documents_expected_artifacts_and_failures() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    assert "Expected artifacts" in text
    assert "Failure interpretation" in text
    assert "source-starved" in text
    assert "missing artifact blocks durable evidence" in text
    assert "keyword-only" in text


def test_parity_doc_forbids_private_paths_and_manual_annotation() -> None:
    text = PARITY.read_text(encoding="utf-8")
    assert "D:\\Code\\CodexProjects\\PhD_Application" in text
    assert "D:\\ResearchArtifacts" in text
    assert "D:\\ResearchOS" in text
    assert "manual annotation" in text
    assert "human-gold" in text
