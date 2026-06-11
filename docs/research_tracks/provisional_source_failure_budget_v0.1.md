# Provisional Source Failure Budget v0.1

These bands are observational policy. They are not hard-coded production thresholds.

| Band | Provisional interpretation | Example signals |
|---|---|---|
| `healthy_observation` | complete, observable run with no starvation | artifacts complete, no all-red state, high source availability |
| `degraded_but_usable` | usable output despite partial source degradation | yellow sources, bounded retryable failures, records remain traceable |
| `source_starved_warning` | discovery result cannot support absence claims | 0 records and all-red/unreachable sources |
| `diagnostic_required` | repeated or structural failure needs manual investigation | missing artifact, recurring starvation, stale weekly coverage, CI/local divergence |
| `insufficient_evidence` | no defensible stability conclusion | no actual post-tag sample or missing evidence class |

Suggested initial warning references:

- artifact completeness below 100%: diagnostic review;
- any source-starved run: warning;
- repeated source-starved runs in one seven-run window: diagnostic required;
- reachability below 80%: degraded observation;
- IACR latest below 85%: monitor/recover;
- Semantic Scholar at 0%: optional enrichment unavailable.

All numeric references remain `TODO_VERIFY` until post-tag evidence requirements are met.
