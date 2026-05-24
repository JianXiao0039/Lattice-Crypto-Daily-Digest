from __future__ import annotations

import os
import re
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path


REQUIRED_ENV = (
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "MAIL_FROM",
    "MAIL_TO",
)
DIGEST_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_latest_digest(digests_dir: Path) -> Path | None:
    if not digests_dir.exists():
        return None
    candidates = sorted(path for path in digests_dir.glob("*.md") if DIGEST_RE.match(path.name))
    return candidates[-1] if candidates else None


def missing_env(env: dict[str, str]) -> list[str]:
    return [name for name in REQUIRED_ENV if not env.get(name)]


def _mail_recipients(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def send_digest_email(digest_path: Path, env: dict[str, str]) -> None:
    digest_date = digest_path.stem
    body = digest_path.read_text(encoding="utf-8")

    try:
        smtp_port = int(env["SMTP_PORT"])
    except ValueError as exc:
        raise ValueError("SMTP_PORT must be an integer") from exc

    recipients = _mail_recipients(env["MAIL_TO"])
    if not recipients:
        raise ValueError("MAIL_TO must contain at least one recipient")

    message = EmailMessage()
    message["Subject"] = f"格密码论文日报 - {digest_date}"
    message["From"] = env["MAIL_FROM"]
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    with smtplib.SMTP(env["SMTP_HOST"], smtp_port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(env["SMTP_USER"], env["SMTP_PASSWORD"])
        smtp.send_message(message)


def main() -> int:
    env = dict(os.environ)
    missing = missing_env(env)
    if missing:
        print("missing SMTP configuration: " + ", ".join(missing), file=sys.stderr)
        return 1

    digest_path = find_latest_digest(project_root() / "digests")
    if digest_path is None:
        print("no digest found in digests/YYYY-MM-DD.md", file=sys.stderr)
        return 1

    try:
        send_digest_email(digest_path, env)
    except Exception as exc:  # noqa: BLE001 - surface SMTP failures without printing secrets.
        print(f"failed to send email: {exc}", file=sys.stderr)
        return 1

    print(f"sent email to {env['MAIL_TO']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
