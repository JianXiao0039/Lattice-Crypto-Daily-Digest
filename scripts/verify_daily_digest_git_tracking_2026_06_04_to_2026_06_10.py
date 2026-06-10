from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


DATES = tuple(f"2026-06-{day:02d}" for day in range(4, 11))


@dataclass(frozen=True)
class PathAudit:
    path: str
    local_exists: bool
    git_tracked: bool
    ignored_by_standard_check: bool
    matching_ignore_rule: str | None
    latest_commit: str | None
    remote_present: bool | None


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _remote_ref_exists(root: Path, remote_ref: str) -> bool:
    return _git(root, "rev-parse", "--verify", "--quiet", remote_ref).returncode == 0


def audit_path(root: Path, relative_path: str, remote_ref: str, remote_available: bool) -> PathAudit:
    tracked = _git(root, "ls-files", "--error-unmatch", "--", relative_path).returncode == 0
    standard_ignore = _git(root, "check-ignore", "--quiet", "--", relative_path).returncode == 0
    ignore_rule_result = _git(root, "check-ignore", "-v", "--no-index", "--", relative_path)
    ignore_rule = ignore_rule_result.stdout.strip() or None
    log_result = _git(root, "log", "-1", "--format=%h %s", "--", relative_path)
    latest_commit = log_result.stdout.strip() or None

    remote_present: bool | None = None
    if remote_available:
        remote_present = _git(root, "cat-file", "-e", f"{remote_ref}:{relative_path}").returncode == 0

    return PathAudit(
        path=relative_path,
        local_exists=(root / relative_path).exists(),
        git_tracked=tracked,
        ignored_by_standard_check=standard_ignore,
        matching_ignore_rule=ignore_rule,
        latest_commit=latest_commit,
        remote_present=remote_present,
    )


def build_audit(root: Path, remote_ref: str) -> dict[str, object]:
    remote_available = _remote_ref_exists(root, remote_ref)
    rows: list[dict[str, object]] = []
    for target_date in DATES:
        digest = audit_path(root, f"digests/{target_date}.md", remote_ref, remote_available)
        data = audit_path(root, f"data/{target_date}.json", remote_ref, remote_available)
        rows.append({"date": target_date, "digest": asdict(digest), "data": asdict(data)})

    return {
        "repository": str(root),
        "remote_ref": remote_ref,
        "remote_ref_available": remote_available,
        "dates": rows,
    }


def _format_bool(value: bool | None) -> str:
    if value is None:
        return "TODO_VERIFY"
    return "yes" if value else "no"


def print_table(audit: dict[str, object]) -> None:
    print(f"Repository: {audit['repository']}")
    print(f"Remote ref: {audit['remote_ref']} (available={audit['remote_ref_available']})")
    print()
    print("date | digest local/tracked/ignored/rule/remote | data local/tracked/rule/remote | digest commit")
    print("-" * 140)
    for row in audit["dates"]:  # type: ignore[index]
        digest = row["digest"]
        data = row["data"]
        digest_state = "/".join(
            [
                _format_bool(digest["local_exists"]),
                _format_bool(digest["git_tracked"]),
                _format_bool(digest["ignored_by_standard_check"]),
                _format_bool(bool(digest["matching_ignore_rule"])),
                _format_bool(digest["remote_present"]),
            ]
        )
        data_state = "/".join(
            [
                _format_bool(data["local_exists"]),
                _format_bool(data["git_tracked"]),
                _format_bool(bool(data["matching_ignore_rule"])),
                _format_bool(data["remote_present"]),
            ]
        )
        print(f"{row['date']} | {digest_state} | {data_state} | {digest['latest_commit'] or 'none'}")

    print()
    print("Digest state columns: local/tracked/standard-ignore/matching-ignore-rule/remote")
    print("Data state columns: local/tracked/matching-ignore-rule/remote")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Git tracking for daily digest artifacts from 2026-06-04 to 2026-06-10.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--remote-ref", default="origin/main")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of the table.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    if _git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        raise SystemExit(f"not a Git worktree: {root}")
    audit = build_audit(root, args.remote_ref)
    if args.json:
        print(json.dumps(audit, ensure_ascii=True, indent=2))
    else:
        print_table(audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
