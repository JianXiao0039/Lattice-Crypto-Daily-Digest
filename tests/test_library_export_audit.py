from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.audit_library_export import audit_library_export
from lattice_digest.export_library import generate_library_export


POLLUTION_MARKERS = ("<b>", "</b>", "contentReference", "oaicite", "id=")
SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA")


def _records() -> list[dict[str, object]]:
    return [
        {
            "title": "Transformer LWE Hybrid Attack",
            "authors": ["Alice"],
            "abstract": "AI-assisted lattice cryptanalysis for LWE with BKZ hybrid attack.",
            "source": "arxiv",
            "url": "https://example.test/lwe",
            "doi": "10.1000/test-lwe",
            "date": "2026-05-30",
            "reading_priority_score": 95,
            "priority_label": "必须精读",
        },
        {
            "title": "Module-SIS Chameleon Hash",
            "authors": [],
            "abstract": "Module-SIS chameleon hash commitment with parameter estimation.",
            "source": "iacr_eprint",
            "url": "https://example.test/msis",
            "date": "2026-05-30",
            "reading_priority_score": 82,
            "priority_label": "建议精读",
        },
        {
            "title": "ML-KEM Constant-Time Audit",
            "authors": ["Bob"],
            "abstract": "Kyber ML-KEM side-channel fault attack and constant-time implementation audit.",
            "source": "crossref",
            "url": "https://example.test/mlkem",
            "date": "2026-05-29",
            "reading_priority_score": 76,
            "priority_label": "建议精读",
        },
        {
            "title": "ZK-friendly PQ Privacy Commitment",
            "authors": ["Carol"],
            "abstract": "Lattice-based ZK-friendly post-quantum privacy commitment and anonymous credential.",
            "source": "openalex",
            "url": "https://example.test/zk",
            "date": "2026-05-28",
            "reading_priority_score": 70,
            "priority_label": "建议精读",
        },
        {
            "title": "FHE Application",
            "authors": [],
            "abstract": "",
            "source": "semantic_scholar",
            "url": "",
            "date": "",
            "reading_priority_score": 45,
            "priority_label": "暂存",
        },
    ]


def _write_digest(root: Path) -> Path:
    data_dir = root / "data"
    data_dir.mkdir()
    digest = data_dir / "2026-05-30.json"
    digest.write_text(
        json.dumps({"metadata": {"target_date": "2026-05-30"}, "records": _records()}, ensure_ascii=False),
        encoding="utf-8",
    )
    return data_dir


def _combined_text(output_dir: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in output_dir.iterdir() if path.is_file())


def test_audit_reports_from_library_items_json() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = _write_digest(root)
        library_dir = root / "exports" / "library"
        generate_library_export(data_dir, library_dir, formats="all")

        result = audit_library_export(library_dir / "library-items.json", root / "audits" / "library-export")

        assert len(result.items) == 5
        assert (root / "audits" / "library-export" / "tag-quality-report.md").exists()
        assert (root / "audits" / "library-export" / "field-quality-report.md").exists()
        assert (root / "audits" / "library-export" / "taxonomy-confusion-report.json").exists()
        assert (root / "audits" / "library-export" / "zotero-import-checklist.md").exists()


def test_audit_reports_from_data_digest_json() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = _write_digest(root)
        output_dir = root / "audits" / "library-export"

        result = audit_library_export(data_dir, output_dir, from_date="2026-05-30", to_date="2026-05-30")

        assert len(result.items) == 5
        tag_report = (output_dir / "tag-quality-report.md").read_text(encoding="utf-8")
        assert "AI4Lattice" in tag_report
        assert "Module-SIS" in tag_report
        assert "Chameleon Hash" in tag_report
        assert "BKZ" in tag_report


def test_dry_run_does_not_write_files_or_modify_inputs() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = _write_digest(root)
        digests_dir = root / "digests"
        digests_dir.mkdir()
        digest_md = digests_dir / "2026-05-30.md"
        digest_md.write_text("original", encoding="utf-8")
        db_path = root / "papers.db"
        db_path.write_text("db", encoding="utf-8")

        result = audit_library_export(data_dir, root / "audits" / "library-export", dry_run=True)

        assert len(result.items) == 5
        assert result.dry_run
        assert not (root / "audits").exists()
        assert digest_md.read_text(encoding="utf-8") == "original"
        assert db_path.read_text(encoding="utf-8") == "db"


def test_field_confusion_and_zotero_reports_content() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = _write_digest(root)
        output_dir = root / "audits" / "library-export"
        audit_library_export(data_dir, output_dir)

        field_report = (output_dir / "field-quality-report.md").read_text(encoding="utf-8")
        assert "缺 DOI 数量" in field_report
        assert "缺作者数量" in field_report
        assert "缺摘要数量" in field_report

        confusion = json.loads((output_dir / "taxonomy-confusion-report.json").read_text(encoding="utf-8"))
        assert "lwe_rlwe_mlwe_distribution" in confusion
        assert "sis_module_sis_ring_sis_distribution" in confusion

        checklist = (output_dir / "zotero-import-checklist.md").read_text(encoding="utf-8")
        assert "CSL JSON" in checklist
        assert "BibTeX" in checklist
        assert "RIS" in checklist
        assert "Zotero" in checklist


def test_audit_outputs_are_clean_and_secret_free() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = _write_digest(root)
        output_dir = root / "audits" / "library-export"
        audit_library_export(data_dir, output_dir)

        combined = _combined_text(output_dir)
        for marker in POLLUTION_MARKERS:
            assert marker not in combined
        for pattern in SECRET_PATTERNS:
            assert pattern not in combined
