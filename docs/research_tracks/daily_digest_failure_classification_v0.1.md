# Daily Digest Failure Classification v0.1

Status: public failure classification doc.

# Purpose

Normalize daily reliability failure modes so that automation prompts and manual runbooks do not confuse empty output with healthy output.

# Classes

| Class | Meaning | Typical action |
| --- | --- | --- |
| `reachable` | probe endpoint reachable and responded normally | continue |
| `dns` | name resolution failure | check DNS / network / VPN |
| `tls` | TLS/SSL handshake or EOF failure | retry manually; inspect SSL path |
| `proxy` | proxy-related configuration clue | inspect proxy environment |
| `timeout` | request timed out | retry manually; do not overinterpret empty output |
| `http_status` | endpoint returned non-auth, non-rate-limit HTTP error | inspect source stability |
| `rate_limit` | upstream throttling | retry manually later; do not treat as irrelevance |
| `api_key_or_auth` | auth / forbidden condition | verify safe key presence and permissions |
| `parser` | endpoint reachable but parse failed | inspect parser / format drift |
| `failed_attempt_guard` | run intentionally refused to keep hammering a failing source | use explicit manual retry path |
| `cache_hit` | source latest data served from same-day cache | acceptable recovery status |
| `source_starved` | latest daily artifact has 0 records and effective all-red / unreachable source context | label explicitly; do not call it normal success |

# Interpretation Rules

- `source_starved` is stronger than `empty`;
- `reachable` in probe mode does not guarantee green ingest status;
- `cache_hit` is valid evidence for IACR latest recovery;
- `rate_limit` and `api_key_or_auth` must be separated.
