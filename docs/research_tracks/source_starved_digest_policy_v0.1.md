# Source-Starved Digest Policy v0.1

Status: public source-health interpretation policy.

# Definition

A digest is source-starved when:

- generated record count is 0; and
- all or most configured external sources are red; or
- source-health warnings show retryable DNS/TLS/proxy/timeout/rate-limit/server failures.

# Interpretation

Source-starved output is not evidence that no relevant papers exist.

It means the radar did not receive reliable enough source input.

# Empty Digest

An empty digest under source starvation should be labeled:

```text
source-starved; do not interpret as no relevant papers
```

# Empty Handoff

An empty handoff under source starvation should be labeled:

```text
source-starved handoff; weekly input may be incomplete
```

# Manual Recovery

Run:

```powershell
python scripts\probe_source_connectivity.py
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
scripts\run_weekly_handoff.bat
```

# Non-Claims

Source-starved status does not change ranking thresholds, taxonomy, source scoring, or negative keyword semantics.

