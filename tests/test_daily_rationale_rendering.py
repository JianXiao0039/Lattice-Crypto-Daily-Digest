from __future__ import annotations

from datetime import date

from lattice_digest.digest import generate_markdown, reading_priority_score
from lattice_digest.models import make_paper_record


def test_daily_markdown_includes_rationale_fields_for_abstract_rich_paper() -> None:
    record = make_paper_record(
        title="Hybrid attacks against MLWE-based ML-KEM parameters",
        abstract=(
            "We study the problem of estimating the security of MLWE instances used in ML-KEM. "
            "We propose a hybrid attack model that combines lattice reduction, coordinate guessing, and BKZ cost calibration. "
            "Our results improve the explanation of parameter margins for post-quantum deployment."
        ),
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2606/001",
        relevance_label="A",
        relevance_score=95,
        keywords_matched=["MLWE", "ML-KEM", "BKZ"],
    )

    markdown = generate_markdown([record], date(2026, 6, 18))

    assert "- Recommendation rationale:" in markdown
    assert "Paper problem:" in markdown
    assert "Method / construction / attack / implementation:" in markdown
    assert "Main contribution:" in markdown
    assert "Radar relevance:" in markdown
    assert "Why read / skim / track / ignore:" in markdown
    assert "Evidence basis: abstract-derived" in markdown
    assert "We propose a hybrid attack model" in markdown


def test_daily_markdown_does_not_hallucinate_for_title_only_paper() -> None:
    record = make_paper_record(
        title="LWE signatures without abstract",
        abstract="",
        source="openalex",
        source_url="https://example.org/title-only",
        relevance_label="A",
        relevance_score=90,
        keywords_matched=["LWE", "signature"],
    )

    markdown = generate_markdown([record], date(2026, 6, 18))

    assert "Evidence basis: metadata-derived" in markdown
    assert "仅有标题/关键词，不能可靠判断具体方法、构造、攻击或系统" in markdown
    assert "仅有标题/关键词，不能可靠判断论文声称的新贡献" in markdown
    assert "TODO_VERIFY" in markdown
    assert "the conclusion says" not in markdown.lower()


def test_daily_rationale_preserves_order_scores_labels_and_priority() -> None:
    first = make_paper_record(
        title="Transformer LWE hybrid attack ranking",
        abstract="AI-assisted lattice cryptanalysis for LWE with coordinate selection and hybrid attack.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2606.00001",
        relevance_label="A",
        relevance_score=82,
    )
    second = make_paper_record(
        title="Module-SIS chameleon hash commitments",
        abstract="Module-SIS commitment and chameleon hash constructions with rejection sampling.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2606/002",
        relevance_label="A",
        relevance_score=76,
    )
    before = [
        (record.title, record.relevance_label, record.relevance_score, reading_priority_score(record))
        for record in (first, second)
    ]

    markdown = generate_markdown([second, first], date(2026, 6, 18))

    after = [
        (record.title, record.relevance_label, record.relevance_score, reading_priority_score(record))
        for record in (first, second)
    ]
    assert before == after
    section_2 = markdown.split("## 3. AI4Lattice 与机器学习辅助密码分析", 1)[0].split("## 2. 高优先级论文", 1)[1]
    assert section_2.index(first.title) < section_2.index(second.title)
