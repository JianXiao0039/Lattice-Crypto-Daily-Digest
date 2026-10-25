"""Source grounding, frozen history and privacy migration acceptance."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import pytest

from lattice_digest.public_technical import detail, check_detail, cards, PENDING
from lattice_digest.publication_events import scope_evaluator_for_policy, POLICY_VERSION, PREVIOUS_POLICY_VERSION
from lattice_digest.report_gate import verify, encoded, sha, GateError
from lattice_digest.public_report import project, render, export, inspect_tree, validate_public, index_bytes
from lattice_digest.public_publisher import publish
from tests.test_public_report_pipeline import canonical, bare


def rehash(p):
    p['public_generation_id']=sha(encoded(dict(p,public_generation_id='')))
    return p


def test_old_v2_evaluator_is_exact_frozen_source():
    p=Path(__file__).parents[1]/'src/lattice_digest/scientific_scope_v2.py'
    assert hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()=='16e617f95324249e8072337dacbb28c5f762591fe5526718c2b30fa9d0d62f07'


def test_generic_bootstrap_implementation_relation_and_frozen_compatibility():
    row=dict(title='Programmable Bootstrapping for Large Tables',
        abstract='Programmable bootstrapping in FHEW/TFHE evaluates a lookup table. '
                 'We present a new packing technique. In a TFHE-rs-based engine, the technique evaluates a large lookup table.',
        source_url='https://eprint.iacr.org/2026/1234')
    assert not scope_evaluator_for_policy(PREVIOUS_POLICY_VERSION)(row)['lattice_relevance_qualified']
    assert scope_evaluator_for_policy(POLICY_VERSION)(row)['lattice_relevance_qualified']
    for abstract in ['We compare against a TFHE implementation that evaluates tables.',
                     'A TFHE engine evaluates a lookup table in related work.',
                     'This does not apply to TFHE.']:
        changed={**row,'title':'General arithmetic circuits','abstract':abstract}
        assert not scope_evaluator_for_policy(POLICY_VERSION)(changed)['lattice_relevance_qualified']


def test_unknown_or_changed_abstract_is_pending_without_claim_transfer():
    d=detail('A changed abstract','https://eprint.iacr.org/2026/2618',['FHE'])
    assert d['status']==PENDING and d['result_zh']==PENDING
    assert check_detail(d,'https://eprint.iacr.org/2026/2618',['FHE'])==d


def test_reviewed_cards_have_conditions_and_no_unqualified_break_claims():
    cs=cards()
    assert len(cs)>=7
    reaction=next(c for c in cs.values() if c['source_url'].endswith('/2490'))
    assert '不破坏 RLWE' in reaction['assumptions_zh']
    sampling=next(c for c in cs.values() if c['source_url'].endswith('/2521'))
    assert '精确' in sampling['assumptions_zh']
    for digest,c in cs.items():
        d={k:v for k,v in c.items() if k!='source_url'}
        check_detail(dict(d,status='REVIEWED_PUBLIC_ABSTRACT',abstract_sha256=digest),c['source_url'],[])


@pytest.mark.parametrize('payload',['invented theorem','C:/Users/private/plan','<script>bad</script>',
                                  'private@example.test','x\u202ey'])
def test_v2_arbitrary_technical_claim_or_private_injection_fails(canonical,payload):
    p=project(verify(canonical,'daily','2026-09-22'))
    p['papers'][0]['technical_detail']['result_zh']=payload
    with pytest.raises(GateError):validate_public(rehash(p))


def test_public_clock_is_deterministic_and_never_guesses_scheduler(canonical):
    pair=verify(canonical,'daily','2026-09-22')
    pair.payload['metadata']['source_query_runtime']=[dict(started_at='2026-09-22T10:00:00Z',finished_at='2026-09-22T10:01:00Z')]
    p=project(pair)
    assert p['temporal_evidence']['scheduler_event_time']=='UNKNOWN'
    assert p['temporal_evidence']['actual_collection_end']=='2026-09-22T10:01:00+00:00'
    assert render(p)==render(json.loads(encoded(p)))
    p['temporal_evidence']['mailbox_id']='PRIVATE'
    with pytest.raises(GateError):validate_public(rehash(p))


def test_frozen_v1_readability_and_current_v2_are_both_valid(canonical):
    pair=verify(canonical,'daily','2026-09-22')
    v1=project(pair,readable_version=1);v2=project(pair)
    assert '<!-- public-readable-v1 -->'.encode() in render(v1)
    assert v1['event_count']==v2['event_count']
    assert v1['canonical_pair_sha256']==v2['canonical_pair_sha256']
    assert v2['papers'][0]['technical_detail']['status'] in (PENDING,'REVIEWED_PUBLIC_ABSTRACT')


def write_v1(pair,out):
    # Construct a genuine deterministic legacy tree using its frozen schema.
    p=project(pair,readable_version=1);k='daily:2026-09-22'
    j='daily/2026/2026-09-22.json';m='daily/2026/2026-09-22.md'
    (out/Path(j).parent).mkdir(parents=True)
    jb=encoded(p)+b'\n';mb=render(p)
    (out/j).write_bytes(jb);(out/m).write_bytes(mb)
    manifest=dict(schema_version='public-manifest-v1',reports={k:dict(json=j,markdown=m,json_sha256=sha(jb),
        markdown_sha256=sha(mb),quality=p['quality'],public_generation_id=p['public_generation_id'])})
    (out/'manifest.json').write_bytes(encoded(manifest)+b'\n');(out/'index.md').write_bytes(index_bytes(manifest))
    inspect_tree(out)


def test_reviewed_readability_promotion_noop_and_frozen_event_hash_boundary(canonical,tmp_path):
    pair=verify(canonical,'daily','2026-09-22');old=tmp_path/'old';write_v1(pair,old)
    remote=bare(tmp_path);a=publish(old,remote,approved=True)
    new=tmp_path/'new';export(canonical,'daily','2026-09-22',new)
    import shutil
    bad=tmp_path/'bad';shutil.copytree(new,bad)
    manifest=json.loads((bad/'manifest.json').read_bytes());entry=manifest['reports']['daily:2026-09-22']
    p=json.loads((bad/entry['json']).read_bytes());p['papers'][0]['authors']=['Unexpected Author']
    rehash(p);jb=encoded(p)+b'\n';mb=render(p)
    (bad/entry['json']).write_bytes(jb);(bad/entry['markdown']).write_bytes(mb)
    entry.update(json_sha256=sha(jb),markdown_sha256=sha(mb),public_generation_id=p['public_generation_id'])
    (bad/'manifest.json').write_bytes(encoded(manifest)+b'\n')
    inspect_tree(bad)
    with pytest.raises(GateError,match='same-authority'):publish(bad,remote,approved=True)
    b=publish(new,remote,approved=True)
    assert b['commit']!=a['commit'] and b['remote_readback']=='PASS'
    assert publish(new,remote,approved=True)['status']=='NO_OP'
    history=subprocess.check_output(['git','--git-dir',remote,'rev-list','--count','public-digests']).strip()
    assert history==b'2'
    with pytest.raises(GateError):publish(old,remote,approved=True)
