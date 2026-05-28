from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from lattice_digest.config import load_config_bundle, project_root
from lattice_digest.dedup import deduplicate
from lattice_digest.digest import generate_markdown
from lattice_digest.models import PaperRecord
from lattice_digest.ranker import rank_records
from lattice_digest.sources import FetchContext, build_source
from lattice_digest.sources.base import parse_date_for_filter
from lattice_digest.storage import write_json, write_markdown, write_sqlite
from lattice_digest.text import parse_duration_to_hours


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a daily Chinese digest for lattice cryptography papers.")
    parser.add_argument("--since", default="36h", help="Lookback window, e.g. 36h or 7d.")
    parser.add_argument("--output", default="markdown,json", help="Comma-separated outputs: markdown,json.")
    parser.add_argument("--send", default="none", help="Delivery backend. Currently only 'none' is implemented.")
    parser.add_argument("--dry-run", action="store_true", help="Run without network writes or output artifact writes.")
    parser.add_argument("--config-dir", type=Path, default=None, help="Override config directory.")
    parser.add_argument("--target-date", default=None, help="Output report date in YYYY-MM-DD format.")
    parser.add_argument("--collector", choices=("local_codex", "github_actions"), default=None)
    parser.add_argument(
        "--quality-status",
        choices=("authoritative", "provisional", "authoritative_backfill"),
        default=None,
    )
    parser.add_argument("--run-mode", choices=("daily", "backfill", "dry_run"), default="daily")
    parser.add_argument("--force", action="store_true", help="Overwrite authoritative reports for the target date.")
    return parser.parse_args(argv)


def _enabled_source_configs(sources_config: dict) -> list[dict]:
    return [source for source in sources_config.get("sources", []) if source.get("enabled", False)]


def _collect_records(source_configs: list[dict], context: FetchContext) -> list[PaperRecord]:
    records: list[PaperRecord] = []
    for source_config in source_configs:
        name = source_config.get("name", source_config.get("type", "unknown"))
        context.health(name)
        try:
            adapter = build_source(source_config)
            fetched = adapter.fetch(context)
            records.extend(fetched)
            context.warnings.append(f"{name}: fetched {len(fetched)} candidate records")
        except Exception as exc:  # noqa: BLE001 - source failures should not fabricate or stop the digest.
            context.add_error(f"{name}: failed ({exc})", name)
    return records


def _filter_reliable(records: list[PaperRecord]) -> tuple[list[PaperRecord], int]:
    kept: list[PaperRecord] = []
    dropped = 0
    for record in records:
        if not record.source or not record.source_url:
            dropped += 1
            continue
        if record.relevance_label == "D":
            dropped += 1
            continue
        kept.append(record)
    return kept, dropped


def _sort_records(records: list[PaperRecord]) -> list[PaperRecord]:
    return sorted(
        records,
        key=lambda record: (
            record.reading_priority,
            -record.relevance_score,
            record.publication_date or "",
            record.title.lower(),
        ),
    )


def _record_source_names(record: PaperRecord) -> list[str]:
    return [item.strip() for item in record.source.split(",") if item.strip()]


def _parse_target_date(value: str | None, now_local: datetime) -> date:
    if not value:
        return now_local.date()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"invalid --target-date {value!r}; expected YYYY-MM-DD") from exc


def _coverage_window(target_date: date, hours: int, target_date_was_explicit: bool) -> tuple[datetime, datetime]:
    if target_date_was_explicit:
        local_end = datetime.combine(target_date + timedelta(days=1), time.min, ZoneInfo("Asia/Singapore"))
        coverage_end = local_end.astimezone(timezone.utc)
    else:
        coverage_end = datetime.now(timezone.utc)
    return coverage_end - timedelta(hours=hours), coverage_end


def _record_effective_datetime(record: PaperRecord) -> datetime | None:
    return parse_date_for_filter(record.update_date) or parse_date_for_filter(record.publication_date)


def _filter_records_to_coverage(
    records: list[PaperRecord],
    coverage_start: datetime,
    coverage_end: datetime,
) -> tuple[list[PaperRecord], int]:
    kept: list[PaperRecord] = []
    dropped = 0
    for record in records:
        parsed = _record_effective_datetime(record)
        if parsed is not None and coverage_start <= parsed < coverage_end:
            kept.append(record)
        elif parsed is None:
            kept.append(record)
        else:
            dropped += 1
    return kept, dropped


def _load_existing_metadata(root: Path, target_date: date) -> dict[str, object] | None:
    path = root / "data" / f"{target_date.isoformat()}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    metadata = payload.get("metadata")
    return metadata if isinstance(metadata, dict) else None


def _should_skip_write(
    existing_metadata: dict[str, object] | None,
    new_quality_status: str,
    force: bool,
) -> bool:
    if force or not existing_metadata:
        return False
    old_quality = str(existing_metadata.get("quality_status") or "")
    if new_quality_status == "provisional" and old_quality in {"authoritative", "authoritative_backfill"}:
        return True
    if old_quality in {"authoritative", "authoritative_backfill"}:
        return True
    return False


def _supersedes_metadata(
    existing_metadata: dict[str, object] | None,
    new_quality_status: str,
) -> dict[str, object] | None:
    if not existing_metadata:
        return None
    if _is_provisional_metadata(existing_metadata) and new_quality_status == "authoritative_backfill":
        return {
            "collector": existing_metadata.get("collector"),
            "run_date": existing_metadata.get("run_date"),
            "quality_status": existing_metadata.get("quality_status"),
        }
    return None


def _is_provisional_metadata(metadata: dict[str, object] | None) -> bool:
    if not metadata:
        return False
    return metadata.get("collector") == "github_actions" or metadata.get("quality_status") == "provisional"


def _archive_existing_provisional(root: Path, target_date: date, existing_metadata: dict[str, object] | None) -> list[Path]:
    if not _is_provisional_metadata(existing_metadata):
        return []
    archive_dir = root / "archive" / "provisional"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived: list[Path] = []
    for source_path, target_path in [
        (root / "data" / f"{target_date.isoformat()}.json", archive_dir / f"{target_date.isoformat()}.json"),
        (root / "digests" / f"{target_date.isoformat()}.md", archive_dir / f"{target_date.isoformat()}.md"),
    ]:
        if source_path.exists():
            shutil.copy2(source_path, target_path)
            archived.append(target_path)
    return archived


def _build_run_metadata(
    *,
    target_date: date,
    run_datetime: datetime,
    collector: str,
    quality_status: str,
    run_mode: str,
    coverage_start: datetime,
    coverage_end: datetime,
    since_window: str,
    supersedes: dict[str, object] | None,
) -> dict[str, object]:
    return {
        "target_date": target_date.isoformat(),
        "run_date": run_datetime.date().isoformat(),
        "collector": collector,
        "quality_status": quality_status,
        "run_mode": run_mode,
        "coverage_start": coverage_start.isoformat(),
        "coverage_end": coverage_end.isoformat(),
        "since_window": since_window,
        "backfill": run_mode == "backfill",
        "supersedes": supersedes,
    }


def _update_source_health_after_pipeline(
    context: FetchContext,
    ranked: list[PaperRecord],
    reliable: list[PaperRecord],
    deduped: list[PaperRecord],
    final_records: list[PaperRecord],
) -> None:
    for health in context.source_health.values():
        health.relevance_filtered_candidates = 0
        health.scoring_threshold_candidates = 0
        health.deduped_candidates = 0
        health.final_records = 0

    for record in reliable:
        for source_name in _record_source_names(record):
            context.health(source_name).relevance_filtered_candidates += 1

    for record in ranked:
        if record.relevance_label in {"A", "B", "C"} and record.relevance_score >= 40:
            for source_name in _record_source_names(record):
                context.health(source_name).scoring_threshold_candidates += 1

    for record in deduped:
        for source_name in _record_source_names(record):
            context.health(source_name).deduped_candidates += 1

    for record in final_records:
        for source_name in _record_source_names(record):
            context.health(source_name).final_records += 1


def _print_source_health(source_health: list[dict[str, object]]) -> None:
    print("\nSource Health:")
    if not source_health:
        print("- no source health data")
        return
    for item in source_health:
        warnings = item.get("warnings") if isinstance(item.get("warnings"), list) else []
        errors = item.get("errors") if isinstance(item.get("errors"), list) else []
        print(
            "- {source}: raw={raw}, normalized={normalized}, date_filtered={date_filtered}, "
            "deduped={deduped}, relevance_filtered={relevance}, threshold={threshold}, "
            "final={final}, status={status}, error_type={error_type}, retryable={retryable}, "
            "warnings={warnings}, errors={errors}".format(
                source=item.get("source", "unknown"),
                raw=item.get("raw_count", item.get("raw_candidates", 0)),
                normalized=item.get("normalized_count", item.get("normalized_candidates", 0)),
                date_filtered=item.get("date_filtered_count", item.get("date_filtered_candidates", 0)),
                deduped=item.get("deduped_candidates", 0),
                relevance=item.get("relevance_filtered_candidates", 0),
                threshold=item.get("scoring_threshold_candidates", 0),
                final=item.get("final_count", item.get("final_records", 0)),
                status=item.get("health_status", item.get("status", "unknown")),
                error_type=item.get("error_type") or "none",
                retryable=item.get("retryable"),
                warnings=len(warnings),
                errors=len(errors),
            )
        )


def _load_dotenv(root: Path) -> None:
    env_path = root / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = project_root()
    _load_dotenv(root)
    configs = load_config_bundle(args.config_dir)
    hours = parse_duration_to_hours(args.since)
    run_datetime = datetime.now(ZoneInfo("Asia/Singapore"))
    digest_date = _parse_target_date(args.target_date, run_datetime)
    coverage_start, coverage_end = _coverage_window(digest_date, hours, args.target_date is not None)
    since = coverage_start
    collector = args.collector or "local_codex"
    quality_status = args.quality_status or ("provisional" if collector == "github_actions" else "authoritative")
    run_mode = "dry_run" if args.dry_run else args.run_mode
    existing_metadata = _load_existing_metadata(root, digest_date)
    supersedes = _supersedes_metadata(existing_metadata, quality_status)
    metadata = _build_run_metadata(
        target_date=digest_date,
        run_datetime=run_datetime,
        collector=collector,
        quality_status=quality_status,
        run_mode=run_mode,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        since_window=args.since,
        supersedes=supersedes,
    )
    request_config = configs["sources"].get("request", {})
    context = FetchContext(
        root=root,
        since=since,
        dry_run=args.dry_run,
        timeout_seconds=int(request_config.get("timeout_seconds", 20)),
        user_agent=request_config.get("user_agent", "lattice-crypto-daily-digest/0.1"),
        http_cache_ttl_seconds=int(request_config.get("cache_ttl_seconds", 12 * 60 * 60)),
        per_domain_min_interval_seconds=float(request_config.get("per_domain_min_interval_seconds", 1.0)),
        max_retries=int(request_config.get("max_retries", 2)),
        api_keys={
            "SEMANTIC_SCHOLAR_API_KEY": os.getenv("SEMANTIC_SCHOLAR_API_KEY", ""),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "CONTACT_EMAIL": os.getenv("CONTACT_EMAIL", ""),
        },
    )

    source_configs = _enabled_source_configs(configs["sources"])
    records = _collect_records(source_configs, context)
    ranked = rank_records(records, configs["taxonomy"], configs["keywords"], configs["negative"])
    if args.target_date is not None:
        ranked, coverage_dropped = _filter_records_to_coverage(ranked, coverage_start, coverage_end)
        if coverage_dropped:
            context.warnings.append(f"coverage filter dropped {coverage_dropped} records outside target_date window")
    reliable, dropped_count = _filter_reliable(ranked)
    deduped = deduplicate(reliable)
    ordered = _sort_records(deduped)
    _update_source_health_after_pipeline(context, ranked, reliable, deduped, ordered)
    source_health = context.source_health_summary()
    outputs = {item.strip().lower() for item in args.output.split(",") if item.strip()}

    if args.send != "none":
        context.warnings.append(f"send backend '{args.send}' is not implemented; no delivery was attempted")

    if args.dry_run:
        print("DRY RUN: no output files were written and network fetches were skipped.")
        print(f"Candidates: {len(records)} | Included after ranking/dedup: {len(ordered)} | Dropped/D: {dropped_count}")
        if context.warnings:
            print("\nWarnings:")
            for warning in context.warnings:
                print(f"- {warning}")
        _print_source_health(source_health)
        print("\nMarkdown preview:")
        print(generate_markdown(ordered, digest_date, dropped_count, source_health, context.warnings, args.since, metadata))
        return 0

    if _should_skip_write(existing_metadata, quality_status, args.force):
        old_quality = existing_metadata.get("quality_status") if existing_metadata else "unknown"
        old_collector = existing_metadata.get("collector") if existing_metadata else "unknown"
        print(
            "Skipped writing {date}: existing report is {collector}/{quality}; use --force to overwrite.".format(
                date=digest_date.isoformat(),
                collector=old_collector,
                quality=old_quality,
            )
        )
        _print_source_health(source_health)
        return 0

    written: list[Path] = []
    if quality_status == "authoritative_backfill" and supersedes:
        written.extend(_archive_existing_provisional(root, digest_date, existing_metadata))
    if "json" in outputs:
        written.append(write_json(ordered, root / "data", digest_date, source_health, context.warnings, args.since, metadata))
    if "markdown" in outputs or "md" in outputs:
        written.append(
            write_markdown(
                ordered,
                root / "digests",
                digest_date,
                dropped_count,
                source_health,
                context.warnings,
                args.since,
                metadata,
            )
        )
    written.append(write_sqlite(ordered, root / "papers.db"))

    print(f"Generated {len(ordered)} digest records.")
    for path in written:
        print(path)
    if context.warnings:
        print("\nWarnings:")
        for warning in context.warnings:
            print(f"- {warning}")
    _print_source_health(source_health)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
