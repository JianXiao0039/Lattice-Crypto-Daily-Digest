from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from lattice_digest.config import load_config_bundle, project_root
from lattice_digest.candidate_ledger import build_candidate_ledger, write_candidate_ledger
from lattice_digest.dedup import deduplicate
from lattice_digest.digest import generate_markdown
from lattice_digest.artifact_paths import (
    daily_data_path,
    daily_digest_path,
    legacy_daily_data_candidates,
    legacy_daily_digest_candidates,
    resolve_existing,
)
from lattice_digest.models import PaperRecord
from lattice_digest.ranker import rank_records
from lattice_digest.radar_freshness import enrich_record_for_daily_radar
from lattice_digest.observability_v3 import assign_observability_routes
from lattice_digest.query_portfolio_v3 import load_query_portfolio_v3
from lattice_digest.retrieval_metrics_v3 import evidence_metrics, query_marginal_yield, source_diversity_metrics
from lattice_digest.retrieval_v3 import apply_semantic_consequence_analysis_v3, prepare_for_semantic_analysis_v3
from lattice_digest.source_health_ledger import write_source_health_ledger
from lattice_digest.sources import FetchContext, build_source
from lattice_digest.sources.base import parse_date_for_filter
from lattice_digest.storage import write_json, write_markdown, write_sqlite
from lattice_digest.promotion_history import load_promotion_history, apply_promotion_history
from lattice_digest.authority import derive_authority
from lattice_digest.storage import publish_daily_pair
from lattice_digest.text import parse_duration_to_hours
from lattice_digest.runtime_paths import RuntimePaths, env_file
from lattice_digest.recovery_window import exact_window, recovery_metadata


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a daily Chinese digest for lattice cryptography papers.")
    date_window = parser.add_mutually_exclusive_group()
    date_window.add_argument("--since", default=None, help="Lookback window, e.g. 36h or 7d. Defaults to 36h.")
    date_window.add_argument(
        "--date",
        type=_parse_cli_date,
        default=None,
        help="Generate artifacts for exactly one Asia/Singapore calendar date in YYYY-MM-DD format.",
    )
    parser.add_argument("--output", default="markdown,json", help="Comma-separated outputs: markdown,json.")
    parser.add_argument("--send", default="none", help="Delivery backend. Currently only 'none' is implemented.")
    parser.add_argument("--dry-run", action="store_true", help="Run without network writes or output artifact writes.")
    parser.add_argument("--preflight", action="store_true", help="Resolve paths, provenance and window without discovery or writes.")
    parser.add_argument("--coverage-start", default=None, help="Exact historical start with timezone offset.")
    parser.add_argument("--coverage-end", default=None, help="Exact historical end with timezone offset.")
    parser.add_argument("--original-missing-reason", default=None)
    parser.add_argument("--config-dir", type=Path, default=None, help="Override config directory.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help=(
            "Write generated artifacts under this root instead of the project root. "
            "Useful for scratch QA; preserves the normal data/YYYY/daily and digests/YYYY/daily layout."
        ),
    )
    parser.add_argument(
        "--candidate-ledger",
        action="store_true",
        help="Write a non-authoritative decision ledger under OUTPUT_ROOT/audits/worktree.",
    )
    parser.add_argument("--target-date", default=None, help="Output report date in YYYY-MM-DD format.")
    parser.add_argument("--collector", choices=("local_codex", "github_actions"), default=None)
    parser.add_argument(
        "--quality-status",
        choices=("authoritative", "provisional", "authoritative_backfill"),
        default=None,
    )
    parser.add_argument("--run-mode", choices=("daily", "backfill", "dry_run"), default="daily")
    parser.add_argument("--force", action="store_true", help="Overwrite authoritative reports for the target date.")
    parser.add_argument(
        "--retry-failed-sources",
        action="store_true",
        help="Manually retry sources that only have a failed same-day attempt marker, without bypassing successful caches.",
    )
    parser.add_argument(
        "--include-latest-sources",
        action="store_true",
        help="Manually include source-native latest feeds, allowing safe latest-source recovery for failed same-day attempts.",
    )
    args = parser.parse_args(argv)
    if args.date is not None and args.target_date is not None:
        parser.error("--date cannot be combined with legacy --target-date")
    if bool(args.coverage_start) != bool(args.coverage_end):
        parser.error("--coverage-start and --coverage-end must be supplied together")
    if args.coverage_start:
        if args.date is not None:
            parser.error("exact coverage cannot be combined with --date")
        try:
            exact_window(args.coverage_start, args.coverage_end, args.target_date,
                         run_mode=args.run_mode,
                         since_hours=parse_duration_to_hours(args.since) if args.since else None)
        except (ValueError, TypeError) as exc:
            parser.error(str(exc))
    return args


def _parse_cli_date(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid date {value!r}; expected YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise argparse.ArgumentTypeError(f"invalid date {value!r}; expected YYYY-MM-DD")
    return parsed


def _enabled_source_configs(sources_config: dict) -> list[dict]:
    catalog = {
        str(item.get("id")): item
        for item in sources_config.get("critical_query_groups", [])
        if isinstance(item, dict) and item.get("id")
    }
    enabled: list[dict] = []
    for source in sources_config.get("sources", []):
        if not source.get("enabled", False):
            continue
        merged = dict(source)
        ids = [str(item) for item in source.get("critical_query_family_ids", [])]
        merged["critical_query_groups"] = [catalog[item] for item in ids if item in catalog]
        enabled.append(merged)
    return enabled


def _collect_records(source_configs: list[dict], context: FetchContext) -> list[PaperRecord]:
    records: list[PaperRecord] = []
    for source_config in source_configs:
        name = source_config.get("name", source_config.get("type", "unknown"))
        context.register_source(source_config)
        context.health(name)
        try:
            adapter = build_source(source_config)
            fetched = adapter.fetch(context)
            records.extend(fetched)
            context.warnings.append(f"{name}: fetched {len(fetched)} candidate records")
        except Exception as exc:  # noqa: BLE001 - source failures should not fabricate or stop the digest.
            context.add_error(f"{name}: failed ({exc})", name)
            context.record_route_event(
                "source",
                str(name),
                "SOURCE",
                "SOURCE_FAILED",
                type(exc).__name__,
                terminal=True,
            )
        finally:
            fetched_count = len(fetched) if "fetched" in locals() else 0
            context.finish_source(str(name), fetched_count)
            if "fetched" in locals():
                del fetched
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


def _filter_by_source_role(
    records: list[PaperRecord],
    source_configs: list[dict],
    context: FetchContext,
) -> tuple[list[PaperRecord], list[PaperRecord]]:
    """Keep enrichment-only records from masquerading as abstract-rich discovery.

    A merged record backed by any discovery source is retained. A standalone
    metadata/identifier record without an abstract must satisfy the explicit
    source threshold. This does not change relevance scoring or source health.
    """
    configs_by_name = {
        str(item.get("name") or item.get("type")): item
        for item in source_configs
    }
    kept: list[PaperRecord] = []
    dropped: list[PaperRecord] = []
    discovery_roles = {"DISCOVERY_PRIMARY", "DISCOVERY_SECONDARY"}
    for record in records:
        source_names = _record_source_names(record)
        source_roles = {
            role
            for name in source_names
            for role in context.source_roles(name)
        }
        if record.abstract or source_roles.intersection(discovery_roles):
            kept.append(record)
            continue
        thresholds = [
            int(configs_by_name.get(name, {}).get("standalone_no_abstract_min_relevance_score", 101))
            for name in source_names
        ]
        threshold = min(thresholds, default=101)
        if record.relevance_score >= threshold:
            kept.append(record)
            continue
        dropped.append(record)
        context.record_route_event(
            "canonical_candidate",
            record.paper_id or record.source_url,
            "SOURCE_ROLE_POLICY",
            "LOW_EVIDENCE_ENRICHMENT_ONLY_REJECTED",
            f"standalone no-abstract score {record.relevance_score} below {threshold}",
            terminal=True,
        )
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


def _coverage_window(target_date: date, hours: int, target_date_was_explicit: bool,
                     now: datetime | None = None) -> tuple[datetime, datetime]:
    if target_date_was_explicit:
        local_end = datetime.combine(target_date + timedelta(days=1), time.min, ZoneInfo("Asia/Singapore"))
        coverage_end = local_end.astimezone(timezone.utc)
    else:
        coverage_end = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return coverage_end - timedelta(hours=hours), coverage_end


def _exact_date_coverage_window(target_date: date) -> tuple[datetime, datetime]:
    local_start = datetime.combine(target_date, time.min, ZoneInfo("Asia/Singapore"))
    local_end = datetime.combine(target_date + timedelta(days=1), time.min, ZoneInfo("Asia/Singapore"))
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


def _record_effective_datetime(record: PaperRecord) -> datetime | None:
    if record.update_date_kind == "AUTHORITATIVE_CONTENT_REVISION_DATE":
        parsed_update = parse_date_for_filter(record.update_timestamp or record.update_date)
        if parsed_update is not None:
            return parsed_update
    if record.announcement_date_kind == "AUTHORITATIVE_ANNOUNCEMENT_DATE":
        parsed_announcement = parse_date_for_filter(record.announcement_date)
        if parsed_announcement is not None:
            return parsed_announcement
    if record.publication_date_kind == "AUTHORITATIVE_PUBLICATION_DATE":
        return parse_date_for_filter(record.publication_timestamp or record.publication_date)
    return None


def _filter_records_to_coverage(
    records: list[PaperRecord],
    coverage_start: datetime,
    coverage_end: datetime,
    *,
    digest_date: date,
    include_backfill: bool,
) -> tuple[list[PaperRecord], int]:
    kept: list[PaperRecord] = []
    dropped = 0
    for record in records:
        enriched = enrich_record_for_daily_radar(
            record,
            digest_date,
            coverage_start=coverage_start,
            coverage_end=coverage_end,
        )
        if enriched.primary_today_new_eligible:
            kept.append(enriched)
            continue
        if enriched.freshness_bucket in {"CRITICAL_NEWLY_OBSERVED_VERIFY_FIRST", "recent_content_revision"}:
            kept.append(enriched)
            continue
        if include_backfill:
            kept.append(enriched)
            continue
        dropped += 1
    return kept, dropped


def _load_existing_metadata(root: Path, target_date: date) -> dict[str, object] | None:
    path, used_legacy = resolve_existing(
        daily_data_path(target_date, root / "data"),
        legacy_daily_data_candidates(target_date, root / "data"),
    )
    if not path.exists():
        return None
    if used_legacy:
        print(f"Warning: using legacy daily JSON fallback: {path}", file=os.sys.stderr)
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
        (daily_data_path(target_date, root / "data"), archive_dir / f"{target_date.isoformat()}.json"),
        (daily_digest_path(target_date, root / "digests"), archive_dir / f"{target_date.isoformat()}.md"),
    ]:
        fallback_candidates = (
            legacy_daily_data_candidates(target_date, root / "data")
            if source_path.suffix == ".json"
            else legacy_daily_digest_candidates(target_date, root / "digests")
        )
        resolved, _ = resolve_existing(source_path, fallback_candidates)
        if resolved.exists():
            shutil.copy2(resolved, target_path)
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
            "final={final}, latest={latest_status}/{latest_records}, status={status}, error_type={error_type}, retryable={retryable}, "
            "warnings={warnings}, errors={errors}".format(
                source=item.get("source", "unknown"),
                raw=item.get("raw_count", item.get("raw_candidates", 0)),
                normalized=item.get("normalized_count", item.get("normalized_candidates", 0)),
                date_filtered=item.get("date_filtered_count", item.get("date_filtered_candidates", 0)),
                deduped=item.get("deduped_candidates", 0),
                relevance=item.get("relevance_filtered_candidates", 0),
                threshold=item.get("scoring_threshold_candidates", 0),
                final=item.get("final_count", item.get("final_records", 0)),
                latest_status=item.get("latest_feed_status") or "n/a",
                latest_records=item.get("latest_feed_records", 0),
                status=item.get("health_status", item.get("status", "unknown")),
                error_type=item.get("error_type") or "none",
                retryable=item.get("retryable"),
                warnings=len(warnings),
                errors=len(errors),
            )
        )


def _load_dotenv(root: Path, *, public: bool = False) -> None:
    env_path = env_file(root, public=public or os.getenv('LATTICE_DIGEST_PUBLIC_AUTOMATION') == '1')
    if env_path is None or not env_path.exists():
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


def main(argv: list[str] | None = None, *, preflight_proof: dict | None = None) -> int:
    args = parse_args(argv)
    root = project_root()
    paths = RuntimePaths.resolve(code_root=root, canonical_root=args.output_root)
    output_root = paths.canonical_root
    if args.candidate_ledger and args.output_root is None:
        raise SystemExit("--candidate-ledger requires an explicit external --output-root")
    if os.getenv('LATTICE_DIGEST_PUBLIC_AUTOMATION') == '1' and args.config_dir is not None and args.config_dir.resolve() != paths.config_root:
        raise SystemExit('public configuration must come from published code/config')
    run_datetime = datetime.now(ZoneInfo("Asia/Singapore"))
    from lattice_digest.runtime_provenance import runtime_provenance, public_runtime_allowed, schedule_telemetry
    code_provenance = runtime_provenance(root)
    public_automation = (args.collector == 'github_actions' or os.getenv('LATTICE_DIGEST_PUBLIC_AUTOMATION') == '1'
                         or bool(args.coverage_start)
                         or (output_root == root and args.run_mode == 'daily'
                             and code_provenance['runtime_code_state'] in {'UNPUBLISHED_RUNTIME_CODE', 'UNPUBLISHED_RUNTIME_COMMIT', 'DIRTY_RUNTIME_DEPENDENCY'}))
    allowed = public_runtime_allowed(code_provenance, public_automation=public_automation)
    exact_date = args.date
    since_window = "24h" if exact_date is not None else (args.since or "36h")
    hours = parse_duration_to_hours(since_window)
    digest_date = exact_date or _parse_target_date(args.target_date, run_datetime)
    if args.coverage_start:
        coverage_start, coverage_end = exact_window(args.coverage_start, args.coverage_end, args.target_date,
                                                   run_mode=args.run_mode,
                                                   since_hours=hours if args.since else None)
        since_window = f"{(coverage_end - coverage_start).total_seconds() / 3600:g}h"
    elif exact_date is not None:
        coverage_start, coverage_end = _exact_date_coverage_window(digest_date)
    else:
        coverage_start, coverage_end = _coverage_window(digest_date, hours, args.target_date is not None, run_datetime)
    since = coverage_start
    collector = args.collector or "local_codex"
    quality_status = args.quality_status or ("provisional" if collector == "github_actions" else "authoritative")
    run_mode = args.run_mode if args.coverage_start else ("dry_run" if args.dry_run else args.run_mode)
    existing_metadata = _load_existing_metadata(output_root, digest_date)
    supersedes = _supersedes_metadata(existing_metadata, quality_status)
    metadata = _build_run_metadata(
        target_date=digest_date,
        run_datetime=run_datetime,
        collector=collector,
        quality_status=quality_status,
        run_mode=run_mode,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        since_window=since_window,
        supersedes=supersedes,
    )
    metadata.update(code_provenance)
    metadata.update(schedule_telemetry(run_datetime))
    metadata['runtime_paths'] = paths.as_dict()
    if args.coverage_start:
        metadata.update(recovery_metadata(digest_date, coverage_start, coverage_end, run_datetime, args.original_missing_reason))
        if args.preflight:
            metadata['actual_recovery_run_time'] = 'UNKNOWN'
            metadata['recovery_executed_at'] = 'UNKNOWN'
            metadata['preflight_started_at'] = run_datetime.isoformat()
    if args.preflight:
        print(json.dumps({**(preflight_proof or {}), 'preflight': True, 'discovery': 'NOT_STARTED', 'writes': 0,
                          'public_runtime_allowed': allowed, 'metadata': metadata,
                          'canonical_target_exists': daily_data_path(digest_date, paths.data_root).exists()
                              or daily_digest_path(digest_date, paths.digest_root).exists()}, ensure_ascii=False, indent=2))
        return 0 if allowed else 2
    if public_automation and not allowed:
        print('PUBLIC_AUTOMATION_RUNTIME_CODE_BLOCKED: ' + json.dumps(code_provenance, ensure_ascii=False))
        return 2
    _load_dotenv(root, public=public_automation)
    configs = load_config_bundle(args.config_dir)
    request_config = configs["sources"].get("request", {})
    context = FetchContext(
        root=output_root,
        since=since,
        dry_run=args.dry_run,
        timeout_seconds=int(request_config.get("timeout_seconds", 20)),
        user_agent=request_config.get("user_agent", "lattice-crypto-daily-digest/0.1"),
        http_cache_ttl_seconds=int(request_config.get("cache_ttl_seconds", 12 * 60 * 60)),
        per_domain_min_interval_seconds=float(request_config.get("per_domain_min_interval_seconds", 1.0)),
        max_retries=int(request_config.get("max_retries", 2)),
        max_retry_after_seconds=float(request_config.get("max_retry_after_seconds", 10)),
        per_source_time_budget_seconds=float(request_config.get("per_source_time_budget_seconds", 120)),
        global_time_budget_seconds=float(request_config.get("global_time_budget_seconds", 600)),
        source_circuit_breaker_failures=int(request_config.get("source_circuit_breaker_failures", 3)),
        runtime_journal_max_events=int(request_config.get("runtime_journal_max_events", 2000)),
        retry_failed_sources=args.retry_failed_sources,
        include_latest_sources=args.include_latest_sources,
        api_keys={
            "SEMANTIC_SCHOLAR_API_KEY": os.getenv("SEMANTIC_SCHOLAR_API_KEY", ""),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "CONTACT_EMAIL": os.getenv("CONTACT_EMAIL", ""),
        },
    )

    source_configs = _enabled_source_configs(configs["sources"])
    records = _collect_records(source_configs, context)
    prepared_v3 = prepare_for_semantic_analysis_v3(records)
    ranked = rank_records(
        list(prepared_v3.records),
        configs["taxonomy"],
        configs["keywords"],
        configs["negative"],
    )
    ranked = apply_semantic_consequence_analysis_v3(ranked)
    observed, observability_decisions = assign_observability_routes(
        ranked,
        digest_date,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
    )
    ranked = list(observed)
    ranked_before_coverage = list(ranked)
    query_portfolio_v3 = load_query_portfolio_v3()
    shadow_schedule = query_portfolio_v3.fair_schedule(
        [str(item.get("name") or item.get("type")) for item in source_configs],
        global_budget=48,
        per_source_budget=12,
    )
    metadata["retrieval_v3"] = {
        "pipeline_order": [
            "RAW_OCCURRENCE",
            "OBSERVABILITY_LEDGER",
            "IDENTITY_RESOLUTION",
            "EVIDENCE_MERGE",
            "SELECTIVE_ENRICHMENT",
            "SEMANTIC_CONSEQUENCE_ANALYSIS",
            "STRICT_DAILY_ELIGIBILITY",
        ],
        "raw_occurrences": len(records),
        "canonical_candidates": len(prepared_v3.identity.canonical_records),
        "strong_identity_merges": prepared_v3.identity.strong_merge_count,
        "secondary_identity_merges": prepared_v3.identity.secondary_merge_count,
        "unsafe_fuzzy_auto_merges": 0,
        "merge_proposals": len(prepared_v3.identity.merge_proposals),
        "metadata_conflicts": prepared_v3.identity.conflict_count,
        "enrichment_selected": prepared_v3.enrichment.selected_count,
        "enrichment_requests": prepared_v3.enrichment.request_count,
        "enrichment_upgraded": prepared_v3.enrichment.upgraded_count,
        "observability_routes": [decision.model_dump(mode="json") for decision in observability_decisions],
        "query_portfolio_v3_activation": "active" if query_portfolio_v3.production_active else "shadow",
        "production_query_activation_decision": (
            "ACTIVE" if query_portfolio_v3.production_active else "BATCH_A_PRODUCTION_QUERY_ACTIVATION_DEFERRED_BY_FROZEN_BOUNDARY"
        ),
        "shadow_query_schedule": [query.model_dump(mode="json") for query in shadow_schedule],
    }
    ranked, coverage_dropped = _filter_records_to_coverage(
        ranked,
        coverage_start,
        coverage_end,
        digest_date=digest_date,
        include_backfill=run_mode == "backfill",
    )
    if coverage_dropped:
        context.warnings.append(
            f"strict freshness filter dropped {coverage_dropped} ordinary records outside the {since_window} window"
        )
    coverage_kept = list(ranked)
    reliable, dropped_count = _filter_reliable(ranked)
    deduped = deduplicate(reliable)
    role_eligible, role_dropped = _filter_by_source_role(deduped, source_configs, context)
    if role_dropped:
        context.warnings.append(
            f"source-role policy dropped {len(role_dropped)} standalone low-evidence metadata records"
        )
    ordered = _sort_records(role_eligible)
    prior_promotions, history_evidence = load_promotion_history(output_root / "data", digest_date)
    ordered = apply_promotion_history(ordered, prior_promotions)
    metadata["promotion_history"] = history_evidence
    metadata["retrieval_v3"]["source_diversity_unique_marginal_recall"] = source_diversity_metrics(ranked_before_coverage)
    metadata["retrieval_v3"]["query_marginal_yield"] = query_marginal_yield(ranked_before_coverage)
    metadata["retrieval_v3"]["evidence_metrics"] = evidence_metrics(ranked_before_coverage)
    _update_source_health_after_pipeline(context, ranked, reliable, deduped, ordered)
    source_health = context.source_health_summary()
    from lattice_digest.evidence_contract import propagate_source_health
    ordered = propagate_source_health(ordered, source_health)
    degraded_sources = [
        str(item.get("source"))
        for item in source_health
        if item.get("runtime_state") == "partial" or item.get("health_status") in {"yellow", "red"}
    ]
    metadata["completion_state"] = "degraded_complete" if degraded_sources else "complete"
    metadata.update(derive_authority(ordered, source_health, source_configs=source_configs))
    metadata["degraded_sources"] = degraded_sources
    metadata["runtime_journal"] = str(context.runtime_journal_path)
    context.checkpoint(
        "PIPELINE_FINALIZED",
        {"completion_state": metadata["completion_state"], "final_records": len(ordered)},
    )
    if args.candidate_ledger and not args.dry_run:
        ledger = build_candidate_ledger(
            records,
            ranked_before_coverage,
            coverage_kept,
            reliable,
            deduped,
            ordered,
            source_health,
            digest_date,
            context.query_attempts,
            run_id=context.run_id,
            run_started_at=context.run_started_at,
            raw_occurrences=context.raw_occurrences,
            normalized_candidates=context.normalized_candidates,
            route_events=context.route_events,
        )
        write_candidate_ledger(ledger, output_root, digest_date)
    # Actual finish is journaled after durable publication. It cannot truthfully
    # be embedded in an artifact before that artifact has finished being written.
    metadata.update(schedule_telemetry(run_datetime))
    if args.coverage_start:
        metadata['trigger_kind'] = 'BACKFILL'
    metadata['source_query_runtime'] = list(context.query_attempts)
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
        print(generate_markdown(ordered, digest_date, dropped_count, source_health, context.warnings, since_window, metadata, source_configs=source_configs))
        return 0

    write_source_health_ledger(source_health, output_root, digest_date, run_datetime)

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
        written.extend(_archive_existing_provisional(output_root, digest_date, existing_metadata))
    if outputs & {"json", "markdown", "md"}:
        try:
            written.extend(publish_daily_pair(ordered, output_root, digest_date, dropped_count,
                                             source_health, context.warnings, since_window, metadata,
                                             force=args.force or bool(supersedes), source_configs=source_configs))
        except (ValueError, OSError) as exc:
            print(f"Daily canonical promotion failed: {exc}")
            return 2
    written.append(write_sqlite(ordered, output_root / "papers.db"))
    context.checkpoint('RUN_FINISHED', schedule_telemetry(run_datetime, datetime.now(ZoneInfo('Asia/Singapore'))))

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
