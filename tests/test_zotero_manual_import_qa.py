from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.zotero_compat import generate_zotero_export


SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA", ".env", "ZOTERO_KEY")


def _sample_records() -> list[dict[str, object]]:
    return [
        {
            "title": "Swin-guided Transformer LWE and MLWE Coordinate Selection for BKZ Hybrid Attack",
            "authors": ["Alice Example", "Bob Example"],
            "abstract": "AI-assisted lattice cryptanalysis for LWE, Ring-LWE RLWE, Module-LWE MLWE, BKZ and hybrid attack.",
            "source": "arxiv",
            "url": "https://arxiv.org/abs/2605.12345",
            "arxiv_id": "2605.12345",
            "date": "2026-05-30",
            "reading_priority_score": 95,
            "priority_label": "必须精读",
            "reason_for_priority": "命中 Swin, Transformer LWE, MLWE, BKZ 和 hybrid attack。",
        },
        {
            "title": "Module-SIS Chameleon Hash Commitment",
            "authors": ["Carol Example"],
            "abstract": "Module-SIS and Short Integer Solution based lattice commitment and chameleon hash.",
            "source": "iacr_eprint",
            "url": "https://eprint.iacr.org/2026/123",
            "eprint_id": "2026/123",
            "date": "2026-05-30",
            "reading_priority_score": 82,
            "priority_label": "建议精读",
        },
    ]


def _write_digest(root: Path, records: list[dict[str, object]]) -> None:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "target_date": "2026-05-30",
            "collector": "local_codex",
            "quality_status": "authoritative_backfill",
            "run_mode": "backfill",
        },
        "records": records,
    }
    (data_dir / "2026-05-30.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _combined_export_text(path: Path) -> str:
    return "\n".join(file.read_text(encoding="utf-8") for file in path.iterdir() if file.suffix in {".json", ".bib", ".ris", ".md"})


def test_zotero_manual_import_fields_and_stable_ids() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_digest(root, _sample_records())
        cwd = Path.cwd()
        os.chdir(root)
        try:
            result = generate_zotero_export(input_dir=Path("data"), output_dir=Path("exports/zotero"))
        finally:
            os.chdir(cwd)

        zotero = json.loads((root / result.run_dir / "zotero_items.json").read_text(encoding="utf-8"))
        csl = json.loads((root / result.run_dir / "items.csl.json").read_text(encoding="utf-8"))

        first = zotero[0]
        assert first["latticeDigestID"].startswith("lib-")
        assert first["canonicalID"]
        assert first["title"]
        assert first["creators"]
        assert first["date"]
        assert first["url"]
        assert first["abstractNote"]
        assert first["tags"]
        assert first["extra"]
        assert csl[0]["id"]


def test_zotero_manual_import_tags_cover_lattice_research_lines() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_digest(root, _sample_records())
        result = generate_zotero_export(input_dir=root / "data", output_dir=root / "exports" / "zotero")
        zotero = json.loads((result.run_dir / "zotero_items.json").read_text(encoding="utf-8"))
        tags = {tag["tag"] for item in zotero for tag in item["tags"]}

        assert "LC/Problem/LWE" in tags
        assert "LC/Problem/RLWE" in tags
        assert "LC/Problem/MLWE" in tags
        assert "LC/Problem/Module-SIS" in tags
        assert "LC/Attack/BKZ" in tags
        assert "LC/AI/AI4Lattice" in tags
        assert "LC/ResearchLine/Module-SIS-Chameleon-Hash" in tags


def test_empty_records_do_not_crash_and_write_empty_import_files() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_digest(root, [])
        result = generate_zotero_export(input_dir=root / "data", output_dir=root / "exports" / "zotero")

        assert result.items == []
        assert json.loads((result.run_dir / "zotero_items.json").read_text(encoding="utf-8")) == []
        assert json.loads((result.run_dir / "items.csl.json").read_text(encoding="utf-8")) == []
        assert (result.run_dir / "items.bib").read_text(encoding="utf-8") == ""
        assert (result.run_dir / "items.ris").read_text(encoding="utf-8") == ""


def test_zotero_exports_do_not_contain_local_absolute_paths_or_secrets() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_digest(root, _sample_records())
        cwd = Path.cwd()
        os.chdir(root)
        try:
            result = generate_zotero_export(input_dir=Path("data"), output_dir=Path("exports/zotero"))
        finally:
            os.chdir(cwd)

        export_dir = root / result.run_dir
        combined = _combined_export_text(export_dir)

        assert str(root) not in combined
        assert "D:\\" not in combined
        assert "C:\\" not in combined
        for pattern in SECRET_PATTERNS:
            assert pattern not in combined


def test_zotero_manual_import_docs_and_qa_script_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    doc = (root / "docs" / "zotero-manual-import.md").read_text(encoding="utf-8")
    template = (root / "docs" / "templates" / "zotero-import-audit.md").read_text(encoding="utf-8")
    script = (root / "scripts" / "qa_zotero_manual_import.ps1").read_text(encoding="utf-8")

    assert "Windows PowerShell" in doc
    assert "Windows CMD" in doc
    assert "CSL-JSON" in doc
    assert "BibTeX" in doc
    assert "RIS" in doc
    assert "title/authors/year/url/abstract/tags" in doc
    assert "Zotero Manual Import Audit" in template
    assert "--dry-run" in script
    assert "csl-json,bibtex,ris" in script
