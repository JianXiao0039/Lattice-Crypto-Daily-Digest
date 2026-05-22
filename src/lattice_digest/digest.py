from __future__ import annotations

from collections import defaultdict
from datetime import date

from lattice_digest.models import PaperRecord


def _record_link(record: PaperRecord) -> str:
    if record.pdf_url:
        return f"[来源]({record.source_url}) / [PDF]({record.pdf_url})"
    return f"[来源]({record.source_url})"


def generate_markdown(records: list[PaperRecord], digest_date: date, filtered_count: int = 0) -> str:
    included = [record for record in records if record.relevance_label in {"A", "B", "C"}]
    lines: list[str] = [
        f"# 格密码相关论文每日推送（{digest_date.isoformat()}）",
        "",
        f"今日入选 {len(included)} 篇；过滤或降为 D 类 {filtered_count} 篇。",
        "",
    ]
    if not included:
        lines.extend([
            "今天未发现满足规则的格密码强相关新论文。",
            "",
            "说明：系统不会为了凑数量纳入只有 `lattice` 字样但缺少密码学上下文的论文。",
            "",
        ])
        return "\n".join(lines)

    grouped: dict[str, list[PaperRecord]] = defaultdict(list)
    for record in included:
        grouped[record.relevance_label].append(record)

    headings = {
        "A": "A 类：优先阅读",
        "B": "B 类：值得关注",
        "C": "C 类：按需跟进",
    }
    for label in ("A", "B", "C"):
        if not grouped.get(label):
            continue
        lines.extend([f"## {headings[label]}", ""])
        for index, record in enumerate(grouped[label], start=1):
            title = record.chinese_title or record.title
            lines.append(f"### {index}. {title}")
            if title != record.title:
                lines.append(f"- 原题：{record.title}")
            lines.append(f"- 作者：{', '.join(record.authors) if record.authors else '未知'}")
            lines.append(f"- 来源：{record.source}；{_record_link(record)}")
            if record.venue or record.publication_date:
                lines.append(f"- 时间/ venue：{record.publication_date or '未知'}；{record.venue or '未知'}")
            lines.append(f"- 分类：{record.relevance_label}；分数：{record.relevance_score}；阅读优先级：{record.reading_priority}")
            if record.taxonomy_tags:
                lines.append(f"- Taxonomy：{', '.join(record.taxonomy_tags)}")
            if record.keywords_matched:
                lines.append(f"- 命中关键词：{', '.join(record.keywords_matched)}")
            lines.append(f"- 入选理由：{record.reason or '命中格密码相关规则'}")
            if record.abstract:
                abstract = record.abstract[:500] + ("..." if len(record.abstract) > 500 else "")
                lines.append(f"- 摘要摘录：{abstract}")
            lines.append("")
    return "\n".join(lines)

