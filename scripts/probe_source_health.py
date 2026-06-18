from __future__ import annotations

import argparse
import json
import os
import socket
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIMEOUT_SECONDS = 8.0
LOW_LOAD_PAUSE_SECONDS = 1.0
USER_AGENT = "lattice-crypto-daily-digest-source-health-probe/0.1"

SOURCE_TARGETS: tuple[dict[str, str], ...] = (
    {
        "source": "arxiv",
        "endpoint_label": "arXiv API query",
        "url": "https://export.arxiv.org/api/query?search_query=all%3AML-KEM&start=0&max_results=1",
    },
    {
        "source": "crossref",
        "endpoint_label": "Crossref works query",
        "url": "https://api.crossref.org/works?query=ML-KEM&rows=1",
    },
    {
        "source": "dblp",
        "endpoint_label": "DBLP publication search",
        "url": "https://dblp.org/search/publ/api?q=ML-KEM&format=json&h=1",
    },
    {
        "source": "iacr_eprint",
        "endpoint_label": "IACR ePrint RSS/latest",
        "url": "https://eprint.iacr.org/rss/rss.xml",
    },
    {
        "source": "openalex",
        "endpoint_label": "OpenAlex works query",
        "url": "https://api.openalex.org/works?search=ML-KEM&per-page=1",
    },
    {
        "source": "semantic_scholar",
        "endpoint_label": "Semantic Scholar paper search",
        "url": "https://api.semanticscholar.org/graph/v1/paper/search?query=ML-KEM&limit=1&fields=title",
    },
)


def semantic_scholar_key_state(env: dict[str, str] | None = None) -> dict[str, Any]:
    source = env if env is not None else os.environ
    value = (source.get("SEMANTIC_SCHOLAR_API_KEY") or "").strip()
    return {
        "env_var": "SEMANTIC_SCHOLAR_API_KEY",
        "present": bool(value),
        "status": "present" if value else "missing_key",
    }


def retry_after_from_headers(headers: Any) -> str | None:
    if headers is None:
        return None
    try:
        value = headers.get("Retry-After")
    except AttributeError:
        return None
    return str(value).strip() if value else None


def classify_exception(exc: BaseException, *, source: str | None = None) -> dict[str, Any]:
    if isinstance(exc, urllib.error.HTTPError):
        code = int(exc.code)
        retryable = code in {408, 425, 429, 500, 502, 503, 504}
        if code == 429:
            status = "rate_limited"
            failure_class = "rate_limited"
        elif code in {401, 403}:
            status = "auth_failed" if source == "semantic_scholar" else "forbidden"
            failure_class = "authentication_or_access"
        elif code >= 500:
            status = "server_error"
            failure_class = "http_5xx"
        else:
            status = "http_error"
            failure_class = "http_status"
        return {
            "status": status,
            "failure_class": failure_class,
            "status_code": code,
            "retryable": retryable,
            "retry_after": retry_after_from_headers(exc.headers),
            "message": str(exc.reason),
        }
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, ssl.SSLError):
            return {
                "status": "ssl_failure",
                "failure_class": "tls",
                "status_code": None,
                "retryable": True,
                "retry_after": None,
                "message": str(reason),
            }
        if isinstance(reason, socket.gaierror):
            return {
                "status": "dns_failure",
                "failure_class": "dns",
                "status_code": None,
                "retryable": True,
                "retry_after": None,
                "message": str(reason),
            }
        if isinstance(reason, TimeoutError) or isinstance(reason, socket.timeout):
            return {
                "status": "timeout",
                "failure_class": "timeout",
                "status_code": None,
                "retryable": True,
                "retry_after": None,
                "message": str(reason),
            }
        return {
            "status": "network_failure",
            "failure_class": "url_error",
            "status_code": None,
            "retryable": True,
            "retry_after": None,
            "message": str(reason),
        }
    if isinstance(exc, TimeoutError) or isinstance(exc, socket.timeout):
        return {
            "status": "timeout",
            "failure_class": "timeout",
            "status_code": None,
            "retryable": True,
            "retry_after": None,
            "message": str(exc),
        }
    if isinstance(exc, ssl.SSLError):
        return {
            "status": "ssl_failure",
            "failure_class": "tls",
            "status_code": None,
            "retryable": True,
            "retry_after": None,
            "message": str(exc),
        }
    return {
        "status": "unknown_failure",
        "failure_class": type(exc).__name__,
        "status_code": None,
        "retryable": False,
        "retry_after": None,
        "message": str(exc),
    }


def classify_success_payload(source: str, content: bytes) -> dict[str, Any]:
    if source == "openalex":
        try:
            payload = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError as exc:
            return {"status": "parser_failure", "record_count": 0, "message": str(exc)}
        results = payload.get("results")
        count = len(results) if isinstance(results, list) else 0
        return {
            "status": "empty_response" if count == 0 else "ok",
            "record_count": count,
            "message": "valid OpenAlex response with zero results" if count == 0 else "OpenAlex returned results",
        }
    if source == "semantic_scholar":
        try:
            payload = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError as exc:
            return {"status": "parser_failure", "record_count": 0, "message": str(exc)}
        data = payload.get("data")
        count = len(data) if isinstance(data, list) else 0
        return {
            "status": "empty_response" if count == 0 else "ok",
            "record_count": count,
            "message": "no candidates to enrich" if count == 0 else "Semantic Scholar returned candidates",
        }
    if source == "crossref":
        try:
            payload = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError as exc:
            return {"status": "parser_failure", "record_count": 0, "message": str(exc)}
        items = payload.get("message", {}).get("items")
        count = len(items) if isinstance(items, list) else 0
        return {
            "status": "empty_response" if count == 0 else "ok",
            "record_count": count,
            "message": "valid Crossref response with zero items" if count == 0 else "Crossref returned items",
        }
    if source == "iacr_eprint":
        try:
            from lattice_digest.sources.iacr import parse_iacr_feed

            records = parse_iacr_feed(content.decode("utf-8", errors="replace"))
        except Exception as exc:  # pragma: no cover - integration path.
            return {"status": "parser_failure", "record_count": 0, "message": f"{type(exc).__name__}: {exc}"}
        return {
            "status": "zero_latest_records" if len(records) == 0 else "ok",
            "record_count": len(records),
            "message": "IACR feed parsed with zero records" if not records else "IACR feed parsed",
        }
    if source == "arxiv":
        text = content.decode("utf-8", errors="replace")
        count = text.count("<entry>")
        return {
            "status": "empty_response" if count == 0 else "ok",
            "record_count": count,
            "message": "valid arXiv response with zero entries" if count == 0 else "arXiv returned entries",
        }
    if source == "dblp":
        try:
            payload = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError as exc:
            return {"status": "parser_failure", "record_count": 0, "message": str(exc)}
        hits = payload.get("result", {}).get("hits", {}).get("hit")
        count = len(hits) if isinstance(hits, list) else 0
        return {
            "status": "empty_response" if count == 0 else "ok",
            "record_count": count,
            "message": "valid DBLP response with zero hits" if count == 0 else "DBLP returned hits",
        }
    return {"status": "ok", "record_count": None, "message": "source reached"}


def classify_iacr_latest_state(
    *,
    reachable: bool,
    parsed: bool,
    record_count: int,
    failed_attempt_guard: bool = False,
    cache_hit: bool = False,
) -> dict[str, Any]:
    if failed_attempt_guard:
        status = "failed_attempt_guard"
    elif cache_hit:
        status = "cache_hit"
    elif not reachable:
        status = "network_failure"
    elif not parsed:
        status = "parser_failure"
    elif record_count == 0:
        status = "zero_latest_records"
    else:
        status = "normal_latest_feed_success"
    return {
        "source": "iacr_eprint",
        "latest_feed_status": status,
        "latest_feed_records": record_count,
        "interpretable_as_no_relevant_papers": False if status != "normal_latest_feed_success" else None,
    }


def _build_request(target: dict[str, str], env: dict[str, str] | None = None) -> urllib.request.Request:
    source_env = env if env is not None else os.environ
    headers = {"User-Agent": USER_AGENT}
    if target["source"] == "semantic_scholar":
        key = (source_env.get("SEMANTIC_SCHOLAR_API_KEY") or "").strip()
        if key:
            headers["x-api-key"] = key
    return urllib.request.Request(target["url"], headers=headers)


def probe_target(
    target: dict[str, str],
    *,
    timeout: float,
    env: dict[str, str] | None = None,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    started = time.perf_counter()
    result: dict[str, Any] = {
        "source": target["source"],
        "endpoint_label": target["endpoint_label"],
        "url": target["url"],
        "reachable": False,
        "status": "not_run",
        "failure_class": None,
        "status_code": None,
        "retryable": False,
        "retry_after": None,
        "record_count": None,
        "elapsed_seconds": None,
        "notes": [],
    }
    if target["source"] == "semantic_scholar":
        result["semantic_scholar_key"] = semantic_scholar_key_state(env)
        if not result["semantic_scholar_key"]["present"]:
            result["status"] = "missing_key"
            result["notes"].append("Semantic Scholar key absent; probe still checks public quota path.")
    request = _build_request(target, env)
    try:
        with opener(request, timeout=timeout) as response:
            content = response.read(512_000)
            result["reachable"] = True
            result["status_code"] = int(getattr(response, "status", 200))
            result.update(classify_success_payload(target["source"], content))
    except Exception as exc:
        classified = classify_exception(exc, source=target["source"])
        result.update(classified)
    finally:
        result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    if target["source"] == "semantic_scholar":
        result["notes"].append("Semantic Scholar API key value was not printed.")
    if target["source"] == "iacr_eprint":
        latest_status = classify_iacr_latest_state(
            reachable=bool(result["reachable"]),
            parsed=result.get("status") in {"ok", "zero_latest_records"},
            record_count=int(result.get("record_count") or 0),
        )
        result.update(latest_status)
    return result


def build_probe_report(
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    low_load: bool = False,
    targets: tuple[dict[str, str], ...] = SOURCE_TARGETS,
    env: dict[str, str] | None = None,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    probes: list[dict[str, Any]] = []
    for index, target in enumerate(targets):
        if low_load and index:
            time.sleep(LOW_LOAD_PAUSE_SECONDS)
        probes.append(probe_target(target, timeout=timeout, env=env, opener=opener))
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "low_load" if low_load else "single_pass",
        "anti_abuse_policy": {
            "manual_only": True,
            "no_proxy_rotation": True,
            "no_fake_user_agent_rotation": True,
            "honor_retry_after": True,
            "no_captcha_or_access_control_bypass": True,
            "one_request_per_source_in_low_load_probe": True,
        },
        "semantic_scholar_key": semantic_scholar_key_state(env),
        "probes": probes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a manual, low-load source health probe.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--low-load", action="store_true", help="Pause between sources and run one request per source.")
    args = parser.parse_args(argv)
    report = build_probe_report(timeout=args.timeout, low_load=args.low_load)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
