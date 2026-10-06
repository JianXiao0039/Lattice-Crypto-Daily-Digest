"""Bounded read-only audit. Missing artifacts alone never establish scheduler failure."""
from __future__ import annotations
import argparse
from datetime import date, timedelta
import json
from pathlib import Path

GAP_CAUSES = {'SCHEDULER_DID_NOT_TRIGGER', 'RUN_FAILED', 'ERROR_ONLY_ARTIFACT',
              'TARGET_DATE_RESOLUTION_MISMATCH', 'ARTIFACT_REMOVED', 'UNKNOWN'}


def audit_daily_continuity(data_dir: Path, start: date, end: date, *, trigger_records=()) -> dict:
    if end < start or (end - start).days >= 62:
        raise ValueError('continuity audit requires 1..62 days')
    digests = data_dir.parent / 'digests'
    rows = []
    day = start
    while day <= end:
        stamp = day.isoformat()
        jp = data_dir / str(day.year) / 'daily' / f'{stamp}.json'
        mp = digests / str(day.year) / 'daily' / f'{stamp}.md'
        ep = digests / str(day.year) / 'daily' / f'{stamp}-error.md'
        cause, status = 'UNKNOWN', 'MISSING'
        metadata = {}
        if jp.exists():
            try:
                payload = json.loads(jp.read_text(encoding='utf-8'))
                if not isinstance(payload, dict) or not isinstance(payload.get('records'), list):
                    raise ValueError('invalid Daily envelope')
                metadata = payload.get('metadata') or {}
                if not isinstance(metadata, dict):
                    raise ValueError('invalid Daily metadata')
                if metadata.get('target_date') and metadata['target_date'] != stamp:
                    cause, status = 'TARGET_DATE_RESOLUTION_MISMATCH', 'MISMATCH'
                else:
                    status = 'PAIR_PRESENT' if mp.exists() else 'JSON_WITHOUT_MARKDOWN'
            except (OSError, ValueError, TypeError):
                status = 'INVALID_JSON'
        elif ep.exists():
            status, cause = 'ERROR_ONLY', 'ERROR_ONLY_ARTIFACT'
        elif mp.exists():
            status = 'MARKDOWN_WITHOUT_JSON'
        facts = [dict(t) for t in trigger_records if t.get('target_date') == stamp]
        if status != 'PAIR_PRESENT' and cause == 'UNKNOWN':
            explicit = {t.get('gap_cause') for t in facts if t.get('evidence') and t.get('gap_cause') in GAP_CAUSES - {'UNKNOWN'}}
            if len(explicit) == 1:
                cause = explicit.pop()
        rows.append({'date': stamp, 'artifact_state': status, 'gap_cause': cause if status != 'PAIR_PRESENT' else None,
                     'json_present': jp.exists(), 'markdown_present': mp.exists(), 'error_present': ep.exists(),
                     'run_started_at': metadata.get('run_started_at', 'UNKNOWN'),
                     'trigger_kind': metadata.get('trigger_kind', 'UNKNOWN'), 'trigger_records': facts})
        day += timedelta(days=1)
    gaps = [r for r in rows if r['artifact_state'] != 'PAIR_PRESENT']
    return {'schema_version': 'daily-continuity-v2', 'audit_mode': 'READ_ONLY_CANONICAL',
            'start': start.isoformat(), 'end': end.isoformat(), 'expected_days': len(rows),
            'paired_days': len(rows) - len(gaps), 'gap_count': len(gaps), 'gaps': gaps, 'days': rows,
            'continuity_state': 'INCOMPLETE' if gaps else 'COMPLETE',
            'semantic_validation': 'NOT_PERFORMED_BY_CONTINUITY_AUDIT'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--start', type=date.fromisoformat, required=True)
    parser.add_argument('--end', type=date.fromisoformat, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(audit_daily_continuity(args.data_dir, args.start, args.end), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
