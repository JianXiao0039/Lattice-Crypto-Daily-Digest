"""Real public generation in disposable nested checkouts; source transport is synthetic."""
from datetime import date, timedelta
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest
from tests.test_runtime_isolation_v2 import published_repo, nested_repo, invoke
from lattice_digest.artifact_paths import daily_data_path, daily_digest_path, weekly_data_path, weekly_digest_path
from lattice_digest.authority import configured_sources, semantic_qa, derive_authority
from lattice_digest.evidence_contract import bind_source_evidence
from lattice_digest.models import make_paper_record, PaperRecord
from lattice_digest.digest import generate_markdown
from lattice_digest.storage import publish_daily_pair


def row(day, version='v1', **changes):
    return dict(title='Synthetic Module-SIS chameleon hash construction',
        abstract='We construct a chameleon hash from Module-SIS with a lattice trapdoor.',
        source='arxiv',source_url=f'https://arxiv.org/abs/2512.99999{version}',
        arxiv_id=f'2512.99999{version}',publication_date=str(day),
        publication_timestamp=f'{day}T00:00:00Z') | changes


def health(degraded=False):
    return [dict(source=s['name'],health_status='yellow' if degraded else 'green',
        runtime_state='partial' if degraded else 'complete',query_groups_total=1,
        query_groups_success=0 if degraded else 1,query_groups_failed=1 if degraded else 0)
        for s in configured_sources() if s.get('enabled')]


def generate_daily(root, canonical, day, rows, degraded=False):
    from tests.v41_history_fixture import seed_empty_history
    seed_empty_history(canonical, day)
    # Only the discovery transport is replaced. Public preflight, live Git
    # authority, ranking, freshness, publication, SQLite and QA actually execute.
    script = f'''
import json, sys
from lattice_digest import run
from lattice_digest.models import make_paper_record
from lattice_digest.public_daily import main
rows = json.loads({json.dumps(rows)!r})
def collect(configs, context):
    for config in configs:
        context.register_source(config)
        item = context.health(config['name'])
        item.runtime_state = {'partial' if degraded else 'complete'!r}
        item.query_groups_total = 1
        item.query_groups_success = {0 if degraded else 1}
        item.query_groups_failed = {1 if degraded else 0}
    return [make_paper_record(**item) for item in rows]
run._collect_records = collect
sys.exit(main(['--target-date',{str(day)!r},'--since','36h','--output','markdown,json','--send','none']))
'''
    env = dict(os.environ,PYTHONPATH=str(root/'src'),PYTHONDONTWRITEBYTECODE='1',
               LATTICE_DIGEST_CANONICAL_ROOT=str(canonical))
    result = subprocess.run([os.environ.get('LATTICE_DIGEST_TEST_PUBLIC_PYTHON', sys.executable),
                            '-c',script],cwd=root,env=env,
                            capture_output=True,text=True,encoding='utf-8')
    assert result.returncode == 0, result.stdout + result.stderr
    path = daily_data_path(day,canonical/'data')
    payload = json.loads(path.read_text(encoding='utf-8'))
    md = daily_digest_path(day,canonical/'digests').read_text(encoding='utf-8')
    assert semantic_qa(payload,md)['status'] == 'PASS'
    assert payload['metadata']['runtime_paths']['canonical_root'] == str(canonical)
    assert (canonical/'papers.db').is_file()
    assert not (root/'papers.db').exists()
    return payload, md


def test_public_daily_real_generation_revision_duplicate_and_negative_control(nested_repo):
    root, canonical, _ = nested_repo
    day = date(2025,12,29)
    new = row(day)
    payload, _ = generate_daily(root,canonical,day,[new])
    assert payload['metadata']['selection_counts']['primary_new'] == 1
    day += timedelta(days=1)
    revision = row('2025-12-29','v2',update_timestamp=f'{day}T00:00:00Z',update_date=str(day),
        abstract=new['abstract']+' We add a new collision adaptation bound.')
    payload, _ = generate_daily(root,canonical,day,[revision])
    assert payload['metadata']['selection_counts']['selected'] == 1
    assert len(payload['publication_event_ledger']['collections']['revision_events']) == 1
    day += timedelta(days=1)
    negative = row(day,arxiv_id='2512.99998v1',source_url='https://arxiv.org/abs/2512.99998v1',
        title='Synthetic HQC comparison',abstract='We implement HQC and compare with ML-KEM.')
    payload, md = generate_daily(root,canonical,day,[revision,negative],degraded=True)
    assert payload['metadata']['selection_counts']['selected'] == 0
    assert payload['metadata']['authority_state'] == 'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'
    assert 'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS' in md
    hqc = [item for item in payload['records'] if item['title'] == negative['title']]
    assert len(hqc) == 1
    assert not hqc[0]['lattice_relevance_qualified']


@pytest.mark.parametrize('has_paper,expected', [
    (True, 'AUTHORITATIVE_DEGRADED'), (False, 'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS')])
def test_public_daily_degraded_generation_is_conservative(nested_repo, has_paper, expected):
    root, canonical, _ = nested_repo
    day = date(2025, 12, 29)
    payload, md = generate_daily(root, canonical, day, [row(day)] if has_paper else [], degraded=True)
    assert payload['metadata']['authority_state'] == expected
    assert payload['metadata']['selection_counts']['primary_new'] == int(has_paper)
    assert expected in md


def test_public_daily_frozen_real_lwe_source_snapshot(nested_repo):
    root, canonical, _ = nested_repo
    fixtures = json.loads((Path(__file__).parent/'fixtures/scientific_publication_p0_canaries.json')
                          .read_text(encoding='utf-8'))
    frozen = next(item for item in fixtures if item['source_record']['eprint_id'] == '2026/2261')
    # Actual saved source fields and original publication date; no live provider claim.
    source = frozen['source_record']
    payload, md = generate_daily(root, canonical, date.fromisoformat(source['publication_date']), [source])
    assert payload['metadata']['selection_counts']['primary_new'] == 1
    assert payload['records'][0]['source_url'] == source['source_url']
    assert source['title'] in md
    assert payload['records'][0]['lattice_relevance_qualified']


def seed_days(canonical, start, days, degraded_day=None, overlap=False, legacy_days=0):
    from tests.v41_history_fixture import seed_empty_history
    seed_empty_history(canonical, start)
    code = canonical / '.ops/runtime/published'
    runtime = {}
    if code.is_dir():
        preflight = invoke(code, canonical, 'lattice_digest.public_daily', ['--preflight','--since','36h'])
        assert preflight.returncode == 0, preflight.stdout + preflight.stderr
        runtime = json.loads(preflight.stdout)['runtime_provenance']
    first = row(start)
    for index in range(days):
        day = start + timedelta(days=index)
        records = [bind_source_evidence(make_paper_record(**first))] if index == 0 or overlap else []
        jp, mp = publish_daily_pair(records,canonical,day,source_health=health(index==degraded_day),
            metadata={**runtime,'target_date':str(day),'quality_status':'authoritative',
                      'collector':'local_codex','run_mode':'daily',
                      'coverage_start':f'{day-timedelta(days=1)}T00:00:00+08:00',
                      'coverage_end':f'{day}T23:59:59+08:00'})
        if index < legacy_days:
            # Exercise the supported pre-P0 schema using its real legacy renderer
            # and independently computed QA, never a forged stored PASS.
            payload = json.loads(jp.read_text(encoding='utf-8'))
            metadata = payload['metadata']
            metadata.pop('publication_policy_version')
            payload.pop('publication_event_ledger')
            for record in payload['records']:
                for field in ('publication_event_type', 'publication_event_id'):
                    record.pop(field, None)
            metadata.update(derive_authority(payload['records'], payload['source_health'],
                                            promotion_history=metadata.get('promotion_history')))
            metadata.pop('markdown_sha256', None)
            metadata.pop('semantic_qa', None)
            md = generate_markdown([PaperRecord(**{key:value for key,value in record.items()
                                    if key in PaperRecord.model_fields}) for record in payload['records']], day,
                                   source_health=payload['source_health'], metadata=metadata)
            md += f"\n<!-- generation:{metadata['generation_id']} -->\n"
            qa = semantic_qa(payload, md, candidate=True)
            assert qa['status'] == 'PASS', qa
            metadata['semantic_qa'] = {key:value for key,value in qa.items() if key != 'derived_authority'}
            metadata['markdown_sha256'] = hashlib.sha256(md.encode('utf-8')).hexdigest()
            jp.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            mp.write_bytes(md.encode('utf-8'))
            assert semantic_qa(payload, md)['status'] == 'PASS'


@pytest.mark.parametrize('days,degraded,expected', [
    (7,None,'AUTHORITATIVE_COMPLETE'),(5,None,'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'),
    (7,3,'AUTHORITATIVE_DEGRADED')])
def test_public_weekly_full_generation_iso_boundary_and_qa(nested_repo,days,degraded,expected):
    root, canonical, _ = nested_repo
    start, end = date(2025,12,29), date(2026,1,4)
    seed_days(canonical,start,days,degraded,overlap=True)
    result = invoke(root,canonical,'lattice_digest.public_weekly',
                    ['--from-date',str(start),'--to-date',str(end)])
    assert result.returncode == 0, result.stdout + result.stderr
    jp = weekly_data_path(2026, 1, canonical/'data')
    mp = weekly_digest_path(2026, 1, canonical/'digests')
    payload = json.loads(jp.read_text(encoding='utf-8')); md = mp.read_text(encoding='utf-8')
    assert payload['week_id'] == '2026-W01'
    assert payload['coverage']['authority_state'] == expected
    assert len(payload['coverage']['loaded_days']) == days
    assert payload['coverage']['unique_records'] == 1
    assert payload['publication_event_views']['counts']['primary_publication_events'] == 1
    assert expected in md and '2026-W01' in md and first_title() in md
    assert len(payload['coverage']['semantically_valid_days']) == days


def first_title():
    return row('2025-12-29')['title']


@pytest.mark.parametrize('legacy_days', [7, 3])
def test_public_weekly_legacy_and_mixed_inputs_do_not_inflate_events(nested_repo, legacy_days):
    root, canonical, _ = nested_repo
    start = date(2025, 12, 29)
    seed_days(canonical, start, 7, overlap=True, legacy_days=legacy_days)
    result = invoke(root, canonical, 'lattice_digest.public_weekly',
                    ['--from-date', str(start), '--to-date', '2026-01-04'])
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(weekly_data_path(2026, 1, canonical/'data').read_text(encoding='utf-8'))
    assert payload['coverage']['unique_records'] == 1
    assert payload['publication_event_views']['counts']['primary_publication_events'] == 1
    assert len(payload['coverage']['semantically_valid_days']) == 7


@pytest.mark.parametrize('days,degraded,expected', [
    (31,None,'AUTHORITATIVE_COMPLETE'),(5,None,'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'),
    (31,3,'AUTHORITATIVE_DEGRADED')])
def test_public_monthly_full_generation_and_authorized_downstream(nested_repo,days,degraded,expected):
    root, canonical, _ = nested_repo
    seed_days(canonical,date(2025,12,1),days,degraded,overlap=True)
    result = invoke(root,canonical,'lattice_digest.public_monthly',['--month','2025-12','--exports','--obsidian'])
    assert result.returncode == 0, result.stdout + result.stderr
    jp=canonical/'data/2025/monthly/2025-12.json';mp=canonical/'digests/2025/monthly/2025-12.md'
    payload=json.loads(jp.read_text(encoding='utf-8'));md=mp.read_text(encoding='utf-8')
    assert payload['input_quality']['authority_state'] == expected
    assert len(payload['input_daily_files']) == days
    assert payload['total_unique_records'] == 1
    assert payload['publication_event_views']['counts']['primary_publication_events'] == 1
    assert len(payload['input_quality']['semantically_valid_days']) == days
    assert expected in md and first_title() in md
    assert (canonical/'state/reading-queue.json').is_file()
    assert list((canonical/'exports/obsidian-paper-notes/Papers').glob('*.md'))
    assert not (root/'exports').exists()
    if days == 31 and degraded is None:
        # The optional production profiles pass the same independent gate;
        # an unreviewed profile must still fail even with a valid payload hash.
        from lattice_digest.report_gate import verify, GateError, sha, encoded
        original = jp.read_bytes()
        try:
            for profile in ('MONTHLY', 'MONTHLY_EXPORTS', 'MONTHLY_OBSIDIAN', 'UNKNOWN_PROFILE'):
                payload['metadata']['runtime_command_profile'] = profile
                payload['metadata'].pop('payload_content_sha256')
                payload['metadata']['payload_content_sha256'] = sha(encoded(payload))
                jp.write_bytes(encoded(payload))
                if profile == 'UNKNOWN_PROFILE':
                    with pytest.raises(GateError) as rejected:
                        verify(canonical, 'monthly', '2025-12')
                    assert rejected.value.code == 'RUNTIME_MODE_INVALID'
                else:
                    verify(canonical, 'monthly', '2025-12')
        finally:
            jp.write_bytes(original)


def test_public_monthly_mixed_inputs_and_weekly_context_never_double_count(nested_repo):
    root, canonical, _ = nested_repo
    start = date(2025, 12, 1)
    seed_days(canonical, start, 31, overlap=True, legacy_days=5)
    weekly = invoke(root, canonical, 'lattice_digest.public_weekly',
                    ['--from-date', str(start), '--to-date', '2025-12-07'])
    assert weekly.returncode == 0, weekly.stdout + weekly.stderr
    result = invoke(root, canonical, 'lattice_digest.public_monthly', ['--month', '2025-12'])
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads((canonical/'data/2025/monthly/2025-12.json').read_text(encoding='utf-8'))
    assert payload['total_unique_records'] == 1
    assert payload['publication_event_views']['counts']['primary_publication_events'] == 1
    assert len(payload['input_quality']['semantically_valid_days']) == 31
