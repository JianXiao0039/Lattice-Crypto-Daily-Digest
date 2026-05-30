from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from lattice_digest.export_library import (
    SECRET_PATTERNS,
    clean_text,
    filter_items,
    load_library_items,
)


TAG_CATEGORIES = (
    "research_tags",
    "lattice_tags",
    "pqc_tags",
    "ai_tags",
    "attack_tags",
    "primitive_tags",
    "implementation_tags",
    "zotero_tags",
)


@dataclass(frozen=True)
class LibraryAuditResult:
    items: list[dict[str, Any]]
    output_dir: Path
    written_paths: list[Path]
    dry_run: bool = False


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [clean_text(item) for item in value if clean_text(item)]
    if isinstance(value, str) and value.strip():
        return [clean_text(value)]
    return []


def _split_csv(values: Iterable[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        for part in str(value).split(","):
            cleaned = clean_text(part)
            if cleaned:
                result.append(cleaned)
    return list(dict.fromkeys(result))


def _load_library_items_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [dict(item) for item in payload["items"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    return []


def load_audit_items(
    input_path: Path,
    *,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[dict[str, Any]]:
    if input_path.is_file() and input_path.name == "library-items.json":
        return _load_library_items_json(input_path)
    if input_path.is_file() and input_path.suffix == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "items" in payload:
            return _load_library_items_json(input_path)
    return load_library_items(input_path, from_date=from_date, to_date=to_date, dedup=True)


def _tag_counts(items: list[dict[str, Any]], key: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for item in items:
        counter.update(_as_list(item.get(key)))
    return counter


def _has_any(item: dict[str, Any], key: str, tags: Iterable[str]) -> bool:
    available = set(_as_list(item.get(key)))
    return bool(available & set(tags))


def _text(item: dict[str, Any]) -> str:
    fields = [
        item.get("title"),
        item.get("abstract"),
        item.get("reason_for_priority"),
        item.get("why_it_matters"),
        " ".join(_as_list(item.get("research_tags"))),
        " ".join(_as_list(item.get("lattice_tags"))),
        " ".join(_as_list(item.get("pqc_tags"))),
        " ".join(_as_list(item.get("ai_tags"))),
        " ".join(_as_list(item.get("attack_tags"))),
        " ".join(_as_list(item.get("primitive_tags"))),
        " ".join(_as_list(item.get("implementation_tags"))),
    ]
    return " ".join(clean_text(value).lower() for value in fields)


def _brief(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_id": item.get("item_id"),
        "title": item.get("title"),
        "source": item.get("source"),
        "url": item.get("url"),
        "reading_priority_score": item.get("reading_priority_score"),
        "priority_label": item.get("priority_label"),
        "tags": {
            "lattice_tags": _as_list(item.get("lattice_tags")),
            "pqc_tags": _as_list(item.get("pqc_tags")),
            "ai_tags": _as_list(item.get("ai_tags")),
            "attack_tags": _as_list(item.get("attack_tags")),
            "primitive_tags": _as_list(item.get("primitive_tags")),
            "implementation_tags": _as_list(item.get("implementation_tags")),
        },
    }


def field_quality_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total_items": len(items),
        "missing_authors": sum(1 for item in items if not _as_list(item.get("authors"))),
        "missing_doi": sum(1 for item in items if not clean_text(item.get("doi"))),
        "missing_url": sum(1 for item in items if not clean_text(item.get("url"))),
        "missing_abstract": sum(1 for item in items if not clean_text(item.get("abstract"))),
        "missing_date_or_year": sum(1 for item in items if not item.get("year") and not clean_text(item.get("date"))),
        "missing_source": sum(1 for item in items if not clean_text(item.get("source"))),
        "missing_priority": sum(1 for item in items if item.get("reading_priority_score") in (None, "") and not clean_text(item.get("priority_label"))),
    }


def build_confusion_report(items: list[dict[str, Any]]) -> dict[str, Any]:
    counts_by_tag_category = {key: dict(_tag_counts(items, key)) for key in TAG_CATEGORIES}
    ai_candidates = [item for item in items if _as_list(item.get("ai_tags"))]
    attack_candidates = [item for item in items if _as_list(item.get("attack_tags"))]
    fhe_candidates = [item for item in items if _has_any(item, "primitive_tags", {"FHE", "CKKS", "BFV", "BGV", "TFHE"})]

    possible_ai_fp = [
        _brief(item)
        for item in ai_candidates
        if not any(term in _text(item) for term in ("lwe", "rlwe", "mlwe", "sis", "bkz", "lattice", "cryptanalysis"))
    ]
    possible_attack_fp = [
        _brief(item)
        for item in attack_candidates
        if not any(term in _text(item) for term in ("lwe", "rlwe", "mlwe", "sis", "bkz", "lattice", "cryptanalysis", "ntru"))
    ]
    possible_fhe_over = [
        _brief(item)
        for item in fhe_candidates
        if not any(term in _text(item) for term in ("security", "attack", "parameter", "implementation", "benchmark", "bootstrapping"))
    ]

    lattice_counts = _tag_counts(items, "lattice_tags")
    pqc_counts = _tag_counts(items, "pqc_tags")
    attack_counts = _tag_counts(items, "attack_tags")
    primitive_counts = _tag_counts(items, "primitive_tags")
    return {
        "metadata": {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_items": len(items),
        },
        "counts_by_tag_category": counts_by_tag_category,
        "possible_ai4lattice_false_positives": possible_ai_fp,
        "possible_attack_false_positives": possible_attack_fp,
        "possible_fhe_overclassification": possible_fhe_over,
        "lwe_rlwe_mlwe_distribution": {
            "LWE": lattice_counts.get("LWE", 0),
            "Ring-LWE": lattice_counts.get("Ring-LWE", 0),
            "Module-LWE": lattice_counts.get("Module-LWE", 0),
            "Sparse LWE": lattice_counts.get("Sparse LWE", 0),
            "Binary Secret LWE": lattice_counts.get("Binary Secret LWE", 0),
            "Ternary Secret LWE": lattice_counts.get("Ternary Secret LWE", 0),
        },
        "sis_module_sis_ring_sis_distribution": {
            "SIS": lattice_counts.get("SIS", 0),
            "Module-SIS": lattice_counts.get("Module-SIS", 0),
            "Ring-SIS": lattice_counts.get("Ring-SIS", 0),
        },
        "pqc_scheme_distribution": dict(pqc_counts),
        "attack_distribution": dict(attack_counts),
        "primitive_distribution": dict(primitive_counts),
        "module_sis_chameleon_hash_candidates": [
            _brief(item)
            for item in items
            if _has_any(item, "lattice_tags", {"Module-SIS"}) and _has_any(item, "primitive_tags", {"Chameleon Hash", "Module-SIS Chameleon Hash"})
        ],
        "ai4lattice_candidates": [_brief(item) for item in ai_candidates],
        "implementation_security_candidates": [
            _brief(item) for item in items if "Implementation Security" in _as_list(item.get("research_tags"))
        ],
        "zkpq_privacy_candidates": [
            _brief(item)
            for item in items
            if "ZK-friendly PQ Privacy" in _as_list(item.get("research_tags")) or _has_any(item, "primitive_tags", {"ZK-Friendly", "Lattice-Based ZK"})
        ],
        "field_quality_summary": field_quality_summary(items),
    }


def _candidate_lines(items: list[dict[str, Any]], limit: int = 20, *, include_risk: bool = False) -> list[str]:
    if not items:
        return ["- 无"]
    lines: list[str] = []
    for item in items[:limit]:
        risk = "；可能风险：需要人工核验标签上下文" if include_risk else ""
        reason = clean_text(item.get("reason_for_priority") or item.get("why_it_matters"))
        reason_part = f"；reason：{reason}" if reason else ""
        lines.append(
            f"- {item.get('title') or 'Untitled'}：{item.get('reading_priority_score', 0)} / "
            f"{item.get('priority_label') or 'unknown'}；source：{item.get('source') or 'unknown'}{reason_part}{risk}"
        )
    return lines


def render_tag_quality_report(items: list[dict[str, Any]], confusion: dict[str, Any]) -> str:
    lines = ["# Library Export Tag Quality Report", ""]
    tagged_count = sum(
        1
        for item in items
        if any(_as_list(item.get(key)) for key in ("research_tags", "lattice_tags", "pqc_tags", "ai_tags", "attack_tags", "primitive_tags", "implementation_tags"))
    )
    high_priority_count = sum(1 for item in items if int(item.get("reading_priority_score") or 0) >= 70)
    todo_verify_count = sum(1 for item in items if "TODO_VERIFY" in _as_list(item.get("export_warnings")) or "TODO_VERIFY" in _as_list(item.get("research_tags")))
    lines.extend(
        [
            "## 1. 标签审计摘要",
            "",
            f"- 总条目数：{len(items)}",
            f"- 有标签条目数：{tagged_count}",
            f"- 无标签条目数：{len(items) - tagged_count}",
            f"- 高优先级条目数：{high_priority_count}",
            f"- TODO_VERIFY 条目数：{todo_verify_count}",
            "",
            "## 2. 标签分布",
            "",
        ]
    )
    for key in TAG_CATEGORIES:
        lines.append(f"### {key}")
        counts = _tag_counts(items, key).most_common(20)
        lines.extend([f"- {tag}: {count}" for tag, count in counts] or ["- 无"])
        lines.append("")

    lines.extend(["## 3. AI4Lattice 候选", ""])
    lines.extend(_candidate_lines(confusion["ai4lattice_candidates"], include_risk=True))
    lines.extend(["", "## 4. 可能 AI4Lattice 误报", ""])
    lines.extend(_candidate_lines(confusion["possible_ai4lattice_false_positives"], include_risk=True))
    lines.extend(["", "## 5. Module-SIS / Chameleon Hash 候选", ""])
    lines.extend(_candidate_lines(confusion["module_sis_chameleon_hash_candidates"]))
    lines.extend(["", "## 6. Lattice Reduction / BKZ 候选", ""])
    lines.extend(_candidate_lines([item for item in items if _has_any(item, "lattice_tags", {"BKZ", "G6K", "fplll", "LLL"})]))
    lines.extend(["", "## 7. 可能 Attack 标签误报", ""])
    lines.extend(_candidate_lines(confusion["possible_attack_false_positives"], include_risk=True))
    lines.extend(["", "## 8. FHE 分类检查", ""])
    fhe_items = [item for item in items if _has_any(item, "primitive_tags", {"FHE", "CKKS", "BFV", "BGV", "TFHE"})]
    if fhe_items:
        for item in fhe_items:
            text = _text(item)
            if any(term in text for term in ("attack", "security", "parameter")):
                kind = "FHE security / attack / parameter"
            elif any(term in text for term in ("implementation", "benchmark", "ntt", "constant-time")):
                kind = "FHE implementation"
            elif any(term in text for term in ("construction", "scheme", "bootstrapping")):
                kind = "FHE theory / construction"
            else:
                kind = "FHE application-only"
            lines.append(f"- {item.get('title') or 'Untitled'}：{kind}；{item.get('reading_priority_score', 0)} / {item.get('priority_label') or 'unknown'}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 9. Implementation Security 候选", ""])
    lines.extend(_candidate_lines(confusion["implementation_security_candidates"]))
    lines.extend(["", "## 10. ZK-friendly PQ Privacy 候选", ""])
    lines.extend(_candidate_lines(confusion["zkpq_privacy_candidates"]))
    lines.append("")
    return "\n".join(lines)


def render_field_quality_report(items: list[dict[str, Any]]) -> str:
    titles = [clean_text(item.get("title")).lower() for item in items if clean_text(item.get("title"))]
    urls = [clean_text(item.get("url")).lower() for item in items if clean_text(item.get("url"))]
    title_counts = Counter(titles)
    url_counts = Counter(urls)
    source_counts = Counter(clean_text(item.get("source")) or "unknown" for item in items)
    priority_counts = Counter(clean_text(item.get("priority_label")) or "unknown" for item in items)
    summary = field_quality_summary(items)

    def missing_lines(predicate) -> list[str]:
        missing = [item for item in items if predicate(item)]
        return _candidate_lines(missing, limit=50)

    lines = [
        "# Library Export Field Quality Report",
        "",
        "## 1. 字段完整性摘要",
        "",
        f"- 总条目数：{summary['total_items']}",
        f"- 缺作者数量：{summary['missing_authors']}",
        f"- 缺 DOI 数量：{summary['missing_doi']}",
        f"- 缺 URL 数量：{summary['missing_url']}",
        f"- 缺摘要数量：{summary['missing_abstract']}",
        f"- 缺日期/年份数量：{summary['missing_date_or_year']}",
        f"- 缺 source 数量：{summary['missing_source']}",
        f"- 缺 priority 数量：{summary['missing_priority']}",
        "",
        "## 2. 缺作者条目",
        "",
        *missing_lines(lambda item: not _as_list(item.get("authors"))),
        "",
        "## 3. 缺 DOI 条目",
        "",
        *missing_lines(lambda item: not clean_text(item.get("doi"))),
        "",
        "## 4. 缺 URL 条目",
        "",
        *missing_lines(lambda item: not clean_text(item.get("url"))),
        "",
        "## 5. 缺摘要条目",
        "",
        *missing_lines(lambda item: not clean_text(item.get("abstract"))),
        "",
        "## 6. 重复标题候选",
        "",
    ]
    duplicate_titles = [(title, count) for title, count in title_counts.items() if count > 1]
    lines.extend([f"- {title}: {count}" for title, count in duplicate_titles] or ["- 无"])
    lines.extend(["", "## 7. 重复 URL 候选", ""])
    duplicate_urls = [(url, count) for url, count in url_counts.items() if count > 1]
    lines.extend([f"- {url}: {count}" for url, count in duplicate_urls] or ["- 无"])
    lines.extend(["", "## 8. Source 分布", ""])
    lines.extend([f"- {source}: {count}" for source, count in source_counts.most_common()] or ["- 无"])
    lines.extend(["", "## 9. Priority 分布", ""])
    lines.extend([f"- {priority}: {count}" for priority, count in priority_counts.most_common()] or ["- 无"])
    lines.extend(
        [
            "",
            "## 10. Zotero 导入风险",
            "",
            "- 缺作者、缺年份或缺 URL 的条目需要导入后人工修复。",
            "- 缺 DOI 不代表错误，但会影响 Zotero 去重和引用质量。",
            "- 标签过多时应优先保留研究主线标签，删除噪声标签。",
            "- `TODO_VERIFY` 只表示需要核验，不表示结论已经成立。",
        ]
    )
    lines.append("")
    return "\n".join(lines)


def render_zotero_import_checklist() -> str:
    return """# Zotero Manual Import Checklist

## 1. 推荐导入顺序

1. CSL JSON：`library-items.csl.json`。
2. BibTeX：`library-items.bib`。
3. RIS：`library-items.ris`。

## 2. 导入前检查

- 是否已生成 `library-items.csl.json`。
- 是否已生成 `library-items.bib`。
- 是否已生成 `library-items.ris`。
- 是否已清楚这是 file-based manual import，不是 Zotero XPI plugin。

## 3. Zotero 中需要人工检查的字段

- 检查 title 是否完整。
- 检查 authors 是否缺失或顺序异常。
- 检查 year / date 是否正确。
- 检查 DOI 是否存在且没有重复。
- 检查 URL 是否能打开。
- 检查 abstract 是否缺失。
- 检查 tags 是否过多。
- 检查 note 是否包含 source、priority、score 和 research tags。

## 4. 推荐 Zotero collection 结构

- Lattice Problems
- Lattice Reduction
- Lattice Cryptanalysis
- PQC Standards
- Lattice Primitives
- Implementation Security
- AI4Lattice
- FHE
- ZK/PQ Privacy
- Short-Term Paper Candidates
- PhD Long-Term Direction

## 5. 导入后不要做什么

- 不要盲目全量保留 tags。
- 不要把 TODO_VERIFY 当作已验证结论。
- 不要把 toy benchmark 当真实安全结论。
- 不要把 GitHub Actions provisional 结果当作最高质量结果。
"""


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _assert_clean_output(text: str) -> None:
    markers = ("<", "contentReference", "oaicite", "id=")
    for marker in markers:
        if marker in text:
            raise ValueError(f"Audit output contains forbidden marker: {marker}")
    for pattern in SECRET_PATTERNS:
        # SECRET_PATTERNS are regex strings from export_library; use a simple
        # substring check for the public prefixes that matter in generated text.
        prefix = pattern.split("[", 1)[0].replace("\\", "")
        if prefix and prefix in text:
            raise ValueError(f"Audit output contains secret-like pattern: {prefix}")


def write_audit_reports(items: list[dict[str, Any]], output_dir: Path, *, formats: str = "all") -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    confusion = build_confusion_report(items)
    selected = set(_split_csv([formats or "all"]))
    if "all" in selected:
        selected = {"markdown", "json"}
    written: list[Path] = []
    if "json" in selected:
        path = output_dir / "taxonomy-confusion-report.json"
        _write_json(path, confusion)
        written.append(path)
    if "markdown" in selected:
        reports = {
            output_dir / "tag-quality-report.md": render_tag_quality_report(items, confusion),
            output_dir / "field-quality-report.md": render_field_quality_report(items),
            output_dir / "zotero-import-checklist.md": render_zotero_import_checklist(),
        }
        for path, content in reports.items():
            _assert_clean_output(content)
            path.write_text(content, encoding="utf-8")
            written.append(path)
    return written


def audit_library_export(
    input_path: Path,
    output_dir: Path,
    *,
    from_date: str | None = None,
    to_date: str | None = None,
    min_priority_score: int = 0,
    tags: Iterable[str] = (),
    sources: Iterable[str] = (),
    formats: str = "all",
    dry_run: bool = False,
) -> LibraryAuditResult:
    items = load_audit_items(input_path, from_date=from_date, to_date=to_date)
    items = filter_items(
        items,
        min_priority_score=min_priority_score,
        tags=_split_csv(tags),
        sources=_split_csv(sources),
    )
    if dry_run:
        return LibraryAuditResult(items=items, output_dir=output_dir, written_paths=[], dry_run=True)
    written = write_audit_reports(items, output_dir, formats=formats)
    return LibraryAuditResult(items=items, output_dir=output_dir, written_paths=written)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit stable library export quality for Zotero/manual import.")
    parser.add_argument("--input", default="exports/library/library-items.json")
    parser.add_argument("--from-date", default=None)
    parser.add_argument("--to-date", default=None)
    parser.add_argument("--output-dir", default="audits/library-export")
    parser.add_argument("--min-priority-score", type=int, default=0)
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--format", default="all", help="markdown,json or all")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = audit_library_export(
        Path(args.input),
        Path(args.output_dir),
        from_date=args.from_date,
        to_date=args.to_date,
        min_priority_score=args.min_priority_score,
        tags=args.tag,
        sources=args.source,
        formats=args.format,
        dry_run=args.dry_run,
    )
    print(f"audit items: {len(result.items)}")
    print(f"output dir: {result.output_dir}")
    if result.dry_run:
        print("dry-run: no files written")
    else:
        for path in result.written_paths:
            print(f"wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
