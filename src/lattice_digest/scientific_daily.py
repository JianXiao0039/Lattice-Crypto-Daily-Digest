"""Chinese event-first rendering. Detail budgets never truncate the event ledger."""
from __future__ import annotations

import json
import re
from urllib.parse import urlsplit
from lattice_digest.publication_events import COLLECTIONS
from lattice_digest.authority import INCOMPLETE_ZERO_TEXT, HISTORY_INCOMPLETE_ZERO_TEXT
from lattice_digest.scientific_contribution import abstract_guide, contribution_view, role_summary


def _safe(text):
    return str(text or 'unknown').replace('\n',' ').replace('|','\\|')


def _public_link(value):
    """Only already public scholarly URLs can enter optional source displays."""
    try:
        parsed = urlsplit(str(value or ''))
        if parsed.scheme != 'https' or parsed.query or parsed.fragment or parsed.username or parsed.port:
            return None
        pattern = {'eprint.iacr.org': r'/\d{4}/\d{1,6}(?:v\d+)?',
                   'arxiv.org': r'/abs/(?:\d{4}\.\d{4,5}|[A-Za-z-]+/\d{7})(?:v\d+)?',
                   'doi.org': r'/10\.\d{4,9}/[A-Za-z0-9._:/;+-]+'}.get(parsed.hostname)
        if pattern and re.fullmatch(pattern, parsed.path):
            return parsed.geturl()
    except ValueError:
        pass
    return None


def _optional_source_lines(payload, meta):
    status = meta.get('gmail_iacr') or meta.get('gmail_reconciliation') or payload.get('gmail_iacr')
    state = status.get('status') if isinstance(status, dict) else status
    allowed = {'GMAIL_AUTHORIZATION_REQUIRED', 'GMAIL_UNAVAILABLE', 'GMAIL_DISABLED',
               'GMAIL_RECONCILIATION_COMPLETE', 'GMAIL_RECONCILIATION_PARTIAL',
               'GMAIL_AVAILABLE', 'GMAIL_NOT_CONFIGURED', 'GMAIL_RECONCILED', 'GMAIL_PARTIAL'}
    state = state if state in allowed else 'GMAIL_NOT_CONFIGURED'
    lines = [f'- IACR 邮件核对：{state}；邮件收件时间不替代公开论文首发时间。']
    if state in {'GMAIL_AUTHORIZATION_REQUIRED', 'GMAIL_DISABLED', 'GMAIL_NOT_CONFIGURED'}:
        lines += ['- 邮件核对未完成；本报告继续依据公开学术来源，不能据此推断邮箱中没有通知。']
    # Message IDs, subjects, addresses and diagnostic bodies are deliberately absent.
    late = payload.get('late_arrivals') or meta.get('late_arrivals') or []
    if isinstance(late, list) and late:
        lines += ['', '### 迟到发现与更正（不计为今日首发）', '']
        seen = set()
        for item in late[:20]:
            if not isinstance(item, dict):
                continue
            url = _public_link(item.get('source_url') or item.get('url'))
            identity = item.get('canonical_identity') or item.get('eprint_id') or url
            if not url or identity in seen:
                continue
            seen.add(identity)
            lines += [f'- 公开论文候选：{url}；此前窗口未完成发现，原始出版时间与历史归属仍按来源证据核验。']
        lines += ['- 上列条目是迟到观察或更正；保留原事件身份，不因本次补录重新累计研究成果。']
    return lines


def render_scientific_daily(payload: dict) -> str:
    meta=payload['metadata'];ledger=payload['publication_event_ledger'];counts=ledger['counts']
    rows=payload['records'];collections=ledger['collections']
    detail_budget=int(meta.get('daily_priority_display_budget',5))
    background_budget=int(meta.get('daily_background_display_budget',5))
    if detail_budget<0 or background_budget<0:raise ValueError('display budgets must be nonnegative')
    events=[e for k in COLLECTIONS[:3] for e in collections[k]]
    priority=sorted(events,key=lambda e:(e['action']!='verify_first',-int(rows[e['row_index']].get('recommendation_score') or 0),e['event_id']))
    detailed={e['event_id'] for e in priority[:detail_budget]}
    lines=[f"# 格密码科研情报日报 - {meta['target_date']}",'','## 1. 科学结论与阅读决策','',
           f"- Daily publication events：{counts['event_count']}",
           f"- Primary New：{counts['primary_new']}",
           f"- Genuine revisions：{len(collections['revision_events'])}",
           f"- New critical verification alerts：{len(collections['new_critical_verify_events'])}",
           f"- Event paper identities：{counts['event_paper_identities']}",
           f"- Historical observations（档案人口，非 Daily 入选）：{counts['historical_observations']}",
           f"- Background updates：{counts['background_updates']}",
           f"- Total observed records：{counts['observations']}",
           f"- Observed paper identities：{counts['observed_paper_identities']}",
           '- A/B/C/D event classification：'+json.dumps(counts['classification_counts'],ensure_ascii=False,sort_keys=True),
           '- Recommendation action partition：'+json.dumps(counts['action_counts'],ensure_ascii=False,sort_keys=True),
           f"- authority_state：{meta['authority_state']}",
           f"- target_date：{meta['target_date']}",
           f"- run_date：{meta.get('run_date','unknown')}",
           f"- collector：{meta.get('collector','unknown')}",
           f"- quality_status：{meta.get('quality_status','unknown')}",
           f"- run_mode：{meta.get('run_mode','unknown')}",
           f"- backfill：{str(bool(meta.get('backfill'))).lower()}",
           f"- coverage_start：{meta.get('coverage_start',ledger['coverage_start'])}",
           f"- coverage_end：{meta.get('coverage_end',ledger['coverage_end'])}",
           '- 日期与相关性分别核验；来源陈述不等于已验证定理。',
           '- 原始论文身份、全部事件和历史观察保留在配对 JSON；回填模式不扩大 Daily 入选。','']
    audit_lines = lines[4:]
    lines = lines[:4] + [f"本次建立 {counts['event_count']} 个格密码事件，其中真正新增 {counts['primary_new']} 篇；权威状态：{meta['authority_state']}。",
        '阅读分类采用 scientific-contribution-v3.1，区分数学基础、算法、密码分析、原语、实现、应用与邻接 PQC；不改写 A/B/C/D 冻结评分。', '']
    if not events:
        history_blocked=meta.get('promotion_history',{}).get('schema_version') == 'history-evidence-v41' and meta['promotion_history'].get('complete') is not True
        if history_blocked:lines += [HISTORY_INCOMPLETE_ZERO_TEXT,'']
        if not meta['source_coverage']['complete']:lines += [INCOMPLETE_ZERO_TEXT,'']
        elif not history_blocked:lines += ['今日未发现值得记录的格密码相关新论文。','']
    else:
        lines += [f"阅读计划覆盖 {len(events)} 个真实事件；详读预算 {detail_budget} 项，其余保留完整简明索引。",'']
    for name,heading in zip(COLLECTIONS[:3],('2. 真正新增格密码论文','3. 真正内容修订','4. 新关键安全核验提醒')):
        lines += ['## '+heading,'']
        entries=collections[name]
        if not entries:lines += ['本节没有已建立的事件。',''];continue
        for e in entries:
            row=rows[e['row_index']]
            lines += ['<!-- event:'+e['event_id']+' -->',
                f"- [{_safe(row['title'])}]({row['source_url']})｜{row.get('relevance_label')}/{row.get('relevance_score')}｜{e['scientific_scope']}｜{e['action']}｜事件日期 {e['event_date']}",
                f"  - 身份：{e['canonical_identity']}；事件：{e['event_id']}；来源版本：{e['source_version'] or 'unknown'}。"]
            if e['event_id'] in detailed:
                contribution = contribution_view(row)
                lines += [f"  - 作者：{_safe(', '.join(row.get('authors',[])))}；venue：{_safe(row.get('venue'))}。",
                    f"  - arXiv：{_safe(row.get('arxiv_id'))}；ePrint：{_safe(row.get('eprint_id'))}；DOI：{_safe(row.get('doi'))}。",
                    f"  - 首发：{_safe(row.get('publication_timestamp') or row.get('publication_date'))}；修订：{_safe(row.get('update_timestamp') or row.get('update_date'))}。",
                    f"  - 中文标题／摘要：{_safe(row.get('critical_claim_zh') or 'TODO_VERIFY_TRANSLATION；当前无已授权翻译后端，不伪造译文。')}",
                    f"  - 贡献分类：{contribution['category']}（{contribution['category_zh']}）；文献性质：{contribution['contribution_kind']}。",
                    f"  - 中文技术导读：{abstract_guide(row)}",
                    '<details><summary>官方原始摘要与分类证据</summary>', '',
                    f"  - 原始摘要：{_safe(row.get('abstract'))}",
                    f"  - 来源支持的角色：{_safe(role_summary(row))}。",
                    f"  - 分类规则：{contribution['classification_rule']}；证据：{contribution['evidence_confidence']}。",
                    f"  - 入选依据：{e['reason']}。",
                    f"  - 来源内容 SHA-256：{e['source_content_sha256'] or 'TODO_VERIFY'}。",
                    '  - 阅读问题：明确主研究对象、假设、参数、证明范围及实验终点；标准化方案适用性须另证。', '', '</details>']
            if name=='new_critical_verify_events':
                watch=next(w for w in ledger['critical_watch'] if w['event_id']==e['event_id'])
                lines += ['  - CRITICAL_WATCH：'+_safe(json.dumps(watch,ensure_ascii=False)),
                          '  - 不构成标准化 ML-KEM／ML-DSA 已被攻破的结论；证明与具体参数均为 TODO_VERIFY。']
        lines.append('')
    lines += ['## 5. 有依据的背景更新与观察','']
    for e in collections['background_updates'][:background_budget]:
        row=rows[e['row_index']]
        lines += [f"- [{_safe(row['title'])}]({row['source_url']})｜{e['scientific_scope']}｜{e['reason']}；不计为 core Daily 事件。"]
    if not collections['background_updates']:lines += ['本次没有需要单列的背景更新。']
    lines += [f"- CRITICAL_WATCH 存量：{len(ledger['critical_watch'])}；未变化的旧信号仅保留机器账本，不重复开启阅读提醒。",'',
              '## 6. 来源健康与覆盖限制','',
              '- source-starved / source_coverage：'+json.dumps(meta['source_coverage'],ensure_ascii=False,sort_keys=True),
              '- TRANSLATION_BACKEND_SELECTION_REQUIRED', '- BILINGUAL_RELEASE_NOT_YET_AVAILABLE']
    for h in payload.get('source_health',[]):
        lines += [f"- {_safe(h.get('source'))}：{_safe(h.get('health_status') or h.get('status'))}；{_safe(h.get('runtime_state'))}；{_safe(h.get('error_type'))}。"]
    if payload.get('warnings'):
        lines += [f"- 本次记录 {len(payload['warnings'])} 条运行限制；完整原始提供者诊断保留在配对 JSON 与检索 journal，不在正文展开。"]
    lines += _optional_source_lines(payload, meta)
    lines += ['','## 7. 具体阅读与复现问题','',
              '- 对上列来源逐项核验主对象、假设和参数；验证新版本与上一版实际改变的内容。',
              '- 安全结果需核验归约方向、敌手模型、复杂度与反驳／勘误；不从元数据推断方案攻破。',
              '- NO_ACTIONABLE_RESEARCH_IDEA_FROM_CURRENT_EVIDENCE',
              '- 此处没有经完整瓶颈、closest work、差异、可行终点及 novelty 核验的研究提案。','',
              '<!-- counts:'+json.dumps(counts,sort_keys=True,separators=(',',':'))+' -->','']
    lines += ['<details><summary>审计附录：执行窗口、完整计数与来源权威</summary>', '', *audit_lines, '</details>', '']
    return '\n'.join(lines)
