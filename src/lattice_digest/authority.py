"""One operational authority decision for the current (non-bilingual) product.

Completion, coverage, selection and QA are independent. Configuration is trusted
local input, never recovered from an artifact's self-reported authority label.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from lattice_digest.config import load_structured_file, project_root
from lattice_digest.source_roles import serialized_source_roles

POLICY_VERSION = 'daily-correctness-v1'
INCOMPLETE_ZERO_TEXT = '本次运行未形成满足严格入选条件的论文，但部分必需来源覆盖不完整，因此不能据此判断该时间窗口内没有值得关注的新研究。'
INCOMPLETE = 'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'
COMPLETE = 'AUTHORITATIVE_COMPLETE'
DEGRADED = 'AUTHORITATIVE_DEGRADED'
PARTIAL = 'PARTIAL_VERIFY_FIRST'


def configured_sources() -> list[dict[str, Any]]:
    return load_structured_file(project_root() / 'config/sources.yaml')['sources']


def source_complete(row: dict[str, Any]) -> bool:
    if str(row.get('health_status') or row.get('status') or '').lower() != 'green':
        return False
    if row.get('runtime_state') != 'complete':
        return False
    if any(row.get(k) for k in ['errors', 'error_type', 'error_message', 'circuit_open', 'requests_skipped', 'query_groups_failed']):
        return False
    total, success = row.get('query_groups_total', 0), row.get('query_groups_success', 0)
    return isinstance(total, int) and isinstance(success, int) and total >= 0 and success == total


def derive_authority(records: list[Any], source_health: list[dict[str, Any]] | None, *, source_configs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    configs = configured_sources() if source_configs is None else source_configs
    health = {str(r.get('source')): r for r in (source_health or []) if isinstance(r, dict)}
    required, optional, incomplete, degraded = [], [], [], []
    for config in configs:
        if not config.get('enabled', True):
            continue
        name = str(config.get('name') or config.get('type'))
        roles = serialized_source_roles(config)
        required_here = config.get('required_for_authority', any(r in {'DISCOVERY_PRIMARY', 'DISCOVERY_SECONDARY', 'CRITICAL_WATCH'} for r in roles))
        (required if required_here else optional).append(name)
        if not source_complete(health.get(name, {})):
            degraded.append(name)
            if required_here:
                incomplete.append(name)
    coverage_complete = bool(required) and not incomplete
    rows = [r if isinstance(r, dict) else r.model_dump() for r in records if isinstance(r, dict) or hasattr(r, 'model_dump')]
    from lattice_digest.publication_events import CORE_EVENTS
    event_contract=any(r.get('publication_event_type') for r in rows)
    selected = [r for r in rows if r.get('publication_event_type') in CORE_EVENTS] if event_contract else [r for r in rows if r.get('relevance_label') in {'A', 'B', 'C'}]
    decisive = any(r.get('security_impact_severity') == 'CRITICAL' and (r.get('freshness_bucket') == 'CRITICAL_NEWLY_OBSERVED_VERIFY_FIRST' or r.get('evidence_confidence') not in {'HIGH', 'high', 'verified'} or r.get('cross_day_event') == 'IDENTITY_UNCERTAIN') for r in selected)
    if decisive:
        authority = PARTIAL
    elif not coverage_complete and not selected:
        authority = INCOMPLETE
    elif degraded or not coverage_complete:
        authority = DEGRADED
    else:
        authority = COMPLETE
    return {
        'authority_policy_version': POLICY_VERSION,
        'authority_scope': 'configured-source Daily correctness; excludes gated bilingual release',
        'authority_state': authority,
        'source_coverage': {'complete': coverage_complete, 'required_sources': sorted(required), 'optional_sources': sorted(optional), 'incomplete_required_sources': sorted(incomplete), 'degraded_sources': sorted(degraded)},
        'selection_counts': {'selected': len(selected), 'primary_new': sum(r.get('primary_today_new_eligible') is True for r in selected)},
        'render_branch': ('ZERO_SELECTED_COMPLETE' if coverage_complete else 'ZERO_SELECTED_INCOMPLETE') if not selected else 'POSITIVE_SELECTED',
        'translation_status': 'TRANSLATION_BACKEND_SELECTION_REQUIRED',
        'bilingual_release_status': 'BILINGUAL_RELEASE_NOT_YET_AVAILABLE',
    }


def semantic_qa(payload: dict[str, Any], markdown: str | None, *, source_configs: list[dict[str, Any]] | None = None, candidate: bool = False, check_classification: bool = True) -> dict[str, Any]:
    records = payload.get('records')
    meta = payload.get('metadata') if isinstance(payload.get('metadata'), dict) else {}
    health = payload.get('source_health') or meta.get('source_health') or []
    decision = derive_authority(records if isinstance(records, list) else [], health, source_configs=source_configs)
    issues: list[str] = []
    unknown: list[str] = []
    if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
        issues.append('invalid_records')
    from lattice_digest.publication_events import POLICY_VERSION as EVENT_POLICY, ledger_issues
    if meta.get('publication_policy_version')==EVENT_POLICY:
        issues.extend(ledger_issues(payload,markdown))
        decision['selection_counts']=payload.get('publication_event_ledger',{}).get('counts',{})
    for key in ['authority_state', 'source_coverage', 'selection_counts', 'render_branch']:
        if key in meta and meta[key] != decision[key]:
            issues.append('authority_evidence_mismatch:' + key)
    stored_qa = meta.get('semantic_qa') if isinstance(meta.get('semantic_qa'), dict) else {}
    if stored_qa.get('status') == 'FAIL':
        issues.append('explicit_semantic_failure')
    if not candidate and (meta.get('authority_policy_version') != POLICY_VERSION or stored_qa.get('status') != 'PASS'):
        unknown.append('missing_or_legacy_semantic_evidence')
    if markdown is None:
        unknown.append('markdown_unavailable')
    else:
        if meta.get('markdown_sha256') and hashlib.sha256(markdown.encode('utf-8')).hexdigest() != meta['markdown_sha256']:
            issues.append('pair_content_mismatch')
        if meta.get('generation_id') and f"<!-- generation:{meta['generation_id']} -->" not in markdown:
            issues.append('pair_generation_mismatch')
        if decision['render_branch'] == 'ZERO_SELECTED_INCOMPLETE':
            # Structured branch is the first line of defence. This detects
            # contradictory prose anywhere, including later empty sections.
            sanitized = markdown.replace(INCOMPLETE_ZERO_TEXT, '').replace('最近 36 小时的检索覆盖不完整，当前不能据此断言没有相关新论文。', '')
            patterns = [r'可跳过', r'(?i)\b(?:safe to skip|nothing relevant today|no papers worth reading)\b', r'今[天日](?:未发现|没有|无)[^\n。]{0,60}(?:论文|新研究|研究进展)', r'(?i)no (?:relevant|new|worthwhile) (?:papers|research)']
            if any(re.search(p, sanitized) for p in patterns):
                issues.append('incomplete_zero_negative_or_skip_claim')
            if INCOMPLETE_ZERO_TEXT not in markdown:
                issues.append('incomplete_zero_caveat_missing')
            if any(s not in markdown for s in decision['source_coverage']['incomplete_required_sources']):
                issues.append('incomplete_sources_not_visible')
        if meta.get('authority_policy_version') == POLICY_VERSION and decision['authority_state'] not in markdown:
            issues.append('rendered_authority_missing')
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        from lattice_digest.evidence_contract import evidence_quality_issues
        if check_classification:
            issues.extend(evidence_quality_issues(record))
        if record.get('primary_today_new_eligible') is True and record.get('cross_day_event') in {'UNCHANGED_CROSS_DAY_DUPLICATE', 'GENUINE_NEW_VERSION', 'GENUINE_CONTENT_REVISION', 'METADATA_ONLY_UPDATE', 'IDENTITY_UNCERTAIN'}:
            issues.append('cross_day_false_primary')
    status = 'FAIL' if issues else ('UNKNOWN' if unknown else 'PASS')
    return {'status': status, 'semantic_valid': status == 'PASS', 'issues': sorted(set(issues)), 'unknown': unknown, 'derived_authority': decision}
