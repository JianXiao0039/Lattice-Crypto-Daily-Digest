"""Bounded, redacted evidence for rejected Daily candidates; never publication."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import traceback
from uuid import uuid4

from lattice_digest.evidence_contract import evidence_quality_issues, score_to_label, source_topics

MAX_CANDIDATE_BYTES = 8 * 1024 * 1024
SENSITIVE = re.compile(r'(?i)(?:secret|password|passwd|credential|authorization|cookie|api[_-]?key|access[_-]?token|refresh[_-]?token|(?:^|[_-])token(?:$|[_-]))')


class DailyPublicationQAError(ValueError):
    """A rejection retains its original decisions even if audit persistence fails."""
    def __init__(self, details: dict, diagnostic_path: Path | None, persistence_error: str | None = None):
        self.details = details
        self.issues = details['issues']
        self.diagnostic_path = diagnostic_path
        self.persistence_error = persistence_error
        codes = sorted({issue['issue_code'] for issue in self.issues})
        super().__init__('Daily publication QA failed: ' + ', '.join(codes)
                         + ('; diagnostic=' + str(diagnostic_path) if diagnostic_path else '; diagnostic persistence failed'))


def redact(value, *, secrets: tuple[str, ...] | None = None):
    if secrets is None:
        secrets = tuple(v for k, v in os.environ.items() if SENSITIVE.search(k) and len(v) >= 4)
    if isinstance(value, dict):
        return {str(k): '[REDACTED]' if SENSITIVE.search(str(k)) or str(k) in {'body_preview', 'response_body_preview', 'headers', 'http_response_body'}
                else redact(v, secrets=secrets) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item, secrets=secrets) for item in value]
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, '[REDACTED]')
        value = re.sub(r'(?i)\bBearer\s+[^\s,;"<>]+', 'Bearer [REDACTED]', value)
        value = re.sub(r'(?i)((?:api[_-]?key|token|password|secret|authorization)\s*[=:]\s*)[^\s&;,"<>]+', r'\1[REDACTED]', value)
        value = re.sub(r'(https?://)[^/\s:@]+:[^/\s@]+@', r'\1[REDACTED]@', value)
        value = value.split('; body_preview=', 1)[0]
        return value[:32768]
    return value


def issue_details(payload, markdown, structural, semantic, cross_day):
    """Describe decisions already made by QA; this function cannot allow a pair."""
    issues = []
    def add(code, stage, field, expected, observed):
        issues.append({'issue_code': code, 'issue_severity': 'ERROR', 'qa_stage': stage,
                       'affected_field': field, 'expected_value': expected, 'observed_value': observed,
                       'artifact_path': 'candidate.json' if field != 'markdown' else 'candidate.md'})
    if not structural:
        add('STRUCTURAL_QA_FAILED', 'structural', 'records/metadata.target_date/markdown',
            'list records, matching target date, Markdown starts with # ',
            {'records_type': type(payload.get('records')).__name__, 'target_date': payload.get('metadata', {}).get('target_date'), 'markdown_heading': markdown[:100]})
    field_map = {
        'RELEVANCE_SCORE_LABEL_INCONSISTENT': ('relevance_score', 'relevance_label'),
        'ONTOLOGY_COANCHOR_POLICY_VIOLATION': ('relevance_score', 'evidence_items', 'source_concept_ids'),
        'INFERENCE_TO_EVIDENCE_FEEDBACK': ('source_evidence_terms', 'source_concept_ids', 'source_taxonomy_tags'),
        'GENERATED_PROSE_AS_SOURCE_EVIDENCE': ('evidence_items',),
        'UNSUPPORTED_DIRECT_RESEARCH_RELATION': ('research_relations',),
        'SOURCE_HEALTH_PROVENANCE_MISSING_FOR_SELECTED': ('source_health', 'source_health_provenance'),
    }
    described = set()
    for index, row in enumerate(payload.get('records', [])):
        if not isinstance(row, dict):
            continue
        for code in evidence_quality_issues(row):
            if code not in semantic.get('issues', []):
                continue
            fields = field_map.get(code, ())
            observed = {name: row.get(name) for name in fields}
            expected = 'source-grounded values required by evidence contract'
            if code == 'RELEVANCE_SCORE_LABEL_INCONSISTENT':
                try:
                    expected = {'relevance_label': score_to_label(row.get('relevance_score'))}
                except (ValueError, TypeError):
                    expected = 'valid score and corresponding A/B/C/D label'
            elif code == 'UNSUPPORTED_DIRECT_RESEARCH_RELATION':
                expected = {'source_topics': sorted(source_topics(row)), 'direct_evidence_types': ['SOURCE_EXPLICIT', 'SOURCE_STRUCTURAL', 'SOURCE_RELATION']}
                observed = [relation for relation in row.get('research_relations', []) if relation.get('strength') in {'DIRECT', 'STRUCTURAL'} and (relation.get('topic') not in source_topics(row) or relation.get('evidence_type') not in expected['direct_evidence_types'])]
            add(code, 'semantic', f'records[{index}].' + ','.join(fields), expected, observed)
            described.add(code)
    for code in semantic.get('issues', []):
        if code not in described:
            field = code.split(':', 1)[-1] if code.startswith('authority_evidence_mismatch:') else 'markdown'
            add(code, 'semantic', field, semantic.get('derived_authority', {}).get(field, 'semantic QA invariant'), payload.get('metadata', {}).get(field) if field != 'markdown' else 'contradiction or missing contract text; inspect candidate.md')
    for item in cross_day:
        add(item['issue_code'], 'cross_day', f"records[{item['record_index']}].primary_today_new_eligible", 'NEW_DISTINCT_PAPER', item['event'])
    for code in semantic.get('unknown', []):
        add(code, 'semantic', 'metadata.semantic_qa', 'PASS with complete QA evidence', 'UNKNOWN')
    return issues


def reject_daily_candidate(audit_root, payload, markdown, structural, semantic, cross_day):
    meta = payload.get('metadata', {})
    run_id = meta.get('run_id') or Path(str(meta.get('runtime_journal') or '')).stem or meta.get('generation_id')
    details = {'schema_version': 1, 'publication_state': 'QA_REJECTED_DIAGNOSTIC_ONLY',
               'qa_stage': 'publication', 'qa_decision': 'REJECT', 'run_id': run_id,
               **{key: meta.get(key) for key in ('target_date', 'coverage_start', 'coverage_end', 'run_mode', 'runtime_git_head', 'runtime_code_state', 'recovery_executed_at', 'original_missing_reason')},
               'recorded_at': datetime.now(timezone.utc).isoformat(),
               'structural_qa': {'status': 'PASS' if structural else 'FAIL'},
               'semantic_qa': semantic, 'cross_day_qa': {'status': 'FAIL' if cross_day else 'PASS', 'issues': cross_day},
               'issues': issue_details(payload, markdown, structural, semantic, cross_day),
               'source_provenance': payload.get('source_health', []),
               'exception_type': 'DailyPublicationQAError',
               'bounded_traceback': traceback.format_stack(limit=8),
               'original_candidate_sha256': {'json': hashlib.sha256(json.dumps(payload, ensure_ascii=False, indent=2).encode()).hexdigest(), 'markdown': hashlib.sha256(markdown.encode()).hexdigest()}}
    details = redact(details)
    details['candidate_redacted'] = True
    details['issue_detail_count'] = len(details['issues'])
    details['issue_codes'] = sorted({issue['issue_code'] for issue in details['issues']})
    if len(json.dumps(details, ensure_ascii=False).encode('utf-8')) > MAX_CANDIDATE_BYTES:
        # Every decision/code survives; over-budget repeated record detail is
        # represented by counts and one bounded example per code.
        from collections import Counter
        details['issue_counts'] = dict(Counter(issue['issue_code'] for issue in details['issues']))
        examples = {}
        for issue in details['issues']:
            examples.setdefault(issue['issue_code'], issue)
        details['issues'] = list(examples.values())
        details['issue_details_complete'] = False
        details['source_provenance'] = [{k: row.get(k) for k in ('source', 'health_status', 'runtime_state', 'error_type')} for row in payload.get('source_health', []) if isinstance(row, dict)][:100]
    else:
        details['issue_details_complete'] = True
    candidate = redact(payload)
    candidate.setdefault('metadata', {})['publication_state'] = 'QA_REJECTED_DIAGNOSTIC_ONLY'
    content = json.dumps(candidate, ensure_ascii=False, indent=2).encode('utf-8')
    md_content = redact(markdown).encode('utf-8')
    details['candidate_complete'] = len(content) + len(md_content) <= MAX_CANDIDATE_BYTES
    if not details['candidate_complete']:
        # Retain decisions and bounded offending fields; never retain an unbounded tree.
        small_meta = {key: candidate.get('metadata', {}).get(key) for key in ('target_date', 'coverage_start', 'coverage_end', 'run_mode', 'publication_state')}
        content = json.dumps({'metadata': small_meta, 'records': [], 'diagnostic_only': True}, ensure_ascii=False, indent=2).encode('utf-8')
        md_content = md_content[:MAX_CANDIDATE_BYTES // 2]
    directory = Path(audit_root) / 'audits/daily-publication-failures' / uuid4().hex
    try:
        directory.mkdir(parents=True)
        artifacts = {}
        for name, body in [('candidate.json', content), ('candidate.md', md_content)]:
            with (directory / name).open('xb') as stream:
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
            artifacts[name] = {'path': str(directory / name), 'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body)}
        details['artifacts'] = artifacts
        for issue in details['issues']:
            artifact = artifacts.get(issue['artifact_path'], artifacts['candidate.json'])
            issue['artifact_path'] = artifact['path']
            issue['candidate_artifact_sha256'] = artifact['sha256']
        path = directory / 'failure.json'
        with path.open('x', encoding='utf-8') as stream:
            json.dump(details, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise DailyPublicationQAError(details, None, type(exc).__name__) from exc
    raise DailyPublicationQAError(details, path)
