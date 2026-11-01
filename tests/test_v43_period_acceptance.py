"""Semantic QA does not authorize independent period event ownership."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path

import pytest

from lattice_digest.daily_inputs import PERIOD_INPUT_POLICY_V43
from lattice_digest.publication_events import period_views, period_evidence_caveat
from lattice_digest.weekly_synthesis import build_weekly_synthesis, render_markdown as weekly_markdown
from lattice_digest.monthly_synthesis import build_monthly_synthesis, render_markdown as monthly_markdown


def oct27():
    p = json.loads((Path(__file__).parent/'fixtures/v43_oct27_period_candidates.json').read_bytes())
    assert p['canonical_sha256'] == '54032b2b1661d81674f92fbbd2a377f5bd401b87ac9e06fd3da20e2c6b4b27e8'
    assert any(r['doi'] == '10.21203/rs.3.rs-11270790/v1' for r in p['records'])
    p['_daily_input_quality'] = {'semantic_status':'PASS', 'assessment_policy': PERIOD_INPUT_POLICY_V43,
                                 'independent_acceptance':'UNKNOWN_NOT_EVALUATED'}
    return p


def test_real_oct27_failed_candidate_never_gains_v43_verified_count():
    p = oct27(); before = deepcopy(p)
    frozen = period_views([(date(2026,10,27),p)])
    new = period_views([(date(2026,10,27),p)], assessment_policy=PERIOD_INPUT_POLICY_V43)
    assert new['collections'] == frozen['collections']
    assert new['counts'] == frozen['counts']
    assert new['evidence_provenance']['verified_current_schema_event_count'] == 0
    assert new['evidence_provenance']['pending_independent_event_candidate_count'] == 4
    assert new['evidence_provenance']['input_evidence_tiers'][0]['evidence_tier'] == 'SEMANTICALLY_VALID_EVENT_CANDIDATE'
    assert '待独立验收候选 4' in period_evidence_caveat(new)
    assert p == before
    # The frozen v1 evaluator retains its deployed byte-equivalent projection.
    assert frozen['evidence_provenance']['policy_version'] == 'period-event-evidence-v1'
    assert frozen['evidence_provenance']['verified_current_schema_event_count'] == 4


def test_v43_preserves_cross_day_identity_conflicts():
    first = oct27(); second = deepcopy(first)
    for rows in second['publication_event_ledger']['collections'].values():
        for e in rows: e['event_id'] += '-conflicting-next-day'
    loaded = [(date(2026,10,27),first),(date(2026,10,28),second)]
    old = period_views(loaded)
    new = period_views(loaded, assessment_policy=PERIOD_INPUT_POLICY_V43)
    assert old['ownership_conflicts'] and new['ownership_conflicts'] == old['ownership_conflicts']
    assert new['collections'] == old['collections']
    assert new['evidence_provenance']['verified_current_schema_event_count'] == 0


@pytest.mark.parametrize('kind',['weekly','monthly'])
def test_new_period_policy_is_explicit_and_old_default_frozen(tmp_path, kind):
    if kind == 'weekly':
        build = lambda **kw: build_weekly_synthesis(tmp_path/'data',date(2026,10,26),date(2026,11,1),**kw)
        render = weekly_markdown
    else:
        build = lambda **kw: build_monthly_synthesis(tmp_path/'data','2026-10',**kw)
        render = monthly_markdown
    old = build(); new = build(assessment_policy=PERIOD_INPUT_POLICY_V43)
    assert 'period_input_policy' not in old.get('metadata',{})
    assert new['metadata']['period_input_policy'] == PERIOD_INPUT_POLICY_V43
    assert new['publication_event_views']['evidence_provenance']['verified_current_schema_event_count'] == 0
    assert new['publication_event_views']['evidence_provenance']['internal_counts_authorization'] == 'PENDING_INDEPENDENT_REPORT_GATE'
    assert '待独立验收候选 0' in render(new)


def test_unknown_period_assessment_rejected(tmp_path):
    with pytest.raises(ValueError,match='UNSUPPORTED_PERIOD_INPUT_POLICY'):
        period_views([],assessment_policy='unreviewed')
