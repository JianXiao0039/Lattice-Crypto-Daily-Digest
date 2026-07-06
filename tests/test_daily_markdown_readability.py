from __future__ import annotations

from datetime import date

from lattice_digest.digest import generate_markdown
from lattice_digest.models import make_paper_record


def _paper(**overrides: object):
    data = {
        "title": "Sparse LWE cryptanalysis with BKZ cost models",
        "abstract": "We study sparse LWE cryptanalysis using BKZ, G6K and hybrid attacks.",
        "source": "arxiv",
        "source_url": "https://arxiv.org/abs/2607.00001",
        "venue": "arXiv",
        "publication_date": "2026-07-06",
        "relevance_label": "A",
        "relevance_score": 94,
    }
    data.update(overrides)
    return make_paper_record(**data)


def _source_health() -> list[dict[str, object]]:
    return [
        {"source": "arxiv", "status": "green", "final_records": 1},
        {"source": "dblp", "status": "yellow", "error_type": "ssl_error", "retryable": True},
        {"source": "semantic_scholar", "status": "red", "error_type": "rate_limit", "retryable": True},
    ]


def test_markdown_contains_action_first_daily_summary_and_source_health_risk() -> None:
    markdown = generate_markdown([_paper()], date(2026, 7, 6), source_health=_source_health())

    assert "### 今日读什么 / What to read today" in markdown
    assert "Daily verdict：" in markdown
    assert "Action counts：read_now=" in markdown
    assert "Top-level risk：Source health：green=1，yellow=1，red=1" in markdown
    assert "降级源：dblp、semantic_scholar" in markdown


def test_primary_item_renders_recommendation_before_audit_details() -> None:
    markdown = generate_markdown([_paper()], date(2026, 7, 6))
    primary_section = markdown.split("## 2. 高优先级论文", 1)[1].split("## 2b.", 1)[0]

    assert "Placement：primary today/new" in primary_section
    assert "#### Recommendation / Action" in primary_section
    assert "Recommendation：Strong" in primary_section
    assert "Suggested action：今日精读" in primary_section
    assert "Why it matters：" in primary_section
    assert primary_section.index("#### Recommendation / Action") < primary_section.index("#### Audit Details")


def test_no_primary_day_renders_useful_low_signal_summary() -> None:
    markdown = generate_markdown(
        [
            _paper(
                title="Private analytics with CKKS homomorphic encryption",
                abstract="The paper uses CKKS and fully homomorphic encryption for healthcare inference.",
                publication_date="2026-06-20",
                relevance_score=92,
            )
        ],
        date(2026, 7, 6),
        source_health=_source_health(),
    )

    assert "今日无 primary-new 必读" in markdown
    assert "今日没有 primary-new 高优先级论文" in markdown
    assert "backfill/older/TODO_VERIFY=1" in markdown


def test_backfill_section_is_distinct_and_does_not_use_read_today_action() -> None:
    markdown = generate_markdown(
        [_paper(publication_date="2026-06-20", relevance_score=100)],
        date(2026, 7, 6),
    )
    backfill_section = markdown.split("## 2b. 回填 / 较早 / 待核验项目", 1)[1].split("## 3.", 1)[0]

    assert "以下项目未进入 primary today/new" in backfill_section
    assert "Placement：backfill / older non-primary" in backfill_section
    assert "freshness_bucket：backfill" in backfill_section
    assert "Suggested action：暂存" in backfill_section
    assert "Read today" not in backfill_section
    assert "今日精读" not in backfill_section


def test_todo_verify_risk_generated_markers_and_venue_ccf_are_visible() -> None:
    markdown = generate_markdown(
        [
            _paper(
                title="Cybersecurity journal lattice note",
                abstract="",
                source="crossref",
                source_url="https://example.test/cybersecurity",
                venue="Cybersecurity",
                publication_date=None,
                relevance_label="C",
                relevance_score=50,
            )
        ],
        date(2026, 7, 6),
    )

    assert "Placement：TODO_VERIFY / non-primary" in markdown
    assert "Risk strip：" in markdown
    assert "missing_date_basis" in markdown
    assert "Venue / CCF：Cybersecurity；journal；CCF=TODO_VERIFY" in markdown
    assert "abstract_en：TODO_VERIFY" in markdown
    assert "abstract_zh：TODO_VERIFY:" in markdown
    assert "Generated/translated markers：abstract_zh=TODO_VERIFY" in markdown
    assert "TODO_VERIFY visible：yes" in markdown


def test_user_workflow_fields_render_without_json_schema_changes() -> None:
    markdown = generate_markdown([_paper()], date(2026, 7, 6))

    assert "#### User Workflow" in markdown
    assert "User relevance：Sparse LWE/RLWE/MLWE" in markdown
    assert "PhD / application：" in markdown
    assert "Blog / Obsidian / project hook：" in markdown
    assert "PI / advisor question：" in markdown
    assert "recommendation_score_breakdown：" in markdown
    assert "primary_action_allowed：True" in markdown


def test_markdown_rendering_is_deterministic() -> None:
    records = [_paper(), _paper(title="Module-SIS chameleon hash", abstract="Module-SIS chameleon hash trapdoor adaptation.")]

    first = generate_markdown(records, date(2026, 7, 6), source_health=_source_health())
    second = generate_markdown(records, date(2026, 7, 6), source_health=_source_health())

    assert first == second
