from __future__ import annotations

import socket
import ssl
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from scripts.probe_source_connectivity import classify_error, iacr_cache_state, semantic_scholar_key_state


def test_semantic_scholar_key_state_does_not_expose_value() -> None:
    state = semantic_scholar_key_state({"SEMANTIC_SCHOLAR_API_KEY": "fake-secret-value"})

    assert state == {
        "env_var": "SEMANTIC_SCHOLAR_API_KEY",
        "present": True,
        "length": len("fake-secret-value"),
    }
    assert "fake-secret-value" not in str(state)


def test_semantic_scholar_missing_key_is_reported_as_absent() -> None:
    state = semantic_scholar_key_state({})

    assert state["present"] is False
    assert state["length"] == 0


def test_classify_dns_url_error() -> None:
    error = urllib.error.URLError(socket.gaierror("name resolution failed"))

    classified = classify_error(error)

    assert classified["error_type"] == "dns_error"
    assert classified["failure_class"] == "dns"
    assert classified["retryable"] is True


def test_classify_tls_url_error() -> None:
    error = urllib.error.URLError(ssl.SSLError("certificate verify failed"))

    classified = classify_error(error)

    assert classified["error_type"] == "tls_error"
    assert classified["failure_class"] == "tls"
    assert classified["retryable"] is True


def test_classify_http_rate_limit() -> None:
    error = urllib.error.HTTPError("https://example.test", 429, "Too Many Requests", hdrs=None, fp=None)

    classified = classify_error(error)

    assert classified["error_type"] == "rate_limit"
    assert classified["failure_class"] == "rate_limit"
    assert classified["status_code"] == 429
    assert classified["retryable"] is True


def test_classify_http_auth_failure() -> None:
    error = urllib.error.HTTPError("https://example.test", 403, "Forbidden", hdrs=None, fp=None)

    classified = classify_error(error)

    assert classified["error_type"] == "auth_or_forbidden"
    assert classified["failure_class"] == "api_key_or_auth"
    assert classified["status_code"] == 403
    assert classified["retryable"] is False


def test_classify_http_server_error() -> None:
    error = urllib.error.HTTPError("https://example.test", 500, "Internal Server Error", hdrs=None, fp=None)

    classified = classify_error(error)

    assert classified["error_type"] == "server_error"
    assert classified["failure_class"] == "http_status"
    assert classified["status_code"] == 500
    assert classified["retryable"] is True


def test_iacr_cache_state_reports_attempt_and_cache_without_writing(tmp_path: Path) -> None:
    now = datetime(2026, 6, 7, tzinfo=timezone.utc)
    (tmp_path / "iacr_eprint_2026-06-07.attempt").write_text("attempt", encoding="utf-8")

    state = iacr_cache_state(cache_dir=tmp_path, now=now)

    assert state["today_utc"] == "2026-06-07"
    assert state["attempt_marker_exists"] is True
    assert state["cache_xml_exists"] is False
