from __future__ import annotations

from lattice_digest.reliability_dashboard import (
    classify_empty_digest_reason,
    classify_semantic_scholar_enrichment_status,
    count_high_priority,
    count_source_statuses,
)


def test_count_source_statuses_handles_known_and_unknown_values() -> None:
    counts = count_source_statuses(
        [
            {"status": "green"},
            {"health_status": "yellow"},
            {"status": "red"},
            {"status": "mystery"},
        ]
    )

    assert counts == {"green": 1, "yellow": 1, "red": 1, "unknown": 1}


def test_count_high_priority_counts_a_and_priority_one_records() -> None:
    count = count_high_priority(
        [
            {"relevance_label": "A"},
            {"reading_priority": 1},
            {"priority_label": "建议精读"},
            {"relevance_label": "B"},
        ]
    )

    assert count == 3


def test_classify_empty_digest_reason_distinguishes_all_red_from_partial_failure() -> None:
    all_red = classify_empty_digest_reason(
        [],
        [{"status": "red"}, {"status": "red"}],
        None,
    )
    degraded = classify_empty_digest_reason(
        [],
        [{"status": "yellow"}, {"status": "yellow"}],
        None,
    )

    assert all_red == "all_red_sources"
    assert degraded == "degraded_sources_no_records"


def test_classify_semantic_scholar_status_distinguishes_rate_limit_and_success() -> None:
    daily_payload = {
        "records": [{"semantic_scholar_enrichment": {"status": "ok"}}],
        "source_health": [{"source": "semantic_scholar", "status": "yellow", "api_key_used": True}],
    }
    rate_limited = classify_semantic_scholar_enrichment_status(
        {"records": [], "source_health": [{"source": "semantic_scholar", "status": "yellow", "api_key_used": True}]},
        {
            "probes": [
                {
                    "source": "semantic_scholar",
                    "reachable": False,
                    "retryable": True,
                    "status_code": 429,
                    "error_type": "rate_limit",
                }
            ]
        },
        env={"SEMANTIC_SCHOLAR_API_KEY": "x" * 44},
    )
    success = classify_semantic_scholar_enrichment_status(
        daily_payload,
        None,
        env={"SEMANTIC_SCHOLAR_API_KEY": "x" * 44},
    )

    assert rate_limited == "rate_limit"
    assert success == "enrichment_successful"
