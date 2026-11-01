import hashlib
import json
from pathlib import Path

import pytest

from lattice_digest.scientific_scope import evaluate_scope as frozen_scope
from lattice_digest.scientific_scope_v44 import evaluate_scope


FIXTURES = json.loads((Path(__file__).parent / 'fixtures/v44_scope.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('row', FIXTURES, ids=lambda row: row['paper_id'])
def test_official_abstract_scope(row):
    assert hashlib.sha256(row['abstract'].encode()).hexdigest() == row['abstract_sha256']
    assert evaluate_scope(row)['lattice_relevance_qualified'] is row['expected_qualified']


def test_historical_publication_scope_is_frozen():
    row = next(row for row in FIXTURES if row['paper_id'] == 'arxiv:2610.30383')
    assert frozen_scope(row)['scientific_scope'] == 'GENERAL_CRYPTO_BACKGROUND'
    assert evaluate_scope(row)['scientific_scope'] == 'LATTICE_RELEVANT_IMPLEMENTATION'


@pytest.mark.parametrize('title,abstract', [
    ('SIMD Keccak for video processing', 'We evaluate ML-KEM only as an unrelated comparison baseline. ML-KEM speedups are not our research contribution.'),
    ('Structured hints for code theory', 'We illustrate structured leakage in ring and module lattice implementations only as unrelated background. LWE is a baseline; our result concerns linear codes.'),
])
def test_new_scope_rules_cannot_promote_baseline_or_background(title, abstract):
    assert not evaluate_scope({'title':title, 'abstract':abstract})['lattice_relevance_qualified']


@pytest.mark.parametrize('abstract', [
    'ML-KEM computes forward NTT on secret polynomials only as a comparison baseline.',
    'This chip computes NTT over public image data. ML-KEM is unrelated.',
    'A blog alleges key recovery; no verified primitive relation is provided.',
])
def test_ntt_title_alone_does_not_establish_scope(abstract):
    row = {'title': 'Twiddle Faults on the Forward NTT', 'abstract': abstract,
           'source_url': 'https://example.invalid/TEST_ONLY'}
    assert not evaluate_scope(row)['lattice_relevance_qualified']
