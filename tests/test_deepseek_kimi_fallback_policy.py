from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKS = ROOT / "docs" / "research_tracks"


def test_deepseek_and_kimi_route_prompt_improvement_docs_exist() -> None:
    assert (TRACKS / "v0.6_deepseek_claude_route_prompt_improvement_v0.1.md").exists()
    assert (TRACKS / "v0.6_kimi_code_route_prompt_improvement_v0.1.md").exists()


def test_deepseek_kimi_docs_require_codex_review_and_no_release_work() -> None:
    combined = "\n".join(
        (TRACKS / name).read_text(encoding="utf-8").lower()
        for name in [
            "v0.6_deepseek_claude_route_prompt_improvement_v0.1.md",
            "v0.6_kimi_code_route_prompt_improvement_v0.1.md",
        ]
    )
    assert "codex review" in combined
    assert "no release ownership" in combined
    assert "git add/commit/push/tag" in combined
    assert "private paths" in combined
    assert "background automation" in combined
