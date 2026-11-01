"""TEST_ONLY mechanism checks; source content uses frozen official fixtures."""
from copy import deepcopy
import pytest
from lattice_digest.public_technical import grounded_detail, check_detail
from lattice_digest.public_report import project, validate_public, render
from lattice_digest.report_gate import verify, encoded, sha, GateError
from tests.test_public_report_pipeline import canonical, DAY


def test_abstract_extraction_is_literal_bounded_and_e2():
    abstract = 'We study fully homomorphic encryption. ' * 40
    card = grounded_detail(abstract, 'https://eprint.iacr.org/2026/1', ['FHE'])
    assert card['evidence_level'] == 'E2'
    assert card['source_excerpt'] in ' '.join(abstract.split())
    assert len(card['source_excerpt']) <= 500
    assert check_detail(card, 'https://eprint.iacr.org/2026/1', ['FHE']) == card
    for key, value in [('evidence_level', 'E3'), ('result_zh', 'ML-KEM is broken'),
                       ('method_zh', 'An independently proved attack')]:
        altered = dict(card, **{key: value})
        with pytest.raises(ValueError):
            check_detail(altered, 'https://eprint.iacr.org/2026/1', ['FHE'])


def test_historical_primary_source_radar_does_not_create_publication(canonical):
    pair = verify(canonical, 'daily', str(DAY))
    # TEST_ONLY: force an already-bound row into non-event display. It does not
    # create any new source date or imply a real historical acceptance.
    pair.events.clear()
    p = project(pair)
    assert p['event_count'] == 0 and p['entry_count'] == 0 and p['papers'] == []
    assert len(p['noncounting_observations']) == 1
    assert p['noncounting_observations'][0]['technical_detail']['evidence_level'] == 'E2'
    assert '不增加发表事件数' in render(p).decode()
    changed = deepcopy(p)
    changed['noncounting_observations'][0]['technical_detail']['result_zh'] = 'Unsupported'
    changed['public_generation_id'] = ''
    changed['public_generation_id'] = sha(encoded(changed))
    with pytest.raises(GateError):
        validate_public(changed)


def test_private_or_secondary_source_does_not_enter_radar(canonical):
    pair = verify(canonical, 'daily', str(DAY))
    pair.events.clear()
    pair.source_rows[0]['source'] = 'gmail'
    assert project(pair)['noncounting_observations'] == []
    pair.source_rows[0]['source'] = 'openalex'
    assert project(pair)['noncounting_observations'] == []


@pytest.mark.parametrize('change', [
    {'arxiv_id': '2610.11111', 'source_url': 'https://arxiv.org/abs/2610.22222', 'source': 'arxiv'},
    {'arxiv_id': '2610.11111v1', 'source_url': 'https://arxiv.org/abs/2610.11111v2', 'source': 'arxiv'},
    {'source_url': 'https://eprint.iacr.org/2026/2137?private=canary'},
])
def test_radar_conflicted_identity_is_verify_first(canonical, change):
    pair = verify(canonical, 'daily', str(DAY))
    pair.events.clear()
    pair.source_rows[0].update(change)
    assert project(pair)['noncounting_observations'] == []


def test_optional_unsafe_radar_does_not_hide_unrelated_safe_observation(canonical):
    pair = verify(canonical, 'daily', str(DAY))
    pair.events.clear()
    bad = deepcopy(pair.source_rows[0])
    bad.update(paper_id='iacr:2026/9999', eprint_id='2026/9999', doi=None,
               source_url='https://eprint.iacr.org/2026/9999',
               abstract=bad['abstract']+' private@example.test')
    pair.source_rows.append(bad)
    p = project(pair)
    assert len(p['noncounting_observations']) == 1
    assert 'private@example.test' not in render(p).decode()


def test_cloud_public_only_contract_cannot_emit_unrebindable_excerpts(canonical):
    pair = verify(canonical, 'daily', str(DAY))
    pair.events.clear()
    pair.payload['metadata']['collector'] = 'github_actions'
    assert project(pair)['noncounting_observations'] == []
