# Source Retry Policy v0.1

Status: public manual retry policy.

# Purpose

Define when failed source requests may be retried manually without creating background automation.

# Normal Runs

Normal runs use existing source semantics and polite caching. Source failures are recorded in source health and should not silently become research conclusions.

# Retryable Failures

Retryable classes:

- DNS
- TLS
- proxy
- timeout
- HTTP 408 / 425 / 429 / 500 / 502 / 503 / 504
- source warning marked retryable
- failed attempt guard when explicit manual retry is intended

Usually not retryable until fixed:

- invalid request;
- API-key missing when the source requires it;
- API-key invalid / forbidden;
- parser failure with reproducible source content.

# Manual Retry Flags

Use `--retry-failed-sources` when a failed same-day attempt marker exists.

Use `--include-latest-sources` when source-native RSS/latest recovery is explicitly needed.

# Not Automated

Do not create retry loops, daemons, schedulers, watchers, cron jobs, startup tasks, or Task Scheduler tasks.

# Stop Conditions

Stop and inspect manually when:

- repeated auth failure occurs;
- repeated parser failure occurs;
- all sources fail with DNS/TLS/proxy symptoms;
- a source remains rate-limited;
- generated artifacts remain source-starved after recovery.

