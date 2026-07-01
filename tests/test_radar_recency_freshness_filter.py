from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.digest import generate_markdown
from lattice_digest.models import make_paper_record
from lattice_digest.radar_freshness import apply_daily_freshness_policy, enrich_record_for_daily_radar
from lattice_digest.storage import write_json


def _paper(**overrides: object):
    data = {
        "title": "BKZ cost models for LWE attacks",
        "abstract": "We study lattice cryptanalysis for LWE and BKZ hybrid attacks.",
        "source": "arxiv",
        "source_url": "https://arxiv.org/abs/2607.00001",
        "relevance_label": "A",
        "relevance_score": 95,
        "publication_date": "2026-07-01",
    }
    data.update(overrides)
    return make_paper_record(**data)


def test_june_early_mid_month_papers_are_excluded_from_2026_07_01_primary_today_new() -> None:
    old_items = [
        _paper(title="June 1 LWE paper", source_url="https://arxiv.org/abs/2606.00001", publication_date="2026-06-01"),
        _paper(title="June 20 MLWE paper", source_url="https://arxiv.org/abs/2606.00020", publication_date="2026-06-20"),
    ]

    primary, routed = apply_daily_freshness_policy(old_items, date(2026, 7, 1))

    assert primary == []
    assert {record.title for record in routed} == {"June 1 LWE paper", "June 20 MLWE paper"}
    assert all(record.freshness_bucket == "backfill" for record in routed)
    assert all(record.freshness_reason for record in routed)


def test_stale_high_relevance_cannot_be_promoted_into_primary_by_ranking() -> None:
    stale = _paper(
        title="Transformer LWE coordinate selection with BKZ hybrid attacks",
        source_url="https://arxiv.org/abs/2606.00010",
        publication_date="2026-06-10",
        relevance_score=100,
    )

    markdown = generate_markdown([stale], date(2026, 7, 1))

    assert "## 2. 高优先级论文\n\n今日无高优先级论文。" in markdown
    assert "## 2b. 回填 / 较早 / 待核验项目" in markdown
    assert "Transformer LWE coordinate selection with BKZ hybrid attacks" in markdown
    assert "freshness_bucket：backfill" in markdown


def test_first_seen_inside_window_routes_old_publication_as_newly_discovered_backfill() -> None:
    record = _paper(publication_date="2026-06-15", first_seen_date="2026-07-01")

    primary, routed = apply_daily_freshness_policy([record], date(2026, 7, 1))

    assert primary == []
    assert routed[0].freshness_bucket == "newly_discovered_but_older"
    assert routed[0].selected_date_basis == "first_seen_date"
    assert routed[0].primary_today_new_eligible is False


def test_official_status_changed_inside_window_uses_explicit_update_bucket() -> None:
    record = _paper(publication_date="2026-06-12", official_status_change_date="2026-07-01")

    primary, routed = apply_daily_freshness_policy([record], date(2026, 7, 1))

    assert primary == []
    assert routed[0].freshness_bucket == "official_status_changed"
    assert routed[0].selected_date_basis == "official_status_change_date"


def test_missing_or_ambiguous_source_date_is_todo_verify_and_non_primary() -> None:
    record = _paper(publication_date=None, update_date="unknown")

    primary, routed = apply_daily_freshness_policy([record], date(2026, 7, 1))

    assert primary == []
    assert routed[0].freshness_bucket == "date_uncertain_todo_verify"
    assert routed[0].selected_date_basis == "TODO_VERIFY"
    assert "selected_date_basis" in routed[0].TODO_VERIFY_flags


def test_source_publication_date_is_not_overwritten_by_first_seen_or_scrape_time() -> None:
    record = _paper(publication_date="2026-06-15", first_seen_date="2026-07-01")

    enriched = enrich_record_for_daily_radar(record, date(2026, 7, 1))

    assert enriched.publication_date == "2026-06-15"
    assert enriched.first_seen_date == "2026-07-01"
    assert enriched.selected_date_basis == "first_seen_date"


def test_json_output_contains_freshness_fields_without_replacing_source_date() -> None:
    record = _paper(publication_date="2026-06-15", first_seen_date="2026-07-01")
    with TemporaryDirectory() as tmp:
        path = write_json([record], Path(tmp), date(2026, 7, 1))
        item = json.loads(path.read_text(encoding="utf-8"))["records"][0]

    assert item["publication_date"] == "2026-06-15"
    assert item["first_seen_date"] == "2026-07-01"
    assert item["freshness_bucket"] == "newly_discovered_but_older"
    assert item["primary_today_new_eligible"] is False
