from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.weekly_synthesis import (
    AI_LATTICE,
    IDEA_BANK_CANDIDATES,
    LATTICE_REDUCTION_ATTACKS,
    LWE_FAMILY,
    PAPER_PLAN_CANDIDATES,
    PQC_STANDARDS,
    SIS_NTRU_COMMITMENTS,
    build_weekly_synthesis,
    main,
    render_markdown,
    write_weekly_outputs,
)


def _record(
    title: str,
    abstract: str,
    *,
    label: str = "A",
    score: int = 90,
    source: str = "arxiv",
    url: str | None = None,
    doi: str | None = None,
    arxiv_id: str | None = None,
    publication_date: str = "2026-05-30",
) -> dict[str, object]:
    return {
        "title": title,
        "normalized_title": title.lower(),
        "abstract": abstract,
        "authors": ["Alice Example"],
        "source": source,
        "source_url": url or f"https://example.org/{title.lower().replace(' ', '-')}",
        "doi": doi,
        "arxiv_id": arxiv_id,
        "publication_date": publication_date,
        "relevance_label": label,
        "relevance_score": score,
        "keywords_matched": [],
        "taxonomy_tags": [],
        "ranking_explanation": {
            "relevance_label": label,
            "relevance_score": score,
            "positive_signals": [],
            "negative_signals": [],
        },
    }


def _write_day(data_dir: Path, day: str, records: list[dict[str, object]]) -> None:
    payload = {
        "metadata": {"target_date": day},
        "records": records,
        "source_health": [
            {
                "source": "arxiv",
                "health_status": "green",
                "final_count": len(records),
                "error_type": None,
            }
        ],
    }
    (data_dir / f"{day}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sample_data(data_dir: Path) -> None:
    data_dir.mkdir()
    _write_day(
        data_dir,
        "2026-05-29",
        [
            _record(
                "Transformer LWE coordinate selection",
                "AI-assisted lattice cryptanalysis for LWE and BKZ hybrid attack.",
                score=92,
                arxiv_id="2605.00001v1",
                publication_date="2026-05-29",
            ),
            _record(
                "Module-SIS chameleon hash commitments",
                "Module-SIS commitment and chameleon hash construction.",
                score=88,
                doi="10.1000/module-sis",
                publication_date="2026-05-29",
            ),
        ],
    )
    _write_day(
        data_dir,
        "2026-05-31",
        [
            _record(
                "Module-SIS chameleon hash commitments",
                "SIS and NTRU commitment interface with chameleon hash.",
                score=86,
                source="iacr_eprint",
                doi="10.1000/module-sis",
                publication_date="2026-05-31",
            ),
            _record(
                "ML-KEM side-channel implementation audit",
                "Kyber ML-KEM implementation side-channel and fault attack audit.",
                label="B",
                score=78,
                source="iacr_eprint",
                publication_date="2026-05-31",
            ),
            _record(
                "Generic PQC migration survey",
                "Post-quantum cryptography deployment overview.",
                label="B",
                score=60,
                source="crossref",
                publication_date="2026-05-31",
            ),
        ],
    )


def test_weekly_synthesis_loads_daily_json_files_and_reports_missing_days() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        _sample_data(data_dir)

        payload = build_weekly_synthesis(
            data_dir,
            date(2026, 5, 29),
            date(2026, 5, 31),
            datetime(2026, 5, 31, tzinfo=timezone.utc),
        )

    assert payload["coverage"]["loaded_days"] == ["2026-05-29", "2026-05-31"]
    assert payload["coverage"]["missing_days"] == ["2026-05-30"]
    assert payload["coverage"]["expected_days"] == 3


def test_weekly_synthesis_merges_duplicates_and_preserves_seen_metadata() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        _sample_data(data_dir)
        payload = build_weekly_synthesis(data_dir, date(2026, 5, 29), date(2026, 5, 31))

    sis_records = [
        record
        for record in payload["sections"][SIS_NTRU_COMMITMENTS]
        if record["title"] == "Module-SIS chameleon hash commitments"
    ]
    assert len(sis_records) == 1
    assert sis_records[0]["seen_dates"] == ["2026-05-29", "2026-05-31"]
    assert sis_records[0]["seen_sources"] == ["arxiv", "iacr_eprint"]


def test_weekly_synthesis_label_counts_are_correct() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        _sample_data(data_dir)
        payload = build_weekly_synthesis(data_dir, date(2026, 5, 29), date(2026, 5, 31))

    assert payload["coverage"]["total_records"] == 5
    assert payload["coverage"]["unique_records"] == 4
    assert payload["label_counts"] == {"A": 2, "B": 2}


def test_weekly_synthesis_section_grouping_works() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        _sample_data(data_dir)
        payload = build_weekly_synthesis(data_dir, date(2026, 5, 29), date(2026, 5, 31))

    assert payload["sections"][LWE_FAMILY]
    assert payload["sections"][AI_LATTICE]
    assert payload["sections"][SIS_NTRU_COMMITMENTS]
    assert payload["sections"][LATTICE_REDUCTION_ATTACKS]
    assert payload["sections"][PQC_STANDARDS]


def test_weekly_json_output_shape_is_stable() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = root / "data"
        _sample_data(data_dir)
        payload = build_weekly_synthesis(data_dir, date(2026, 5, 29), date(2026, 5, 31))
        json_path, markdown_path = write_weekly_outputs(payload, root / "data" / "weekly", root / "digests" / "weekly")
        loaded = json.loads(json_path.read_text(encoding="utf-8"))

    assert markdown_path.name.endswith(".md")
    assert loaded["schema_version"] == 1
    assert loaded["week_id"].startswith("2026-W")
    assert set(loaded) >= {
        "schema_version",
        "week_id",
        "coverage",
        "label_counts",
        "sections",
        "idea_bank_candidates",
        "paper_plan_candidates",
        "source_health_summary",
    }


def test_weekly_markdown_contains_expected_section_headers() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        _sample_data(data_dir)
        payload = build_weekly_synthesis(data_dir, date(2026, 5, 29), date(2026, 5, 31))
        markdown = render_markdown(payload)

    for header in [
        "## Executive Summary",
        "## High-Priority Papers This Week",
        "## LWE / RLWE / MLWE",
        "## SIS / NTRU / Commitments / Chameleon Hash",
        "## BKZ / LLL / G6K / Lattice Reduction / Attacks",
        "## PQC Standards / ML-KEM / ML-DSA / Falcon",
        "## AI-assisted Lattice Cryptanalysis",
        "## Implementation / Side-channel / Systems",
        "## Idea Bank Candidates",
        "## Paper Plan Candidates",
        "## Source Health Summary",
        "## Coverage Notes",
    ]:
        assert header in markdown


def test_idea_bank_candidate_selection_is_deterministic() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        _sample_data(data_dir)
        first = build_weekly_synthesis(data_dir, date(2026, 5, 29), date(2026, 5, 31))
        second = build_weekly_synthesis(data_dir, date(2026, 5, 29), date(2026, 5, 31))

    assert first["idea_bank_candidates"] == second["idea_bank_candidates"]
    assert any(IDEA_BANK_CANDIDATES in record["research_sections"] for record in first["sections"][AI_LATTICE])


def test_paper_plan_candidate_selection_is_deterministic() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        _sample_data(data_dir)
        first = build_weekly_synthesis(data_dir, date(2026, 5, 29), date(2026, 5, 31))
        second = build_weekly_synthesis(data_dir, date(2026, 5, 29), date(2026, 5, 31))

    assert first["paper_plan_candidates"] == second["paper_plan_candidates"]
    assert any(PAPER_PLAN_CANDIDATES in record["research_sections"] for record in first["sections"][SIS_NTRU_COMMITMENTS])


def test_weekly_synthesis_dry_run_writes_no_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = root / "data"
        _sample_data(data_dir)
        result = main(
            [
                "--from-date",
                "2026-05-29",
                "--to-date",
                "2026-05-31",
                "--data-dir",
                str(data_dir),
                "--json-output-dir",
                str(root / "data" / "weekly"),
                "--digest-output-dir",
                str(root / "digests" / "weekly"),
                "--dry-run",
            ]
        )

        assert result == 0
        assert not (root / "data" / "weekly").exists()
        assert not (root / "digests" / "weekly").exists()
