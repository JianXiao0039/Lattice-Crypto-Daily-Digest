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
def published_repo(tmp_path, monkeypatch):
    root = tmp_path / 'code'
    root.mkdir()
    manifest = json.loads((ROOT / MANIFEST_PATH).read_text(encoding='utf-8'))
    paths = set().union(*(set(item['paths']) for item in manifest['profiles'].values()))
    paths |= {'src/lattice_digest/weekly_handoff.py', 'scripts/run_local_digest_backfill.ps1', '.gitignore'}
    for name in sorted(paths):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    # A compiled test-only authority policy in the disposable copied source.
    # Production has no env/CLI override accepting arbitrary local refs.
    authority = tmp_path / 'test-authority.git'
    policy = root / 'src/lattice_digest/remote_authority.py'
    marker = "APPROVED_ORIGIN = 'https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git'"
    content = policy.read_text(encoding='utf-8')
    assert content.count(marker) == 1
    policy.write_text(content.replace(marker, f'APPROVED_ORIGIN = {str(authority)!r}'), encoding='utf-8')
    import lattice_digest.runtime_provenance as runtime_module
    monkeypatch.setattr(runtime_module, 'APPROVED_ORIGIN', str(authority))
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL)
    git('init', '-b', 'main')
    git('config', 'user.name', 'fixture')
    git('config', 'user.email', 'fixture@example.test')
    git('add', '--', *sorted(paths))
    git('commit', '-m', 'fixture published authority')
    git('update-ref', 'refs/remotes/origin/main', 'HEAD')
    # TEST AUTHORITY only. A bare remote permits fixture publication without
    # mutating a checked-out branch or relaxing receive.denyCurrentBranch.
    subprocess.check_output(['git', 'clone', '--bare', str(root), str(authority)],
                            stderr=subprocess.STDOUT)
    git('remote', 'add', 'origin', str(authority))
    return root, git


def invoke(root, canonical, module, args):
    env = dict(os.environ, PYTHONPATH=str(root / 'src'),
               LATTICE_DIGEST_CANONICAL_ROOT=str(canonical), PYTHONDONTWRITEBYTECODE='1')
    env.pop('LATTICE_DIGEST_PUBLIC_AUTOMATION', None)
    env.pop('LATTICE_DIGEST_ENV_FILE', None)
    return subprocess.run([os.environ.get('LATTICE_DIGEST_TEST_PUBLIC_PYTHON', sys.executable),
                           '-m', module, *args], cwd=root, env=env,
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
    actual = runtime_provenance(root, profile, verify_remote=True)
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
        'runtime_code_state':'PUBLISHED_CLEAN_RUNTIME','authority_mode':'LIVE_REMOTE_VERIFIED','runtime_git_head':'fixture-head',
        'runtime_code_manifest_sha256':'fixture-hash'})
    def fail_scratch(*args,**kwargs):
        assert args[1] != tmp_path and kwargs['history_root'] == tmp_path
        assert not list(tmp_path.iterdir())
        raise ValueError('synthetic scratch QA rejection')
    monkeypatch.setattr(storage,'_publish_daily_pair_locked',fail_scratch)
    with pytest.raises(ValueError,match='scratch QA rejection'):
        storage.publish_daily_pair([],tmp_path,date(2026,10,7),metadata=metadata)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('kind', ['provisional_json', 'authoritative_json', 'markdown_only'])
def test_exact_existing_target_stops_before_discovery_and_never_auto_supersedes(tmp_path, monkeypatch, kind):
    from lattice_digest import run
    from lattice_digest.artifact_paths import daily_data_path, daily_digest_path
    target = date(2025,1,7)
    path = (daily_digest_path(target,tmp_path/'digests') if kind=='markdown_only' else
            daily_data_path(target,tmp_path/'data'))
    path.parent.mkdir(parents=True)
    original = ('existing synthetic Markdown fixture' if kind=='markdown_only' else json.dumps({
        'metadata':{'quality_status':'provisional' if kind.startswith('provisional') else 'authoritative',
                    'collector':'github_actions','target_date':'2025-01-07'},'records':[]}))
    path.write_text(original,encoding='utf-8')
    monkeypatch.setattr(run,'project_root',lambda:tmp_path)
    monkeypatch.setattr('lattice_digest.runtime_provenance.runtime_provenance',
                        lambda root:{'runtime_code_state':'PUBLISHED_CLEAN_RUNTIME','authority_mode':'LIVE_REMOTE_VERIFIED'})
    monkeypatch.setattr(run,'load_config_bundle',lambda *args:pytest.fail('existing exact target must stop before discovery configuration'))
    monkeypatch.setattr(run,'_collect_records',lambda *args:pytest.fail('discovery must not start'))
    assert run.main(['--run-mode','backfill','--target-date','2025-01-07',
                     '--quality-status','authoritative_backfill',
                     '--coverage-start','2025-01-05T21:04:26.631541+08:00',
                     '--coverage-end','2025-01-07T09:04:26.631541+08:00']) == 2
    assert path.read_text(encoding='utf-8') == original
    assert [entry for entry in tmp_path.rglob('*') if entry.is_file()] == [path]


@pytest.fixture
def nested_repo(published_repo, tmp_path):
    published, _ = published_repo
    canonical = tmp_path / 'canonical'
    root = canonical / '.ops/runtime/published'
    shutil.copytree(published, root)
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL)
    return root, canonical, git


@pytest.mark.parametrize('module,args', [
    ('lattice_digest.public_daily', ['--preflight','--since','36h']),
    ('lattice_digest.public_weekly', ['--preflight']),
    ('lattice_digest.public_monthly', ['--preflight']),
    ('lattice_digest.public_monthly', ['--preflight','--exports']),
    ('lattice_digest.public_monthly', ['--preflight','--exports','--obsidian']),
])
def test_trusted_nested_runtime_with_dirty_outer_source_passes(nested_repo, module, args):
    root, canonical, _ = nested_repo
    outer = canonical / 'src/lattice_digest/workflow.py'
    outer.parent.mkdir(parents=True)
    outer.write_text("raise RuntimeError('dirty development must never execute')\n")
    before = outer.read_bytes()
    result = invoke(root, canonical, module, args)
    assert result.returncode == 0, result.stdout + result.stderr
    proof = json.loads(result.stdout)
    assert proof['writes'] == 0
    assert proof['runtime_provenance']['runtime_code_state'] == 'PUBLISHED_CLEAN_RUNTIME'
    assert proof['runtime_provenance']['runtime_provenance_observation'] == 'LIVE_REMOTE'
    assert all((root / name).is_file() for name in proof['observed_import_paths'])
    assert outer.read_bytes() == before
    assert not (canonical / 'papers.db').exists()


@pytest.mark.parametrize('mutation', ['dirty_workflow','unpublished','missing_manifest','incorrect_manifest',
    'manifest_omission','incorrect_canonical','runtime_db','runtime_data','arbitrary_ops'])
def test_nested_boundary_adversarial_blocks(nested_repo, mutation):
    root, canonical, git = nested_repo
    if mutation == 'dirty_workflow':
        with (root/'src/lattice_digest/workflow.py').open('a') as stream:
            stream.write('\n# dirty runtime\n')
    elif mutation == 'unpublished':
        (root/'note.md').write_text('unpublished docs-only commit')
        git('add','--','note.md'); git('commit','-m','unpublished')
        # A stale/manipulated tracking ref must not authorize the commit.
        git('update-ref','refs/remotes/origin/main','HEAD')
    elif mutation == 'missing_manifest':
        (root/MANIFEST_PATH).unlink()
    elif mutation in ('incorrect_manifest','manifest_omission'):
        manifest = json.loads((root/MANIFEST_PATH).read_text())
        if mutation == 'incorrect_manifest':
            manifest['schema_version'] = 999
        else:
            manifest['profiles']['DAILY']['paths'].remove('src/lattice_digest/workflow.py')
        (root/MANIFEST_PATH).write_text(json.dumps(manifest))
        git('add','--',MANIFEST_PATH); git('commit','-m','invalid fixture manifest')
        git('push','origin','HEAD:refs/heads/main')  # Only the temporary local fixture remote.
    elif mutation == 'incorrect_canonical':
        canonical = canonical / 'wrong'
        canonical.mkdir()
    elif mutation == 'runtime_db':
        (root/'papers.db').write_bytes(b'second universe')
    elif mutation == 'runtime_data':
        (root/'data').mkdir()
    else:
        other = canonical / '.ops/arbitrary'
        shutil.copytree(root, other)
        root = other
    result = invoke(root, canonical, 'lattice_digest.public_daily', ['--preflight'])
    assert result.returncode == 2, result.stdout + result.stderr
    assert not (canonical/'data').exists()


@pytest.mark.parametrize('entry', ['outer_src','arbitrary_ops','external','empty'])
def test_nested_unexpected_pythonpath_blocks(nested_repo, tmp_path, entry):
    root, canonical, _ = nested_repo
    extra = {'outer_src':str(canonical/'src'), 'arbitrary_ops':str(canonical/'.ops/other'),
             'external':str(tmp_path/'unknown'), 'empty':''}[entry]
    env = dict(os.environ, PYTHONPATH=str(root/'src')+os.pathsep+extra,
               LATTICE_DIGEST_CANONICAL_ROOT=str(canonical), PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable,'-m','lattice_digest.public_daily','--preflight'],
                            cwd=root,env=env,capture_output=True,text=True)
    assert result.returncode == 2, result.stdout + result.stderr


def test_outer_unknown_module_import_blocks(nested_repo):
    root, canonical, _ = nested_repo
    source = canonical/'outer.py'
    source.write_text('value = 1\n')
    script = (
        'import importlib.util,sys; '
        f'spec=importlib.util.spec_from_file_location("unknown_outer",{str(source)!r}); '
        'module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; '
        'spec.loader.exec_module(module); '
        'from lattice_digest.public_daily import main; sys.exit(main(["--preflight"]))')
    env = dict(os.environ,PYTHONPATH=str(root/'src'),LATTICE_DIGEST_CANONICAL_ROOT=str(canonical),
               PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable,'-c',script],cwd=root,env=env,capture_output=True,text=True)
    assert result.returncode == 2 and 'canonical development tree' in result.stdout


def test_outer_lattice_module_import_blocks(nested_repo):
    root, canonical, _ = nested_repo
    source = canonical/'workflow.py'
    source.write_text('value = 1\n')
    script = (
        'import importlib.util,sys; from lattice_digest.public_daily import main; '
        f'spec=importlib.util.spec_from_file_location("lattice_digest.workflow",{str(source)!r}); '
        'module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; '
        'spec.loader.exec_module(module); sys.exit(main(["--preflight"]))')
    env = dict(os.environ,PYTHONPATH=str(root/'src'),LATTICE_DIGEST_CANONICAL_ROOT=str(canonical),
               PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable,'-c',script],cwd=root,env=env,capture_output=True,text=True)
    assert result.returncode == 2 and 'canonical development tree' in result.stdout


@pytest.mark.parametrize('target', ['runtime','canonical_data','dependency'])
def test_windows_junction_escape_blocks(nested_repo, tmp_path, target):
    root, canonical, _ = nested_repo
    outside = tmp_path/'outside'
    outside.mkdir()
    if target == 'runtime':
        saved = tmp_path/'saved_runtime'
        shutil.move(root,saved)
        link, destination = root, saved
    elif target == 'canonical_data':
        link, destination = canonical/'data', outside
    else:
        saved = outside/'lattice_digest'
        shutil.move(root/'src/lattice_digest',saved)
        link, destination = root/'src/lattice_digest', saved
    if os.name == 'nt':
        # Windows native junctions need no Developer Mode/admin symlink privilege.
        result = subprocess.run(['cmd','/c','mklink','/J',str(link),str(destination)],capture_output=True)
        assert result.returncode == 0, result.stderr
    else:
        link.symlink_to(destination,target_is_directory=True)
    try:
        result = invoke(root,canonical,'lattice_digest.public_daily',['--preflight'])
        assert result.returncode == 2, result.stdout + result.stderr
    finally:
        if os.name == 'nt':
            os.rmdir(link)  # Remove only the fixture junction, never its target.
        else:
            link.unlink()


def test_windows_case_and_dot_normalization(nested_repo):
    root, canonical, _ = nested_repo
    env = dict(os.environ,PYTHONPATH=str(root/'src'),PYTHONDONTWRITEBYTECODE='1',
               LATTICE_DIGEST_CANONICAL_ROOT=str(canonical/'.'/'child'/'..'))
    (canonical/'child').mkdir()
    if os.name == 'nt':
        env['LATTICE_DIGEST_CANONICAL_ROOT'] = env['LATTICE_DIGEST_CANONICAL_ROOT'].swapcase()
        env['PYTHONPATH'] = env['PYTHONPATH'].swapcase()
    result = subprocess.run([sys.executable,'-m','lattice_digest.public_weekly','--preflight'],
                            cwd=root,env=env,capture_output=True,text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_git_discovery_cannot_inherit_outer_repository(published_repo):
    root, _ = published_repo
    child = root / 'ordinary-subdirectory'
    child.mkdir()
    info = runtime_provenance(child, 'DAILY', verify_remote=True)
    assert info['runtime_code_state'] == 'UNKNOWN_RUNTIME_PROVENANCE'
    assert 'independent Git checkout' in info['runtime_provenance_error']


def test_unknown_live_authority_blocks(nested_repo):
    root, canonical, git = nested_repo
    git('remote', 'remove', 'origin')
    result = invoke(root, canonical, 'lattice_digest.public_daily', ['--preflight'])
    assert result.returncode == 2
    assert 'UNKNOWN_RUNTIME_PROVENANCE' in result.stdout


def test_manifest_worktree_hash_mismatch_blocks(nested_repo):
    root, canonical, _ = nested_repo
    with (root / MANIFEST_PATH).open('a') as stream:
        stream.write('\n ')
    result = invoke(root, canonical, 'lattice_digest.public_weekly', ['--preflight'])
    assert result.returncode == 2
    assert 'DIRTY_RUNTIME_DEPENDENCY' in result.stdout


@pytest.mark.parametrize('location', ['untrusted_ops', 'trusted_unmanifested'])
def test_untrusted_module_not_hidden_by_nonpackage_name(nested_repo, location):
    root, canonical, _ = nested_repo
    source = (canonical / '.ops/other' if location == 'untrusted_ops' else root) / 'extra.py'
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text('value = 1\n')
    script = (
        'import importlib.util,sys; '
        f'spec=importlib.util.spec_from_file_location("untrusted_extra",{str(source)!r}); '
        'module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; '
        'spec.loader.exec_module(module); '
        'from lattice_digest.public_daily import main; sys.exit(main(["--preflight"]))')
    env = dict(os.environ, PYTHONPATH=str(root/'src'),
               LATTICE_DIGEST_CANONICAL_ROOT=str(canonical), PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable, '-c', script], cwd=root, env=env,
                            capture_output=True, text=True)
    assert result.returncode == 2
    assert ('canonical development tree' if location == 'untrusted_ops'
            else 'import omitted from command manifest') in result.stdout
