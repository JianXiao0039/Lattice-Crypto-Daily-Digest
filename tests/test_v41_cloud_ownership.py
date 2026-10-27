"""October 27 source-backed public ownership regressions; no Git mutation."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from lattice_digest.cloud_public_history import ownership_history
from lattice_digest.public_report import inspect_tree, validate_catalog, validate_public
from lattice_digest.report_gate import GateError, encoded, sha

FIXTURE = Path(__file__).parent / 'fixtures' / 'v41_cloud_public'
REF = '3dfa6cc5ec3c6850138459b4740b65b79fad4f5d'


def test_original_cloud_candidate_exactly_conflicts_with_authoritative_public26():
    m26, f26 = inspect_tree(FIXTURE / 'public26')
    m27, f27 = inspect_tree(FIXTURE / 'cloud27')
    provenance = json.loads((FIXTURE / 'provenance.json').read_text('utf-8'))
    assert sha(f26['daily/2026/2026-10-26.json']) == provenance['public26_json_sha256']
    assert sha(f27['daily/2026/2026-10-27.json']) == provenance['public27_json_sha256']
    assert provenance['artifact_zip_sha256'] == 'd2d6188ddb67bacec8eec3203166258a3d8d9c48344c8e9a00ecf93d9f0661b3'
    conflict = [r for r in provenance['candidate_trace'] if r['already_owned']]
    assert len(conflict) == 1
    assert conflict[0]['identity'] == 'doi:10.21203/rs.3.rs-11270790/v1'
    assert conflict[0]['same_event_id'] and conflict[0]['same_abstract_sha256']
    merged = {'reports': {**m26['reports'], **m27['reports']}}
    with pytest.raises(GateError, match='EVENT_OWNERSHIP_CONFLICT'):
        validate_catalog(merged, {**f26, **f27})


def test_validated_public_catalog_is_only_an_ownership_veto():
    rows, evidence = ownership_history(FIXTURE / 'public26', REF, '2026-10-27')
    duplicated = [r for r in rows if r.get('doi') == '10.21203/rs.3.rs-11270790/v1']
    assert len(duplicated) == 1
    assert duplicated[0]['_public_primary_owner'] == 'daily:2026-10-26'
    assert duplicated[0]['_public_event_id'] == 'b587afe451d8a061baab91575e388e6f8ad811b6be77702262e88fa4d412fc9c'
    assert not evidence['history_complete']
    assert evidence['state'] == 'HISTORY_EVIDENCE_UNUSABLE'
    assert evidence['ownership_rows_sha256'] == sha(encoded(rows))
    # No public snapshot can manufacture the old source abstract or revision.
    assert all('abstract' not in r and 'update_timestamp' not in r for r in rows)


@pytest.mark.parametrize('mutation', ['doi_case', 'new_event_id'])
def test_catalog_rejects_stable_identity_even_if_event_id_changes(mutation):
    m26, f26 = inspect_tree(FIXTURE / 'public26')
    m27, f27 = inspect_tree(FIXTURE / 'cloud27')
    report = json.loads(f27['daily/2026/2026-10-27.json'])
    paper = next(p for p in report['papers'] if p['public_canonical_id'].startswith('doi:'))
    if mutation == 'doi_case':
        paper['public_canonical_id'] = paper['public_canonical_id'].upper().replace('DOI:', 'doi:')
    else:
        paper['event_id'] = 'a' * 64
    report['public_generation_id'] = ''
    report['public_generation_id'] = sha(encoded(report))
    report = validate_public(report)
    files = {**f26, **f27, 'daily/2026/2026-10-27.json': encoded(report)}
    with pytest.raises(GateError, match='EVENT_OWNERSHIP_CONFLICT'):
        validate_catalog({'reports': {**m26['reports'], **m27['reports']}}, files)


def test_public_catalog_accepts_genuinely_distinct_remaining_source_events_without_no_news_claim():
    m26, f26 = inspect_tree(FIXTURE / 'public26')
    m27, f27 = inspect_tree(FIXTURE / 'cloud27')
    report = json.loads(f27['daily/2026/2026-10-27.json'])
    report['papers'] = [p for p in report['papers'] if not p['public_canonical_id'].startswith('doi:')]
    report['entry_count'] = report['event_count'] = 3
    report['omitted_event_count'] = 1
    report['public_generation_id'] = ''
    report['public_generation_id'] = sha(encoded(report))
    validated = validate_public(report)
    validate_catalog({'reports': {**m26['reports'], **m27['reports']}},
                     {**f26, **f27, 'daily/2026/2026-10-27.json': encoded(validated)})
    assert report['quality'] == 'PROVISIONAL_PUBLIC'
    assert report['source_coverage_state'] != 'AUTHORITATIVE_COMPLETE'
    # This catalog-level acceptance does not grant scientific export authority.
    assert report['limitations_zh'][0] == '来源覆盖受限时，报告不能用于断言该时期没有相关新论文。'


def test_history_snapshot_invalid_pin_and_tampering_fail_closed(tmp_path):
    import shutil
    with pytest.raises(GateError, match='HISTORY_EVIDENCE_UNUSABLE'):
        ownership_history(FIXTURE / 'public26', 'public-digests', '2026-10-27')
    root = tmp_path / 'snapshot'
    shutil.copytree(FIXTURE / 'public26', root)
    (root / 'daily/2026/2026-10-26.json').write_bytes(b'{}')
    with pytest.raises(GateError):
        ownership_history(root, REF, '2026-10-27')


def test_failure_receipt_artifacts_are_retained_without_changing_schedule():
    import yaml
    workflow = yaml.safe_load((Path(__file__).parents[1] / '.github/workflows/daily.yml').read_text('utf-8'))
    event = workflow.get('on', workflow.get(True))
    assert event['schedule'] == [{'cron': '17 1 * * *'}]
    publisher = workflow['jobs']['publish']['steps']
    receipt = next(s for s in publisher if s.get('name') == 'Retain public publication receipt')
    assert receipt['if'] == 'always()'
    steps = workflow['jobs']['digest']['steps']
    diagnostic = next(s for s in steps if s.get('name') == 'Retain sanitized failure diagnostics')
    assert diagnostic['if'] == 'always()'
    assert 'cloud-canonical' not in diagnostic['with']['path']
    assert 'public-history-gate.json' in diagnostic['with']['path']


def test_cloud_incomplete_generation_emits_blocked_receipt(tmp_path, monkeypatch, capsys):
    from lattice_digest import cloud_daily, run
    monkeypatch.setattr(cloud_daily, 'resolve_target', lambda *a: {'target_date': '2026-10-27'})
    def blocked_generation(args, cloud_context):
        assert cloud_context['prior_public_ownership']
        assert not cloud_context['public_ownership_evidence']['history_complete']
        return 2
    monkeypatch.setattr(run, 'main', blocked_generation)
    result = cloud_daily.main(['--event-created-at', '2026-10-27T06:14:54+00:00',
        '--trigger', 'schedule', '--output-root', str(tmp_path/'canonical'),
        '--public-output', str(tmp_path/'public'), '--public-history-root', str(FIXTURE/'public26'),
        '--public-history-ref', REF])
    receipt = json.loads(capsys.readouterr().out)
    assert result == 2 and receipt['delivery_state'] == 'HISTORY_EVIDENCE_BLOCKED'
    assert receipt['code'] == 'SCIENTIFIC_QA_INCOMPLETE'
    assert receipt['publish_pending'] is False and not receipt['public_export_eligible']
    assert not (tmp_path/'public').exists()


@pytest.mark.parametrize('unsafe', ['symlink', 'oversized'])
def test_read_only_snapshot_transport_rejects_unsafe_archive(tmp_path, monkeypatch, unsafe):
    import io
    import tarfile
    from lattice_digest import cloud_public_history as history
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        member = tarfile.TarInfo('repository/manifest.json')
        if unsafe == 'symlink':
            member.type = tarfile.SYMTYPE
            member.linkname = '../private'
            archive.addfile(member)
        else:
            member.size = 1024*1024+1
            archive.addfile(member, io.BytesIO(b' ' * member.size))
    class Opener:
        def open(self, request, timeout):
            return io.BytesIO(encoded({'object': {'sha': REF}}) if '/git/ref/' in request.full_url else buffer.getvalue())
    monkeypatch.setattr(history.urllib.request, 'build_opener', lambda *a: Opener())
    code = 'HISTORY_RESOURCE_LIMIT' if unsafe == 'oversized' else 'HISTORY_EVIDENCE_UNUSABLE'
    with pytest.raises(GateError, match=code):
        history.fetch_snapshot('JianXiao0039/Lattice-Crypto-Daily-Digest', tmp_path/'snapshot')
    assert not (tmp_path/'snapshot').exists()


def test_snapshot_fetch_is_bounded_create_only_and_does_not_consume_local_token(tmp_path, monkeypatch):
    import io
    import tarfile
    from lattice_digest import cloud_public_history as history
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        for name, content in inspect_tree(FIXTURE/'public26')[1].items():
            member = tarfile.TarInfo('repository/'+name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    class Opener:
        def open(self, request, timeout):
            assert not request.has_header('Authorization')
            assert timeout == 30
            return io.BytesIO(encoded({'object': {'sha': REF}}) if '/git/ref/' in request.full_url else buffer.getvalue())
    monkeypatch.setenv('GH_TOKEN', 'PRIVATE_LOCAL_TOKEN_CANARY')
    monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
    monkeypatch.setattr(history.urllib.request, 'build_opener', lambda *a: Opener())
    root = tmp_path/'snapshot'
    receipt = history.fetch_snapshot('JianXiao0039/Lattice-Crypto-Daily-Digest', root)
    assert receipt['source_ref'] == REF
    assert receipt['report_count'] == 1
    assert inspect_tree(root)[1] == inspect_tree(FIXTURE/'public26')[1]
    with pytest.raises(GateError, match='PUBLISH_CONFLICT'):
        history.fetch_snapshot('JianXiao0039/Lattice-Crypto-Daily-Digest', root)
    monkeypatch.setattr(history, 'MAX_TAR_BYTES', 64)
    with pytest.raises(GateError, match='HISTORY_RESOURCE_LIMIT'):
        history.fetch_snapshot('JianXiao0039/Lattice-Crypto-Daily-Digest', tmp_path/'bomb')
