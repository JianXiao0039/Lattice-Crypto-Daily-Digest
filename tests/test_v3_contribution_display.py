"""Independent display tests: no score/identity or scientific-claim upgrades."""
from copy import deepcopy
from datetime import date
import hashlib

import pytest

from lattice_digest.authority import semantic_qa
from lattice_digest.evidence_contract import bind_source_evidence
from lattice_digest.models import make_paper_record
from lattice_digest.scientific_contribution import Contribution, VERSION, abstract_guide, contribution_view, role_summary
from lattice_digest.scientific_daily import render_scientific_daily
from lattice_digest.storage import build_daily_payload


def row(title, abstract):
    return {'title': title, 'abstract': abstract, 'source': 'iacr_eprint',
            'source_url': 'https://eprint.iacr.org/2026/9999',
            'publication_timestamp': '2026-10-18T00:00:00Z'}


@pytest.mark.parametrize('title,abstract,expected', [
    ('Hardness of hinted ISIS from lattice problems', 'We prove a lattice hardness reduction.', 'LATTICE_FOUNDATIONS'),
    ('Polynomial-space SVP algorithms', 'We give an SVP algorithm in polynomial space.', 'LATTICE_ALGORITHMS'),
    ('FFT dual attack on Module-LWE', 'We analyze a dual attack on Module-LWE.', 'LATTICE_CRYPTANALYSIS'),
    ('Lattice-based polynomial commitment scheme', 'We construct a polynomial commitment scheme for lattice cryptography under Module-SIS.', 'LATTICE_PRIMITIVES'),
    ('Fixed-point implementation of Falcon', 'We implement Falcon signatures with fixed-point arithmetic.', 'LATTICE_IMPLEMENTATIONS'),
    ('ML-KEM device binding application', 'We use ML-KEM in a device binding protocol.', 'LATTICE_APPLICATIONS'),
    ('SoK: Post-quantum signature aggregation', 'We compare Falcon, ML-DSA and non-lattice signatures.', 'ADJACENT_PQC'),
    ('Distributed key generation', 'We construct a protocol under bilinear-group assumptions.', 'NON_LATTICE'),
    ('A novel cryptographic protocol', '', 'NON_LATTICE'),
])
def test_source_object_taxonomy_independent_of_frozen_score(title, abstract, expected):
    r = row(title, abstract)
    r.update(relevance_label='D', relevance_score=7, taxonomy_tags=['BKZ', 'LWE'])
    before = deepcopy(r)
    decision = contribution_view(r)
    assert decision['category'] == expected
    assert decision['taxonomy_version'] == VERSION
    assert decision['frozen_selection_changed'] is False
    assert r == before
    for span in decision['source_spans']:
        assert span['source_excerpt'] in r[span['source_field']]
        assert span['source_sha256'] == hashlib.sha256(r[span['source_field']].encode()).hexdigest()


def test_nine_categories_and_unverified_identity():
    assert len(Contribution) == 9
    assert contribution_view({'title': 'Falcon algorithm'})['category'] == 'VERIFY_FIRST'


def test_generated_tags_and_owner_text_do_not_create_lattice_scope():
    r = row('Neural network parameter extraction', 'We recover a neural network architecture.')
    r.update(taxonomy_tags=['LWE', 'BKZ'], conclusion='We break Module-LWE.',
             scientific_owner_review_v1={'category': 'LATTICE_CRYPTANALYSIS'})
    assert contribution_view(r)['category'] == 'NON_LATTICE'


def test_dissertation_identity_not_new_algorithm():
    v = contribution_view(row('Lattice Cryptography: Isomorphisms & Dual Attacks PhD thesis',
                              'We study lattice isomorphisms and lattice cryptography.'))
    assert v['contribution_kind'] == 'DISSERTATION'
    assert v['verification_boundary'].endswith('E3_FULLTEXT_NOT_VERIFIED')


def test_role_summary_deduplicates_exact_role_object_only():
    roles = [{'role': 'PRIMARY_RESEARCH_OBJECT', 'technical_target': 'LWE'}] * 3
    roles.append({'role': 'ATTACK_TARGET', 'technical_target': 'LWE'})
    assert role_summary({'source_relation_roles': roles}) == 'PRIMARY_RESEARCH_OBJECT: LWE; ATTACK_TARGET: LWE'


def test_abstract_guide_retains_evidence_and_translation_boundaries():
    guide = abstract_guide(row('Primal attack on LWE', 'We study an attack on LWE in a weak parameter range.'))
    assert '摘要级研究指南（E2，非全文翻译）' in guide
    assert 'TODO_VERIFY_TRANSLATION' in guide and 'E3 全文、证明与实验尚未核验' in guide
    assert 'LWE' in guide and '区分渐近结果和实用攻击' in guide
    assert '已被攻破' not in guide
    assert 'E1' in abstract_guide(row('Primal attack on LWE', ''))


def payload(tmp_path):
    r = bind_source_evidence(make_paper_record(**row('Falcon fixed-point implementation',
        'We implement Falcon signatures using fixed-point arithmetic.')))
    return build_daily_payload([r], tmp_path/'data', date(2026, 10, 19),
        [{'source': 'iacr_eprint', 'health_status': 'green', 'runtime_state': 'complete',
          'query_groups_total': 1, 'query_groups_success': 1}],
        warnings=['PRIVATE-DIAGNOSTIC sentinel HTTP 429 body and tracking token'],
        metadata={'target_date': '2026-10-19', 'coverage_start': '2026-10-17T21:00:00+08:00',
                  'coverage_end': '2026-10-19T09:00:00+08:00', '_publication_prior': []})


def test_renderer_human_flow_preserves_exact_ledger_qa_and_json(tmp_path):
    p = payload(tmp_path)
    original = deepcopy(p)
    md = render_scientific_daily(p)
    assert semantic_qa(p, md, candidate=True)['status'] == 'PASS'
    assert p == original
    assert 'PRIVATE-DIAGNOSTIC' not in md
    assert 'PRIVATE-DIAGNOSTIC' in p['warnings'][0]
    assert '<summary>官方原始摘要与分类证据</summary>' in md
    assert 'We implement Falcon' in md
    assert md.index('中文技术导读') < md.index('原始摘要：')
    assert md.index('审计附录：') < md.index('- Daily publication events：')


def test_optional_gmail_status_discloses_missing_permission_without_private_data(tmp_path):
    p = payload(tmp_path)
    p['metadata']['gmail_iacr'] = {'status': 'GMAIL_AUTHORIZATION_REQUIRED',
        'message_id': 'PRIVATE-MESSAGE', 'subject': 'PRIVATE-SUBJECT', 'address': 'private@example.test'}
    md = render_scientific_daily(p)
    assert 'GMAIL_AUTHORIZATION_REQUIRED' in md
    assert '邮件核对未完成' in md
    assert all(s not in md for s in ('PRIVATE-MESSAGE', 'PRIVATE-SUBJECT', 'private@example.test'))


def test_late_arrival_is_displayed_once_without_new_publication_or_email_links(tmp_path):
    p = payload(tmp_path)
    before = deepcopy(p['publication_event_ledger'])
    p['late_arrivals'] = [{'eprint_id': '2026/8888', 'source_url': 'https://eprint.iacr.org/2026/8888'},
        {'eprint_id': '2026/8888', 'source_url': 'https://eprint.iacr.org/2026/8888'},
        {'source_url': 'https://mail.google.com/mail/u/0/?token=PRIVATE'},
        {'source_url': 'https://eprint.iacr.org/2026/1) [PRIVATE](https://evil.example)'},
        {'source_url': 'https://eprint.iacr.org/2026/7777?unsubscribe=PRIVATE'}]
    md = render_scientific_daily(p)
    assert '迟到发现与更正（不计为今日首发）' in md
    assert md.count('https://eprint.iacr.org/2026/8888') == 1
    assert 'PRIVATE' not in md
    assert p['publication_event_ledger'] == before
    assert semantic_qa(p, md, candidate=True)['status'] == 'PASS'
