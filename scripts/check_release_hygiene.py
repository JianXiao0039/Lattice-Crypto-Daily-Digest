from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
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

CANONICAL_GENERATED_ARTIFACT_PATTERNS = (
    "data/*/daily/*.json",
    "data/*/weekly/*.json",
    "data/*/monthly/*.json",
    "digests/*/daily/*.md",
    "digests/*/weekly/*.md",
    "digests/*/monthly/*.md",
)

SOURCE_CODE_DELETE_PATTERNS = (
    "src/*",
    "scripts/*",
)

LEGACY_DAILY_JSON_RE = re.compile(r"^data/(\d{4})-(\d{2})-(\d{2})\.json$")
LEGACY_WEEKLY_JSON_RE = re.compile(r"^data/weekly/(\d{4})-W(\d{2})\.json$")
LEGACY_MONTHLY_JSON_RE = re.compile(r"^data/monthly/(\d{4})-(\d{2})\.json$")


class HygieneError(RuntimeError):
    pass


def _run_git(args: list[str]) -> list[str]:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE)
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def _run_git_status(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_valid(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return True


def _is_ignored(path: str) -> bool:
    result = _run_git_status(["check-ignore", "-q", "--no-index", "--", path])
    return result.returncode == 0


def _staged_name_status_entries() -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in _run_git(["diff", "--cached", "--name-status"]):
        parts = line.split("\t")
        if len(parts) >= 2:
            entries.append((parts[0], parts[-1]))
    return entries


def _legacy_json_counterpart(path: str) -> str | None:
    normalized = path.replace("\\", "/")
    if match := LEGACY_DAILY_JSON_RE.match(normalized):
        year, month, day = match.groups()
        return f"data/{year}/daily/{year}-{month}-{day}.json"
    if match := LEGACY_WEEKLY_JSON_RE.match(normalized):
        iso_year, week = match.groups()
        return f"data/{iso_year}/weekly/{iso_year}-W{week}.json"
    if match := LEGACY_MONTHLY_JSON_RE.match(normalized):
        year, month = match.groups()
        return f"data/{year}/monthly/{year}-{month}.json"
    return None


def _verified_generated_artifact_untracking(path: str, staged_paths: set[str]) -> tuple[bool, str]:
    canonical = _legacy_json_counterpart(path)
    if canonical is None:
        return False, "not_a_recognized_legacy_generated_json_path"
    if canonical in staged_paths:
        return False, "canonical_counterpart_is_staged"

    legacy_path = ROOT / path
    canonical_path = ROOT / canonical
    if not legacy_path.is_file():
        return False, "legacy_working_tree_file_missing"
    if not _is_ignored(path):
        return False, "legacy_path_not_ignored_after_untracking"
    if not canonical_path.is_file():
        return False, "canonical_counterpart_missing"
    if not _json_valid(legacy_path):
        return False, "legacy_json_invalid"
    if not _json_valid(canonical_path):
        return False, "canonical_json_invalid"
    if _sha256(legacy_path) != _sha256(canonical_path):
        return False, "legacy_canonical_hash_mismatch"
    return True, "authorized_generated_artifact_untracking_verified"


def migration_aware_staged_hygiene(entries: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    staged_paths = {path for _, path in entries}
    blocked: list[str] = []
    accepted: list[str] = []
    for status, path in entries:
        if _matches(path, NEVER_TRACK_PATTERNS):
            blocked.append(path)
            continue
        if status == "D":
            if _matches(path, GENERATED_ARTIFACT_PATTERNS):
                ok, reason = _verified_generated_artifact_untracking(path, staged_paths)
                if ok:
                    accepted.append(f"{path}:{reason}")
                else:
                    blocked.append(f"{path}:{reason}")
                continue
            if _matches(path, SOURCE_CODE_DELETE_PATTERNS):
                blocked.append(f"{path}:source_code_deletion")
                continue
            blocked.append(f"{path}:unverified_staged_deletion")
        elif _matches(path, GENERATED_ARTIFACT_PATTERNS + CANONICAL_GENERATED_ARTIFACT_PATTERNS):
            blocked.append(path)
    return sorted(blocked), sorted(accepted)


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
        blocked, accepted = migration_aware_staged_hygiene(_staged_name_status_entries())
        if blocked:
            raise HygieneError("Forbidden staged paths: " + ", ".join(blocked))
        if accepted:
            messages.append("authorized_generated_artifact_untracking_verified: " + ", ".join(accepted))

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
