"""Cross-process renderer reproducibility, including case-variant keywords."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def test_ranking_and_markdown_are_identical_across_hash_seeds():
    root = Path(__file__).resolve().parents[1]
    program = '''
import hashlib, json
from datetime import date
from lattice_digest.models import make_paper_record
from lattice_digest.ranking_explainability import build_ranking_explanation
from lattice_digest.digest import generate_markdown
r = make_paper_record(title='LWE and ISIS lattice cryptanalysis',
    abstract='We study Learning With Errors and lattice reduction.',
    source='arxiv', source_url='https://arxiv.org/abs/2601.90001')
r = r.model_copy(update={'keywords_matched': ['lwe', 'LWE', 'isis', 'ISIS',
    'Learning With Errors', 'Learning with Errors', 'learning with errors'],
    'relevance_score': 90, 'relevance_label': 'A'})
print(json.dumps({'ranking': build_ranking_explanation(r),
    'markdown_sha256': hashlib.sha256(generate_markdown([r], date(2026,1,2)).encode()).hexdigest()}, sort_keys=True))
'''
    results = []
    for seed in ('0', '1', '2', '17'):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE='1',
                   PYTHONPATH=str(root / 'src'))
        result = subprocess.run([os.environ.get('LATTICE_DIGEST_TEST_PUBLIC_PYTHON', sys.executable),
                                 '-c', program], cwd=root, env=env,
                                capture_output=True, text=True, encoding='utf-8', check=True)
        results.append(json.loads(result.stdout))
    assert all(value == results[0] for value in results[1:])
