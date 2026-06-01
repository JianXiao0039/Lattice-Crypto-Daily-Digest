from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import lattice_digest.workflow as workflow
from lattice_digest.workflow import WorkflowOptions, run_daily_workflow, run_full_workflow, run_weekly_workflow


class FakeRunner(workflow.WorkflowRunner):
    def __init__(self, *, fail_step: str | None = None) -> None:
        self.calls: list[tuple[str, bool]] = []
        self.fail_step = fail_step

    def _record(self, name: str, dry_run: bool, outputs: list[str] | None = None) -> dict[str, object]:
        self.calls.append((name, dry_run))
        if self.fail_step == name:
            raise RuntimeError(f"{name} boom")
        return {"outputs": outputs or [f"fake/{name}.txt"], "warnings": []}

    def hygiene(self) -> dict[str, object]:
        self.calls.append(("hygiene", False))
        if self.fail_step == "hygiene":
            raise RuntimeError("hygiene boom")
        return {"messages": ["ok"]}

    def daily(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, object]:
        return self._record("daily", dry_run, ["data/YYYY-MM-DD.json", "digests/YYYY-MM-DD.md", "papers.db"])

    def weekly_synthesis(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, object]:
        return self._record("weekly synthesis", dry_run, ["data/weekly/2026-W22.json"])

    def research_artifact_export(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, object]:
        return self._record("research artifact export", dry_run, ["exports/research-artifacts/2026-05-31"])

    def reading_queue_import(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, object]:
        return self._record("reading queue import", dry_run, ["state/reading-queue.json"])

    def obsidian_scaffold(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, object]:
        return self._record("obsidian scaffold", dry_run, ["exports/obsidian-paper-notes/Papers/a.md"])

    def research_progress(self, options: WorkflowOptions, *, dry_run: bool) -> dict[str, object]:
        return self._record("research progress", dry_run, ["exports/research-progress/2026-W22/manifest.json"])


def _weekly_options(root: Path, *, execute: bool = False, generate_notes: bool = False) -> WorkflowOptions:
    return WorkflowOptions(
        workflow="weekly",
        execute=execute,
        from_date="2026-05-25",
        to_date="2026-05-31",
        skip_hygiene=True,
        generate_notes=generate_notes,
        output_dir=root / "exports" / "workflow-runs",
    )


def test_weekly_dry_run_writes_no_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = run_weekly_workflow(_weekly_options(root), FakeRunner())

    assert result["dry_run"] is True
    assert result["summary"]["planned"] == 5
    assert not (root / "exports").exists()


def test_daily_dry_run_does_not_invoke_runner_or_write_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        runner = FakeRunner()
        result = run_daily_workflow(
            WorkflowOptions(
                workflow="daily",
                skip_hygiene=True,
                output_dir=root / "exports" / "workflow-runs",
            ),
            runner,
        )

    assert result["dry_run"] is True
    assert result["summary"]["planned"] == 1
    assert runner.calls == []
    assert not (root / "exports").exists()


def test_weekly_execute_invokes_steps_and_writes_manifest() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        runner = FakeRunner()
        result = run_weekly_workflow(_weekly_options(root, execute=True), runner)
        manifests = list((root / "exports" / "workflow-runs").glob("*-weekly/manifest.json"))
        loaded = json.loads(manifests[0].read_text(encoding="utf-8"))

    assert result["summary"]["ok"] == 5
    assert [name for name, _ in runner.calls] == [
        "weekly synthesis",
        "research artifact export",
        "reading queue import",
        "obsidian scaffold",
        "research progress",
    ]
    assert loaded["workflow"] == "weekly"
    assert loaded["schema_version"] == 1
    assert all("exports/workflow-runs" in str(path).replace("\\", "/") for path in manifests)


def test_weekly_execute_without_generate_notes_keeps_obsidian_scaffold_dry_run() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        runner = FakeRunner()
        run_weekly_workflow(_weekly_options(root, execute=True), runner)

    assert ("obsidian scaffold", True) in runner.calls


def test_weekly_execute_generate_notes_allows_obsidian_writes() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        runner = FakeRunner()
        run_weekly_workflow(_weekly_options(root, execute=True, generate_notes=True), runner)

    assert ("obsidian scaffold", False) in runner.calls


def test_full_workflow_includes_daily_then_weekly_steps() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        options = WorkflowOptions(
            workflow="full",
            execute=False,
            from_date="2026-05-25",
            to_date="2026-05-31",
            skip_hygiene=True,
            output_dir=root / "exports" / "workflow-runs",
        )
        result = run_full_workflow(options, FakeRunner())

    names = [step["name"] for step in result["steps"]]
    assert names == [
        "daily digest",
        "weekly synthesis",
        "research artifact export",
        "reading queue import",
        "obsidian scaffold",
        "research progress",
    ]


def test_status_report_reads_fixture_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "digests").mkdir()
        (root / "data" / "weekly").mkdir(parents=True)
        (root / "state").mkdir()
        (root / "audits" / "source-health").mkdir(parents=True)
        (root / "exports" / "research-progress" / "2026-W22").mkdir(parents=True)
        (root / "exports" / "research-artifacts" / "2026-05-31").mkdir(parents=True)
        (root / "exports" / "obsidian-paper-notes" / "Papers").mkdir(parents=True)
        (root / "digests" / "2026-05-31.md").write_text("# Digest\n", encoding="utf-8")
        (root / "data" / "weekly" / "2026-W22.json").write_text("{}", encoding="utf-8")
        (root / "state" / "reading-queue.json").write_text('{"records":[{"title":"A"}]}', encoding="utf-8")
        (root / "audits" / "source-health" / "2026-05-31.json").write_text("{}", encoding="utf-8")
        (root / "exports" / "research-progress" / "2026-W22" / "manifest.json").write_text("{}", encoding="utf-8")
        (root / "exports" / "research-artifacts" / "2026-05-31" / "manifest.json").write_text("{}", encoding="utf-8")
        (root / "exports" / "obsidian-paper-notes" / "Papers" / "a.md").write_text("# A\n", encoding="utf-8")
        original = Path.cwd()
        os.chdir(root)
        try:
            report = workflow.status_report()
        finally:
            os.chdir(original)

    assert report["latest_daily_digest"].endswith("2026-05-31.md")
    assert report["latest_weekly_synthesis"].endswith("2026-W22.json")
    assert report["reading_queue"]["records"] == 1
    assert report["latest_source_health_ledger"].endswith("2026-05-31.json")


def test_doctor_checks_asia_singapore_zoneinfo() -> None:
    code, report = workflow.doctor_report(strict=True)
    zone = next(item for item in report["checks"] if item["name"] == "Asia/Singapore timezone")

    assert code == 0
    assert zone["ok"] is True
    assert "Asia/Singapore" in zone["detail"]


def test_manifest_shape_is_stable() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = run_weekly_workflow(_weekly_options(root, execute=True), FakeRunner())
        manifest = json.loads(next((root / "exports" / "workflow-runs").glob("*-weekly/manifest.json")).read_text(encoding="utf-8"))

    assert set(manifest) == {
        "schema_version",
        "workflow",
        "profile",
        "run_date",
        "started_at",
        "finished_at",
        "dry_run",
        "steps",
        "outputs",
        "summary",
    }
    assert manifest["steps"] == result["steps"]


def test_failing_step_returns_nonzero_from_cli() -> None:
    class FailingRunnerFactory:
        def __call__(self) -> FakeRunner:
            return FakeRunner(fail_step="weekly synthesis")

    original = workflow.WorkflowRunner
    workflow.WorkflowRunner = FailingRunnerFactory()  # type: ignore[assignment]
    try:
        code = workflow.main(["weekly", "--execute", "--skip-hygiene", "--from-date", "2026-05-25", "--to-date", "2026-05-31"])
    finally:
        workflow.WorkflowRunner = original

    assert code == 1


def test_generated_workflow_output_path_stays_under_exports_workflow_runs() -> None:
    options = WorkflowOptions(workflow="weekly", output_dir=Path("exports") / "workflow-runs")
    path = workflow._run_dir(options)

    assert str(path).replace("\\", "/").startswith("exports/workflow-runs/")


def test_weekly_step_ordering_is_deterministic() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = [step["name"] for step in run_weekly_workflow(_weekly_options(root), FakeRunner())["steps"]]
        second = [step["name"] for step in run_weekly_workflow(_weekly_options(root), FakeRunner())["steps"]]

    assert first == second


def test_status_writes_no_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        original = Path.cwd()
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        os.chdir(root)
        try:
            workflow.status_report()
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        finally:
            os.chdir(original)

    assert after == before


def test_doctor_writes_no_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        original = Path.cwd()
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        os.chdir(root)
        try:
            workflow.doctor_report(strict=False)
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        finally:
            os.chdir(original)

    assert after == before


def test_low_load_profile_is_reflected_in_planned_steps() -> None:
    options = WorkflowOptions(workflow="daily", low_load=True, skip_hygiene=True)
    result = run_daily_workflow(options, FakeRunner())
    daily_step = result["steps"][0]

    assert result["profile"]["name"] == "low-load"
    assert "--since 36h" in daily_step["command"]
    assert any("low-load profile" in warning for warning in daily_step["warnings"])


def test_no_network_profile_skips_daily_fetch() -> None:
    runner = FakeRunner()
    options = WorkflowOptions(workflow="daily", execute=True, no_network=True, skip_hygiene=True)
    result = run_daily_workflow(options, runner)

    assert result["profile"]["name"] == "offline/no-network"
    assert result["steps"][0]["status"] == "skipped"
    assert result["summary"]["skipped"] == 1
    assert runner.calls == []


def test_low_load_execute_remains_manual_and_creates_no_scheduler_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        runner = FakeRunner()
        result = run_daily_workflow(
            WorkflowOptions(
                workflow="daily",
                execute=True,
                low_load=True,
                skip_hygiene=True,
                output_dir=root / "exports" / "workflow-runs",
            ),
            runner,
        )
        created = [path.name.lower() for path in root.rglob("*") if path.is_file()]

    assert result["profile"]["name"] == "low-load"
    assert runner.calls == [("daily", False)]
    assert not any("scheduler" in name or "cron" in name or "watcher" in name for name in created)


def test_skip_progress_skips_progress_step_on_execute() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        options = _weekly_options(root, execute=True)
        options.skip_progress = True
        runner = FakeRunner()
        result = run_weekly_workflow(options, runner)

    progress = next(step for step in result["steps"] if step["name"] == "research progress")
    assert progress["status"] == "skipped"
    assert "research progress" not in [name for name, _ in runner.calls]


def test_no_scheduler_files_are_created_by_workflow_phase() -> None:
    forbidden_suffixes = (".xml",)
    forbidden_names = {"watcher.ps1", "start_watcher.bat", "install_watcher_task.ps1", "uninstall_watcher_task.ps1"}
    root = Path(__file__).resolve().parents[1]
    created = [
        path
        for path in [root / "scripts" / name for name in forbidden_names]
        if path.exists()
    ]
    scheduler_xml = [path for path in root.glob("scripts/*scheduler*") if path.suffix.lower() in forbidden_suffixes]

    assert created == []
    assert scheduler_xml == []


def test_manual_low_load_docs_do_not_configure_scheduler_or_cron() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs" / "manual-low-load-workflow.md").read_text(encoding="utf-8").lower()

    assert "no windows task scheduler" in text
    assert "no cron" in text
    assert "schtasks" not in text
    assert "<task" not in text
