"""L0 observations, L1 source scope, L2 events and L3 actions are separate.

No crawl time or historical-library size is a publication event. The same pure
ledger drives Daily selection, rendering, QA and period aggregation.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, date, time, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import re
from typing import Any

from lattice_digest.promotion_history import identity_keys, authoritative_version, content_fingerprint
from lattice_digest.scientific_scope import evaluate_scope

POLICY_VERSION = 'scientific-publication-p0-v1'
COLLECTIONS = ('primary_publication_events','revision_events','new_critical_verify_events',
               'background_updates','historical_library_observations')
CORE_EVENTS = set(COLLECTIONS[:3])


def source_correction_events(row: dict) -> list[dict]:
    """Dated author correction notes in original abstract, not generated prose."""
    text=str(row.get('abstract') or '')
    months=('January','February','March','April','May','June','July','August','September','October','November','December')
    pattern=r'(?:Additional\s+)?note\s+('+'|'.join(months)+r')\s+(\d{1,2})(?:/|,?\s+)(\d{2,4})\s*:'
    events=[]
    for match in re.finditer(pattern,text,re.I):
        excerpt=text[match.start():]
        if not re.search(r'\b(?:updated|correct(?:ion|ed)?|proof|lemma|rebuttal|clarifications)\b',excerpt,re.I):continue
        year=int(match[3]);year=2000+year if year<100 else year
        try:changed=date(year,next(i+1 for i,m in enumerate(months) if m.lower()==match[1].lower()),int(match[2]))
        except ValueError:continue
        events.append({'event_kind':'SOURCE_CORRECTION','change_date':changed.isoformat(),
                       'date_precision':'DATE_ONLY_SOURCE_NOTE','evidence_state':'SOURCE_ASSERTED',
                       'source_url':row.get('source_url'),'source_excerpt':excerpt,
                       'source_sha256':hashlib.sha256(text.encode()).hexdigest(),
                       'proof_verification_status':'TODO_VERIFY'})
    return events


def timestamp(value) -> datetime | None:
    if not value:
        return None
    try:
        parsed=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except (ValueError,TypeError):
        try:
            parsed=parsedate_to_datetime(str(value))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
        except (ValueError,TypeError,IndexError):
            return None


def coverage(metadata: dict, target: date) -> tuple[datetime,datetime]:
    start,end=timestamp(metadata.get('coverage_start')),timestamp(metadata.get('coverage_end'))
    if start is None or end is None:
        end=datetime.combine(target+timedelta(days=1),time.min,timezone.utc)
        start=end-timedelta(hours=36)
    if start >= end:
        raise ValueError('publication coverage start must precede end')
    return start,end


def canonical_identity(row: dict) -> str:
    keys=identity_keys(row)
    for prefix in ('doi:','arxiv:','eprint:','url:'):
        values=sorted(k for k in keys if k.startswith(prefix))
        if values:return values[0]
    return 'uncertain:'+hashlib.sha256(str(row.get('title') or '').encode()).hexdigest()


def event_id(identity: str, kind: str, evidence: str) -> str:
    return hashlib.sha256(json.dumps([identity,kind,evidence],ensure_ascii=False).encode()).hexdigest()


def _in_window(value,start,end):
    value=timestamp(value)
    return value is not None and start <= value < end


def _action(row, kind):
    if kind=='new_critical_verify_events':return 'verify_first'
    if str(row.get('recommendation_level'))=='TODO_VERIFY':return 'verify_first'
    return 'read_now' if str(row.get('recommendation_level')) in {'Strong','Medium'} else 'skim'


def build_event_ledger(records: list[dict], metadata: dict, prior: list[dict] = ()) -> dict:
    target=date.fromisoformat(str(metadata['target_date'])[:10])
    start,end=coverage(metadata,target)
    collections={k:[] for k in COLLECTIONS}
    watches=[]; decisions=[]; seen_events=set(); observed_by_key={}; selected_by_key={}; qualified_identities=set()
    prior_by_key={}
    for position,p in enumerate(prior):
        for key in identity_keys(p):prior_by_key.setdefault(key,set()).add(position)
    for index,row in enumerate(records):
        scientific=evaluate_scope(row)
        identity=canonical_identity(row); keys=identity_keys(row)
        positions=set().union(*(prior_by_key.get(key,set()) for key in keys)) if keys else set()
        matches=[prior[p] for p in sorted(positions)]
        conflicting=any(any({k for k in keys if k.startswith(ns)} and {k for k in identity_keys(p) if k.startswith(ns)} and
            {k for k in keys if k.startswith(ns)}.isdisjoint({k for k in identity_keys(p) if k.startswith(ns)})
            for ns in ('doi:','arxiv:','eprint:')) for p in matches)
        # Preserve an already known representative when DOI/source aliases change.
        representatives=[canonical_identity(p) for p in matches]
        representatives.extend(observed_by_key[k] for k in keys if k in observed_by_key)
        if representatives:identity=sorted(representatives)[0]
        for key in keys:observed_by_key[key]=identity
        fingerprint=content_fingerprint(row)
        same_content=any(fingerprint and fingerprint==content_fingerprint(p) for p in matches)
        kind='historical_library_observations'; basis='';reason='no qualified new publication event'
        pub=row.get('preprint_first_posted_at') or row.get('publication_timestamp') or row.get('publication_date')
        # A proceedings/indexed year cannot override a distinct first-posted timestamp.
        pub_kind='AUTHORITATIVE_PUBLICATION_DATE' if row.get('preprint_first_posted_at') else row.get('publication_date_kind','AUTHORITATIVE_PUBLICATION_DATE')
        ann=row.get('announcement_timestamp') or row.get('announcement_date')
        revision=row.get('source_version_timestamp') or row.get('update_timestamp') or row.get('update_date')
        new_pub=pub if pub_kind=='AUTHORITATIVE_PUBLICATION_DATE' and _in_window(pub,start,end) else ann if row.get('announcement_date_kind','AUTHORITATIVE_ANNOUNCEMENT_DATE')=='AUTHORITATIVE_ANNOUNCEMENT_DATE' and _in_window(ann,start,end) else ''
        version=authoritative_version(row)
        older_versions=[authoritative_version(p) for p in matches if authoritative_version(p)]
        new_version=bool(version and older_versions and int(version[1:])>max(int(v[1:]) for v in older_versions))
        content_changed=bool(matches and fingerprint and all(content_fingerprint(p) and fingerprint!=content_fingerprint(p) for p in matches))
        revision_in_window=row.get('update_date_kind','AUTHORITATIVE_CONTENT_REVISION_DATE')=='AUTHORITATIVE_CONTENT_REVISION_DATE' and _in_window(revision,start,end)
        # An unseen v2 alone does not prove a new revision. Timestamp must differ
        # from first publication; prior evidence closes the content/version route.
        distinct_revision=timestamp(revision)!=timestamp(pub)
        genuinely_revised=revision_in_window and (new_version or content_changed or
            (not matches and version and int(version[1:])>1 and distinct_revision))
        date_uncertain=(not timestamp(pub) and not timestamp(ann) and not timestamp(revision)) or (bool(pub) and timestamp(pub) is None and not new_pub and not genuinely_revised)
        future_only=timestamp(pub) is not None and timestamp(pub)>=end and not new_pub and not genuinely_revised
        from lattice_digest.evidence_contract import source_scope_score, Scope
        qualified=scientific['lattice_relevance_qualified'] and source_scope_score(row)[0] in {Scope.DIRECT_LATTICE_CRYPTO,Scope.DIRECT_LATTICE_HARDNESS_THEORY}
        if qualified:qualified_identities.add(identity)
        if not keys or conflicting:
            reason='IDENTITY_UNCERTAIN: conflicting or absent canonical identity'
        elif future_only or date_uncertain:
            reason='DATE_UNCERTAIN: future/absent authoritative event date; TODO_VERIFY'
        elif row.get('publication_event_blockers'):
            reason='SOURCE_ROLE_POLICY: '+','.join(row['publication_event_blockers'])
        elif qualified and new_pub and not matches:
            kind='primary_publication_events';basis=str(new_pub);reason='source publication/announcement in coverage; identity not previously observed'
        elif qualified and genuinely_revised:
            kind='revision_events';basis=str(revision);reason='source-authenticated in-window content/version revision'
        elif not qualified and scientific['scientific_scope'] in {'ADJACENT_PQC','GENERAL_CRYPTO_BACKGROUND'} and scientific['score']>=40 and any(not r['negative_applicability'] for r in scientific['source_relation_roles']) and (new_pub or genuinely_revised):
            kind='background_updates';basis=str(new_pub or revision);reason='new adjacent/general observation, outside core Daily'
        elif qualified and row.get('source_metadata_correction_date') and _in_window(row['source_metadata_correction_date'],start,end):
            kind='background_updates';basis=str(row['source_metadata_correction_date']);reason='source metadata correction; not new research'
        # A newly observed extraordinary signal gets a distinct verify-first event,
        # never a primary-new event. Unchanged evidence cannot reopen it.
        critical=qualified and row.get('security_impact_severity')=='CRITICAL'
        changes=[e for e in [*(row.get('critical_verification_events') or []),*source_correction_events(row)] if
            e.get('source_url') and e.get('source_excerpt') and e.get('source_sha256') and
            e.get('evidence_state') in {'SOURCE_ASSERTED','INDEPENDENTLY_VERIFIED'} and
            e.get('event_kind') in {'SIGNIFICANT_SECURITY_VERIFICATION','SOURCE_CORRECTION','AUTHORITATIVE_CONTENT_REVISION'} and
            _in_window(e.get('change_date'),start,end)]
        def change_signature(e):
            # Metadata URL aliases do not make identical evidence a new alert.
            return json.dumps({k:e.get(k) for k in ('event_kind','change_date','source_excerpt','source_sha256')},sort_keys=True)
        prior_changes={change_signature(e) for p in matches for e in [*(p.get('critical_verification_events') or []),*source_correction_events(p)]}
        changes=[e for e in changes if change_signature(e) not in prior_changes]
        first_seen=row.get('first_seen_at') or row.get('first_seen_date')
        if (critical and kind not in CORE_EVENTS and not conflicting and not future_only and not row.get('publication_event_blockers') and
            (changes or (not same_content and not matches and _in_window(first_seen,start,end)))):
            kind='new_critical_verify_events';basis=str(changes[0]['change_date'] if changes else first_seen);reason='new critical source evidence; verify proof, parameters and reduction direction'
        evidence='|'.join([fingerprint,version,basis,json.dumps(changes,sort_keys=True) if kind=='new_critical_verify_events' else ''])
        eid=event_id(identity,kind,evidence)
        signature=(kind, '' if kind=='primary_publication_events' else '|'.join([version,basis]) if version else evidence)
        duplicate_alias=any(signature in selected_by_key.get(key,set()) for key in keys)
        if kind in CORE_EVENTS and (eid in seen_events or duplicate_alias):
            kind='historical_library_observations';basis='';reason='duplicate canonical event in same input'
            eid=event_id(identity,kind,'|'.join([fingerprint,version,basis]))
        elif kind in CORE_EVENTS:
            for key in keys:selected_by_key.setdefault(key,set()).add(signature)
        seen_events.add(eid)
        entry={'row_index':index,'canonical_identity':identity,'event_id':eid,'collection':kind,
               'event_date':basis,'source_version':version,'source_content_sha256':fingerprint,
               'reason':reason,'action':_action(row,kind) if kind in CORE_EVENTS else 'observe_only',
               'relevance_label':row.get('relevance_label','D'),'scientific_scope':scientific['scientific_scope']}
        collections[kind].append(entry);decisions.append(entry)
        if critical:
            watches.append({**entry,'channel':'CRITICAL_WATCH','original_publication_date':pub,
                'new_evidence_change_date':basis or next((e['change_date'] for e in reversed(source_correction_events(row))),None),'affected_problem':[r['technical_target'] for r in scientific['source_relation_roles']],
                'reduction_direction':row.get('critical_signal_relations') or 'TODO_VERIFY',
                'claim_confidence':row.get('evidence_confidence') or 'TODO_VERIFY',
                'proof_verification_status':'TODO_VERIFY', 'known_rebuttals_corrections':[
                    *row.get('source_limitations',[]),*[s for s in re.split(r'(?<=[.!?])\s+',str(row.get('abstract') or ''))
                    if re.search(r'\b(?:note|incorrect|correction|rebuttal|lemma|preprint)\b',s,re.I)]],
                'rebuttal_search_status':'NOT_INDEPENDENTLY_SEARCHED','next_human_review_action':'核验原稿、证明、归约方向及参数范围；不得外推标准化 PQC 攻破',
                'reopened':kind=='new_critical_verify_events'})
    active=[e for name in COLLECTIONS[:3] for e in collections[name]]
    counts={'observations':len(records),'observed_paper_identities':len({e['canonical_identity'] for e in decisions}),'qualified_lattice_identities':len(qualified_identities),
            'selected':len(active),'primary_new':len(collections['primary_publication_events']),
            'event_count':len(active),'event_paper_identities':len({e['canonical_identity'] for e in active}),
            'historical_observations':len(collections['historical_library_observations']),
            'background_updates':len(collections['background_updates']),
            'classification_counts':dict(Counter(e['relevance_label'] for e in active)),
            'action_counts':dict(Counter(e['action'] for e in active))}
    return {'policy_version':POLICY_VERSION,'collections':collections,'critical_watch':watches,
            'decisions':decisions,'counts':counts,'coverage_start':start.isoformat(),'coverage_end':end.isoformat()}


def attach_events(records, metadata, prior=()):
    rows=[r.model_dump() for r in records]
    ledger=build_event_ledger(rows,metadata,prior)
    output=[]
    for record,entry in zip(records,ledger['decisions']):
        is_primary=entry['collection']=='primary_publication_events'
        output.append(record.model_copy(update={'publication_event_id':entry['event_id'],
            'publication_event_type':entry['collection'],'publication_event_date':entry['event_date'],
            'publication_event_reason':entry['reason'],'primary_today_new_eligible':is_primary,
            'primary_action_allowed':is_primary,
            'suggested_action':{'read_now':'Read today','skim':'Skim for related work','verify_first':'READ_AND_VERIFY_IMMEDIATELY' if record.security_impact_severity=='CRITICAL' else 'TODO_VERIFY before reading','observe_only':'Save for background'}[entry['action']],
            'recommended_action':entry['action'],
            'freshness_bucket':'primary_today_new' if is_primary else 'recent_content_revision' if entry['collection']=='revision_events' else record.freshness_bucket}))
    return output,ledger


def ledger_issues(payload: dict, markdown: str | None = None):
    ledger=payload.get('publication_event_ledger')
    if not isinstance(ledger,dict):return ['PUBLICATION_EVENT_LEDGER_MISSING']
    records=payload.get('records',[]); meta=payload.get('metadata',{})
    # Recompute using the bounded source-history evidence saved with the ledger.
    try:
        recomputed=build_event_ledger(records,meta,payload.get('publication_history_evidence',[]))
        if not isinstance(ledger.get('collections'),dict) or not isinstance(ledger.get('counts'),dict) or not recomputed['counts'].keys() <= ledger['counts'].keys() or not set(COLLECTIONS) <= ledger['collections'].keys():
            return ['PUBLICATION_EVENT_LEDGER_INVALID']
    except (ValueError,TypeError,KeyError,AttributeError):
        return ['PUBLICATION_EVENT_LEDGER_INVALID']
    issues=[]
    if ledger!=recomputed:issues.append('PUBLICATION_EVENT_LEDGER_MISMATCH')
    if meta.get('selection_counts')!=ledger['counts']:issues.append('PUBLICATION_COUNTS_MISMATCH')
    for row,entry in zip(records,recomputed['decisions']):
        if row.get('publication_event_type')!=entry['collection'] or row.get('publication_event_id')!=entry['event_id']:
            issues.append('PUBLICATION_ROW_EVENT_MISMATCH')
        if row.get('primary_today_new_eligible') is not (entry['collection']=='primary_publication_events'):
            issues.append('PUBLICATION_ROW_PRIMARY_MISMATCH')
    if markdown is not None:
        import re
        summary={'Daily publication events':ledger['counts']['event_count'],
                 'Primary New':ledger['counts']['primary_new'],
                 'Genuine revisions':len(ledger['collections'].get('revision_events',[])),
                 'New critical verification alerts':len(ledger['collections'].get('new_critical_verify_events',[])),
                 'Event paper identities':ledger['counts']['event_paper_identities'],
                 'Total observed records':ledger['counts']['observations'],
                 'Observed paper identities':ledger['counts']['observed_paper_identities'],
                 'Historical observations（档案人口，非 Daily 入选）':ledger['counts']['historical_observations'],
                 'Background updates':ledger['counts']['background_updates']}
        for label,value in summary.items():
            rendered=re.findall(r'^- '+re.escape(label)+r'：([^\n]+)$',markdown,re.M)
            if rendered!=[str(value)]:issues.append('PUBLICATION_RENDER_SUMMARY_MISMATCH')
        for label,key in [('A/B/C/D event classification','classification_counts'),('Recommendation action partition','action_counts')]:
            expected=json.dumps(ledger['counts'][key],ensure_ascii=False,sort_keys=True)
            if re.findall(r'^- '+re.escape(label)+r'：([^\n]+)$',markdown,re.M)!=[expected]:
                issues.append('PUBLICATION_RENDER_ACTION_CLASSIFICATION_MISMATCH')
        for name in COLLECTIONS[:3]:
            for entry in ledger['collections'][name]:
                if markdown.count('<!-- event:'+entry['event_id']+' -->')!=1:
                    issues.append('PUBLICATION_RENDER_EVENT_PARTITION_MISMATCH')
        if '<!-- counts:'+json.dumps(ledger['counts'],sort_keys=True,separators=(',',':'))+' -->' not in markdown:
            issues.append('PUBLICATION_RENDER_COUNTS_MISMATCH')
    return sorted(set(issues))


def period_event_rows(payload):
    """P0 inputs are events only; legacy artifacts stay explicitly compatible.

    Legacy inputs lacking the new contract must be reviewed, not silently declared
    to have verified P0 semantics. Existing quality assessment records that gap.
    """
    rows=payload.get('records',[])
    if '_period_publication_rows' in payload:return payload['_period_publication_rows']
    if payload.get('metadata',{}).get('publication_policy_version')==POLICY_VERSION:
        if payload.get('_daily_input_quality',{}).get('semantic_status') in {'FAIL','UNKNOWN'}:return []
        return [r for r in rows if r.get('publication_event_type') in CORE_EVENTS]
    return rows


def normalize_period_inputs(loaded):
    """Reconcile controlled pre-P0 Daily pairs using their exact source window.

    Unversioned legacy archives remain readable for compatibility, with no claim
    that their population is a canonical publication-event count.
    """
    normalized=[];prior=[]
    for day,payload in sorted(loaded,key=lambda item:item[0]):
        meta=payload.get('metadata',{});rows=payload.get('records',[])
        if meta.get('publication_policy_version')!=POLICY_VERSION and meta.get('quality_status') in {'authoritative','authoritative_backfill'} and meta.get('coverage_start') and meta.get('coverage_end'):
            ledger=build_event_ledger(rows,{**meta,'target_date':day.isoformat()},prior)
            selected=[]
            from lattice_digest.evidence_contract import source_scope_score,score_to_label
            if payload.get('_daily_input_quality',{}).get('semantic_status') not in {'FAIL','UNKNOWN'}:
                for e in ledger['decisions']:
                    if e['collection'] in CORE_EVENTS:
                        row=rows[e['row_index']];scope,score=source_scope_score(row)
                        selected.append({**row,'upstream_relevance_label':row.get('relevance_label'),
                            'upstream_relevance_score':row.get('relevance_score'),'relevance_score':score,
                            'relevance_label':score_to_label(score),'relevance_scope':str(scope),
                            'publication_event_id':e['event_id'],'publication_event_type':e['collection'],
                            'primary_today_new_eligible':e['collection']=='primary_publication_events'})
            payload={**payload,'_period_publication_rows':selected,'_period_event_ledger':ledger,
                     '_period_reconciliation':'SOURCE_WINDOW_REPLAY_OF_PRE_P0_CONTROLLED_DAILY'}
        normalized.append((day,payload));prior.extend(rows)
    return normalized


def period_views(loaded):
    collections={k:{} for k in COLLECTIONS}
    for day,payload in loaded:
        if payload.get('_daily_input_quality',{}).get('semantic_status') in {'FAIL','UNKNOWN'}:continue
        for name,entries in payload.get('_period_event_ledger',payload.get('publication_event_ledger',{})).get('collections',{}).items():
            if name in collections:
                for entry in entries:collections[name][entry['event_id']]=entry
    return {'collections':{k:list(v.values()) for k,v in collections.items()},
            'counts':{k:len(v) for k,v in collections.items()},
            'trend_scope':'loaded canonical publication events only; partial source coverage does not establish a global field trend'}
