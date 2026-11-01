"""Provider envelopes must not become successful zero-hit research days."""
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from lattice_digest.sources.base import FetchContext
from lattice_digest.sources.dblp import DblpSource
from lattice_digest.sources.semantic_scholar import SemanticScholarSource


def fetch_shape(tmp_path, monkeypatch, source, envelope):
    name, cls = ('dblp', DblpSource) if source == 'dblp' else ('semantic_scholar', SemanticScholarSource)
    monkeypatch.setattr(f'lattice_digest.sources.{name}.fetch_json', lambda *a, **kw: envelope)
    context = FetchContext(root=tmp_path, since=datetime(2026, 10, 30, tzinfo=timezone.utc), dry_run=False)
    config = {'name': name, 'url': 'https://example.test/search', 'queries': ['LWE'], 'query_terms': ['LWE']}
    rows = cls(config).fetch(context)
    context.finish_source(name, len(rows))
    return rows, context.health(name)


@pytest.mark.parametrize('envelope', [{}, {'data': None}, {'data': {}}, {'data': [None]}, {'message': 'Too Many Requests', 'code': '429'}])
def test_semantic_missing_or_malformed_data_never_means_zero_success(tmp_path, monkeypatch, envelope):
    rows, health = fetch_shape(tmp_path, monkeypatch, 'semantic_scholar', envelope)
    assert rows == []
    assert health.query_groups_success == 0 and health.query_groups_failed > 0
    assert health.runtime_state != 'complete'
    assert health.error_type() == 'malformed_response'


@pytest.mark.parametrize('hits', [{}, {'@total': '3'}, {'@total': '1', 'hit': 'bad'}, {'hit': [None]}, {'hit': [{'info': None}]}])
def test_dblp_incomplete_envelope_never_means_zero_success(tmp_path, monkeypatch, hits):
    rows, health = fetch_shape(tmp_path, monkeypatch, 'dblp', {'result': {'hits': hits}})
    assert rows == []
    assert health.query_groups_success == 0 and health.query_groups_failed > 0
    assert health.runtime_state != 'complete'


@pytest.mark.parametrize('source,envelope', [('dblp', {'result': {'hits': {'@total': '0'}}}), ('semantic_scholar', {'data': []})])
def test_explicit_valid_empty_shape_is_success(tmp_path, monkeypatch, source, envelope):
    rows, health = fetch_shape(tmp_path, monkeypatch, source, envelope)
    assert rows == [] and health.query_groups_failed == 0 and health.query_groups_success == 1


def test_dblp_single_hit_object_is_not_iterated_as_keys(tmp_path, monkeypatch):
    rows, health = fetch_shape(tmp_path, monkeypatch, 'dblp', {'result': {'hits': {'@total': '1', 'hit': {'info': {
        'title': 'Module-LWE', 'url': 'https://dblp.org/rec/example', 'year': '2026', 'authors': {'author': []}
    }}}}})
    assert len(rows) == 1 and health.query_groups_success == 1


def test_oct30_saved_provider_failures_remain_unavailable(tmp_path):
    """Replay observed transport/HTTP failures without contacting a provider.

    The DBLP saved preview is deliberately incomplete and is only used to test
    rejection of its actual HTML shape, never to claim a complete snapshot.
    """
    from lattice_digest.http import request_json
    snapshot = json.loads((Path(__file__).parent / 'fixtures/v43_source_incident.json').read_text('utf-8'))
    assert snapshot['source_json_sha256'] == '089b64fd52f953ea7f73fe2a69bba86a5e7cb30f19aa3c5c8c4c59d7edc36778'
    for source in snapshot['sources']:
        diagnostic = source['request_diagnostics'][0]
        calls = []
        class Response:
            status = diagnostic['http_status']
            headers = {'Content-Type': diagnostic['content_type'] or ''}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return (diagnostic['body_preview'] or '').encode('utf-8')
        def opener(request, timeout):
            calls.append(1)
            if diagnostic['http_status'] is None:
                raise URLError('saved incident transport failure')
            if diagnostic['http_status'] == 429:
                raise HTTPError(request.full_url, 429, 'saved provider rate limit', {}, None)
            return Response()
        data, response = request_json(diagnostic['effective_url'], user_agent='v43-offline-replay',
                                      open_func=opener, cache_dir=tmp_path/source['source'],
                                      min_interval_seconds=0, max_retries=1, sleep_func=lambda _:None)
        assert data is None and not response.ok and len(calls) <= 2
        assert not list((tmp_path/source['source']).glob('*.body'))
