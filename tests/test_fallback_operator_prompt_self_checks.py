from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEEPSEEK = ROOT / "docs/operations/deepseek_claude_dry_run_prompt_v0.1.md"
KIMI = ROOT / "docs/operations/kimi_code_dry_run_prompt_v0.1.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_deepseek_prompt_includes_boundary_self_check() -> None:
    text = _read(DEEPSEEK)
    assert "DeepSeek-Claude Boundary Self-Check" in text
    for phrase in [
        "I will not read or write PhD_Application",
        "I will not read or write ResearchArtifacts",
        "I will not write ResearchOS",
        "I will not run git add/commit/push/tag",
        "I will not create automation",
        "I will not modify ranking/source/taxonomy",
        "I will ask for Codex review before any code change",
        "I will report unavailable commands honestly",
    ]:
        assert phrase in text


def test_kimi_prompt_includes_boundary_self_check() -> None:
    text = _read(KIMI)
    assert "Kimi Code Boundary Self-Check" in text
    for phrase in [
        "I received the full prompt",
        "I will only run explicit commands",
        "I will not infer unsupported command success",
        "I will not read/write private paths",
        "I will not run git add/commit/push/tag",
        "I will not create automation",
        "I will not modify source code unless explicitly authorized",
        "I will request Codex review for any code change",
    ]:
        assert phrase in text


def test_fallback_prompts_have_safety_bans_and_command_unavailable_rule() -> None:
    for path in [DEEPSEEK, KIMI]:
        text = _read(path)
        assert "D:\\Code\\CodexProjects\\PhD_Application" in text
        assert "D:\\ResearchArtifacts" in text
        assert "D:\\ResearchOS" in text
        assert "Run `git add`, `git commit`, `git push`, or `git tag`" in text
        assert "automatic future runs" in text
        assert "source fetchers" in text
        assert "ranking scores" in text
        assert "taxonomy semantics" in text
        assert "command_unavailable" in text


def test_fallback_prompts_require_same_report_sections_and_paste_back() -> None:
    sections = [
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
        "BEGIN FALLBACK_OPERATOR_PASTE_BACK",
    ]
    for path in [DEEPSEEK, KIMI]:
        text = _read(path)
        for section in sections:
            assert section in text

