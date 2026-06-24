from __future__ import annotations

import re
import os
import warnings
from datetime import date
from pathlib import Path


DAILY_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})\.(?P<suffix>md|json)$")
WEEKLY_RE = re.compile(r"^(?P<week>\d{4}-W\d{2})\.(?P<suffix>md|json)$")
MONTHLY_RE = re.compile(r"^(?P<month>\d{4}-\d{2})\.(?P<suffix>md|json)$")
LEGACY_FALLBACK_ENV = "LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK"
LEGACY_FALLBACK_TRUE_VALUES = {"1", "true", "yes", "on", "compat"}
LEGACY_FALLBACK_FALSE_VALUES = {"0", "false", "no", "off"}


def _date_text(value: date | str) -> str:
    text = value.isoformat() if isinstance(value, date) else str(value)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise ValueError(f"expected YYYY-MM-DD date, got {value!r}")
    return text


def _month_text(year: int | str, month: int | str | None = None) -> str:
    if month is None:
        text = str(year)
        if not re.fullmatch(r"\d{4}-\d{2}", text):
            raise ValueError(f"expected YYYY-MM month, got {year!r}")
        return text
    return f"{int(year):04d}-{int(month):02d}"


def _week_text(iso_year: int | str, iso_week: int | str | None = None) -> str:
    if iso_week is None:
        text = str(iso_year)
        if not re.fullmatch(r"\d{4}-W\d{2}", text):
            raise ValueError(f"expected YYYY-Www ISO week, got {iso_year!r}")
        return text
    return f"{int(iso_year):04d}-W{int(iso_week):02d}"


def daily_digest_path(value: date | str, root: Path = Path("digests")) -> Path:
    text = _date_text(value)
    return root / text[:4] / "daily" / f"{text}.md"


def daily_data_path(value: date | str, root: Path = Path("data")) -> Path:
    text = _date_text(value)
    return root / text[:4] / "daily" / f"{text}.json"


def weekly_digest_path(iso_year: int | str, iso_week: int | str | None = None, root: Path = Path("digests")) -> Path:
    week = _week_text(iso_year, iso_week)
    return root / week[:4] / "weekly" / f"{week}.md"


def weekly_data_path(iso_year: int | str, iso_week: int | str | None = None, root: Path = Path("data")) -> Path:
    week = _week_text(iso_year, iso_week)
    return root / week[:4] / "weekly" / f"{week}.json"


def monthly_digest_path(year: int | str, month: int | str | None = None, root: Path = Path("digests")) -> Path:
    text = _month_text(year, month)
    return root / text[:4] / "monthly" / f"{text}.md"


def monthly_data_path(year: int | str, month: int | str | None = None, root: Path = Path("data")) -> Path:
    text = _month_text(year, month)
    return root / text[:4] / "monthly" / f"{text}.json"


def legacy_daily_digest_candidates(value: date | str, root: Path = Path("digests")) -> list[Path]:
    text = _date_text(value)
    return [root / f"{text}.md"]


def legacy_daily_data_candidates(value: date | str, root: Path = Path("data")) -> list[Path]:
    text = _date_text(value)
    return [root / f"{text}.json"]


def legacy_weekly_digest_candidates(iso_year: int | str, iso_week: int | str | None = None, root: Path = Path("digests")) -> list[Path]:
    week = _week_text(iso_year, iso_week)
    return [root / "weekly" / f"{week}.md"]


def legacy_weekly_data_candidates(iso_year: int | str, iso_week: int | str | None = None, root: Path = Path("data")) -> list[Path]:
    week = _week_text(iso_year, iso_week)
    return [root / "weekly" / f"{week}.json"]


def legacy_monthly_digest_candidates(year: int | str, month: int | str | None = None, root: Path = Path("digests")) -> list[Path]:
    text = _month_text(year, month)
    return [root / "monthly" / f"{text}.md"]


def legacy_monthly_data_candidates(year: int | str, month: int | str | None = None, root: Path = Path("data")) -> list[Path]:
    text = _month_text(year, month)
    return [root / "monthly" / f"{text}.json"]


def legacy_fallback_allowed(allow_legacy_fallback: bool | None = None) -> bool:
    if allow_legacy_fallback is not None:
        return allow_legacy_fallback
    value = os.environ.get(LEGACY_FALLBACK_ENV)
    if value is None:
        return False
    normalized = value.strip().casefold()
    if normalized in LEGACY_FALLBACK_TRUE_VALUES:
        return True
    if normalized in LEGACY_FALLBACK_FALSE_VALUES:
        return False
    warnings.warn(
        f"{LEGACY_FALLBACK_ENV}={value!r} is not recognized; legacy fallback remains disabled.",
        RuntimeWarning,
        stacklevel=2,
    )
    return False


def resolve_existing(
    canonical: Path,
    legacy_candidates: list[Path],
    *,
    allow_legacy_fallback: bool | None = None,
) -> tuple[Path, bool]:
    if canonical.exists():
        return canonical, False
    if not legacy_fallback_allowed(allow_legacy_fallback):
        return canonical, False
    for candidate in legacy_candidates:
        if candidate.exists():
            warnings.warn(
                "Temporary legacy artifact fallback used: "
                f"canonical path {canonical} is missing; resolved legacy path {candidate}. "
                "Compatibility fallback is read-only and temporary.",
                RuntimeWarning,
                stacklevel=2,
            )
            return candidate, True
    return canonical, False


def parse_daily_artifact_path(path: Path) -> str | None:
    match = DAILY_RE.match(path.name)
    return match.group("date") if match else None


def parse_weekly_artifact_path(path: Path) -> str | None:
    match = WEEKLY_RE.match(path.name)
    return match.group("week") if match else None


def parse_monthly_artifact_path(path: Path) -> str | None:
    match = MONTHLY_RE.match(path.name)
    return match.group("month") if match else None
