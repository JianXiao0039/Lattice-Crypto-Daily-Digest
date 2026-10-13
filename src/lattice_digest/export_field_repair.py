"""Owner-only field repairs; all bytes outside generated relevance tokens survive."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from uuid import uuid4

from lattice_digest.evidence_contract import source_scope_score, score_to_label
from lattice_digest.public_contract import public_preflight, _reject_redirects
from lattice_digest.report_repair import checked_path, digest


def candidate_bytes(root: Path, item: dict) -> tuple[Path, bytes, bytes, list[dict]]:
    path = checked_path(Path(item['path']), root / 'exports')
    # Check lexical redirects first, then decide ownership on the actual target.
    path = path.resolve()
    relative = path.relative_to((root / 'exports').resolve()).as_posix()
    if path.suffix != '.md' or not relative.startswith(('reading-queue/', 'research-artifacts/', 'research-progress/')):
        raise ValueError('export ownership is outside reviewed generated paths')
    original = path.read_bytes()
    if digest(original) != item['original_sha256']:
        raise ValueError('export original hash drift')
    lines = original.decode('utf-8').splitlines(keepends=True)
    changed = list(lines); seen = set(); evidence = []
    for patch in item['patches']:
        index = patch['line'] - 1
        if index in seen or not 0 <= index < len(lines):
            raise ValueError('duplicate/invalid generated line')
        seen.add(index)
        source = checked_path(Path(patch['source_path']), root / 'data')
        source = source.resolve()
        if not re.fullmatch(r'\d{4}/daily/\d{4}-\d{2}-\d{2}\.json', source.relative_to((root / 'data').resolve()).as_posix()):
            raise ValueError('source is not canonical Daily')
        raw = source.read_bytes()
        if digest(raw) != patch['source_sha256']:
            raise ValueError('upstream source hash drift')
        payload = json.loads(raw)
        rows = payload if isinstance(payload, list) else payload['records']
        row = rows[patch['source_row']]
        url = patch['url']
        urls = [row.get('source_url'), *row.get('source_urls', [])]
        if url not in urls or url not in lines[index] or not lines[index].startswith('- '):
            raise ValueError('generated line/source identity mismatch')
        matches = list(re.finditer(r'｜([ABCD]) / (\d{1,3})｜', lines[index]))
        if len(matches) != 1:
            raise ValueError('generated relevance token is missing or ambiguous')
        match = matches[0]
        if (match.group(1), int(match.group(2))) != (patch['old_label'], patch['old_score']):
            raise ValueError('original relevance token drift')
        scope, score = source_scope_score(row)
        label = score_to_label(score)
        changed[index] = lines[index][:match.start()] + f'｜{label} / {score}｜' + lines[index][match.end():]
        evidence.append({'line': index + 1, 'url': url, 'source_path': str(source),
            'source_sha256': patch['source_sha256'], 'source_row': patch['source_row'],
            'before': {'label': patch['old_label'], 'score': patch['old_score']},
            'after': {'label': label, 'score': score}, 'source_scope': str(scope)})
    candidate = ''.join(changed).encode('utf-8')
    if not evidence or original == candidate:
        raise ValueError('empty/no-op generated field repair')
    return path, original, candidate, evidence


def repair_export(root: Path, item: dict, evidence_root: Path, *, execute: bool = False) -> dict:
    path, original, candidate, changes = candidate_bytes(root, item)
    result = {'path': str(path), 'before_sha256': digest(original), 'after_sha256': digest(candidate),
        'changes': changes, 'qa': {'source_scope': 'PASS', 'non_generated_bytes_preserved': 'PASS'},
        'scientific_prose': 'NOT_REWRITTEN_REQUIRE_SEPARATE_EVIDENCE_AUDIT'}
    if not execute:
        return {**result, 'status': 'QA_PASSED_NOT_PROMOTED'}
    lock = path.with_name('.' + path.name + '.export-repair.lock')
    _reject_redirects(lock)
    with lock.open('x', encoding='utf-8') as lock_stream:
        try:
            directory = checked_path(evidence_root / uuid4().hex, root / '.ops/evidence')
            directory.mkdir(parents=True, exist_ok=False)
            with gzip.open(directory / 'original.md.gz', 'wb') as stream: stream.write(original)
            with gzip.open(directory / 'original.md.gz', 'rb') as stream:
                if stream.read() != original: raise ValueError('snapshot byte verification failed')
            journal = directory / 'transaction.json'
            journal.write_text(json.dumps({**result, 'status': 'PREPARED'}, ensure_ascii=False, indent=2), encoding='utf-8')
            fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.')
            replaced = False
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(candidate); stream.flush(); os.fsync(stream.fileno())
                # Recheck upstream source and original immediately before publication.
                candidate_bytes(root, item)
                os.replace(temporary, path)
                replaced = True
                if path.read_bytes() != candidate: raise OSError('export verification failed')
            except BaseException:
                # Never roll back an edit made by another writer. Prepublication
                # drift belongs to that writer; only our exact replacement is ours.
                if replaced and path.read_bytes() == candidate:
                    backup_fd, backup_name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '.rollback-')
                    try:
                        with os.fdopen(backup_fd, 'wb') as stream:
                            stream.write(original); stream.flush(); os.fsync(stream.fileno())
                        if path.read_bytes() == candidate: os.replace(backup_name, path)
                    finally:
                        Path(backup_name).unlink(missing_ok=True)
                journal.write_text(json.dumps({**result, 'status': 'FAILED_NO_USER_BYTES_ROLLED_BACK'}, ensure_ascii=False, indent=2), encoding='utf-8')
                raise
            finally:
                Path(temporary).unlink(missing_ok=True)
            result.update(status='PROMOTED', evidence_directory=str(directory))
            journal.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            return result
        finally:
            lock_stream.close()
            lock.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args(argv)
    paths, proof = public_preflight('EXPORT_FIELD_REPAIR')
    plan = checked_path(args.plan, paths.canonical_root / '.ops/evidence')
    raw = plan.read_bytes()
    if digest(raw) != args.plan_sha256: raise ValueError('export plan hash drift')
    items = json.loads(raw)
    if not isinstance(items, list) or not items: raise ValueError('empty/invalid export plan')
    results = []
    for item in items:
        try:
            results.append(repair_export(paths.canonical_root, item, plan.parent / 'export-transactions', execute=args.execute))
        except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            results.append({'path': item.get('path'), 'status': 'BLOCKED', 'error': type(exc).__name__ + ': ' + str(exc)})
    receipt = plan.with_name(plan.stem + ('-execution' if args.execute else '-preflight') + '.json')
    receipt.write_text(json.dumps({'runtime': proof['runtime_provenance'], 'results': results}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'promoted': sum(r['status'] == 'PROMOTED' for r in results),
        'blocked': sum(r['status'] == 'BLOCKED' for r in results)}))
    return int(any(r['status'] == 'BLOCKED' for r in results))


if __name__ == '__main__': raise SystemExit(main())
