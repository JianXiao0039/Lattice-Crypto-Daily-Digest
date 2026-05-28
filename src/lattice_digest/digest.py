from __future__ import annotations

from collections import defaultdict
from datetime import date

from lattice_digest.models import PaperRecord


def _record_link(record: PaperRecord) -> str:
    if record.pdf_url:
        return f"[来源]({record.source_url}) / [PDF]({record.pdf_url})"
    return f"[来源]({record.source_url})"


def _text(record: PaperRecord) -> str:
    return " ".join(
        [
            record.title,
            record.abstract,
            " ".join(record.taxonomy_tags),
            " ".join(record.keywords_matched),
        ]
    ).lower()


def _relation(record: PaperRecord, terms: tuple[str, ...]) -> str:
    text = _text(record)
    matched = [term for term in terms if term.lower() in text]
    if matched:
        return "强相关：" + ", ".join(dict.fromkeys(matched))
    return "弱相关"


def _summary(record: PaperRecord) -> str:
    if record.abstract:
        compact = " ".join(record.abstract.split())
        return compact[:180] + ("..." if len(compact) > 180 else "")
    keywords = "、".join(record.keywords_matched[:5]) if record.keywords_matched else "格密码相关关键词"
    return f"来源元数据未提供摘要；当前仅能确认该条目命中 {keywords}，分类依据主要来自题名、来源和可验证元数据。"


def _why_it_matters(record: PaperRecord) -> str:
    if record.reason:
        return record.reason
    return "该条目具有可验证来源，并命中格密码/PQC 相关分类规则。"


def _reading_strategy(record: PaperRecord) -> str:
    if record.relevance_label == "A":
        return "先读摘要、问题定义和主要定理，再检查参数、实验或攻击成本是否影响现有研究假设。"
    if record.relevance_label == "B":
        return "先确认与具体 lattice scheme 或部署场景的关系，再决定是否深入正文。"
    return "保留为背景材料，优先阅读引言和相关工作。"


def _append_paper(lines: list[str], record: PaperRecord, index: int, include_relations: bool) -> None:
    lines.append(f"### {index}. {record.title}")
    lines.append(f"- Paper ID：{record.paper_id or 'unknown'}")
    lines.append(f"- 中文标题翻译：{record.chinese_title or 'unknown'}")
    lines.append(f"- Original title：{record.title}")
    lines.append(f"- Authors：{', '.join(record.authors) if record.authors else 'unknown'}")
    lines.append(f"- Source：{record.source}")
    lines.append(f"- Venue：{record.venue or 'unknown'}")
    lines.append(f"- URL：{record.source_url}")
    lines.append(f"- PDF URL：{record.pdf_url or 'unknown'}")
    lines.append(f"- arXiv ID：{record.arxiv_id or 'unknown'}")
    lines.append(f"- ePrint ID：{record.eprint_id or 'unknown'}")
    lines.append(f"- DOI：{record.doi or 'unknown'}")
    lines.append(f"- Publication date：{record.publication_date or 'unknown'}")
    lines.append(f"- Update date：{record.update_date or 'unknown'}")
    lines.append(f"- Relevance label：{record.relevance_label}")
    lines.append(f"- Relevance score：{record.relevance_score}")
    lines.append(f"- Reading priority：{record.reading_priority}")
    lines.append(f"- Taxonomy tags：{', '.join(record.taxonomy_tags) if record.taxonomy_tags else 'unknown'}")
    lines.append(f"- Matched keywords：{', '.join(record.keywords_matched) if record.keywords_matched else 'unknown'}")
    lines.append(
        f"- Negative keywords：{', '.join(record.negative_keywords_matched) if record.negative_keywords_matched else '无'}"
    )
    lines.append(f"- 中文摘要：{_summary(record)}")
    lines.append(f"- Why it matters：{_why_it_matters(record)}")
    lines.append(f"- Suggested reading strategy：{_reading_strategy(record)}")
    if include_relations:
        lines.append("- 与研究方向的关系：")
        lines.append(f"  - LWE/RLWE/MLWE：{_relation(record, ('LWE', 'RLWE', 'Ring-LWE', 'MLWE', 'Module-LWE'))}")
        lines.append(f"  - SIS/NTRU：{_relation(record, ('SIS', 'Ring-SIS', 'NTRU'))}")
        lines.append(f"  - BKZ/G6K/fplll：{_relation(record, ('BKZ', 'G6K', 'fplll', 'lattice reduction'))}")
        lines.append(f"  - ML-KEM/Kyber：{_relation(record, ('ML-KEM', 'Kyber'))}")
        lines.append(f"  - ML-DSA/Dilithium：{_relation(record, ('ML-DSA', 'Dilithium'))}")
        lines.append(f"  - Falcon/FN-DSA：{_relation(record, ('Falcon', 'FN-DSA'))}")
        lines.append(f"  - FHE/CKKS/BFV/BGV/TFHE：{_relation(record, ('FHE', 'CKKS', 'BFV', 'BGV', 'TFHE'))}")
        lines.append(
            f"  - implementation / side-channel / fault attacks："
            f"{_relation(record, ('implementation', 'side-channel', 'fault', 'NTT', 'masking'))}"
        )
        lines.append(
            f"  - AI-assisted lattice cryptanalysis："
            f"{_relation(record, ('AI', 'machine learning', 'neural', 'Transformer', 'learned'))}"
        )
    lines.append("")


def _source_health_lines(source_health: list[dict[str, object]] | None) -> list[str]:
    lines = ["## Source Health", ""]
    if not source_health:
        lines.extend(["暂无 source health 数据。", ""])
        return lines

    lines.append("| Source | Raw | Normalized | Date Filtered | Deduped | Relevance Filtered | Threshold | Final | Warnings | Errors |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for item in source_health:
        warnings = item.get("warnings") if isinstance(item.get("warnings"), list) else []
        errors = item.get("errors") if isinstance(item.get("errors"), list) else []
        lines.append(
            "| {source} | {raw} | {normalized} | {date_filtered} | {deduped} | {relevance} | {threshold} | {final} | {warnings} | {errors} |".format(
                source=item.get("source", "unknown"),
                raw=item.get("raw_candidates", 0),
                normalized=item.get("normalized_candidates", 0),
                date_filtered=item.get("date_filtered_candidates", 0),
                deduped=item.get("deduped_candidates", 0),
                relevance=item.get("relevance_filtered_candidates", 0),
                threshold=item.get("scoring_threshold_candidates", 0),
                final=item.get("final_records", 0),
                warnings=len(warnings),
                errors=len(errors),
            )
        )
    lines.append("")

    for item in source_health:
        source = item.get("source", "unknown")
        warnings = item.get("warnings") if isinstance(item.get("warnings"), list) else []
        errors = item.get("errors") if isinstance(item.get("errors"), list) else []
        for warning in warnings:
            lines.append(f"- {source} warning: {warning}")
        for error in errors:
            lines.append(f"- {source} error: {error}")
    lines.append("")
    return lines


def generate_markdown(
    records: list[PaperRecord],
    digest_date: date,
    filtered_count: int = 0,
    source_health: list[dict[str, object]] | None = None,
) -> str:
    included = [record for record in records if record.relevance_label in {"A", "B", "C"}]
    grouped: dict[str, list[PaperRecord]] = defaultdict(list)
    for record in included:
        grouped[record.relevance_label].append(record)
    a_count = len(grouped["A"])
    b_count = len(grouped["B"])
    c_count = len(grouped["C"])
    lines: list[str] = [
        f"# 格密码相关论文每日推送（{digest_date.isoformat()}）",
        "",
        "## 今日结论",
        "",
        f"今日 A/B/C 类论文数量：A={a_count}，B={b_count}，C={c_count}；过滤或降为 D 类 {filtered_count} 篇。",
    ]
    if a_count + b_count == 0:
        lines.append("今日无强相关格密码论文。")
    if not included:
        lines.append("今日未发现值得记录的格密码相关新论文。")
    lines.append("")

    lines.extend(["## A 类：今日必读格密码论文", ""])
    if grouped["A"]:
        for index, record in enumerate(grouped["A"], start=1):
            _append_paper(lines, record, index, include_relations=True)
    else:
        lines.extend(["今日无 A 类必读格密码论文。", ""])

    lines.extend(["## B 类：值得跟踪论文", ""])
    if grouped["B"]:
        for index, record in enumerate(grouped["B"], start=1):
            _append_paper(lines, record, index, include_relations=True)
    else:
        lines.extend(["今日无 B 类值得跟踪论文。", ""])

    lines.extend(["## C 类：可选关注 / 背景启发", ""])
    if grouped["C"]:
        for index, record in enumerate(grouped["C"], start=1):
            _append_paper(lines, record, index, include_relations=False)
    else:
        lines.extend(["今日无 C 类背景启发论文。", ""])

    lines.extend(["## D 类过滤说明", ""])
    lines.append(f"今日过滤或降为 D 类 {filtered_count} 条；系统继续排除非密码学 lattice、无可靠 URL/source、以及缺少密码学上下文的 SIS/lattice 误报。")
    lines.append("")

    lines.extend(["## 今日统计", ""])
    lines.append(f"- A 类：{a_count}")
    lines.append(f"- B 类：{b_count}")
    lines.append(f"- C 类：{c_count}")
    lines.append(f"- D 类/过滤：{filtered_count}")
    lines.append("")

    lines.extend(["## 明日跟踪建议", ""])
    lines.append("继续优先检查 IACR ePrint、arXiv cs.CR/math.NT/cs.IT、OpenAlex、Crossref 与 Semantic Scholar 中更新的 LWE/SIS/NTRU/BKZ/FHE/PQC 条目；对只有年份或缺少更新时间的外部搜索结果保持保守过滤。")
    lines.append("")

    lines.extend(["## 今日一句话总结", ""])
    if a_count + b_count:
        top_titles = "；".join(record.title for record in (grouped["A"] + grouped["B"])[:3])
        lines.append(f"今日最值得跟踪的是：{top_titles}。")
    elif c_count:
        lines.append("今日无 A/B 类强相关格密码论文，仅保留少量 C 类背景线索。")
    else:
        lines.append("今日未发现值得记录的格密码相关新论文。")
    lines.append("")
    lines.extend(_source_health_lines(source_health))
    return "\n".join(lines)
