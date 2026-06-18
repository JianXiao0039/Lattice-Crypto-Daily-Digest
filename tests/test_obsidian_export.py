from __future__ import annotations

import json
from pathlib import Path

from lattice_digest.obsidian_scaffold import generate_scaffolds, render_note


def _queue_record(title: str = "Abstract supported LWE paper") -> dict[str, object]:
    return {
        "dedup_key": "title:abstract-supported-lwe-paper",
        "title": title,
        "source": "arxiv",
        "source_url": "https://example.test/lwe",
        "doi": "",
        "arxiv_id": "2606.00001",
        "publication_date": "2026-06-18",
        "date": "2026-06-18",
        "relevance_label": "A",
        "class_label": "A",
        "relevance_score": 90,
        "score": 90,
        "queue_priority": "HIGH",
        "reading_action": "精读",
        "reading_status": "TODO_READ",
        "review_status": "TODO_VERIFY",
        "track": "LWE / RLWE / MLWE",
        "research_sections": ["LWE / RLWE / MLWE"],
        "report_buckets": ["High-Priority Papers"],
        "direction_tags": ["LWE / RLWE / MLWE"],
        "evidence_basis": ["abstract-derived", "metadata-derived"],
        "rationale_problem": "从摘要看，论文关注的问题是：LWE attack costs.",
        "rationale_method": "It proposes a benchmark method.",
        "rationale_contribution": "It improves attack-cost guidance.",
        "rationale_relevance": "该论文与 lattice/PQC radar 相关。",
        "rationale_caveat": "TODO_VERIFY: full proof details.",
        "TODO_VERIFY": ["TODO_VERIFY: full proof details."],
        "seen_sources": ["arxiv"],
        "status_history": [],
    }


def test_obsidian_note_scaffold_contains_radar_reading_sections() -> None:
    note = render_note(_queue_record())

    assert "status: unread" in note
    assert 'reading_action: "精读"' in note
    assert "## 1. Radar Recommendation" in note
    assert "## 2. Paper Work Summary" in note
    assert "## 3. Relevance to My Research" in note
    assert "## 4. Reading Checklist" in note
    assert "## 5. TODO_VERIFY" in note
    assert "## 6. Links" in note


def test_obsidian_export_is_deterministic_utf8_lf_one_final_newline(tmp_path: Path) -> None:
    state_path = tmp_path / "state/reading-queue.json"
    output_dir = tmp_path / "exports/obsidian-paper-notes/Papers"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(json.dumps({"records": [_queue_record()]}, ensure_ascii=False), encoding="utf-8")

    first = generate_scaffolds(state_path=state_path, output_dir=output_dir)
    path = first["written"][0]
    first_bytes = path.read_bytes()
    second = generate_scaffolds(state_path=state_path, output_dir=output_dir)

    assert second["written"] == []
    assert first_bytes == path.read_bytes()
    assert not first_bytes.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in first_bytes
    assert first_bytes.endswith(b"\n")
    assert not first_bytes.endswith(b"\n\n")


def test_refresh_generated_updates_tool_created_note_only(tmp_path: Path) -> None:
    state_path = tmp_path / "state/reading-queue.json"
    output_dir = tmp_path / "exports/obsidian-paper-notes/Papers"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(json.dumps({"records": [_queue_record()]}, ensure_ascii=False), encoding="utf-8")
    first = generate_scaffolds(state_path=state_path, output_dir=output_dir)
    path = first["written"][0]
    path.write_text('---\ncreated_by: "lattice_digest.obsidian_scaffold"\n---\n\nold generated note\n', encoding="utf-8")

    second = generate_scaffolds(state_path=state_path, output_dir=output_dir, refresh_generated=True)

    assert second["refreshed"] == [path]
    assert "old generated note" not in path.read_text(encoding="utf-8")
    assert "## 1. Radar Recommendation" in path.read_text(encoding="utf-8")


def test_refresh_generated_does_not_overwrite_manual_note(tmp_path: Path) -> None:
    state_path = tmp_path / "state/reading-queue.json"
    output_dir = tmp_path / "exports/obsidian-paper-notes/Papers"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(json.dumps({"records": [_queue_record()]}, ensure_ascii=False), encoding="utf-8")
    first = generate_scaffolds(state_path=state_path, output_dir=output_dir)
    path = first["written"][0]
    path.write_text("manual note", encoding="utf-8")

    second = generate_scaffolds(state_path=state_path, output_dir=output_dir, refresh_generated=True)

    assert second["refreshed"] == []
    assert second["skipped_existing"] == [path]
    assert path.read_text(encoding="utf-8") == "manual note"


def test_title_only_note_does_not_hallucinate_method() -> None:
    record = _queue_record("Title only paper")
    record["evidence_basis"] = ["title-derived"]
    record["rationale_method"] = "仅有标题/关键词，不能可靠判断具体方法、构造、攻击或系统。"
    record["rationale_contribution"] = "仅有标题/关键词，不能可靠判断论文声称的新贡献。"

    note = render_note(record)

    assert "不能可靠判断具体方法" in note
    assert "we prove" not in note.lower()
