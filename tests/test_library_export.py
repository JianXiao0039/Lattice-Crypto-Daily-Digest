from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.export_library import bibtex_key, generate_library_export, record_to_library_item, render_bibtex
from lattice_digest.library_taxonomy import classify_text


SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA")
POLLUTION_MARKERS = ("<b>", "</b>", "contentReference", "oaicite", "id=")


def _sample_records() -> list[dict[str, object]]:
    return [
        {
            "title": "Transformer LWE Cryptanalysis with BKZ Hybrid Ranking",
            "authors": ["Alice A.", "Bob B."],
            "abstract": "AI-assisted lattice cryptanalysis for LWE, BKZ, G6K and fplll hybrid attacks.",
            "source": "arxiv",
            "url": "https://arxiv.org/abs/2605.00001",
            "arxiv_id": "2605.00001",
            "doi": "10.1000/lwe.1",
            "date": "2026-05-30",
            "reading_priority_score": 95,
            "priority_label": "必须精读",
            "reason_for_priority": "命中 Transformer LWE、BKZ 和 hybrid attack。",
            "why_it_matters": "直接服务 AI4Lattice 与 LWE 攻击主线。",
            "suggested_action": "今日精读",
            "research_hooks": ["构造 LWE coordinate selection benchmark。"],
            "advisor_questions": ["是否能接入 hybrid attack pipeline？"],
        },
        {
            "title": "Module-SIS Chameleon Hash Commitment with Reproducible Parameters",
            "authors": ["Carol C."],
            "abstract": "A Module-SIS commitment and chameleon hash with parameter estimation and implementation artifact.",
            "source": "iacr_eprint",
            "url": "https://eprint.iacr.org/2026/001",
            "eprint_id": "2026/001",
            "date": "2026-05-30",
            "reading_priority_score": 82,
            "priority_label": "建议精读",
            "reason_for_priority": "命中 Module-SIS、commitment、chameleon hash。",
            "suggested_action": "本周阅读",
        },
        {
            "title": "ML-KEM and ML-DSA Implementation Audit",
            "authors": ["Dana D."],
            "abstract": "Kyber ML-KEM and Dilithium ML-DSA side-channel, fault attack and constant-time audit.",
            "source": "crossref",
            "url": "https://doi.org/10.1000/pqc.1",
            "doi": "10.1000/pqc.1",
            "date": "2026-05-29",
            "reading_priority_score": 78,
            "priority_label": "建议精读",
            "reason_for_priority": "实现安全与 PQC 标准方案相关。",
        },
        {
            "title": "FHE CKKS BFV BGV TFHE Application Benchmark",
            "authors": [],
            "abstract": "FHE application benchmark for CKKS, BFV, BGV and TFHE bootstrapping.",
            "source": "openalex",
            "url": "https://example.test/fhe",
            "date": "2026-05-28",
            "reading_priority_score": 55,
            "priority_label": "可略读",
        },
        {
            "title": "Generic Transformer for Traffic Prediction",
            "authors": ["Eve E."],
            "abstract": "A transformer model for traffic prediction without cryptanalysis or lattice context.",
            "source": "semantic_scholar",
            "url": "https://example.test/traffic",
            "date": "2026-05-28",
            "reading_priority_score": 20,
            "priority_label": "低相关",
        },
        {
            "title": "Sparse RLWE and MLWE Attacks over Ring-SIS Benchmarks",
            "abstract": "Ring-LWE RLWE Module-LWE MLWE LWE Ring-SIS SIS and Short Integer Solution benchmarks.",
            "source": "dblp",
            "url": "https://dblp.org/rec/test",
            "date": "2026-05-27",
            "reading_priority_score": 74,
            "priority_label": "建议精读",
        },
    ]


def _write_digest(path: Path, records: list[dict[str, object]] | None = None) -> Path:
    data_dir = path / "data"
    data_dir.mkdir()
    digest = data_dir / "2026-05-30.json"
    payload = {"metadata": {"target_date": "2026-05-30"}, "records": records or _sample_records()}
    digest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return digest


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_generates_library_items_and_interop_formats() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        digest = _write_digest(root)
        output_dir = root / "exports" / "library"

        result = generate_library_export(digest, output_dir, formats="all")

        assert len(result.items) == 6
        library_json = json.loads((output_dir / "library-items.json").read_text(encoding="utf-8"))
        assert library_json["metadata"]["schema_version"] == 1
        assert library_json["items"][0]["item_id"].startswith("lib-")
        assert library_json["items"][0]["dedup_key"]
        assert (output_dir / "library-items.csl.json").exists()
        assert (output_dir / "library-items.bib").exists()
        assert (output_dir / "library-items.ris").exists()
        assert (output_dir / "zotero-tags.json").exists()
        assert (output_dir / "import-report.md").exists()


def test_csl_bibtex_ris_and_tags_content() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        digest = _write_digest(root)
        output_dir = root / "exports" / "library"
        result = generate_library_export(digest, output_dir, formats="all")

        csl = json.loads((output_dir / "library-items.csl.json").read_text(encoding="utf-8"))
        assert csl[0]["title"]
        assert csl[0]["URL"]
        assert "note" in csl[0]

        first_key = bibtex_key(result.items[0])
        second_key = bibtex_key(result.items[0])
        assert first_key == second_key
        assert first_key in _read(output_dir / "library-items.bib")

        ris = _read(output_dir / "library-items.ris")
        assert "TY  -" in ris
        assert "TI  -" in ris
        assert "ER  -" in ris

        tags = json.loads((output_dir / "zotero-tags.json").read_text(encoding="utf-8"))
        flattened_priority = {tag for item in tags for tag in item["priority_tags"]}
        assert "priority/must-read" in flattened_priority or "priority/recommended" in flattened_priority

        report = _read(output_dir / "import-report.md")
        assert "标签分布" in report
        assert "质量警告" in report


def test_lattice_taxonomy_distinguishes_core_families() -> None:
    lwe = classify_text(title="LWE RLWE MLWE attacks", abstract="Learning with errors, Ring-LWE and Module-LWE.")
    assert "LWE" in lwe.lattice_tags
    assert "Ring-LWE" in lwe.lattice_tags
    assert "Module-LWE" in lwe.lattice_tags

    sis = classify_text(title="SIS Module-SIS Ring-SIS", abstract="Short Integer Solution, Module-SIS and Ring-SIS.")
    assert "SIS" in sis.lattice_tags
    assert "Module-SIS" in sis.lattice_tags
    assert "Ring-SIS" in sis.lattice_tags

    reduction = classify_text(title="BKZ G6K fplll", abstract="BKZ lattice reduction with G6K and fplll.")
    assert "BKZ" in reduction.lattice_tags
    assert "G6K" in reduction.lattice_tags
    assert "fplll" in reduction.lattice_tags


def test_ai4lattice_requires_ai_and_lattice_context() -> None:
    ai_lattice = classify_text(title="Transformer LWE", abstract="Transformer for LWE cryptanalysis and BKZ.")
    assert "AI4Lattice" in ai_lattice.ai_tags

    generic_ai = classify_text(title="Generic Transformer", abstract="Transformer for traffic prediction.")
    assert "AI4Lattice" not in generic_ai.ai_tags


def test_export_does_not_propagate_old_falcon_x_false_positive_tags() -> None:
    item = record_to_library_item(
        {
            "title": "Falcon-X: A Time Series Foundation Model",
            "abstract": "Falcon-X is a generic forecasting model for heterogeneous time series.",
            "source": "semantic_scholar",
            "url": "https://example.test/falcon-x",
            "taxonomy_tags": ["C03_Falcon_FNDSA", "pqc_lattice_schemes"],
            "reason": "标题命中核心格密码关键词：falcon。",
            "reading_priority_score": 40,
        },
        "2026-05-30",
    )

    assert "Falcon" not in item["pqc_tags"]


def test_primitive_pqc_implementation_zk_and_fhe_tags() -> None:
    primitive = classify_text(
        title="Module-SIS Chameleon Hash Commitment",
        abstract="Module-SIS commitment and lattice chameleon hash.",
    )
    assert "Module-SIS" in primitive.lattice_tags
    assert "Commitment" in primitive.primitive_tags
    assert "Chameleon Hash" in primitive.primitive_tags

    pqc = classify_text(
        title="ML-KEM Kyber ML-DSA Dilithium",
        abstract="Falcon implementation side-channel fault attack constant-time audit.",
    )
    assert "ML-KEM" in pqc.pqc_tags
    assert "Kyber" in pqc.pqc_tags
    assert "ML-DSA" in pqc.pqc_tags
    assert "Dilithium" in pqc.pqc_tags
    assert "Falcon" in pqc.pqc_tags
    assert "Side-Channel" in pqc.implementation_tags
    assert "Fault Attack" in pqc.implementation_tags
    assert "Constant-Time" in pqc.implementation_tags

    falcon_x = classify_text(title="Falcon-X time series model", abstract="A generic foundation model.")
    assert "Falcon" not in falcon_x.pqc_tags

    zk = classify_text(title="ZK-friendly post-quantum privacy", abstract="ZK-friendly lattice commitment anonymous credential.")
    assert "ZK-Friendly" in zk.primitive_tags
    assert "ZK-friendly PQ Privacy" in zk.research_tags

    fhe = classify_text(title="FHE CKKS BFV BGV TFHE", abstract="Homomorphic encryption bootstrapping application benchmark.")
    assert {"FHE", "CKKS", "BFV", "BGV", "TFHE"}.issubset(set(fhe.primitive_tags))
    assert not fhe.attack_tags


def test_dry_run_filters_and_does_not_write_files_or_modify_inputs() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        digest = _write_digest(root)
        digests_dir = root / "digests"
        digests_dir.mkdir()
        digest_md = digests_dir / "2026-05-30.md"
        digest_md.write_text("original", encoding="utf-8")
        db_path = root / "papers.db"
        db_path.write_text("db", encoding="utf-8")

        result = generate_library_export(
            digest,
            root / "exports" / "library",
            formats="all",
            min_priority_score=70,
            dry_run=True,
        )

        assert all(int(item["reading_priority_score"]) >= 70 for item in result.items)
        assert result.dry_run
        assert not (root / "exports").exists()
        assert digest_md.read_text(encoding="utf-8") == "original"
        assert db_path.read_text(encoding="utf-8") == "db"


def test_outputs_are_clean_and_do_not_contain_secret_patterns() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        digest = _write_digest(
            root,
            [
                {
                    "title": "<b>Bad</b> contentReference oaicite id=abc Transformer LWE",
                    "abstract": "AI-assisted lattice cryptanalysis for LWE.",
                    "source": "arxiv",
                    "url": "https://example.test/paper",
                    "reading_priority_score": 90,
                    "priority_label": "必须精读",
                }
            ],
        )
        output_dir = root / "exports" / "library"
        generate_library_export(digest, output_dir, formats="all")

        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in output_dir.iterdir()
            if path.suffix in {".json", ".bib", ".ris", ".md"}
        )
        for marker in POLLUTION_MARKERS:
            assert marker not in combined
        for pattern in SECRET_PATTERNS:
            assert pattern not in combined


def test_render_bibtex_omits_fabricated_anonymous_author() -> None:
    item = {
        "title": "Untitled LWE note",
        "authors": [],
        "year": 2026,
        "url": "https://example.test",
        "doi": "",
        "venue": "",
        "source": "arxiv",
        "priority_label": "可略读",
        "reading_priority_score": 55,
        "dedup_key": "title:test",
    }

    bib = render_bibtex([item])

    assert "anonymous" not in bib.lower()
    assert "@misc" in bib
