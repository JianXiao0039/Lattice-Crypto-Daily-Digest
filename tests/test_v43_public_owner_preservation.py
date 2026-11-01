"""Authority ordering must not delete an accepted scientific event."""
import json
import subprocess
from pathlib import Path
import pytest
from lattice_digest.public_report import export, inspect_tree, validate_public, render, index_bytes
from lattice_digest.public_publisher import publish
from lattice_digest.report_gate import encoded, sha, GateError
from tests.test_public_report_pipeline import canonical, DAY, bare, publisher_tier_fixture

@pytest.mark.parametrize('mutation', ['remove', 'rewrite_event_id'])
def test_higher_authority_cannot_rewrite_counted_history(canonical, tmp_path, mutation):
    old = tmp_path/'published'; new = tmp_path/'replacement'
    export(canonical,'daily',str(DAY),old)
    export(canonical,'daily',str(DAY),new)
    publisher_tier_fixture(old,'PROVISIONAL_PUBLIC')
    remote=bare(tmp_path)
    first=publish(old,remote,approved=True)
    manifest,files=inspect_tree(new)
    key,entry=next(iter(manifest['reports'].items()))
    report=json.loads(files[entry['json']])
    assert report['event_count'] > 0
    if mutation=='remove':
        report.update(papers=[],event_count=0,entry_count=0,historical_candidate_count=0,omitted_event_count=0)
    else:
        report['papers'][0]['event_id']='0'*64
    # TEST_ONLY adversarial public-schema-valid candidate; no scientific gate
    # has authorized the removal. Publisher must preserve the earlier owner.
    report['public_generation_id']=''; report['public_generation_id']=sha(encoded(report))
    report=validate_public(report)
    jb=encoded(report)+b'\n'; mb=render(report)
    (new/entry['json']).write_bytes(jb);(new/entry['markdown']).write_bytes(mb)
    entry.update(json_sha256=sha(jb),markdown_sha256=sha(mb),public_generation_id=report['public_generation_id'])
    (new/'manifest.json').write_bytes(encoded(manifest)+b'\n');(new/'index.md').write_bytes(index_bytes(manifest))
    inspect_tree(new)
    with pytest.raises(GateError) as failure: publish(new,remote,approved=True)
    assert failure.value.code=='EVENT_HISTORY_REWRITE_REQUIRES_REVIEW'
    current=subprocess.check_output(['git','--git-dir',remote,'rev-parse','public-digests'],text=True).strip()
    assert current==first['commit']
