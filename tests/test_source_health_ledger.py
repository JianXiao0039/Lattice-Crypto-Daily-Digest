from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import lattice_digest.run as run_module
from lattice_digest.models import make_paper_record
from lattice_digest.source_health_ledger import (
    build_source_health_payload,
    render_source_health_markdown,
    write_source_health_ledger,
)
from lattice_digest.sources.base import SourceAdapter


def _sample_source_health() -> list[dict[str, object]]:
    return [
        {
            "source": "arxiv",
            "health_status": "green",
            "raw_count": 5,
            "normalized_count": 4,
            "date_filtered_count": 3,
            "deduped_candidates": 2,
            "relevance_filtered_candidates": 2,
            "scoring_threshold_candidates": 1,
            "final_count": 1,
            "warnings": ["minor warning"],
            "errors": [],
            "error_type": None,
            "retryable": False,
        }
    ]


def _write_minimal_config(config_dir) -> None:  # type: ignore[no-untyped-def]
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text(
        """
request:
  timeout_seconds: 1
sources:
  - name: fake_source
    type: fake
    enabled: true
""".strip(),
        encoding="utf-8",
    )
    (config_dir / "taxonomy.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "keywords.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "negative_keywords.yaml").write_text("{}", encoding="utf-8")


def test_source_health_ledger_writes_json() -> None:
    run_date = date(2026, 5, 27)
    generated_at = datetime(2026, 5, 27, 1, 2, 3, tzinfo=timezone.utc)

    with TemporaryDirectory() as tmp:
        json_path, _ = write_source_health_ledger(_sample_source_health(), Path(tmp), run_date, generated_at)
        payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    assert payload["run_date"] == "2026-05-27"
    assert payload["generated_at"] == generated_at.isoformat()
    assert payload["sources"][0]["source"] == "arxiv"
    assert payload["sources"][0]["status"] == "green"
    assert payload["sources"][0]["threshold_count"] == 1
    assert payload["sources"][0]["warnings_count"] == 1


def test_source_health_ledger_writes_markdown() -> None:
    run_date = date(2026, 5, 27)
    with TemporaryDirectory() as tmp:
        _, markdown_path = write_source_health_ledger(_sample_source_health(), Path(tmp), run_date)
        markdown = markdown_path.read_text(encoding="utf-8")

    assert "# Source Health Ledger - 2026-05-27" in markdown
    assert "| Source | Status | Raw | Normalized | Final | Error Type | Retryable | Warnings | Errors |" in markdown
    assert "| arxiv | green | 5 | 4 | 1 | none | False | 1 | 0 |" in markdown


def test_source_health_ledger_handles_empty_sources() -> None:
    payload = build_source_health_payload([], date(2026, 5, 27), datetime(2026, 5, 27, tzinfo=timezone.utc))
    markdown = render_source_health_markdown(payload)

    assert payload["sources"] == []
    assert "No source health data." in markdown


def test_main_writes_source_health_ledger_for_successful_source() -> None:
    class SuccessfulSource(SourceAdapter):
        def fetch(self, context):  # type: ignore[no-untyped-def]
            context.set_source_counts(self.name, raw=1, normalized=1, date_filtered=1)
            return [
                make_paper_record(
                    title="BKZ cost models for LWE primal attacks",
                    abstract="We study lattice cryptanalysis, LWE, BKZ and hybrid attack.",
                    source=self.name,
                    source_url="https://example.org/lwe-bkz",
                    publication_date="2026-05-27",
                )
            ]

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config_dir = root / "config"
        _write_minimal_config(config_dir)

        original_project_root = run_module.project_root
        original_build_source = run_module.build_source
        try:
            run_module.project_root = lambda: root
            run_module.build_source = lambda config: SuccessfulSource(config)
            result = run_module.main(
                [
                    "--target-date",
                    "2026-05-27",
                    "--since",
                    "36h",
                    "--output",
                    "markdown,json",
                    "--send",
                    "none",
                    "--config-dir",
                    str(config_dir),
                ]
            )
        finally:
            run_module.project_root = original_project_root
            run_module.build_source = original_build_source

        assert result == 0
        ledger_path = root / "audits" / "source-health" / "2026-05-27.json"
        payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert payload["sources"][0]["source"] == "fake_source"
    assert payload["sources"][0]["status"] == "green"
    assert payload["sources"][0]["final_count"] == 1


def test_main_writes_source_health_ledger_for_failed_source() -> None:
    class BrokenSource(SourceAdapter):
        def fetch(self, context):  # type: ignore[no-untyped-def]
            raise RuntimeError("simulated source failure")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config_dir = root / "config"
        _write_minimal_config(config_dir)

        original_project_root = run_module.project_root
        original_build_source = run_module.build_source
        try:
            run_module.project_root = lambda: root
            run_module.build_source = lambda config: BrokenSource(config)
            result = run_module.main(
                [
                    "--target-date",
                    "2026-05-27",
                    "--since",
                    "36h",
                    "--output",
                    "markdown,json",
                    "--send",
                    "none",
                    "--config-dir",
                    str(config_dir),
                ]
            )
        finally:
            run_module.project_root = original_project_root
            run_module.build_source = original_build_source

        assert result == 0
        ledger_path = root / "audits" / "source-health" / "2026-05-27.json"
        payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert payload["sources"][0]["source"] == "fake_source"
    assert payload["sources"][0]["status"] == "red"
    assert payload["sources"][0]["error_type"] == "source_error"
    assert "simulated source failure" in payload["sources"][0]["errors"][0]
