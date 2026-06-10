from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


DATES = tuple(f"2026-06-{day:02d}" for day in range(4, 11))


@dataclass(frozen=True)
class DailyCheck:
    date: str
    local_markdown: bool
    git_tracked: bool
    remote_present: bool | None


def _run(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], root)


def build_report(root: Path, remote_ref: str) -> dict[str, object]:
    remote_available = _git(root, "rev-parse", "--verify", "--quiet", remote_ref).returncode == 0
    help_result = _run([sys.executable, "-m", "lattice_digest.run", "--help"], root)
    date_help_available = help_result.returncode == 0 and "--date DATE" in help_result.stdout

    daily: list[DailyCheck] = []
    for target_date in DATES:
        path = f"digests/{target_date}.md"
        tracked = _git(root, "ls-files", "--error-unmatch", "--", path).returncode == 0
        remote_present: bool | None = None
        if remote_available:
            remote_present = _git(root, "cat-file", "-e", f"{remote_ref}:{path}").returncode == 0
        daily.append(
            DailyCheck(
                date=target_date,
                local_markdown=(root / path).exists(),
                git_tracked=tracked,
                remote_present=remote_present,
            )
        )

    weekly_json = root / "data" / "weekly" / "2026-W23.json"
    handoff_json = root / "handoffs" / "weekly" / "2026-W23-handoff-packets.json"
    handoff_markdown = root / "handoffs" / "weekly" / "2026-W23-handoff-packets.md"

    checks = {
        "date_help_available": date_help_available,
        "all_daily_local": all(item.local_markdown for item in daily),
        "all_daily_tracked": all(item.git_tracked for item in daily),
        "all_daily_remote": remote_available and all(item.remote_present is True for item in daily),
        "weekly_json_present": weekly_json.exists(),
        "handoff_json_present": handoff_json.exists(),
        "handoff_markdown_present": handoff_markdown.exists(),
    }
    required_passed = all(checks.values())

    return {
        "repository": str(root),
        "remote_ref": remote_ref,
        "remote_ref_available": remote_available,
        "checks": checks,
        "daily": [asdict(item) for item in daily],
        "required_passed": required_passed,
        "ci_status": "TODO_VERIFY_EXTERNAL_CI",
        "release_status_without_ci": "local_and_remote_artifact_checks_passed" if required_passed else "blocked",
    }


def print_report(report: dict[str, object]) -> None:
    print(f"Repository: {report['repository']}")
    print(f"Remote ref: {report['remote_ref']} (available={report['remote_ref_available']})")
    print()
    for name, result in report["checks"].items():  # type: ignore[union-attr]
        print(f"{name}: {'PASS' if result else 'FAIL'}")
    print()
    print("date | local | tracked | remote")
    print("-" * 42)
    for row in report["daily"]:  # type: ignore[index]
        remote = "TODO_VERIFY" if row["remote_present"] is None else str(row["remote_present"])
        print(f"{row['date']} | {row['local_markdown']} | {row['git_tracked']} | {remote}")
    print()
    print(f"required_passed: {report['required_passed']}")
    print("ci_status: TODO_VERIFY_EXTERNAL_CI")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify local and remote artifact prerequisites for the v0.4 release candidate.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--remote-ref", default="origin/main")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    if _git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        raise SystemExit(f"not a Git worktree: {root}")
    report = build_report(root, args.remote_ref)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print_report(report)
    return 0 if report["required_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
