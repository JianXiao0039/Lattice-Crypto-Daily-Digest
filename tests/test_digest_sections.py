from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.digest import generate_markdown
from lattice_digest.digest_sections import (
    AI_LATTICE,
    HIGH_PRIORITY,
    IDEA_BANK_CANDIDATES,
    IMPLEMENTATION_SYSTEMS,
    LATTICE_REDUCTION_ATTACKS,
    LWE_FAMILY,
    PAPER_PLAN_CANDIDATES,
    PQC_STANDARDS,
    SIS_NTRU_COMMITMENTS,
    assign_research_sections,
    is_idea_bank_candidate,
    is_paper_plan_candidate,
)
from lattice_digest.models import make_paper_record
from lattice_digest.storage import write_json


def _record(title: str, abstract: str, score: int = 85, label: str = "A"):
    return make_paper_record(
        title=title,
        abstract=abstract,
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.88001",
        relevance_label=label,
        relevance_score=score,
        keywords_matched=[],
        taxonomy_tags=[],
    )


def test_section_assignment_for_lwe_rlwe_mlwe() -> None:
    record = _record("Module-LWE attack estimates", "The work studies RLWE, MLWE and sparse LWE.")

    sections = assign_research_sections(record)

    assert LWE_FAMILY in sections
    assert HIGH_PRIORITY in sections


def test_section_assignment_for_sis_ntru_commitment_chameleon_hash() -> None:
    record = _record(
        "Module-SIS chameleon hash commitments",
        "The construction relates SIS, NTRU and commitment interfaces.",
    )

    sections = assign_research_sections(record)

    assert SIS_NTRU_COMMITMENTS in sections


def test_section_assignment_for_bkz_lll_g6k_lattice_attacks() -> None:
    record = _record(
        "BKZ and G6K baselines for LWE attacks",
        "We compare LLL, fplll, lattice reduction and hybrid attack costs.",
    )

    sections = assign_research_sections(record)

    assert LATTICE_REDUCTION_ATTACKS in sections


def test_section_assignment_for_ml_kem_ml_dsa_falcon() -> None:
    record = _record(
        "ML-KEM and ML-DSA implementation security",
        "The paper discusses Kyber, Dilithium and Falcon in NIST PQC.",
    )

    sections = assign_research_sections(record)

    assert PQC_STANDARDS in sections


def test_section_assignment_for_ai_assisted_lattice_cryptanalysis() -> None:
    record = _record(
        "Transformer LWE coordinate selection",
        "AI-assisted lattice cryptanalysis for BKZ hybrid attacks.",
    )

    sections = assign_research_sections(record)

    assert AI_LATTICE in sections


def test_json_records_contain_research_sections() -> None:
    record = _record("BKZ for MLWE attacks", "LWE, MLWE, BKZ and lattice reduction.")
    with TemporaryDirectory() as tmp:
        path = write_json([record], Path(tmp), date(2026, 5, 31))
        payload = json.loads(path.read_text(encoding="utf-8"))

    sections = payload["records"][0]["research_sections"]
    assert LWE_FAMILY in sections
    assert LATTICE_REDUCTION_ATTACKS in sections


def test_markdown_contains_expected_research_section_headers() -> None:
    record = _record("Transformer LWE ranking", "AI-assisted lattice cryptanalysis for LWE.")
    markdown = generate_markdown([record], date(2026, 5, 31), metadata={"target_date": "2026-05-31"})

    assert "### Research-Oriented Sections" in markdown
    assert f"#### {HIGH_PRIORITY}" in markdown
    assert f"#### {AI_LATTICE}" in markdown
    assert "### Source Health Summary" in markdown
    assert "audits/source-health/2026-05-31.json" in markdown


def test_research_sections_do_not_change_ranking_score_or_label() -> None:
    record = _record("ML-KEM side-channel analysis", "Kyber implementation fault attack.", score=76, label="B")

    before = (record.relevance_score, record.relevance_label)
    _ = assign_research_sections(record)
    after = (record.relevance_score, record.relevance_label)

    assert after == before


def test_idea_bank_candidate_criteria_are_deterministic() -> None:
    record = _record("BKZ for LWE hybrid attacks", "G6K and fplll cost model.", score=70, label="B")

    assert is_idea_bank_candidate(record) is True
    assert is_idea_bank_candidate(record) is True
    assert IDEA_BANK_CANDIDATES in assign_research_sections(record)


def test_paper_plan_candidate_criteria_are_deterministic() -> None:
    positive = _record(
        "Module-SIS chameleon hash commitments",
        "SIS commitment and chameleon hash construction.",
        score=82,
        label="A",
    )
    weak = _record("Generic PQC migration survey", "Overview of post-quantum deployment.", score=60, label="B")

    assert is_paper_plan_candidate(positive) is True
    assert is_paper_plan_candidate(positive) is True
    assert PAPER_PLAN_CANDIDATES in assign_research_sections(positive)
    assert is_paper_plan_candidate(weak) is False
    assert IMPLEMENTATION_SYSTEMS not in assign_research_sections(weak)
