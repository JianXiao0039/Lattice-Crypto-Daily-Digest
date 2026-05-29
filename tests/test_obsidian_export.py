from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.obsidian import export_cards, render_card, safe_slug


def _digest_payload() -> dict:
    return {
        "metadata": {
            "target_date": "2026-05-29",
            "collector": "local_codex",
            "quality_status": "authoritative",
        },
        "records": [
            {
                "title": "Swin Transformer for LWE/BKZ: ML-KEM?",
                "authors": ["Alice", "Bob"],
                "source": "arxiv",
                "url": "https://arxiv.org/abs/2601.00001",
                "date": "2026-05-29",
                "abstract": "",
                "reading_priority_score": 91,
                "priority_label": "必须精读",
                "reason_for_priority": "命中 AI4Lattice、LWE、BKZ 与 ML-KEM 主线。",
                "suggested_action": "Read today",
                "research_tags": ["AI4Lattice", "LWE", "BKZ", "ML-KEM"],
                "research_hooks": ["复现一个小型 LWE ranking benchmark。"],
                "advisor_questions": ["这个模型能否接入 dual attack？"],
            },
            {
                "title": "Generic PQC migration overview",
                "source": "crossref",
                "url": "https://doi.org/10.0000/pqc",
                "abstract": "A generic overview.",
                "reading_priority_score": 42,
                "priority_label": "暂存",
                "reason_for_priority": "泛 PQC 背景。",
                "suggested_action": "Save for background",
                "research_tags": ["PQC"],
            },
        ],
    }


def _write_digest(tmp: Path, payload: dict | None = None) -> Path:
    path = tmp / "2026-05-29.json"
    path.write_text(json.dumps(payload or _digest_payload(), ensure_ascii=False), encoding="utf-8")
    return path


def test_export_generates_obsidian_card_with_frontmatter_and_sections() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        input_path = _write_digest(root)
        output_dir = root / "exports" / "obsidian" / "papers"

        results = export_cards(input_path, output_dir, min_priority=70)

        assert len(results) == 1
        card = results[0].path.read_text(encoding="utf-8")
        assert "type: paper_card" in card
        assert "status: unread" in card
        assert 'source_digest_date: "2026-05-29"' in card
        assert 'title: "Swin Transformer for LWE/BKZ: ML-KEM?"' in card
        assert "reading_priority_score: 91" in card
        assert 'priority_label: "必须精读"' in card
        assert "tags:" in card
        assert '"lattice_crypto"' in card
        for index in range(1, 12):
            assert f"## {index}. " in card


def test_missing_abstract_outputs_todo_verify() -> None:
    card = render_card(_digest_payload()["records"][0], "2026-05-29", _digest_payload()["metadata"])

    assert "TODO_VERIFY：当前 digest 未提供摘要，需要打开原文核验。" in card


def test_min_priority_filters_low_priority_records() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        input_path = _write_digest(root)
        output_dir = root / "exports" / "obsidian" / "papers"

        results = export_cards(input_path, output_dir, min_priority=90)

        assert len(results) == 1
        assert "swin-transformer" in results[0].path.name


def test_dry_run_does_not_write_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        input_path = _write_digest(root)
        output_dir = root / "exports" / "obsidian" / "papers"

        results = export_cards(input_path, output_dir, min_priority=70, dry_run=True)

        assert len(results) == 1
        assert not output_dir.exists()
        assert not results[0].path.exists()


def test_slug_removes_windows_illegal_characters() -> None:
    slug = safe_slug('A <Bad>: "LWE/ML-KEM" | Paper?*')

    assert not any(char in slug for char in '<>:"/\\|?*')
    assert " " not in slug


def test_existing_file_is_not_overwritten_by_default() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        input_path = _write_digest(root)
        output_dir = root / "exports" / "obsidian" / "papers"
        first = export_cards(input_path, output_dir, min_priority=70)[0]
        first.path.write_text("HAND WRITTEN NOTE", encoding="utf-8")

        second = export_cards(input_path, output_dir, min_priority=70)[0]

        assert first.path.read_text(encoding="utf-8") == "HAND WRITTEN NOTE"
        assert second.path != first.path
        assert "__new" in second.path.stem


def test_force_overwrites_and_backs_up_existing_file() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        input_path = _write_digest(root)
        output_dir = root / "exports" / "obsidian" / "papers"
        first = export_cards(input_path, output_dir, min_priority=70)[0]
        first.path.write_text("HAND WRITTEN NOTE", encoding="utf-8")

        second = export_cards(input_path, output_dir, min_priority=70, force=True)[0]

        assert second.path == first.path
        assert "HAND WRITTEN NOTE" not in second.path.read_text(encoding="utf-8")
        backups = list((root / "exports" / "obsidian" / "backups").glob("**/*.md"))
        assert backups
        assert backups[0].read_text(encoding="utf-8") == "HAND WRITTEN NOTE"


def test_generated_card_has_no_html_or_pollution_markers() -> None:
    payload = _digest_payload()
    payload["records"][0]["abstract"] = "<div>bad</div> contentReference oaicite id=abc"
    card = render_card(payload["records"][0], "2026-05-29", payload["metadata"])

    assert "<div>" not in card
    assert "contentReference" not in card
    assert "oaicite" not in card
    assert "id=" not in card


def test_obsidian_wikilinks_cover_common_lattice_topics() -> None:
    card = render_card(_digest_payload()["records"][0], "2026-05-29", _digest_payload()["metadata"])

    for link in ["[[LWE]]", "[[BKZ]]", "[[ML-KEM]]", "[[AI4Lattice]]"]:
        assert link in card
