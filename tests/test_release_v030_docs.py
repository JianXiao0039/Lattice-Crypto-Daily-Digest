from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA")


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_version_sources_are_v030() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    src_init = _read("src/lattice_digest/__init__.py")
    bridge_init = _read("lattice_digest/__init__.py")

    assert pyproject["project"]["version"] == "0.3.0"
    assert '__version__ = "0.3.0"' in src_init
    assert '__version__ = "0.3.0"' in bridge_init


def test_changelog_documents_v030_stabilization_release() -> None:
    changelog = _read("CHANGELOG.md")

    for needle in [
        "v0.3.0",
        "Workflow Command Center",
        "Manual low-load workflow profiles",
        "Ranking explainability",
        "Source Health Ledger",
        "Weekly Research Synthesis",
        "Obsidian Paper Note Scaffold",
        "No Windows Task Scheduler integration",
    ]:
        assert needle in changelog


def test_v030_release_doc_exists_and_states_no_scheduled_automation() -> None:
    release_doc = _read("docs/releases/v0.3.0.md")

    for needle in [
        "Research Workflow Stabilization Release",
        "Workflow Command Center",
        "Manual Low-Load Profile",
        "Windows Task Scheduler",
        "cron job",
        "automatic scheduled runs",
        "python -m lattice_digest.workflow doctor",
    ]:
        assert needle in release_doc


def test_readme_mentions_v030_workflow_command_center_and_low_load() -> None:
    readme = _read("README.md")

    for needle in [
        "v0.3.0 stable",
        "docs/releases/v0.3.0.md",
        "Workflow Command Center",
        "--low-load",
        "no Task Scheduler",
        "docs/workflow-command-center.md",
        "docs/manual-low-load-workflow.md",
    ]:
        assert needle in readme


def test_generated_artifacts_remain_ignored() -> None:
    gitignore = _read(".gitignore")

    for needle in [
        "exports/",
        "exports/workflow-runs/",
        "audits/",
        "state/reading-queue.json",
        "data/*.json",
        "data/weekly/",
        "digests/*.md",
        "digests/weekly/",
        "papers.db",
        ".env",
    ]:
        assert needle in gitignore


def test_v030_release_docs_do_not_contain_secret_patterns() -> None:
    combined = "\n".join(
        [
            _read("README.md"),
            _read("CHANGELOG.md"),
            _read("docs/releases/v0.3.0.md"),
            _read("docs/workflow-command-center.md"),
            _read("docs/manual-low-load-workflow.md"),
        ]
    )

    for pattern in SECRET_PATTERNS:
        assert pattern not in combined
    assert not re.search(r"github_pat_[A-Za-z0-9_]+", combined)
