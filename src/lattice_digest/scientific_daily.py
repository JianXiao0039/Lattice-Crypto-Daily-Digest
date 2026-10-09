"""Chinese event-first rendering. Detail budgets never truncate the event ledger."""
from __future__ import annotations

import json
from lattice_digest.publication_events import COLLECTIONS
from lattice_digest.authority import INCOMPLETE_ZERO_TEXT


def _safe(text):
    return str(text or 'unknown').replace('\n',' ').replace('|','\\|')


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
    if not events:
        if not meta['source_coverage']['complete']:lines += [INCOMPLETE_ZERO_TEXT,'']
        else:lines += ['今日未发现值得记录的格密码相关新论文。','']
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
                lines += [f"  - 作者：{_safe(', '.join(row.get('authors',[])))}；venue：{_safe(row.get('venue'))}。",
                    f"  - arXiv：{_safe(row.get('arxiv_id'))}；ePrint：{_safe(row.get('eprint_id'))}；DOI：{_safe(row.get('doi'))}。",
                    f"  - 首发：{_safe(row.get('publication_timestamp') or row.get('publication_date'))}；修订：{_safe(row.get('update_timestamp') or row.get('update_date'))}。",
                    f"  - 中文标题／摘要：{_safe(row.get('critical_claim_zh') or 'TODO_VERIFY_TRANSLATION；当前无已授权翻译后端，不伪造译文。')}",
                    f"  - 原始摘要：{_safe(row.get('abstract'))}",
                    f"  - 来源支持的角色：{_safe('; '.join(r['role']+': '+r['technical_target'] for r in row.get('source_relation_roles',[])))}。",
                    f"  - 入选依据：{e['reason']}。",
                    f"  - 来源内容 SHA-256：{e['source_content_sha256'] or 'TODO_VERIFY'}。",
                    '  - 阅读问题：明确主研究对象、假设、参数、证明范围及实验终点；标准化方案适用性须另证。']
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
    for warning in payload.get('warnings',[]):lines += ['- 运行限制：'+_safe(warning)]
    lines += ['','## 7. 具体阅读与复现问题','',
              '- 对上列来源逐项核验主对象、假设和参数；验证新版本与上一版实际改变的内容。',
              '- 安全结果需核验归约方向、敌手模型、复杂度与反驳／勘误；不从元数据推断方案攻破。',
              '- NO_ACTIONABLE_RESEARCH_IDEA_FROM_CURRENT_EVIDENCE',
              '- 此处没有经完整瓶颈、closest work、差异、可行终点及 novelty 核验的研究提案。','',
              '<!-- counts:'+json.dumps(counts,sort_keys=True,separators=(',',':'))+' -->','']
    return '\n'.join(lines)
