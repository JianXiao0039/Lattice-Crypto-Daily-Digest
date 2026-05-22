from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass
class HttpWarning:
    url: str
    source: str = "http"
    status_code: int | None = None
    reason: str = ""
    attempts: int = 0
    retry_after: float | None = None
    error: str | None = None

    def to_message(self) -> str:
        status = f"HTTP {self.status_code}" if self.status_code else "request error"
        detail = self.reason or self.error or "unknown error"
        retry = f"; retry_after={self.retry_after:g}s" if self.retry_after is not None else ""
        return f"{self.source}: skipped {self.url} after {self.attempts} attempt(s): {status} {detail}{retry}"


@dataclass
class HttpResponse:
    ok: bool
    url: str
    status_code: int | None = None
    text: str = ""
    from_cache: bool = False
    warning: HttpWarning | None = None


_LAST_REQUEST_BY_DOMAIN: dict[str, float] = {}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _cache_paths(cache_dir: Path, url: str) -> tuple[Path, Path]:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_dir / f"{digest}.body", cache_dir / f"{digest}.json"


def _read_cache(cache_dir: Path, url: str, ttl: timedelta, now: datetime) -> HttpResponse | None:
    body_path, meta_path = _cache_paths(cache_dir, url)
    if not body_path.exists() or not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        fetched_at = datetime.fromisoformat(meta["fetched_at"])
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        if now - fetched_at > ttl:
            return None
        return HttpResponse(
            ok=True,
            url=url,
            status_code=int(meta.get("status_code") or 200),
            text=body_path.read_text(encoding="utf-8"),
            from_cache=True,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return None


def _write_cache(cache_dir: Path, url: str, text: str, status_code: int, now: datetime) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    body_path, meta_path = _cache_paths(cache_dir, url)
    body_path.write_text(text, encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            {
                "url": url,
                "status_code": status_code,
                "fetched_at": now.isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _retry_after_seconds(value: str | None, now: datetime) -> float | None:
    if not value:
        return None
    raw = value.strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        pass
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return max(0.0, (parsed - now).total_seconds())
    except (TypeError, ValueError, IndexError):
        return None


def _respect_domain_interval(
    url: str,
    min_interval_seconds: float,
    sleep_func: Callable[[float], None],
    monotonic_func: Callable[[], float],
) -> None:
    if min_interval_seconds <= 0:
        return
    domain = _domain(url)
    last = _LAST_REQUEST_BY_DOMAIN.get(domain)
    current = monotonic_func()
    if last is not None:
        delay = min_interval_seconds - (current - last)
        if delay > 0:
            sleep_func(delay)
    _LAST_REQUEST_BY_DOMAIN[domain] = monotonic_func()


def request_text(
    url: str,
    *,
    source: str = "http",
    user_agent: str,
    timeout_seconds: int = 20,
    headers: dict[str, str] | None = None,
    cache_dir: Path,
    cache_ttl_seconds: int = 12 * 60 * 60,
    min_interval_seconds: float = 1.0,
    max_retries: int = 2,
    retry_statuses: tuple[int, ...] = (429, 503),
    warnings: list[str] | None = None,
    sleep_func: Callable[[float], None] = time.sleep,
    monotonic_func: Callable[[], float] = time.monotonic,
    now_func: Callable[[], datetime] = _now_utc,
    open_func=None,
) -> HttpResponse:
    now = now_func()
    cache_hit = _read_cache(cache_dir, url, timedelta(seconds=cache_ttl_seconds), now)
    if cache_hit is not None:
        return cache_hit

    attempts = max(1, max_retries + 1)
    request_headers = {"User-Agent": user_agent, **(headers or {})}
    opener = open_func or urlopen
    last_warning: HttpWarning | None = None

    for attempt in range(1, attempts + 1):
        _respect_domain_interval(url, min_interval_seconds, sleep_func, monotonic_func)
        request = Request(url, headers=request_headers)
        try:
            with opener(request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
                status_code = int(getattr(response, "status", None) or getattr(response, "code", None) or 200)
                _write_cache(cache_dir, url, body, status_code, now_func())
                return HttpResponse(ok=True, url=url, status_code=status_code, text=body)
        except HTTPError as exc:
            status_code = int(exc.code)
            retry_after = _retry_after_seconds(exc.headers.get("Retry-After"), now_func())
            last_warning = HttpWarning(
                url=url,
                source=source,
                status_code=status_code,
                reason=str(exc.reason),
                attempts=attempt,
                retry_after=retry_after,
            )
            if status_code not in retry_statuses or attempt >= attempts:
                break
            delay = retry_after if retry_after is not None else min(60.0, 2 ** (attempt - 1))
            sleep_func(delay)
        except (URLError, TimeoutError, OSError) as exc:
            last_warning = HttpWarning(
                url=url,
                source=source,
                reason=exc.__class__.__name__,
                attempts=attempt,
                error=str(exc),
            )
            break

    assert last_warning is not None
    if warnings is not None:
        warnings.append(last_warning.to_message())
    return HttpResponse(ok=False, url=url, warning=last_warning)


def request_json(*args, **kwargs) -> tuple[dict | None, HttpResponse]:
    response = request_text(*args, **kwargs)
    if not response.ok:
        return None, response
    try:
        return json.loads(response.text), response
    except json.JSONDecodeError as exc:
        warning = HttpWarning(
            url=response.url,
            source=kwargs.get("source", "http"),
            status_code=response.status_code,
            reason="invalid JSON",
            attempts=1,
            error=str(exc),
        )
        warnings = kwargs.get("warnings")
        if warnings is not None:
            warnings.append(warning.to_message())
        return None, HttpResponse(ok=False, url=response.url, status_code=response.status_code, warning=warning)
