from __future__ import annotations

import json
from pathlib import Path

from lattice_digest.artifact_paths import daily_data_path, daily_digest_path
from lattice_digest.sources.base import SourceAdapter


def test_all_red_date_targeted_run_still_writes_source_health_artifact(tmp_path: Path, monkeypatch) -> None:
    import lattice_digest.run as run_module

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text(
        "sources:\n  - name: broken_source\n    type: broken\n    enabled: true\n",
        encoding="utf-8",
    )
    (config_dir / "taxonomy.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "keywords.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "negative_keywords.yaml").write_text("{}", encoding="utf-8")

    class BrokenSource(SourceAdapter):
        def fetch(self, context):  # type: ignore[no-untyped-def]
            raise RuntimeError("simulated source failure")

    monkeypatch.setattr(run_module, "project_root", lambda: tmp_path)
    monkeypatch.setattr(run_module, "build_source", lambda config: BrokenSource(config))

    result = run_module.main(
        [
            "--date",
            "2026-06-06",
            "--output",
            "markdown,json",
            "--send",
            "none",
            "--retry-failed-sources",
            "--include-latest-sources",
            "--config-dir",
            str(config_dir),
        ]
    )

    json_path = daily_data_path("2026-06-06", tmp_path / "data")
    markdown_path = daily_digest_path("2026-06-06", tmp_path / "digests")
    assert result == 0
    assert json_path.exists()
    assert markdown_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["records"] == []
    assert payload["source_health"]
    assert payload["source_health"][0]["status"] == "red"
    assert payload["source_health"][0]["retryable"] is True
    assert "simulated source failure" in payload["source_health"][0]["errors"][0]

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "broken_source" in markdown
    assert "数据源健康与空报告处理" in markdown
