# Portable Repository Path Contract v0.1

## Contract

Repository-relative paths serialized into dictionaries, JSON, Markdown, reports, or snapshots must use `/` on every operating system.

Use:

```python
path.relative_to(project_root).as_posix()
```

Do not serialize portable fields with plain `str(relative_path)`.

## Covered Reliability Fields

- `latest_daily_artifact`
- `latest_weekly_artifact`
- `latest_handoff_artifact`
- dashboard `daily_json`
- dashboard `daily_markdown`
- dashboard `weekly_json`
- dashboard `weekly_handoff_json`

Missing artifacts retain `None`; field names are unchanged.
