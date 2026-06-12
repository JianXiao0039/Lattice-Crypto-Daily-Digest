from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

NEVER_TRACK_PATTERNS = (
    "exports/*",
    "exports",
    "audits/*",
    "audits",
    ".pytest_tmp/*",
    ".pytest_tmp",
    "__pycache__/*",
    "__pycache__",
    "*/__pycache__/*",
    ".env",
    "state/reading-queue.json",
    "state/reading-queue.lock",
)

GENERATED_ARTIFACT_PATTERNS = (
    "data/*.json",
    "digests/*.md",
    "papers.db",
)


class HygieneError(RuntimeError):
    pass


def _run_git(args: list[str]) -> list[str]:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE)
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def _read_current_version() -> str:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = pyproject["project"]["version"]
    init_text = (ROOT / "src" / "lattice_digest" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init_text)
    if not match:
        raise HygieneError("src/lattice_digest/__init__.py does not expose __version__.")
    init_version = match.group(1)
    if project_version != init_version:
        raise HygieneError(f"Version mismatch: pyproject={project_version}, __version__={init_version}.")
    return project_version


def _check_release_docs(version: str) -> None:
    release_doc = ROOT / "docs" / "releases" / f"v{version}.md"
    if not release_doc.exists():
        raise HygieneError(f"Missing release document: {release_doc.relative_to(ROOT)}")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"v{version}" not in changelog and version not in changelog:
        raise HygieneError(f"CHANGELOG.md does not mention current version {version}.")


def forbidden_staged_paths(paths: list[str]) -> list[str]:
    patterns = NEVER_TRACK_PATTERNS + GENERATED_ARTIFACT_PATTERNS
    return sorted(path for path in paths if _matches(path, patterns))


def forbidden_tracked_paths(paths: list[str], *, strict_generated: bool = False) -> list[str]:
    patterns = NEVER_TRACK_PATTERNS + (GENERATED_ARTIFACT_PATTERNS if strict_generated else ())
    return sorted(path for path in paths if _matches(path, patterns))


def run_checks(*, strict_tracked_generated: bool = False, check_staged: bool = True) -> list[str]:
    messages: list[str] = []
    version = _read_current_version()
    _check_release_docs(version)
    messages.append(f"version ok: {version}")

    if check_staged:
        staged = forbidden_staged_paths(_run_git(["diff", "--cached", "--name-only"]))
        if staged:
            raise HygieneError("Forbidden generated artifacts are staged: " + ", ".join(staged))

    tracked = forbidden_tracked_paths(_run_git(["ls-files"]), strict_generated=strict_tracked_generated)
    if tracked:
        raise HygieneError("Forbidden artifacts are tracked: " + ", ".join(tracked))

    if not strict_tracked_generated:
        legacy = forbidden_tracked_paths(_run_git(["ls-files"]), strict_generated=True)
        legacy = [path for path in legacy if _matches(path, GENERATED_ARTIFACT_PATTERNS)]
        if legacy:
            messages.append(
                "legacy tracked digest artifacts present; run with --strict-tracked-generated after repository cleanup to fail on them"
            )

    messages.append("release hygiene ok")
    return messages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check release metadata and generated-artifact hygiene.")
    parser.add_argument(
        "--strict-tracked-generated",
        action="store_true",
        help="Also fail if data/*.json, digests/*.md, or papers.db are tracked. Enable after legacy artifacts are removed.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        messages = run_checks(strict_tracked_generated=args.strict_tracked_generated)
    except (HygieneError, subprocess.CalledProcessError) as exc:
        print(f"release hygiene failed: {exc}", file=sys.stderr)
        return 1
    for message in messages:
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
