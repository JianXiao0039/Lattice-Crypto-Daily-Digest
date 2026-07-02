from __future__ import annotations

from datetime import date

from lattice_digest.radar_output_qa import normalize_daily_payload, render_normalized_daily_markdown


def _legacy_payload() -> dict:
    return {
        "metadata": {"target_date": "2026-07-01", "run_date": "2026-07-01", "since_window": "7d"},
        "records": [
            {
                "title": "MergeLLL: A Hierarchical Divide-and-Conquer Framework for LLL-Based Lattice Reduction",
                "authors": ["Example Author"],
                "abstract": "We study LLL-based lattice reduction.",
                "source": "arxiv",
                "source_url": "https://arxiv.org/abs/2606.25000",
                "venue": "arXiv",
                "publication_date": "2026-06-25",
                "update_date": "2026-06-25",
                "relevance_label": "A",
                "relevance_score": 100,
                "taxonomy_tags": ["lattice_reduction"],
            },
            {
                "title": "A Lightweight Post-Quantum Authentication Framework for 5G Base Station Bootstrapping",
                "authors": ["Example Author"],
                "abstract": "We study post-quantum authentication using lattice-based KEMs.",
                "source": "arxiv",
                "source_url": "https://arxiv.org/abs/2606.29000",
                "venue": "arXiv",
                "publication_date": "2026-06-29",
                "update_date": "2026-06-29",
                "relevance_label": "A",
                "relevance_score": 100,
                "taxonomy_tags": ["pqc_deployment"],
            },
            {
                "title": "Exploring Side-Channel Protections in Hardware Implementations of PQC ML-KEM Verification",
                "authors": ["Example Author"],
                "abstract": "We study side-channel protections for ML-KEM.",
                "source": "arxiv",
                "source_url": "https://arxiv.org/abs/2606.30000",
                "venue": "arXiv",
                "publication_date": "2026-06-30",
                "update_date": "2026-06-30",
                "relevance_label": "A",
                "relevance_score": 100,
                "taxonomy_tags": ["implementation_security"],
            },
        ],
        "source_health": [{"source": "arxiv", "status": "yellow"}],
        "warnings": [],
    }


def test_legacy_2026_07_01_json_is_normalized_to_freshness_and_metadata_contract() -> None:
    normalized = normalize_daily_payload(_legacy_payload(), date(2026, 7, 1))
    records = normalized["records"]

    assert normalized["metadata"]["legacy_daily_output_normalized"] is True
    assert len(records) == 3
    for item in records:
        for field in (
            "selected_date_basis",
            "freshness_bucket",
            "freshness_reason",
            "primary_today_new_eligible",
            "venue_type",
            "CCF_rank",
            "abstract_en",
            "abstract_zh",
            "conclusion_en",
            "conclusion_zh",
            "recommendation_level",
            "recommendation_score",
            "recommendation_reason",
            "TODO_VERIFY_flags",
        ):
            assert field in item
        assert item["abstract_zh"].startswith("model-generated zh summary:")
        assert item["conclusion_zh"].startswith("model-generated zh summary:")
        assert item["CCF_rank"] == "N/A"

    stale = [item for item in records if item["publication_date"] in {"2026-06-25", "2026-06-29"}]
    assert stale
    assert all(item["primary_today_new_eligible"] is False for item in stale)
    assert all(item["freshness_bucket"] == "backfill" for item in stale)
    assert all(item["recommendation_level"] == "Backfill" for item in stale)


def test_legacy_2026_07_01_markdown_routes_stale_high_score_items_out_of_primary() -> None:
    markdown = render_normalized_daily_markdown(_legacy_payload(), date(2026, 7, 1))

    assert "## 2. 高优先级论文\n\n今日无高优先级论文。" not in markdown
    high_priority_section = markdown.split("## 2. 高优先级论文", 1)[1].split("## 2b.", 1)[0]
    assert "MergeLLL" not in high_priority_section
    assert "Lightweight Post-Quantum" not in high_priority_section
    assert "Exploring Side-Channel" in high_priority_section
    routed_section = markdown.split("## 2b. 回填 / 较早 / 待核验项目", 1)[1]
    assert "MergeLLL" in routed_section
    assert "Lightweight Post-Quantum" in routed_section
    assert "freshness_bucket：backfill" in routed_section


def test_legacy_missing_dates_route_to_todo_verify_and_non_primary() -> None:
    payload = _legacy_payload()
    payload["records"] = [
        {
            "title": "Cybersecurity journal lattice note",
            "authors": [],
            "abstract": "",
            "source": "crossref",
            "source_url": "https://example.test/cybersecurity",
            "venue": "Cybersecurity",
            "relevance_label": "C",
            "relevance_score": 50,
        },
        {
            "title": "ACM CCS lattice deployment paper",
            "authors": [],
            "abstract": "Lattice-based deployment study.",
            "source": "crossref",
            "source_url": "https://example.test/ccs",
            "venue": "ACM CCS",
            "publication_date": "2026-07-01",
            "relevance_label": "B",
            "relevance_score": 75,
        },
        {
            "title": "PKC lattice protocol paper",
            "authors": [],
            "abstract": "Lattice-based protocol study.",
            "source": "crossref",
            "source_url": "https://example.test/pkc",
            "venue": "PKC",
            "publication_date": "2026-07-01",
            "relevance_label": "B",
            "relevance_score": 75,
        },
    ]

    records = normalize_daily_payload(payload, date(2026, 7, 1))["records"]
    cybersecurity = records[0]
    ccs = records[1]
    pkc = records[2]

    assert cybersecurity["primary_today_new_eligible"] is False
    assert cybersecurity["freshness_bucket"] == "date_uncertain_todo_verify"
    assert cybersecurity["CCF_rank"] == "TODO_VERIFY"
    assert "venue" in cybersecurity["TODO_VERIFY_flags"]
    assert "abstract_en" in cybersecurity["TODO_VERIFY_flags"]
    assert ccs["CCF_rank"] == "A"
    assert pkc["CCF_rank"] == "B"
