import json
import ssl
from urllib.error import HTTPError
from datetime import datetime, timezone
import pytest
from lattice_digest.http import request_json, request_text
from lattice_digest.sources.base import FetchContext, _response_failure_category


class Response:
    status=200
    def __init__(self,body=b'{}',content_type='application/json'):
        self.body=body; self.headers={'Content-Type':content_type}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return self.body


@pytest.mark.parametrize('code',[406,429,500,503])
def test_http_failures_never_become_zero_hit_success(tmp_path,code):
    calls=[]
    def opener(request,timeout):
        calls.append(1)
        raise HTTPError(request.full_url,code,'provider failure',{},None)
    data,response=request_json('https://example.test/query',user_agent='test',cache_dir=tmp_path,open_func=opener,min_interval_seconds=0,sleep_func=lambda t:None)
    assert data is None and not response.ok and len(calls)<=3
    assert not list(tmp_path.glob('*.body'))


@pytest.mark.parametrize('body,ctype',[(b'<html>failure</html>','text/html'),(b'invalid','application/json'),(b'[]','application/json')])
def test_malformed_response_is_not_cached_or_a_transport_failure(tmp_path,body,ctype):
    data,response=request_json('https://example.test/query',user_agent='test',cache_dir=tmp_path,open_func=lambda *a,**kw:Response(body,ctype),min_interval_seconds=0)
    assert data is None and _response_failure_category(response)=='malformed_response'
    assert not list(tmp_path.glob('*.body'))


@pytest.mark.parametrize('error,category',[(ssl.SSLError('bad TLS'),'ssl_error'),(TimeoutError(),'timeout')])
def test_transport_category(tmp_path,error,category):
    def opener(*a,**kw):raise error
    _,response=request_json('https://example.test/query',user_agent='test',cache_dir=tmp_path,open_func=opener,min_interval_seconds=0)
    assert _response_failure_category(response)==category


def test_long_retry_after_defers_instead_of_early_retry(tmp_path):
    calls=[];sleeps=[]
    def opener(request,timeout):
        calls.append(1);raise HTTPError(request.full_url,429,'rate limit',{'Retry-After':'30'},None)
    response=request_text('https://example.test/query',user_agent='test',cache_dir=tmp_path,open_func=opener,min_interval_seconds=0,sleep_func=sleeps.append)
    assert not response.ok and len(calls)==1 and sleeps==[]


def test_malformed_circuit_and_zero_success(tmp_path):
    context=FetchContext(root=tmp_path,since=datetime(2026,9,17,tzinfo=timezone.utc),dry_run=False)
    for _ in range(3):context.note_request_result('dblp',ok=False,failure_category='malformed_response')
    assert not context.request_allowed('dblp')
    context.note_request_result('arxiv',ok=True)
    assert context.request_allowed('arxiv')


def test_valid_zero_response_is_distinct_from_unavailable(tmp_path):
    data,response=request_json('https://example.test/query',user_agent='test',cache_dir=tmp_path,open_func=lambda *a,**kw:Response(b'{"data":[]}'),min_interval_seconds=0)
    assert response.ok and data=={'data':[]}


def test_bad_historical_json_cache_is_not_reused(tmp_path):
    request_text('https://example.test/bad-cache',user_agent='test',cache_dir=tmp_path,open_func=lambda *a,**kw:Response(b'<html/>','text/html'),min_interval_seconds=0)
    data,response=request_json('https://example.test/bad-cache',user_agent='test',cache_dir=tmp_path,open_func=lambda *a,**kw:Response(b'{"data":[]}'),min_interval_seconds=0)
    assert response.ok and not response.from_cache and data=={'data':[]}


def test_deadline_caps_timeout_and_retry_sleep(tmp_path):
    calls=[];sleeps=[]
    def opener(request,timeout):
        calls.append(timeout);raise HTTPError(request.full_url,503,'busy',{'Retry-After':'3'},None)
    response=request_text('https://deadline.test/query',user_agent='test',cache_dir=tmp_path,open_func=opener,min_interval_seconds=0,time_budget_seconds=2,sleep_func=sleeps.append,monotonic_func=lambda:100.0)
    assert not response.ok and calls==[2] and sleeps==[]


def test_provider_defer_stops_later_queries_in_same_run(tmp_path,monkeypatch):
    from lattice_digest.http import HttpResponse,HttpWarning
    from lattice_digest.sources.base import fetch_json
    calls=[]
    def limited(*args,**kwargs):
        calls.append(1)
        return None,HttpResponse(False,'https://example.test',warning=HttpWarning(url='https://example.test',status_code=429,retry_after=30))
    monkeypatch.setattr('lattice_digest.sources.base.request_json',limited)
    context=FetchContext(root=tmp_path,since=datetime(2026,9,17,tzinfo=timezone.utc),dry_run=False)
    for _ in range(4):assert fetch_json(context,'https://example.test',source_name='semantic_scholar') is None
    assert len(calls)==1 and context.health('semantic_scholar').runtime_state=='partial'
