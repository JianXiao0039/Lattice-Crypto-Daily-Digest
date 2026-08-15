from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from lattice_digest.config import load_config_bundle
from lattice_digest.digest import generate_markdown
from lattice_digest.models import make_paper_record
from lattice_digest.radar_freshness import enrich_record_for_daily_radar
from lattice_digest.ranker import classify_record
from lattice_digest.run import _filter_records_to_coverage
from lattice_digest.sources.base import FetchContext
from lattice_digest.sources.openalex import OpenAlexSource


RUN_DATE = date(2026, 8, 15)
COVERAGE_END = datetime(2026, 8, 15, 10, tzinfo=timezone.utc)
COVERAGE_START = COVERAGE_END - timedelta(hours=36)


def _paper(**overrides: object):
    data = {
        "title": "LWE and lattice reduction",
        "abstract": "We study LWE cryptanalysis with lattice reduction and BKZ.",
        "source": "openalex",
        "source_url": "https://example.test/paper",
        "publication_date": "2026-08-15",
        "relevance_label": "A",
        "relevance_score": 95,
    }
    data.update(overrides)
    return make_paper_record(**data)


@pytest.mark.parametrize(
    ("year", "title"),
    [
        ("2004-11-01", "New lattice-based cryptographic constructions"),
        ("2009-01-01", "Public-Key Cryptosystems from the Worst-Case Shortest Vector Problem"),
        ("2010-01-01", "On Ideal Lattices and Learning with Errors over Rings"),
        ("2011-01-01", "Fully Homomorphic Encryption from Ring-LWE"),
        ("2013-01-01", "Homomorphic Encryption from Learning with Errors"),
        ("2014-07-01", "Fully Homomorphic Encryption without Bootstrapping"),
        ("2015-10-01", "On the concrete hardness of Learning with Errors"),
        ("2016-01-01", "A Decade of Lattice Cryptography"),
        ("2018-02-14", "CRYSTALS-Dilithium"),
    ],
)
def test_openalex_index_update_cannot_make_cold_classic_primary(year: str, title: str) -> None:
    record = _paper(
        title=title,
        publication_date=year,
        update_date="2026-08-15",
        update_date_kind="INDEX_METADATA_UPDATE_DATE",
    )
    enriched = enrich_record_for_daily_radar(
        record,
        RUN_DATE,
        coverage_start=COVERAGE_START,
        coverage_end=COVERAGE_END,
    )
    kept, dropped = _filter_records_to_coverage(
        [record], COVERAGE_START, COVERAGE_END, digest_date=RUN_DATE, include_backfill=False
    )
    assert enriched.primary_today_new_eligible is False
    assert enriched.freshness_bucket == "backfill"
    assert kept == [] and dropped == 1


def test_genuine_publication_inside_36h_is_primary() -> None:
    record = _paper(publication_date="2026-08-15T08:00:00+00:00")
    enriched = enrich_record_for_daily_radar(
        record, RUN_DATE, coverage_start=COVERAGE_START, coverage_end=COVERAGE_END
    )
    assert enriched.primary_today_new_eligible is True
    assert enriched.selected_date_basis == "publication_date"


def test_exact_timestamp_before_36h_boundary_is_not_current() -> None:
    record = _paper(publication_date="2026-08-13T21:59:59+00:00")
    enriched = enrich_record_for_daily_radar(
        record, RUN_DATE, coverage_start=COVERAGE_START, coverage_end=COVERAGE_END
    )
    assert enriched.primary_today_new_eligible is False


def test_authenticated_content_revision_has_separate_nonpublication_route() -> None:
    record = _paper(
        publication_date="2020-01-01",
        update_date="2026-08-15T08:00:00+00:00",
        update_date_kind="AUTHORITATIVE_CONTENT_REVISION_DATE",
    )
    enriched = enrich_record_for_daily_radar(
        record, RUN_DATE, coverage_start=COVERAGE_START, coverage_end=COVERAGE_END
    )
    kept, _ = _filter_records_to_coverage(
        [record], COVERAGE_START, COVERAGE_END, digest_date=RUN_DATE, include_backfill=False
    )
    assert enriched.selected_date_basis == "update_date"
    assert enriched.freshness_bucket == "recent_content_revision"
    assert enriched.primary_today_new_eligible is False
    assert len(kept) == 1


def test_ordinary_newly_observed_old_item_is_not_normal_daily() -> None:
    record = _paper(publication_date="2018-01-01", first_seen_at="2026-08-15T08:00:00+00:00")
    enriched = enrich_record_for_daily_radar(
        record, RUN_DATE, coverage_start=COVERAGE_START, coverage_end=COVERAGE_END
    )
    kept, _ = _filter_records_to_coverage(
        [record], COVERAGE_START, COVERAGE_END, digest_date=RUN_DATE, include_backfill=False
    )
    assert enriched.freshness_bucket == "newly_discovered_but_older"
    assert kept == []


def test_critical_newly_observed_old_item_uses_narrow_verify_first_route() -> None:
    configs = load_config_bundle()
    record = make_paper_record(
        title="A Polynomial-Time Quantum Algorithm for the Dihedral Coset Problem",
        abstract=(
            "This Preliminary Draft claims a polynomial-time quantum algorithm for the Dihedral Coset Problem. "
            "Combined with Regev's reduction from approximate SVP and LWE to DCP, it may yield polynomial-time "
            "quantum algorithms for these lattice problems with faulty sample rate 1/O(log n)."
        ),
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2026/1591",
        publication_date="2026-08-03",
        first_seen_at="2026-08-15T08:00:00+00:00",
        venue="Preliminary Draft",
    )
    ranked = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])
    enriched = enrich_record_for_daily_radar(
        ranked, RUN_DATE, coverage_start=COVERAGE_START, coverage_end=COVERAGE_END
    )
    kept, _ = _filter_records_to_coverage(
        [ranked], COVERAGE_START, COVERAGE_END, digest_date=RUN_DATE, include_backfill=False
    )
    assert enriched.security_impact_severity == "CRITICAL"
    assert enriched.freshness_bucket == "CRITICAL_NEWLY_OBSERVED_VERIFY_FIRST"
    assert enriched.primary_today_new_eligible is False
    assert enriched.suggested_action == "READ_AND_VERIFY_IMMEDIATELY"
    assert len(kept) == 1
    markdown = generate_markdown(
        kept,
        RUN_DATE,
        source_health=[{"source": "iacr_eprint", "health_status": "green", "runtime_state": "complete"}],
        metadata={"completion_state": "complete"},
    )
    assert "CRITICAL newly-observed 安全信号" in markdown
    assert "CRITICAL newly observed verify-first count：1" in markdown


def test_backfill_remains_explicit_opt_in() -> None:
    old = _paper(publication_date="2015-01-01")
    kept, _ = _filter_records_to_coverage(
        [old], COVERAGE_START, COVERAGE_END, digest_date=RUN_DATE, include_backfill=True
    )
    assert len(kept) == 1
    assert kept[0].primary_today_new_eligible is False


def test_english_placeholder_is_not_marked_as_completed_chinese_translation() -> None:
    enriched = enrich_record_for_daily_radar(_paper(), RUN_DATE)
    assert enriched.abstract_zh.startswith("TODO_VERIFY: TODO_VERIFY_TRANSLATION: English source:")
    assert enriched.translation_fidelity_status == "TODO_VERIFY_TRANSLATION"
    assert "TODO_VERIFY_TRANSLATION" in enriched.TODO_VERIFY_flags
    assert enriched.abstract in enriched.abstract_zh


def test_empty_report_distinguishes_healthy_from_degraded_coverage() -> None:
    healthy = [{"source": "arxiv", "health_status": "green", "runtime_state": "complete"}]
    degraded = [{"source": "arxiv", "health_status": "yellow", "runtime_state": "partial"}]
    assert "最近 36 小时未发现满足当前格密码研究门槛的新论文。" in generate_markdown([], RUN_DATE, source_health=healthy)
    assert "最近 36 小时的检索覆盖不完整，当前不能据此断言没有相关新论文。" in generate_markdown([], RUN_DATE, source_health=degraded)


def test_openalex_adapter_records_index_update_semantics_without_freshness_promotion(tmp_path, monkeypatch) -> None:
    payload = {
        "results": [
            {
                "id": "https://openalex.org/W-old",
                "title": "On the concrete hardness of Learning with Errors",
                "publication_date": "2015-10-01",
                "updated_date": "2026-08-15T08:00:00Z",
                "abstract_inverted_index": {"LWE": [0], "cryptanalysis": [1]},
                "authorships": [],
                "primary_location": {},
            }
        ]
    }
    monkeypatch.setattr("lattice_digest.sources.openalex.fetch_json", lambda *args, **kwargs: payload)
    context = FetchContext(root=tmp_path, since=COVERAGE_START, dry_run=False)
    source = OpenAlexSource(
        {
            "name": "openalex",
            "type": "openalex",
            "url": "https://api.openalex.org/works",
            "query_terms": ["LWE"],
            "max_results": 5,
        }
    )
    records = source.fetch(context)
    normalized = context.normalized_candidates[0]
    assert records == []
    assert normalized["update_date_kind"] == "INDEX_METADATA_UPDATE_DATE"
    assert normalized["publication_date_kind"] == "AUTHORITATIVE_PUBLICATION_DATE"
