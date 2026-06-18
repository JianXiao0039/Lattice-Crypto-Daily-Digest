from __future__ import annotations

from pathlib import Path

from lattice_digest.recommendation_rationale import build_recommendation_rationale


ROOT = Path(__file__).resolve().parents[1]


def test_rationale_integration_does_not_require_manual_annotation_fields() -> None:
    rationale = build_recommendation_rationale(
        {
            "title": "ML-KEM side-channel implementation audit",
            "abstract": "We analyze ML-KEM implementation side-channel and fault attack risks.",
            "source": "iacr_eprint",
            "keywords_matched": ["ML-KEM", "side-channel"],
        }
    ).to_dict()

    assert "human_gold_label" not in rationale
    assert "human_review_status" not in rationale


def test_rationale_helper_is_not_imported_by_fetchers_ranker_or_taxonomy() -> None:
    checked = [
        ROOT / "src" / "lattice_digest" / "ranker.py",
        ROOT / "src" / "lattice_digest" / "digest_sections.py",
        ROOT / "src" / "lattice_digest" / "library_taxonomy.py",
    ]
    checked.extend((ROOT / "src" / "lattice_digest" / "sources").glob("*.py"))

    for path in checked:
        text = path.read_text(encoding="utf-8")
        assert "recommendation_rationale" not in text, str(path)


def test_rationale_integration_does_not_reference_private_or_artifact_paths() -> None:
    for relative in [
        "src/lattice_digest/recommendation_rationale.py",
        "src/lattice_digest/digest.py",
        "src/lattice_digest/weekly_synthesis.py",
    ]:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "PhD_Application" not in text
        assert "ResearchArtifacts" not in text
