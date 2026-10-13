import gzip
import json
from pathlib import Path

import pytest

from lattice_digest.authority import semantic_qa
from lattice_digest import report_repair as repair
from lattice_digest.export_field_repair import candidate_bytes, repair_export
from lattice_digest.scientific_scope import evaluate_scope


def row():
    return {'title': 'Module Lattice Security (Part IV): Probabilistic Polynomial Quantum Attack on Module-LWE over 2-Power Cyclotomics',
        'abstract': 'We present a quantum attack on ML-KEM and related 2-power cyclotomic lattice schemes.',
        'source': 'arxiv', 'source_url': 'http://arxiv.org/abs/2605.17412v2',
        'paper_id': 'arxiv:2605.17412', 'publication_date': '2026-05-17',
        'update_date': '2026-05-25', 'authors': ['Ming-Xing Luo'], 'relevance_label': 'A', 'relevance_score': 100}


@pytest.mark.parametrize('rows', [[], [row()]])
def test_legacy_restatement_preserves_missing_facts_and_never_reroutes_new(rows, tmp_path):
    raw = json.dumps(rows).encode()
    candidate = repair.prepare_legacy_candidate(rows, repair.digest(raw), '2026-05-26')
    md = repair.render_daily(candidate, '2026-05-26')
    assert semantic_qa(candidate, md.decode())['status'] == 'PASS'
    assert '原始覆盖窗口' in md.decode() and 'N/A' in md.decode()
    assert 'publication_event_ledger' not in candidate
    assert candidate['metadata']['coverage_start'] is None
    assert candidate['metadata']['source_coverage']['complete'] is False
    assert not any(r['primary_today_new_eligible'] for r in candidate['records'])
    repair.validate_legacy_wrapper(rows, candidate, '2026-05-26')
    jp, mp = repair.pair_paths(tmp_path, 'daily', '2026-05-26')
    jp.parent.mkdir(parents=True); mp.parent.mkdir(parents=True)
    jp.write_text(json.dumps(candidate)); mp.write_bytes(md)
    assert repair.validate_candidate(tmp_path, tmp_path, 'daily', '2026-05-26', rows, candidate, md)['durable'] == 'PASS'


@pytest.mark.parametrize('mutation', ['health', 'window', 'primary', 'event', 'source', 'original_hash'])
def test_legacy_unknown_health_is_not_a_publication_qa_bypass(mutation):
    original = [row()]
    candidate = repair.prepare_legacy_candidate(original, 'a' * 64, '2026-05-26')
    if mutation == 'health': candidate['source_health'][0]['health_status'] = 'green'
    if mutation == 'window': candidate['metadata']['coverage_start'] = '2026-05-25T00:00:00+08:00'
    if mutation == 'primary': candidate['records'][0]['primary_today_new_eligible'] = True
    if mutation == 'event': candidate['publication_event_ledger'] = {}
    if mutation == 'source': candidate['records'][0]['abstract'] = 'Replacement source'
    if mutation == 'original_hash': candidate['metadata']['legacy_original_json_sha256'] = ''
    if mutation != 'original_hash':
        with pytest.raises(ValueError): repair.validate_legacy_wrapper(original, candidate, '2026-05-26')
    assert semantic_qa(candidate, repair.render_daily(candidate, '2026-05-26').decode())['status'] == 'FAIL'


def export_fixture(tmp_path):
    source = tmp_path / 'data/2026/daily/2026-05-26.json'
    source.parent.mkdir(parents=True); source.write_text(json.dumps({'records': [row()]}))
    export = tmp_path / 'exports/reading-queue/todo-read.md'
    export.parent.mkdir(parents=True)
    export.write_bytes(('# 手工笔记\r\n- Example｜A / 100｜review_status=human-approved｜' + row()['source_url'] + '\r\n用户笔记保持原样\r\n').encode())
    item = {'path': str(export), 'original_sha256': repair.digest(export.read_bytes()), 'patches': [{
        'line': 2, 'old_label': 'A', 'old_score': 100, 'url': row()['source_url'],
        'source_path': str(source), 'source_sha256': repair.digest(source.read_bytes()), 'source_row': 0}]}
    return export, source, item


def test_export_repair_preserves_manual_annotations_exact_bytes_and_snapshot(tmp_path):
    export, source, item = export_fixture(tmp_path)
    old = export.read_bytes()
    result = repair_export(tmp_path, item, tmp_path / '.ops/evidence/transactions', execute=True)
    assert result['status'] == 'PROMOTED'
    assert export.read_bytes() == old.replace(b'A / 100', b'A / 90')
    with gzip.open(Path(result['evidence_directory']) / 'original.md.gz', 'rb') as stream:
        assert stream.read() == old


@pytest.mark.parametrize('mutation', ['export_drift', 'source_drift', 'identity', 'path', 'traversal'])
def test_export_drift_and_ownership_fail_before_writing(tmp_path, mutation):
    export, source, item = export_fixture(tmp_path)
    if mutation == 'export_drift': export.write_bytes(export.read_bytes() + b'New user note')
    if mutation == 'source_drift': source.write_bytes(source.read_bytes() + b' ')
    if mutation == 'identity': item['patches'][0]['url'] = 'https://example.test/unrelated'
    if mutation == 'path': item['path'] = str(tmp_path / 'docs/manual.md')
    if mutation == 'traversal':
        manual = tmp_path / 'exports/manual.md'; manual.write_bytes(export.read_bytes())
        item['path'] = str(export.parent / '../manual.md')
    old = export.read_bytes()
    with pytest.raises(ValueError): candidate_bytes(tmp_path, item)
    assert export.read_bytes() == old


def test_math_power_is_not_physical_attack_but_power_analysis_is():
    assert evaluate_scope(row())['scientific_scope'] == 'CORE_LATTICE_CRYPTO'
    physical = dict(row(), title='Power analysis of ML-KEM', abstract='We study power traces of an ML-KEM implementation.')
    assert evaluate_scope(physical)['scientific_scope'] == 'LATTICE_RELEVANT_IMPLEMENTATION'


def test_export_concurrent_edit_before_publication_is_never_rolled_back(tmp_path, monkeypatch):
    import lattice_digest.export_field_repair as export_repair
    export, source, item = export_fixture(tmp_path)
    user_bytes = export.read_bytes() + '并发用户笔记'.encode()
    actual = export_repair.candidate_bytes
    calls = []
    def drift(*args):
        calls.append(1)
        if len(calls) == 2: export.write_bytes(user_bytes)
        return actual(*args)
    monkeypatch.setattr(export_repair, 'candidate_bytes', drift)
    with pytest.raises(ValueError, match='hash drift'):
        repair_export(tmp_path, item, tmp_path / '.ops/evidence/transactions', execute=True)
    assert export.read_bytes() == user_bytes
    assert not list(export.parent.glob('*.lock'))


def test_entry_failure_is_durable_redacted_and_does_not_claim_source_zero(tmp_path, monkeypatch):
    from lattice_digest.public_contract import record_entry_failure
    monkeypatch.setenv('LATTICE_DIGEST_CANONICAL_ROOT', str(tmp_path))
    monkeypatch.setenv('TEST_API_KEY', 'private-secret-for-test')
    path = record_entry_failure('DAILY', ValueError('private-secret-for-test'), stage='PREFLIGHT')
    payload = json.loads(Path(path).read_text())
    assert 'private-secret-for-test' not in Path(path).read_text()
    assert payload['source_attempts'] == payload['discovery_counts'] == 'N/A'
    assert payload['status'] == 'REPORT_NOT_GENERATED_OPERATIONAL_FAILURE'
    assert not (tmp_path / 'data').exists()
