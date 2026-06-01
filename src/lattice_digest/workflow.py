from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from lattice_digest import __version__


SCHEMA_VERSION = 1
DEFAULT_WORKFLOW_DIR = Path("exports") / "workflow-runs"


@dataclass
class WorkflowOptions:
    workflow: str
    execute: bool = False
    days: int = 7
    from_date: str | None = None
    to_date: str | None = None
    since: str = "7d"
    output: str = "markdown,json"
    send: str = "none"
    skip_hygiene: bool = False
    generate_notes: bool = False
    continue_on_error: bool = False
    low_load: bool = False
    offline: bool = False
    no_network: bool = False
    skip_heavy_sources: bool = False
    skip_zotero: bool = False
    skip_notes: bool = False
    skip_progress: bool = False
    yes: bool = False
    output_dir: Path = DEFAULT_WORKFLOW_DIR


@dataclass
class StepRecord:
    name: str
    command: str
    outputs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    status: str = "planned"
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "command": self.command,
            "outputs": self.outputs,
            "warnings": self.warnings,
            "error": self.error,
        }


class WorkflowStepError(RuntimeError):
    def __init__(self, step: StepRecord) -> None:
        super().__init__(f"workflow step failed: {step.name}: {step.error}")
        self.step = step


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _date_window(options: WorkflowOptions) -> tuple[date, date]:
    if options.from_date and options.to_date:
        return _parse_date(options.from_date), _parse_date(options.to_date)
    end = _parse_date(options.to_date) if options.to_date else datetime.now().date()
    return end - timedelta(days=int(options.days or 7) - 1), end


def _week_id(value: date) -> str:
    iso = value.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _run_dir(options: WorkflowOptions) -> Path:
    run_date = datetime.now().date().isoformat()
    return options.output_dir / f"{run_date}-{options.workflow}"


def _safe_json_load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _latest(pattern: str) -> Path | None:
    matches = sorted(Path().glob(pattern), key=lambda item: str(item))
    return matches[-1] if matches else None


def _run_git_status() -> tuple[bool, str]:
    try:
        result = subprocess.run(["git", "status", "--porcelain"], check=True, text=True, stdout=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as exc:
        return True, f"unknown ({exc})"
    output = result.stdout.strip()
    return bool(output), "dirty" if output else "clean"


class WorkflowRunner:
    def hygiene(self) -> dict[str, Any]:
        from scripts.check_release_hygiene import run_checks

        return {"messages": run_checks()}

    def daily(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, Any]:
        from lattice_digest import run as daily_run

        argv = ["--since", _effective_since(options), "--output", options.output, "--send", options.send]
        if dry_run:
            argv.append("--dry-run")
        code = daily_run.main(argv)
        if code:
            raise RuntimeError(f"daily digest returned {code}")
        return {"outputs": ["data/YYYY-MM-DD.json", "digests/YYYY-MM-DD.md", "papers.db"]}

    def weekly_synthesis(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, Any]:
        from lattice_digest import weekly_synthesis

        argv = ["--days", str(options.days)]
        if options.from_date:
            argv.extend(["--from-date", options.from_date])
        if options.to_date:
            argv.extend(["--to-date", options.to_date])
        if dry_run:
            argv.append("--dry-run")
        code = weekly_synthesis.main(argv)
        if code:
            raise RuntimeError(f"weekly synthesis returned {code}")
        start, end = _date_window(options)
        week = _week_id(end)
        return {"outputs": [f"data/weekly/{week}.json", f"digests/weekly/{week}.md"]}

    def research_artifact_export(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, Any]:
        from lattice_digest.research_artifact_export import generate_research_artifact_export

        result = generate_research_artifact_export(
            days=options.days,
            from_date=options.from_date,
            to_date=options.to_date,
            formats=_artifact_formats(options),
            dry_run=dry_run,
        )
        outputs = [str(path) for path in result.get("written_paths", [])] or [str(result.get("export_root"))]
        return {"outputs": outputs}

    def reading_queue_import(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, Any]:
        from lattice_digest.reading_queue import DEFAULT_STATE_PATH, import_queue, load_import_candidates, load_state, save_state

        candidates, metadata = load_import_candidates(
            days=options.days,
            from_date=options.from_date,
            to_date=options.to_date,
        )
        state, summary = import_queue(load_state(DEFAULT_STATE_PATH), candidates)
        if not dry_run:
            save_state(DEFAULT_STATE_PATH, state)
        return {"outputs": [str(DEFAULT_STATE_PATH)], "warnings": [f"summary={summary}", f"input={metadata.get('input_mode')}"]}

    def obsidian_scaffold(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, Any]:
        from lattice_digest.obsidian_scaffold import generate_scaffolds

        result = generate_scaffolds(dry_run=dry_run)
        outputs = [str(entry["path"]) for entry in result["plan"]["entries"]]
        return {"outputs": outputs, "warnings": [f"selected={len(outputs)}"]}

    def research_progress(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, Any]:
        from lattice_digest.research_progress import generate_research_progress

        result = generate_research_progress(
            days=options.days,
            from_date=options.from_date,
            to_date=options.to_date,
            output_dir=Path("exports") / "research-progress",
            dry_run=dry_run,
        )
        outputs = [str(path) for path in result.get("written", [])] or [str(path) for path in result["manifest"]["output_files"]]
        return {"outputs": outputs}


def _step(
    name: str,
    command: str,
    outputs: list[str] | None = None,
    warnings: list[str] | None = None,
) -> StepRecord:
    return StepRecord(name=name, command=command, outputs=outputs or [], warnings=warnings or [])


def _daily_steps(options: WorkflowOptions) -> list[StepRecord]:
    steps: list[StepRecord] = []
    if not options.skip_hygiene:
        steps.append(_step("release hygiene", "python scripts/check_release_hygiene.py"))
    warnings = _profile_warnings(options)
    if _network_disabled(options):
        warnings.append("offline/no-network profile skips daily digest fetches; no network requests are performed")
    if options.low_load and options.since == "7d":
        warnings.append("low-load profile uses --since 36h instead of the workflow default 7d")
    if options.execute and not options.yes and not options.low_load and not _network_disabled(options):
        warnings.append("heavy network daily fetch planned; use --yes to acknowledge or --low-load/--no-network for a lighter manual run")
    steps.append(
        _step(
            "daily digest",
            f"python -m lattice_digest.run --since {_effective_since(options)} --output {options.output} --send {options.send}",
            ["data/YYYY-MM-DD.json", "digests/YYYY-MM-DD.md", "papers.db"],
            warnings,
        )
    )
    return steps


def _weekly_steps(options: WorkflowOptions) -> list[StepRecord]:
    steps: list[StepRecord] = []
    if not options.skip_hygiene:
        steps.append(_step("release hygiene", "python scripts/check_release_hygiene.py"))
    start, end = _date_window(options)
    week = _week_id(end)
    date_flags = _date_flags(options)
    steps.append(
        _step(
            "weekly synthesis",
            f"python -m lattice_digest.weekly_synthesis {date_flags}".strip(),
            [f"data/weekly/{week}.json", f"digests/weekly/{week}.md"],
            _profile_warnings(options),
        )
    )
    steps.append(
        _step(
            "research artifact export",
            f"python -m lattice_digest.research_artifact_export {date_flags} --formats {_artifact_formats(options)}".strip(),
            [f"exports/research-artifacts/{end.isoformat()}"],
            ["zotero export pack format skipped"] if options.skip_zotero else [],
        )
    )
    steps.append(
        _step(
            "reading queue import",
            f"python -m lattice_digest.reading_queue import {date_flags}".strip(),
            ["state/reading-queue.json"],
        )
    )
    if options.skip_notes:
        steps.append(
            _step(
                "obsidian scaffold",
                "python -m lattice_digest.obsidian_scaffold generate",
                ["exports/obsidian-paper-notes/Papers"],
                ["skipped by --skip-notes"],
            )
        )
    else:
        steps.append(
            _step(
                "obsidian scaffold",
                "python -m lattice_digest.obsidian_scaffold generate",
                ["exports/obsidian-paper-notes/Papers"],
                [] if options.generate_notes else ["forced dry-run unless --generate-notes is provided"],
            )
        )
    if not options.skip_progress:
        steps.append(
            _step(
                "research progress",
                f"python -m lattice_digest.research_progress generate {date_flags}".strip(),
                [f"exports/research-progress/{week}"],
            )
        )
    else:
        steps.append(
            _step(
                "research progress",
                f"python -m lattice_digest.research_progress generate {date_flags}".strip(),
                [f"exports/research-progress/{week}"],
                ["skipped by --skip-progress"],
            )
        )
    return steps


def _network_disabled(options: WorkflowOptions) -> bool:
    return options.offline or options.no_network


def _profile_name(options: WorkflowOptions) -> str:
    if _network_disabled(options):
        return "offline/no-network"
    if options.low_load:
        return "low-load"
    return "normal"


def _effective_since(options: WorkflowOptions) -> str:
    if options.low_load and options.since == "7d":
        return "36h"
    return options.since


def _artifact_formats(options: WorkflowOptions) -> str:
    if options.skip_zotero:
        return "obsidian,advisor,backlog"
    return "obsidian,advisor,backlog,zotero"


def _profile_warnings(options: WorkflowOptions) -> list[str]:
    warnings: list[str] = []
    if options.low_load:
        warnings.append("low-load profile: manual, dry-run by default, reduced default daily lookback")
    if options.offline:
        warnings.append("offline profile: no network-dependent steps should run")
    if options.no_network:
        warnings.append("no-network profile: network-dependent steps are skipped")
    if options.skip_heavy_sources:
        warnings.append("--skip-heavy-sources is a workflow-level hint; fetcher source selection is unchanged")
    return warnings


def _date_flags(options: WorkflowOptions) -> str:
    if options.from_date and options.to_date:
        return f"--from-date {options.from_date} --to-date {options.to_date}"
    flags = f"--days {options.days}"
    if options.to_date:
        flags += f" --to-date {options.to_date}"
    return flags


def _execute_step(
    step: StepRecord,
    invoke: Callable[[], dict[str, Any]],
    *,
    planned_only: bool,
) -> StepRecord:
    if planned_only:
        step.status = "planned"
        return step
    try:
        result = invoke()
    except Exception as exc:  # noqa: BLE001 - workflow layer should report the exact failed step.
        step.status = "failed"
        step.error = str(exc)
        raise WorkflowStepError(step) from exc
    step.status = "ok"
    if isinstance(result.get("outputs"), list):
        step.outputs = [str(item) for item in result["outputs"]]
    if isinstance(result.get("warnings"), list):
        step.warnings.extend(str(item) for item in result["warnings"])
    return step


def run_daily_workflow(options: WorkflowOptions, runner: WorkflowRunner | None = None) -> dict[str, Any]:
    runner = runner or WorkflowRunner()
    dry_run = not options.execute
    steps: list[StepRecord] = []
    for planned in _daily_steps(options):
        if planned.name == "daily digest" and _network_disabled(options):
            planned.status = "skipped"
            steps.append(planned)
            continue
        if planned.name == "release hygiene":
            invoke = runner.hygiene
        else:
            invoke = lambda planned=planned: runner.daily(options, dry_run=False)
        steps.append(_execute_step(planned, invoke, planned_only=dry_run))
    return _workflow_result(options, steps, dry_run=dry_run)


def run_weekly_workflow(
    options: WorkflowOptions,
    runner: WorkflowRunner | None = None,
    *,
    write_manifest: bool = True,
) -> dict[str, Any]:
    runner = runner or WorkflowRunner()
    dry_run = not options.execute
    steps: list[StepRecord] = []
    for planned in _weekly_steps(options):
        if dry_run:
            planned.status = "planned"
            steps.append(planned)
            continue
        if planned.name == "obsidian scaffold" and options.skip_notes:
            planned.status = "skipped"
            steps.append(planned)
            continue
        if planned.name == "research progress" and options.skip_progress:
            planned.status = "skipped"
            steps.append(planned)
            continue
        invoke = _weekly_invoke(planned.name, options, runner)
        steps.append(_execute_step(planned, invoke, planned_only=False))
    result = _workflow_result(options, steps, dry_run=dry_run)
    if options.execute and write_manifest:
        _write_manifest(result, options)
    return result


def _weekly_invoke(name: str, options: WorkflowOptions, runner: WorkflowRunner) -> Callable[[], dict[str, Any]]:
    mapping: dict[str, Callable[[], dict[str, Any]]] = {
        "release hygiene": runner.hygiene,
        "weekly synthesis": lambda: runner.weekly_synthesis(options, dry_run=False),
        "research artifact export": lambda: runner.research_artifact_export(options, dry_run=False),
        "reading queue import": lambda: runner.reading_queue_import(options, dry_run=False),
        "obsidian scaffold": lambda: runner.obsidian_scaffold(options, dry_run=not options.generate_notes),
        "research progress": lambda: runner.research_progress(options, dry_run=False),
    }
    return mapping[name]


def run_full_workflow(options: WorkflowOptions, runner: WorkflowRunner | None = None) -> dict[str, Any]:
    runner = runner or WorkflowRunner()
    dry_run = not options.execute
    daily_options = WorkflowOptions(**{**options.__dict__, "workflow": "daily"})
    weekly_options = WorkflowOptions(**{**options.__dict__, "workflow": "weekly"})
    if dry_run:
        daily = run_daily_workflow(daily_options, runner)
        weekly = run_weekly_workflow(weekly_options, runner, write_manifest=False)
    else:
        daily = run_daily_workflow(daily_options, runner)
        weekly = run_weekly_workflow(weekly_options, runner, write_manifest=False)
    steps = [StepRecord(**step) for step in daily["steps"]] + [StepRecord(**step) for step in weekly["steps"]]
    result = _workflow_result(options, steps, dry_run=dry_run)
    if options.execute:
        _write_manifest(result, options)
    return result


def _workflow_result(options: WorkflowOptions, steps: list[StepRecord], *, dry_run: bool) -> dict[str, Any]:
    failed = [step for step in steps if step.status == "failed"]
    ok = [step for step in steps if step.status == "ok"]
    planned = [step for step in steps if step.status == "planned"]
    skipped = [step for step in steps if step.status == "skipped"]
    outputs = sorted({output for step in steps for output in step.outputs})
    return {
        "schema_version": SCHEMA_VERSION,
        "workflow": options.workflow,
        "profile": {
            "name": _profile_name(options),
            "low_load": options.low_load,
            "offline": options.offline,
            "no_network": options.no_network,
            "skip_heavy_sources": options.skip_heavy_sources,
            "skip_zotero": options.skip_zotero,
            "skip_notes": options.skip_notes,
            "skip_progress": options.skip_progress,
        },
        "run_date": datetime.now().date().isoformat(),
        "started_at": _now_utc().isoformat(),
        "finished_at": _now_utc().isoformat(),
        "dry_run": dry_run,
        "steps": [step.as_dict() for step in steps],
        "outputs": outputs,
        "summary": {
            "ok": len(ok),
            "planned": len(planned),
            "skipped": len(skipped),
            "failed": len(failed),
            "total": len(steps),
        },
    }


def _write_manifest(result: dict[str, Any], options: WorkflowOptions) -> Path:
    run_dir = _run_dir(options)
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "manifest.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def status_report() -> dict[str, Any]:
    queue_path = Path("state") / "reading-queue.json"
    queue_payload = _safe_json_load(queue_path) if queue_path.exists() else {}
    queue_records = queue_payload.get("records") if isinstance(queue_payload.get("records"), list) else []
    git_dirty, git_status = _run_git_status()
    return {
        "latest_daily_digest": str(_latest("digests/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md") or ""),
        "latest_weekly_synthesis": str(_latest("data/weekly/*.json") or ""),
        "reading_queue": {"path": str(queue_path), "exists": queue_path.exists(), "records": len(queue_records)},
        "latest_research_artifact_pack": str(_latest("exports/research-artifacts/*/manifest.json") or ""),
        "latest_obsidian_scaffold_output": str(_latest("exports/obsidian-paper-notes/Papers/*.md") or ""),
        "latest_research_progress": str(_latest("exports/research-progress/*/manifest.json") or ""),
        "latest_source_health_ledger": str(_latest("audits/source-health/*.json") or ""),
        "git": {"dirty": git_dirty, "status": git_status},
    }


def doctor_report(*, strict: bool = False) -> tuple[int, dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str, *, critical: bool = True) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail, "critical": critical})

    add("python", sys.version_info >= (3, 11), sys.version.split()[0])
    add("package version", bool(__version__), __version__)
    try:
        zone = ZoneInfo("Asia/Singapore")
    except Exception as exc:  # noqa: BLE001
        add("Asia/Singapore timezone", False, str(exc))
    else:
        add("Asia/Singapore timezone", True, str(zone))
    for path in [Path("data"), Path("digests"), Path("src") / "lattice_digest"]:
        add(f"directory {path}", path.exists(), "exists" if path.exists() else "missing", critical=path.parts[-1] == "lattice_digest")
    try:
        messages = WorkflowRunner().hygiene()["messages"]
    except Exception as exc:  # noqa: BLE001
        add("release hygiene", False, str(exc), critical=True)
    else:
        add("release hygiene", True, "; ".join(messages), critical=True)
    queue = Path("state") / "reading-queue.json"
    add("reading queue", queue.exists(), str(queue), critical=False)
    weekly = _latest("data/weekly/*.json")
    add("latest weekly JSON", weekly is not None, str(weekly or "missing"), critical=False)
    failed_critical = [item for item in checks if item["critical"] and not item["ok"]]
    code = 1 if strict and failed_critical else 0
    return code, {"schema_version": SCHEMA_VERSION, "strict": strict, "checks": checks}


def _print_workflow_result(result: dict[str, Any]) -> None:
    print(f"Workflow {result['workflow']} dry_run={result['dry_run']}")
    print(f"Profile: {result.get('profile', {}).get('name', 'normal')}")
    for step in result["steps"]:
        print(f"- {step['status']}: {step['name']} :: {step['command']}")
        if step["error"]:
            print(f"  error: {step['error']}")
        for warning in step["warnings"]:
            print(f"  warning: {warning}")
        for output in step["outputs"][:5]:
            print(f"  output: {output}")
    print(f"Summary: {result['summary']}")


def _print_mapping(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe workflow command center for lattice digest research automation.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    daily = subparsers.add_parser("daily", help="Plan or run the daily digest workflow.")
    daily.add_argument("--execute", action="store_true")
    daily.add_argument("--since", default="7d")
    daily.add_argument("--output", default="markdown,json")
    daily.add_argument("--send", default="none")
    daily.add_argument("--skip-hygiene", action="store_true")
    _add_profile_args(daily)

    weekly = subparsers.add_parser("weekly", help="Plan or run the weekly research workflow.")
    _add_weekly_args(weekly)

    full = subparsers.add_parser("full", help="Plan or run daily followed by weekly.")
    full.add_argument("--execute", action="store_true")
    full.add_argument("--since", default="7d")
    full.add_argument("--output", default="markdown,json")
    full.add_argument("--send", default="none")
    _add_weekly_args(full, include_execute=False)
    full.add_argument("--yes", action="store_true", help="Acknowledge that full --execute may run network-heavy daily fetching.")

    subparsers.add_parser("status", help="Show local workflow status without writing files.")
    doctor = subparsers.add_parser("doctor", help="Run local environment checks without writing files.")
    doctor.add_argument("--strict", action="store_true")
    return parser


def _add_weekly_args(parser: argparse.ArgumentParser, *, include_execute: bool = True) -> None:
    if include_execute:
        parser.add_argument("--execute", action="store_true")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--from-date")
    parser.add_argument("--to-date")
    parser.add_argument("--generate-notes", action="store_true")
    parser.add_argument("--skip-hygiene", action="store_true")
    _add_profile_args(parser)


def _add_profile_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--low-load", action="store_true", help="Use a manual low-load workflow profile.")
    parser.add_argument("--offline", action="store_true", help="Skip network-dependent workflow steps where possible.")
    parser.add_argument("--no-network", action="store_true", help="Alias-like explicit no-network profile; skips daily fetching.")
    parser.add_argument("--skip-heavy-sources", action="store_true", help="Record a low-load source hint without changing fetcher semantics.")
    parser.add_argument("--skip-zotero", action="store_true", help="Skip Zotero-oriented export pack formats where available.")
    parser.add_argument("--skip-notes", action="store_true", help="Skip Obsidian note scaffold generation.")
    parser.add_argument("--skip-progress", action="store_true", help="Skip research progress log generation.")


def _options_from_args(args: argparse.Namespace) -> WorkflowOptions:
    return WorkflowOptions(
        workflow=args.command,
        execute=bool(getattr(args, "execute", False)),
        days=int(getattr(args, "days", 7) or 7),
        from_date=getattr(args, "from_date", None),
        to_date=getattr(args, "to_date", None),
        since=str(getattr(args, "since", "7d")),
        output=str(getattr(args, "output", "markdown,json")),
        send=str(getattr(args, "send", "none")),
        skip_hygiene=bool(getattr(args, "skip_hygiene", False)),
        generate_notes=bool(getattr(args, "generate_notes", False)),
        low_load=bool(getattr(args, "low_load", False)),
        offline=bool(getattr(args, "offline", False)),
        no_network=bool(getattr(args, "no_network", False)),
        skip_heavy_sources=bool(getattr(args, "skip_heavy_sources", False)),
        skip_zotero=bool(getattr(args, "skip_zotero", False)),
        skip_notes=bool(getattr(args, "skip_notes", False)),
        skip_progress=bool(getattr(args, "skip_progress", False)),
        yes=bool(getattr(args, "yes", False)),
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "status":
        _print_mapping(status_report())
        return 0
    if args.command == "doctor":
        code, payload = doctor_report(strict=args.strict)
        _print_mapping(payload)
        return code
    options = _options_from_args(args)
    try:
        if args.command == "daily":
            result = run_daily_workflow(options)
        elif args.command == "weekly":
            result = run_weekly_workflow(options)
        elif args.command == "full":
            result = run_full_workflow(options)
        else:
            print(f"unknown command: {args.command}", file=sys.stderr)
            return 1
    except WorkflowStepError as exc:
        print(f"FAILED: {exc.step.name}: {exc.step.error}", file=sys.stderr)
        return 1
    _print_workflow_result(result)
    return 1 if result["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
