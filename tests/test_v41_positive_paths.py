"""Source-backed controls with explicitly simulated complete history transport.

The complete test history is not a claim that production October 17 was observed.
The original forensic recovery remains blocked.
"""
from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
import shutil

import pytest

from lattice_digest.models import PaperRecord
from lattice_digest.publication_events import period_views
from lattice_digest.promotion_history import apply_promotion_history
from lattice_digest.storage import publish_daily_pair
from lattice_digest.public_report import export, inspect_tree
from lattice_digest.report_gate import verify, encoded
from tests.test_nested_public_e2e import health
from tests.v41_history_fixture import seed_empty_history

ORIGINAL=Path(os.environ.get('V41_ORIGINAL_ROOT', str(Path(__file__).resolve().parents[4])))


def test_cloud_zero_new_export_when_duplicate_owned_and_history_explicitly_complete(tmp_path):
    day=date(2026,10,27)
    original=ORIGINAL/'data/2026/daily/2026-10-26.json'
    if not original.is_file():pytest.skip('preserved incident input unavailable')
    prior=json.loads(original.read_bytes())
    row=next(r for r in prior['records'] if r.get('doi')=='10.21203/rs.3.rs-11270790/v1')
    record=PaperRecord.model_validate({k:v for k,v in row.items() if k in PaperRecord.model_fields})
    record=apply_promotion_history([record],prior['records'])[0]
    root=tmp_path/'canonical'
    seed_empty_history(root,day)
    for kind,extension in [('data','json'),('digests','md')]:
        path=Path(kind)/'2026/daily'/('2026-10-26.'+extension)
        shutil.copyfile(ORIGINAL/path,root/path)
    metadata={'target_date':str(day),'collector':'github_actions','quality_status':'provisional','run_mode':'daily',
        'coverage_start':'2026-10-25T13:17:00+00:00','coverage_end':'2026-10-27T01:17:00+00:00',
        'test_evidence':'SOURCE_BACKED_ROW_WITH_SIMULATED_COMPLETE_HISTORY_NOT_PRODUCTION_REPLAY'}
    publish_daily_pair([record],root,day,source_health=health(degraded=True),metadata=metadata)
    pair=verify(root,'daily',str(day))
    assert pair.payload['metadata']['promotion_history']['complete'] is True
    assert pair.payload['publication_event_ledger']['counts']['event_count']==0
    export(root,'daily',str(day),tmp_path/'public')
    manifest,files=inspect_tree(tmp_path/'public')
    public=json.loads(files['daily/2026/2026-10-27.json'])
    assert public['quality']=='PROVISIONAL_PUBLIC' and public['event_count']==0
    assert public['source_coverage_state']=='INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'
    assert '今日未发现值得记录的格密码相关新论文。'.encode() not in files['daily/2026/2026-10-27.md']
    assert b'runtime_paths' not in b''.join(files.values())


def test_periods_deduplicate_identity_even_if_a_bad_daily_changes_event_id():
    fixture=Path(__file__).parent/'fixtures/v41_cloud_public'
    public=json.loads((fixture/'public26/daily/2026/2026-10-26.json').read_bytes())
    paper=public['papers'][0]
    entry={'canonical_identity':paper['public_canonical_id'],'row_index':0,'event_id':paper['event_id']}
    payload={'metadata':{'publication_policy_version':'scientific-publication-v4-v3'},
        '_daily_input_quality':{'semantic_status':'PASS'},'records':[{'source_url':paper['source_url']}],
        'publication_event_ledger':{'collections':{'primary_publication_events':[entry]}}}
    bad=deepcopy(payload)
    bad['publication_event_ledger']['collections']['primary_publication_events'][0]['event_id']='a'*64
    views=period_views([(date(2026,10,26),payload),(date(2026,10,27),bad)])
    assert views['counts']['primary_publication_events']==1
    assert views['evidence_provenance']['verified_current_schema_event_count']==1
    assert views['ownership_conflicts']==[{'input_date':'2026-10-27','owner_date':'2026-10-26',
        'event_id':'a'*64,'code':'EVENT_OWNERSHIP_CONFLICT'}]
