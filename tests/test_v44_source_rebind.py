"""TEST_ONLY publication transport; no real historical date assertions."""
import json
import pytest
from lattice_digest.public_report import export, render, validate_public
from lattice_digest.public_publisher import publish
from lattice_digest.public_technical import grounded_detail
from lattice_digest.report_gate import encoded, sha, GateError
from lattice_digest.storage import publish_daily_pair
from lattice_digest.evidence_contract import bind_source_evidence
from lattice_digest.models import make_paper_record
from tests.test_public_report_pipeline import source_with_test_time, META, DAY, bare
from tests.test_nested_public_e2e import health
from tests.v41_history_fixture import seed_empty_history


def rewrite(output, manifest, p):
    entry = next(iter(manifest['reports'].values()))
    p['public_generation_id'] = ''
    p['public_generation_id'] = sha(encoded(p))
    jb, mb = encoded(p)+b'\n', render(p)
    (output/entry['json']).write_bytes(jb)
    (output/entry['markdown']).write_bytes(mb)
    entry.update(json_sha256=sha(jb), markdown_sha256=sha(mb), public_generation_id=p['public_generation_id'])
    (output/'manifest.json').write_bytes(encoded(manifest)+b'\n')


def candidate(tmp_path):
    root = tmp_path/'canonical'
    seed_empty_history(root, DAY)
    row = source_with_test_time(publication_date='2000-01-01')
    publish_daily_pair([bind_source_evidence(make_paper_record(**row))], root, DAY,
                       source_health=health(degraded=True), metadata=META)
    output = tmp_path/'candidate'
    manifest = export(root, 'daily', str(DAY), output)
    return root, output, manifest


def test_bound_radar_has_real_local_bare_remote_readback(tmp_path):
    root, output, _ = candidate(tmp_path)
    result = publish(output, str(bare(tmp_path)), approved=True, canonical_root=root)
    assert result['status'] == 'PUBLISHED_TEST_REMOTE'
    assert result['remote_readback'] == 'PASS'


def test_one_way_same_canonical_noncounting_migration(tmp_path):
    from copy import deepcopy
    root, output, manifest = candidate(tmp_path)
    entry = next(iter(manifest['reports'].values()))
    original = json.loads((output/entry['json']).read_bytes())
    old = deepcopy(original)
    old['noncounting_observations'] = []
    old['revision_reason'] = 'SOURCE_GROUNDED_READABILITY_AND_CLOCK_DISCLOSURE_V2'
    rewrite(output, manifest, old)
    remote = str(bare(tmp_path))
    assert publish(output, remote, approved=True)['status'] == 'PUBLISHED_TEST_REMOTE'
    rewrite(output, manifest, original)
    result = publish(output, remote, approved=True, canonical_root=root)
    assert result['status'] == 'PUBLISHED_TEST_REMOTE'
    assert result['remote_readback'] == 'PASS'
    assert publish(output, remote, approved=True, canonical_root=root)['status'] == 'NO_OP'


def test_self_consistent_forgery_fails_independent_source_rebuild(tmp_path):
    root, output, manifest = candidate(tmp_path)
    entry = next(iter(manifest['reports'].values()))
    path = output/entry['json']
    p = json.loads(path.read_bytes())
    row = p['noncounting_observations'][0]
    row['technical_detail'] = grounded_detail('A fabricated author result about LWE.', row['source_url'], row['source_topics'])
    p['public_generation_id'] = ''
    p['public_generation_id'] = sha(encoded(p))
    validate_public(p)  # self-consistency alone is deliberately insufficient
    jb, mb = encoded(p)+b'\n', render(p)
    path.write_bytes(jb); (output/entry['markdown']).write_bytes(mb)
    entry.update(json_sha256=sha(jb), markdown_sha256=sha(mb), public_generation_id=p['public_generation_id'])
    (output/'manifest.json').write_bytes(encoded(manifest)+b'\n')
    remote = str(bare(tmp_path))
    with pytest.raises(GateError, match='PUBLIC_SOURCE_REBIND_REQUIRED'):
        publish(output, remote, approved=True)
    with pytest.raises(GateError, match='PUBLIC_SOURCE_REBIND_MISMATCH'):
        publish(output, remote, approved=True, canonical_root=root)
