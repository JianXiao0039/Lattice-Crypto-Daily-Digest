from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA")


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_v031_release_artifacts_are_archival_docs() -> None:
    assert (ROOT / "docs" / "releases" / "v0.3.1.md").exists()
    assert "v0.3.1" in _read("CHANGELOG.md")


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


def test_v031_release_does_not_require_readme_current_release_wording() -> None:
    readme = _read("README.md")
    release_doc = _read("docs/releases/v0.3.1.md")

    assert "v0.3.1 patch release" not in readme
    assert "v0.3.1" in release_doc
    assert "patch release" in release_doc or "Manual Operations Patch Release" in release_doc


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
