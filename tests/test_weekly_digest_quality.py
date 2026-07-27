from __future__ import annotations

import copy
import json
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from lattice_digest.artifact_paths import daily_data_path
from lattice_digest.digest import generate_markdown
from lattice_digest.models import make_paper_record
from lattice_digest.weekly_synthesis import (
    _all_weekly_records,
    _route_weekly_records,
    build_weekly_synthesis,
    dedup_key,
    render_markdown,
    write_weekly_outputs,
)


def _record(
    title: str,
    *,
    source: str = "arxiv",
    source_url: str | None = None,
    doi: str | None = None,
    arxiv_id: str | None = None,
    eprint_id: str | None = None,
    freshness_bucket: str = "primary_today_new",
    primary_eligible: bool = True,
    recommendation_level: str = "Strong",
    recommendation_score: int = 90,
    research_value_score: int = 92,
    suggested_action: str = "Read today",
    todo_flags: list[str] | None = None,
    risk_flags: list[str] | None = None,
    user_tags: list[str] | None = None,
    venue: str = "arXiv",
    venue_type: str = "preprint",
    ccf_rank: str = "N/A",
    venue_status: str = "known",
    abstract_zh: str = "[generated/translated] 中文摘要",
) -> dict[str, object]:
    return {
        "title": title,
        "normalized_title": title.lower(),
        "abstract": f"{title} studies lattice cryptography and post-quantum security.",
        "abstract_en": f"{title} studies lattice cryptography.",
        "abstract_zh": abstract_zh,
        "conclusion_en": "[generated summary] Research value requires source verification.",
        "conclusion_zh": "[generated/translated] 结论摘要",
        "authors": ["Alice Example"],
        "source": source,
        "source_url": source_url or f"https://example.org/{title.lower().replace(' ', '-')}",
        "doi": doi,
        "arxiv_id": arxiv_id,
        "eprint_id": eprint_id,
        "publication_date": "2026-07-06",
        "selected_date_basis": "publication_date",
        "freshness_bucket": freshness_bucket,
        "freshness_reason": (
            "publication_date within freshness window"
            if primary_eligible
            else "outside freshness window; route outside primary"
        ),
        "primary_today_new_eligible": primary_eligible,
        "relevance_label": "A",
        "relevance_score": 95,
        "recommendation_level": recommendation_level,
        "recommendation_score": recommendation_score,
        "research_value_score": research_value_score,
        "recommendation_reason": "Directly supports Sparse LWE cryptanalysis and BKZ cost analysis.",
        "user_relevance_tags": user_tags or ["Sparse LWE", "BKZ", "PhD paper reading"],
        "phd_application_relevance": "Useful for PhD direction, PI email, and project ideas.",
        "recommendation_risk_flags": risk_flags or [],
        "recommendation_evidence_basis": ["title", "abstract", "freshness"],
        "suggested_action": suggested_action,
        "TODO_VERIFY_flags": todo_flags or [],
        "venue": venue,
        "venue_type": venue_type,
        "CCF_rank": ccf_rank,
        "venue_status": venue_status,
        "taxonomy_tags": ["lwe_sis_ntru_foundations"],
        "keywords_matched": ["LWE", "BKZ"],
    }


def _write_day(
    data_dir: Path,
    day: str,
    records: list[dict[str, object]],
    *,
    health_status: str = "green",
    source: str = "arxiv",
) -> None:
    payload = {
        "metadata": {"target_date": day},
        "records": records,
        "source_health": [
            {
                "source": source,
                "health_status": health_status,
                "status": health_status,
                "final_count": len(records),
                "error_type": None if health_status == "green" else "timeout",
            }
        ],
    }
    path = daily_data_path(day, data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build(
    records: list[dict[str, object]],
    *,
    health_status: str = "green",
) -> dict[str, object]:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        _write_day(data_dir, "2026-07-06", records, health_status=health_status)
        return build_weekly_synthesis(
            data_dir,
            date(2026, 7, 6),
            date(2026, 7, 6),
            datetime(2026, 7, 6, tzinfo=timezone.utc),
        )


def test_weekly_summary_and_date_range_render() -> None:
    markdown = render_markdown(_build([_record("Sparse LWE attack")]))

    assert "## Executive Summary" in markdown
    assert "2026-07-06 .. 2026-07-06" in markdown
    assert "安全 primary-new 1" in markdown


def test_canonical_daily_aggregation_is_deterministic() -> None:
    first = _build([_record("Sparse LWE attack")])
    second = _build([_record("Sparse LWE attack")])

    assert first == second
    assert first["coverage"]["loaded_days"] == ["2026-07-06"]


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (_record("DOI first", doi="10.1000/weekly"), _record("DOI second", doi="https://doi.org/10.1000/weekly")),
        (_record("arXiv first", arxiv_id="2607.00001v1"), _record("arXiv second", arxiv_id="2607.00001v3")),
        (_record("ePrint first", eprint_id="2026/123"), _record("ePrint second", eprint_id="2026/123")),
        (
            _record("URL first", source_url="https://example.org/canonical"),
            _record("URL second", source_url="https://example.org/canonical"),
        ),
        (
            _record("Normalized Weekly Title", source_url=""),
            {
                **_record("Normalized weekly title!", source_url=""),
                "source_url": "",
                "normalized_title": "",
            },
        ),
    ],
)
def test_weekly_dedup_identity_priority(left: dict[str, object], right: dict[str, object]) -> None:
    if "Title" in str(left["title"]):
        left["source_url"] = ""
    payload = _build([left, right])

    assert payload["coverage"]["unique_records"] == 1


def test_duplicate_merge_preserves_seen_dates_sources_flags_and_placements() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        first = _record("Merged paper", doi="10.1000/merge", todo_flags=["venue"])
        second = _record(
            "Merged paper update",
            doi="10.1000/merge",
            source="iacr_eprint",
            freshness_bucket="backfill",
            primary_eligible=False,
            suggested_action="Read today",
            risk_flags=["source_health=yellow"],
        )
        _write_day(data_dir, "2026-07-06", [first])
        _write_day(data_dir, "2026-07-07", [second], source="iacr_eprint")
        payload = build_weekly_synthesis(data_dir, date(2026, 7, 6), date(2026, 7, 7))

    merged = _all_weekly_records(payload)[0]
    assert merged["seen_dates"] == ["2026-07-06", "2026-07-07"]
    assert merged["seen_sources"] == ["arxiv", "iacr_eprint"]
    assert merged["TODO_VERIFY_flags"] == ["venue"]
    assert merged["recommendation_risk_flags"] == ["source_health=yellow"]
    assert len(merged["_weekly_occurrences"]) == 2
    assert merged["primary_today_new_eligible"] is True


def test_primary_new_freshness_safety_and_top_selection() -> None:
    fresh = _record("Fresh primary", recommendation_score=80)
    stale = _record(
        "Stale high score",
        freshness_bucket="backfill",
        primary_eligible=False,
        recommendation_level="Backfill",
        recommendation_score=100,
        research_value_score=100,
        suggested_action="Read today",
    )
    payload = _build([fresh, stale])
    routed = _route_weekly_records(payload)
    markdown = render_markdown(payload)

    assert [item["title"] for item in routed["primary_new"]] == ["Fresh primary"]
    top_section = markdown.split("## Primary Today/New", 1)[0]
    assert "Fresh primary" in top_section
    assert "Stale high score" not in top_section


def test_backfill_is_separate_and_never_gets_read_today_display() -> None:
    payload = _build(
        [
            _record(
                "Valuable backfill",
                freshness_bucket="backfill",
                primary_eligible=False,
                recommendation_level="Backfill",
                research_value_score=99,
                suggested_action="Read today",
            )
        ]
    )
    markdown = render_markdown(payload)
    backfill_section = markdown.split("## High-Value Backfill / Older", 1)[1].split("## TODO_VERIFY", 1)[0]

    assert "Valuable backfill" in backfill_section
    assert "Save for background" in backfill_section
    assert "Suggested action: **Read today**" not in backfill_section


def test_todo_verify_routes_to_verify_first_and_not_read_now() -> None:
    payload = _build(
        [
            _record(
                "Ambiguous venue paper",
                recommendation_level="TODO_VERIFY",
                todo_flags=["venue_status"],
                venue_status="TODO_VERIFY",
            )
        ]
    )
    routed = _route_weekly_records(payload)
    markdown = render_markdown(payload)

    assert [item["title"] for item in routed["verify_first"]] == ["Ambiguous venue paper"]
    assert "Verify source first" in markdown
    assert "### read now\n\n- None." in markdown


def test_topic_distribution_uses_user_aligned_axis() -> None:
    markdown = render_markdown(
        _build(
            [
                _record(
                    "AI-assisted lattice attack",
                    user_tags=["AI4LC", "Sparse LWE", "BKZ"],
                )
            ]
        )
    )

    assert "- AI4LC: 1" in markdown
    assert "- lattice cryptanalysis / BKZ / G6K / sparse LWE:" in markdown


def test_venue_ccf_summary_is_conservative() -> None:
    payload = _build(
        [
            _record("Trusted A", venue="CRYPTO", venue_type="conference", ccf_rank="A"),
            _record(
                "Unknown journal",
                source="crossref",
                venue="Cybersecurity",
                venue_type="journal",
                ccf_rank="unknown",
                venue_status="TODO_VERIFY",
            ),
        ]
    )
    markdown = render_markdown(payload)

    assert "'A': 1" in markdown
    assert "'unknown': 1" in markdown
    assert "No rank is inferred from Crossref, DBLP, OpenAlex, Semantic Scholar" in markdown


def test_source_health_summary_and_red_source_verify_first() -> None:
    payload = _build([_record("Source-risk paper")], health_status="red")
    routed = _route_weekly_records(payload)
    markdown = render_markdown(payload)

    assert routed["verify_first"]
    assert "source_health=red:arxiv" in markdown
    assert "Weekly confidence: **low**" in markdown


def test_reading_queue_categories_are_rendered_read_only() -> None:
    payload = _build(
        [
            _record(
                "Module-SIS chameleon hash",
                user_tags=["Module-SIS", "chameleon hash", "project idea", "implementation"],
            )
        ]
    )
    markdown = render_markdown(payload)

    for category in (
        "read now",
        "skim",
        "save for background",
        "verify first",
        "Obsidian queue",
        "blog candidate",
        "PhD/PI email candidate",
        "project idea candidate",
    ):
        assert f"### {category}" in markdown


def test_missing_daily_artifacts_create_partial_week_without_failure() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        _write_day(data_dir, "2026-07-06", [_record("Partial week paper")])
        payload = build_weekly_synthesis(data_dir, date(2026, 7, 6), date(2026, 7, 8))

    assert payload["coverage"]["missing_days"] == ["2026-07-07", "2026-07-08"]
    assert "source-starved partial coverage" in render_markdown(payload)


def test_low_signal_week_renders_useful_guidance() -> None:
    payload = _build(
        [
            _record(
                "Background only",
                freshness_bucket="backfill",
                primary_eligible=False,
                recommendation_level="Backfill",
                suggested_action="Save",
            )
        ]
    )
    markdown = render_markdown(payload)

    assert "Low-signal week" in markdown
    assert "无安全 primary-new" in markdown


def test_source_starved_empty_week_does_not_claim_no_papers_exist() -> None:
    payload = _build([], health_status="red")
    markdown = render_markdown(payload)

    assert "Source-starved week" in markdown
    assert "do not infer that no relevant papers exist" in markdown


def test_generated_translated_markers_remain_visible() -> None:
    markdown = render_markdown(_build([_record("Bilingual record")]))

    assert "Generated/translated markers" in markdown
    assert "abstract_zh: generated/translated marker preserved" in markdown
    assert "[generated/translated] 中文摘要" in markdown


def test_rendering_is_deterministic_and_does_not_mutate_payload() -> None:
    payload = _build([_record("Deterministic weekly record")])
    before = copy.deepcopy(payload)

    assert render_markdown(payload) == render_markdown(payload)
    assert payload == before


def test_serialized_json_schema_stays_v1_and_strips_private_context() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        payload = _build([_record("Schema-safe weekly record")])
        json_path, _ = write_weekly_outputs(payload, root / "data", root / "digests")
        serialized = json_path.read_text(encoding="utf-8")
        loaded = json.loads(serialized)

    assert loaded["schema_version"] == 1
    assert "_weekly_" not in serialized
    assert set(loaded) == set(payload)


def test_daily_markdown_renderer_remains_compatible() -> None:
    record = make_paper_record(
        title="ML-KEM implementation note",
        abstract="ML-KEM constant-time implementation analysis.",
        source="arxiv",
        source_url="https://example.org/ml-kem",
        relevance_label="A",
        relevance_score=90,
    )

    markdown = generate_markdown([record], date(2026, 7, 6))

    assert "## 1. 今日核心结论" in markdown
    assert "## 2. 高优先级论文" in markdown


def test_weekly_generation_uses_files_only_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr("socket.create_connection", fail_network)
    payload = _build([_record("Offline weekly synthesis")])

    assert payload["coverage"]["unique_records"] == 1
