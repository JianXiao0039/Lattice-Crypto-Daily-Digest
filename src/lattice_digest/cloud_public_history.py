"""Read-only public ownership evidence; absence is never proof of first publication.

Only an immutable GitHub public-digests snapshot is accepted. The complete
public tree is independently validated, including its unchanged privacy schema.
This is an ownership veto, not a substitute for local scientific history.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import os
from pathlib import Path
import re
import tarfile
import urllib.request

from lattice_digest.report_gate import encoded, fail, sha, GateError
from lattice_digest.public_report import inspect_tree

MAX_SNAPSHOT_BYTES = 32 * 1024 * 1024
MAX_SNAPSHOT_FILES = 4096
MAX_TAR_BYTES = 64 * 1024 * 1024


def ownership_history(root: Path, source_ref: str, target: str) -> tuple[list[dict], dict]:
    if not re.fullmatch(r'[a-f0-9]{40}', source_ref):
        fail('HISTORY_EVIDENCE_UNUSABLE', 'public ownership requires an immutable source revision')
    from datetime import date
    day = date.fromisoformat(target)
    # inspect_tree validates the full schema; preflight caps even a caller-
    # supplied tree before it can cause unbounded inventory or byte reads.
    from lattice_digest.public_contract import _reject_redirects
    count = total = 0
    def safe_path(path):
        try:
            _reject_redirects(path)
        except ValueError:
            fail('HISTORY_EVIDENCE_UNUSABLE', 'public ownership tree contains a redirected path')
    safe_path(root.absolute())
    for current, dirs, names in os.walk(root, followlinks=False):
        for name in [*dirs, *names]:
            path = Path(current) / name
            safe_path(path)
            count += 1
            if count > MAX_SNAPSHOT_FILES * 2:
                fail('HISTORY_RESOURCE_LIMIT', 'public ownership inventory exceeds budget')
            if path.is_file():
                size = path.stat().st_size
                total += size
                if size > 1024*1024 or total > MAX_SNAPSHOT_BYTES:
                    fail('HISTORY_RESOURCE_LIMIT', 'public ownership bytes exceed budget')
    manifest, files = inspect_tree(root)
    if len(files) > MAX_SNAPSHOT_FILES or sum(map(len, files.values())) > MAX_SNAPSHOT_BYTES:
        fail('HISTORY_RESOURCE_LIMIT', 'public ownership snapshot exceeds the resource budget')
    rows = []
    for key, entry in sorted(manifest['reports'].items()):
        if not key.startswith('daily:') or date.fromisoformat(key[6:]) >= day:
            continue
        report = json.loads(files[entry['json']])
        # The public catalog is a veto across every authority tier. Cloud cannot
        # reassess a locally authoritative source or transfer its event owner.
        for paper in report['papers']:
            if paper['event_kind'] != 'primary_publication_events':
                continue
            identity = paper['public_canonical_id']
            row = {'source_url': paper['source_url'], 'paper_id': identity,
                   '_promotion_date': key[6:], '_public_primary_owner': key,
                   '_public_event_id': paper['event_id']}
            namespace, value = identity.split(':', 1)
            if namespace in ('doi', 'arxiv', 'eprint'):
                row[{'doi': 'doi', 'arxiv': 'arxiv_id', 'eprint': 'eprint_id'}[namespace]] = value
            rows.append(row)
    evidence = {'schema_version': 'public-ownership-history-v1', 'source_ref': source_ref,
                'manifest_sha256': sha(files['manifest.json']), 'report_count': len(manifest['reports']),
                'owner_count': len(rows), 'history_complete': False,
                'state': 'HISTORY_EVIDENCE_UNUSABLE', 'ownership_rows_sha256': sha(encoded(rows))}
    return rows, evidence


def fetch_snapshot(repository: str, output: Path) -> dict:
    """Fetch one pinned public branch archive without Git operations or secrets in logs."""
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        fail('HISTORY_EVIDENCE_UNUSABLE', 'invalid public repository identity')
    from lattice_digest.public_contract import _reject_redirects
    _reject_redirects(output.absolute())
    if output.exists():
        fail('PUBLISH_CONFLICT', 'public history snapshot is create-only')

    def read(url, maximum):
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'lattice-digest-public-history'}
        # Explicit CI capability only. No dotenv or implicit mailbox token source.
        token = os.environ.get('GH_TOKEN') if os.environ.get('GITHUB_ACTIONS') == 'true' else None
        if token:
            headers['Authorization'] = 'Bearer ' + token
        class Redirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, hdrs, newurl):
                from urllib.parse import urlsplit
                parts = urlsplit(newurl)
                if parts.scheme != 'https' or parts.hostname not in ('api.github.com', 'codeload.github.com'):
                    fail('HISTORY_EVIDENCE_UNUSABLE', 'unreviewed public history transport redirect')
                redirected = super().redirect_request(req, fp, code, msg, hdrs, newurl)
                if redirected is not None:
                    redirected.remove_header('Authorization')
                return redirected
        opener = urllib.request.build_opener(Redirect())
        with opener.open(urllib.request.Request(url, headers=headers), timeout=30) as response:
            raw = response.read(maximum + 1)
        if len(raw) > maximum:
            fail('HISTORY_RESOURCE_LIMIT', 'public ownership transport exceeds budget')
        return raw

    try:
        ref = json.loads(read(f'https://api.github.com/repos/{repository}/git/ref/heads/public-digests', 65536))['object']['sha']
        if not re.fullmatch(r'[a-f0-9]{40}', ref):
            raise ValueError
        raw = read(f'https://api.github.com/repos/{repository}/tarball/{ref}', MAX_SNAPSHOT_BYTES)
        # Bound expansion before tarfile can allocate a PAX header or cache a
        # member. Limiting only member.size after parsing is too late.
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as compressed:
            tar_bytes = compressed.read(MAX_TAR_BYTES + 1)
        if len(tar_bytes) > MAX_TAR_BYTES:
            fail('HISTORY_RESOURCE_LIMIT', 'public archive expansion exceeds budget')
        members = []
        total = 0
        # Bound the decompressed archive too; a small gzip cannot allocate an
        # unbounded tar index or output tree.
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode='r|') as archive:
            for ordinal, member in enumerate(archive):
                if ordinal >= MAX_SNAPSHOT_FILES * 2:
                    fail('HISTORY_RESOURCE_LIMIT', 'public archive header budget exceeded')
                if member.isdir():
                    continue
                relative = '/'.join(member.name.split('/')[1:])
                if (not member.isfile() or not (relative in ('manifest.json', 'index.md') or
                        re.fullmatch(r'(daily|weekly|monthly)/\d{4}/\d{4}-(?:\d{2}-\d{2}|W\d{2}|\d{2})\.(json|md)', relative))):
                    fail('HISTORY_EVIDENCE_UNUSABLE', 'public archive contains an unsafe member')
                total += member.size
                if member.size <= 0 or member.size > 1024 * 1024 or total > MAX_SNAPSHOT_BYTES or len(members) >= MAX_SNAPSHOT_FILES:
                    fail('HISTORY_RESOURCE_LIMIT', 'public archive exceeds bounded tree limits')
                if any(name == relative for name, _ in members):
                    fail('HISTORY_EVIDENCE_UNUSABLE', 'public archive contains duplicate members')
                content = archive.extractfile(member).read(member.size + 1)
                if len(content) != member.size:
                    fail('HISTORY_EVIDENCE_UNUSABLE', 'public archive member is truncated')
                members.append((relative, content))
        output.mkdir(parents=True)
        for relative, content in members:
            path = output / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        manifest, files = inspect_tree(output)
        return {'schema_version': 'public-snapshot-receipt-v1', 'source_ref': ref,
                'manifest_sha256': sha(files['manifest.json']), 'report_count': len(manifest['reports'])}
    except GateError:
        raise
    except (KeyError, ValueError, OSError, tarfile.TarError):
        # A partially materialized directory is never evidence: callers require
        # inspect_tree and a completed receipt. Keep it for failure diagnosis.
        fail('HISTORY_EVIDENCE_UNUSABLE', 'public ownership snapshot unavailable or invalid')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args(argv)
    from lattice_digest.report_gate import GateError
    try:
        receipt = fetch_snapshot(args.repository, args.output)
        args.receipt.write_bytes(encoded(receipt) + b'\n')
        print(json.dumps({'gate': 'PUBLIC_HISTORY_GATE', 'status': 'PASS', **receipt}))
        return 0
    except (GateError, OSError, ValueError) as exc:
        print(json.dumps({'gate': 'PUBLIC_HISTORY_GATE', 'status': 'FAIL',
                          'code': exc.code if isinstance(exc, GateError) else 'HISTORY_EVIDENCE_UNUSABLE'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
