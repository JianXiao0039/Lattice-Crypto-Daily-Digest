from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import pytest

from lattice_digest.sources.arxiv import ArxivSource
from lattice_digest.sources.iacr import IacrEprintSource
from lattice_digest.sources.base import FetchContext


def context(tmp_path):
    return FetchContext(root=tmp_path, since=datetime(2026, 10, 13, 13, tzinfo=timezone.utc), dry_run=False)


def atom(ids=(), *, total=None, start=0):
    counters = '' if total is None else f'<o:totalResults>{total}</o:totalResults><o:startIndex>{start}</o:startIndex>'
    rows = ''.join(f'<entry><id>https://arxiv.org/abs/2610.{i:05d}v1</id><title>Module lattice algorithm {i}</title>'
                   '<summary>Exact SVP in module lattices.</summary><published>2026-10-14T01:00:00Z</published>'
                   '<updated>2026-10-14T02:00:00Z</updated></entry>' for i in ids)
    return f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:o="http://a9.com/-/spec/opensearch/1.1/">{counters}{rows}</feed>'


def run_arxiv(tmp_path, monkeypatch, responder, **config):
    calls = []
    def fetch(ctx, url, source_name):
        query = parse_qs(urlparse(url).query)
        calls.append(query)
        return responder(query)
    monkeypatch.setattr('lattice_digest.sources.arxiv.fetch_text', fetch)
    monkeypatch.setattr('lattice_digest.sources.arxiv.critical_query_requests', lambda *a, **kw: [])
    ctx = context(tmp_path)
    cfg = {'name': 'arxiv', 'url': 'https://export.arxiv.org/api/query', 'query_groups': [['SVP']], 'per_query_results': 2, **config}
    ctx.register_source(cfg)
    records = ArxivSource(cfg).fetch(ctx)
    ctx.finish_source('arxiv', len(records))
    return records, ctx, calls


def coverage(ctx, source):
    return [row for row in ctx.health(source).request_diagnostics if row.get('kind') == 'source_coverage_v1']


def test_arxiv_official_pagination_exhausts_query_and_preserves_dates(tmp_path, monkeypatch):
    def respond(q):
        start = int(q['start'][0])
        return atom([1, 2] if start == 0 else [3], total=3, start=start)
    records, ctx, calls = run_arxiv(tmp_path, monkeypatch, respond)
    assert [q['start'][0] for q in calls] == ['0', '2']
    assert len(records) == 3
    assert {r.publication_timestamp for r in records} == {'2026-10-14T01:00:00Z'}
    assert ctx.since == datetime(2026, 10, 13, 13, tzinfo=timezone.utc)
    assert ctx.health('arxiv').runtime_state == 'complete'
    assert coverage(ctx, 'arxiv')[-1]['coverage_state'] == 'SOURCE_COMPLETE'
    assert coverage(ctx, 'arxiv')[-1]['scope'] == 'CONFIGURED_QUERY_EXPRESSIONS_NOT_ALL_ARXIV'


def test_arxiv_query_budget_preserves_partial_candidates(tmp_path, monkeypatch):
    records, ctx, calls = run_arxiv(tmp_path, monkeypatch, lambda q: atom([1, 2], total=9), max_pages_per_query=1)
    assert len(calls) == 1 and len(records) == 2
    assert ctx.query_attempts[0]['status'] == 'partial'
    assert ctx.query_attempts[0]['raw_candidates'] == 2
    assert ctx.health('arxiv').runtime_state == 'partial'
    assert ctx.health('arxiv').runtime_reason_code == 'ARXIV_QUERY_PAGE_BUDGET_EXHAUSTED'


def test_arxiv_total_budget_visits_expressions_before_second_pages(tmp_path, monkeypatch):
    records, ctx, calls = run_arxiv(tmp_path, monkeypatch, lambda q: atom([1, 2], total=8),
                                    query_groups=[['SVP'], ['hinted ISIS']], max_total_pages=2)
    assert len(calls) == 2 and len({q['search_query'][0] for q in calls}) == 2
    assert all(q['start'] == ['0'] for q in calls)
    assert len(records) == 2
    assert all(a['status'] == 'partial' for a in ctx.query_attempts)
    assert coverage(ctx, 'arxiv')[-1]['coverage_state'] == 'SOURCE_PARTIAL'


def test_arxiv_paginated_diagnostics_bind_to_actual_query_not_last_scheduled(tmp_path, monkeypatch):
    def respond(q):
        return atom([1], total=1)
    calls = []
    def fetch(ctx, url, source_name):
        q = parse_qs(urlparse(url).query)
        calls.append(q)
        ctx.health(source_name).request_diagnostics.append({'attempt_id': ctx.query_attempts[-1]['attempt_id'], 'http_status': 200})
        return respond(q)
    monkeypatch.setattr('lattice_digest.sources.arxiv.fetch_text', fetch)
    monkeypatch.setattr('lattice_digest.sources.arxiv.critical_query_requests', lambda *a, **kw: [])
    ctx = context(tmp_path)
    ArxivSource({'name': 'arxiv', 'url': 'https://export.arxiv.org/api/query', 'query_groups': [['SVP'], ['LWQ']]}).fetch(ctx)
    diagnostics = [d for d in ctx.health('arxiv').request_diagnostics if 'http_status' in d]
    assert [d['attempt_id'] for d in diagnostics] == [a['attempt_id'] for a in ctx.query_attempts]
    assert all(d['pagination_start'] == 0 for d in diagnostics)


def test_arxiv_unattempted_budget_query_is_unknown_not_zero(tmp_path, monkeypatch):
    _, ctx, calls = run_arxiv(tmp_path, monkeypatch, lambda q: atom([1], total=1),
                              query_groups=[['SVP'], ['LWQ']], max_total_pages=1)
    assert len(calls) == 1
    skipped = [a for a in ctx.query_attempts if a['status'] == 'skipped_by_budget']
    assert len(skipped) == 1 and skipped[0]['raw_candidates'] is None
    assert skipped[0]['coverage_semantics'] == 'UNKNOWN_COVERAGE'
    assert not any(e.get('decision') == 'QUERY_ZERO_HIT' for e in ctx.route_events)


def test_arxiv_missing_pagination_metadata_never_claims_complete(tmp_path, monkeypatch):
    records, ctx, calls = run_arxiv(tmp_path, monkeypatch, lambda q: atom([1]))
    assert len(records) == 1 and len(calls) == 1
    assert ctx.health('arxiv').runtime_state == 'partial'
    assert ctx.health('arxiv').runtime_reason_code == 'ARXIV_PAGINATION_METADATA_MISSING'


def test_arxiv_missing_counters_empty_page_is_unknown_not_zero_hit(tmp_path, monkeypatch):
    _, ctx, _ = run_arxiv(tmp_path, monkeypatch, lambda q: atom([]))
    assert ctx.query_attempts[0]['status'] == 'partial'
    assert ctx.query_attempts[0]['coverage_semantics'] == 'UNKNOWN_COVERAGE'
    assert not any(e.get('decision') == 'QUERY_ZERO_HIT' for e in ctx.route_events)


@pytest.mark.parametrize('budget', [{'max_total_pages': 0}, {'max_pages_per_query': 0}])
def test_arxiv_zero_budget_makes_no_request(tmp_path, monkeypatch, budget):
    records, ctx, calls = run_arxiv(tmp_path, monkeypatch, lambda q: pytest.fail('zero budget must not fetch'), **budget)
    assert records == [] and calls == []
    assert ctx.query_attempts[0]['raw_candidates'] is None
    assert ctx.query_attempts[0]['status'] == 'skipped_by_budget'


@pytest.mark.parametrize('response', [atom([], total=5), atom([1], total=0), atom([1], total=3, start=1)])
def test_arxiv_inconsistent_or_empty_nonexhausted_page_is_partial(tmp_path, monkeypatch, response):
    _, ctx, calls = run_arxiv(tmp_path, monkeypatch, lambda q: response)
    assert len(calls) == 1
    assert coverage(ctx, 'arxiv')[-1]['coverage_state'] != 'SOURCE_COMPLETE'
    assert ctx.query_attempts[0]['status'] == 'partial'


def test_arxiv_second_page_transport_failure_preserves_first_page(tmp_path, monkeypatch):
    records, ctx, calls = run_arxiv(tmp_path, monkeypatch,
                                    lambda q: atom([1, 2], total=4) if q['start'] == ['0'] else None)
    assert len(records) == 2 and len(calls) == 2
    assert ctx.query_attempts[0]['status'] == 'partial'
    assert ctx.query_attempts[0]['raw_candidates'] == 2
    assert coverage(ctx, 'arxiv')[-1]['coverage_state'] == 'SOURCE_PARTIAL'


def test_arxiv_valid_empty_query_is_exhausted_zero(tmp_path, monkeypatch):
    records, ctx, calls = run_arxiv(tmp_path, monkeypatch, lambda q: atom([], total=0))
    assert records == [] and len(calls) == 1
    assert ctx.query_attempts[0]['status'] == 'success'
    assert coverage(ctx, 'arxiv')[-1]['coverage_state'] == 'SOURCE_COMPLETE'


def test_arxiv_failed_transport_is_unavailable_not_a_zero_query(tmp_path, monkeypatch):
    _, ctx, calls = run_arxiv(tmp_path, monkeypatch, lambda q: None)
    assert len(calls) == 1 and ctx.query_attempts[0]['raw_candidates'] is None
    assert coverage(ctx, 'arxiv')[-1]['coverage_state'] == 'SOURCE_UNAVAILABLE'


def test_arxiv_repeated_page_or_changed_total_is_partial(tmp_path, monkeypatch):
    _, ctx, calls = run_arxiv(tmp_path, monkeypatch,
                              lambda q: atom([1, 2], total=4, start=int(q['start'][0])))
    assert len(calls) == 2
    assert ctx.health('arxiv').runtime_reason_code == 'ARXIV_REPEATED_PAGE'
    assert coverage(ctx, 'arxiv')[-1]['coverage_state'] == 'SOURCE_PARTIAL'


def test_arxiv_total_changed_during_pagination_preserves_partial(tmp_path, monkeypatch):
    records, ctx, calls = run_arxiv(tmp_path, monkeypatch,
                                    lambda q: atom([1, 2], total=4) if q['start'] == ['0'] else atom([3, 4], total=5, start=2))
    assert len(calls) == 2 and len(records) == 4
    assert ctx.health('arxiv').runtime_reason_code == 'ARXIV_RESULTS_CHANGED_DURING_PAGINATION'


def test_iacr_bounded_latest_feed_is_partial_even_with_100_entries_and_cached_once(tmp_path, monkeypatch):
    calls = []
    body = '<rss><channel>' + ''.join(f'<item><title>Lattice source {i}</title><link>https://eprint.iacr.org/2026/{i}</link><pubDate>2026-10-14</pubDate></item>' for i in range(100, 200)) + '</channel></rss>'
    def fetch(*a, **kw):
        calls.append(1)
        return body
    monkeypatch.setattr('lattice_digest.sources.iacr.fetch_text', fetch)
    cfg = {'name': 'iacr_eprint', 'url': 'https://eprint.iacr.org/rss/rss.xml'}
    for _ in range(2):
        ctx = context(tmp_path)
        records = IacrEprintSource(cfg).fetch(ctx)
        ctx.finish_source('iacr_eprint', len(records))
        assert len(records) == 100
        receipt = coverage(ctx, 'iacr_eprint')[-1]
        assert receipt['coverage_state'] == 'SOURCE_PARTIAL'
        assert receipt['historical_window_complete'] is False
        assert receipt['requested_since'] == ctx.since.isoformat()
        assert ctx.health('iacr_eprint').runtime_state == 'partial'
    assert len(calls) == 1


def test_iacr_antibot_html_is_parse_failure_not_zero(tmp_path, monkeypatch):
    monkeypatch.setattr('lattice_digest.sources.iacr.fetch_text', lambda *a, **kw: '<html><body>challenge</body></html>')
    ctx = context(tmp_path)
    records = IacrEprintSource({'name': 'iacr_eprint', 'url': 'https://eprint.iacr.org/rss/rss.xml'}).fetch(ctx)
    assert records == [] and ctx.query_attempts[0]['status'] == 'failed'
    assert ctx.query_attempts[0]['raw_candidates'] is None
    assert coverage(ctx, 'iacr_eprint')[-1]['coverage_state'] == 'SOURCE_UNAVAILABLE'


def test_iacr_failed_guard_keeps_unknown_and_does_not_retry(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr('lattice_digest.sources.iacr.fetch_text', lambda *a, **kw: calls.append(1))
    cfg = {'name': 'iacr_eprint', 'url': 'https://eprint.iacr.org/rss/rss.xml'}
    for _ in range(2):
        ctx = context(tmp_path)
        assert IacrEprintSource(cfg).fetch(ctx) == []
        assert ctx.query_attempts[0]['raw_candidates'] is None
        assert coverage(ctx, 'iacr_eprint')[-1]['coverage_state'] == 'SOURCE_UNAVAILABLE'
    assert len(calls) == 1
