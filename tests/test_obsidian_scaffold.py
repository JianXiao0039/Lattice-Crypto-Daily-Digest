from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.digest_sections import (
    AI_LATTICE,
    HIGH_PRIORITY,
    LATTICE_REDUCTION_ATTACKS,
    LWE_FAMILY,
    SIS_NTRU_COMMITMENTS,
)
from lattice_digest.obsidian_scaffold import (
    assign_note_paths,
    build_scaffold_plan,
    generate_scaffolds,
    render_note,
    select_records,
    slugify_title,
)


STAMP = "2026-05-31T00:00:00+00:00"


def _queue_record(
    title: str,
    key: str,
    *,
    reading_status: str = "TODO_READ",
    review_status: str = "TODO_VERIFY",
    priority: str = "HIGH",
    score: int = 90,
    sections: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "dedup_key": key,
        "title": title,
        "source_url": f"https://example.org/{key.replace(':', '-')}",
        "doi": "10.1000/example" if key.startswith("doi:") else "",
        "arxiv_id": "2605.00001" if key.startswith("arxiv:") else "",
        "publication_date": "2026-05-31",
        "relevance_label": "A" if priority == "HIGH" else "B",
        "relevance_score": score,
        "research_sections": sections
        or [HIGH_PRIORITY, LWE_FAMILY, LATTICE_REDUCTION_ATTACKS, AI_LATTICE],
        "ranking_explanation": {"relevance_label": "A", "relevance_score": score},
        "seen_dates": ["2026-05-31"],
        "seen_sources": ["arxiv"],
        "queue_priority": priority,
        "track": AI_LATTICE,
        "reading_status": reading_status,
        "review_status": review_status,
        "zotero_key": "ZOT123",
        "obsidian_note_path": "",
        "personal_notes_path": "",
        "added_at": STAMP,
        "updated_at": STAMP,
        "status_history": [{"timestamp": STAMP, "action": "imported"}],
    }


def _state(records: list[dict[str, object]]) -> dict[str, object]:
    return {"schema_version": 1, "updated_at": STAMP, "records": records}


def _write_state(root: Path, state: dict[str, object]) -> Path:
    path = root / "state" / "reading-queue.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_obsidian_scaffold_generates_note_for_todo_read_high_record() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        state_path = _write_state(root, _state([_queue_record("Transformer LWE coordinate selection", "arxiv:2605.00001")]))
        result = generate_scaffolds(state_path=state_path, output_dir=root / "exports" / "obsidian-paper-notes" / "Papers")
        note = result["written"][0].read_text(encoding="utf-8")

    assert len(result["written"]) == 1
    assert "# Transformer LWE coordinate selection" in note
    assert "type: paper_note" in note


def test_obsidian_scaffold_skips_ignored_record() -> None:
    state = _state([_queue_record("Ignored paper", "title:ignored", reading_status="IGNORED")])

    selected = select_records(state)

    assert selected == []


def test_obsidian_scaffold_skips_not_relevant_record() -> None:
    state = _state([_queue_record("Not relevant paper", "title:not-relevant", review_status="NOT_RELEVANT")])

    selected = select_records(state)

    assert selected == []


def test_obsidian_scaffold_generates_deterministic_sanitized_filename() -> None:
    slug = slugify_title('Transformer/LWE: coordinate*selection? <test>')

    assert slug == "transformer-lwe-coordinate-selection-test"


def test_obsidian_scaffold_resolves_filename_collision_deterministically() -> None:
    records = [
        _queue_record("Same Title", "doi:10.1000/a"),
        _queue_record("Same Title", "doi:10.1000/b"),
    ]
    paths = assign_note_paths(records, Path("Papers"))

    assert paths["doi:10.1000/a"].name.startswith("same-title--")
    assert paths["doi:10.1000/b"].name.startswith("same-title--")
    assert paths["doi:10.1000/a"] != paths["doi:10.1000/b"]


def test_obsidian_scaffold_dry_run_writes_no_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        state_path = _write_state(root, _state([_queue_record("Dry run paper", "title:dry-run")]))
        result = generate_scaffolds(
            state_path=state_path,
            output_dir=root / "exports" / "obsidian-paper-notes" / "Papers",
            dry_run=True,
        )

    assert len(result["plan"]["entries"]) == 1
    assert not (root / "exports").exists()


def test_obsidian_scaffold_existing_note_is_not_overwritten() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        state_path = _write_state(root, _state([_queue_record("Existing Note", "title:existing")]))
        output_dir = root / "exports" / "obsidian-paper-notes" / "Papers"
        output_dir.mkdir(parents=True)
        note = output_dir / "existing-note.md"
        note.write_text("manual note", encoding="utf-8")
        result = generate_scaffolds(state_path=state_path, output_dir=output_dir)
        existing_content = note.read_text(encoding="utf-8")

    assert result["written"] == []
    assert result["skipped_existing"] == [note]
    assert existing_content == "manual note"


def test_obsidian_scaffold_frontmatter_contains_expected_metadata() -> None:
    note = render_note(_queue_record("Metadata paper", "arxiv:2605.00001"))

    for text in [
        "type: paper_note",
        'dedup_key: "arxiv:2605.00001"',
        'relevance_label: "A"',
        "relevance_score: 90",
        'queue_priority: "HIGH"',
        'reading_status: "TODO_READ"',
        'review_status: "TODO_VERIFY"',
        "research_sections:",
        "source_url:",
        "zotero_key:",
        'created_by: "lattice_digest.obsidian_scaffold"',
    ]:
        assert text in note


def test_obsidian_scaffold_note_contains_required_sections() -> None:
    note = render_note(_queue_record("Section paper", "doi:10.1000/section"))

    for header in [
        "## Metadata",
        "## Why Queued",
        "## Reading Goal",
        "## TL;DR",
        "## Core Problem",
        "## Method / Construction / Attack Idea",
        "## Mathematical Checkpoints",
        "## Experiment / Artifact Checkpoints",
        "## Relation to My Research",
        "## Possible Use",
        "## Questions for Advisor",
        "## Reading Log",
        "## Verification Status",
    ]:
        assert header in note


def test_obsidian_scaffold_note_does_not_contain_invented_claim_language() -> None:
    note = render_note(_queue_record("Careful paper", "title:careful"))

    lowered = note.lower()
    for forbidden in ["we prove", "breaks kyber", "experimental results show", "security is proven"]:
        assert forbidden not in lowered
    assert "TODO_AFTER_READING" in note
    assert "TODO_VERIFY" in note


def test_obsidian_scaffold_update_queue_writes_note_path_but_preserves_statuses() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        record = _queue_record(
            "Module-SIS chameleon hash",
            "doi:10.1000/module-sis",
            review_status="NEEDS_MATH_CHECK",
            sections=[HIGH_PRIORITY, SIS_NTRU_COMMITMENTS],
        )
        state_path = _write_state(root, _state([record]))
        result = generate_scaffolds(
            state_path=state_path,
            output_dir=root / "exports" / "obsidian-paper-notes" / "Papers",
            update_queue=True,
            timestamp="2026-06-01T00:00:00+00:00",
        )
        loaded = json.loads(state_path.read_text(encoding="utf-8"))

    updated = loaded["records"][0]
    assert result["written"]
    assert updated["reading_status"] == "TODO_READ"
    assert updated["review_status"] == "NEEDS_MATH_CHECK"
    assert updated["zotero_key"] == "ZOT123"
    assert updated["obsidian_note_path"].endswith("module-sis-chameleon-hash.md")
    assert updated["status_history"][-1]["action"] == "obsidian_scaffold"


def test_obsidian_scaffold_ordering_of_generated_notes_is_deterministic() -> None:
    records = [
        _queue_record("Medium paper", "title:medium", priority="MEDIUM", score=80),
        _queue_record("High paper", "title:high", priority="HIGH", score=90),
        _queue_record("Another high paper", "title:another", priority="HIGH", score=95),
    ]
    plan = build_scaffold_plan(_state(records), Path("Papers"))

    assert [entry["title"] for entry in plan["entries"]] == ["Another high paper", "High paper", "Medium paper"]
