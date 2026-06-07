from __future__ import annotations

import argparse
import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_ROOT / "cache"

SOURCE_TARGETS = [
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
]


def _proxy_notes() -> list[str]:
    notes = []
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        if os.environ.get(name):
            notes.append(f"{name} is set")
    return notes


def semantic_scholar_key_state(env: dict[str, str] | None = None) -> dict[str, Any]:
    source = env if env is not None else os.environ
    value = source.get("SEMANTIC_SCHOLAR_API_KEY") or ""
    return {
        "env_var": "SEMANTIC_SCHOLAR_API_KEY",
        "present": bool(value.strip()),
        "length": len(value.strip()) if value.strip() else 0,
    }


def classify_error(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, urllib.error.HTTPError):
        code = int(exc.code)
        retryable = code in {408, 425, 429, 500, 502, 503, 504}
        if code == 429:
            error_type = "rate_limit"
        elif code in {401, 403}:
            error_type = "auth_or_forbidden"
        elif code >= 500:
            error_type = "server_error"
        else:
            error_type = "http_error"
        return {"error_type": error_type, "status_code": code, "retryable": retryable, "message": str(exc.reason)}
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, ssl.SSLError):
            return {"error_type": "tls_error", "status_code": None, "retryable": True, "message": str(reason)}
        if isinstance(reason, socket.gaierror):
            return {"error_type": "dns_error", "status_code": None, "retryable": True, "message": str(reason)}
        if isinstance(reason, TimeoutError) or isinstance(reason, socket.timeout):
            return {"error_type": "timeout", "status_code": None, "retryable": True, "message": str(reason)}
        return {"error_type": "url_error", "status_code": None, "retryable": True, "message": str(reason)}
    if isinstance(exc, TimeoutError) or isinstance(exc, socket.timeout):
        return {"error_type": "timeout", "status_code": None, "retryable": True, "message": str(exc)}
    if isinstance(exc, ssl.SSLError):
        return {"error_type": "tls_error", "status_code": None, "retryable": True, "message": str(exc)}
    return {"error_type": type(exc).__name__, "status_code": None, "retryable": False, "message": str(exc)}


def iacr_cache_state(cache_dir: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    root = cache_dir or CACHE_DIR
    today = (now or datetime.now(timezone.utc)).date().isoformat()
    attempt_path = root / f"iacr_eprint_{today}.attempt"
    cache_path = root / f"iacr_eprint_{today}.xml"
    return {
        "today_utc": today,
        "attempt_marker_exists": attempt_path.exists(),
        "cache_xml_exists": cache_path.exists(),
        "attempt_marker": _display_path(attempt_path) if attempt_path.exists() else None,
        "cache_xml": _display_path(cache_path) if cache_path.exists() else None,
    }


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _build_request(target: dict[str, str]) -> urllib.request.Request:
    headers = {"User-Agent": "lattice-crypto-daily-digest-source-probe/0.1"}
    if target["source"] == "semantic_scholar":
        key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
        if key:
            headers["x-api-key"] = key
    return urllib.request.Request(target["url"], headers=headers)


def _parse_iacr_records(content: bytes) -> dict[str, Any]:
    try:
        from lattice_digest.sources.iacr import parse_iacr_feed

        records = parse_iacr_feed(content.decode("utf-8", errors="replace"))
        return {"parser_status": "parsed", "records": len(records), "parser_error": None}
    except Exception as exc:  # pragma: no cover - covered through integration/manual probe.
        return {"parser_status": "parser_failure", "records": 0, "parser_error": f"{type(exc).__name__}: {exc}"}


def probe_target(target: dict[str, str], timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    result: dict[str, Any] = {
        "source": target["source"],
        "endpoint_label": target["endpoint_label"],
        "url": target["url"],
        "reachable": False,
        "status_code": None,
        "error_type": None,
        "timeout_seconds": timeout,
        "tls_error": False,
        "dns_error": False,
        "proxy_related_clue": False,
        "retryable": False,
        "elapsed_seconds": None,
        "notes": [],
    }
    request = _build_request(target)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read(512_000)
            result["reachable"] = True
            result["status_code"] = int(getattr(response, "status", 200))
            result["retryable"] = False
            result["notes"].append(f"read_bytes={len(content)}")
            if target["source"] == "iacr_eprint":
                result.update(_parse_iacr_records(content))
    except Exception as exc:
        classified = classify_error(exc)
        result.update(classified)
        result["tls_error"] = classified["error_type"] == "tls_error"
        result["dns_error"] = classified["error_type"] == "dns_error"
        message = str(classified.get("message") or "").lower()
        result["proxy_related_clue"] = "proxy" in message or bool(_proxy_notes())
        if target["source"] == "iacr_eprint":
            result.update({"parser_status": "not_run", "records": 0, "parser_error": None})
    finally:
        result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    if target["source"] == "semantic_scholar":
        result["semantic_scholar_key"] = semantic_scholar_key_state()
        result["notes"].append("Semantic Scholar API key value was not printed.")
    if target["source"] == "iacr_eprint":
        result["iacr_cache_state"] = iacr_cache_state()
    proxy_notes = _proxy_notes()
    if proxy_notes:
        result["notes"].extend(proxy_notes)
    return result


def build_probe_report(timeout: float) -> dict[str, Any]:
    probes = [probe_target(target, timeout=timeout) for target in SOURCE_TARGETS]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "semantic_scholar_key": semantic_scholar_key_state(),
        "iacr_cache_state": iacr_cache_state(),
        "probes": probes,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manually probe source connectivity without writing files.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-source timeout in seconds.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_probe_report(timeout=args.timeout)
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
