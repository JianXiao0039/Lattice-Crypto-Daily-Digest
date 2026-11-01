"""Noncounting source identity gate. It never grants publication ownership."""
import re
from urllib.parse import urlsplit
from lattice_digest.promotion_history import identity_keys, authoritative_version_conflicted


def identity_gate(row):
    keys = identity_keys(row)
    if authoritative_version_conflicted(row):
        return False, 'VERIFY_FIRST_VERSION_CONFLICT'
    for prefix in ('doi:', 'arxiv:', 'eprint:'):
        if sum(k.startswith(prefix) for k in keys) > 1:
            return False, 'VERIFY_FIRST_IDENTIFIER_CONFLICT'
    url = str(row.get('source_url') or '')
    try:
        parsed = urlsplit(url)
        if parsed.port:
            return False, 'VERIFY_FIRST_SOURCE_IDENTITY_MISMATCH'
    except ValueError:
        return False, 'VERIFY_FIRST_SOURCE_IDENTITY_MISMATCH'
    routes = {
        'arxiv': ('arxiv.org', r'/abs/(\d{4}\.\d{4,5})(?:v\d+)?', 'arxiv:'),
        'iacr_eprint': ('eprint.iacr.org', r'/(\d{4}/[1-9]\d*)', 'eprint:')}
    route = routes.get(row.get('source'))
    if not route:
        return False, 'VERIFY_FIRST_NOT_PRIMARY_ADAPTER'
    match = re.fullmatch(route[1], parsed.path)
    if (parsed.scheme not in ('https', 'http') or parsed.hostname != route[0] or
            parsed.username or parsed.password or parsed.query or parsed.fragment or
            not match or route[2]+match[1] not in keys):
        return False, 'VERIFY_FIRST_SOURCE_IDENTITY_MISMATCH'
    return True, 'SOURCE_IDENTITY_ACCEPTED_NONCOUNTING'
