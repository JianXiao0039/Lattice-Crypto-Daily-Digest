from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA")


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_version_sources_are_v031() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    src_init = _read("src/lattice_digest/__init__.py")
    bridge_init = _read("lattice_digest/__init__.py")

    assert pyproject["project"]["version"] == "0.3.1"
    assert '__version__ = "0.3.1"' in src_init
    assert '__version__ = "0.3.1"' in bridge_init


def test_changelog_documents_v031_patch_release() -> None:
    changelog = _read("CHANGELOG.md")

    for needle in [
        "v0.3.1",
        "Deterministic E2E workflow acceptance suite",
        "Stale release test hotfix",
        "Manual operations runbook",
        "Recovery playbook",
        "Artifact retention policy",
        "Troubleshooting docs",
        "No Windows Task Scheduler integration",
    ]:
        assert needle in changelog


def test_v031_release_doc_exists_and_states_manual_only_boundaries() -> None:
    release_doc = _read("docs/releases/v0.3.1.md")

    for needle in [
        "Manual Operations Patch Release",
        "End-to-End Workflow Acceptance Suite",
        "manual-only workflow",
        "dry-run",
        "--low-load",
        "--no-network",
        "Windows Task Scheduler",
        "cron job",
        "automatic local scheduled runs",
    ]:
        assert needle in release_doc


def test_readme_links_v031_release_doc() -> None:
    readme = _read("README.md")

    for needle in [
        "v0.3.1 patch release",
        "docs/releases/v0.3.1.md",
        "docs/manual-operations-runbook.md",
        "docs/recovery-playbook.md",
        "docs/artifact-retention-policy.md",
        "docs/troubleshooting.md",
    ]:
        assert needle in readme


def test_v031_operator_docs_exist() -> None:
    for relative in [
        "docs/e2e-acceptance-suite.md",
        "docs/manual-operations-runbook.md",
        "docs/recovery-playbook.md",
        "docs/artifact-retention-policy.md",
        "docs/troubleshooting.md",
    ]:
        assert (ROOT / relative).exists()


def test_v031_release_docs_do_not_contain_secret_patterns() -> None:
    combined = "\n".join(
        [
            _read("README.md"),
            _read("CHANGELOG.md"),
            _read("docs/releases/v0.3.1.md"),
            _read("docs/e2e-acceptance-suite.md"),
            _read("docs/manual-operations-runbook.md"),
            _read("docs/recovery-playbook.md"),
            _read("docs/artifact-retention-policy.md"),
            _read("docs/troubleshooting.md"),
        ]
    )

    for pattern in SECRET_PATTERNS:
        assert pattern not in combined
    assert not re.search(r"github_pat_[A-Za-z0-9_]+", combined)
