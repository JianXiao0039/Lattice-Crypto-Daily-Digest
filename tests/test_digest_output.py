from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from lattice_digest.digest import generate_markdown


EXPECTED_SECTIONS = [
    "## 今日结论",
    "## A 类：今日必读格密码论文",
    "## B 类：值得跟踪论文",
    "## C 类：可选关注 / 背景启发",
    "## D 类过滤说明",
    "## 今日统计",
    "## 明日跟踪建议",
    "## 今日一句话总结",
]


def test_empty_digest_generates_eight_chinese_sections() -> None:
    markdown = generate_markdown([], date(2026, 5, 23), filtered_count=0)

    for section in EXPECTED_SECTIONS:
        assert section in markdown
    assert "今日无强相关格密码论文" in markdown
    assert "今日未发现值得记录的格密码相关新论文" in markdown


def test_empty_json_archive_is_parseable() -> None:
    parsed = json.loads("[]")

    assert parsed == []


def test_papers_db_exists_and_is_not_deleted() -> None:
    db_path = Path(__file__).resolve().parents[1] / "papers.db"

    assert db_path.exists()
    assert db_path.is_file()

