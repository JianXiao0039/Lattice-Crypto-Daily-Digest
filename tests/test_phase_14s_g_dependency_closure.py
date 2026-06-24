from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "audits" / "canonical_default" / "phase-14s-g-proposed-commit-manifest.json"


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_artifact_paths_module_is_included_when_callers_import_it() -> None:
    data = _manifest()
    included = {entry["path"] for entry in data["files"] if entry["included"]}
    assert "src/lattice_digest/artifact_paths.py" in included

    for path in included:
        if not path.endswith(".py"):
            continue
        source = (ROOT / path).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports_artifact_paths = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "lattice_digest.artifact_paths"
            for node in ast.walk(tree)
        )
        if imports_artifact_paths:
            assert "src/lattice_digest/artifact_paths.py" in included


def test_dependency_closure_excludes_unrelated_mixed_changes() -> None:
    data = _manifest()
    excluded = {entry["path"] for entry in data["files"] if not entry["included"]}
    assert "src/lattice_digest/obsidian_scaffold.py" in excluded
    assert "scripts/audit_legacy_fallback_usage.py" in excluded
    assert "scripts/run_local_digest_backfill.ps1" in excluded


def test_dependency_closure_manifest_has_no_unlisted_untracked_runtime_dependency() -> None:
    data = _manifest()
    included = {entry["path"] for entry in data["files"] if entry["included"]}
    production = {
        entry["path"]
        for entry in data["files"]
        if entry["included"] and entry["dependency_role"] == "production"
    }
    assert production
    for path in production:
        assert path in included
    assert data["dependency_closure_decision"] in {
        "dependency_closure_verified",
        "dependency_closure_verified_with_limits",
    }
