"""Owner-only, hash-guarded replacement of evidence-derived report pairs.

No discovery, database writes, scheduler changes or implicit legacy conversion.
Per-file replacement is atomic; ordinary I/O failure rolls back both files.
A journal and pair hash make a crash between replacements detectable.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4
from zoneinfo import ZoneInfo

from lattice_digest.artifact_paths import daily_data_path, daily_digest_path, weekly_data_path, weekly_digest_path, monthly_data_path, monthly_digest_path
from lattice_digest.authority import semantic_qa
from lattice_digest.digest import generate_markdown
from lattice_digest.models import PaperRecord
from lattice_digest.promotion_history import load_promotion_history, classify_event
from lattice_digest.public_contract import public_preflight, _reject_redirects
from lattice_digest.runtime_provenance import runtime_provenance, public_runtime_allowed
from lattice_digest.weekly_synthesis import build_weekly_synthesis, render_markdown as render_weekly, _strip_private_weekly
from lattice_digest.monthly_synthesis import build_monthly_synthesis, render_markdown as render_monthly
from scripts.verify_durable_artifacts import verify_daily, verify_weekly, verify_monthly

SOURCE_FIELDS = ('title','authors','abstract','conclusion','source','source_url','source_urls','paper_id','doi','arxiv_id','eprint_id','venue',
    'publication_date','publication_timestamp','publication_date_kind','preprint_first_posted_at','announcement_date','announcement_timestamp',
    'update_date','update_timestamp','update_date_kind','source_version_timestamp','first_seen_at','first_seen_date')
REPAIR_NOTE = '\n\n<!-- verified-report-repair -->\n- 历史报告修复：保留原始来源记录与观察时间；缺失的旧版出版事件证据仍为 UNKNOWN，不能视为新观察的当前模式事实。\n'

# A missing-health marker describes absent evidence, never a provider attempt.
LEGACY_HEALTH = [{'source': 'UNKNOWN_LEGACY_PROVIDER_HEALTH',
    'health_status': 'unknown', 'runtime_state': 'NOT_RECORDED',
    'evidence_state': 'UNRESOLVED_EVIDENCE', 'requests_attempted': 'N/A'}]


def prepare_legacy_candidate(original: list, original_sha256: str, target: str) -> dict:
    """Source-only derivation; observation dates and health are explicitly absent."""
    from lattice_digest.evidence_contract import bind_source_evidence
    fields = ('scientific_scope', 'source_relation_roles', 'lattice_relevance_qualified', 'scope_reason',
        'evidence_policy_version', 'evidence_items', 'consequence_edges', 'source_concept_ids',
        'source_evidence_terms', 'source_taxonomy_tags', 'ontology_neighbor_tags', 'research_relations',
        'user_research_hypotheses', 'source_limitations', 'relevance_scope', 'relevance_score', 'relevance_label', 'reading_priority')
    rows = []
    for original_row in original:
        p = PaperRecord(**{k:v for k,v in original_row.items() if k in PaperRecord.model_fields})
        bound = bind_source_evidence(p).model_dump(mode='json')
        row = dict(original_row)
        row.update({k: bound[k] for k in fields})
        row.update(primary_today_new_eligible=False, primary_action_allowed=False,
            publication_event_type='', freshness_bucket='date_uncertain_todo_verify',
            source_health='unknown', source_health_provenance={
                str(original_row.get('source') or 'UNKNOWN'): {
                    'health_status': 'unknown', 'runtime_state': 'NOT_RECORDED', 'evidence_state': 'UNRESOLVED_EVIDENCE'}})
        rows.append(row)
    meta = {'target_date': target, 'target_date_basis': 'CANONICAL_FILENAME',
        'legacy_schema_restatement': 'SOURCE_PRESERVING_UNKNOWN_WINDOW',
        'legacy_original_json_sha256': original_sha256,
        'coverage_start': None, 'coverage_end': None, 'run_date': None, 'run_mode': None,
        'quality_status': None, 'publication_policy_version': None,
        'generation_id': uuid4().hex, 'repair_executed_at': datetime.now(timezone.utc).isoformat(),
        'publication_event_semantics': 'UNRESOLVED_LEGACY_ARCHIVE_NOT_CURRENT_EVENT_FACT',
        'scientific_claim_verification': 'UNRESOLVED_EVIDENCE'}
    from lattice_digest.authority import derive_authority
    meta.update(derive_authority(rows, LEGACY_HEALTH))
    payload = {'records': rows, 'metadata': meta, 'source_health': [dict(item) for item in LEGACY_HEALTH],
        'warnings': ['历史来源重述；未重新采集，缺失原时窗口与提供者健康。']}
    markdown = render_daily(payload, target)
    qa = semantic_qa(payload, markdown.decode('utf-8'), candidate=True)
    if qa['status'] != 'PASS': raise ValueError('legacy candidate QA failed: ' + json.dumps(qa))
    meta['semantic_qa'] = {k:v for k,v in qa.items() if k != 'derived_authority'}
    meta['markdown_sha256'] = digest(render_daily(payload, target))
    return payload


def validate_legacy_wrapper(original: list, candidate: dict, target: str) -> None:
    """Permit an audited restatement while retaining unknown historical facts."""
    if any(not isinstance(row, dict) for row in original):
        raise ValueError('invalid legacy source rows')
    if _source_projection(original) != _source_projection(candidate.get('records', [])):
        raise ValueError('legacy source records, identities or timestamps changed')
    meta = candidate.get('metadata', {})
    if meta.get('legacy_schema_restatement') != 'SOURCE_PRESERVING_UNKNOWN_WINDOW':
        raise ValueError('legacy restatement marker missing')
    if meta.get('target_date') != target or meta.get('target_date_basis') != 'CANONICAL_FILENAME':
        raise ValueError('legacy target ownership missing')
    if any(meta.get(key) is not None for key in ('coverage_start', 'coverage_end', 'run_date', 'publication_policy_version')):
        raise ValueError('legacy missing window or observation cannot be invented')
    if 'publication_event_ledger' in candidate or candidate.get('source_health') != LEGACY_HEALTH:
        raise ValueError('legacy publication events or provider health cannot be invented')
    for row in candidate['records']:
        if row.get('primary_today_new_eligible') or row.get('primary_action_allowed') or row.get('publication_event_type'):
            raise ValueError('legacy restatement cannot promote publication events')

def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def prepare_missing_candidate(target: str) -> dict:
    """An explicit evidence gap, without invented discovery or window counts."""
    date.fromisoformat(target)
    payload = prepare_legacy_candidate([], digest(b'[]'), target)
    meta = payload['metadata']
    meta.pop('legacy_original_json_sha256')
    meta.update(historical_missing_report='ORIGINAL_WINDOW_AND_OBSERVATIONS_UNKNOWN',
                original_failed_discovery_counts='N/A', original_execution_status='UNKNOWN_NO_SUCCESS_PAIR',
                source_snapshot_kind='NO_RECOVERABLE_ORIGINAL_PROVIDER_SNAPSHOT',
                recovery_executed_at=datetime.now(timezone.utc).isoformat())
    meta['markdown_sha256'] = digest(render_daily(payload, target))
    return payload


def pair_paths(root: Path, kind: str, target: str) -> tuple[Path, Path]:
    if kind == 'daily':
        day = date.fromisoformat(target)
        return daily_data_path(day,root/'data'), daily_digest_path(day,root/'digests')
    if kind == 'weekly':
        year, week = map(int,target.split('-W'))
        date.fromisocalendar(year,week,1)
        return weekly_data_path(target,root=root/'data'), weekly_digest_path(target,root=root/'digests')
    if kind == 'monthly':
        datetime.strptime(target,'%Y-%m')
        return monthly_data_path(target,root=root/'data'), monthly_digest_path(target,root=root/'digests')
    raise ValueError('unsupported report kind')

def checked_path(path: Path, within: Path) -> Path:
    path=path.absolute()
    _reject_redirects(path)
    if not path.resolve().is_relative_to(within.resolve()):
        raise ValueError('repair path escapes authorized root')
    return path

def render_daily(payload: dict, target: str) -> bytes:
    meta=payload['metadata']
    if meta.get('legacy_schema_restatement') == 'SOURCE_PRESERVING_UNKNOWN_WINDOW':
        return render_legacy_archive(payload, target)
    rows=[PaperRecord(**{k:v for k,v in row.items() if k in PaperRecord.model_fields}) for row in payload['records']]
    rendered=generate_markdown(rows,date.fromisoformat(target),int(meta.get('filtered_count',0)),
        payload.get('source_health',[]),payload.get('warnings',[]),meta.get('since_window','36h'),
        {**meta,'_publication_payload':payload})
    rendered+=f"\n<!-- generation:{meta['generation_id']} -->\n"
    # Source warnings can contain Windows CRLF. Preserve their original JSON
    # bytes, but publish a single Markdown newline convention for hash readers.
    return (rendered+REPAIR_NOTE).replace('\r\n','\n').replace('\r','\n').encode('utf-8')


def render_legacy_archive(payload: dict, target: str) -> bytes:
    """No floating/date-only freshness or generated old prose in a restatement."""
    from lattice_digest.authority import INCOMPLETE_ZERO_TEXT
    meta = payload['metadata']; rows = payload['records']
    lines = [f'# 格密码论文日报：{target}（历史来源重述）', '', '## 今日结论', '',
        '这是已保存来源的历史重述，没有执行该历史日期的重新观察。原始覆盖窗口、运行时间和提供者健康均未记录，保持 UNKNOWN。',
        '历史记录数量不是当日新论文数量；本报告未验证任何当日首次出版或修订事件。',
        f"覆盖权威：{meta['authority_state']}；出版事实核验：UNRESOLVED_EVIDENCE。",
        INCOMPLETE_ZERO_TEXT if meta.get('render_branch') == 'ZERO_SELECTED_INCOMPLETE' else '当日新增事件数为 N/A；来源记录仅用于历史归档与后续核验。',
        '', '## A 类：今日必读格密码论文', '', '未建立当日事件列表；下方仅为来源支持的历史记录。',
        '', '## B 类：值得跟踪论文', '', '未建立当日事件列表。',
        '', '## C 类：可选关注 / 背景启发', '', '背景分类保留在历史审计附录。',
        '', '## D 类过滤说明', '', f"历史来源中 D 类记录 {sum(r.get('relevance_label') == 'D' for r in rows)} 条；不纳入阅读推荐。",
        '', '## 今日统计', '', f'已保存历史观察记录：{len(rows)}；新增/修订事件：N/A；来源请求：N/A（未记录）。',
        '', '## 明日跟踪建议', '', '先核验原论文与历史来源窗口；不能由本次重述断言原日报日期没有新研究。',
        '', '## 今日一句话总结', '', '历史来源已保留，缺失覆盖与出版事件证据尚未补齐。',
        '', '## 历史来源审计附录', '', 'TRANSLATION_BACKEND_SELECTION_REQUIRED / BILINGUAL_RELEASE_NOT_YET_AVAILABLE',
        '中文标题和摘要未完成核验翻译；以下原文内容属于来源作者主张，不能视为独立验证的定理或密码攻击结论。',
        '未记录健康的必需来源：' + ', '.join(meta['source_coverage']['incomplete_required_sources'])]
    if meta.get('historical_missing_report'):
        lines += ['', '## 历史缺口恢复说明', '',
            '本文件仅恢复明确的不完整状态，未恢复原时采集覆盖或论文发现。原始执行状态 UNKNOWN；原始发现数量 N/A；原始覆盖窗口 UNKNOWN。',
            '已保存原时观察：无可恢复证据；不能解释为该日发现零篇论文。未创建出版事件账本，未将后续观察提前为历史事实。',
            '后续保存的文献线索另存于独立恢复记录；不作为该日首次观察或新增事件。',
            f"恢复记录生成时间（实际）：{meta['recovery_executed_at']}"]
    for index, row in enumerate(rows):
        if row.get('relevance_label') == 'D': continue
        lines += ['', f"### 历史记录 {index + 1}：{row.get('title', 'UNKNOWN')}", '',
            f"- 来源：{row.get('source', 'UNKNOWN')}；URL：{row.get('source_url', 'UNKNOWN')}",
            f"- paper ID：{row.get('paper_id') or 'UNKNOWN'}；arXiv：{row.get('arxiv_id') or 'UNKNOWN'}；ePrint：{row.get('eprint_id') or 'UNKNOWN'}；DOI：{row.get('doi') or 'UNKNOWN'}",
            f"- 历史来源分类：{row.get('relevance_label')} / {row.get('relevance_score')}；范围：{row.get('scientific_scope') or 'UNKNOWN'}",
            '- 阅读动作：verify_first；TODO_VERIFY 原论文主张、参数及证明，不升级为已验证安全结论。',
            '- 作者：' + ', '.join(row.get('authors', [])),
            f"- 来源保存的出版日期：{row.get('publication_date') or 'UNKNOWN'}；更新日期：{row.get('update_date') or 'UNKNOWN'}；原时观察：UNKNOWN。",
            '', '原摘要（作者主张，未独立核验；不是已完成的中文翻译）：', '', str(row.get('abstract') or 'UNKNOWN')]
    lines += ['', f"<!-- generation:{meta['generation_id']} -->", REPAIR_NOTE]
    return '\n'.join(lines).replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')

def _source_projection(rows):
    return [{k:r[k] for k in SOURCE_FIELDS if k in r} for r in rows]


def render_period_repair(payload: dict, render) -> bytes:
    """Preserve legacy repairs and the newer durable generation-pair contract."""
    import re
    generation=payload.get('metadata',{}).get('generation_id')
    text=render(payload)+REPAIR_NOTE
    if not generation:return text.encode('utf-8')
    if not isinstance(generation,str) or not re.fullmatch(r'[0-9a-f]{32}',generation):
        raise ValueError('invalid period repair generation identity')
    text+='\n<!-- generation:'+generation+' -->\n'
    return text.replace('\r\n','\n').replace('\r','\n').encode('utf-8')

def validate_candidate(root: Path, candidate_root: Path, kind: str, target: str, original: dict, candidate: dict, markdown: bytes) -> dict:
    if kind=='daily':
        if isinstance(original, list):
            validate_legacy_wrapper(original, candidate, target)
            original = {'records': original, 'source_health': LEGACY_HEALTH, 'metadata': {}}
        if not isinstance(original,dict) or not isinstance(original.get('records'),list):
            raise ValueError('unreconciled legacy schema cannot be automatically repaired')
        if _source_projection(original['records']) != _source_projection(candidate.get('records',[])):
            raise ValueError('source records, identities or timestamps changed')
        if original.get('source_health',[]) != candidate.get('source_health',[]):
            raise ValueError('original provider health changed')
        old=original.get('metadata',{});meta=candidate.get('metadata',{})
        for key in ('coverage_start','coverage_end','publication_policy_version','quality_status','run_date','run_mode'):
            if old.get(key)!=meta.get(key):
                from lattice_digest.publication_events import LEGACY_POLICY_VERSION, POLICY_VERSION
                migration=meta.get('classification_policy_migration',{})
                permitted=(key=='publication_policy_version' and old.get(key)==LEGACY_POLICY_VERSION
                    and meta.get(key)==POLICY_VERSION and migration.get('from')==LEGACY_POLICY_VERSION
                    and migration.get('to')==POLICY_VERSION and migration.get('original_generation_id')==old.get('generation_id'))
                if not permitted:raise ValueError('original coverage or policy changed: '+key)
        if meta.get('target_date')!=target:raise ValueError('candidate target date mismatch')
        if markdown!=render_daily(candidate,target):raise ValueError('candidate Markdown is not the authorized renderer output')
        qa=semantic_qa(candidate,markdown.decode('utf-8'))
        if qa['status']!='PASS':raise ValueError('candidate semantic QA failed: '+json.dumps(qa))
        prior=[]
        if any(r.get('primary_today_new_eligible') for r in candidate['records']):
            prior,_=load_promotion_history(root/'data',date.fromisoformat(target))
        for row in candidate['records']:
            event,_=classify_event(row,prior)
            if row.get('primary_today_new_eligible') and event!='NEW_DISTINCT_PAPER' and row.get('publication_event_type')!='primary_publication_events':
                raise ValueError('cross-day false primary')
        durable=verify_daily(candidate_root,target)
    else:
        if kind=='weekly':
            year,week=map(int,target.split('-W'));start=date.fromisocalendar(year,week,1)
            expected=_strip_private_weekly(build_weekly_synthesis(root/'data',start,start+timedelta(days=6),datetime.fromisoformat(candidate['generated_at'])))
            render=render_weekly;durable=verify_weekly(candidate_root,target)
        else:
            first=datetime.strptime(target,'%Y-%m').date()
            today=datetime.now(ZoneInfo('Asia/Singapore')).date()
            following=first.replace(year=first.year+1,month=1) if first.month==12 else first.replace(month=first.month+1)
            if following>today:raise ValueError('monthly period has not ended')
            expected=build_monthly_synthesis(root/'data',target,generated_at=datetime.fromisoformat(candidate['generated_at']))
            render=render_monthly;durable=verify_monthly(candidate_root,target)
        proposed={k:v for k,v in candidate.items() if k not in ('metadata','repair_receipt')}
        actual={k:v for k,v in expected.items() if k not in ('metadata','repair_receipt')}
        if proposed!=actual:raise ValueError('period data differs from current canonical input derivation')
        if original.get('metadata',{}).get('generation_id') and not candidate.get('metadata',{}).get('generation_id'):
            raise ValueError('modern period repair cannot discard generation contract')
        expected_render={**expected,'metadata':candidate.get('metadata',{})}
        if markdown!=render_period_repair(expected_render,render):
            raise ValueError('period Markdown differs from source-derived renderer')
        if candidate.get('metadata',{}).get('generation_id'):
            from lattice_digest.period_delivery import verify_period_pair
            candidate_json,candidate_markdown=pair_paths(candidate_root,kind,target)
            if json.loads(candidate_json.read_bytes())!=candidate or candidate_markdown.read_bytes()!=markdown:
                raise ValueError('period candidate bytes differ from validated promotion contents')
            verify_period_pair(candidate_json,candidate_markdown)
        qa=durable.get('semantic_qa',{})
    if durable.get('status')!='verified':raise ValueError('durable verifier failed: '+json.dumps(durable))
    return {'structural':'PASS','semantic':qa['status'],'cross_day':'PASS','durable':'PASS',
            'authority_state':durable.get('authority_state')}

def _promote(paths: tuple[Path,Path], contents: tuple[bytes,bytes], expected: tuple[str,str], evidence: Path) -> dict:
    original=tuple(p.read_bytes() for p in paths)
    if tuple(map(digest,original))!=expected:raise ValueError('original pair hash changed; refuse replacement')
    evidence.mkdir(parents=True,exist_ok=False)
    for name,data in zip(('original.json.gz','original.md.gz'),original):
        with gzip.open(evidence/name,'wb') as stream:stream.write(data)
        with gzip.open(evidence/name,'rb') as stream:
            if stream.read()!=data:raise ValueError('original snapshot restoration failed')
    journal={'state':'PREPARED','targets':[str(p) for p in paths],'original_sha256':list(expected),
             'candidate_sha256':list(map(digest,contents)),'pair_atomicity':'PER_FILE_ATOMIC; JOURNALED_PAIR; ORDINARY_ERROR_ROLLBACK'}
    receipt=evidence/'receipt.json';receipt.write_text(json.dumps(journal,indent=2),encoding='utf-8')
    temps=[];promoted=[]
    try:
        for p,data in zip(paths,contents):
            fd,name=tempfile.mkstemp(prefix='.report-repair-',dir=p.parent);temps.append(Path(name))
            with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        if tuple(digest(p.read_bytes()) for p in paths)!=expected:raise ValueError('pair changed during candidate staging')
        for index,(temp,p) in enumerate(zip(temps,paths)):
            os.replace(temp,p);promoted.append(index)
        if tuple(digest(p.read_bytes()) for p in paths)!=tuple(map(digest,contents)):raise OSError('promoted pair verification failed')
    except (OSError,ValueError):
        for index in reversed(promoted):
            fd,name=tempfile.mkstemp(prefix='.report-rollback-',dir=paths[index].parent)
            with os.fdopen(fd,'wb') as stream:stream.write(original[index]);stream.flush();os.fsync(stream.fileno())
            os.replace(name,paths[index])
        journal['state']='ROLLED_BACK';receipt.write_text(json.dumps(journal,indent=2),encoding='utf-8')
        raise
    finally:
        for p in temps:p.unlink(missing_ok=True)
    journal['state']='PROMOTED';receipt.write_text(json.dumps(journal,indent=2),encoding='utf-8')
    return journal

def _create_missing(paths: tuple[Path,Path], contents: tuple[bytes,bytes], evidence: Path) -> dict:
    """Create absent files without replacement; rollback only our unchanged links."""
    if any(p.exists() for p in paths): raise ValueError('missing pair target already exists')
    evidence.mkdir(parents=True, exist_ok=False)
    journal={'state':'PREPARED','targets':[str(p) for p in paths], 'original_sha256':[None,None],
             'candidate_sha256':list(map(digest,contents)),
             'pair_atomicity':'NO_REPLACE_LINK_INSTALL; JOURNALED_PAIR; ORDINARY_ERROR_ROLLBACK'}
    receipt=evidence/'receipt.json';receipt.write_text(json.dumps(journal,indent=2),encoding='utf-8')
    temps=[];installed=[]
    try:
        for p,data in zip(paths,contents):
            p.parent.mkdir(parents=True,exist_ok=True)
            fd,name=tempfile.mkstemp(prefix='.missing-report-',dir=p.parent);temps.append(Path(name))
            with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        for index,(temp,p) in enumerate(zip(temps,paths)):
            os.link(temp,p)
            installed.append(index)
        if tuple(digest(p.read_bytes()) for p in paths)!=tuple(map(digest,contents)):
            raise ValueError('new pair changed before final verification')
    except (OSError,ValueError):
        retained=[]
        for index in reversed(installed):
            p=paths[index]
            if p.exists() and p.samefile(temps[index]) and p.read_bytes()==contents[index]:p.unlink()
            elif p.exists():retained.append(str(p))
        journal['state']='ROLLBACK_BLOCKED_BY_CONCURRENT_CHANGE' if retained else 'ROLLED_BACK'
        journal['retained_concurrent_changes']=retained
        receipt.write_text(json.dumps(journal,indent=2),encoding='utf-8')
        raise
    finally:
        for temp in temps:temp.unlink(missing_ok=True)
    journal['state']='PROMOTED';receipt.write_text(json.dumps(journal,indent=2),encoding='utf-8')
    return journal


def create_missing_pair(root: Path, item: dict, evidence_root: Path, *, execute: bool=False) -> dict:
    kind,target=item['kind'],item['target']
    if kind!='daily':raise ValueError('unknown-window gap creation supports Daily only')
    if date.fromisoformat(target)>datetime.now(ZoneInfo('Asia/Singapore')).date():raise ValueError('future Daily')
    paths=pair_paths(root,kind,target)
    for p in paths:checked_path(p,root)
    candidate_root=checked_path(Path(item['candidate_root']),root/'.ops/scratch')
    candidates=pair_paths(candidate_root,kind,target)
    for p in candidates:checked_path(p,candidate_root)
    checked_path(evidence_root,root/'.ops/evidence')
    contents=tuple(p.read_bytes() for p in candidates)
    if tuple(map(digest,contents))!=(item['candidate_json_sha256'],item['candidate_markdown_sha256']):raise ValueError('candidate hash mismatch')
    payload=json.loads(contents[0]);meta=payload.get('metadata',{})
    if (payload.get('records')!=[] or 'publication_event_ledger' in payload or payload.get('source_health')!=LEGACY_HEALTH
        or meta.get('target_date')!=target or meta.get('target_date_basis')!='CANONICAL_FILENAME'
        or meta.get('legacy_schema_restatement')!='SOURCE_PRESERVING_UNKNOWN_WINDOW'
        or meta.get('historical_missing_report')!='ORIGINAL_WINDOW_AND_OBSERVATIONS_UNKNOWN'
        or meta.get('original_failed_discovery_counts')!='N/A'
        or meta.get('original_execution_status')!='UNKNOWN_NO_SUCCESS_PAIR'
        or meta.get('source_snapshot_kind')!='NO_RECOVERABLE_ORIGINAL_PROVIDER_SNAPSHOT'
        or any(meta.get(k) is not None for k in ('coverage_start','coverage_end','run_date','run_mode','publication_policy_version','quality_status','legacy_original_json_sha256','recovery_requested_window','original_requested_window'))):
        raise ValueError('missing historical evidence cannot become invented observations or coverage')
    recovered=datetime.fromisoformat(meta['recovery_executed_at'])
    if recovered.tzinfo is None:raise ValueError('recovery observation time requires timezone')
    if contents[1]!=render_daily(payload,target):raise ValueError('missing candidate is not authorized renderer output')
    durable=verify_daily(candidate_root,target)
    if durable['status']!='verified':raise ValueError('missing candidate durable QA failed')
    paths[0].parent.mkdir(parents=True,exist_ok=True)
    lock=paths[0].with_name('.'+paths[0].stem+'.report-repair.lock');_reject_redirects(lock)
    stream=lock.open('x',encoding='utf-8')
    try:
        with stream:
            if any(p.exists() for p in paths):raise ValueError('missing pair target already exists')
            qa={'structural':'PASS','semantic':'PASS','durable':'PASS','cross_day':'NO_OBSERVATIONS_CREATED',
                'authority_state':durable['authority_state']}
            if not execute:return {'kind':kind,'target':target,'status':'QA_PASSED_NOT_PROMOTED','qa':qa}
            result=_create_missing(paths,contents,evidence_root/(kind+'-'+target+'-'+uuid4().hex))
            return {'kind':kind,'target':target,'status':'PROMOTED_INCOMPLETE_HISTORY','qa':qa,**result}
    finally:lock.unlink(missing_ok=True)


def repair_pair(root: Path, item: dict, evidence_root: Path, *, execute: bool=False) -> dict:
    if item.get('operation')=='CREATE_INCOMPLETE_HISTORY':return create_missing_pair(root,item,evidence_root,execute=execute)
    kind,target=item['kind'],item['target'];paths=pair_paths(root,kind,target)
    for p in paths:checked_path(p,root)
    candidate_root=checked_path(Path(item['candidate_root']),root/'.ops/scratch')
    candidates=pair_paths(candidate_root,kind,target)
    for p in candidates:checked_path(p,candidate_root)
    expected=(item['original_json_sha256'],item['original_markdown_sha256'])
    checked_path(evidence_root,root/'.ops/evidence')
    contents=tuple(p.read_bytes() for p in candidates)
    if tuple(map(digest,contents))!=(item['candidate_json_sha256'],item['candidate_markdown_sha256']):
        raise ValueError('candidate hash mismatch')
    lock=paths[0].with_name('.'+paths[0].stem+'.report-repair.lock')
    _reject_redirects(lock)
    stream=lock.open('x',encoding='utf-8')
    try:
        with stream:
            original=json.loads(paths[0].read_bytes());candidate=json.loads(contents[0])
            if isinstance(original, list) and candidate.get('metadata', {}).get('legacy_original_json_sha256') != expected[0]:
                raise ValueError('legacy original byte hash missing or mismatched')
            if tuple(digest(p.read_bytes()) for p in paths)!=expected:raise ValueError('original pair hash mismatch')
            checks=validate_candidate(root,candidate_root,kind,target,original,candidate,contents[1])
            if not execute:return {'kind':kind,'target':target,'status':'QA_PASSED_NOT_PROMOTED','qa':checks}
            result=_promote(paths,contents,expected,evidence_root/(kind+'-'+target+'-'+uuid4().hex))
            return {'kind':kind,'target':target,'status':'PROMOTED','qa':checks,**result}
    finally:lock.unlink(missing_ok=True)

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--plan-sha256',required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args(argv)
    paths,proof=public_preflight('REPORT_REPAIR')
    plan=checked_path(args.plan,paths.canonical_root/'.ops/evidence');content=plan.read_bytes()
    if digest(content)!=args.plan_sha256:raise ValueError('repair plan hash mismatch')
    items=json.loads(content)
    if not isinstance(items,list) or not items:raise ValueError('empty/invalid repair plan')
    evidence=checked_path(plan.parent/'transactions',paths.canonical_root/'.ops/evidence')
    results=[]
    for item in items:
        try:results.append(repair_pair(paths.canonical_root,item,evidence,execute=args.execute))
        except (OSError,ValueError,KeyError,TypeError) as exc:
            results.append({'kind':item.get('kind'),'target':item.get('target'),'status':'BLOCKED','error':type(exc).__name__+': '+str(exc)})
    target=plan.with_name(plan.stem+('-execution' if args.execute else '-preflight')+'.json')
    target.write_text(json.dumps({'runtime':proof['runtime_provenance'],'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'items':len(results),'promoted':sum(r['status'] in ('PROMOTED','PROMOTED_INCOMPLETE_HISTORY') for r in results),'blocked':sum(r['status']=='BLOCKED' for r in results),'receipt':str(target)}))
    return 1 if any(r['status']=='BLOCKED' for r in results) else 0

if __name__=='__main__':raise SystemExit(main())
