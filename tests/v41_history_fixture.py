"""Explicit synthetic history for tests of a fully evidenced control path.

These empty observations are test transport inputs, never real historical facts.
Tests for incomplete evidence must not call this helper.
"""
from datetime import timedelta
import hashlib
import json


def seed_empty_history(root, target, *, days=14):
    for offset in range(1, days + 1):
        day = target - timedelta(days=offset)
        j = root / 'data' / str(day.year) / 'daily' / (str(day) + '.json')
        m = root / 'digests' / str(day.year) / 'daily' / (str(day) + '.md')
        if j.exists() or m.exists():
            continue
        generation = hashlib.sha256(('V41_SYNTHETIC_EMPTY_HISTORY:' + str(day)).encode()).hexdigest()[:32]
        markdown = f'# Synthetic test transport history {day}\n\nNo simulated observations.\n<!-- generation:{generation} -->\n'.encode()
        payload = {'metadata': {'target_date': str(day), 'generation_id': generation,
            'markdown_sha256': hashlib.sha256(markdown).hexdigest(),
            'quality_status': 'authoritative', 'publication_state': 'QA_PASSED',
            'structural_qa': {'status': 'PASS'}, 'semantic_qa': {'status': 'PASS'},
            'fixture_evidence': 'SYNTHETIC_EMPTY_HISTORY_NOT_REAL_OBSERVATION'}, 'records': []}
        j.parent.mkdir(parents=True, exist_ok=True); m.parent.mkdir(parents=True, exist_ok=True)
        j.write_text(json.dumps(payload), encoding='utf-8'); m.write_bytes(markdown)
