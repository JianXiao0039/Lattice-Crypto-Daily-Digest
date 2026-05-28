from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.models import make_paper_record
from lattice_digest.sources.base import SourceAdapter
from lattice_digest.storage import write_sqlite


def _write_config(root: Path, *, enabled_source: bool = False) -> Path:
    config_dir = root / "config"
    config_dir.mkdir()
    source_block = (
        """
sources:
  - name: fake_source
    type: fake
    enabled: true
""".strip()
        if enabled_source
        else "sources: []"
    )
    (config_dir / "sources.yaml").write_text(source_block, encoding="utf-8")
    (config_dir / "taxonomy.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "keywords.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "negative_keywords.yaml").write_text("{}", encoding="utf-8")
    return config_dir


def _run_in_temp_root(root: Path, args: list[str], records: list | None = None) -> int:
    import lattice_digest.run as run_module

    class FakeSource(SourceAdapter):
        def fetch(self, context):  # type: ignore[no-untyped-def]
            context.set_source_counts(self.name, raw=len(records or []), normalized=len(records or []), date_filtered=len(records or []))
            return list(records or [])

    original_project_root = run_module.project_root
    original_build_source = run_module.build_source
    original_rank_records = run_module.rank_records
    try:
        run_module.project_root = lambda: root
        run_module.build_source = lambda config: FakeSource(config)
        run_module.rank_records = lambda incoming, taxonomy, keywords, negative: list(incoming)
        return run_module.main(args)
    finally:
        run_module.project_root = original_project_root
        run_module.build_source = original_build_source
        run_module.rank_records = original_rank_records


def test_target_date_writes_metadata_and_named_outputs() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config_dir = _write_config(root)

        result = _run_in_temp_root(
            root,
            [
                "--target-date",
                "2026-05-27",
                "--since",
                "7d",
                "--output",
                "markdown,json",
                "--send",
                "none",
                "--collector",
                "local_codex",
                "--quality-status",
                "authoritative_backfill",
                "--run-mode",
                "backfill",
                "--config-dir",
                str(config_dir),
            ],
        )

        assert result == 0
        json_path = root / "data" / "2026-05-27.json"
        markdown_path = root / "digests" / "2026-05-27.md"
        assert json_path.exists()
        assert markdown_path.exists()

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        metadata = payload["metadata"]
        assert metadata["target_date"] == "2026-05-27"
        assert metadata["collector"] == "local_codex"
        assert metadata["quality_status"] == "authoritative_backfill"
        assert metadata["run_mode"] == "backfill"
        assert metadata["backfill"] is True
        assert metadata["coverage_start"]
        assert metadata["coverage_end"]

        markdown = markdown_path.read_text(encoding="utf-8")
        assert "target_date：2026-05-27" in markdown
        assert "collector：local_codex" in markdown
        assert "quality_status：authoritative_backfill" in markdown


def test_backfill_keeps_record_even_if_paper_already_exists_in_papers_db() -> None:
    record = make_paper_record(
        title="BKZ cost models for LWE attacks",
        abstract="A lattice cryptanalysis paper about BKZ and LWE attacks.",
        source="fake_source",
        source_url="https://example.test/lwe-bkz",
        publication_date="2026-05-27",
        relevance_label="A",
        relevance_score=90,
    )
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config_dir = _write_config(root, enabled_source=True)
        write_sqlite([record], root / "papers.db")

        result = _run_in_temp_root(
            root,
            [
                "--target-date",
                "2026-05-27",
                "--since",
                "7d",
                "--output",
                "markdown,json",
                "--send",
                "none",
                "--collector",
                "local_codex",
                "--quality-status",
                "authoritative_backfill",
                "--run-mode",
                "backfill",
                "--config-dir",
                str(config_dir),
            ],
            [record],
        )

        assert result == 0
        payload = json.loads((root / "data" / "2026-05-27.json").read_text(encoding="utf-8"))
        assert [item["title"] for item in payload["records"]] == ["BKZ cost models for LWE attacks"]


def test_provisional_report_can_be_replaced_by_authoritative_backfill() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config_dir = _write_config(root)
        data_dir = root / "data"
        digest_dir = root / "digests"
        data_dir.mkdir()
        digest_dir.mkdir()
        (data_dir / "2026-05-27.json").write_text(
            json.dumps(
                {
                    "metadata": {
                        "target_date": "2026-05-27",
                        "collector": "github_actions",
                        "run_date": "2026-05-27",
                        "quality_status": "provisional",
                    },
                    "records": [{"title": "old provisional"}],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (digest_dir / "2026-05-27.md").write_text("old provisional", encoding="utf-8")

        result = _run_in_temp_root(
            root,
            [
                "--target-date",
                "2026-05-27",
                "--since",
                "7d",
                "--output",
                "markdown,json",
                "--send",
                "none",
                "--collector",
                "local_codex",
                "--quality-status",
                "authoritative_backfill",
                "--run-mode",
                "backfill",
                "--config-dir",
                str(config_dir),
            ],
        )

        assert result == 0
        payload = json.loads((data_dir / "2026-05-27.json").read_text(encoding="utf-8"))
        metadata = payload["metadata"]
        assert metadata["quality_status"] == "authoritative_backfill"
        assert metadata["supersedes"] == {
            "collector": "github_actions",
            "run_date": "2026-05-27",
            "quality_status": "provisional",
        }
        archived_json = root / "archive" / "provisional" / "2026-05-27.json"
        archived_markdown = root / "archive" / "provisional" / "2026-05-27.md"
        assert archived_json.exists()
        assert archived_markdown.exists()
        archived_payload = json.loads(archived_json.read_text(encoding="utf-8"))
        assert archived_payload["records"][0]["title"] == "old provisional"
        assert archived_markdown.read_text(encoding="utf-8") == "old provisional"


def test_authoritative_backfill_is_not_overwritten_by_github_provisional() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config_dir = _write_config(root)
        data_dir = root / "data"
        digest_dir = root / "digests"
        data_dir.mkdir()
        digest_dir.mkdir()
        existing_payload = {
            "metadata": {
                "target_date": "2026-05-27",
                "collector": "local_codex",
                "run_date": "2026-05-28",
                "quality_status": "authoritative_backfill",
            },
            "records": [{"title": "authoritative"}],
        }
        (data_dir / "2026-05-27.json").write_text(json.dumps(existing_payload, ensure_ascii=False), encoding="utf-8")
        (digest_dir / "2026-05-27.md").write_text("authoritative", encoding="utf-8")

        result = _run_in_temp_root(
            root,
            [
                "--target-date",
                "2026-05-27",
                "--since",
                "36h",
                "--output",
                "markdown,json",
                "--send",
                "none",
                "--collector",
                "github_actions",
                "--quality-status",
                "provisional",
                "--run-mode",
                "daily",
                "--config-dir",
                str(config_dir),
            ],
        )

        assert result == 0
        payload = json.loads((data_dir / "2026-05-27.json").read_text(encoding="utf-8"))
        assert payload == existing_payload
        assert (digest_dir / "2026-05-27.md").read_text(encoding="utf-8") == "authoritative"


def test_original_run_without_target_date_still_writes_today_output() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config_dir = _write_config(root)

        result = _run_in_temp_root(
            root,
            [
                "--since",
                "7d",
                "--output",
                "markdown,json",
                "--send",
                "none",
                "--config-dir",
                str(config_dir),
            ],
        )

        assert result == 0
        assert list((root / "data").glob("*.json"))
        assert list((root / "digests").glob("*.md"))
