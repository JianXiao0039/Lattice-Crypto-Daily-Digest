from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.digest import generate_markdown, research_tags
from lattice_digest.models import make_paper_record
from lattice_digest.storage import write_json


EXPECTED_SECTIONS = [
    "## 1. 今日核心结论",
    "## 2. 高优先级论文",
    "## 3. AI4Lattice 与机器学习辅助密码分析",
    "## 4. 格基约简与经典攻击",
    "## 5. PQC 标准、原语与实现",
    "## 6. 阅读队列与精读建议",
    "## 7. 可孵化研究 idea 与导师讨论问题",
    "## 8. 数据源健康与空报告处理",
]


def _source_health() -> list[dict[str, object]]:
    return [
        {
            "source": "iacr_eprint",
            "raw_candidates": 2,
            "normalized_candidates": 2,
            "date_filtered_candidates": 2,
            "deduped_candidates": 1,
            "relevance_filtered_candidates": 1,
            "scoring_threshold_candidates": 1,
            "final_records": 1,
            "warnings": [],
            "errors": [],
        }
    ]


def test_empty_digest_generates_intelligence_report_sections() -> None:
    markdown = generate_markdown([], date(2026, 5, 23), filtered_count=0, source_health=_source_health())

    for section in EXPECTED_SECTIONS:
        assert section in markdown
    assert "今日没有通过筛选的论文" in markdown
    assert "今日未发现值得记录的格密码相关新论文" in markdown
    assert "绿色：正常" in markdown
    assert "python -m lattice_digest.run --since 7d --output markdown,json --send none" in markdown


def test_ai4lattice_record_enters_ai4lattice_section() -> None:
    record = make_paper_record(
        title="Swin Transformer for LWE coordinate selection",
        abstract="We study AI-assisted lattice cryptanalysis and neural ranking for BKZ hybrid attacks.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.00001",
        relevance_label="A",
        relevance_score=91,
        reading_priority=1,
        keywords_matched=["LWE", "BKZ", "AI-assisted lattice cryptanalysis"],
    )

    markdown = generate_markdown([record], date(2026, 5, 23), source_health=_source_health())

    assert "## 3. AI4Lattice 与机器学习辅助密码分析" in markdown
    assert "Swin Transformer for LWE coordinate selection" in markdown
    assert "模型角色：" in markdown
    assert "toy-only" in markdown
    assert "AI4Lattice" in research_tags(record)


def test_lattice_keywords_generate_research_tags() -> None:
    record = make_paper_record(
        title="Module-SIS and MLWE estimates for ML-KEM and ML-DSA with BKZ",
        abstract="The paper studies LWE, Module-LWE, Module-SIS, Kyber, Dilithium and lattice reduction.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2600/001",
        relevance_label="A",
        relevance_score=95,
    )

    tags = set(research_tags(record))

    assert {"LWE", "MLWE", "Module-SIS", "ML-KEM", "ML-DSA", "Lattice Reduction"} <= tags


def test_json_output_contains_source_health_and_intelligence_fields() -> None:
    record = make_paper_record(
        title="Improved MLWE security estimates for ML-KEM",
        abstract="We analyze LWE, MLWE, Kyber and primal attack costs.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.00002",
        relevance_label="A",
        relevance_score=90,
        publication_date="2026-05-23",
    )
    with TemporaryDirectory() as tmp:
        path = write_json([record], Path(tmp), date(2026, 5, 23), _source_health(), ["warning"], "7d")
        payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["metadata"]["run_date"] == "2026-05-23"
    assert payload["metadata"]["since_window"] == "7d"
    assert payload["source_health"][0]["source"] == "iacr_eprint"
    assert "MLWE" in payload["records"][0]["research_tags"]
    assert payload["records"][0]["why_it_matters"]
    assert payload["records"][0]["suggested_action"] == "Read immediately"
    assert payload["records"][0]["source_health_ref"] == "arxiv"


def test_papers_db_exists_and_is_not_deleted() -> None:
    db_path = Path(__file__).resolve().parents[1] / "papers.db"

    assert db_path.exists()
    assert db_path.is_file()
