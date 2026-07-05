from __future__ import annotations

import json
from pathlib import Path

from lattice_digest.artifact_paths import daily_data_path, daily_digest_path
from lattice_digest.models import make_paper_record
from lattice_digest.sources.base import SourceAdapter


def _write_config(root: Path) -> Path:
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text(
        "sources:\n  - name: fake_source\n    type: fake\n    enabled: true\n",
        encoding="utf-8",
    )
    (config_dir / "taxonomy.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "keywords.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "negative_keywords.yaml").write_text("{}", encoding="utf-8")
    return config_dir


def test_parse_args_accepts_output_root(tmp_path: Path) -> None:
    import lattice_digest.run as run_module

    args = run_module.parse_args(["--output-root", str(tmp_path)])

    assert args.output_root == tmp_path


def test_output_root_writes_scratch_artifacts_without_overwriting_authoritative_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import lattice_digest.run as run_module

    project_root = tmp_path / "project"
    scratch_root = tmp_path / "scratch"
    project_root.mkdir()
    config_dir = _write_config(project_root)

    authoritative_json = daily_data_path("2026-07-01", project_root / "data")
    authoritative_md = daily_digest_path("2026-07-01", project_root / "digests")
    authoritative_json.parent.mkdir(parents=True)
    authoritative_md.parent.mkdir(parents=True)
    authoritative_json.write_text(
        json.dumps(
            {
                "metadata": {
                    "target_date": "2026-07-01",
                    "collector": "local_codex",
                    "quality_status": "authoritative",
                },
                "records": [{"title": "existing authoritative"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    authoritative_md.write_text("existing authoritative markdown", encoding="utf-8")

    record = make_paper_record(
        title="BKZ cost models for LWE attacks",
        abstract="We study lattice cryptanalysis for LWE and BKZ hybrid attacks.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2607.00001",
        venue="arXiv",
        publication_date="2026-07-01",
        relevance_label="A",
        relevance_score=95,
        reason="lattice cryptography and BKZ cryptanalysis",
    )

    class FakeSource(SourceAdapter):
        def fetch(self, context):  # type: ignore[no-untyped-def]
            context.set_source_counts(self.name, raw=1, normalized=1, date_filtered=1)
            return [record]

    monkeypatch.setattr(run_module, "project_root", lambda: project_root)
    monkeypatch.setattr(run_module, "build_source", lambda config: FakeSource(config))
    monkeypatch.setattr(run_module, "rank_records", lambda incoming, taxonomy, keywords, negative: list(incoming))

    result = run_module.main(
        [
            "--date",
            "2026-07-01",
            "--output",
            "markdown,json",
            "--send",
            "none",
            "--output-root",
            str(scratch_root),
            "--config-dir",
            str(config_dir),
        ]
    )

    assert result == 0

    scratch_json = daily_data_path("2026-07-01", scratch_root / "data")
    scratch_md = daily_digest_path("2026-07-01", scratch_root / "digests")
    assert scratch_json.exists()
    assert scratch_md.exists()
    assert (scratch_root / "papers.db").exists()
    assert (scratch_root / "audits" / "source-health" / "2026-07-01.json").exists()

    assert json.loads(authoritative_json.read_text(encoding="utf-8"))["records"] == [
        {"title": "existing authoritative"}
    ]
    assert authoritative_md.read_text(encoding="utf-8") == "existing authoritative markdown"

    payload = json.loads(scratch_json.read_text(encoding="utf-8"))
    item = payload["records"][0]
    assert payload["metadata"]["target_date"] == "2026-07-01"
    assert item["selected_date_basis"] == "publication_date"
    assert item["freshness_bucket"] == "primary_today_new"
    assert item["freshness_reason"]
    assert item["primary_today_new_eligible"] is True
    assert item["venue"] == "arXiv"
    assert item["venue_type"] == "preprint"
    assert item["CCF_rank"] == "N/A"
    assert item["abstract_en"]
    assert item["abstract_zh"].startswith("model-generated zh summary:")
    assert item["conclusion_en"].startswith("model-generated from available metadata:")
    assert item["conclusion_zh"].startswith("model-generated zh summary:")
    assert item["recommendation_level"] == "Strong"
    assert item["recommendation_score"] >= 85
    assert "LWE/RLWE/MLWE" in item["recommendation_reason"]
    assert item["user_relevance_tags"]
    assert item["suggested_action"] == "Read today"


def test_default_output_root_remains_project_root(tmp_path: Path, monkeypatch) -> None:
    import lattice_digest.run as run_module

    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = _write_config(project_root)

    class FakeSource(SourceAdapter):
        def fetch(self, context):  # type: ignore[no-untyped-def]
            context.set_source_counts(self.name, raw=0, normalized=0, date_filtered=0)
            return []

    monkeypatch.setattr(run_module, "project_root", lambda: project_root)
    monkeypatch.setattr(run_module, "build_source", lambda config: FakeSource(config))
    monkeypatch.setattr(run_module, "rank_records", lambda incoming, taxonomy, keywords, negative: list(incoming))

    result = run_module.main(
        [
            "--date",
            "2026-07-01",
            "--output",
            "markdown,json",
            "--send",
            "none",
            "--config-dir",
            str(config_dir),
        ]
    )

    assert result == 0
    assert daily_data_path("2026-07-01", project_root / "data").exists()
    assert daily_digest_path("2026-07-01", project_root / "digests").exists()
