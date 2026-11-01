"""TEST_ONLY mechanics: no synthetic scientific gold labels."""
from datetime import datetime,timezone,timedelta
import json
from urllib.parse import parse_qs,urlparse
from lattice_digest.sources.base import FetchContext
from lattice_digest.sources.arxiv import ArxivSource
from lattice_digest.sources.iacr import IacrEprintSource
from lattice_digest.source_batch_iacr import parse_iacr_days


def atom(ids,total,start=0):
    entries=''.join(f'<entry><id>https://arxiv.org/abs/2610.{i:05d}v1</id><title>TEST_ONLY</title><summary>test</summary><published>2026-10-29T01:00:00Z</published><updated>2026-10-30T01:00:00Z</updated><category term="cs.CC"/></entry>' for i in ids)
    return f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:o="http://a9.com/-/spec/opensearch/1.1/"><o:totalResults>{total}</o:totalResults><o:startIndex>{start}</o:startIndex>{entries}</feed>'


def ctx(tmp_path):
    return FetchContext(root=tmp_path,since=datetime(2026,10,29,tzinfo=timezone.utc),dry_run=False,cache_dir=tmp_path/'cache')


def test_native_before_keywords_and_submission_sort_crosslist_dedup(tmp_path,monkeypatch):
    calls=[]
    def fetch(c,url,source_name):
        q=parse_qs(urlparse(url).query);calls.append(q)
        return atom([1],1)
    monkeypatch.setattr('lattice_digest.sources.arxiv.fetch_text',fetch)
    cfg={'name':'arxiv','url':'https://export.arxiv.org/api/query','query_groups':[['BKZ']],
         'native_batch':{'enabled':True,'categories':['cs.CR','cs.CC','quant-ph']}}
    c=ctx(tmp_path);records=ArxivSource(cfg).fetch(c)
    assert 'submittedDate:[' in calls[0]['search_query'][0]
    assert 'all:' not in calls[0]['search_query'][0]
    assert calls[0]['sortBy']==['submittedDate']
    assert calls[3]['sortBy']==['lastUpdatedDate']
    assert len(records)==1
    assert records[0].publication_date=='2026-10-29'
    assert records[0].update_date=='2026-10-30'
    assert records[0].publication_date_kind=='AUTHORITATIVE_SUBMISSION_DATE'
    assert records[0].publication_timestamp=='2026-10-29T01:00:00Z'


def test_native_page_budget_and_failure_preserve_partial(tmp_path,monkeypatch):
    calls=[]
    def fetch(c,url,source_name):
        q=parse_qs(urlparse(url).query);calls.append(q)
        return atom([1],1000) if len(calls)==1 else None
    monkeypatch.setattr('lattice_digest.sources.arxiv.fetch_text',fetch)
    c=ctx(tmp_path)
    records=ArxivSource({'name':'arxiv','url':'https://export.arxiv.org/api/query','query_groups':[['BKZ']],
                       'max_total_pages':2,'native_batch':{'enabled':True,'max_pages':1}}).fetch(c)
    assert len(records)==1
    assert c.query_attempts[0]['status']=='partial'
    assert c.health('arxiv').runtime_state in ('partial','failed')
    assert len(calls)==2


def test_iacr_bounded_retry_then_cap(tmp_path,monkeypatch):
    c=ctx(tmp_path);c.cache_dir.mkdir()
    now=datetime.now(timezone.utc)
    marker=c.cache_dir/f'iacr_eprint_{now.date().isoformat()}.attempt'
    marker.write_text(json.dumps({'attempts':1,'next_eligible_retry':(now-timedelta(hours=1)).isoformat()}))
    calls=[]
    monkeypatch.setattr('lattice_digest.sources.iacr.fetch_text',lambda *a,**k:calls.append(1))
    cfg={'name':'iacr_eprint','url':'https://eprint.iacr.org/rss/rss.xml','retry_failed_after_seconds':21600}
    assert IacrEprintSource(cfg).fetch(c)==[]
    assert IacrEprintSource(cfg).fetch(ctx(tmp_path))==[]
    assert len(calls)==1
    saved=json.loads(marker.read_text())
    assert saved['attempts']==2 and saved['response_status']=='TRANSPORT_FAILED'


def test_iacr_retry_cooldown_and_malformed_not_cached(tmp_path,monkeypatch):
    calls=[]
    monkeypatch.setattr('lattice_digest.sources.iacr.fetch_text',lambda *a,**k:(calls.append(1) or '<html>challenge</html>'))
    cfg={'name':'iacr_eprint','url':'https://eprint.iacr.org/rss/rss.xml','retry_failed_after_seconds':21600}
    assert IacrEprintSource(cfg).fetch(ctx(tmp_path))==[]
    assert IacrEprintSource(cfg).fetch(ctx(tmp_path))==[]
    assert len(calls)==1
    assert not list((tmp_path/'cache').glob('*.xml'))


def test_official_days_parser_does_not_create_publication_time():
    html='Papers updated in last 31 days <div class="d-flex mb-1"><a href="/2026/1">id</a>Last updated:&nbsp; 2026-10-29<div class="papertitle">TEST_ONLY</div><div class="summaryauthors">A and B</div><div class="paper-abstract">test abstract</div>'
    record=parse_iacr_days(html)[0]
    assert record.publication_date is None
    assert record.update_date=='2026-10-29'
    assert record.authors==['A','B']

def test_iacr_historical_failure_cooldown_and_empty_challenge(tmp_path):
    from lattice_digest.source_batch_iacr import fetch_iacr_days
    c=ctx(tmp_path);c.cache_dir.mkdir()
    calls=[]
    def fail(*a,**k):calls.append(1);return None
    assert fetch_iacr_days(c,{},fail)==[]
    assert fetch_iacr_days(ctx(tmp_path),{},fail)==[]
    assert len(calls)==1
    assert not list(c.cache_dir.glob('*.html'))
    import pytest
    with pytest.raises(ValueError):
        parse_iacr_days('Papers updated in last 31 days challenge')

def test_native_submission_timestamp_is_not_first_publication(tmp_path,monkeypatch):
    """TEST_ONLY qualified row isolates time-kind permission from scope/identity."""
    from lattice_digest.publication_events import build_event_ledger
    xml=atom([1],1).replace('<title>TEST_ONLY</title>', '<title>TEST_ONLY LWE lattice cryptanalysis</title>').replace('<summary>test</summary>', '<summary>We study LWE lattice cryptanalysis.</summary>')
    monkeypatch.setattr('lattice_digest.sources.arxiv.fetch_text',lambda *a,**k:xml)
    cfg={'name':'arxiv','url':'https://export.arxiv.org/api/query','query_groups':[['LWE']],
         'native_batch':{'enabled':True,'categories':['cs.CC']}}
    records=ArxivSource(cfg).fetch(ctx(tmp_path))
    assert len(records)==1
    row=records[0].model_dump(mode='json')
    assert row['publication_timestamp']=='2026-10-29T01:00:00Z'
    assert row['publication_date_kind']=='AUTHORITATIVE_SUBMISSION_DATE'
    assert not row.get('announcement_timestamp') and not row.get('announcement_date')
    meta={'target_date':'2026-10-29','coverage_start':'2026-10-29T00:00:00+00:00',
          'coverage_end':'2026-10-30T00:00:00+00:00'}
    actual=build_event_ledger([row],meta)
    assert actual['counts']['primary_new']==0
    assert actual['collections']['primary_publication_events']==[]
    # Counterfactual mechanism control: only falsely upgrading the kind would
    # create a primary event; source value, identity and scope are unchanged.
    false_publication=dict(row,publication_date_kind='AUTHORITATIVE_PUBLICATION_DATE')
    control=build_event_ledger([false_publication],meta)
    assert control['counts']['primary_new']==1
