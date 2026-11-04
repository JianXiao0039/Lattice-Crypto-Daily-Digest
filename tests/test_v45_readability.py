"""Source-bound text regression; constructed source wrappers are TEST_ONLY."""
from lattice_digest.critical_translation import build_critical_claim_translation, source_math_fragments
from lattice_digest.models import make_paper_record

# Verbatim mathematical fragments from official 2026/1591 landing abstract.
SOURCE = r"""We present a polynomial-time quantum algorithm for the Dihedral Coset Problem (DCP). The algorithm can tolerate a faulty sample rate as high as $1/O(\log{n})$, allowing the algorithm-reduction combination to efficiently solve, for example, SVP with a $\sqrt{n}$ polylog($n$) approximation factor, or LWE instances with $\alpha=\sqrt{n}$ polylog($n$). Additional note: https://eprint.iacr.org/2026/1693 has been posted claiming to prove that the algorithm can't possibly work."""


def record(abstract=SOURCE):
    return make_paper_record(paper_id='eprint:2026/1591', source='iacr_eprint',
        source_url='https://eprint.iacr.org/2026/1591',
        title='A Polynomial-Time Quantum Algorithm for the Dihedral Coset Problem',
        authors=['Daniel R. Simon'], abstract=abstract)


def test_source_math_stops_at_closed_delimiter_not_later_parenthesis():
    fragments=source_math_fragments(SOURCE)
    assert r'$1/O(\log{n})$' in fragments
    assert r'$\alpha=\sqrt{n}$' in fragments
    assert all('allowing' not in f for f in fragments)
    assert source_math_fragments('1/O(log n), then O(sqrt(n) polylog(n))-factor') == ['1/O(log n)','O(sqrt(n) polylog(n))']


def test_chinese_claim_keeps_whole_math_and_contested_boundary():
    text=build_critical_claim_translation(record())
    for fragment in source_math_fragments(SOURCE):
        assert fragment in text
    assert 'allowing the algorithm' not in text
    assert 'https://eprint.iacr.org/2026/1693' in text
    assert '未独立复核数学证明，未执行 Lean' in text
    assert 'TODO_VERIFY' in text


def test_refutation_is_not_translated_as_positive_algorithm():
    text=build_critical_claim_translation(record('The algorithm does not solve DCP and cannot succeed. We release Lean 4 code.'))
    assert '作者反驳' in text
    assert '尚未独立复核全文证明或执行 Lean' in text
    assert '提出针对二面体陪集问题' not in text


def test_unclosed_or_escaped_math_is_not_spliced_into_chinese():
    assert source_math_fragments(r'TEST_ONLY $1/O(log n) and unrelated English') == []
    assert source_math_fragments(r'TEST_ONLY \$not math\$') == []
    assert source_math_fragments(r'TEST_ONLY \(x+1\) and \[y^2\]') == [r'\(x+1\)',r'\[y^2\]']


def test_noncounting_critical_watch_remains_visible_without_private_ledger_fields():
    from lattice_digest.publication_events import build_event_ledger, POLICY_VERSION
    from lattice_digest.scientific_daily import render_scientific_daily
    row=record().model_dump()
    row.update(publication_date='2026-08-03',security_impact_severity='CRITICAL')
    meta=dict(target_date='2026-11-04',coverage_start='2026-11-02T13:07:43+00:00',
        coverage_end='2026-11-04T01:07:43+00:00',publication_policy_version=POLICY_VERSION,
        source_coverage={'complete':False},authority_state='PROVISIONAL_PUBLIC')
    ledger=build_event_ledger([row],meta)
    assert ledger['counts']['primary_new']==0
    assert ledger['critical_watch']
    ledger['critical_watch'][0]['private_test_canary']='TEST_ONLY_PRIVATE_LEDGER_CANARY'
    text=render_scientific_daily(dict(metadata=meta,records=[row],publication_event_ledger=ledger))
    assert '持续关注的重大安全主张（不计入当期事件）' in text
    assert 'CONTESTED_HIGH_IMPACT_LATTICE_SECURITY_CLAIM' in text
    assert 'https://eprint.iacr.org/2026/1693' in text
    assert 'TEST_ONLY_PRIVATE_LEDGER_CANARY' not in text
    assert '原始摘要' in text


def _official_abstracts():
    import json
    from pathlib import Path
    return json.loads((Path(__file__).parent/'fixtures/v45_contested_abstracts.json').read_text(encoding='utf-8'))['abstracts']


def test_exact_reviewed_contested_cards_do_not_transfer_to_changed_source():
    from lattice_digest.public_technical import detail, check_detail, PENDING
    for ident, abstract in _official_abstracts().items():
        url='https://eprint.iacr.org/2026/'+ident
        card=detail(abstract,url,['DCP'])
        assert card['status']=='REVIEWED_PUBLIC_ABSTRACT'
        assert 'CONTESTED_HIGH_IMPACT_LATTICE_SECURITY_CLAIM' in str(card)
        assert '未执行 Lean' in str(card)
        assert check_detail(card,url,['DCP'])==card
        assert detail(abstract+' TEST_ONLY_CHANGED_SOURCE',url,['DCP'])['status']==PENDING
        assert detail(abstract,'https://eprint.iacr.org/2026/9999',['DCP'])['status']==PENDING


from tests.test_public_report_pipeline import canonical, DAY


def test_public_noncounting_radar_preserves_reviewed_controversy(canonical):
    from lattice_digest.report_gate import verify
    from lattice_digest.public_report import project, validate_public, render
    from lattice_digest.models import make_paper_record
    pair=verify(canonical,'daily',str(DAY))
    pair.events.clear()
    for ident,abstract in _official_abstracts().items():
        title=('A Polynomial-Time Quantum Algorithm for the Dihedral Coset Problem' if ident=='1591'
               else 'The ePrint:2026/1591 Quantum Algorithm Does Not Solve DCP')
        pair.source_rows.append(make_paper_record(paper_id='iacr:2026/'+ident,source='iacr_eprint',
            source_url='https://eprint.iacr.org/2026/'+ident,eprint_id='2026/'+ident,
            title=title,authors=['TEST_ONLY_PROJECTION_WRAPPER'],abstract=abstract).model_dump())
    public=project(pair)
    validate_public(public)
    watches=[o for o in public['noncounting_observations'] if o['source_url'] in
             ['https://eprint.iacr.org/2026/1591','https://eprint.iacr.org/2026/1693']]
    # 1693 lacks direct lattice terms in its own abstract: keep the frozen
    # scope gate and preserve its rebuttal through the reviewed 1591 card.
    assert len(watches)==1
    assert '2026/1693' in watches[0]['technical_detail']['result_zh']
    assert public['event_count']==0
    assert all(o['technical_detail']['status']=='REVIEWED_PUBLIC_ABSTRACT' for o in watches)
    markdown=render(public).decode()
    assert 'CONTESTED_HIGH_IMPACT_LATTICE_SECURITY_CLAIM' in markdown.replace('\\_', '_')
    assert 'November 3' in markdown
    assert '未执行 Lean' in markdown

    for row in pair.source_rows:
        if row.get('eprint_id')=='2026/1591':
            row['abstract']+=' TEST_ONLY_CHANGED_ABSTRACT'
    changed=project(pair)
    assert not any(o['source_url']=='https://eprint.iacr.org/2026/1591' for o in changed['noncounting_observations'])
