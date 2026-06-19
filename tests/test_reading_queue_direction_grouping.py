from __future__ import annotations

from lattice_digest.digest_sections import HIGH_PRIORITY, LATTICE_REDUCTION_ATTACKS, LWE_FAMILY, PQC_STANDARDS
from lattice_digest.reading_queue import (
    import_queue,
    render_by_reading_action,
    render_by_research_direction,
    render_todo_verify_categories,
)


def _candidate(
    title: str,
    sections: list[str],
    *,
    abstract: str,
    label: str = "A",
    score: int = 90,
    keywords: list[str] | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "abstract": abstract,
        "source": "fixture",
        "source_url": f"https://example.test/{title.lower().replace(' ', '-')}",
        "publication_date": "2026-06-20",
        "relevance_label": label,
        "relevance_score": score,
        "research_sections": sections,
        "keywords_matched": keywords or ["LWE", "BKZ"],
    }


def test_reading_queue_groups_by_reading_action_and_research_direction() -> None:
    state, _ = import_queue(
        {"records": []},
        [
            _candidate(
                "LWE hybrid attack",
                [HIGH_PRIORITY, LWE_FAMILY, LATTICE_REDUCTION_ATTACKS],
                abstract="We propose a hybrid attack and benchmark BKZ cost for LWE.",
            ),
            _candidate(
                "ML-KEM deployment audit",
                [PQC_STANDARDS],
                abstract="We study ML-KEM deployment and implementation caveats.",
                label="B",
                score=70,
                keywords=["ML-KEM", "implementation"],
            ),
        ],
        timestamp="2026-06-20T00:00:00+00:00",
    )

    by_action = render_by_reading_action(state)
    by_direction = render_by_research_direction(state)
    assert "## 精读" in by_action
    assert "LWE hybrid attack" in by_action
    assert "## lattice reduction / BKZ / cryptanalysis" in by_direction
    assert "LWE hybrid attack" in by_direction
    assert "## ML-KEM / ML-DSA / PQC implementation" in by_direction
    assert "ML-KEM deployment audit" in by_direction


def test_reading_queue_preserves_todo_verify_categories_without_manual_annotation() -> None:
    state, _ = import_queue(
        {"records": []},
        [
            _candidate(
                "Title only LWE paper",
                [LWE_FAMILY],
                abstract="",
                label="C",
                score=45,
            )
        ],
        timestamp="2026-06-20T00:00:00+00:00",
    )
    record = state["records"][0]
    rendered = render_todo_verify_categories(state)

    assert record["todo_verify_categories"]
    assert "source-health / metadata incompleteness" in record["todo_verify_categories"]
    assert "Title only LWE paper" in rendered
    serialized = repr(record)
    assert "human_gold_label" not in serialized
    assert "manual_annotation_status" not in serialized
