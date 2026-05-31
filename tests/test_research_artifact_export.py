from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.research_artifact_export import (
    AI_LATTICE,
    LATTICE_REDUCTION_ATTACKS,
    LWE_FAMILY,
    generate_research_artifact_export,
    render_advisor_update,
    render_backlog,
)


def _weekly_payload() -> dict[str, object]:
    ai_record = {
        "title": "Transformer LWE coordinate selection",
        "abstract": "AI-assisted lattice cryptanalysis for LWE and BKZ.",
        "source": "arxiv",
        "source_url": "https://arxiv.org/abs/2605.00001",
        "publication_date": "2026-05-31",
        "relevance_label": "A",
        "relevance_score": 92,
        "research_sections": [
            "High-Priority Papers",
            LWE_FAMILY,
            LATTICE_REDUCTION_ATTACKS,
            AI_LATTICE,
            "Idea Bank Candidates",
            "Paper Plan Candidates",
        ],
        "ranking_explanation": {"relevance_label": "A", "relevance_score": 92},
        "seen_dates": ["2026-05-31"],
        "seen_sources": ["arxiv"],
    }
    module_record = {
        "title": "Module-SIS chameleon hash commitments",
        "abstract": "Module-SIS commitment and chameleon hash construction.",
        "source": "iacr_eprint",
        "source_url": "https://eprint.iacr.org/2026/001",
        "publication_date": "2026-05-30",
        "relevance_label": "A",
        "relevance_score": 88,
        "research_sections": [
            "High-Priority Papers",
            "SIS / NTRU / Commitments / Chameleon Hash",
            "Idea Bank Candidates",
            "Paper Plan Candidates",
        ],
        "ranking_explanation": {"relevance_label": "A", "relevance_score": 88},
        "seen_dates": ["2026-05-30"],
        "seen_sources": ["iacr_eprint"],
    }
    pqc_record = {
        "title": "ML-KEM side-channel implementation audit",
        "abstract": "Kyber ML-KEM side-channel and fault attack audit.",
        "source": "crossref",
        "source_url": "https://doi.org/10.1000/pqc",
        "publication_date": "2026-05-29",
        "relevance_label": "B",
        "relevance_score": 78,
        "research_sections": ["PQC Standards / ML-KEM / ML-DSA / Falcon", "Implementation / Side-channel / Systems"],
        "ranking_explanation": {"relevance_label": "B", "relevance_score": 78},
        "seen_dates": ["2026-05-29"],
        "seen_sources": ["crossref"],
    }
    return {
        "schema_version": 1,
        "week_id": "2026-W22",
        "from_date": "2026-05-25",
        "to_date": "2026-05-31",
        "sections": {
            "High-Priority Papers": [ai_record, module_record],
            LWE_FAMILY: [ai_record],
            LATTICE_REDUCTION_ATTACKS: [ai_record],
            AI_LATTICE: [ai_record],
            "SIS / NTRU / Commitments / Chameleon Hash": [module_record],
            "PQC Standards / ML-KEM / ML-DSA / Falcon": [pqc_record],
            "Implementation / Side-channel / Systems": [pqc_record],
        },
        "idea_bank_candidates": [
            {
                "title": ai_record["title"],
                "relevance_label": "A",
                "relevance_score": 92,
                "source_url": ai_record["source_url"],
                "reason": "命中 AI4Lattice / lattice cryptanalysis 主线，可作为 idea bank 候选记录。",
            }
        ],
        "paper_plan_candidates": [
            {
                "title": module_record["title"],
                "relevance_label": "A",
                "relevance_score": 88,
                "source_url": module_record["source_url"],
                "reason": "满足较高相关性，且贴近 Module-SIS/chameleon hash/commitment 短期论文规划。",
            }
        ],
    }


def _write_weekly(root: Path) -> Path:
    path = root / "data" / "weekly" / "2026-W22.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_weekly_payload(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_daily(root: Path) -> None:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "title": "Transformer LWE coordinate selection",
        "abstract": "AI-assisted lattice cryptanalysis for LWE and BKZ.",
        "source": "arxiv",
        "source_url": "https://arxiv.org/abs/2605.00001",
        "publication_date": "2026-05-31",
        "relevance_label": "A",
        "relevance_score": 92,
        "research_sections": [
            "High-Priority Papers",
            LWE_FAMILY,
            LATTICE_REDUCTION_ATTACKS,
            AI_LATTICE,
            "Idea Bank Candidates",
            "Paper Plan Candidates",
        ],
    }
    (data_dir / "2026-05-31.json").write_text(
        json.dumps({"records": [record], "source_health": []}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_research_artifact_export_loads_weekly_json() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly = _write_weekly(root)
        result = generate_research_artifact_export(
            from_date="2026-05-25",
            to_date="2026-05-31",
            weekly_json=weekly,
            daily_data_dir=root / "data",
            output_dir=root / "exports" / "research-artifacts",
            dry_run=True,
        )

    assert result["manifest"]["input_mode"] == "weekly_json"
    assert result["manifest"]["counts"]["records"] == 3


def test_research_artifact_export_falls_back_to_daily_json() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_daily(root)
        result = generate_research_artifact_export(
            from_date="2026-05-31",
            to_date="2026-05-31",
            daily_data_dir=root / "data",
            output_dir=root / "exports" / "research-artifacts",
            dry_run=True,
        )

    assert result["manifest"]["input_mode"] == "daily_json_fallback"
    assert result["manifest"]["counts"]["records"] == 1


def test_research_artifact_export_generates_manifest_shape_and_paths() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly = _write_weekly(root)
        result = generate_research_artifact_export(
            from_date="2026-05-25",
            to_date="2026-05-31",
            weekly_json=weekly,
            daily_data_dir=root / "data",
            output_dir=root / "exports" / "research-artifacts",
            formats="obsidian,advisor,backlog,zotero",
        )

        manifest = json.loads((root / "exports" / "research-artifacts" / "2026-05-31" / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert manifest["export_date"] == "2026-05-31"
    assert manifest["from_date"] == "2026-05-25"
    assert manifest["to_date"] == "2026-05-31"
    assert manifest["counts"]["records"] == 3
    assert all("exports\\research-artifacts" in path or "exports/research-artifacts" in path for path in manifest["output_files"])
    assert result["written_paths"]


def test_research_artifact_export_generates_obsidian_reading_queue() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly = _write_weekly(root)
        generate_research_artifact_export(
            from_date="2026-05-25",
            to_date="2026-05-31",
            weekly_json=weekly,
            daily_data_dir=root / "data",
            output_dir=root / "exports" / "research-artifacts",
            formats="obsidian",
        )
        queue = (root / "exports" / "research-artifacts" / "2026-05-31" / "obsidian" / "reading-queue.md").read_text(encoding="utf-8")

    assert "type: research_artifact_export" in queue
    assert "Transformer LWE coordinate selection" in queue
    assert "TODO_READ" in queue


def test_research_artifact_export_generates_advisor_update_draft_without_claims() -> None:
    payload = _weekly_payload()
    records = payload["sections"]["High-Priority Papers"]
    text = render_advisor_update(payload, records, date(2026, 5, 25), date(2026, 5, 31))

    assert "Draft only" in text
    assert "does not claim" in text
    assert "Needs verification" in text
    assert "proves" not in text.lower().replace("does not claim that any paper proves", "")


def test_research_artifact_export_generates_paper_reading_backlog() -> None:
    payload = _weekly_payload()
    records = payload["sections"]["High-Priority Papers"]
    text = render_backlog(records, date(2026, 5, 25), date(2026, 5, 31))

    assert "# Paper Reading Backlog" in text
    assert "Transformer LWE coordinate selection" in text
    assert "Module-SIS chameleon hash commitments" in text


def test_research_artifact_export_dry_run_writes_no_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly = _write_weekly(root)
        result = generate_research_artifact_export(
            from_date="2026-05-25",
            to_date="2026-05-31",
            weekly_json=weekly,
            daily_data_dir=root / "data",
            output_dir=root / "exports" / "research-artifacts",
            dry_run=True,
        )

        assert result["written_paths"] == []
        assert not (root / "exports").exists()


def test_research_artifact_export_deterministic_ordering() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly = _write_weekly(root)
        first = generate_research_artifact_export(
            from_date="2026-05-25",
            to_date="2026-05-31",
            weekly_json=weekly,
            daily_data_dir=root / "data",
            output_dir=root / "exports" / "research-artifacts",
            dry_run=True,
        )
        second = generate_research_artifact_export(
            from_date="2026-05-25",
            to_date="2026-05-31",
            weekly_json=weekly,
            daily_data_dir=root / "data",
            output_dir=root / "exports" / "research-artifacts",
            dry_run=True,
        )

    assert [record["title"] for record in first["records"]] == [record["title"] for record in second["records"]]
    assert first["records"][0]["title"] == "Transformer LWE coordinate selection"


def test_research_artifact_export_zotero_subset() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly = _write_weekly(root)
        generate_research_artifact_export(
            from_date="2026-05-25",
            to_date="2026-05-31",
            weekly_json=weekly,
            daily_data_dir=root / "data",
            output_dir=root / "exports" / "research-artifacts",
            formats="zotero",
        )
        run_dir = root / "exports" / "research-artifacts" / "2026-05-31" / "zotero"

        assert (run_dir / "reading-queue.json").exists()
        assert (run_dir / "reading-queue.bib").exists()
        assert (run_dir / "reading-queue.ris").exists()
