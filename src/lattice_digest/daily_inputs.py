"""Shared Daily input quality assessment for period aggregators."""
from __future__ import annotations
import json
from pathlib import Path
from lattice_digest.artifact_paths import daily_digest_path, legacy_daily_digest_candidates, resolve_existing
from lattice_digest.authority import semantic_qa, COMPLETE, DEGRADED, INCOMPLETE, PARTIAL


def assess_daily_input(path: Path, day, data_dir: Path, used_legacy: bool = False):
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
        payload = raw if isinstance(raw, dict) else {'records': raw, 'metadata': {}} if isinstance(raw, list) else {}
        structural = isinstance(payload.get('records'), list) and all(isinstance(r, dict) for r in payload['records'])
    except (OSError, ValueError):
        payload, structural = {'records': []}, False
    md_path, legacy_md = resolve_existing(daily_digest_path(day, data_dir.parent / 'digests'), legacy_daily_digest_candidates(day, data_dir.parent / 'digests'))
    md = md_path.read_text(encoding='utf-8') if md_path.exists() else None
    # Coverage/publication integrity and classification quality are orthogonal.
    # A historical B/80 conflict is exposed without changing a PASS pair into
    # a source-coverage failure. The default public verifier still rejects it.
    qa = semantic_qa(payload, md, check_classification=False)
    from lattice_digest.evidence_contract import classification_summary
    payload['_classification_quality'] = classification_summary(payload.get('records', []) if structural else [])
    quality = {
        'date': day.isoformat(), 'structural_valid': structural,
        'semantic_valid': qa['semantic_valid'], 'semantic_status': qa['status'],
        'source_degraded': not qa['derived_authority']['source_coverage']['complete'],
        'legacy_fallback': used_legacy or legacy_md,
        'authority_state': qa['derived_authority']['authority_state'],
        'defects': qa['issues'] + qa['unknown'],
    }
    quality['fully_valid'] = structural and quality['semantic_valid'] and not quality['source_degraded'] and not quality['legacy_fallback']
    payload['_daily_input_quality'] = quality
    if not isinstance(payload.get('records'), list):
        payload['records'] = []
    if not quality['semantic_valid']:
        payload['records'] = [{**r, 'daily_input_defects': quality['defects'], 'primary_today_new_eligible': False,
                               'freshness_bucket': 'date_uncertain_todo_verify'} for r in payload.get('records', []) if isinstance(r, dict)]
    return payload


def summarize_daily_inputs(loaded, missing):
    rows = [p['_daily_input_quality'] for _, p in loaded]
    total = sum(len(p.get('records', [])) for _, p in loaded)
    valid = [r['date'] for r in rows if r['fully_valid']]
    if missing or not rows or any(not r['structural_valid'] or r['semantic_status'] == 'UNKNOWN' for r in rows):
        state = INCOMPLETE
    elif any(r['semantic_status'] == 'FAIL' for r in rows):
        state = PARTIAL if total else INCOMPLETE
    elif len(valid) == len(rows):
        state = COMPLETE
    else:
        state = DEGRADED
    return {
        'authority_state': state, 'fully_valid_days': valid,
        'continuity_status': {'state': 'INCOMPLETE' if missing else 'INPUTS_PRESENT',
                              'missing_dates': list(missing),
                              'gap_causes': {day: 'UNKNOWN' for day in missing},
                              'mode': 'READ_ONLY_LOADED_INPUTS'},
        'structurally_valid_days': [r['date'] for r in rows if r['structural_valid']],
        'semantically_valid_days': [r['date'] for r in rows if r['semantic_valid']],
        'semantic_failed_days': [r['date'] for r in rows if r['semantic_status'] == 'FAIL'],
        'semantic_unknown_days': [r['date'] for r in rows if r['semantic_status'] == 'UNKNOWN'],
        'source_degraded_days': [r['date'] for r in rows if r['source_degraded']],
        'legacy_fallback_days': [r['date'] for r in rows if r['legacy_fallback']],
        'missing_days': missing, 'daily_input_quality': rows,
    }
