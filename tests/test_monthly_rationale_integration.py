from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.monthly_synthesis import build_monthly_synthesis, render_markdown


def _write_day(data_dir: Path, day: str, records: list[dict[str, object]]) -> None:
    payload = {"metadata": {"target_date": day}, "records": records, "source_health": []}
    (data_dir / f"{day}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_monthly_core_papers_include_recommendation_rationale() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        data_dir.mkdir()
        _write_day(
            data_dir,
            "2026-06-01",
            [
                {
                    "title": "Hybrid attacks against MLWE-based ML-KEM parameters",
                    "abstract": "We study MLWE security estimates. We propose a hybrid attack model with BKZ calibration.",
                    "source": "iacr_eprint",
                    "source_url": "https://eprint.iacr.org/2606/001",
                    "relevance_label": "A",
                    "relevance_score": 95,
                    "reading_priority_score": 90,
                    "keywords_matched": ["MLWE", "ML-KEM", "BKZ"],
                }
            ],
        )
        payload = build_monthly_synthesis(data_dir, "2026-06")

    rationale = payload["core_papers"][0]["rationale"]
    assert rationale["confidence"] == "abstract_supported"
    assert "abstract-derived" in rationale["evidence_basis"]
    assert "We propose a hybrid attack model" in rationale["method"]


def test_monthly_title_only_record_does_not_hallucinate_method_or_contribution() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        data_dir.mkdir()
        _write_day(
            data_dir,
            "2026-06-01",
            [
                {
                    "title": "LWE signatures without abstract",
                    "source": "openalex",
                    "source_url": "https://example.org/title-only",
                    "relevance_label": "A",
                    "relevance_score": 90,
                    "keywords_matched": ["LWE", "signature"],
                }
            ],
        )
        payload = build_monthly_synthesis(data_dir, "2026-06")
        markdown = render_markdown(payload)

    rationale = payload["core_papers"][0]["rationale"]
    assert rationale["confidence"] == "metadata_supported"
    assert "不能可靠判断具体方法" in rationale["method"]
    assert "不能可靠判断论文声称的新贡献" in rationale["contribution"]
    assert "TODO_VERIFY" in markdown


def test_monthly_rationale_requires_no_manual_annotation_fields() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        data_dir.mkdir()
        _write_day(
            data_dir,
            "2026-06-01",
            [
                {
                    "title": "ML-DSA implementation audit",
                    "abstract": "We analyze ML-DSA implementation side-channel and fault risks.",
                    "source": "arxiv",
                    "source_url": "https://example.org/ml-dsa",
                    "relevance_label": "A",
                    "relevance_score": 92,
                    "keywords_matched": ["ML-DSA", "side-channel"],
                }
            ],
        )
        payload = build_monthly_synthesis(data_dir, "2026-06")

    serialized = json.dumps(payload, ensure_ascii=False)
    assert "human_gold" not in serialized
    assert "human_review_status" not in serialized
