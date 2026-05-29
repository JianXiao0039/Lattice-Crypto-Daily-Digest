from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WINDOWS_ILLEGAL_CHARS = '<>:"/\\|?*'
FORBIDDEN_MARKERS = ("contentReference", "oaicite", "id=")

LINK_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("AI4Lattice", ("ai4lattice", "ai-assisted lattice", "neural cryptanalysis", "machine learning lwe")),
    ("Swin Transformer for LWE", ("swin transformer", "swin-guided")),
    ("LWE", ("lwe", "learning with errors")),
    ("RLWE", ("rlwe", "ring-lwe", "ring learning with errors")),
    ("MLWE", ("mlwe", "module-lwe", "module learning with errors")),
    ("Sparse LWE", ("sparse lwe",)),
    ("Dual Attack", ("dual attack", "dual attacks")),
    ("Primal Attack", ("primal attack", "primal attacks")),
    ("Hybrid Attack", ("hybrid attack", "hybrid attacks")),
    ("BKZ", ("bkz", "block korkine-zolotarev")),
    ("LLL", ("lll", "lenstra")),
    ("G6K", ("g6k",)),
    ("fplll", ("fplll",)),
    ("Module-SIS", ("module-sis", "msis")),
    ("Chameleon Hash", ("chameleon hash",)),
    ("Commitment", ("commitment", "commitments")),
    ("ML-KEM", ("ml-kem", "kyber", "crystals-kyber")),
    ("ML-DSA", ("ml-dsa", "dilithium", "crystals-dilithium")),
    ("FHE", ("fhe", "fully homomorphic encryption", "ckks", "bfv", "bgv", "tfhe", "bootstrapping")),
)


@dataclass(frozen=True)
class ExportResult:
    title: str
    path: Path
    dry_run: bool = False
    backed_up_to: Path | None = None


def load_digest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"digest JSON must be an object: {path}")
    return payload


def digest_date(payload: dict[str, Any], input_path: Path) -> str:
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        for key in ("target_date", "run_date"):
            value = str(metadata.get(key) or "").strip()
            if value:
                return value[:10]
    return input_path.stem


def short_hash(value: str, length: int = 8) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def safe_slug(title: str, max_length: int = 90) -> str:
    text = title.lower().strip()
    for char in WINDOWS_ILLEGAL_CHARS:
        text = text.replace(char, " ")
    text = re.sub(r"[\x00-\x1f]", " ", text)
    text = re.sub(r"[^\w\s.-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"[\s_.]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-. ")
    if not text:
        text = "untitled"
    if len(text) > max_length:
        suffix = short_hash(title)
        text = text[: max_length - len(suffix) - 1].rstrip("-") + "-" + suffix
    return text


def _yaml_quote(value: object) -> str:
    text = sanitize_text(str(value or ""))
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def sanitize_text(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"<[^>]+>", "", text)
    for marker in FORBIDDEN_MARKERS:
        text = text.replace(marker, "")
    return text.strip()


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [sanitize_text(item) for item in value if sanitize_text(item)]
    if isinstance(value, str) and value.strip():
        return [sanitize_text(value)]
    return []


def _record_score(record: dict[str, Any]) -> int:
    try:
        return int(record.get("reading_priority_score") or 0)
    except (TypeError, ValueError):
        return 0


def _record_label(record: dict[str, Any]) -> str:
    return sanitize_text(record.get("priority_label") or "")


def filter_records(
    records: list[dict[str, Any]],
    *,
    min_priority: int = 70,
    labels: set[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    selected = [
        record
        for record in records
        if _record_score(record) >= min_priority and (labels is None or _record_label(record) in labels)
    ]
    selected.sort(key=lambda record: (-_record_score(record), sanitize_text(record.get("title")).lower()))
    return selected[:limit] if limit is not None else selected


def candidate_links(record: dict[str, Any]) -> list[str]:
    fields = [
        record.get("title"),
        record.get("abstract"),
        record.get("reason_for_priority"),
        " ".join(_as_list(record.get("research_tags") or record.get("tags"))),
    ]
    text = " ".join(sanitize_text(field).lower() for field in fields)
    links: list[str] = []
    for link, terms in LINK_RULES:
        if any(term in text for term in terms):
            links.append(f"[[{link}]]")
    return links


def _frontmatter_list(values: list[str], fallback: list[str] | None = None) -> list[str]:
    actual = values or (fallback or [])
    return [f"  - {_yaml_quote(value)}" for value in actual]


def _research_line(record: dict[str, Any], links: list[str]) -> str:
    if not links:
        return "候选关联：暂无；需要阅读原文后手动判断。"
    return "候选关联：" + "、".join(links) + "。这些链接仅基于标题、摘要、标签和优先级原因推断，需要阅读原文确认。"


def render_card(record: dict[str, Any], source_digest_date: str, metadata: dict[str, Any]) -> str:
    title = sanitize_text(record.get("title") or "Untitled Paper")
    authors = _as_list(record.get("authors"))
    source = sanitize_text(record.get("source") or "")
    url = sanitize_text(record.get("url") or record.get("source_url") or "")
    published_date = sanitize_text(record.get("date") or record.get("publication_date") or record.get("update_date") or "")
    score = _record_score(record)
    label = _record_label(record)
    research_tags = _as_list(record.get("research_tags") or record.get("tags"))
    obsidian_tags = ["lattice_crypto", "TODO_CLASSIFY"]
    links = candidate_links(record)
    reason = sanitize_text(record.get("reason_for_priority") or "TODO_MANUAL：补充为什么值得读。")
    suggested_action = sanitize_text(record.get("suggested_action") or "TODO_MANUAL")
    hooks = _as_list(record.get("research_hooks"))
    questions = _as_list(record.get("advisor_questions"))
    abstract = sanitize_text(record.get("abstract"))

    lines: list[str] = [
        "---",
        "type: paper_card",
        "status: unread",
        f"source_digest_date: {_yaml_quote(source_digest_date)}",
        f"collector: {_yaml_quote(metadata.get('collector') or '')}",
        f"quality_status: {_yaml_quote(metadata.get('quality_status') or '')}",
        f"title: {_yaml_quote(title)}",
        "authors:",
        *_frontmatter_list(authors),
        f"source: {_yaml_quote(source)}",
        f"url: {_yaml_quote(url)}",
        f"published_date: {_yaml_quote(published_date)}",
        f"reading_priority_score: {score}",
        f"priority_label: {_yaml_quote(label)}",
        "tags:",
        *_frontmatter_list(obsidian_tags),
        "---",
        "",
        f"# {title}",
        "",
        "## 1. 基本信息",
        "",
        f"* 标题：{title}",
        f"* 作者：{', '.join(authors) if authors else 'unknown'}",
        f"* 来源：{source or 'unknown'}",
        f"* 日期：{published_date or 'unknown'}",
        f"* URL：{url or 'unknown'}",
        f"* Digest 日期：{source_digest_date}",
        f"* Collector：{sanitize_text(metadata.get('collector') or '')}",
        f"* Quality Status：{sanitize_text(metadata.get('quality_status') or '')}",
        "",
        "## 2. 为什么值得读",
        "",
        reason or "TODO_MANUAL：补充为什么值得读。",
        "",
        "## 3. 研究标签",
        "",
    ]
    if research_tags:
        lines.extend(f"* {tag}" for tag in research_tags)
    else:
        lines.append("* TODO_CLASSIFY")
    lines.extend(
        [
            "",
            "## 4. 与我的研究主线的关系",
            "",
            _research_line(record, links),
            "",
            "## 5. Suggested Action",
            "",
            suggested_action or "TODO_MANUAL",
            "",
            "## 6. Research Hooks",
            "",
        ]
    )
    lines.extend(f"* {hook}" for hook in hooks) if hooks else lines.append("* TODO_MANUAL：补充该论文可能启发的研究 idea。")
    lines.extend(["", "## 7. Advisor Questions", ""])
    lines.extend(f"* {question}" for question in questions) if questions else lines.append("* TODO_MANUAL：补充可问导师的问题。")
    lines.extend(["", "## 8. 摘要", ""])
    lines.append(abstract or "TODO_VERIFY：当前 digest 未提供摘要，需要打开原文核验。")
    lines.extend(
        [
            "",
            "## 9. 我的阅读笔记",
            "",
            "TODO_READ",
            "",
            "## 10. 可迁移到我课题的 idea",
            "",
            "TODO_IDEA",
            "",
            "## 11. 后续动作",
            "",
            "* [ ] 打开论文链接",
            "* [ ] 判断是否需要精读",
            "* [ ] 如果精读，整理成 paper_note",
            "* [ ] 如果有价值，加入组会候选",
            "* [ ] 如果和短期论文相关，加入 idea bank",
            "",
        ]
    )
    return "\n".join(lines)


def _unique_existing_path(path: Path) -> Path:
    if not path.exists():
        return path
    candidate = path.with_name(f"{path.stem}__new{path.suffix}")
    if not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}__new-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _unique_backup_path(path: Path, output_dir: Path, source_digest_date: str) -> Path:
    backup_dir = output_dir.parent / "backups" / source_digest_date
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"{path.stem}__backup{path.suffix}"
    if not backup.exists():
        return backup
    index = 2
    while True:
        candidate = backup_dir / f"{path.stem}__backup-{index}{path.suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _target_paths(records: list[dict[str, Any]], source_digest_date: str, dated_dir: Path) -> list[Path]:
    seen: dict[str, int] = {}
    paths: list[Path] = []
    for record in records:
        title = sanitize_text(record.get("title") or "untitled")
        slug = safe_slug(title)
        seen[slug] = seen.get(slug, 0) + 1
        if seen[slug] > 1:
            slug = f"{slug}-{short_hash(title + str(seen[slug]))}"
        paths.append(dated_dir / f"{source_digest_date}__{slug}.md")
    return paths


def export_cards(
    input_path: Path,
    output_dir: Path,
    *,
    min_priority: int = 70,
    labels: set[str] | None = None,
    force: bool = False,
    dry_run: bool = False,
    limit: int | None = None,
) -> list[ExportResult]:
    payload = load_digest(input_path)
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    records = payload.get("records") if isinstance(payload.get("records"), list) else []
    records = [record for record in records if isinstance(record, dict)]
    source_digest_date = digest_date(payload, input_path)
    selected = filter_records(records, min_priority=min_priority, labels=labels, limit=limit)
    dated_dir = output_dir / source_digest_date
    target_paths = _target_paths(selected, source_digest_date, dated_dir)

    results: list[ExportResult] = []
    if not dry_run:
        dated_dir.mkdir(parents=True, exist_ok=True)
    for record, base_path in zip(selected, target_paths, strict=True):
        target_path = base_path
        backed_up_to: Path | None = None
        if target_path.exists() and force:
            backed_up_to = _unique_backup_path(target_path, output_dir, source_digest_date)
            if not dry_run:
                shutil.copy2(target_path, backed_up_to)
        elif target_path.exists() and not force:
            target_path = _unique_existing_path(target_path)
        content = render_card(record, source_digest_date, metadata)
        if not dry_run:
            target_path.write_text(content, encoding="utf-8")
        results.append(ExportResult(title=sanitize_text(record.get("title") or "Untitled Paper"), path=target_path, dry_run=dry_run, backed_up_to=backed_up_to))
    return results


def _parse_labels(value: str | None) -> set[str] | None:
    if not value:
        return None
    labels = {item.strip() for item in value.split(",") if item.strip()}
    return labels or None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export digest records as Obsidian paper cards.")
    parser.add_argument("--input", required=True, type=Path, help="Digest JSON path, e.g. data/2026-05-29.json.")
    parser.add_argument("--output-dir", type=Path, default=Path("exports/obsidian/papers"))
    parser.add_argument("--min-priority", type=int, default=70)
    parser.add_argument("--labels", default=None, help="Comma-separated priority_label values.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing card files after backing them up.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned card paths without writing files.")
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    results = export_cards(
        args.input,
        args.output_dir,
        min_priority=args.min_priority,
        labels=_parse_labels(args.labels),
        force=args.force,
        dry_run=args.dry_run,
        limit=args.limit,
    )
    prefix = "DRY RUN: would export" if args.dry_run else "exported"
    print(f"{prefix} {len(results)} Obsidian paper card(s).")
    for result in results:
        suffix = f" (backup: {result.backed_up_to})" if result.backed_up_to else ""
        print(f"- {result.path}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
