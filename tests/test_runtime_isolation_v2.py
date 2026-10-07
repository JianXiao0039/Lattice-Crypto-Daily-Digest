from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from lattice_digest.runtime_paths import RuntimePaths, env_file
from lattice_digest.recovery_window import exact_window, validate_recovery_metadata, recovery_metadata
from lattice_digest.runtime_dependencies import MANIFEST_PATH, profile_paths
from lattice_digest.runtime_provenance import runtime_provenance, public_runtime_allowed

ROOT = Path(__file__).resolve().parents[1]
START = '2026-10-05T21:04:26.631541+08:00'
END = '2026-10-07T09:04:26.631541+08:00'


@pytest.fixture
def published_repo(tmp_path):
    root = tmp_path / 'code'
    root.mkdir()
    manifest = json.loads((ROOT / MANIFEST_PATH).read_text(encoding='utf-8'))
    paths = set().union(*(set(item['paths']) for item in manifest['profiles'].values()))
    paths |= {'src/lattice_digest/weekly_handoff.py', 'scripts/run_local_digest_backfill.ps1', '.gitignore'}
    for name in sorted(paths):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL)
    git('init', '-b', 'main')
    git('config', 'user.name', 'fixture')
    git('config', 'user.email', 'fixture@example.test')
    git('add', '--', *sorted(paths))
    git('commit', '-m', 'fixture published authority')
    git('update-ref', 'refs/remotes/origin/main', 'HEAD')
    git('remote', 'add', 'origin', str(root))
    return root, git


def invoke(root, canonical, module, args):
    env = dict(os.environ, PYTHONPATH=str(root / 'src'),
               LATTICE_DIGEST_CANONICAL_ROOT=str(canonical), PYTHONDONTWRITEBYTECODE='1')
    env.pop('LATTICE_DIGEST_PUBLIC_AUTOMATION', None)
    env.pop('LATTICE_DIGEST_ENV_FILE', None)
    return subprocess.run([sys.executable, '-m', module, *args], cwd=root, env=env,
                          capture_output=True, text=True, encoding='utf-8')


def test_single_root_contract_and_manual_defaults(tmp_path, monkeypatch):
    code, canonical = tmp_path / 'code', tmp_path / 'existing'
    paths = RuntimePaths.resolve(code_root=code, canonical_root=canonical, environ={})
    assert paths.config_root == code / 'config'
    assert paths.database_path == canonical / 'papers.db'
    for name, directory in [('data_root','data'), ('digest_root','digests'), ('audit_root','audits'),
                             ('state_root','state'), ('export_root','exports')]:
        assert getattr(paths, name) == canonical / directory
    monkeypatch.delenv('LATTICE_DIGEST_CANONICAL_ROOT', raising=False)
    from lattice_digest.weekly_synthesis import parse_args
    assert parse_args([]).data_dir == Path('data')
    monkeypatch.setenv('LATTICE_DIGEST_CANONICAL_ROOT', str(canonical))
    assert parse_args([]).data_dir == canonical / 'data'


def test_secret_file_is_explicit_for_public_runtime(tmp_path):
    code = tmp_path / 'code'
    assert env_file(code, public=True, environ={}) is None
    assert env_file(code, public=False, environ={}) == code / '.env'
    secret = tmp_path / 'external.env'
    secret.write_text('TEST_KEY=fixture-secret')
    assert env_file(code, public=True, environ={'LATTICE_DIGEST_ENV_FILE':str(secret)}) == secret
    with pytest.raises(ValueError):
        env_file(code, public=True, environ={'LATTICE_DIGEST_ENV_FILE':'relative.env'})


@pytest.mark.parametrize('value', ['relative-canonical-root', 'missing-absolute-root'])
def test_public_root_typos_fail_before_git_or_directory_creation(tmp_path, monkeypatch, value):
    from lattice_digest.public_contract import public_preflight
    supplied = value if value.startswith('relative') else str(tmp_path/value)
    monkeypatch.setenv('LATTICE_DIGEST_CANONICAL_ROOT', supplied)
    monkeypatch.setattr('lattice_digest.public_contract.runtime_provenance',
                        lambda *args,**kwargs: pytest.fail('invalid paths must fail before Git'))
    with pytest.raises(ValueError, match='canonical root'):
        public_preflight('DAILY')
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('profile,path,blocking', [
    ('DAILY','src/lattice_digest/weekly_handoff.py',False),
    ('DAILY','scripts/run_local_digest_backfill.ps1',False),
    ('DAILY','src/lattice_digest/workflow.py',True),
    ('MONTHLY','src/lattice_digest/obsidian_scaffold.py',False),
    ('MONTHLY_EXPORTS','src/lattice_digest/obsidian_scaffold.py',False),
    ('MONTHLY_OBSIDIAN','src/lattice_digest/obsidian_scaffold.py',True),
])
def test_real_dirty_path_execution_profiles(published_repo, profile, path, blocking):
    root, git = published_repo
    initial = runtime_provenance(root, profile)
    assert initial['runtime_code_state'] == 'PUBLISHED_CLEAN_RUNTIME'
    with (root / path).open('a', encoding='utf-8') as stream:
        stream.write('\n# unrelated fixture edit\n')
    actual = runtime_provenance(root, profile)
    assert actual['runtime_code_state'] == ('DIRTY_RUNTIME_DEPENDENCY' if blocking else 'PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_WORKTREE')
    assert public_runtime_allowed(actual, public_automation=True) == (not blocking)
    assert (actual['runtime_code_manifest_sha256'] == initial['runtime_code_manifest_sha256']) == (not blocking)


def test_manifest_omission_new_import_and_unknown_dynamic_fail_closed(published_repo):
    root, git = published_repo
    module = root / 'src/lattice_digest/new_runtime.py'
    module.write_text('value = 1\n')
    source = root / 'src/lattice_digest/public_weekly.py'
    with source.open('a', encoding='utf-8') as stream:
        stream.write('\nfrom lattice_digest import new_runtime\n')
    manifest = json.loads((root / MANIFEST_PATH).read_text())
    with pytest.raises(ValueError, match='omission'):
        profile_paths(root, manifest, 'WEEKLY')
    git('add', '--', 'src/lattice_digest/new_runtime.py', 'src/lattice_digest/public_weekly.py')
    git('commit', '-m', 'fixture omitted import')
    git('update-ref', 'refs/remotes/origin/main', 'HEAD')
    info = runtime_provenance(root, 'WEEKLY')
    assert info['runtime_code_state'] == 'UNKNOWN_RUNTIME_PROVENANCE'
    assert not public_runtime_allowed(info, public_automation=True)
    module.write_text("__import__('unknown_runtime')\n")
    with pytest.raises(ValueError, match='dynamic'):
        profile_paths(root, manifest, 'WEEKLY')


def test_staged_runtime_change_blocks_even_when_worktree_matches_authority(published_repo):
    root, git = published_repo
    path = root / 'src/lattice_digest/public_weekly.py'
    original = path.read_bytes()
    path.write_bytes(original + b'\n# staged change\n')
    git('add', '--', 'src/lattice_digest/public_weekly.py')
    path.write_bytes(original)
    assert runtime_provenance(root, 'WEEKLY')['runtime_code_state'] == 'DIRTY_RUNTIME_DEPENDENCY'


def test_any_unpublished_head_and_tampered_manifest_block(published_repo):
    root, git = published_repo
    note = root / 'note.md'
    note.write_text('docs only')
    git('add', '--', 'note.md')
    git('commit', '-m', 'fixture unpublished docs')
    assert runtime_provenance(root, 'DAILY')['runtime_code_state'] == 'UNPUBLISHED_RUNTIME_COMMIT'
    git('update-ref', 'refs/remotes/origin/main', 'HEAD')
    (root / MANIFEST_PATH).write_text('{}')
    assert runtime_provenance(root, 'DAILY')['runtime_code_state'] == 'DIRTY_RUNTIME_DEPENDENCY'


@pytest.mark.parametrize('module,args', [
    ('lattice_digest.public_daily',['--preflight','--since','36h']),
    ('lattice_digest.public_weekly',['--preflight']),
    ('lattice_digest.public_monthly',['--preflight']),
    ('lattice_digest.public_monthly',['--preflight','--exports']),
    ('lattice_digest.public_monthly',['--preflight','--exports','--obsidian']),
])
def test_public_no_write_import_trace_and_single_universe(published_repo, tmp_path, module, args):
    root, _ = published_repo
    canonical = tmp_path / 'canonical'
    canonical.mkdir()
    result = invoke(root, canonical, module, args)
    assert result.returncode == 0, result.stdout + result.stderr
    proof = json.loads(result.stdout)
    assert proof['runtime_paths']['canonical_root'] == str(canonical)
    assert proof['runtime_provenance']['runtime_code_state'] == 'PUBLISHED_CLEAN_RUNTIME'
    assert not list(canonical.iterdir())
    assert not any((root / name).exists() for name in ('data','digests','state','exports','audits','papers.db'))


def test_exact_2026_10_07_preflight_round_trip_no_discovery(published_repo, tmp_path):
    root, _ = published_repo
    canonical = tmp_path / 'canonical'
    canonical.mkdir()
    result = invoke(root, canonical, 'lattice_digest.public_daily', [
        '--preflight','--run-mode','backfill','--target-date','2026-10-07',
        '--coverage-start',START,'--coverage-end',END,'--since','36h',
        '--original-missing-reason','PUBLIC_AUTOMATION_RUNTIME_CODE_BLOCKED'])
    assert result.returncode == 0, result.stdout + result.stderr
    assert START in result.stdout and END in result.stdout
    assert 'BACKFILL' in result.stdout and '"canonical_target_exists": false' in result.stdout
    assert not list(canonical.iterdir())


@pytest.mark.parametrize('changes', [
    {'run_mode':'daily'}, {'target':None}, {'start':'2026-10-05T21:04:26'},
    {'end':START}, {'since_hours':24},
])
def test_exact_window_rejects_ambiguous_or_invalid_requests(changes):
    values = dict(start=START, end=END, target='2026-10-07', run_mode='backfill', since_hours=36)
    values.update(changes)
    with pytest.raises(ValueError):
        exact_window(**values)


def test_normal_36h_calendar_24h_and_fractional_exact_duration():
    from lattice_digest.run import _coverage_window, _exact_date_coverage_window, parse_args
    now = datetime.fromisoformat(END)
    lower, upper = _coverage_window(date(2026,10,7),36,False,now)
    assert upper == now and upper - lower == timedelta(hours=36)
    lower, upper = _exact_date_coverage_window(date(2026,10,7))
    assert upper - lower == timedelta(hours=24) and upper.hour == 16
    lower, upper = exact_window(START,END,'2026-10-07',run_mode='backfill')
    metadata = recovery_metadata(date(2026,10,7),lower,upper,now,'PUBLIC_AUTOMATION_RUNTIME_CODE_BLOCKED')
    metadata.update(target_date='2026-10-07',coverage_start=START,coverage_end=END,run_mode='backfill')
    validate_recovery_metadata(metadata,date(2026,10,7))
    metadata['coverage_end'] = '2026-10-07T00:00:00+08:00'
    with pytest.raises(ValueError, match='mismatch'):
        validate_recovery_metadata(metadata,date(2026,10,7))
    with pytest.raises(SystemExit):
        parse_args(['--coverage-start',START])


def test_published_obsidian_wrapper_interface(tmp_path):
    from scripts.export_obsidian_notes import main
    assert main(['--latest','--dry-run','--state-path',str(tmp_path/'missing.json'),
                 '--output-dir',str(tmp_path/'exports')]) == 0
    assert not list(tmp_path.iterdir())


def test_monthly_downstream_all_paths_use_canonical_root(tmp_path, monkeypatch):
    from lattice_digest.monthly_downstream import run_downstream
    calls = {}
    monkeypatch.setattr('lattice_digest.reading_queue.main', lambda argv: calls.setdefault('queue',argv) and 0)
    monkeypatch.setattr('lattice_digest.research_artifact_export.generate_research_artifact_export',
                        lambda **kwargs: calls.update(artifacts=kwargs))
    monkeypatch.setattr('lattice_digest.research_progress.generate_research_progress',
                        lambda **kwargs: calls.update(progress=kwargs))
    monkeypatch.setattr('lattice_digest.monthly_obsidian.export_notes', lambda paths: calls.update(notes=paths))
    paths = RuntimePaths.resolve(code_root=tmp_path/'code',canonical_root=tmp_path/'canonical',environ={})
    run_downstream(paths,'2025-01-01','2025-01-31',obsidian=True)
    assert str(paths.data_root) in calls['queue']
    assert str(paths.state_root/'reading-queue.json') in calls['queue']
    assert calls['artifacts']['daily_data_dir'] == paths.data_root
    assert calls['artifacts']['output_dir'] == paths.export_root/'research-artifacts'
    assert calls['progress']['reading_queue'] == paths.state_root/'reading-queue.json'
    assert calls['progress']['source_health_dir'] == paths.audit_root/'source-health'
    for key in ('obsidian_notes_dir','artifact_dir','output_dir'):
        assert calls['progress'][key].is_relative_to(paths.export_root)
    assert calls['notes'] == paths


def test_exact_publication_rejects_window_or_runtime_before_any_canonical_write(tmp_path, monkeypatch):
    from lattice_digest.storage import publish_daily_pair
    lower, upper = exact_window(START,END,'2026-10-07',run_mode='backfill')
    metadata = recovery_metadata(date(2026,10,7),lower,upper,upper,'PUBLIC_AUTOMATION_RUNTIME_CODE_BLOCKED')
    metadata.update(target_date='2026-10-07',coverage_start=START,coverage_end=END,run_mode='backfill')
    metadata['coverage_end'] = START
    with pytest.raises(ValueError, match='mismatch'):
        publish_daily_pair([],tmp_path,date(2026,10,7),metadata=metadata)
    assert not list(tmp_path.iterdir())
    metadata['coverage_end'] = END
    monkeypatch.setattr('lattice_digest.runtime_provenance.runtime_provenance',
                        lambda *args,**kwargs: {'runtime_code_state':'DIRTY_RUNTIME_DEPENDENCY'})
    with pytest.raises(ValueError, match='published runtime'):
        publish_daily_pair([],tmp_path,date(2026,10,7),metadata=metadata)
    assert not list(tmp_path.iterdir())


def test_exact_recovery_scratch_qa_precedes_canonical_directories_and_preserves_history(tmp_path, monkeypatch):
    from lattice_digest import storage
    lower, upper = exact_window(START,END,'2026-10-07',run_mode='backfill')
    metadata = recovery_metadata(date(2026,10,7),lower,upper,upper,'PUBLIC_AUTOMATION_RUNTIME_CODE_BLOCKED')
    metadata.update(target_date='2026-10-07',coverage_start=START,coverage_end=END,run_mode='backfill',
                    runtime_git_head='fixture-head',runtime_code_manifest_sha256='fixture-hash')
    monkeypatch.setattr('lattice_digest.runtime_provenance.runtime_provenance',lambda *args,**kwargs:{
        'runtime_code_state':'PUBLISHED_CLEAN_RUNTIME','runtime_git_head':'fixture-head',
        'runtime_code_manifest_sha256':'fixture-hash'})
    def fail_scratch(*args,**kwargs):
        assert args[1] != tmp_path and kwargs['history_root'] == tmp_path
        assert not list(tmp_path.iterdir())
        raise ValueError('synthetic scratch QA rejection')
    monkeypatch.setattr(storage,'_publish_daily_pair_locked',fail_scratch)
    with pytest.raises(ValueError,match='scratch QA rejection'):
        storage.publish_daily_pair([],tmp_path,date(2026,10,7),metadata=metadata)
    assert not list(tmp_path.iterdir())
