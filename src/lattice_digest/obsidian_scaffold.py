from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lattice_digest.reading_queue import DEFAULT_STATE_PATH, load_state, queue_sort_key, save_state


DEFAULT_OUTPUT_DIR = Path("exports") / "obsidian-paper-notes" / "Papers"
DEFAULT_READING_STATUSES = ("TODO_READ", "READING")
DEFAULT_REVIEW_STATUSES = ("TODO_VERIFY", "NEEDS_MATH_CHECK", "NEEDS_REPLICATION", "NEEDS_CODE_CHECK")
DEFAULT_PRIORITIES = ("HIGH", "MEDIUM")
SCHEMA_VERSION = 1
CREATED_BY = "lattice_digest.obsidian_scaffold"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_csv(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if not value:
        return default
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _clean(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("contentReference", "").replace("oaicite", "").replace("id=", "")
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())


def _yaml_scalar(value: object) -> str:
    text = _clean(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _yaml_list(name: str, values: list[str]) -> list[str]:
    lines = [f"{name}:"]
    if not values:
        lines.append("  []")
        return lines
    lines.extend(f"  - {_yaml_scalar(value)}" for value in values)
    return lines


def _stable_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted({str(value) for value in values if str(value)})


def _stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]


def slugify_title(title: str, *, max_length: int = 90) -> str:
    text = title.lower()
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", text)
    text = re.sub(r"[^\w\u4e00-\u9fff.-]+", " ", text, flags=re.UNICODE)
    text = "-".join(text.split())
    text = text.strip(".-")
    if not text:
        text = "untitled-paper"
    if len(text) > max_length:
        text = text[:max_length].rstrip(".-")
    return text or "untitled-paper"


def _note_base_slug(record: dict[str, Any]) -> str:
    return slugify_title(str(record.get("title") or "untitled-paper"))


def _note_hash(record: dict[str, Any]) -> str:
    return _stable_hash(str(record.get("dedup_key") or record.get("title") or "untitled-paper"))


def select_records(
    state: dict[str, Any],
    *,
    reading_statuses: tuple[str, ...] = DEFAULT_READING_STATUSES,
    review_statuses: tuple[str, ...] = DEFAULT_REVIEW_STATUSES,
    priorities: tuple[str, ...] = DEFAULT_PRIORITIES,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for record in state.get("records", []):
        if not isinstance(record, dict):
            continue
        if record.get("reading_status") not in reading_statuses:
            continue
        if record.get("review_status") not in review_statuses:
            continue
        if record.get("queue_priority") not in priorities:
            continue
        if record.get("reading_status") == "IGNORED" or record.get("review_status") == "NOT_RELEVANT":
            continue
        selected.append(record)
    return sorted(selected, key=queue_sort_key)


def assign_note_paths(records: list[dict[str, Any]], output_dir: Path) -> dict[str, Path]:
    base_counts: dict[str, int] = {}
    for record in records:
        base = _note_base_slug(record)
        base_counts[base] = base_counts.get(base, 0) + 1
    paths: dict[str, Path] = {}
    for record in records:
        base = _note_base_slug(record)
        if base_counts[base] > 1:
            filename = f"{base}--{_note_hash(record)}.md"
        else:
            filename = f"{base}.md"
        paths[str(record.get("dedup_key"))] = output_dir / filename
    return paths


def render_note(record: dict[str, Any]) -> str:
    title = _clean(record.get("title") or "Untitled Paper")
    sections = _stable_list(record.get("research_sections"))
    lines = [
        "---",
        "type: paper_note",
        "status: scaffold",
        f"source: {_yaml_scalar(record.get('seen_sources', ['unknown'])[0] if isinstance(record.get('seen_sources'), list) and record.get('seen_sources') else 'unknown')}",
        f"title: {_yaml_scalar(title)}",
        f"dedup_key: {_yaml_scalar(record.get('dedup_key') or '')}",
        f"relevance_label: {_yaml_scalar(record.get('relevance_label') or '')}",
        f"relevance_score: {int(record.get('relevance_score') or 0)}",
        f"queue_priority: {_yaml_scalar(record.get('queue_priority') or '')}",
        f"reading_status: {_yaml_scalar(record.get('reading_status') or '')}",
        f"review_status: {_yaml_scalar(record.get('review_status') or '')}",
        f"track: {_yaml_scalar(record.get('track') or '')}",
        *_yaml_list("research_sections", sections),
        f"source_url: {_yaml_scalar(record.get('source_url') or '')}",
        f"doi: {_yaml_scalar(record.get('doi') or '')}",
        f"arxiv_id: {_yaml_scalar(record.get('arxiv_id') or '')}",
    ]
    if record.get("zotero_key"):
        lines.append(f"zotero_key: {_yaml_scalar(record.get('zotero_key'))}")
    lines.extend(
        [
            f"created_by: {_yaml_scalar(CREATED_BY)}",
            "---",
            "",
            f"# {title}",
            "",
            "## Metadata",
            "",
            f"- Dedup key: {_clean(record.get('dedup_key') or '')}",
            f"- Source URL: {_clean(record.get('source_url') or 'TODO_VERIFY')}",
            f"- DOI: {_clean(record.get('doi') or 'TODO_VERIFY')}",
            f"- arXiv ID: {_clean(record.get('arxiv_id') or 'TODO_VERIFY')}",
            f"- Relevance: {_clean(record.get('relevance_label') or '')} / {int(record.get('relevance_score') or 0)}",
            f"- Queue priority: {_clean(record.get('queue_priority') or '')}",
            "",
            "## Why Queued",
            "",
            "- Needs verification against the original paper before any contribution, attack, security, or experiment statement.",
            f"- Queue track: {_clean(record.get('track') or 'Potentially relevant')}",
            f"- Research sections: {', '.join(sections) if sections else 'TODO_VERIFY'}",
            "",
            "## Reading Goal",
            "",
            "- TODO_AFTER_READING: decide whether this paper should be read fully, skimmed for related work, or ignored.",
            "",
            "## TL;DR",
            "",
            "- TODO_AFTER_READING",
            "",
            "## Core Problem",
            "",
            "- TODO_VERIFY",
            "",
            "## Method / Construction / Attack Idea",
            "",
            "- TODO_VERIFY",
            "",
            "## Mathematical Checkpoints",
            "",
            "- TODO_VERIFY: assumptions, reductions, parameter choices, and proof obligations.",
            "",
            "## Experiment / Artifact Checkpoints",
            "",
            "- TODO_VERIFY: code, benchmark, dataset, implementation details, and reproducibility claims.",
            "",
            "## Relation to My Research",
            "",
            "- Candidate for related work.",
            "- Potentially relevant to lattice cryptography research directions; confirm after reading.",
            "",
            "## Possible Use",
            "",
            "- TODO_AFTER_READING: related work, baseline, advisor discussion, paper plan input, or no action.",
            "",
            "## Questions for Advisor",
            "",
            "- TODO_AFTER_READING: formulate one precise question after checking the paper.",
            "",
            "## Reading Log",
            "",
            "- TODO_AFTER_READING",
            "",
            "## Verification Status",
            "",
            f"- Current review status: {_clean(record.get('review_status') or 'TODO_VERIFY')}",
            "- Needs verification before reuse.",
            "",
        ]
    )
    return "\n".join(lines)


def build_scaffold_plan(
    state: dict[str, Any],
    output_dir: Path,
    *,
    reading_statuses: tuple[str, ...] = DEFAULT_READING_STATUSES,
    review_statuses: tuple[str, ...] = DEFAULT_REVIEW_STATUSES,
    priorities: tuple[str, ...] = DEFAULT_PRIORITIES,
) -> dict[str, Any]:
    records = select_records(
        state,
        reading_statuses=reading_statuses,
        review_statuses=review_statuses,
        priorities=priorities,
    )
    paths = assign_note_paths(records, output_dir)
    entries: list[dict[str, Any]] = []
    for record in records:
        key = str(record.get("dedup_key"))
        path = paths[key]
        entries.append(
            {
                "dedup_key": key,
                "title": record.get("title"),
                "path": path,
                "record": record,
                "exists": path.exists(),
                "content": render_note(record),
            }
        )
    return {"schema_version": SCHEMA_VERSION, "output_dir": output_dir, "entries": entries}


def _append_history(record: dict[str, Any], timestamp: str, path: str, *, action: str) -> None:
    history = record.setdefault("status_history", [])
    if isinstance(history, list):
        history.append(
            {
                "timestamp": timestamp,
                "action": action,
                "field": "obsidian_note_path",
                "old": record.get("obsidian_note_path", ""),
                "new": path,
            }
        )


def _update_queue_paths(state: dict[str, Any], entries: list[dict[str, Any]], *, timestamp: str) -> None:
    path_by_key = {str(entry["dedup_key"]): str(entry["path"]) for entry in entries}
    for record in state.get("records", []):
        if not isinstance(record, dict):
            continue
        key = str(record.get("dedup_key"))
        if key not in path_by_key:
            continue
        path = path_by_key[key]
        if record.get("obsidian_note_path") == path:
            continue
        _append_history(record, timestamp, path, action="obsidian_scaffold")
        record["obsidian_note_path"] = path
        record["updated_at"] = timestamp
    state["updated_at"] = timestamp


def generate_scaffolds(
    *,
    state_path: Path = DEFAULT_STATE_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    reading_statuses: tuple[str, ...] = DEFAULT_READING_STATUSES,
    review_statuses: tuple[str, ...] = DEFAULT_REVIEW_STATUSES,
    priorities: tuple[str, ...] = DEFAULT_PRIORITIES,
    update_queue: bool = False,
    dry_run: bool = False,
    timestamp: str | None = None,
) -> dict[str, Any]:
    state = load_state(state_path)
    plan = build_scaffold_plan(
        state,
        output_dir,
        reading_statuses=reading_statuses,
        review_statuses=review_statuses,
        priorities=priorities,
    )
    written: list[Path] = []
    skipped: list[Path] = []
    existing: list[Path] = []
    if not dry_run:
        for entry in plan["entries"]:
            path: Path = entry["path"]
            if path.exists():
                skipped.append(path)
                existing.append(path)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(entry["content"]), encoding="utf-8")
            written.append(path)
        if update_queue:
            stamp = timestamp or now_iso()
            _update_queue_paths(state, plan["entries"], timestamp=stamp)
            save_state(state_path, state)
    else:
        for entry in plan["entries"]:
            if entry["path"].exists():
                existing.append(entry["path"])
    return {
        "plan": plan,
        "written": written,
        "skipped_existing": skipped,
        "existing": existing,
        "dry_run": dry_run,
        "update_queue": update_queue,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Obsidian paper note scaffolds from the local reading queue.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate", help="Generate paper note scaffolds.")
    generate.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    generate.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    generate.add_argument("--vault-dir", type=Path)
    generate.add_argument("--papers-subdir", default="Papers")
    generate.add_argument("--statuses", default=",".join(DEFAULT_READING_STATUSES))
    generate.add_argument("--review-statuses", default=",".join(DEFAULT_REVIEW_STATUSES))
    generate.add_argument("--priorities", default=",".join(DEFAULT_PRIORITIES))
    generate.add_argument("--update-queue", action="store_true")
    generate.add_argument("--dry-run", action="store_true")
    return parser


def _resolve_output_dir(args: argparse.Namespace) -> Path:
    if args.vault_dir:
        return args.vault_dir / args.papers_subdir
    return args.output_dir


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "generate":
        print(f"unknown command: {args.command}", file=sys.stderr)
        return 1
    result = generate_scaffolds(
        state_path=args.state,
        output_dir=_resolve_output_dir(args),
        reading_statuses=parse_csv(args.statuses, DEFAULT_READING_STATUSES),
        review_statuses=parse_csv(args.review_statuses, DEFAULT_REVIEW_STATUSES),
        priorities=parse_csv(args.priorities, DEFAULT_PRIORITIES),
        update_queue=args.update_queue,
        dry_run=args.dry_run,
    )
    entries = result["plan"]["entries"]
    print(f"Obsidian scaffold: selected={len(entries)}, written={len(result['written'])}, skipped_existing={len(result['skipped_existing'])}")
    if args.dry_run:
        print("DRY RUN: no files written and queue state unchanged.")
    for entry in entries:
        prefix = "would write" if args.dry_run else ("exists" if entry["path"].exists() and entry["path"] not in result["written"] else "target")
        print(f"{prefix}: {entry['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
