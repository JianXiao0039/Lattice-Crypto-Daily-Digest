from __future__ import annotations

import json
from pathlib import Path


def test_date_targeted_empty_run_creates_missing_digest_artifacts(tmp_path: Path, monkeypatch) -> None:
    import lattice_digest.run as run_module

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text("sources: []", encoding="utf-8")
    (config_dir / "taxonomy.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "keywords.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "negative_keywords.yaml").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(run_module, "project_root", lambda: tmp_path)

    result = run_module.main(
        [
            "--date",
            "2026-06-09",
            "--output",
            "markdown,json",
            "--send",
            "none",
            "--config-dir",
            str(config_dir),
        ]
    )

    json_path = tmp_path / "data" / "2026-06-09.json"
    markdown_path = tmp_path / "digests" / "2026-06-09.md"
    assert result == 0
    assert json_path.exists()
    assert markdown_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["target_date"] == "2026-06-09"
    assert payload["records"] == []
    assert "PhD_Application" not in str(json_path)
    assert "ResearchArtifacts" not in str(json_path)
