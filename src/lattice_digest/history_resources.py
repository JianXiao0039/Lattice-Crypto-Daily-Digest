"""Resource bounded, source-bound legacy history reader (no trusted sidecars).

The 64 MiB ceiling is twice the former 32 MiB ceiling and exceeds the measured
33,998,116-byte incident input without permitting arbitrary archive growth.
All JSON is syntax checked, but only a compact identity/event projection survives
decoding. Limits apply before allocation and across records, not after json.load.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
import stat
from typing import Any

MAX_HISTORY_BYTES = 64 * 1024 * 1024
MAX_MARKDOWN_BYTES = 16 * 1024 * 1024
MAX_HISTORY_RECORDS = 10000
MAX_HISTORY_NODES = 2_000_000
MAX_HISTORY_DEPTH = 48
MAX_TOKEN_CHARS = 256 * 1024
MAX_OBJECT_KEYS = 2048
MAX_COMPACT_BYTES = 16 * 1024 * 1024
# Fourteen individually bounded projections. This is conservative accounting,
# not the archive byte size: at most 14 * 10,000 compact rows survive. JSON input,
# skipped branches and Markdown are released between days.
MAX_TOTAL_COMPACT_BYTES = 14 * MAX_COMPACT_BYTES
CHUNK_CHARS = 64 * 1024
READER_VERSION = 'bounded-history-v41-1'

ROW_FIELDS = frozenset(('title', 'authors', 'venue', 'abstract', 'doi', 'arxiv_id',
    'eprint_id', 'source_url', 'source_urls', 'paper_id', 'source',
    'publication_date', 'publication_timestamp', 'publication_date_kind',
    'preprint_first_posted_at', 'source_version_timestamp', 'announcement_timestamp',
    'announcement_date', 'announcement_date_kind', 'update_date', 'update_timestamp',
    'update_date_kind', 'first_seen_date', 'first_seen_at', 'source_observed_at',
    'source_metadata_correction_date', 'cross_day_event', 'primary_today_new_eligible',
    'publication_event_id', 'publication_event_type', 'publication_event_date',
    'critical_verification_events', 'prior_promotion_dates'))
META_FIELDS = frozenset(('target_date', 'generation_id', 'markdown_sha256',
    'quality_status', 'publication_state', 'structural_qa', 'semantic_qa',
    'publication_policy_version', 'authority_policy_version', 'generated_at',
    'report_generated_at', 'run_date', 'coverage_start', 'coverage_end'))


class HistoryEvidenceError(ValueError):
    """Fixed public diagnostic. Safe parsed rows can only constrain promotions."""
    def __init__(self, code: str, rows=None, receipt=None):
        self.code = code
        self.rows = rows or []
        self.receipt = receipt or {}
        super().__init__(code)


def _reject_redirects(path: Path) -> None:
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0)
                & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)):
            raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE')


def _safe_open(path: Path, maximum: int):
    _reject_redirects(path)
    try:
        before = path.stat()
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum:
            raise HistoryEvidenceError('HISTORY_RESOURCE_LIMIT' if before.st_size > maximum else 'HISTORY_EVIDENCE_UNUSABLE')
        stream = path.open('rb')
        import os
        opened = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns):
            stream.close()
            raise HistoryEvidenceError('HISTORY_INDEX_SOURCE_MISMATCH')
        try:
            _reject_redirects(path)
        except HistoryEvidenceError:
            stream.close()
            raise
        return stream, before
    except OSError:
        raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE') from None


class _JSONProjection:
    """Incremental strict JSON parser with a bounded retained projection."""
    def __init__(self, stream):
        import codecs
        self.stream = stream
        self.decoder = codecs.getincrementaldecoder('utf-8')('strict')
        self.buffer = ''; self.position = 0; self.eof = False
        self.nodes = 0; self.retained = 0; self.read_bytes = 0
        self.digest = hashlib.sha256()

    def fill(self):
        if self.eof:
            return False
        self.buffer = self.buffer[self.position:]; self.position = 0
        chunk = self.stream.read(CHUNK_CHARS)
        self.read_bytes += len(chunk)
        if self.read_bytes > MAX_HISTORY_BYTES:
            raise HistoryEvidenceError('HISTORY_RESOURCE_LIMIT')
        self.digest.update(chunk)
        self.eof = not chunk
        self.buffer += self.decoder.decode(chunk, final=self.eof)
        return bool(chunk)

    def peek(self):
        while True:
            match = re.compile(r'[ \t\r\n]*').match(self.buffer, self.position)
            self.position = match.end()
            if self.position < len(self.buffer):
                return self.buffer[self.position]
            if not self.fill():
                return ''

    def take(self, expected):
        if self.peek() != expected:
            raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE')
        self.position += 1

    def string(self):
        self.take('"')
        start = self.position
        while True:
            try:
                result, end = json.decoder.scanstring(self.buffer, self.position, True)
                if end - start > MAX_TOKEN_CHARS:
                    raise HistoryEvidenceError('HISTORY_RESOURCE_LIMIT')
                self.position = end
                return result
            except json.JSONDecodeError:
                if len(self.buffer) - self.position > MAX_TOKEN_CHARS:
                    raise HistoryEvidenceError('HISTORY_RESOURCE_LIMIT')
                # Preserve the opening quote; scanstring starts just after it.
                self.position -= 1
                if not self.fill():
                    raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE') from None
                self.position = 1; start = 1

    def account(self, value):
        # Conservative CPython-independent accounting: scalar/container overhead
        # plus up to four bytes per Unicode character, including retained keys.
        self.retained += 128 + (4 * len(value) if isinstance(value, str) else 0)
        if self.retained > MAX_COMPACT_BYTES:
            raise HistoryEvidenceError('HISTORY_RESOURCE_LIMIT')

    @staticmethod
    def keep_child(path, key, keep):
        if path == ():
            return key in {'metadata', 'records'}
        if path == ('metadata',):
            return key in META_FIELDS
        if path == ('records', '*'):
            return key in ROW_FIELDS
        if path in {('metadata', 'semantic_qa'), ('metadata', 'structural_qa')}:
            return key == 'status'
        return keep

    def value(self, path=(), keep=True, depth=0):
        self.nodes += 1
        if depth > MAX_HISTORY_DEPTH or self.nodes > MAX_HISTORY_NODES:
            raise HistoryEvidenceError('HISTORY_RESOURCE_LIMIT')
        char = self.peek()
        if char == '{':
            self.position += 1; seen = set(); result = {} if keep else None
            if keep: self.account(result)
            if self.peek() == '}': self.position += 1; return result
            while True:
                key = self.string()
                if len(key) > 512 or len(seen) >= MAX_OBJECT_KEYS:
                    raise HistoryEvidenceError('HISTORY_RESOURCE_LIMIT')
                if key in seen:
                    raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE')
                seen.add(key); self.take(':')
                child_keep = self.keep_child(path, key, keep)
                child = self.value((*path, key), child_keep, depth + 1)
                if child_keep:
                    self.account(key); result[key] = child
                char = self.peek(); self.position += 1
                if char == '}': break
                if char != ',': raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE')
            return result
        if char == '[':
            self.position += 1; result = [] if keep else None; count = 0
            if keep: self.account(result)
            if self.peek() == ']': self.position += 1; return result
            while True:
                count += 1
                if path == ('records',) and count > MAX_HISTORY_RECORDS:
                    raise HistoryEvidenceError('HISTORY_RESOURCE_LIMIT')
                child = self.value((*path, '*'), keep, depth + 1)
                if keep: result.append(child)
                char = self.peek(); self.position += 1
                if char == ']': break
                if char != ',': raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE')
            return result
        if char == '"':
            value = self.string()
        else:
            # Non-string scalars are short; excessive numeric precision is not
            # useful identity evidence and must not create big integer work.
            token = ''
            while True:
                if self.position >= len(self.buffer) and not self.fill(): break
                if self.buffer[self.position] in ',]} \t\r\n': break
                token += self.buffer[self.position]; self.position += 1
                if len(token) > 128: raise HistoryEvidenceError('HISTORY_RESOURCE_LIMIT')
            if token in ('true', 'false', 'null'):
                value = {'true': True, 'false': False, 'null': None}[token]
            elif re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?', token):
                value = json.loads(token)
                if isinstance(value, float) and not math.isfinite(value):
                    raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE')
            else:
                raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE')
        if keep: self.account(value)
        return value if keep else None


def load_verified_history_pair(data_dir: Path, day: date) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read one immutable canonical pair; never read or trust a sidecar.

    Source-bound receipt is recomputed each call, so changing source bytes cannot
    reuse a previously accepted projection. It is not a retrospective assertion
    that a row had been observed earlier than this source report's date.
    """
    from lattice_digest.artifact_paths import daily_data_path, daily_digest_path
    day = date.fromisoformat(str(day))
    data_dir = Path(data_dir).absolute()
    jp = daily_data_path(day, data_dir)
    mp = daily_digest_path(day, data_dir.parent / 'digests')
    try:
        for lock in (data_dir.parent / 'audits' / 'writer-locks' / f'DAILY-{day}.lock',
                     jp.with_name(f'.{day}.publication.lock')):
            _reject_redirects(lock)
            if lock.exists() or lock.is_symlink():
                raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE')
        stream, before = _safe_open(jp, MAX_HISTORY_BYTES)
        with stream:
            parser = _JSONProjection(stream)
            payload = parser.value()
            if parser.peek(): raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE')
        _reject_redirects(jp)
        after = jp.stat()
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            raise HistoryEvidenceError('HISTORY_INDEX_SOURCE_MISMATCH')
        if not isinstance(payload, dict) or not isinstance(payload.get('records'), list) or any(not isinstance(r, dict) for r in payload['records']):
            raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE')
        rows = payload['records']; meta = payload.get('metadata', {})
        receipt = {'date': str(day), 'sha256': parser.digest.hexdigest(),
            'reader_version': READER_VERSION, 'source_bytes': parser.read_bytes,
            'decoded_nodes': parser.nodes, 'compact_accounted_bytes': parser.retained,
            'generation_id': meta.get('generation_id'), 'record_count': len(rows)}
        for row in rows:
            row.update(_promotion_date=str(day), _history_source_sha256=receipt['sha256'],
                       _history_generation_id=receipt['generation_id'])
        generation = meta.get('generation_id')
        if (not isinstance(generation, str) or not re.fullmatch('[a-f0-9]{32}', generation)
                or meta.get('target_date') != str(day)
                or meta.get('quality_status') not in {'authoritative', 'authoritative_backfill'}
                or meta.get('publication_state') != 'QA_PASSED'
                or any(not isinstance(meta.get(k), dict) or meta[k].get('status') != 'PASS' for k in ('structural_qa', 'semantic_qa'))):
            raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE', rows, receipt)
        md_stream, md_before = _safe_open(mp, MAX_MARKDOWN_BYTES)
        with md_stream:
            # Markdown is independently capped at 16 MiB. Decode once, bound its
            # marker and hash, release it before retaining any next day's rows.
            markdown = md_stream.read(MAX_MARKDOWN_BYTES + 1)
        _reject_redirects(mp)
        md_after = mp.stat()
        if ((md_before.st_ino, md_before.st_size, md_before.st_mtime_ns) != (md_after.st_ino, md_after.st_size, md_after.st_mtime_ns)
                or len(markdown) != md_before.st_size):
            raise HistoryEvidenceError('HISTORY_INDEX_SOURCE_MISMATCH', rows, receipt)
        markdown_sha = hashlib.sha256(markdown).hexdigest()
        if (markdown_sha != meta.get('markdown_sha256')
                or markdown.decode('utf-8').count('<!-- generation:' + generation + ' -->') != 1):
            raise HistoryEvidenceError('HISTORY_INDEX_SOURCE_MISMATCH', rows, receipt)
        for row in rows:
            row['_history_verified'] = True
        receipt.update(markdown_sha256=markdown_sha, verified=True,
                       verification='SOURCE_PAIR_BINDING_AND_DURABLE_QA_NOT_RECURSIVE_SCIENTIFIC_ACCEPTANCE')
        return rows, receipt
    except HistoryEvidenceError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
        raise HistoryEvidenceError('HISTORY_EVIDENCE_UNUSABLE') from None
