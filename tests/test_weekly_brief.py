from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.weekly import REQUIRED_SECTIONS, collect_week_records, parse_week, write_weekly_brief


def _record(
    title: str,
    *,
    doi: str | None = None,
    score: int = 70,
    label: str = "建议精读",
    tags: list[str] | None = None,
    reason: str = "测试 priority reason",
) -> dict[str, object]:
    return {
        "title": title,
        "doi": doi,
        "source": "iacr_eprint",
        "url": f"https://example.test/{title.lower().replace(' ', '-')}",
        "reading_priority_score": score,
        "priority_label": label,
        "reason_for_priority": reason,
        "research_tags": tags or [],
        "research_hooks": ["把该论文整理进一周实验计划。"],
        "advisor_questions": ["这篇是否适合作为组会精读？"],
    }


def _write_digest(data_dir: Path, day: str, records: list[dict[str, object]]) -> None:
    payload = {
        "metadata": {"target_date": day, "collector": "local_codex", "quality_status": "authoritative"},
        "records": records,
    }
    (data_dir / f"{day}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_parse_iso_week() -> None:
    start, end, label = parse_week("2026-W22")

    assert start.isoformat() == "2026-05-25"
    assert end.isoformat() == "2026-05-31"
    assert label == "2026-W22"


def test_collect_week_records_deduplicates_and_sorts_by_priority() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        _write_digest(
            data_dir,
            "2026-05-25",
            [
                _record("Lower duplicate", doi="10.1/dup", score=70),
                _record("AI LWE Attack", doi="10.1/ai", score=95, label="必须精读", tags=["AI4Lattice", "LWE"]),
            ],
        )
        _write_digest(
            data_dir,
            "2026-05-26",
            [
                _record("Higher duplicate", doi="10.1/dup", score=85, label="必须精读", tags=["BKZ"]),
                _record("Module-SIS Commitment", doi="10.1/msis", score=78, tags=["Module-SIS", "Commitment"]),
            ],
        )

        records, files = collect_week_records(data_dir, *parse_week("2026-W22")[:2])

        assert len(files) == 2
        assert len(records) == 3
        assert [record["title"] for record in records] == ["AI LWE Attack", "Higher duplicate", "Module-SIS Commitment"]
        duplicate = next(record for record in records if record["doi"] == "10.1/dup")
        assert duplicate["source_digest_dates"] == ["2026-05-25", "2026-05-26"]


def test_write_weekly_brief_outputs_required_sections_and_two_paths() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = root / "data"
        data_dir.mkdir()
        _write_digest(
            data_dir,
            "2026-05-25",
            [
                _record("Transformer LWE Attack", doi="10.1/lwe", score=96, label="必须精读", tags=["AI4Lattice", "LWE"]),
                _record("BKZ Hybrid Attack", doi="10.1/bkz", score=88, label="必须精读", tags=["BKZ", "Lattice Reduction"]),
                _record("Module-SIS Chameleon Hash", doi="10.1/msis", score=76, tags=["Module-SIS", "Chameleon Hash"]),
                _record("ML-KEM Side Channel", doi="10.1/kem", score=74, tags=["ML-KEM", "PQC Implementation"]),
            ],
        )

        result = write_weekly_brief(
            data_dir,
            root / "exports" / "weekly",
            root / "exports" / "obsidian" / "weekly",
            *parse_week("2026-W22")[:2],
            "2026-W22",
        )

        assert result.record_count == 4
        assert result.markdown_path.exists()
        assert result.obsidian_path.exists()
        markdown = result.markdown_path.read_text(encoding="utf-8")
        obsidian = result.obsidian_path.read_text(encoding="utf-8")
        assert markdown == obsidian
        for section in REQUIRED_SECTIONS:
            assert section in markdown
        assert markdown.index("Transformer LWE Attack") < markdown.index("BKZ Hybrid Attack")
        assert "Module-SIS Chameleon Hash" in markdown
        assert "ML-KEM Side Channel" in markdown
        assert "可问导师的问题" in markdown
