from __future__ import annotations

import socket
import ssl
import urllib.error

from scripts.probe_source_health import (
    classify_exception,
    classify_iacr_latest_state,
    classify_success_payload,
    semantic_scholar_key_state,
)


def test_http_429_is_rate_limited_not_generic_failure() -> None:
    error = urllib.error.HTTPError("https://example.test", 429, "Too Many Requests", hdrs=None, fp=None)

    result = classify_exception(error, source="arxiv")

    assert result["status"] == "rate_limited"
    assert result["failure_class"] == "rate_limited"
    assert result["retryable"] is True


def test_dblp_ssl_failure_is_separate_from_generic_network_failure() -> None:
    error = urllib.error.URLError(ssl.SSLError("certificate verify failed"))

    result = classify_exception(error, source="dblp")

    assert result["status"] == "ssl_failure"
    assert result["failure_class"] == "tls"


def test_semantic_scholar_missing_key_is_sanitized() -> None:
    state = semantic_scholar_key_state({})

    assert state == {
        "env_var": "SEMANTIC_SCHOLAR_API_KEY",
        "present": False,
        "status": "missing_key",
    }
    assert "API_KEY=" not in str(state)


def test_semantic_scholar_auth_and_rate_limit_are_distinct() -> None:
    auth = urllib.error.HTTPError("https://example.test", 403, "Forbidden", hdrs=None, fp=None)
    rate = urllib.error.HTTPError("https://example.test", 429, "Too Many Requests", hdrs=None, fp=None)

    assert classify_exception(auth, source="semantic_scholar")["status"] == "auth_failed"
    assert classify_exception(rate, source="semantic_scholar")["status"] == "rate_limited"


def test_dns_and_timeout_are_classified_separately() -> None:
    dns = urllib.error.URLError(socket.gaierror("name resolution failed"))
    timeout = urllib.error.URLError(socket.timeout("timed out"))

    assert classify_exception(dns)["status"] == "dns_failure"
    assert classify_exception(timeout)["status"] == "timeout"


def test_openalex_empty_response_is_not_network_failure() -> None:
    result = classify_success_payload("openalex", b'{"results": []}')

    assert result["status"] == "empty_response"
    assert result["record_count"] == 0


def test_iacr_failed_or_zero_latest_is_not_no_relevant_papers() -> None:
    failed = classify_iacr_latest_state(reachable=False, parsed=False, record_count=0)
    zero = classify_iacr_latest_state(reachable=True, parsed=True, record_count=0)

    assert failed["latest_feed_status"] == "network_failure"
    assert failed["interpretable_as_no_relevant_papers"] is False
    assert zero["latest_feed_status"] == "zero_latest_records"
    assert zero["interpretable_as_no_relevant_papers"] is False
