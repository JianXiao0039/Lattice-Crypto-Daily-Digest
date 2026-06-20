from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


PROMPTS = [
    ROOT / "docs/operations/codex_dry_run_prompt_v0.1.md",
    ROOT / "docs/operations/deepseek_claude_dry_run_prompt_v0.1.md",
    ROOT / "docs/operations/kimi_code_dry_run_prompt_v0.1.md",
]


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_each_prompt_forbids_private_paths_and_git_writes() -> None:
    for path in PROMPTS:
        text = _text(path)
        assert "D:\\Code\\CodexProjects\\PhD_Application" in text
        assert "D:\\ResearchArtifacts" in text
        assert "D:\\ResearchOS" in text
        assert "run `git add`, `git commit`, `git push`, or `git tag`" in text
        assert "Forbidden" in text


def test_each_prompt_forbids_automation_and_source_ranking_taxonomy_changes() -> None:
    for path in PROMPTS:
        text = _text(path)
        assert "background services" in text
        assert "automatic future runs" in text
        assert "source fetchers" in text
        assert "ranking scores" in text
        assert "taxonomy semantics" in text
        assert "query expansion" in text
        assert "negative keyword behavior" in text


def test_each_prompt_contains_same_safe_task_set() -> None:
    required_commands = [
        "python -m lattice_digest.run --since 36h --output markdown,json --send none",
        "python -m lattice_digest.workflow weekly --low-load --skip-hygiene",
        "python -m lattice_digest.monthly_synthesis --month 2026-06",
        "python scripts/probe_source_health.py --low-load",
        "python scripts/verify_durable_artifacts.py --date 2026-06-15 --week 2026-W25 --month 2026-06",
        "python scripts/export_reading_queue.py --latest",
        "python scripts/export_obsidian_notes.py --latest",
        "python scripts/audit_monthly_rationale_quality.py --latest",
        "git diff --check",
        "git diff --cached --check",
        "git status -sb",
    ]
    for path in PROMPTS:
        text = _text(path)
        for command in required_commands:
            assert command in text

