# Daily Automation Monitoring Loop v0.1

## Purpose

Provide a manual observation loop for Daily Public Digest Run without adding schedules, services, or uncontrolled retries.

## After Each Run

1. Confirm `digests/YYYY-MM-DD.md` and `data/YYYY-MM-DD.json` exist, or capture the explicit failure reason.
2. Record digest count, final count, and high-priority count.
3. Record source green/yellow/red counts and retryable errors.
4. Classify zero records:
   - all red: source-starved;
   - at least one healthy source: empty result requiring coverage review.
5. Inspect IACR latest status and record count.
6. Inspect Semantic Scholar status without printing the API key.
7. Verify manual recovery is needed before using retry flags.
8. If publication is expected, verify Git tracking and `origin/main` presence separately.

## Manual Recovery Trigger

Use manual recovery when:

- all effective sources are red;
- IACR latest is blocked by a failed-attempt guard;
- a known date is missing its artifacts;
- network/TLS/proxy health has recovered after a failed run.

## Stop Conditions

Stop and investigate when:

- outputs are missing without an error artifact;
- zero records are presented as normal success despite all-red health;
- API credentials appear in output;
- generated files exist but intended publication tracking is absent.

## Do Not Automate

- no background retry loop;
- no Task Scheduler or cron;
- no automatic source-policy changes;
- no automatic Git add/commit/push outside an explicitly approved publication flow;
- no private workspace writes.
