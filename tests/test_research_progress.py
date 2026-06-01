from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.research_progress import generate_research_progress, render_advisor_update


def _record(
    title: str,
    sections: list[str],
    *,
    label: str = "A",
    score: int = 90,
    queue_priority: str = "HIGH",
    reading_status: str = "TODO_READ",
    review_status: str = "TODO_VERIFY",
) -> dict[str, object]:
    return {
        "title": title,
        "abstract": "Sample record for deterministic progress tests.",
        "source": "arxiv",
        "source_url": f"https://example.org/{title.lower().replace(' ', '-')}",
        "publication_date": "2026-05-31",
        "relevance_label": label,
        "relevance_score": score,
        "research_sections": sections,
        "ranking_explanation": {
            "relevance_label": label,
            "relevance_score": score,
            "decision": "include",
        },
        "queue_priority": queue_priority,
        "reading_status": reading_status,
        "review_status": review_status,
        "track": sections[0] if sections else "Unclassified",
        "obsidian_note_path": "",
        "seen_dates": ["2026-05-31"],
        "seen_sources": ["arxiv"],
        "status_history": [{"timestamp": "2026-05-31T00:00:00+00:00", "event": "imported"}],
    }


def _write_inputs(root: Path) -> dict[str, Path]:
    weekly_record = _record(
        "Transformer LWE coordinate selection",
        ["AI-assisted Lattice Cryptanalysis", "LWE / RLWE / MLWE"],
        score=92,
    )
    weekly_record["dedup_key"] = "arxiv:2605.00001v1"
    implementation_record = _record(
        "ML-DSA implementation audit",
        ["Implementation / Side-channel / Systems", "PQC Standards / ML-KEM / ML-DSA / Falcon"],
        label="B",
        score=78,
        queue_priority="MEDIUM",
        reading_status="READING",
        review_status="NEEDS_REPLICATION",
    )
    implementation_record["dedup_key"] = "doi:10.1000/ml-dsa-audit"
    lower_record = _record(
        "Generic PQC migration survey",
        ["PQC Standards / ML-KEM / ML-DSA / Falcon"],
        label="C",
        score=50,
        queue_priority="LOW",
        reading_status="SAVED",
        review_status="TODO_VERIFY",
    )
    lower_record["dedup_key"] = "title:generic-pqc-migration-survey"

    weekly = {
        "schema_version": 1,
        "week_id": "2026-W22",
        "from_date": "2026-05-25",
        "to_date": "2026-05-31",
        "coverage": {
            "expected_days": 7,
            "loaded_days": ["2026-05-31"],
            "missing_days": ["2026-05-25", "2026-05-26"],
            "unique_records": 3,
        },
        "report_buckets": {
            "High-Priority Papers": [weekly_record],
            "Idea Bank Candidates": [weekly_record, implementation_record],
            "Paper Plan Candidates": [weekly_record],
        },
        "sections": {
            "AI-assisted Lattice Cryptanalysis": [weekly_record],
            "Implementation / Side-channel / Systems": [implementation_record],
            "PQC Standards / ML-KEM / ML-DSA / Falcon": [implementation_record, lower_record],
        },
    }
    weekly_path = root / "data" / "weekly" / "2026-W22.json"
    weekly_path.parent.mkdir(parents=True, exist_ok=True)
    weekly_path.write_text(json.dumps(weekly, ensure_ascii=False, indent=2), encoding="utf-8")

    queue = {
        "schema_version": 1,
        "records": [
            {**weekly_record, "dedup_key": "arxiv:2605.00001v1", "obsidian_note_path": "Papers/transformer-lwe.md"},
            {**implementation_record, "dedup_key": "doi:10.1000/ml-dsa-audit", "obsidian_note_path": "Papers/ml-dsa-audit.md"},
            {**lower_record, "dedup_key": "title:generic-pqc-migration-survey"},
        ],
    }
    queue_path = root / "state" / "reading-queue.json"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_text = json.dumps(queue, ensure_ascii=False, indent=2)
    queue_path.write_text(queue_text, encoding="utf-8")

    health = {
        "schema_version": 1,
        "run_date": "2026-05-31",
        "sources": [
            {"source": "OpenAlex", "status": "red", "error_type": "429", "retryable": True},
            {"source": "Semantic Scholar", "health_status": "yellow", "error_type": "rate_limit", "retryable": True},
        ],
    }
    health_path = root / "audits" / "source-health" / "2026-05-31.json"
    health_path.parent.mkdir(parents=True, exist_ok=True)
    health_path.write_text(json.dumps(health, ensure_ascii=False, indent=2), encoding="utf-8")

    note_path = root / "exports" / "obsidian-paper-notes" / "Papers" / "transformer-lwe.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text("# Transformer LWE coordinate selection\n", encoding="utf-8")

    manifest_path = root / "exports" / "research-artifacts" / "toy-artifact" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"name": "toy-artifact"}, indent=2), encoding="utf-8")

    return {
        "weekly": weekly_path,
        "queue": queue_path,
        "health_dir": health_path.parent,
        "notes_dir": note_path.parent,
        "artifact_dir": manifest_path.parent.parent,
    }


def _generate(root: Path, *, dry_run: bool = False) -> dict[str, object]:
    paths = _write_inputs(root)
    return generate_research_progress(
        from_date="2026-05-25",
        to_date="2026-05-31",
        weekly_json=paths["weekly"],
        reading_queue=paths["queue"],
        source_health_dir=paths["health_dir"],
        obsidian_notes_dir=paths["notes_dir"],
        artifact_dir=paths["artifact_dir"],
        output_dir=root / "exports" / "research-progress",
        dry_run=dry_run,
    )


def test_research_progress_writes_manifest_and_all_documents() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = _generate(root)
        run_dir = result["run_dir"]
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        expected = {
            "manifest.json",
            "advisor-update-draft.md",
            "research-progress-log.md",
            "next-week-plan.md",
            "verification-backlog.md",
        }
        assert {path.name for path in run_dir.iterdir()} == expected
        assert manifest["schema_version"] == 1
        assert manifest["week_id"] == "2026-W22"
        assert manifest["counts"]["high_priority"] == 1
        assert manifest["counts"]["must_verify"] == 3
        assert all("exports" in path and "research-progress" in path for path in manifest["output_files"])


def test_research_progress_documents_have_required_sections_and_cautious_language() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = _generate(root)
        run_dir = result["run_dir"]
        advisor = (run_dir / "advisor-update-draft.md").read_text(encoding="utf-8")
        progress = (run_dir / "research-progress-log.md").read_text(encoding="utf-8")
        next_week = (run_dir / "next-week-plan.md").read_text(encoding="utf-8")
        backlog = (run_dir / "verification-backlog.md").read_text(encoding="utf-8")

    assert "## High-Priority Papers Found" in advisor
    assert "## Candidate Directions, Not Claims" in advisor
    assert "## Reading Queue Delta" in progress
    assert "## Engineering Maintenance" in next_week
    assert "## Needs Original Paper Check" in backlog
    combined = "\n".join([advisor, progress, next_week, backlog]).lower()
    for unsafe in ["this proves", "this breaks", "guaranteed attack", "verified result"]:
        assert unsafe not in combined


def test_research_progress_dry_run_writes_no_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = _generate(root, dry_run=True)

    assert result["written"] == []
    assert not result["run_dir"].exists()


def test_research_progress_handles_missing_weekly_and_queue_gracefully() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = generate_research_progress(
            week_id="2099-W01",
            weekly_json=root / "missing-weekly.json",
            reading_queue=root / "missing-queue.json",
            source_health_dir=root / "missing-health",
            obsidian_notes_dir=root / "missing-notes",
            artifact_dir=root / "missing-artifacts",
            output_dir=root / "exports" / "research-progress",
        )
        manifest = result["manifest"]

    assert manifest["counts"]["weekly_records"] == 0
    assert manifest["counts"]["queue_records"] == 0
    assert result["context"]["weekly_input_mode"] == "missing_weekly_json"
    assert result["context"]["reading_queue_mode"] == "missing_reading_queue"


def test_research_progress_source_health_red_yellow_appears_in_engineering_maintenance() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = _generate(root)
        next_week = (result["run_dir"] / "next-week-plan.md").read_text(encoding="utf-8")

    assert "OpenAlex" in next_week
    assert "red" in next_week
    assert "Semantic Scholar" in next_week
    assert "yellow" in next_week


def test_research_progress_ordering_is_deterministic() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = _generate(root, dry_run=True)
        second = generate_research_progress(
            from_date="2026-05-25",
            to_date="2026-05-31",
            weekly_json=root / "data" / "weekly" / "2026-W22.json",
            reading_queue=root / "state" / "reading-queue.json",
            source_health_dir=root / "audits" / "source-health",
            obsidian_notes_dir=root / "exports" / "obsidian-paper-notes" / "Papers",
            artifact_dir=root / "exports" / "research-artifacts",
            output_dir=root / "exports" / "research-progress",
            dry_run=True,
        )

    assert render_advisor_update(first["context"]) == render_advisor_update(second["context"])


def test_research_progress_does_not_mutate_reading_queue() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = _write_inputs(root)
        before = paths["queue"].read_text(encoding="utf-8")
        generate_research_progress(
            from_date="2026-05-25",
            to_date="2026-05-31",
            weekly_json=paths["weekly"],
            reading_queue=paths["queue"],
            source_health_dir=paths["health_dir"],
            obsidian_notes_dir=paths["notes_dir"],
            artifact_dir=paths["artifact_dir"],
            output_dir=root / "exports" / "research-progress",
        )
        after = paths["queue"].read_text(encoding="utf-8")

    assert after == before
