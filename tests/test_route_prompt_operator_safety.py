from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKS = ROOT / "docs" / "research_tracks"
OPS = ROOT / "docs" / "operations"
FIXTURES = ROOT / "tests" / "fixtures" / "route_prompt"


def test_route_prompt_safety_docs_exist_and_forbid_private_paths() -> None:
    path = TRACKS / "v0.6_cross_operator_route_prompt_safety_policy_v0.1.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "D:\\Code\\CodexProjects\\PhD_Application" in text
    assert "D:\\ResearchArtifacts" in text
    assert "D:\\ResearchOS" in text
    assert "git add/commit/push/tag" in text
    assert "background automation" in text


def test_standardized_route_prompt_header_requires_operator_and_codex_review() -> None:
    text = (FIXTURES / "standardized_route_prompt_header_v0.1.md").read_text(encoding="utf-8")
    assert "Operator:" in text
    assert "Codex: primary engineering/release-maintenance operator" in text
    assert "DeepSeek-Claude: fallback runner/reviewer, no release ownership" in text
    assert "Kimi Code: lightweight fallback runner/reviewer, no release ownership" in text
    assert "Codex review for code changes" in text
    assert "source-health caveats" in text
