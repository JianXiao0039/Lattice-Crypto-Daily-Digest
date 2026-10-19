"""An official source relationship, never a name-only lattice whitelist."""
import json
from pathlib import Path
import pytest
from lattice_digest.scientific_scope import evaluate_scope
from lattice_digest.evidence_contract import source_scope_score
from lattice_digest.publication_events import build_event_ledger

SAVED=json.loads((Path(__file__).parent/'fixtures/mitaka_official_20261019.json').read_text(encoding='utf-8'))

def test_real_official_mitaka_implementation_is_qualified():
    row=SAVED['source_record']
    q=evaluate_scope(row)
    assert q['scientific_scope']=='LATTICE_RELEVANT_IMPLEMENTATION'
    assert q['lattice_relevance_qualified'] is True
    assert source_scope_score(row)[1]==90
    assert any(r['rule']=='primary-object-role-v1.1-explicit-variant-implementation'
               and r['qualifies_lattice_scope'] for r in q['source_relation_roles'])

@pytest.mark.parametrize('title,abstract',[
    ('Efficient implementation of an unnamed signature', 'The Mitaka signature scheme is a variant of Falcon (FN-DSA).'),
    ('Efficient Mitaka implementation', 'We compare Mitaka with Falcon (FN-DSA) as a baseline.'),
    ('Efficient Mitaka implementation', 'Mitaka is fast. Falcon (FN-DSA) is related work.'),
    ('Mitaka crystal lattice vibrations', 'The material has a crystal lattice and a spectroscopic signature.'),
    ('HQC implementation compared with Mitaka', 'The Mitaka signature scheme is a variant of Falcon (FN-DSA). We implement HQC.'),
    ('Efficient Mitaka implementation', 'The Mitaka signature scheme is a variant of Falcon (FN-DSA), but this work is not about cryptography.'),
])
def test_unowned_baseline_material_or_negative_relation_does_not_qualify(title,abstract):
    assert evaluate_scope({'title':title,'abstract':abstract,'source_url':SAVED['source_record']['source_url']})['lattice_relevance_qualified'] is False

def test_original_time_and_cross_day_identity_are_not_changed():
    row=SAVED['source_record']
    before={'target_date':'2026-10-17','coverage_start':'2026-10-15T21:00:00+08:00','coverage_end':'2026-10-17T09:00:00+08:00'}
    observed={'target_date':'2026-10-18','coverage_start':'2026-10-17T04:18:41+08:00','coverage_end':'2026-10-18T16:18:41+08:00'}
    assert build_event_ledger([row],before)['counts']['primary_new']==0
    assert build_event_ledger([row],observed)['counts']['primary_new']==1
    assert build_event_ledger([row],observed,[row])['counts']['primary_new']==0
