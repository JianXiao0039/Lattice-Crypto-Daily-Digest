from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.audit import audit_payload, stable_id, write_audit


def _record(
    title: str,
    *,
    source: str = "iacr_eprint",
    url: str = "https://example.test/paper",
    priority_label: str = "可略读",
    score: int = 55,
    **extra: object,
) -> dict[str, object]:
    record = {
        "title": title,
        "source": source,
        "url": url,
        "reading_priority_score": score,
        "priority_label": priority_label,
        "reason_for_priority": "测试原因",
    }
    record.update(extra)
    return record


def _payload(records: list[dict[str, object]], *, collector: str, quality: str, health: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "metadata": {
            "target_date": "2026-05-29",
            "run_date": "2026-05-29",
            "collector": collector,
            "quality_status": quality,
        },
        "records": records,
        "source_health": health or [],
    }


def test_stable_id_prefers_doi_arxiv_and_title_hash() -> None:
    assert stable_id(_record("Paper A", doi="10.1000/ABC")) == "doi:10.1000/abc"
    assert stable_id(_record("Paper A", arxiv_id="2601.12345")) == "arxiv:2601.12345"
    first = stable_id(_record("A  LWE: Attack!", url=""))
    second = stable_id(_record("a lwe attack", url=""))

    assert first == second
    assert first.startswith("url:") is False
    assert first.startswith("title_hash:")


def test_added_missing_high_priority_and_source_delta_counts() -> None:
    provisional = _payload(
        [
            _record("Common LWE", doi="10.1/common", priority_label="建议精读", score=80),
            _record("GitHub Only", doi="10.1/github", priority_label="可略读", score=55),
        ],
        collector="github_actions",
        quality="provisional",
        health=[
            {"source": "arxiv", "raw_count": 2, "date_filtered_count": 1, "final_count": 1, "health_status": "red"},
        ],
    )
    authoritative = _payload(
        [
            _record("Common LWE", doi="10.1/common", priority_label="建议精读", score=80),
            _record("Local Must Read", doi="10.1/local", priority_label="必须精读", score=92),
        ],
        collector="local_codex",
        quality="authoritative_backfill",
        health=[
            {"source": "arxiv", "raw_count": 5, "date_filtered_count": 3, "final_count": 2, "health_status": "green"},
        ],
    )

    result = audit_payload("2026-05-29", provisional, authoritative)

    assert result["counts"]["added_by_backfill_count"] == 1
    assert result["counts"]["missing_from_backfill_count"] == 1
    assert result["counts"]["high_priority_added_count"] == 1
    assert result["counts"]["high_priority_missing_count"] == 0
    arxiv = next(row for row in result["source_health_comparison"] if row["source"] == "arxiv")
    assert arxiv["delta_raw"] == 3
    assert arxiv["delta_date_filtered"] == 2
    assert arxiv["delta_final"] == 1
    assert arxiv["status_change"] == "red->green"
    assert result["quality_judgment"]["replacement_recommended"] is True


def test_provisional_missing_does_not_crash_and_writes_audit_outputs() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = root / "data"
        data_dir.mkdir()
        (data_dir / "2026-05-29.json").write_text(
            json.dumps(
                _payload([_record("Local Only", doi="10.1/local")], collector="local_codex", quality="authoritative_backfill"),
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        json_path, markdown_path, result = write_audit(root, "2026-05-29")

        assert json_path.exists()
        assert markdown_path.exists()
        assert result["metadata"]["provisional_available"] is False
        assert result["quality_judgment"]["replacement_recommended"] is True
        markdown = markdown_path.read_text(encoding="utf-8")
        for section in [
            "## 1. 审计结论",
            "## 2. 数量对比",
            "## 3. 本地回填新增论文",
            "## 4. GitHub provisional 独有论文",
            "## 5. 高优先级差异",
            "## 6. Source Health 差异",
            "## 7. 风险与处理建议",
        ]:
            assert section in markdown
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert "quality_judgment" in payload
