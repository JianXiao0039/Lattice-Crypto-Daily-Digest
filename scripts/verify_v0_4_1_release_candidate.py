from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.4.1"
HISTORICAL_TAG = "v0.4.0"
HISTORICAL_TARGET = "08c5f07967739ecd008773c4b167cd736848df88"


def _version_from_init(path: Path) -> str:
    match = re.search(r'__version__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"missing __version__: {path}")
    return match.group(1)


def read_versions(root: Path) -> dict[str, str]:
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    versions = {
        "pyproject": str(pyproject["project"]["version"]),
        "source_package": _version_from_init(root / "src" / "lattice_digest" / "__init__.py"),
    }
    bridge = root / "lattice_digest" / "__init__.py"
    versions["bridge_package"] = _version_from_init(bridge) if bridge.exists() else "missing"
    return versions


def validate_submission_contract(workflow_text: str) -> list[str]:
    failures: list[str] = []
    required = (
        'markdown_path="digests/${digest_date}.md"',
        'json_path="data/${digest_date}.json"',
        'git add -f -- "$markdown_path" "$json_path"',
        "git add -- papers.db",
    )
    for item in required:
        if item not in workflow_text:
            failures.append(f"missing workflow contract: {item}")
    forbidden = (
        "git add -f .",
        "git add -f -A",
        "git add -f --all",
        "git add -f -- digests/*.md",
        "git add -f -- data/*.json",
        "git add -f -- papers.db",
    )
    for item in forbidden:
        if item in workflow_text:
            failures.append(f"broad force-add forbidden: {item}")
    return failures


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def build_report(
    root: Path = ROOT,
    *,
    git: Callable[..., str] | None = None,
) -> dict[str, Any]:
    run_git = git or (lambda *args: _git(root, *args))
    versions = read_versions(root)
    workflow_text = (root / ".github" / "workflows" / "daily.yml").read_text(encoding="utf-8")
    staged = [line for line in run_git("diff", "--cached", "--name-only").splitlines() if line]
    tag_target = run_git("rev-parse", HISTORICAL_TAG)

    checks = [
        {
            "name": "active versions",
            "ok": all(value == EXPECTED_VERSION for value in versions.values()),
            "detail": versions,
            "critical": True,
        },
        {
            "name": "historical tag immutable",
            "ok": tag_target == HISTORICAL_TARGET,
            "detail": tag_target,
            "critical": True,
        },
        {
            "name": "daily submission allowlist",
            "ok": not validate_submission_contract(workflow_text),
            "detail": validate_submission_contract(workflow_text),
            "critical": True,
        },
        {
            "name": "release staging gate",
            "ok": not staged,
            "detail": staged,
            "critical": True,
        },
        {
            "name": "release notes",
            "ok": (root / "docs" / "releases" / "v0.4.1.md").exists(),
            "detail": "docs/releases/v0.4.1.md",
            "critical": True,
        },
    ]
    local_ready = all(item["ok"] for item in checks if item["critical"])
    external_gates = {
        "windows_ci": "TODO_VERIFY after publication",
        "ubuntu_ci": "TODO_VERIFY after publication",
        "durable_post_tag_daily_run": "missing",
    }
    return {
        "schema_version": 1,
        "candidate": EXPECTED_VERSION,
        "local_release_checks_passed": local_ready,
        "checks": checks,
        "external_gates": external_gates,
        "tag_decision": "blocked_by_multiple_conditions",
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["local_release_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
