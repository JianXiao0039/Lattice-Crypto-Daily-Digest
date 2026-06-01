from __future__ import annotations

import json
import os
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.digest_sections import (
    AI_LATTICE,
    GENERAL_CRYPTO_PRIVACY,
    HIGH_PRIORITY,
    LATTICE_REDUCTION_ATTACKS,
    LWE_FAMILY,
    PQC_STANDARDS,
    SIS_NTRU_COMMITMENTS,
)
from lattice_digest.obsidian_scaffold import generate_scaffolds
from lattice_digest.reading_queue import import_queue, load_import_candidates
from lattice_digest.research_artifact_export import generate_research_artifact_export
from lattice_digest.research_progress import generate_research_progress
from lattice_digest.weekly_synthesis import build_weekly_synthesis, write_weekly_outputs
from lattice_digest.workflow import WorkflowOptions, run_weekly_workflow


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "e2e"
START = date(2026, 5, 25)
END = date(2026, 5, 27)
GENERATED_AT = datetime(2026, 5, 27, tzinfo=timezone.utc)


def _copy_daily_fixtures(root: Path) -> Path:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for fixture in sorted(FIXTURE_DIR.glob("daily-*.json")):
        day = fixture.stem.removeprefix("daily-")
        shutil.copyfile(fixture, data_dir / f"{day}.json")
    return data_dir


def _copy_queue_fixture(root: Path) -> Path:
    queue_path = root / "state" / "reading-queue.json"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURE_DIR / "reading-queue-state.json", queue_path)
    return queue_path


def _copy_source_health_fixture(root: Path) -> Path:
    health_path = root / "audits" / "source-health" / "2026-05-27.json"
    health_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURE_DIR / "source-health-2026-05-27.json", health_path)
    return health_path.parent


def _build_weekly_from_fixtures(root: Path) -> dict[str, object]:
    data_dir = _copy_daily_fixtures(root)
    return build_weekly_synthesis(data_dir, START, END, GENERATED_AT)


def _write_weekly_from_fixtures(root: Path) -> Path:
    payload = _build_weekly_from_fixtures(root)
    json_path, _ = write_weekly_outputs(payload, root / "data" / "weekly", root / "digests" / "weekly")
    return json_path


def _titles(records: list[dict[str, object]]) -> list[str]:
    return [str(record.get("title")) for record in records]


def test_weekly_synthesis_from_e2e_fixture_daily_json() -> None:
    with TemporaryDirectory() as tmp:
        payload = _build_weekly_from_fixtures(Path(tmp))

    assert payload["coverage"]["loaded_days"] == ["2026-05-25", "2026-05-26", "2026-05-27"]
    assert payload["coverage"]["missing_days"] == []
    assert payload["coverage"]["total_records"] == 6
    assert payload["coverage"]["unique_records"] == 6
    assert "Transformer LWE coordinate selection for hybrid attacks" in _titles(payload["sections"][AI_LATTICE])
    assert "BKZ and G6K baselines for sparse LWE hybrid attacks" in _titles(payload["sections"][LATTICE_REDUCTION_ATTACKS])
    assert "Module-SIS chameleon hash commitments with reproducible parameters" in _titles(payload["sections"][SIS_NTRU_COMMITMENTS])
    health = payload["source_health_summary"]
    assert health["available"] is True
    assert health["status_counts"] == {"green": 3, "red": 1, "yellow": 1}


def test_research_artifact_export_from_weekly_json_fixture() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly_json = _write_weekly_from_fixtures(root)
        result = generate_research_artifact_export(
            from_date=START.isoformat(),
            to_date=END.isoformat(),
            weekly_json=weekly_json,
            daily_data_dir=root / "data",
            output_dir=root / "exports" / "research-artifacts",
            formats="obsidian,advisor,backlog,zotero",
        )
        export_root = result["export_root"]
        manifest = json.loads((export_root / "manifest.json").read_text(encoding="utf-8"))
        reading_queue = (export_root / "obsidian" / "reading-queue.md").read_text(encoding="utf-8")

    assert manifest["counts"]["records"] == 6
    assert manifest["input_mode"] == "weekly_json"
    assert "Transformer LWE coordinate selection" in reading_queue
    assert "Module-SIS chameleon hash" in reading_queue
    assert result["written_paths"]


def test_reading_queue_import_preserves_manual_statuses_from_fixture() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly_json = _write_weekly_from_fixtures(root)
        queue_path = _copy_queue_fixture(root)
        state = json.loads(queue_path.read_text(encoding="utf-8"))
        candidates, metadata = load_import_candidates(
            from_date=START.isoformat(),
            to_date=END.isoformat(),
            data_dir=root / "data",
            weekly_json=weekly_json,
        )
        new_state, summary = import_queue(state, candidates, timestamp="2026-05-28T12:00:00+00:00")

    record = next(item for item in new_state["records"] if item["dedup_key"] == "arxiv:2605.90001")
    assert metadata["input_mode"] == "weekly_json"
    assert summary["updated"] >= 1
    assert record["reading_status"] == "READING"
    assert record["review_status"] == "NEEDS_MATH_CHECK"
    assert record["zotero_key"] == "MANUAL123"
    assert record["obsidian_note_path"] == "Papers/transformer-lwe-coordinate-selection.md"


def test_obsidian_scaffold_dry_run_writes_no_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        state_path = _copy_queue_fixture(root)
        result = generate_scaffolds(
            state_path=state_path,
            output_dir=root / "exports" / "obsidian-paper-notes" / "Papers",
            dry_run=True,
        )

    assert len(result["plan"]["entries"]) == 1
    assert result["written"] == []
    assert not (root / "exports").exists()


def test_obsidian_scaffold_generate_writes_expected_note_scaffold() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        state_path = _copy_queue_fixture(root)
        result = generate_scaffolds(
            state_path=state_path,
            output_dir=root / "exports" / "obsidian-paper-notes" / "Papers",
        )
        note_path = result["written"][0]
        note = note_path.read_text(encoding="utf-8")

    assert note_path.name == "transformer-lwe-coordinate-selection-for-hybrid-attacks.md"
    assert "type: paper_note" in note
    assert "Transformer LWE coordinate selection for hybrid attacks" in note
    assert "## Verification Status" in note


def test_research_progress_export_generates_advisor_update_and_backlog() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly_json = _write_weekly_from_fixtures(root)
        queue_path = _copy_queue_fixture(root)
        health_dir = _copy_source_health_fixture(root)
        note_dir = root / "exports" / "obsidian-paper-notes" / "Papers"
        note_dir.mkdir(parents=True)
        (note_dir / "transformer-lwe-coordinate-selection.md").write_text("# Transformer LWE\n", encoding="utf-8")
        result = generate_research_progress(
            from_date=START.isoformat(),
            to_date=END.isoformat(),
            weekly_json=weekly_json,
            reading_queue=queue_path,
            source_health_dir=health_dir,
            obsidian_notes_dir=note_dir,
            artifact_dir=root / "exports" / "research-artifacts",
            output_dir=root / "exports" / "research-progress",
        )
        advisor = (result["run_dir"] / "advisor-update-draft.md").read_text(encoding="utf-8")
        backlog = (result["run_dir"] / "verification-backlog.md").read_text(encoding="utf-8")
        next_week = (result["run_dir"] / "next-week-plan.md").read_text(encoding="utf-8")

    assert "## High-Priority Papers Found" in advisor
    assert "Transformer LWE coordinate selection" in advisor
    assert "## Needs Math Check" in backlog
    assert "NEEDS_MATH_CHECK" in backlog
    assert "OpenAlex" in next_week


def test_workflow_weekly_dry_run_writes_no_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        options = WorkflowOptions(
            workflow="weekly",
            execute=False,
            from_date=START.isoformat(),
            to_date=END.isoformat(),
            skip_hygiene=True,
            output_dir=root / "exports" / "workflow-runs",
        )
        result = run_weekly_workflow(options)

    assert result["dry_run"] is True
    assert result["summary"]["planned"] == 5
    assert not (root / "exports").exists()
    assert not (root / "data").exists()
    assert not (root / "state").exists()


def test_workflow_weekly_execute_in_temp_dirs_writes_expected_outputs_only() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_daily_fixtures(root)
        original = Path.cwd()
        os.chdir(root)
        try:
            options = WorkflowOptions(
                workflow="weekly",
                execute=True,
                from_date=START.isoformat(),
                to_date=END.isoformat(),
                skip_hygiene=True,
                output_dir=root / "exports" / "workflow-runs",
            )
            result = run_weekly_workflow(options)
        finally:
            os.chdir(original)

        files = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())

    assert result["summary"]["ok"] == 5
    assert "data/weekly/2026-W22.json" in files
    assert "digests/weekly/2026-W22.md" in files
    assert "state/reading-queue.json" in files
    assert any(path.endswith("-weekly/manifest.json") and path.startswith("exports/workflow-runs/") for path in files)
    assert any(path.startswith("exports/research-artifacts/2026-05-27/") for path in files)
    assert any(path.startswith("exports/research-progress/2026-W22/") for path in files)
    assert not any(path.startswith("exports/obsidian-paper-notes/") for path in files)
    assert not any("papers.db" in path for path in files)


def test_false_positive_falcon_x_does_not_enter_pqc_falcon_section() -> None:
    with TemporaryDirectory() as tmp:
        payload = _build_weekly_from_fixtures(Path(tmp))

    pqc_titles = _titles(payload["sections"][PQC_STANDARDS])
    watchlist_titles = _titles(payload["sections"]["Other / Watchlist"])
    assert "Falcon-X: a time series foundation model" not in pqc_titles
    assert "Falcon-X: a time series foundation model" in watchlist_titles


def test_false_positive_anonymous_two_party_gbdt_stays_out_of_lattice_sections() -> None:
    with TemporaryDirectory() as tmp:
        payload = _build_weekly_from_fixtures(Path(tmp))

    title = "Practical Anonymous Two-Party GBDT"
    assert title not in _titles(payload["sections"][AI_LATTICE])
    assert title not in _titles(payload["sections"][LWE_FAMILY])
    assert title not in _titles(payload["sections"][SIS_NTRU_COMMITMENTS])
    assert title not in _titles(payload["sections"][PQC_STANDARDS])
    assert title in _titles(payload["sections"][GENERAL_CRYPTO_PRIVACY])


def test_no_scheduled_automation_files_are_created_by_e2e_workflow() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_daily_fixtures(root)
        original = Path.cwd()
        os.chdir(root)
        try:
            run_weekly_workflow(
                WorkflowOptions(
                    workflow="weekly",
                    execute=True,
                    from_date=START.isoformat(),
                    to_date=END.isoformat(),
                    skip_hygiene=True,
                    output_dir=root / "exports" / "workflow-runs",
                )
            )
        finally:
            os.chdir(original)
        created = [path.name.lower() for path in root.rglob("*") if path.is_file()]

    assert not any("task" in name and "scheduler" in name for name in created)
    assert not any("cron" in name for name in created)
    assert not any(name.endswith(".xml") for name in created)
    assert not any(name in {"watcher.ps1", "start_watcher.bat", "install_watcher_task.ps1"} for name in created)


def test_weekly_outputs_are_deterministically_ordered() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = _build_weekly_from_fixtures(root)
        second = build_weekly_synthesis(root / "data", START, END, GENERATED_AT)

    assert first == second
    assert _titles(first["report_buckets"][HIGH_PRIORITY])[:3] == [
        "Transformer LWE coordinate selection for hybrid attacks",
        "BKZ and G6K baselines for sparse LWE hybrid attacks",
        "Module-SIS chameleon hash commitments with reproducible parameters",
    ]
