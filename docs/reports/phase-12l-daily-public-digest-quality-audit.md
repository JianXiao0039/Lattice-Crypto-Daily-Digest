# Phase 12L Daily Public Digest Quality Audit

生成日期：2026-06-08

# Executive Summary

The latest persisted daily public digest artifact on disk is `data/2026-06-08.json`. It contains 6 records, 2 green sources, 4 yellow sources, 0 red sources, and should be treated as a degraded-but-usable day rather than a source-starved day.

The source recovery pilot in Phase 12L also confirmed that `data/2026-06-07.json` remains a historical source-starved artifact with 0 records and all sources red. The daily quality policy therefore needs to distinguish current recovery state from stale failure artifacts on disk.

# Current Audit Snapshot

| Metric | Value |
| --- | --- |
| latest_daily_json | `data/2026-06-08.json` |
| digest_record_count | 6 |
| source_green_count | 2 |
| source_yellow_count | 4 |
| source_red_count | 0 |
| retryable_error_count | 1 |
| source_starved | false |
| generated_artifacts_present | true |
| manual_recovery_needed | conditional; needed only when future daily runs fall back to all-red or stale-source state |

# Historical Failure Reference

| Metric | Value |
| --- | --- |
| historical_source_starved_json | `data/2026-06-07.json` |
| digest_record_count | 0 |
| source_red_count | 6 |
| source_starved | true |

# Quality Gap

The current gap is not only external source instability. It is also observability:

- a source-starved artifact can remain on disk next to a newer recovered artifact;
- weekly outputs can still look healthy because they are supported by earlier successful days;
- a connectivity probe may pass while a real ingestion path still degrades, as shown by DBLP probe success versus latest daily `ssl_error`.

# Required Daily Quality Gates

- expose source health clearly;
- expose source-starved classification clearly;
- distinguish empty digest because of source starvation from empty digest because nothing relevant was found;
- show IACR latest recovery status;
- show Semantic Scholar enrichment availability without printing secrets;
- end with validation summary and `git status -sb`;
- never auto-commit or auto-push.

# Recommended Manual Commands

```powershell
scripts\daily_quality_probe.bat
python scripts\probe_source_connectivity.py
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
git status -sb
```

# Non-Claims

- A source-starved daily digest is not evidence that no relevant papers exist.
- A degraded-but-usable daily digest with yellow sources still requires conservative interpretation.
- Semantic Scholar HTTP 429 means advisory enrichment is temporarily limited; it does not mean papers are irrelevant.
- Manual recovery success does not retroactively validate an older stale artifact unless new artifacts are written.
