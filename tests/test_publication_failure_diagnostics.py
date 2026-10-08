from datetime import date, datetime
import hashlib
import json
from pathlib import Path

import pytest

from lattice_digest import storage
from lattice_digest.authority import INCOMPLETE_ZERO_TEXT
from lattice_digest.models import make_paper_record
from lattice_digest.publication_diagnostics import DailyPublicationQAError, MAX_CANDIDATE_BYTES
from lattice_digest.recovery_window import exact_window, recovery_metadata

DAY = date(2026, 10, 7)
START = '2026-10-05T21:04:26.631541+08:00'
END = '2026-10-07T09:04:26.631541+08:00'
EXECUTED = '2026-10-08T11:21:21.293562+08:00'
HEALTH = [{'source': 'arxiv', 'health_status': 'yellow', 'runtime_state': 'partial'}]


def metadata():
    lower, upper = exact_window(START, END, DAY.isoformat(), run_mode='backfill')
    return {**recovery_metadata(DAY, lower, upper, datetime.fromisoformat(EXECUTED), 'PUBLIC_AUTOMATION_RUNTIME_CODE_BLOCKED'),
            'target_date': DAY.isoformat(), 'coverage_start': START, 'coverage_end': END,
            'run_mode': 'backfill', 'quality_status': 'authoritative_backfill',
            'runtime_git_head': 'fixture-head', 'runtime_code_manifest_sha256': 'fixture-manifest',
            'runtime_code_state': 'PUBLISHED_CLEAN_RUNTIME'}


@pytest.fixture
def runtime_gate(monkeypatch):
    # Unit fixture only; the unchanged public gate is independently exercised in
    # test_runtime_isolation_v2 with real clean Git repositories and subprocesses.
    monkeypatch.setattr('lattice_digest.runtime_provenance.runtime_provenance', lambda *args, **kwargs: {
        'runtime_code_state': 'PUBLISHED_CLEAN_RUNTIME', 'runtime_git_head': 'fixture-head',
        'runtime_code_manifest_sha256': 'fixture-manifest'})


def invalid_record():
    return make_paper_record(title='LWE analysis', abstract='Source studies LWE security.',
                            source='arxiv', source_url='https://arxiv.org/abs/2610.00001v1',
                            arxiv_id='2610.00001v1', publication_date='2026-10-06',
                            relevance_label='A', relevance_score=40)


def reject(root, records=None, **kwargs):
    with pytest.raises(DailyPublicationQAError) as error:
        storage.publish_daily_pair(records if records is not None else [invalid_record()], root, DAY,
                                   source_health=HEALTH, **kwargs)
    return error.value


def test_qa_rejection_retains_structured_issue_fields(tmp_path):
    error = reject(tmp_path)
    detail = json.loads(error.diagnostic_path.read_text(encoding='utf-8'))
    issue = next(i for i in detail['issues'] if i['issue_code'] == 'RELEVANCE_SCORE_LABEL_INCONSISTENT')
    assert issue['affected_field'].startswith('records[0].relevance_score')
    assert issue['expected_value'] == {'relevance_label': 'C'}
    assert issue['observed_value']['relevance_label'] == 'A'
    assert issue['qa_stage'] == 'semantic' and issue['issue_severity'] == 'ERROR'
    assert issue['candidate_artifact_sha256'] == hashlib.sha256(Path(issue['artifact_path']).read_bytes()).hexdigest()
    assert detail['exception_type'] == 'DailyPublicationQAError' and len(detail['bounded_traceback']) <= 8
    assert error.issues and 'RELEVANCE_SCORE_LABEL_INCONSISTENT' in str(error)


def test_exact_temporary_cleanup_leaves_durable_failure_only(tmp_path, monkeypatch, runtime_gate):
    temporary_roots = []
    original = storage._publish_daily_pair_locked
    def capture(records, root, *args, **kwargs):
        temporary_roots.append(root)
        return original(records, root, *args, **kwargs)
    monkeypatch.setattr(storage, '_publish_daily_pair_locked', capture)
    error = reject(tmp_path, metadata=metadata())
    assert temporary_roots and all(not path.exists() for path in temporary_roots)
    assert error.diagnostic_path.is_relative_to(tmp_path / 'audits/daily-publication-failures')
    assert error.diagnostic_path.exists() and error.issues
    assert not (tmp_path / 'data').exists() and not (tmp_path / 'digests').exists()


def test_structural_contradiction_remains_rejected(tmp_path, monkeypatch):
    original = storage.generate_markdown
    monkeypatch.setattr(storage, 'generate_markdown', lambda *a, **k: original(*a, **k).removeprefix('# '))
    error = reject(tmp_path, [])
    assert 'STRUCTURAL_QA_FAILED' in {i['issue_code'] for i in error.issues}


def test_semantic_contradiction_remains_rejected(tmp_path, monkeypatch):
    original = storage.generate_markdown
    monkeypatch.setattr(storage, 'generate_markdown', lambda *a, **k: original(*a, **k) + '\nsafe to skip')
    error = reject(tmp_path, [])
    assert 'incomplete_zero_negative_or_skip_claim' in {i['issue_code'] for i in error.issues}


def test_incomplete_zero_and_limited_history_do_not_assert_full_coverage(tmp_path, runtime_gate):
    jp, mp = storage.publish_daily_pair([], tmp_path, DAY, source_health=HEALTH, metadata=metadata())
    payload = json.loads(jp.read_text(encoding='utf-8'))
    assert payload['metadata']['authority_state'] == 'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'
    assert payload['metadata']['source_coverage']['complete'] is False
    assert INCOMPLETE_ZERO_TEXT in mp.read_text(encoding='utf-8')
    assert payload['metadata']['semantic_qa']['status'] == 'PASS'


def test_exact_timestamps_and_real_execution_survive_rejection(tmp_path, runtime_gate):
    error = reject(tmp_path, metadata=metadata())
    details = json.loads(error.diagnostic_path.read_text(encoding='utf-8'))
    assert details['coverage_start'] == START and details['coverage_end'] == END
    assert details['recovery_executed_at'] == EXECUTED and EXECUTED != END
    candidate = json.loads((error.diagnostic_path.parent / 'candidate.json').read_text(encoding='utf-8'))
    assert candidate['metadata']['recovery_requested_window'] == metadata()['recovery_requested_window']


def test_prior_same_version_false_primary_still_fails(tmp_path):
    from lattice_digest.promotion_history import apply_promotion_history
    from lattice_digest.radar_freshness import STRICT_FRESHNESS_POLICY_VERSION
    row = invalid_record().model_copy(update={'relevance_score': 80, 'primary_today_new_eligible': True,
                                             'freshness_policy_version': STRICT_FRESHNESS_POLICY_VERSION})
    prior = row.model_dump(mode='json')
    path = tmp_path / 'data/2026/daily/2026-10-06.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'metadata': {'quality_status': 'authoritative'}, 'records': [prior]}))
    assert apply_promotion_history([row], [prior])[0].primary_today_new_eligible is False
    error = reject(tmp_path, [row])
    assert 'cross_day_false_primary' in {i['issue_code'] for i in error.issues}
    assert error.details['cross_day_qa']['status'] == 'FAIL'


def test_publication_qa_reruns_without_a_source_crawl(tmp_path, monkeypatch):
    monkeypatch.setattr('lattice_digest.run._collect_records', lambda *a: pytest.fail('no second crawl'))
    first = reject(tmp_path / 'first')
    second = reject(tmp_path / 'second')
    assert [i['issue_code'] for i in first.issues] == [i['issue_code'] for i in second.issues]


def test_existing_valid_pair_never_overwritten(tmp_path, runtime_gate):
    jp, mp = storage.publish_daily_pair([], tmp_path, DAY, source_health=HEALTH, metadata=metadata())
    original = (jp.read_bytes(), mp.read_bytes())
    with pytest.raises(FileExistsError):
        storage.publish_daily_pair([invalid_record()], tmp_path, DAY, source_health=HEALTH, metadata=metadata())
    assert original == (jp.read_bytes(), mp.read_bytes())


def test_valid_positive_degraded_recovery_supported_without_complete_authority(tmp_path, runtime_gate):
    row = invalid_record().model_copy(update={'relevance_score': 80})
    jp, _ = storage.publish_daily_pair([row], tmp_path, DAY, source_health=HEALTH, metadata=metadata())
    meta = json.loads(jp.read_text(encoding='utf-8'))['metadata']
    assert meta['authority_state'] == 'AUTHORITATIVE_DEGRADED'
    assert meta['source_coverage']['complete'] is False
    assert meta['publication_state'] == 'QA_PASSED'


def test_invalid_historical_candidate_is_not_promoted(tmp_path, runtime_gate):
    error = reject(tmp_path, metadata=metadata())
    assert error.details['qa_decision'] == 'REJECT'
    assert not (tmp_path / 'data/2026/daily/2026-10-07.json').exists()
    assert not (tmp_path / 'digests/2026/daily/2026-10-07.md').exists()


def test_secret_and_http_body_redaction(tmp_path, monkeypatch):
    secret = 'test-secret-938319'
    monkeypatch.setenv('INCIDENT_API_KEY', secret)
    error = reject(tmp_path, metadata={'api_key': secret, 'note': 'Bearer hidden-token password=hidden-password',
                                     'url': 'https://user:hidden@host/path?token=hidden-query'},
                   warnings=[f'provider error {secret}; body_preview=<html>unrestricted-body</html>'])
    combined = '\n'.join(p.read_text(encoding='utf-8') for p in error.diagnostic_path.parent.iterdir())
    for forbidden in (secret, 'hidden-token', 'hidden-password', 'hidden-query', 'user:hidden', 'unrestricted-body'):
        assert forbidden not in combined
    assert '[REDACTED]' in combined


def test_diagnostics_are_not_canonical_publication(tmp_path):
    error = reject(tmp_path)
    detail = json.loads(error.diagnostic_path.read_text(encoding='utf-8'))
    candidate = json.loads((error.diagnostic_path.parent / 'candidate.json').read_text(encoding='utf-8'))
    assert candidate['metadata']['publication_state'] == detail['publication_state'] == 'QA_REJECTED_DIAGNOSTIC_ONLY'
    assert not list(tmp_path.rglob('2026-10-07.json'))
    assert not list(tmp_path.rglob('2026-10-07.md'))


def test_diagnostic_io_failure_keeps_issue_list_and_nonzero_exception(tmp_path, monkeypatch):
    monkeypatch.setattr('lattice_digest.publication_diagnostics.os.fsync', lambda *a: (_ for _ in ()).throw(OSError('secret-write-failure')))
    error = reject(tmp_path)
    assert error.issues and error.diagnostic_path is None
    assert error.persistence_error == 'OSError'
    assert 'secret-write-failure' not in str(error)


def test_large_candidate_retention_is_bounded_and_marked_incomplete(tmp_path):
    # Distinct bounded strings exercise the aggregate byte limit, not truncation alone.
    error = reject(tmp_path, metadata={'large_fixture': ['x' * 32000 for _ in range(300)]})
    assert error.details['candidate_complete'] is False
    artifact_bytes = sum(p.stat().st_size for p in error.diagnostic_path.parent.glob('candidate.*'))
    assert artifact_bytes <= MAX_CANDIDATE_BYTES
    json.loads((error.diagnostic_path.parent / 'candidate.json').read_text(encoding='utf-8'))


def incident_records():
    from lattice_digest.evidence_contract import propagate_source_health
    fixture = json.loads((Path(__file__).parent / 'fixtures/publication_qa_incident_2026_10_07.json').read_text(encoding='utf-8'))
    rows = [make_paper_record(**row) for row in fixture['records']]
    return propagate_source_health(rows, [{'source':'arxiv','health_status':'yellow','runtime_state':'partial'},
                                         {'source':'openalex','health_status':'green','runtime_state':'complete'}])


def test_real_late_merge_rebinds_evidence_to_replaced_abstract():
    from lattice_digest.evidence_contract import evidence_quality_issues
    from lattice_digest.retrieval_v3 import apply_semantic_consequence_analysis_v3
    from lattice_digest.dedup import merge_records
    original, longer, _ = incident_records()
    first, second = apply_semantic_consequence_analysis_v3([original, longer])
    assert 'FND.LIP' not in first.source_concept_ids
    assert 'FND.LIP' in second.source_concept_ids
    merged = merge_records(first, second)
    assert merged.abstract == longer.abstract
    assert merged.relevance_score == 90 and merged.relevance_label == 'A'
    assert 'FND.LIP' in merged.source_concept_ids
    assert not evidence_quality_issues(merged)
    assert all(item['source_span'] for item in merged.evidence_items)
    expected_node = 'paper:' + hashlib.sha256((merged.paper_id or merged.source_url).encode('utf-8')).hexdigest()[:24]
    assert all(edge['source_node'] == expected_node for edge in merged.consequence_edges)


def test_real_source_grounded_typed_relation_has_consistent_qa_scope():
    from lattice_digest.evidence_contract import evidence_quality_issues
    from lattice_digest.retrieval_v3 import apply_semantic_consequence_analysis_v3
    row = apply_semantic_consequence_analysis_v3([incident_records()[2]])[0]
    assert row.relevance_score == 80 and row.relevance_label == 'A'
    assert any(edge['target_node'] == 'PRIM.PRIVACY_SIGNATURE' and edge['evidence_state'] == 'SOURCE_ASSERTED' for edge in row.consequence_edges)
    assert not evidence_quality_issues(row)


def test_forged_stored_edge_cannot_bypass_source_scope_cap():
    from lattice_digest.evidence_contract import POLICY_VERSION, evidence_quality_issues
    row = make_paper_record(title='Generic ring signatures', abstract='', source='arxiv',
                            source_url='https://arxiv.org/abs/2610.00002', relevance_score=80,
                            relevance_label='A', evidence_policy_version=POLICY_VERSION,
                            consequence_edges=[{'target_node':'PRIM.PRIVACY_SIGNATURE','evidence_state':'SOURCE_ASSERTED'}],
                            source_health='green',source_health_provenance={'arxiv':{'health_status':'green'}})
    assert 'ONTOLOGY_COANCHOR_POLICY_VIOLATION' in evidence_quality_issues(row)


def test_missing_new_concept_in_merged_source_still_fails():
    from lattice_digest.evidence_contract import evidence_quality_issues
    from lattice_digest.retrieval_v3 import apply_semantic_consequence_analysis_v3
    first, second = apply_semantic_consequence_analysis_v3(incident_records()[:2])
    stale = first.model_copy(update={'abstract':second.abstract,'relevance_score':second.relevance_score,'relevance_label':second.relevance_label})
    assert 'INFERENCE_TO_EVIDENCE_FEEDBACK' in evidence_quality_issues(stale)
