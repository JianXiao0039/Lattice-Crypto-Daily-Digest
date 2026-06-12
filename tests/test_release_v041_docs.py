from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA")


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_version_sources_are_v041() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    src_init = _read("src/lattice_digest/__init__.py")
    bridge = ROOT / "lattice_digest" / "__init__.py"

    assert pyproject["project"]["version"] == "0.4.1"
    assert '__version__ = "0.4.1"' in src_init
    if bridge.exists():
        assert '__version__ = "0.4.1"' in bridge.read_text(encoding="utf-8")


def test_v041_release_docs_record_corrective_scope() -> None:
    release = _read("docs/releases/v0.4.1.md")
    changelog = _read("CHANGELOG.md")
    readme = _read("README.md")

    for needle in [
        "v0.4.1",
        "v0.4.0",
        "0.3.3",
        "forward slashes",
        "Asia/Singapore",
        "non_persisted_automation_post_tag_actual",
        "No ranking or taxonomy change",
    ]:
        assert needle in release
    assert "v0.4.1" in changelog
    assert "docs/releases/v0.4.1.md" in readme


def test_v041_docs_contain_no_secret_patterns() -> None:
    combined = "\n".join(
        [
            _read("README.md"),
            _read("CHANGELOG.md"),
            _read("docs/releases/v0.4.1.md"),
            _read("docs/index.md"),
        ]
    )

    for pattern in SECRET_PATTERNS:
        assert pattern not in combined
    assert not re.search(r"github_pat_[A-Za-z0-9_]+", combined)
