from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.ideas import (
    classify_track,
    generate_idea_bank,
    ideas_from_records,
    merge_ideas,
    render_markdown,
)


def _record(
    title: str,
    *,
    score: int = 80,
    label: str = "建议精读",
    abstract: str = "",
    reason: str = "测试 priority reason",
    hooks: list[str] | None = None,
    questions: list[str] | None = None,
    tags: list[str] | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "url": f"https://example.test/{title.lower().replace(' ', '-')}",
        "source": "iacr_eprint",
        "reading_priority_score": score,
        "priority_label": label,
        "abstract": abstract,
        "reason_for_priority": reason,
        "research_hooks": hooks or [],
        "advisor_questions": questions or ["这个方向是否值得投入？"],
        "research_tags": tags or [],
    }


def _write_digest(path: Path, records: list[dict[str, object]], day: str = "2026-05-29") -> Path:
    payload = {"metadata": {"target_date": day}, "records": records}
    file_path = path / f"{day}.json"
    file_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return file_path


def test_research_hooks_generate_idea() -> None:
    record = _record(
        "Transformer LWE attack ranking",
        abstract="AI-assisted lattice cryptanalysis for LWE and BKZ.",
        hooks=["构造 LWE coordinate selection benchmark。"],
    )

    ideas = ideas_from_records([record])

    assert len(ideas) == 1
    assert ideas[0]["title"] == "构造 LWE coordinate selection benchmark。"
    assert ideas[0]["track"] == "AI4Lattice"


def test_high_priority_without_hooks_generates_conservative_seed() -> None:
    record = _record("BKZ cost model for LWE attacks", hooks=[], tags=["BKZ", "LWE"], score=88, label="必须精读")

    ideas = ideas_from_records([record])

    assert len(ideas) == 1
    assert "保守研究 seed" in ideas[0]["title"]


def test_track_classification_rules() -> None:
    assert classify_track(
        _record("Transformer LWE", abstract="Transformer for LWE cryptanalysis and lattice reduction.")
    )[0] == "AI4Lattice"
    assert classify_track(_record("Generic Transformer", abstract="Transformer for traffic prediction."))[0] != "AI4Lattice"
    assert classify_track(_record("Module-SIS chameleon hash", abstract="Module-SIS commitment and chameleon hash."))[0] == "Module-SIS Primitive"
    assert classify_track(
        _record("ML-KEM implementation audit", abstract="Kyber ML-KEM implementation side-channel leakage audit.")
    )[0] == "ML-KEM / ML-DSA Implementation Security"
    assert classify_track(_record("G6K fplll BKZ", abstract="BKZ, G6K and fplll lattice reduction."))[0] == "BKZ / Lattice Reduction"


def test_generic_pqc_survey_is_not_strong_idea() -> None:
    record = _record(
        "Generic PQC survey",
        abstract="A survey and overview of post-quantum migration.",
        score=90,
        label="必须精读",
        hooks=["整理 PQC survey 背景。"],
    )

    idea = ideas_from_records([record])[0]

    assert idea["track"] == "PQC Systems"
    assert idea["idea_priority_score"] < 70
    assert idea["status"] in {"seed", "parked", "rejected"}


def test_idea_dedup_merges_source_papers() -> None:
    first = ideas_from_records(
        [
            _record(
                "Paper A",
                hooks=["构造 LWE coordinate selection benchmark。"],
                abstract="AI-assisted lattice cryptanalysis for LWE.",
            )
        ]
    )[0]
    second = ideas_from_records(
        [
            _record(
                "Paper B",
                hooks=["构造 LWE coordinate selection benchmark。"],
                abstract="AI-assisted lattice cryptanalysis for LWE.",
            )
        ]
    )[0]

    merged = merge_ideas([first, second])

    assert len(merged) == 1
    assert len(merged[0]["source_papers"]) == 2


def test_existing_idea_bank_incremental_update() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = root / "data"
        data_dir.mkdir()
        output_dir = root / "exports" / "ideas"
        obsidian_dir = root / "exports" / "obsidian" / "ideas"
        existing = ideas_from_records(
            [
                _record(
                    "Existing Paper",
                    hooks=["构造 LWE coordinate selection benchmark。"],
                    abstract="AI-assisted lattice cryptanalysis for LWE.",
                )
            ]
        )
        output_dir.mkdir(parents=True)
        existing_bank = output_dir / "idea-bank.json"
        existing_bank.write_text(json.dumps({"ideas": existing}, ensure_ascii=False), encoding="utf-8")
        _write_digest(
            data_dir,
            [
                _record(
                    "New Paper",
                    hooks=["构造 LWE coordinate selection benchmark。"],
                    abstract="AI-assisted lattice cryptanalysis for LWE.",
                )
            ],
        )

        result = generate_idea_bank(data_dir, output_dir, obsidian_dir, existing_bank=existing_bank)

        assert len(result.ideas) == 1
        assert len(result.ideas[0]["source_papers"]) == 2


def test_markdown_contains_11_sections_and_obsidian_links_are_clean() -> None:
    idea = ideas_from_records(
        [
            _record(
                "Transformer LWE",
                abstract="<b>bad</b> contentReference oaicite id=abc AI-assisted lattice cryptanalysis for LWE.",
                hooks=["构造 LWE coordinate selection benchmark。"],
            )
        ]
    )[0]

    markdown = render_markdown([idea])

    for section in [
        "## 1. 本周最值得推进的 idea",
        "## 2. AI4Lattice / AI-assisted Cryptanalysis",
        "## 3. LWE / RLWE / MLWE Cryptanalysis",
        "## 4. BKZ / Lattice Reduction / Hybrid Attack",
        "## 5. Module-SIS / Commitment / Chameleon Hash",
        "## 6. ML-KEM / ML-DSA Implementation Security",
        "## 7. PQC Systems / Protocols",
        "## 8. FHE / Parameter Security",
        "## 9. ZK-friendly Post-Quantum Privacy",
        "## 10. 暂存 / 低优先级 idea",
        "## 11. 下一步行动清单",
    ]:
        assert section in markdown
    assert "[[AI4Lattice]]" in markdown
    assert "<b>" not in markdown
    assert "contentReference" not in markdown
    assert "oaicite" not in markdown
    assert "id=" not in markdown


def test_dry_run_does_not_write_files_and_min_priority_filters() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = root / "data"
        data_dir.mkdir()
        _write_digest(
            data_dir,
            [
                _record("Low paper", score=40, label="暂存", hooks=["低优先级背景。"]),
                _record("High paper", score=80, label="建议精读", hooks=["构造 LWE coordinate selection benchmark。"], abstract="LWE cryptanalysis."),
            ],
        )

        result = generate_idea_bank(
            data_dir,
            root / "exports" / "ideas",
            root / "exports" / "obsidian" / "ideas",
            min_paper_priority=70,
            dry_run=True,
        )

        assert len(result.ideas) == 1
        assert not (root / "exports").exists()
        assert all(0 <= int(idea["idea_priority_score"]) <= 100 for idea in result.ideas)
