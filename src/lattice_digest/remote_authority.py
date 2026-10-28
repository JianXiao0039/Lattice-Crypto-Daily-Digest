"""Bounded live Git authority; transport recovery never grants offline authority."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import urlsplit

APPROVED_ORIGIN = 'https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git'
TOTAL_SECONDS = 12.0
ATTEMPT_SECONDS = 3.0
MAX_ATTEMPTS = 3
RETRYABLE = {'PROXY_ENDPOINT_UNREACHABLE', 'DNS_FAILURE', 'CONNECTION_TIMEOUT',
             'GITHUB_HTTPS_UNREACHABLE'}


def failure_category(stderr: bytes) -> str:
    """Classify in memory; remote-controlled diagnostic text is never returned."""
    text = stderr.decode('utf-8', errors='replace').lower()
    if any(s in text for s in ('407', 'proxy authentication')):
        return 'PROXY_AUTH_FAILURE'
    if any(s in text for s in ('authentication failed', 'could not read username', '403', '401')):
        return 'REMOTE_AUTH_FAILURE'
    if any(s in text for s in ('certificate', 'ssl', 'tls')):
        return 'TLS_FAILURE'
    if 'resolve' in text:
        return 'DNS_FAILURE'
    if 'proxy' in text and any(s in text for s in ('connect', 'refused', 'unreachable')):
        return 'PROXY_ENDPOINT_UNREACHABLE'
    if 'timed out' in text or 'timeout' in text:
        return 'CONNECTION_TIMEOUT'
    if any(s in text for s in ('connect', 'unreachable', 'connection reset')):
        return 'GITHUB_HTTPS_UNREACHABLE'
    return 'UNKNOWN_NETWORK_FAILURE'


def safe_loopback_proxy(value: str) -> str | None:
    try:
        p = urlsplit(value)
        if (p.scheme not in {'http', 'https'} or p.hostname not in {'127.0.0.1', 'localhost', '::1'}
                or not p.port or p.username is not None or p.password is not None
                or p.path not in {'', '/'} or p.query or p.fragment
                or any(c.isspace() for c in value)):
            return None
        return value
    except ValueError:
        return None


def windows_proxy() -> str | None:
    """Reuse only the already enabled Windows proxy, never environment guesses/PAC."""
    if os.name != 'nt':
        return None
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings') as key:
            if winreg.QueryValueEx(key, 'ProxyEnable')[0] != 1:
                return None
            raw = winreg.QueryValueEx(key, 'ProxyServer')[0]
            for name in ('AutoConfigURL',):
                try:
                    if winreg.QueryValueEx(key, name)[0]:
                        return None  # PAC policy needs a separately reviewed route resolver.
                except FileNotFoundError:
                    pass
        if not isinstance(raw, str):
            return None
        if '=' in raw:
            entries = dict(item.split('=', 1) for item in raw.split(';') if item)
            raw = entries.get('https', '')
        return safe_loopback_proxy(raw if '://' in raw else 'http://' + raw)
    except (OSError, ValueError):
        return None


def live_remote(root: Path, origin_url: str) -> dict:
    """At most three real reads within one wall-clock budget; no cached authority.

    Alternate transport is limited to this project's exact HTTPS origin after a
    proxy endpoint failure. It preserves TLS verification and existing credentials.
    DNS, TLS, authentication or ambiguous failures cannot switch network policy.
    """
    started = time.monotonic()
    deadline = started + TOTAL_SECONDS
    result = {'status': 'UNVERIFIED', 'sha': None, 'attempts': [],
              'error_code': 'UNKNOWN_NETWORK_FAILURE'}
    proxy = None
    for attempt in range(MAX_ATTEMPTS):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        options = ['-c', 'http.sslVerify=true', '-c', 'credential.interactive=false']
        if origin_url == APPROVED_ORIGIN:
            options += ['-c', f'http.{APPROVED_ORIGIN}.sslVerify=true']
        if proxy is not None:
            # URL-specific proxy defeats stale more-specific Git configuration.
            options += ['-c', f'http.{APPROVED_ORIGIN}.proxy={proxy}']
        env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
        env.pop('GIT_SSL_NO_VERIFY', None)
        route = 'EXISTING_WINDOWS_LOOPBACK_PROXY' if proxy else 'EXISTING_GIT_ROUTE'
        try:
            z = subprocess.run(['git', *options, 'ls-remote', '--heads', 'origin', 'refs/heads/main'],
                cwd=root, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                timeout=min(ATTEMPT_SECONDS, remaining))
            code = failure_category(z.stderr) if z.returncode else None
            if not z.returncode:
                match = re.fullmatch(rb'([a-f0-9]{40})\trefs/heads/main\r?\n?', z.stdout)
                if match:
                    result.update(status='VERIFIED', sha=match[1].decode(), error_code=None)
                else:
                    code = 'REMOTE_MAIN_UNRESOLVED'
            result['attempts'].append({'route': route, 'exit': z.returncode, 'error_code': code})
        except subprocess.TimeoutExpired:
            code = 'CONNECTION_TIMEOUT'
            result['attempts'].append({'route': route, 'exit': 'TIMEOUT', 'error_code': code})
        except OSError:
            code = 'GIT_EXECUTION_FAILURE'
            result['attempts'].append({'route': route, 'exit': 'OS_ERROR', 'error_code': code})
        if result['status'] == 'VERIFIED':
            break
        result['error_code'] = code
        if code not in RETRYABLE:
            break
        if code == 'PROXY_ENDPOINT_UNREACHABLE' and origin_url == APPROVED_ORIGIN:
            proxy = windows_proxy()
        if attempt + 1 < MAX_ATTEMPTS:
            time.sleep(min(0.2 * 2 ** attempt, max(0, deadline - time.monotonic())))
    result['elapsed_seconds'] = round(time.monotonic() - started, 3)
    return result
