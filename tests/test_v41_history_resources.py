"""V4.1 regression uses the preserved incident pair when available, never network."""
from datetime import date
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import time

import pytest

from lattice_digest.history_resources import (HistoryEvidenceError, _JSONProjection,
    load_verified_history_pair, MAX_HISTORY_BYTES, MAX_HISTORY_RECORDS,
    MAX_HISTORY_DEPTH, MAX_TOKEN_CHARS, MAX_TOTAL_COMPACT_BYTES)
from lattice_digest.promotion_history import (load_promotion_history, identity_keys, classify_event,
    authoritative_version, authoritative_version_conflicted)

DAY = date(2026, 10, 26)
ORIGINAL = Path(os.environ.get('V41_ORIGINAL_ROOT',
    r'D:\Code\CodexProjects\lattice-crypto-daily-digest'))


@pytest.fixture(scope='module')
def incident_pair():
    jp = ORIGINAL / 'data/2026/daily/2026-10-26.json'
    mp = ORIGINAL / 'digests/2026/daily/2026-10-26.md'
    if not jp.is_file() or not mp.is_file():
        pytest.skip('preserved 33,998,116-byte incident pair unavailable')
    assert jp.stat().st_size == 33998116
    assert hashlib.sha256(jp.read_bytes()).hexdigest() == '57ce85cb8cc85b0a5ea9fe75d0b65b34f11a988914e210f5d33b5c30317647e5'
    assert hashlib.sha256(mp.read_bytes()).hexdigest() == '94ef2ced72cf261ebcfe9ee315e369d354d6b1ef987fc39512ab41557564e848'
    return jp, mp


def install_pair(root, pair):
    jp, mp = root / 'data/2026/daily/2026-10-26.json', root / 'digests/2026/daily/2026-10-26.md'
    jp.parent.mkdir(parents=True); mp.parent.mkdir(parents=True)
    shutil.copyfile(pair[0], jp); shutil.copyfile(pair[1], mp)
    return jp, mp


def test_real_incident_pair_accepted_with_exact_source_binding(incident_pair):
    started = time.monotonic()
    rows, receipt = load_verified_history_pair(ORIGINAL / 'data', DAY)
    assert len(rows) == 683
    assert receipt['source_bytes'] == 33998116
    assert receipt['sha256'] == '57ce85cb8cc85b0a5ea9fe75d0b65b34f11a988914e210f5d33b5c30317647e5'
    assert receipt['generation_id'] == 'e59d853d108a4d848d61bb38d58a8835'
    assert receipt['verified'] is True
    assert all(r['_promotion_date'] == str(DAY) and r['_history_verified'] for r in rows)
    assert time.monotonic() - started < 60
    duplicate = next(r for r in rows if 'doi:10.21203/rs.3.rs-11270790/v1' in identity_keys(r))
    assert classify_event(duplicate, rows)[0] in {'METADATA_ONLY_UPDATE', 'UNCHANGED_CROSS_DAY_DUPLICATE'}
    assert not {'evidence_items', 'research_sections', 'provenance_strength'} & duplicate.keys()


@pytest.mark.parametrize('size', [32 * 1024 * 1024, 32 * 1024 * 1024 + 1, MAX_HISTORY_BYTES])
def test_source_shaped_history_boundaries(tmp_path, incident_pair, size):
    jp, _ = install_pair(tmp_path, incident_pair)
    # Keep all original records, metadata, ledger and their shape. The redundant
    # full historical projection is removed, then legal JSON whitespace fills
    # the exact boundary; this is not a tiny fabricated record substitute.
    payload = json.loads(jp.read_text('utf-8'))
    payload.pop('publication_history_evidence', None)
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()
    assert len(raw) < size
    with jp.open('wb') as stream:
        stream.write(raw)
        remaining = size - len(raw)
        while remaining:
            amount = min(65536, remaining); stream.write(b' ' * amount); remaining -= amount
    rows, receipt = load_verified_history_pair(tmp_path / 'data', DAY)
    assert len(rows) == 683 and receipt['source_bytes'] == size


def test_new_hard_limit_plus_one_rejected_before_decode(tmp_path, incident_pair):
    jp, _ = install_pair(tmp_path, incident_pair)
    with jp.open('r+b') as stream: stream.truncate(MAX_HISTORY_BYTES + 1)
    with pytest.raises(HistoryEvidenceError, match='HISTORY_RESOURCE_LIMIT'):
        load_verified_history_pair(tmp_path / 'data', DAY)


@pytest.mark.parametrize('mutation', ['truncated', 'corrupt', 'missing', 'pair_hash', 'generation'])
def test_unusable_history_has_explicit_incomplete_state(tmp_path, incident_pair, mutation):
    jp, mp = install_pair(tmp_path, incident_pair)
    if mutation == 'truncated':
        with jp.open('r+b') as stream: stream.truncate(jp.stat().st_size // 2)
    elif mutation == 'corrupt': jp.write_bytes(b'{"records": [NaN]}')
    elif mutation == 'missing': jp.unlink()
    elif mutation == 'pair_hash': mp.write_bytes(mp.read_bytes() + b' changed')
    elif mutation == 'generation': mp.write_bytes(mp.read_bytes().replace(b'e59d853d108a4d848d61bb38d58a8835', b'00000000000000000000000000000000'))
    _, evidence = load_promotion_history(tmp_path / 'data', date(2026, 10, 27), days=1)
    assert evidence['schema_version'] == 'history-evidence-v41'
    assert not evidence['complete'] and not evidence['primary_ownership_eligible']
    assert evidence['state'] == 'HISTORY_EVIDENCE_BLOCKED'
    if mutation in {'pair_hash', 'generation'}:
        assert evidence['unusable'][0]['code'] == 'HISTORY_INDEX_SOURCE_MISMATCH'


def test_symlinked_history_is_not_read(tmp_path, incident_pair):
    jp, _ = install_pair(tmp_path, incident_pair)
    jp.unlink()
    try: jp.symlink_to(incident_pair[0])
    except OSError: pytest.skip('Windows symlink creation unavailable')
    with pytest.raises(HistoryEvidenceError, match='HISTORY_EVIDENCE_UNUSABLE'):
        load_verified_history_pair(tmp_path / 'data', DAY)


@pytest.mark.parametrize('raw,code', [
    (b'{"unretained":{"a":1,"a":2},"records":[]}', 'HISTORY_EVIDENCE_UNUSABLE'),
    (b'{"unretained":NaN,"records":[]}', 'HISTORY_EVIDENCE_UNUSABLE'),
    (b'{"unretained":1 2,"records":[]}', 'HISTORY_EVIDENCE_UNUSABLE'),
    (b'{"unretained":1e1000,"records":[]}', 'HISTORY_EVIDENCE_UNUSABLE'),
    (b'{"records":[' + b'{},' * MAX_HISTORY_RECORDS + b'{}]}', 'HISTORY_RESOURCE_LIMIT'),
    (b'{"x":' + b'[' * (MAX_HISTORY_DEPTH + 1) + b'0' + b']' * (MAX_HISTORY_DEPTH + 1) + b'}', 'HISTORY_RESOURCE_LIMIT'),
    (b'{"x":"' + b'a' * (MAX_TOKEN_CHARS + 1) + b'"}', 'HISTORY_RESOURCE_LIMIT'),
], ids=['duplicate-key', 'nan', 'split-number', 'infinite-number', 'records-limit', 'depth-limit', 'token-limit'])
def test_bounded_parser_checks_even_discarded_branches(raw, code):
    with pytest.raises(HistoryEvidenceError, match=code):
        _JSONProjection(io.BytesIO(raw)).value()


def test_source_changes_recompute_binding_without_trusting_sidecar(tmp_path, incident_pair):
    jp, _ = install_pair(tmp_path, incident_pair)
    # No unauthenticated sidecar is part of this fallback contract.
    jp.with_suffix('.history-index.json').write_text('{"verified":true,"records":[]}', 'utf-8')
    _, before = load_verified_history_pair(tmp_path / 'data', DAY)
    with jp.open('ab') as stream: stream.write(b'\n')
    rows, after = load_verified_history_pair(tmp_path / 'data', DAY)
    assert len(rows) == 683 and before['sha256'] != after['sha256']
    assert after['source_bytes'] == before['source_bytes'] + 1


def test_identity_aliases_do_not_use_title():
    assert identity_keys({'doi': '10.21203/RS.3.RS-11270790/v1'}) & identity_keys({'source_url': 'https://DOI.org/10.21203/rs.3.rs-11270790/v1'})
    assert identity_keys({'arxiv_id': '2501.12345v1'}) & identity_keys({'source_url': 'http://arxiv.org/pdf/2501.12345v3.pdf'})
    assert identity_keys({'arxiv_id': 'https://arxiv.org/abs/2501.12345v3'}) == {'arxiv:2501.12345'}
    assert identity_keys({'source_url': 'http://example.org/paper#abstract'}) & identity_keys({'source_url': 'https://example.org/paper/'})
    assert not identity_keys({'title': 'Identical title'})


def test_conflicting_internal_identity_or_version_never_promotes():
    assert classify_event({'doi': '10.1234/one', 'source_url': 'https://doi.org/10.1234/two'}, [])[0] == 'IDENTITY_UNCERTAIN'
    conflict = {'arxiv_id': '2501.12345v2', 'source_url': 'https://arxiv.org/abs/2501.12345v1'}
    assert authoritative_version_conflicted(conflict)
    assert classify_event(conflict, [])[0] == 'IDENTITY_UNCERTAIN'
    assert authoritative_version({'source_url': 'https://arxiv.org/pdf/2501.12345V2.pdf'}) == 'v2'


def test_unchanged_doi_and_authenticated_revision_have_distinct_categories():
    old = {'doi': '10.1234/one', 'abstract': 'Unchanged source abstract.', '_promotion_date': '2026-10-26'}
    current = {'doi': '10.1234/one', 'abstract': 'Unchanged source abstract.'}
    assert classify_event(current, [old])[0] == 'UNCHANGED_CROSS_DAY_DUPLICATE'
    assert classify_event({**current, 'venue': 'corrected metadata'}, [old])[0] == 'METADATA_ONLY_UPDATE'
    revised = {**current, 'abstract': 'Actual technical revision.', 'update_timestamp': '2026-10-27T00:00:00+00:00',
               'update_date_kind': 'AUTHORITATIVE_CONTENT_REVISION_DATE'}
    assert classify_event(revised, [old])[0] == 'GENUINE_CONTENT_REVISION'
    assert classify_event({**revised, 'update_date_kind': 'UNSUPPORTED'}, [old])[0] == 'IDENTITY_UNCERTAIN'
    assert classify_event(revised, [{**old, '_history_verified': False}])[0] == 'IDENTITY_UNCERTAIN'


def test_real_fourteen_day_history_does_not_lose_identity_to_size_limit(incident_pair):
    rows, evidence = load_promotion_history(ORIGINAL / 'data', date(2026, 10, 27))
    assert any(item['date'] == '2026-10-26' for item in evidence['loaded'])
    assert not any(item['code'] == 'HISTORY_RESOURCE_LIMIT' for item in evidence['unusable'])
    assert evidence['compact_accounted_bytes'] <= MAX_TOTAL_COMPACT_BYTES
    # October 17 is not a verified controlled publication. It must remain an
    # explicit blocker; later knowledge cannot turn it into original authority.
    assert not evidence['complete']
    assert any(item['date'] == '2026-10-17' for item in evidence['unusable'])
    assert len(rows) >= 7637
