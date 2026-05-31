from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.digest_sections import (
    AI_LATTICE,
    HIGH_PRIORITY,
    IDEA_BANK_CANDIDATES,
    IMPLEMENTATION_SYSTEMS,
    LATTICE_REDUCTION_ATTACKS,
    LWE_FAMILY,
    PAPER_PLAN_CANDIDATES,
    PQC_STANDARDS,
    SIS_NTRU_COMMITMENTS,
)
from lattice_digest.reading_queue import (
    audit_state,
    export_obsidian,
    import_queue,
    link_record,
    load_import_candidates,
    mark_status,
    queue_priority_for_record,
    save_state,
)


STAMP = "2026-05-31T00:00:00+00:00"
STAMP2 = "2026-06-01T00:00:00+00:00"


def _record(
    title: str,
    sections: list[str],
    *,
    label: str = "A",
    score: int = 90,
    doi: str = "",
    arxiv_id: str = "",
    source_url: str | None = None,
    seen_dates: list[str] | None = None,
    seen_sources: list[str] | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "abstract": "Deterministic sample record.",
        "source": "arxiv",
        "source_url": f"https://example.org/{title.lower().replace(' ', '-')}" if source_url is None else source_url,
        "doi": doi,
        "arxiv_id": arxiv_id,
        "publication_date": "2026-05-31",
        "relevance_label": label,
        "relevance_score": score,
        "research_sections": sections,
        "ranking_explanation": {"relevance_label": label, "relevance_score": score},
        "seen_dates": seen_dates or ["2026-05-31"],
        "seen_sources": seen_sources or ["arxiv"],
    }


def _weekly_payload() -> dict[str, object]:
    ai = _record(
        "Transformer LWE coordinate selection",
        [HIGH_PRIORITY, LWE_FAMILY, LATTICE_REDUCTION_ATTACKS, AI_LATTICE, IDEA_BANK_CANDIDATES, PAPER_PLAN_CANDIDATES],
        arxiv_id="2605.00001v1",
        score=92,
    )
    sis = _record(
        "Module-SIS chameleon hash commitments",
        [HIGH_PRIORITY, SIS_NTRU_COMMITMENTS, IDEA_BANK_CANDIDATES, PAPER_PLAN_CANDIDATES],
        doi="10.1000/module-sis",
        score=88,
        seen_sources=["iacr_eprint"],
    )
    pqc = _record(
        "ML-KEM side-channel implementation audit",
        [PQC_STANDARDS, IMPLEMENTATION_SYSTEMS],
        label="B",
        score=78,
    )
    low = _record("Generic PQC migration survey", [PQC_STANDARDS], label="C", score=50)
    filtered = _record("Crystal lattice physics", [], label="D", score=5)
    return {
        "schema_version": 1,
        "week_id": "2026-W22",
        "from_date": "2026-05-25",
        "to_date": "2026-05-31",
        "sections": {
            HIGH_PRIORITY: [ai, sis],
            LWE_FAMILY: [ai],
            LATTICE_REDUCTION_ATTACKS: [ai],
            AI_LATTICE: [ai],
            SIS_NTRU_COMMITMENTS: [sis],
            PQC_STANDARDS: [pqc, low],
            IMPLEMENTATION_SYSTEMS: [pqc],
            IDEA_BANK_CANDIDATES: [ai, sis],
            PAPER_PLAN_CANDIDATES: [ai, sis],
            "Source Health Summary": [filtered],
        },
    }


def _write_weekly(root: Path) -> Path:
    path = root / "data" / "weekly" / "2026-W22.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_weekly_payload(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_reading_queue_imports_weekly_json() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly = _write_weekly(root)
        candidates, metadata = load_import_candidates(
            from_date="2026-05-25",
            to_date="2026-05-31",
            data_dir=root / "data",
            weekly_json=weekly,
        )
        state, summary = import_queue({"records": []}, candidates, timestamp=STAMP)

    assert metadata["input_mode"] == "weekly_json"
    assert summary["imported"] == 4
    assert [record["title"] for record in state["records"]][:2] == [
        "Transformer LWE coordinate selection",
        "Module-SIS chameleon hash commitments",
    ]


def test_reading_queue_preserves_existing_manual_statuses_on_reimport() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly = _write_weekly(root)
        candidates, _ = load_import_candidates(from_date="2026-05-25", to_date="2026-05-31", data_dir=root / "data", weekly_json=weekly)
        state, _ = import_queue({"records": []}, candidates, timestamp=STAMP)
        key = state["records"][0]["dedup_key"]
        state = mark_status(state, key=key, reading_status="READING", review_status="NEEDS_MATH_CHECK", timestamp=STAMP2)
        state, _ = import_queue(state, candidates, timestamp="2026-06-02T00:00:00+00:00")

    record = next(item for item in state["records"] if item["dedup_key"] == key)
    assert record["reading_status"] == "READING"
    assert record["review_status"] == "NEEDS_MATH_CHECK"


def test_reading_queue_merges_seen_dates_and_sources() -> None:
    first = _record("Module-SIS chameleon hash commitments", [HIGH_PRIORITY, SIS_NTRU_COMMITMENTS], doi="10.1000/module-sis", seen_dates=["2026-05-30"], seen_sources=["arxiv"])
    second = _record("Module-SIS chameleon hash commitments", [HIGH_PRIORITY, SIS_NTRU_COMMITMENTS], doi="10.1000/module-sis", seen_dates=["2026-05-31"], seen_sources=["iacr_eprint"])
    state, _ = import_queue({"records": []}, [first], timestamp=STAMP)
    state, _ = import_queue(state, [second], timestamp=STAMP2)

    assert state["records"][0]["seen_dates"] == ["2026-05-30", "2026-05-31"]
    assert state["records"][0]["seen_sources"] == ["arxiv", "iacr_eprint"]


def test_reading_queue_deduplicates_by_doi_arxiv_source_url_and_title() -> None:
    doi_a = _record("A", [HIGH_PRIORITY, LWE_FAMILY], doi="10.1000/a")
    doi_b = _record("Different A", [HIGH_PRIORITY, LWE_FAMILY], doi="10.1000/a", score=95)
    arxiv_a = _record("B", [HIGH_PRIORITY, LWE_FAMILY], arxiv_id="2605.00002v1")
    arxiv_b = _record("Different B", [HIGH_PRIORITY, LWE_FAMILY], arxiv_id="2605.00002v2")
    url_a = _record("C", [HIGH_PRIORITY, LWE_FAMILY], source_url="https://example.org/c")
    url_b = _record("Different C", [HIGH_PRIORITY, LWE_FAMILY], source_url="https://example.org/c")
    title_a = _record("Same Title!", [HIGH_PRIORITY, LWE_FAMILY], source_url="")
    title_b = _record("Same   Title", [HIGH_PRIORITY, LWE_FAMILY], source_url="")

    state, summary = import_queue({"records": []}, [doi_a, doi_b, arxiv_a, arxiv_b, url_a, url_b, title_a, title_b], timestamp=STAMP)

    assert summary["total"] == 4
    assert len({record["dedup_key"] for record in state["records"]}) == 4


def test_reading_queue_assigns_priority_deterministically() -> None:
    assert queue_priority_for_record(_record("A", [LWE_FAMILY], label="A")) == "HIGH"
    assert queue_priority_for_record(_record("B", [LWE_FAMILY], label="B")) == "MEDIUM"
    assert queue_priority_for_record(_record("C", [LWE_FAMILY], label="C")) == "LOW"


def test_reading_queue_mark_updates_reading_and_review_status() -> None:
    state, _ = import_queue({"records": []}, [_record("A", [HIGH_PRIORITY, LWE_FAMILY])], timestamp=STAMP)
    key = state["records"][0]["dedup_key"]
    state = mark_status(state, key=key, reading_status="READ", timestamp=STAMP2)
    state = mark_status(state, key=key, review_status="VERIFIED", timestamp=STAMP2)

    record = state["records"][0]
    assert record["reading_status"] == "READ"
    assert record["review_status"] == "VERIFIED"
    assert len(record["status_history"]) == 3


def test_reading_queue_invalid_status_fails() -> None:
    state, _ = import_queue({"records": []}, [_record("A", [HIGH_PRIORITY, LWE_FAMILY])], timestamp=STAMP)
    key = state["records"][0]["dedup_key"]

    try:
        mark_status(state, key=key, reading_status="DONE", timestamp=STAMP2)
    except ValueError as exc:
        assert "invalid reading_status" in str(exc)
    else:
        raise AssertionError("invalid status should fail")


def test_reading_queue_link_stores_zotero_key_and_obsidian_note() -> None:
    state, _ = import_queue({"records": []}, [_record("A", [HIGH_PRIORITY, LWE_FAMILY])], timestamp=STAMP)
    key = state["records"][0]["dedup_key"]
    state = link_record(state, key=key, zotero_key="ABC123", obsidian_note="Papers/A.md", timestamp=STAMP2)

    assert state["records"][0]["zotero_key"] == "ABC123"
    assert state["records"][0]["obsidian_note_path"] == "Papers/A.md"


def test_reading_queue_export_obsidian_creates_dashboard_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        state, _ = import_queue({"records": []}, [_record("A", [HIGH_PRIORITY, LWE_FAMILY])], timestamp=STAMP)
        mark_status(state, key=state["records"][0]["dedup_key"], review_status="NEEDS_REPLICATION", timestamp=STAMP2)
        written = export_obsidian(state, root / "exports" / "reading-queue")

        dashboard = (root / "exports" / "reading-queue" / "reading-dashboard.md").read_text(encoding="utf-8")
        todo = (root / "exports" / "reading-queue" / "todo-read.md").read_text(encoding="utf-8")
        replication = (root / "exports" / "reading-queue" / "needs-replication.md").read_text(encoding="utf-8")

    assert len(written) == 3
    assert "type: reading_queue_dashboard" in dashboard
    assert "TODO Read" in todo
    assert "Needs Replication" in replication
    assert "<" not in dashboard
    assert "contentReference" not in dashboard


def test_reading_queue_dry_run_writes_no_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        state, _ = import_queue({"records": []}, [_record("A", [HIGH_PRIORITY, LWE_FAMILY])], timestamp=STAMP)
        targets = export_obsidian(state, root / "exports" / "reading-queue", dry_run=True)

    assert len(targets) == 3
    assert not (root / "exports").exists()


def test_reading_queue_audit_detects_duplicate_keys_and_invalid_records() -> None:
    state = {
        "records": [
            {"dedup_key": "x", "title": "", "source_url": "", "seen_dates": [], "reading_status": "BAD", "review_status": "TODO_VERIFY"},
            {"dedup_key": "x", "title": "Duplicate", "source_url": "https://example.org", "seen_dates": ["2026-05-31"], "reading_status": "TODO_READ", "review_status": "BAD"},
        ]
    }
    result = audit_state(state)

    assert result["critical_errors"] == 4
    assert result["warnings"] == 2
    assert result["duplicate_keys"] == ["x"]


def test_reading_queue_ordering_is_deterministic() -> None:
    records = [
        _record("B paper", [PQC_STANDARDS], label="B", score=70),
        _record("A paper", [LWE_FAMILY], label="A", score=90),
        _record("C paper", [PQC_STANDARDS], label="C", score=50),
    ]
    state, _ = import_queue({"records": []}, records, timestamp=STAMP)

    assert [record["title"] for record in state["records"]] == ["A paper", "B paper", "C paper"]


def test_reading_queue_save_state_writes_expected_json_shape() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "state" / "reading-queue.json"
        state, _ = import_queue({"records": []}, [_record("A", [HIGH_PRIORITY, LWE_FAMILY])], timestamp=STAMP)
        save_state(path, state)
        loaded = json.loads(path.read_text(encoding="utf-8"))

    assert loaded["schema_version"] == 1
    assert loaded["records"][0]["schema_version"] == 1
