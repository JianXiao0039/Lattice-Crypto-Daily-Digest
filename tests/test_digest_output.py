from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.digest import (
    generate_markdown,
    priority_label,
    reading_priority_score,
    reason_for_priority,
    research_tags,
)
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
    assert isinstance(payload["records"][0]["reading_priority_score"], int)
    assert payload["records"][0]["priority_label"] in {"必须精读", "建议精读", "可略读", "暂存", "低相关"}
    assert payload["records"][0]["reason_for_priority"]
    assert payload["records"][0]["why_it_matters"]
    assert payload["records"][0]["suggested_action"] in {
        "Read today",
        "Read this week",
        "Skim for related work",
        "Save for background",
        "Ignore unless needed",
    }
    assert payload["records"][0]["source_health_ref"] == "arxiv"


def test_transformer_lwe_priority_beats_plain_pqc_survey() -> None:
    transformer_lwe = make_paper_record(
        title="Transformer LWE coordinate selection for hybrid attacks",
        abstract="AI-assisted lattice cryptanalysis with Swin-guided candidate ranking for LWE.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.10001",
        relevance_label="B",
        relevance_score=68,
    )
    plain_survey = make_paper_record(
        title="A survey of post-quantum cryptography migration",
        abstract="The paper surveys broad PQC standardization and deployment issues.",
        source="crossref",
        source_url="https://doi.org/10.0000/pqc-survey",
        relevance_label="B",
        relevance_score=72,
    )

    assert reading_priority_score(transformer_lwe) > reading_priority_score(plain_survey)
    assert priority_label(transformer_lwe) in {"必须精读", "建议精读"}
    assert priority_label(plain_survey) in {"暂存", "低相关"}


def test_bkz_lwe_attack_is_recommended_or_higher() -> None:
    record = make_paper_record(
        title="BKZ cost models for LWE primal and dual attacks",
        abstract="We study lattice reduction, G6K, fplll, primal attack and hybrid attack for LWE.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2600/101",
        relevance_label="B",
        relevance_score=66,
    )

    assert priority_label(record) in {"必须精读", "建议精读"}


def test_module_sis_chameleon_hash_is_at_least_skimmable() -> None:
    record = make_paper_record(
        title="Module-SIS chameleon hash commitments from lattices",
        abstract="The construction uses Module-SIS commitments and rejection sampling.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2600/102",
        relevance_label="C",
        relevance_score=45,
    )

    assert reading_priority_score(record) >= 50
    assert priority_label(record) in {"必须精读", "建议精读", "可略读"}


def test_lwe_application_without_attack_context_is_not_must_read() -> None:
    record = make_paper_record(
        title="Practical anonymous two-party gradient boosting decision tree",
        abstract=(
            "The protocol uses homomorphic encryption from ring learning with errors "
            "and dual circuit PSI for secure analytics."
        ),
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.30001",
        taxonomy_tags=["D01_FHE", "lwe_sis_ntru_foundations"],
        relevance_label="A",
        relevance_score=100,
    )

    assert reading_priority_score(record) < 70
    assert priority_label(record) == "可略读"


def test_fhe_application_is_not_must_read() -> None:
    record = make_paper_record(
        title="Private analytics with CKKS homomorphic encryption",
        abstract="We use CKKS and homomorphic encryption for healthcare inference and database analytics.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.30002",
        relevance_label="A",
        relevance_score=92,
    )

    assert reading_priority_score(record) < 85
    assert priority_label(record) != "必须精读"
    assert "FHE 应用论文" in reason_for_priority(record)


def test_generic_pqc_survey_is_not_must_read() -> None:
    record = make_paper_record(
        title="An overview of post-quantum cryptography migration",
        abstract="A generic PQC survey about deployment, standardization and migration.",
        source="crossref",
        source_url="https://doi.org/10.0000/generic-pqc",
        relevance_label="A",
        relevance_score=90,
    )

    assert reading_priority_score(record) <= 60
    assert priority_label(record) != "必须精读"


def test_generic_transformer_ml_without_crypto_context_is_not_high_priority() -> None:
    record = make_paper_record(
        title="Transformer models for traffic forecasting",
        abstract="A generic transformer machine learning method for time series prediction.",
        source="crossref",
        source_url="https://doi.org/10.0000/generic-transformer",
        relevance_label="B",
        relevance_score=80,
    )

    assert reading_priority_score(record) < 50
    assert priority_label(record) in {"暂存", "低相关"}


def test_implementation_audit_needs_lattice_scheme_security_consequence() -> None:
    generic_audit = make_paper_record(
        title="Auditing production cryptographic software",
        abstract="We audit implementation quality for generic cryptographic libraries without PQC schemes.",
        source="crossref",
        source_url="https://doi.org/10.0000/generic-audit",
        relevance_label="A",
        relevance_score=88,
    )
    scheme_audit = make_paper_record(
        title="Auditing reduction placement in production ML-DSA implementations",
        abstract="The audit finds ML-DSA and Dilithium implementation security consequences and production vulnerabilities.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2600/301",
        relevance_label="A",
        relevance_score=92,
    )

    assert priority_label(generic_audit) not in {"必须精读", "建议精读"}
    assert priority_label(scheme_audit) in {"必须精读", "建议精读"}
    assert reading_priority_score(scheme_audit) > reading_priority_score(generic_audit)


def test_unrelated_record_is_low_priority() -> None:
    record = make_paper_record(
        title="Graph neural networks for traffic prediction",
        abstract="A transportation benchmark without cryptographic or lattice cryptanalysis context.",
        source="crossref",
        source_url="https://doi.org/10.0000/traffic",
        relevance_label="D",
        relevance_score=12,
    )

    assert reading_priority_score(record) <= 29
    assert priority_label(record) == "低相关"


def test_markdown_high_priority_section_sorts_by_reading_priority_score() -> None:
    transformer = make_paper_record(
        title="Transformer LWE hybrid attack ranking",
        abstract="AI-assisted lattice cryptanalysis for LWE with coordinate selection and hybrid attack.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.20001",
        relevance_label="A",
        relevance_score=82,
    )
    module_sis = make_paper_record(
        title="Module-SIS chameleon hash commitments",
        abstract="Module-SIS commitment and chameleon hash constructions with rejection sampling.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2600/202",
        relevance_label="A",
        relevance_score=76,
    )
    kyber = make_paper_record(
        title="Kyber implementation side-channel analysis",
        abstract="ML-KEM and Kyber implementation security against side-channel and fault attacks.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.20003",
        relevance_label="A",
        relevance_score=80,
    )

    markdown = generate_markdown([kyber, module_sis, transformer], date(2026, 5, 23))
    section_2 = markdown.split("## 3. AI4Lattice 与机器学习辅助密码分析", 1)[0].split(
        "## 2. 高优先级论文",
        1,
    )[1]

    assert section_2.index(transformer.title) < section_2.index(module_sis.title)
    assert section_2.index(module_sis.title) < section_2.index(kyber.title)


def test_tie_breaker_prefers_ai4lattice_before_generic_pqc() -> None:
    ai_record = make_paper_record(
        title="Neural lattice reduction for LWE attack ranking",
        abstract="AI-assisted lattice cryptanalysis with neural lattice reduction for LWE attacks.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.40001",
        relevance_label="B",
        relevance_score=70,
    )
    pqc_record = make_paper_record(
        title="Post-quantum cryptography deployment notes",
        abstract="PQC standardization and deployment notes for general security teams.",
        source="crossref",
        source_url="https://doi.org/10.0000/pqc-notes",
        relevance_label="A",
        relevance_score=95,
    )

    markdown = generate_markdown([pqc_record, ai_record], date(2026, 5, 23))
    section_2 = markdown.split("## 3. AI4Lattice 与机器学习辅助密码分析", 1)[0].split(
        "## 2. 高优先级论文",
        1,
    )[1]

    assert ai_record.title in section_2
    assert pqc_record.title not in section_2


def test_papers_db_exists_and_is_not_deleted() -> None:
    db_path = Path(__file__).resolve().parents[1] / "papers.db"

    assert db_path.exists()
    assert db_path.is_file()
