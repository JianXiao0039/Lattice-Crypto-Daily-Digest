"""Transport faults must be real denials, never cached release authorization."""
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest
from lattice_digest import remote_authority as remote
from lattice_digest import runtime_provenance as provenance
from tests.test_runtime_isolation_v2 import published_repo


@pytest.mark.parametrize('stderr,code', [
    (b'failed to connect over proxy', 'PROXY_ENDPOINT_UNREACHABLE'),
    (b'Could not resolve host github.com', 'DNS_FAILURE'),
    (b'Connection timed out', 'CONNECTION_TIMEOUT'),
    (b'SSL certificate problem', 'TLS_FAILURE'),
    (b'Authentication failed', 'REMOTE_AUTH_FAILURE'),
    (b'407 Proxy authentication required', 'PROXY_AUTH_FAILURE'),
    (b'Failed to connect to github.com', 'GITHUB_HTTPS_UNREACHABLE'),
    (b'unknown remote diagnostic token=secret', 'UNKNOWN_NETWORK_FAILURE'),
])
def test_failure_categories(stderr, code):
    assert remote.failure_category(stderr) == code


@pytest.mark.parametrize('value', ['http://user:secret@localhost:7890',
    'http://example.com:7890', 'socks5://localhost:7890', 'http://localhost',
    'http://localhost:7890/?token=secret', 'http://localhost:7890/#fragment',
    'http://localhost:7890/path', 'http://localhost:99999', 'http://localhost:7890\n'])
def test_untrusted_proxy_denied(value):
    assert remote.safe_loopback_proxy(value) is None


def test_existing_proxy_recovery_still_performs_real_remote_read(monkeypatch):
    calls = []
    def run(args, **kw):
        calls.append((args, kw))
        assert kw['timeout'] <= remote.ATTEMPT_SECONDS
        assert kw['env']['GIT_TERMINAL_PROMPT'] == '0'
        assert 'http.sslVerify=true' in args
        if len(calls) == 1:
            return SimpleNamespace(returncode=128, stdout=b'', stderr=b'Could not connect over proxy')
        return SimpleNamespace(returncode=0, stdout=b'a'*40+b'\trefs/heads/main\n', stderr=b'')
    monkeypatch.setattr(remote.subprocess, 'run', run)
    monkeypatch.setattr(remote, 'windows_proxy', lambda: 'http://127.0.0.1:7890')
    monkeypatch.setattr(remote.time, 'sleep', lambda _: None)
    result = remote.live_remote(Path('.'), remote.APPROVED_ORIGIN)
    assert result['status'] == 'VERIFIED' and result['sha'] == 'a'*40
    assert len(calls) == 2
    assert f'http.{remote.APPROVED_ORIGIN}.proxy=http://127.0.0.1:7890' in calls[1][0]
    assert '7890' not in str(result) and 'stderr' not in str(result)


@pytest.mark.parametrize('origin', ['https://github.com/other/repo.git', '/tmp/untrusted',
                                  'https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git?x=1'])
def test_other_origin_cannot_switch_route(monkeypatch, origin):
    monkeypatch.setattr(remote, 'windows_proxy', lambda: pytest.fail('unapproved route selection'))
    monkeypatch.setattr(remote.time, 'sleep', lambda _: None)
    monkeypatch.setattr(remote.subprocess, 'run', lambda *a, **k:
        SimpleNamespace(returncode=128, stdout=b'', stderr=b'Failed to connect over proxy'))
    result = remote.live_remote(Path('.'), origin)
    assert result['status'] == 'UNVERIFIED' and result['sha'] is None
    assert len(result['attempts']) == 3


@pytest.mark.parametrize('stderr', [b'SSL certificate failure', b'Authentication failed',
                                    b'407 proxy authentication', b'opaque secret=never-return'])
def test_nonretryable_errors_fail_closed_and_redacted(monkeypatch, stderr):
    monkeypatch.setattr(remote, 'windows_proxy', lambda: pytest.fail('must not switch policy'))
    monkeypatch.setattr(remote.subprocess, 'run', lambda *a, **k:
        SimpleNamespace(returncode=128, stdout=b'', stderr=stderr))
    result = remote.live_remote(Path('.'), remote.APPROVED_ORIGIN)
    assert result['status'] == 'UNVERIFIED' and result['sha'] is None
    assert len(result['attempts']) == 1
    assert 'never-return' not in str(result)


def test_timeout_total_budget_and_backoff(monkeypatch):
    clock = [0.0]
    def run(*a, **kw):
        clock[0] += kw['timeout']
        raise subprocess.TimeoutExpired('git', kw['timeout'])
    monkeypatch.setattr(remote.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(remote.time, 'sleep', lambda t: clock.__setitem__(0, clock[0]+t))
    monkeypatch.setattr(remote.subprocess, 'run', run)
    result = remote.live_remote(Path('.'), remote.APPROVED_ORIGIN)
    assert result['status'] == 'UNVERIFIED' and result['error_code'] == 'CONNECTION_TIMEOUT'
    assert len(result['attempts']) == 3 and clock[0] <= remote.TOTAL_SECONDS


@pytest.mark.parametrize('approval', ['absent', 'altered', 'expired', 'other-sha', 'other-profile'])
def test_no_writable_receipt_grants_offline_authority(published_repo, monkeypatch, approval):
    root, git = published_repo
    (root/'release-approval.json').write_text('{"approval":"'+approval+'"}')
    monkeypatch.setattr(provenance, 'live_remote', lambda *a: {
        'status':'UNVERIFIED','sha':None,'error_code':'PROXY_ENDPOINT_UNREACHABLE','attempts':[]})
    result = provenance.runtime_provenance(root, 'DAILY', verify_remote=True)
    assert result['local_code_integrity'] == 'VERIFIED'
    assert result['authority_mode'] == 'AUTHORITY_UNVERIFIED'
    assert result['remote_freshness'] == result['release_authorization'] == 'UNVERIFIED'
    assert result['runtime_origin_main'] is None
    assert not provenance.public_runtime_allowed(result, public_automation=True)


def test_remote_advance_is_denied_despite_clean_integrity(published_repo, monkeypatch):
    root, git = published_repo
    monkeypatch.setattr(provenance, 'live_remote', lambda *a: {
        'status':'VERIFIED','sha':'a'*40,'error_code':None,'attempts':[]})
    result = provenance.runtime_provenance(root, 'DAILY', verify_remote=True)
    assert result['runtime_code_state'] == 'UNPUBLISHED_RUNTIME_COMMIT'
    assert result['local_code_integrity'] == 'VERIFIED'
    assert result['release_authorization'] == 'UNVERIFIED'
    assert not provenance.public_runtime_allowed(result, public_automation=True)


def test_tamper_denied_before_any_network(published_repo, monkeypatch):
    root, git = published_repo
    with (root/'src/lattice_digest/public_daily.py').open('a') as stream:
        stream.write('\n# tampered\n')
    monkeypatch.setattr(provenance, 'live_remote', lambda *a: pytest.fail('tamper before network'))
    result = provenance.runtime_provenance(root, 'DAILY', verify_remote=True)
    assert result['local_code_integrity'] == 'FAILED'
    assert not provenance.public_runtime_allowed(result, public_automation=True)


def test_local_origin_substitution_cannot_claim_remote_freshness(published_repo, monkeypatch):
    root, git = published_repo
    git('remote', 'set-url', 'origin', str(root))
    monkeypatch.setattr(provenance, 'live_remote', lambda *a: pytest.fail('origin substitution must fail before network'))
    result = provenance.runtime_provenance(root, 'DAILY', verify_remote=True)
    assert result['runtime_failure_category'] == 'REMOTE_ORIGIN_MISMATCH'
    assert result['runtime_origin_main'] is None
    assert result['authority_mode'] == 'AUTHORITY_UNVERIFIED'
    assert not provenance.public_runtime_allowed(result, public_automation=True)


@pytest.mark.parametrize('mode', [None, 'AUTHORITY_UNVERIFIED', 'OFFLINE_CODE_INTEGRITY_VERIFIED'])
def test_clean_local_ref_state_is_not_public_authorization(mode):
    info = {'runtime_code_state':'PUBLISHED_CLEAN_RUNTIME', 'authority_mode':mode}
    assert not provenance.public_runtime_allowed(info, public_automation=True)
    assert provenance.public_runtime_allowed(info, public_automation=False)


@pytest.mark.parametrize('error,expected', [(b'Could not resolve host', 'DNS_FAILURE'),
    (b'Failed to connect over proxy', 'PROXY_ENDPOINT_UNREACHABLE'),
    (b'Git server failed with 128', 'UNKNOWN_NETWORK_FAILURE')])
def test_actual_128_is_denial_not_success(monkeypatch, error, expected):
    monkeypatch.setattr(remote, 'windows_proxy', lambda: None)
    monkeypatch.setattr(remote.time, 'sleep', lambda _: None)
    monkeypatch.setattr(remote.subprocess, 'run', lambda *a, **k:
        SimpleNamespace(returncode=128, stdout=b'a'*40+b'\trefs/heads/main\n', stderr=error))
    result = remote.live_remote(Path('.'), remote.APPROVED_ORIGIN)
    assert result['status'] == 'UNVERIFIED' and result['sha'] is None
    assert result['error_code'] == expected


def test_source_connectivity_does_not_override_failed_authority(tmp_path, monkeypatch):
    import json
    from lattice_digest import public_daily
    monkeypatch.setenv('LATTICE_DIGEST_CANONICAL_ROOT', str(tmp_path))
    monkeypatch.setenv('LATTICE_DIGEST_TRIGGER_KIND', 'RECOVERY')
    monkeypatch.delenv('LATTICE_DIGEST_SCHEDULED_FOR', raising=False)
    # Available sources cannot be called without an eligible release approval.
    monkeypatch.setattr(public_daily.run, 'main', lambda *a, **k: pytest.fail('unauthorized collection'))
    def reject(*a):
        raise ValueError('PUBLIC_AUTOMATION_RUNTIME_CODE_BLOCKED: '+json.dumps({
            'local_code_integrity':'VERIFIED','authority_mode':'AUTHORITY_UNVERIFIED',
            'runtime_failure_category':'PROXY_ENDPOINT_UNREACHABLE'}))
    monkeypatch.setattr(public_daily, 'public_preflight', reject)
    assert public_daily.main(['--target-date','2026-10-28']) == 2
    receipt = json.loads(next((tmp_path/'audits/public-entry-failures').glob('*/failure.json')).read_bytes())
    assert receipt['operational_states']['PREFLIGHT_BLOCKED'] is True
    assert receipt['operational_states']['SOURCE_COLLECTION_STARTED'] is False
    assert receipt['operational_states']['CANONICAL_CREATED'] is False
    assert receipt['schedule_telemetry']['scheduled_for'] == 'UNKNOWN'
    assert not (tmp_path/'data').exists()


def test_delayed_schedule_cannot_claim_on_time_delivery():
    from datetime import datetime
    result = provenance.schedule_telemetry(datetime.fromisoformat('2026-10-28T12:00:00+08:00'),
        environ={'LATTICE_DIGEST_TRIGGER_KIND':'SCHEDULED',
                 'LATTICE_DIGEST_SCHEDULED_FOR':'2026-10-28T09:00:00+08:00'})
    assert result['schedule_lag_seconds'] == 10800
    unknown = provenance.schedule_telemetry(datetime.fromisoformat('2026-10-28T12:00:00+08:00'),
        environ={'LATTICE_DIGEST_TRIGGER_KIND':'RECOVERY'})
    assert unknown['scheduled_for'] == unknown['schedule_lag_seconds'] == 'UNKNOWN'


def test_public_push_is_not_blindly_retried(monkeypatch, tmp_path):
    from lattice_digest import public_publisher
    calls = []
    def reject(*a, **k):
        calls.append(a)
        assert 'GIT_SSL_NO_VERIFY' not in k['env']
        return SimpleNamespace(returncode=128, stdout=b'', stderr=b'Failed to connect over proxy')
    monkeypatch.setenv('GIT_SSL_NO_VERIFY', 'true')
    monkeypatch.setattr(public_publisher.subprocess, 'run', reject)
    monkeypatch.setattr(public_publisher, 'windows_proxy', lambda: pytest.fail('no blind push retry'))
    result = public_publisher.git(tmp_path, 'push', remote.APPROVED_ORIGIN,
                                 'fixture:refs/heads/public-digests', check=False)
    assert result.returncode == 128 and len(calls) == 1


def test_public_read_route_recovery_is_bounded(monkeypatch, tmp_path):
    from lattice_digest import public_publisher
    calls = []
    def run(args, **kw):
        calls.append((args, kw))
        return SimpleNamespace(returncode=128 if len(calls)==1 else 0,
                               stdout=b'', stderr=b'Failed to connect over proxy')
    monkeypatch.setattr(public_publisher.subprocess, 'run', run)
    monkeypatch.setattr(public_publisher, 'windows_proxy', lambda: 'http://127.0.0.1:7890')
    result = public_publisher.git(tmp_path, 'ls-remote', remote.APPROVED_ORIGIN, 'refs/heads/public-digests')
    assert result.returncode == 0 and len(calls) == 2
    assert calls[0][1]['timeout'] + calls[1][1]['timeout'] <= 60


@pytest.mark.parametrize('raw,pac,enabled,expected', [
    ('127.0.0.1:7890', '', 1, 'http://127.0.0.1:7890'),
    ('http=127.0.0.1:7891;https=127.0.0.1:7890', '', 1, 'http://127.0.0.1:7890'),
    ('127.0.0.1:7890', 'https://policy.example/proxy.pac', 1, None),
    ('127.0.0.1:7890', '', 0, None),
    ('user:password@127.0.0.1:7890', '', 1, None),
    ('proxy.example:7890', '', 1, None),
    ('http=127.0.0.1:7890', '', 1, None),
])
def test_windows_policy_route_is_validated_without_disclosing_raw_config(monkeypatch, raw, pac, enabled, expected):
    import sys
    class Key:
        def __enter__(self): return self
        def __exit__(self, *a): pass
    values = {'ProxyEnable':enabled, 'ProxyServer':raw, 'AutoConfigURL':pac}
    fake = SimpleNamespace(HKEY_CURRENT_USER=object(), OpenKey=lambda *a: Key(),
                           QueryValueEx=lambda key,name: (values[name],None))
    with monkeypatch.context() as patch:
        patch.setitem(sys.modules, 'winreg', fake)
        patch.setattr(remote.os, 'name', 'nt')
        actual = remote.windows_proxy()
    assert actual == expected
