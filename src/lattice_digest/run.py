from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from lattice_digest.config import load_config_bundle, project_root
from lattice_digest.dedup import deduplicate
from lattice_digest.digest import generate_markdown
from lattice_digest.models import PaperRecord
from lattice_digest.ranker import rank_records
from lattice_digest.sources import FetchContext, build_source
from lattice_digest.storage import write_json, write_markdown, write_sqlite
from lattice_digest.text import parse_duration_to_hours


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a daily Chinese digest for lattice cryptography papers.")
    parser.add_argument("--since", default="36h", help="Lookback window, e.g. 36h or 7d.")
    parser.add_argument("--output", default="markdown,json", help="Comma-separated outputs: markdown,json.")
    parser.add_argument("--send", default="none", help="Delivery backend. Currently only 'none' is implemented.")
    parser.add_argument("--dry-run", action="store_true", help="Run without network writes or output artifact writes.")
    parser.add_argument("--config-dir", type=Path, default=None, help="Override config directory.")
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
            "final={final}, warnings={warnings}, errors={errors}".format(
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
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
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
    reliable, dropped_count = _filter_reliable(ranked)
    deduped = deduplicate(reliable)
    ordered = _sort_records(deduped)
    _update_source_health_after_pipeline(context, ranked, reliable, deduped, ordered)
    source_health = context.source_health_summary()
    digest_date = datetime.now(ZoneInfo("Asia/Singapore")).date()
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
        print(generate_markdown(ordered, digest_date, dropped_count, source_health))
        return 0

    written: list[Path] = []
    if "json" in outputs:
        written.append(write_json(ordered, root / "data", digest_date, source_health))
    if "markdown" in outputs or "md" in outputs:
        written.append(write_markdown(ordered, root / "digests", digest_date, dropped_count, source_health))
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
