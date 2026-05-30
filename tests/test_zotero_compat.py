from __future__ import annotations

import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.zotero_compat import (
    build_stable_citation_key,
    build_zotero_tags,
    dedup_records_for_zotero,
    generate_zotero_export,
    infer_csl_type,
    infer_zotero_item_type,
)


SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA", ".env", "ZOTERO_KEY")


def _records() -> list[dict[str, object]]:
    return [
        {
            "title": "Transformer LWE Cryptanalysis with BKZ Hybrid Ranking",
            "authors": ["Alice A.", "Bob B."],
            "abstract": "AI-assisted lattice cryptanalysis for LWE, BKZ, G6K, fplll and hybrid attack coordinate selection.",
            "source": "arxiv",
            "url": "https://arxiv.org/abs/2605.00001",
            "arxiv_id": "2605.00001",
            "doi": "10.1000/lwe.1",
            "date": "2026-05-30",
            "reading_priority_score": 96,
            "priority_label": "必须精读",
            "reason_for_priority": "命中 Transformer LWE、BKZ、G6K、fplll 和 hybrid attack。",
            "why_it_matters": "直接服务 AI4Lattice hybrid ranking 和 LWE 攻击主线。",
        },
        {
            "title": "Module-SIS Chameleon Hash Commitment with Reproducible Parameters",
            "authors": ["Carol C."],
            "abstract": "A Module-SIS chameleon hash and lattice commitment with parameter estimation.",
            "source": "iacr_eprint",
            "url": "https://eprint.iacr.org/2026/001",
            "eprint_id": "2026/001",
            "date": "2026-05-29",
            "reading_priority_score": 84,
            "priority_label": "建议精读",
        },
        {
            "title": "Negative-Cyclic RLWE MLWE Modeling for Structured Lattice Samples",
            "authors": ["Dana D."],
            "abstract": "Negacyclic and negative-cyclic representation for RLWE and MLWE structure learning.",
            "source": "semantic_scholar",
            "url": "https://example.test/negacyclic",
            "date": "2026-05-29",
            "reading_priority_score": 75,
            "priority_label": "建议精读",
        },
        {
            "title": "ML-KEM and ML-DSA Implementation Security Audit",
            "authors": ["Eve E."],
            "abstract": "Kyber ML-KEM and Dilithium ML-DSA side-channel, fault attack and constant-time audit.",
            "source": "crossref",
            "url": "https://doi.org/10.1000/pqc.1",
            "doi": "10.1000/pqc.1",
            "date": "2026-05-28",
            "reading_priority_score": 78,
            "priority_label": "建议精读",
        },
        {
            "title": "ML-KEM and ML-DSA Implementation Security Audit Duplicate",
            "authors": ["Eve E."],
            "abstract": "Duplicate DOI should be merged.",
            "source": "openalex",
            "url": "https://openalex.org/test",
            "doi": "10.1000/pqc.1",
            "date": "2026-05-28",
            "reading_priority_score": 70,
            "priority_label": "建议精读",
        },
        {
            "title": "Untitled Report without Authors",
            "authors": [],
            "abstract": "A low-priority report with missing DOI and missing authors.",
            "source": "openalex",
            "url": "https://example.test/no-authors",
            "date": "2026-05-27",
            "reading_priority_score": 35,
            "priority_label": "暂存",
        },
    ]


def _write_digest(root: Path, records: list[dict[str, object]] | None = None) -> Path:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "2026-05-30.json"
    payload = {
        "metadata": {
            "target_date": "2026-05-30",
            "collector": "local_codex",
            "quality_status": "authoritative_backfill",
            "run_mode": "backfill",
        },
        "records": records or _records(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_csl_json_and_zotero_json_outputs_are_valid() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_digest(root)
        result = generate_zotero_export(input_dir=root / "data", output_dir=root / "exports" / "zotero")

        assert result.written_paths
        csl = json.loads((result.run_dir / "items.csl.json").read_text(encoding="utf-8"))
        zotero = json.loads((result.run_dir / "zotero_items.json").read_text(encoding="utf-8"))

        assert isinstance(csl, list)
        assert csl[0]["title"]
        assert "URL" in csl[0]
        assert "note" in csl[0]
        assert zotero[0]["itemType"]
        assert zotero[0]["title"]
        assert zotero[0]["tags"]
        assert zotero[0]["collections"]


def test_bibtex_key_is_stable_ascii_and_ris_records_end_with_er() -> None:
    record = _records()[0]
    key1 = build_stable_citation_key(record)
    key2 = build_stable_citation_key(record)
    assert key1 == key2
    assert " " not in key1
    assert key1.isascii()
    assert re.fullmatch(r"[A-Za-z0-9]+", key1)

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_digest(root)
        result = generate_zotero_export(input_dir=root / "data", output_dir=root / "exports" / "zotero")
        ris = (result.run_dir / "items.ris").read_text(encoding="utf-8")
        records = [chunk for chunk in ris.strip().split("\n\n") if chunk.strip()]
        assert records
        assert all(chunk.strip().endswith("ER  -") for chunk in records)


def test_lattice_research_line_tags_are_generated() -> None:
    ai_tags = {tag["tag"] for tag in build_zotero_tags(_records()[0])}
    assert "LC/Problem/LWE" in ai_tags
    assert "LC/Attack/BKZ" in ai_tags
    assert "LC/AI/AI4Lattice" in ai_tags
    assert "LC/ResearchLine/AI4Lattice-Hybrid-Ranking" in ai_tags
    assert "LC/Tool/G6K" in ai_tags
    assert "LC/Tool/fplll" in ai_tags

    module_sis_tags = {tag["tag"] for tag in build_zotero_tags(_records()[1])}
    assert "LC/Problem/Module-SIS" in module_sis_tags
    assert "LC/Primitive/Chameleon-Hash" in module_sis_tags
    assert "LC/ResearchLine/Module-SIS-Chameleon-Hash" in module_sis_tags

    negacyclic_tags = {tag["tag"] for tag in build_zotero_tags(_records()[2])}
    assert "LC/Problem/RLWE" in negacyclic_tags
    assert "LC/Problem/MLWE" in negacyclic_tags
    assert "LC/ResearchLine/RLWE-MLWE-Negative-Cyclic" in negacyclic_tags

    implementation_tags = {tag["tag"] for tag in build_zotero_tags(_records()[3])}
    assert "LC/Scheme/ML-KEM" in implementation_tags
    assert "LC/Scheme/ML-DSA" in implementation_tags
    assert "LC/Implementation/Side-Channel" in implementation_tags
    assert "LC/Implementation/Fault-Attack" in implementation_tags
    assert "LC/Implementation/Constant-Time" in implementation_tags
    assert "LC/ResearchLine/PQC-Implementation-Security" in implementation_tags


def test_missing_doi_and_authors_do_not_emit_empty_garbage_or_crash() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_digest(root, [_records()[-1]])
        result = generate_zotero_export(input_dir=root / "data", output_dir=root / "exports" / "zotero")
        zotero = json.loads((result.run_dir / "zotero_items.json").read_text(encoding="utf-8"))
        assert "DOI" not in zotero[0]
        assert "creators" not in zotero[0] or zotero[0]["creators"] == []


def test_same_doi_is_deduplicated() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_digest(root)
        result = generate_zotero_export(input_dir=root / "data", output_dir=root / "exports" / "zotero")
        dois = [item.get("doi") for item in result.items if item.get("doi")]
        assert dois.count("10.1000/pqc.1") == 1
        assert len(result.items) == 5


def test_dry_run_does_not_write_files_and_fail_on_empty_is_clear() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_digest(root)
        result = generate_zotero_export(input_dir=root / "data", output_dir=root / "exports" / "zotero", dry_run=True)
        assert result.dry_run
        assert not (root / "exports").exists()

        empty_dir = root / "empty"
        empty_dir.mkdir()
        try:
            generate_zotero_export(input_dir=empty_dir, output_dir=root / "exports" / "zotero", fail_on_empty=True)
        except ValueError as exc:
            assert "No Zotero-compatible records" in str(exc)
        else:
            raise AssertionError("fail_on_empty should raise for empty input")


def test_no_secret_or_private_zotero_key_in_outputs() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_digest(root)
        result = generate_zotero_export(input_dir=root / "data", output_dir=root / "exports" / "zotero")
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in result.run_dir.iterdir()
            if path.suffix in {".json", ".bib", ".ris", ".md"}
        )
        for pattern in SECRET_PATTERNS:
            assert pattern not in combined


def test_item_type_inference_and_windows_style_output_path() -> None:
    conference = {"title": "A paper at CRYPTO", "venue": "CRYPTO 2026", "source": "dblp"}
    preprint = {"title": "A preprint", "source": "arXiv"}
    assert infer_zotero_item_type(conference) == "conferencePaper"
    assert infer_csl_type(conference) == "paper-conference"
    assert infer_zotero_item_type(preprint) == "report"

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_digest(root)
        output_dir = root / "exports" / "zotero"
        result = generate_zotero_export(input_dir=root / "data", output_dir=output_dir)
        assert str(result.run_dir).endswith("2026-05-30")
        assert result.run_dir.exists()


def test_dedup_records_for_zotero_merges_source_information() -> None:
    items = [
        {
            "title": "One",
            "authors": ["A"],
            "doi": "10.1000/example",
            "source": "arxiv",
            "dedup_key": "doi:10.1000/example",
            "source_trace": ["arxiv"],
            "zotero_tags": ["a"],
        },
        {
            "title": "One copy",
            "authors": ["A"],
            "doi": "10.1000/example",
            "source": "crossref",
            "dedup_key": "doi:10.1000/example",
            "source_trace": ["crossref"],
            "zotero_tags": ["b"],
        },
    ]

    deduped = dedup_records_for_zotero(items)

    assert len(deduped) == 1
    assert set(deduped[0]["source_trace"]) == {"arxiv", "crossref"}
