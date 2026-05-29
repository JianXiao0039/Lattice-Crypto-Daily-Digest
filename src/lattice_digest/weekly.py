from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from lattice_digest.audit import stable_id
from lattice_digest.config import project_root
from lattice_digest.obsidian import sanitize_text


REQUIRED_SECTIONS = [
    "## 1. 本周核心结论",
    "## 2. 本周必须精读论文 Top 5",
    "## 3. AI4Lattice / LWE 攻击动向",
    "## 4. BKZ / 格基约简 / Hybrid Attack 动向",
    "## 5. Module-SIS / Commitment / Chameleon Hash 动向",
    "## 6. ML-KEM / ML-DSA 实现安全动向",
    "## 7. 可孵化论文 idea",
    "## 8. 下周阅读计划",
    "## 9. 可问导师的问题",
]


@dataclass(frozen=True)
class WeeklyBriefResult:
    week_label: str
    markdown_path: Path
    obsidian_path: Path
    record_count: int


def parse_week(value: str) -> tuple[date, date, str]:
    if "-W" not in value:
        raise ValueError("week must use ISO format YYYY-Www")
    year_text, week_text = value.split("-W", 1)
    year = int(year_text)
    week = int(week_text)
    start = date.fromisocalendar(year, week, 1)
    end = start + timedelta(days=6)
    return start, end, f"{year}-W{week:02d}"


def week_label_for_range(start: date) -> str:
    iso = start.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def date_range(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def _load_digest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _score(record: dict[str, Any]) -> int:
    try:
        return int(record.get("reading_priority_score") or record.get("relevance_score") or 0)
    except (TypeError, ValueError):
        return 0


def _record_date(payload: dict[str, Any], path: Path) -> str:
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        value = str(metadata.get("target_date") or metadata.get("run_date") or "").strip()
        if value:
            return value[:10]
    return path.stem


def collect_week_records(data_dir: Path, start: date, end: date) -> tuple[list[dict[str, Any]], list[Path]]:
    by_id: dict[str, dict[str, Any]] = {}
    files: list[Path] = []
    for day in date_range(start, end):
        path = data_dir / f"{day.isoformat()}.json"
        payload = _load_digest(path)
        if payload is None:
            continue
        files.append(path)
        digest_date = _record_date(payload, path)
        records = payload.get("records")
        if not isinstance(records, list):
            continue
        for raw in records:
            if not isinstance(raw, dict):
                continue
            record = dict(raw)
            record.setdefault("source_digest_dates", [])
            dates = record["source_digest_dates"]
            if isinstance(dates, list) and digest_date not in dates:
                dates.append(digest_date)
            key = stable_id(record)
            existing = by_id.get(key)
            if existing is None or _score(record) > _score(existing):
                if existing and isinstance(existing.get("source_digest_dates"), list):
                    merged_dates = sorted(set(existing["source_digest_dates"]) | set(record.get("source_digest_dates", [])))
                    record["source_digest_dates"] = merged_dates
                by_id[key] = record
            elif existing and isinstance(existing.get("source_digest_dates"), list):
                existing["source_digest_dates"] = sorted(set(existing["source_digest_dates"]) | set(record.get("source_digest_dates", [])))
    records = list(by_id.values())
    records.sort(key=lambda record: (-_score(record), sanitize_text(record.get("title")).lower()))
    return records, files


def _combined_text(record: dict[str, Any]) -> str:
    values = [
        record.get("title"),
        record.get("abstract"),
        record.get("reason_for_priority"),
        " ".join(str(item) for item in record.get("research_tags") or record.get("tags") or []),
    ]
    return " ".join(sanitize_text(value).lower() for value in values)


def _matches(record: dict[str, Any], terms: tuple[str, ...]) -> bool:
    text = _combined_text(record)
    return any(term in text for term in terms)


def _filter_topic(records: list[dict[str, Any]], terms: tuple[str, ...]) -> list[dict[str, Any]]:
    return [record for record in records if _matches(record, terms)]


def _paper_bullets(records: list[dict[str, Any]], empty_text: str, limit: int | None = None) -> list[str]:
    selected = records[:limit] if limit is not None else records
    if not selected:
        return [empty_text, ""]
    lines: list[str] = []
    for record in selected:
        title = sanitize_text(record.get("title") or "unknown")
        source = sanitize_text(record.get("source") or "unknown")
        url = sanitize_text(record.get("url") or record.get("source_url") or "")
        label = sanitize_text(record.get("priority_label") or "unknown")
        reason = sanitize_text(record.get("reason_for_priority") or "暂无 priority reason。")
        dates = record.get("source_digest_dates")
        date_text = "、".join(str(item) for item in dates) if isinstance(dates, list) else "unknown"
        link = f"，[link]({url})" if url else ""
        lines.append(f"- **{title}**（{source}，{_score(record)} / {label}，digest: {date_text}{link}）：{reason}")
    lines.append("")
    return lines


def _topic_names(records: list[dict[str, Any]]) -> list[str]:
    topics = [
        ("AI4Lattice", ("ai4lattice", "neural", "transformer", "machine learning lwe")),
        ("LWE/MLWE attacks", ("lwe", "mlwe", "dual attack", "primal attack", "hybrid attack")),
        ("BKZ/lattice reduction", ("bkz", "lll", "g6k", "fplll", "lattice reduction")),
        ("Module-SIS/commitment", ("module-sis", "commitment", "chameleon hash")),
        ("PQC implementation", ("ml-kem", "ml-dsa", "kyber", "dilithium", "side-channel", "fault")),
        ("FHE", ("fhe", "ckks", "bfv", "bgv", "tfhe", "bootstrapping")),
    ]
    matched = [name for name, terms in topics if any(_matches(record, terms) for record in records)]
    return matched[:5]


def _ideas(records: list[dict[str, Any]]) -> list[str]:
    hooks: list[str] = []
    for record in records:
        for hook in record.get("research_hooks") or []:
            text = sanitize_text(hook)
            if text and text not in hooks:
                hooks.append(text)
    if hooks:
        return [f"- {hook}" for hook in hooks[:6]]
    return [
        "- 围绕本周 Top papers 建一个参数估计 / attack interface 对照表。",
        "- 挑一篇 LWE/BKZ 论文做 1 周内可复现实验。",
        "- 将高优先级论文拆成组会 slides 的 motivation、method、risk 三段。",
    ]


def _advisor_questions(records: list[dict[str, Any]]) -> list[str]:
    questions: list[str] = []
    for record in records:
        for question in record.get("advisor_questions") or []:
            text = sanitize_text(question)
            if text and text not in questions:
                questions.append(text)
    if questions:
        return [f"{index}. {question}" for index, question in enumerate(questions[:8], start=1)]
    return [
        "1. 本周是否应该优先推进 AI-assisted lattice cryptanalysis，还是 Module-SIS 小原语？",
        "2. 哪篇论文最适合作为组会精读？",
        "3. 哪个方向最能服务 27fall PhD 申请研究主线？",
    ]


def render_weekly_brief(records: list[dict[str, Any]], start: date, end: date, week_label: str, files: list[Path]) -> str:
    must_read = [record for record in records if record.get("priority_label") == "必须精读"]
    recommended = [record for record in records if record.get("priority_label") == "建议精读"]
    topics = _topic_names(records)
    lines: list[str] = [
        f"# Weekly Research Brief - {week_label}",
        "",
        "## 1. 本周核心结论",
        "",
        f"- 日期范围：{start.isoformat()}..{end.isoformat()}",
        f"- 读取 digest JSON：{len(files)} 个",
        f"- 去重后论文数：{len(records)}",
        f"- 必须精读：{len(must_read)}",
        f"- 建议精读：{len(recommended)}",
        f"- 本周主要主题：{'、'.join(topics) if topics else '暂无明显主题'}",
        "",
        "## 2. 本周必须精读论文 Top 5",
        "",
    ]
    lines.extend(_paper_bullets(records, "本周没有达到精读阈值的论文。", limit=5))
    sections = [
        (
            "## 3. AI4Lattice / LWE 攻击动向",
            ("ai4lattice", "transformer lwe", "neural lattice", "machine learning lwe", "lwe", "dual attack", "primal attack"),
            "本周没有明显 AI4Lattice / LWE 攻击动向。",
        ),
        (
            "## 4. BKZ / 格基约简 / Hybrid Attack 动向",
            ("bkz", "lll", "g6k", "fplll", "lattice reduction", "hybrid attack", "sieving", "enumeration"),
            "本周没有明显 BKZ / 格基约简 / Hybrid Attack 动向。",
        ),
        (
            "## 5. Module-SIS / Commitment / Chameleon Hash 动向",
            ("module-sis", "msis", "commitment", "chameleon hash", "trapdoor", "rejection sampling"),
            "本周没有明显 Module-SIS / Commitment / Chameleon Hash 动向。",
        ),
        (
            "## 6. ML-KEM / ML-DSA 实现安全动向",
            ("ml-kem", "kyber", "ml-dsa", "dilithium", "falcon", "side-channel", "fault", "implementation"),
            "本周没有明显 ML-KEM / ML-DSA 实现安全动向。",
        ),
    ]
    for title, terms, empty in sections:
        lines.extend([title, ""])
        lines.extend(_paper_bullets(_filter_topic(records, terms), empty, limit=6))
    lines.extend(["## 7. 可孵化论文 idea", ""])
    lines.extend(_ideas(records))
    lines.extend(["", "## 8. 下周阅读计划", ""])
    if records:
        lines.extend(
            [
                "- Read Today：优先处理 Top 1-2 篇必须精读论文。",
                "- Read This Week：从建议精读中挑 3 篇补 related work。",
                "- Background：把可略读论文加入 citation bank。",
            ]
        )
    else:
        lines.append("- 本周没有可用记录；建议先运行 `python -m lattice_digest.run --since 7d --output markdown,json --send none`。")
    lines.extend(["", "## 9. 可问导师的问题", ""])
    lines.extend(_advisor_questions(records))
    lines.append("")
    return "\n".join(lines)


def write_weekly_brief(
    data_dir: Path,
    output_dir: Path,
    obsidian_output_dir: Path,
    start: date,
    end: date,
    week_label: str,
) -> WeeklyBriefResult:
    records, files = collect_week_records(data_dir, start, end)
    markdown = render_weekly_brief(records, start, end, week_label, files)
    output_dir.mkdir(parents=True, exist_ok=True)
    obsidian_output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / f"{week_label}.md"
    obsidian_path = obsidian_output_dir / f"{week_label}.md"
    markdown_path.write_text(markdown, encoding="utf-8")
    obsidian_path.write_text(markdown, encoding="utf-8")
    return WeeklyBriefResult(week_label, markdown_path, obsidian_path, len(records))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly lattice cryptography research brief.")
    parser.add_argument("--week", default=None, help="ISO week, e.g. 2026-W22.")
    parser.add_argument("--from-date", default=None)
    parser.add_argument("--to-date", default=None)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("exports/weekly"))
    parser.add_argument("--obsidian-output-dir", type=Path, default=Path("exports/obsidian/weekly"))
    parser.add_argument("--root", type=Path, default=None)
    return parser.parse_args(argv)


def _date_arg(value: str | None, name: str) -> date:
    if not value:
        raise SystemExit(f"{name} is required")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"invalid {name}: expected YYYY-MM-DD") from exc


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root or project_root()
    if args.week:
        start, end, week_label = parse_week(args.week)
    else:
        start = _date_arg(args.from_date, "--from-date")
        end = _date_arg(args.to_date, "--to-date")
        if end < start:
            raise SystemExit("--to-date must be greater than or equal to --from-date")
        week_label = week_label_for_range(start)
    data_dir = args.data_dir if args.data_dir.is_absolute() else root / args.data_dir
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    obsidian_output_dir = (
        args.obsidian_output_dir if args.obsidian_output_dir.is_absolute() else root / args.obsidian_output_dir
    )
    result = write_weekly_brief(data_dir, output_dir, obsidian_output_dir, start, end, week_label)
    print(f"Generated weekly brief with {result.record_count} unique record(s).")
    print(result.markdown_path)
    print(result.obsidian_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
