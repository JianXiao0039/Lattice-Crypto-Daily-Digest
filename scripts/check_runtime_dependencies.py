"""Reviewable manifest builder and omission check; never edits runtime data."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from lattice_digest.runtime_dependencies import MANIFEST_PATH, import_closure, profile_paths

ROOT = Path(__file__).resolve().parents[1]


def build_manifest(root: Path = ROOT) -> dict:
    common = ['pyproject.toml', 'config/sources.yaml',
              'config/retrieval_ontology_v3.yaml']
    common += [name for name in ('requirements.txt', 'uv.lock', 'poetry.lock') if (root / name).is_file()]
    profiles = {}
    for name in ('DAILY', 'WEEKLY', 'MONTHLY', 'MONTHLY_EXPORTS', 'MONTHLY_OBSIDIAN'):
        command = name.split('_')[0].lower()
        roots = [f'src/lattice_digest/public_{command}.py']
        scopes, branches = {}, {}
        non_python = list(common)
        if name == 'DAILY':
            scopes['src/lattice_digest/workflow.py'] = ['doctor_report', '_doctor_release_hygiene', '_latest']
            non_python += ['config/taxonomy.yaml', 'config/keywords.yaml', 'config/negative_keywords.yaml',
                           'config/query_portfolio_v3.yaml', 'CHANGELOG.md', 'docs/releases/v0.4.1.md']
        if name.startswith('MONTHLY'):
            branches = {'src/lattice_digest/public_monthly.py': {'args.exports': name != 'MONTHLY'},
                        'src/lattice_digest/monthly_downstream.py': {'obsidian': name == 'MONTHLY_OBSIDIAN'}}
        closure = import_closure(root, roots, function_scopes=scopes, branch_values=branches)
        profiles[name] = {'roots': roots, 'function_scopes': scopes, 'branch_values': branches,
                          'reviewed_non_python': sorted(non_python),
                          'paths': sorted(closure | set(non_python) | {MANIFEST_PATH})}
    return {'schema_version': 1, 'profiles': profiles}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Regenerate only after reviewing closure/config changes.')
    args = parser.parse_args(argv)
    expected = build_manifest()
    target = ROOT / MANIFEST_PATH
    if args.write:
        target.write_text(json.dumps(expected, indent=2) + '\n', encoding='utf-8')
    actual = json.loads(target.read_text(encoding='utf-8'))
    if actual != expected:
        raise ValueError('published dependency manifest is stale; review changes before regeneration')
    for profile in actual['profiles']:
        paths = profile_paths(ROOT, actual, profile)
        print(f'{profile}: {len(paths)} dependencies, omission check PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
