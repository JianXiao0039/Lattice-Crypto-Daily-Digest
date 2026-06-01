from __future__ import annotations

import json
from pathlib import Path

from lattice_digest.digest_sections import (
    HIGH_PRIORITY,
    IDEA_BANK_CANDIDATES,
    PAPER_PLAN_CANDIDATES,
    assign_report_buckets,
    assign_research_sections,
)
from lattice_digest.models import make_paper_record


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "section_golden_cases.json"
REPORT_BUCKETS = {HIGH_PRIORITY, IDEA_BANK_CANDIDATES, PAPER_PLAN_CANDIDATES}


def _load_cases() -> list[dict[str, object]]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _record(case: dict[str, object]):
    keywords = [str(item) for item in case.get("keywords", [])] if isinstance(case.get("keywords"), list) else []
    return make_paper_record(
        title=str(case["title"]),
        abstract=str(case.get("abstract") or ""),
        source=str(case.get("source") or "golden"),
        source_url=f"https://example.org/golden/{case['id']}",
        relevance_label=str(case.get("relevance_label") or "A"),
        relevance_score=int(case.get("relevance_score") or 85),
        keywords_matched=keywords,
        taxonomy_tags=[],
    )


def test_section_golden_cases() -> None:
    for case in _load_cases():
        record = _record(case)

        sections = assign_research_sections(record)
        buckets = assign_report_buckets(record)

        for expected in case.get("expected_sections", []):
            assert expected in sections, f"{case['id']} missing expected section {expected}; got {sections}"

        for forbidden in case.get("forbidden_sections", []):
            assert forbidden not in sections, f"{case['id']} should not include section {forbidden}; got {sections}"

        for expected_bucket in case.get("expected_report_buckets", []):
            assert expected_bucket in buckets, f"{case['id']} missing expected bucket {expected_bucket}; got {buckets}"

        assert not (set(sections) & REPORT_BUCKETS), f"{case['id']} leaked report bucket into research_sections: {sections}"


def test_golden_fixture_ids_are_unique() -> None:
    cases = _load_cases()
    ids = [case["id"] for case in cases]

    assert len(ids) == len(set(ids))


def test_golden_fixture_has_false_and_true_positive_coverage() -> None:
    ids = {str(case["id"]) for case in _load_cases()}

    assert "false_positive_falcon_x_time_series" in ids
    assert "false_positive_anonymous_two_party_gbdt" in ids
    assert "true_positive_transformer_for_lwe" in ids
    assert "true_positive_falcon_signature_implementation" in ids
