from __future__ import annotations

import copy
from datetime import date, datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.weekly_synthesis import build_weekly_synthesis, render_markdown


def _write_day(data_dir: Path, day: str, records: list[dict[str, object]]) -> None:
    payload = {
        "metadata": {"target_date": day},
        "records": records,
        "source_health": [{"source": "arxiv", "health_status": "green", "final_count": len(records)}],
    }
    (data_dir / f"{day}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _record(title: str, abstract: str, score: int = 90) -> dict[str, object]:
    return {
        "title": title,
        "abstract": abstract,
        "authors": ["Alice Example"],
        "source": "arxiv",
        "source_url": f"https://example.org/{title.lower().replace(' ', '-')}",
        "publication_date": "2026-06-18",
        "relevance_label": "A",
        "relevance_score": score,
        "keywords_matched": ["LWE", "BKZ"],
        "taxonomy_tags": ["lwe_sis_ntru_foundations"],
    }


def test_weekly_markdown_includes_compact_rationale_for_top_paper() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        data_dir.mkdir()
        _write_day(
            data_dir,
            "2026-06-18",
            [
                _record(
                    "Hybrid attacks against MLWE-based ML-KEM parameters",
                    (
                        "We study MLWE security estimates for ML-KEM. "
                        "We propose a hybrid attack model with lattice reduction and BKZ calibration. "
                        "Our results improve parameter-margin explanations."
                    ),
                )
            ],
        )
        payload = build_weekly_synthesis(
            data_dir,
            date(2026, 6, 18),
            date(2026, 6, 18),
            datetime(2026, 6, 18, tzinfo=timezone.utc),
        )

    markdown = render_markdown(payload)

    assert "## Top A-level Papers" in markdown
    assert "  - Rationale:" in markdown
    assert "MLWE" in markdown
    assert "Evidence basis: abstract-derived" in markdown
    assert "TODO_VERIFY" in markdown


def test_weekly_rendering_preserves_payload_order_scores_and_labels() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        data_dir.mkdir()
        _write_day(
            data_dir,
            "2026-06-18",
            [
                _record("BKZ cost models for LWE", "We study LWE and BKZ attack cost models.", 91),
                _record("Module-SIS commitments", "We propose Module-SIS commitment constructions.", 89),
            ],
        )
        payload = build_weekly_synthesis(data_dir, date(2026, 6, 18), date(2026, 6, 18))

    before = copy.deepcopy(payload)
    markdown = render_markdown(payload)

    assert payload == before
    rendered_titles = [
        line.split("｜", 1)[0].removeprefix("- ")
        for line in markdown.splitlines()
        if line.startswith("- ") and "｜A /" in line
    ]
    assert rendered_titles[:2] == [
        "BKZ cost models for LWE",
        "Module-SIS commitments",
    ]
    assert "｜A / 91｜" in markdown
    assert "｜A / 89｜" in markdown
