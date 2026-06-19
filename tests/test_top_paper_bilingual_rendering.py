from __future__ import annotations

from lattice_digest.monthly_synthesis import build_core_paper, render_markdown as render_monthly_markdown
from lattice_digest.weekly_synthesis import HIGH_PRIORITY, render_markdown as render_weekly_markdown


def _record() -> dict:
    return {
        "title": "Hybrid attacks against MLWE-based ML-KEM parameters",
        "abstract": (
            "We study MLWE instances used in ML-KEM. "
            "We propose a hybrid attack model combining lattice reduction and BKZ cost calibration. "
            "Our results improve parameter-margin analysis for post-quantum deployment."
        ),
        "keywords_matched": ["MLWE", "ML-KEM", "BKZ"],
        "taxonomy_tags": ["MLWE", "BKZ"],
        "relevance_label": "A",
        "relevance_score": 95,
        "reading_priority_score": 90,
        "source": "fixture",
        "source_url": "https://example.test/paper",
    }


def test_monthly_top_paper_renders_bilingual_block() -> None:
    core_paper = build_core_paper(_record())
    payload = {
        "month": "2026-06",
        "total_unique_records": 1,
        "class_counts": {"A": 1},
        "direction_counts": {"LWE / RLWE / MLWE": 1},
        "source_health_summary": {"source_starved": False, "sources": []},
        "core_papers": [core_paper],
        "reading_priority": {
            "Must Read": [
                {
                    "title": core_paper["title"],
                    "relevance_label": core_paper["relevance_label"],
                    "relevance_score": core_paper["relevance_score"],
                    "reading_priority_score": core_paper["reading_priority_score"],
                    "direction": core_paper["direction"],
                    "reason": core_paper["rationale"]["reading_action"],
                }
            ],
            "Should Skim": [],
            "Track Later": [],
            "Ignore / Peripheral": [],
        },
        "trend_summary": [],
        "TODO_VERIFY": {
            "papers_lacking_abstract": [],
            "title_only_or_metadata_supported_rationales": [],
            "source_starved_days": [],
            "missing_daily_files": [],
            "missing_source_health_records": [],
        },
    }

    markdown = render_monthly_markdown(payload)
    assert "中文：" in markdown
    assert "论文大致工作：" in markdown
    assert "English:" in markdown
    assert "Paper work summary:" in markdown
    assert "Core novelty:" in markdown
    assert "Hybrid attacks against MLWE-based ML-KEM parameters" in markdown


def test_weekly_top_a_paper_renders_bilingual_block_without_changing_payload_order() -> None:
    record = _record()
    payload = {
        "week_id": "2026-W23",
        "from_date": "2026-06-01",
        "to_date": "2026-06-07",
        "coverage": {
            "expected_days": 7,
            "loaded_days": ["2026-06-01"],
            "missing_days": [],
            "total_records": 1,
            "unique_records": 1,
            "label_counts": {"A": 1},
        },
        "label_counts": {"A": 1},
        "sections": {},
        "report_buckets": {HIGH_PRIORITY: [record]},
        "idea_bank_candidates": [],
        "paper_plan_candidates": [],
        "source_health_summary": {"available": False},
    }
    markdown = render_weekly_markdown(payload)

    assert payload["report_buckets"][HIGH_PRIORITY][0]["title"] == record["title"]
    assert "中文：" in markdown
    assert "English:" in markdown
    assert "Paper work summary:" in markdown
