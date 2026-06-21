from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE_14I_DOCS = [
    ROOT / "docs/reports/phase-14i-second-cross-operator-dry-run.md",
    ROOT / "docs/reports/phase-14i-cross-operator-final-comparison.md",
    ROOT / "docs/reports/phase-14i-fallback-acceptance-decision.md",
    ROOT / "docs/operations/cross_operator_second_dry_run_result_v0.1.md",
    ROOT / "docs/operations/cross_operator_fallback_use_policy_after_14i_v0.1.md",
]


def test_docs_do_not_claim_parity_passed_without_fallback_runs() -> None:
    forbidden = [
        "second_cross_operator_dry_run_passed",
        "cross_operator_parity_accepted_with_codex_review",
        "deepseek_claude_fallback_accepted_with_codex_review",
        "kimi_code_fallback_accepted_with_codex_review",
    ]
    for path in PHASE_14I_DOCS:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text


def test_docs_preserve_safety_boundaries() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in PHASE_14I_DOCS)
    assert "No `git add`, `git commit`, `git push`, or `git tag`" in text
    assert "No private PhD_Application, ResearchArtifacts, or ResearchOS path" in text
    assert "No manual annotation workflow" in text
    assert "No external LLM runtime" in text
    assert "daily/weekly/monthly paper discovery" in text

