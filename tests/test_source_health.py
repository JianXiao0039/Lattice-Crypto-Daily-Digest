from __future__ import annotations

import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError

from lattice_digest.http import request_text
from lattice_digest.artifact_paths import daily_data_path, daily_digest_path
from lattice_digest.sources.base import SourceAdapter


class _Headers(dict):
    def get(self, key: str, default: str | None = None) -> str | None:
        return super().get(key, default)


def test_semantic_scholar_400_warning_includes_response_body_preview() -> None:
    body = b'{"error":"bad fields","details":"Semantic Scholar rejected the request"}'

    def fake_open(request: object, timeout: int) -> object:
        raise HTTPError(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            400,
            "Bad Request",
            _Headers({}),
            io.BytesIO(body),
        )

    with TemporaryDirectory() as tmp:
        warnings: list[str] = []
        response = request_text(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            source="semantic_scholar",
            user_agent="test-agent",
            cache_dir=Path(tmp),
            min_interval_seconds=0,
            max_retries=0,
            warnings=warnings,
            open_func=fake_open,
        )

    assert response.ok is False
    assert warnings
    assert "HTTP 400" in warnings[0]
    assert "body_preview=" in warnings[0]
    assert "Semantic Scholar rejected the request" in warnings[0]


def test_main_generates_outputs_and_source_health_when_source_fails() -> None:
    import lattice_digest.run as run_module

    class BrokenSource(SourceAdapter):
        def fetch(self, context):  # type: ignore[no-untyped-def]
            raise RuntimeError("simulated source failure")

    def fake_build_source(config: dict) -> SourceAdapter:
        return BrokenSource(config)

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config_dir = root / "config"
        config_dir.mkdir()
        (config_dir / "sources.yaml").write_text(
            """
request:
  timeout_seconds: 1
sources:
  - name: broken_source
    type: broken
    enabled: true
""".strip(),
            encoding="utf-8",
        )
        (config_dir / "taxonomy.yaml").write_text("{}", encoding="utf-8")
        (config_dir / "keywords.yaml").write_text("{}", encoding="utf-8")
        (config_dir / "negative_keywords.yaml").write_text("{}", encoding="utf-8")

        original_project_root = run_module.project_root
        original_build_source = run_module.build_source
        try:
            run_module.project_root = lambda: root
            run_module.build_source = fake_build_source

            result = run_module.main(
                [
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
        json_files = list((root / "data").rglob("*.json"))
        markdown_files = list((root / "digests").rglob("*.md"))
        assert json_files
        assert markdown_files
        assert (root / "papers.db").exists()

        payload = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert payload["records"] == []
        assert payload["source_health"][0]["source"] == "broken_source"
        assert payload["source_health"][0]["errors"]
        assert "simulated source failure" in payload["source_health"][0]["errors"][0]

        markdown = markdown_files[0].read_text(encoding="utf-8")
        assert "## 8. 数据源健康与空报告处理" in markdown
        assert "broken_source" in markdown
