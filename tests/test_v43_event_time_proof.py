"""TEST_ONLY time variants of a bound source canary, no historical claims."""
from copy import deepcopy
from datetime import date
import json
import pytest
from lattice_digest.models import make_paper_record
from lattice_digest.evidence_contract import bind_source_evidence
from lattice_digest.storage import publish_daily_pair
from lattice_digest.report_gate import verify, GateError
from tests.test_public_report_pipeline import CANARIES, META, DAY
from tests.test_nested_public_e2e import health
from tests.v41_history_fixture import seed_empty_history


@pytest.mark.parametrize('source_time,expected', [
    ('2026-09-22', 'EVENT_TIME_PRECISION_UNPROVEN'),
    ('2026-09-22T00:30:00', 'EVENT_TIME_PRECISION_UNPROVEN'),
    ('2026-09-22T08:00:00+08:00', 'COUNTED'),
    ('2026-09-22T12:00:00+08:00', 'NOT_COUNTED'),
])
def test_counted_event_requires_source_cutoff_and_timezone_proof(tmp_path, source_time, expected):
    root = tmp_path/'canonical'
    seed_empty_history(root, DAY)
    source = deepcopy(CANARIES[0]['source_record'])
    source.update(publication_date='2026-09-22', publication_timestamp=source_time,
                  preprint_first_posted_at=None,
                  announcement_date=None, update_date=None, update_timestamp=None,
                  source_version_timestamp=None)
    record = bind_source_evidence(make_paper_record(**source))
    jp, mp = publish_daily_pair([record],root,DAY,source_health=health(degraded=True),
        metadata={**META,'fixture_evidence':'TEST_ONLY_MODIFIED_SOURCE_TIME_NOT_REAL_PUBLICATION'})
    original = jp.read_bytes(), mp.read_bytes()
    if expected.startswith('EVENT_'):
        with pytest.raises(GateError) as failure:verify(root,'daily',str(DAY))
        assert failure.value.code == expected
        assert json.loads(original[0])['publication_event_ledger']['counts']['primary_new'] == 1
    else:
        pair = verify(root,'daily',str(DAY))
        assert len(pair.events) == (1 if expected == 'COUNTED' else 0)
    assert (jp.read_bytes(), mp.read_bytes()) == original
