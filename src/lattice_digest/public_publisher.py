"""Isolated exact-tree Git publisher. No source checkout, force, rebase or secrets.

Only a separately approved invocation may call publish(). Tests use local bare
remotes. A Git commit and fast-forward ref update form the atomic pair commit.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from lattice_digest.public_report import inspect_tree, index_bytes, validate_catalog, QUALITY
from lattice_digest.report_gate import encoded, fail, GateError, sha


def git(root: Path, *args: str, check: bool = True):
    env = {k:v for k,v in os.environ.items() if not k.startswith(('GIT_', 'SMTP_', 'DIGEST_EMAIL_', 'GMAIL_', 'GOOGLE_'))}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0')
    result = subprocess.run(['git', '-c', 'core.hooksPath=' + os.devnull, *args], cwd=root,
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if check and result.returncode:
        # Git output may contain credential URLs or remote-controlled text. Never echo it.
        fail('REMOTE_PUBLICATION_FAILED', 'Git command failed; diagnostic content redacted')
    return result


def remote_kind(remote: str) -> str:
    if re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?', remote):
        return 'github'
    path = Path(remote)
    if path.is_absolute() and path.is_dir() and (path/'HEAD').is_file() and (path/'objects').is_dir():
        return 'local-test-bare'
    fail('REMOTE_TARGET_INVALID', 'only an exact HTTPS GitHub repository or local bare fixture is allowed')


def remote_files(root: Path, remote: str) -> tuple[str | None, dict[str, bytes], dict]:
    refs = git(root, 'ls-remote', '--heads', remote, 'refs/heads/public-digests')
    if not refs.stdout.strip():
        return None, {}, {'schema_version':'public-manifest-v1', 'reports':{}}
    lines = refs.stdout.splitlines()
    if len(lines) != 1 or not re.fullmatch(rb'[a-f0-9]{40}\trefs/heads/public-digests', lines[0]):
        fail('PUBLISH_CONFLICT', 'remote branch identity unresolved')
    head = lines[0].split()[0].decode()
    git(root, 'fetch', '--no-tags', remote, 'refs/heads/public-digests')
    actual = git(root, 'rev-parse', 'FETCH_HEAD').stdout.decode().strip()
    # A concurrent advance before fetch is safe: inspect the fetched version.
    head = actual
    listing = git(root, 'ls-tree', '-r', '-z', '--full-tree', head).stdout.split(b'\0')
    if len(listing) > 4097:
        fail('PAYLOAD_SIZE_INVALID', 'public branch inventory exceeds bounded readback limit')
    files = {}
    total = 0
    with tempfile.TemporaryDirectory(prefix='public-readback-') as temporary:
        materialized = Path(temporary)
        for entry in listing:
            if not entry:
                continue
            info, name = entry.split(b'\t',1)
            mode, kind, oid = info.split()
            name = name.decode('utf-8')
            if mode != b'100644' or kind != b'blob' or not (name in ('index.md','manifest.json') or re.fullmatch(r'(daily|weekly|monthly)/\d{4}/\d{4}-(?:\d{2}-\d{2}|W\d{2}|\d{2})\.(json|md)',name)):
                fail('PUBLIC_PRIVACY_GATE_FAILED', 'remote public branch contains an unexpected path or mode')
            size = int(git(root, 'cat-file', '-s', oid.decode()).stdout)
            if not 0 < size <= 1024*1024:
                fail('PAYLOAD_SIZE_INVALID', 'remote blob empty or oversized')
            total += size
            if total > 32*1024*1024:
                fail('PAYLOAD_SIZE_INVALID', 'public branch exceeds bounded readback size')
            content = git(root, 'cat-file', 'blob', oid.decode()).stdout
            target = materialized/name
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(content)
            files[name] = content
        manifest, checked = inspect_tree(materialized)
        if checked != files:
            fail('PUBLIC_PRIVACY_GATE_FAILED', 'remote inventory mismatch')
    return head, files, manifest


def publish(candidate: Path, remote: str, *, approved: bool = False, attempts: int = 3,
            use_gh_credentials: bool = False, use_windows_credentials: bool = False,
            accept_superseded: bool = False) -> dict:
    if not approved:
        fail('PUBLICATION_NOT_APPROVED', 'explicit reviewed-publication approval is required')
    kind = remote_kind(remote)
    if use_gh_credentials and (kind != 'github' or shutil.which('gh') is None):
        fail('REMOTE_AUTH_UNAVAILABLE', 'explicit GitHub CLI credential helper is unavailable for this target')
    if use_windows_credentials and (kind != 'github' or os.name != 'nt' or use_gh_credentials):
        fail('REMOTE_AUTH_UNAVAILABLE', 'Windows credential manager is only allowed on Windows GitHub targets')
    if not 1 <= attempts <= 3:
        fail('PUBLISH_CONFLICT', 'retry budget must be one to three')
    incoming, source_files = inspect_tree(candidate)
    if len(incoming['reports']) != 1:
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'one reviewed report per transaction; no historical bulk upload')
    key, entry = next(iter(incoming['reports'].items()))
    with tempfile.TemporaryDirectory(prefix='public-publisher-') as temporary:
        work = Path(temporary)
        git(work, 'init', '--quiet')
        git(work, 'config', 'user.name', 'Public Literature Publisher')
        git(work, 'config', 'user.email', 'publisher@example.invalid')
        if use_gh_credentials:
            # Explicit opt-in after publication approval; no token in argv, URLs or output.
            # The helper uses the operator's gh authentication and is never copied to a branch.
            git(work, 'config', 'credential.helper', '!gh auth git-credential')
        if use_windows_credentials:
            git(work, 'config', 'credential.helper', 'manager')
            git(work, 'config', 'credential.interactive', 'never')
        last_commit = None
        for attempt in range(1, attempts+1):
            base, files, manifest = remote_files(work, remote)
            old = manifest['reports'].get(key)
            if old:
                if QUALITY[old['quality']] > QUALITY[entry['quality']]:
                    if accept_superseded:
                        return {'status':'SUPERSEDED_BY_HIGHER_AUTHORITY', 'remote_readback':'PASS',
                                'commit':base, 'remote_kind':kind, 'published_quality':old['quality'],
                                'report':key, 'public_artifacts':{name:sha(raw) for name,raw in files.items()}}
                    fail('PUBLISH_CONFLICT', 'lower-authority report cannot replace published authority')
                if old == entry:
                    return {'status':'NO_OP', 'remote_readback':'PASS', 'commit':base, 'attempts':attempt, 'remote_kind':kind,
                            'report':key, 'public_artifacts':{name:sha(raw) for name,raw in files.items()}}
                if QUALITY[old['quality']] == QUALITY[entry['quality']]:
                    # The reviewed one-way v1 -> v2 readability migration must
                    # preserve the exact canonical pair and every counted event.
                    from lattice_digest.public_report import validate_public, PublicPaper
                    from lattice_digest.report_gate import strict_json
                    before = validate_public(strict_json(files[old['json']]))
                    after = validate_public(strict_json(source_files[entry['json']]))
                    identity = lambda p: sorted((r['event_id'],r['public_canonical_id'],r['verified_date'],
                        r['event_kind'],r['event_evidence']) for r in p['papers'])
                    upgrade = (before['public_schema_version']=='public-literature-v1' and
                        after['public_schema_version']=='public-literature-v2' and
                        before['canonical_pair_sha256']==after['canonical_pair_sha256'] and
                        before['input_evidence']==after['input_evidence'] and identity(before)==identity(after) and
                        before['papers']==[{k:v for k,v in p.items() if k in PublicPaper.model_fields} for p in after['papers']] and
                        before['source_coverage_state']==after['source_coverage_state'])
                    if not upgrade:
                        fail('PUBLISH_CONFLICT', 'same-authority changed report requires a separate reviewed version policy')
            merged = {'schema_version':'public-manifest-v1', 'reports':{**manifest['reports'], key:entry}}
            files.update({entry['json']:source_files[entry['json']], entry['markdown']:source_files[entry['markdown']],
                          'manifest.json':encoded(merged)+b'\n', 'index.md':index_bytes(merged)})
            validate_catalog(merged,files)
            # Use a fresh index containing exactly the validated public files.
            git(work, 'read-tree', '--empty')
            for name, content in sorted(files.items()):
                target = work/name
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(content)
                git(work, 'add', '--', name)
            staged = set(git(work, 'ls-files', '-z').stdout.decode().strip('\0').split('\0'))
            if staged != set(files):
                fail('PUBLIC_PRIVACY_GATE_FAILED', 'Git index exceeds exact public file allowlist')
            tree = git(work, 'write-tree').stdout.decode().strip()
            reason = ' [reviewed v1-to-v2 source-bound readability correction]' if old and QUALITY[old['quality']]==QUALITY[entry['quality']] else ''
            args = ['commit-tree', tree, '-m', 'Publish reviewed public literature report ' + key + reason]
            if base:
                args.extend(['-p',base])
            last_commit = git(work, *args).stdout.decode().strip()
            # Atomic ref update; ordinary non-fast-forward rejection is reconciled below.
            result = git(work, 'push', '--porcelain', remote, last_commit+':refs/heads/public-digests', check=False)
            if result.returncode:
                observed, _, _ = remote_files(work, remote)
                if observed == base:
                    fail('REMOTE_PERMISSION_OR_TRANSPORT_DENIED', 'push failed without a concurrent remote advance')
                continue
            # Independent fetch and byte verification, never just trust push output.
            try:
                observed, readback, _ = remote_files(work, remote)
            except (GateError, OSError, subprocess.SubprocessError):
                fail('REMOTE_READBACK_FAILED', 'push accepted; readback unavailable; remote may contain the report')
            if observed != last_commit or readback != files:
                fail('REMOTE_READBACK_FAILED', 'remote advanced or bytes differ after successful push; inspect partial success')
            return {'status':'PUBLISHED_TEST_REMOTE' if kind=='local-test-bare' else 'PUBLISHED',
                    'remote_readback':'PASS', 'attempts':attempt, 'commit':last_commit, 'remote_kind':kind,
                    'report':key, 'public_artifacts':{name:sha(raw) for name,raw in readback.items()}}
    fail('PUBLISH_CONFLICT', 'bounded fast-forward reconciliation exhausted; inspect remote before retry')


def main(argv=None):
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--remote',required=True)
    parser.add_argument('--approve-reviewed-publication',action='store_true')
    parser.add_argument('--use-gh-credentials',action='store_true',help='Explicitly use an installed gh credential helper after approval')
    parser.add_argument('--use-windows-credentials',action='store_true')
    parser.add_argument('--accept-superseded',action='store_true',help='Return verified higher-authority existing output without changing it')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(publish(args.candidate,args.remote,approved=args.approve_reviewed_publication,
                                 use_gh_credentials=args.use_gh_credentials,
                                 use_windows_credentials=args.use_windows_credentials,
                                 accept_superseded=args.accept_superseded)))
        return 0
    except (GateError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({'gate':'REMOTE_PUBLICATION_GATE','status':'FAIL',
            'delivery_state':'REMOTE_PUBLICATION_BLOCKED','publish_pending':False,
            'code':exc.code if isinstance(exc,GateError) else 'REMOTE_PUBLICATION_FAILED'}))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
