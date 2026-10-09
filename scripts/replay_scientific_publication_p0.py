"""Offline incident replay. Frozen input pairs are never modified.

Usage: python scripts/replay_scientific_publication_p0.py --input-dir ... --output-dir ...
Human gold is deliberately separate and empty. No source fetch or publication.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lattice_digest.authority import semantic_qa
from lattice_digest.evidence_contract import bind_source_evidence
from lattice_digest.models import PaperRecord
from lattice_digest.promotion_history import load_promotion_history, apply_promotion_history, identity_keys
from lattice_digest.publication_events import canonical_identity, period_views
from lattice_digest.radar_freshness import enrich_record_for_daily_radar
from lattice_digest.scientific_daily import render_scientific_daily
from lattice_digest.scientific_scope import evaluate_scope, ScientificScope
from lattice_digest.storage import build_daily_payload
from lattice_digest.runtime_provenance import runtime_provenance
from lattice_digest.weekly_synthesis import aggregate_records as weekly_records
from lattice_digest.monthly_synthesis import aggregate_records as monthly_records

DAYS=('2026-10-07','2026-10-08','2026-10-09')


def replay(input_dir: Path, output_dir: Path, history_dir: Path | None = None):
    input_dir=input_dir.resolve();output_dir=output_dir.resolve()
    if output_dir==input_dir or output_dir.is_relative_to(input_dir):
        raise ValueError('replay outputs must be outside the frozen input directory')
    if output_dir.is_relative_to(ROOT) or any((output_dir/name).exists() for name in ('papers.db','.git')):
        raise ValueError('output must be a dedicated external replay directory')
    output_dir.mkdir(parents=True,exist_ok=False)
    before_after=[];all_audits=[];loaded=[];replay_prior=[];identities={}
    candidate_provenance=runtime_provenance(ROOT,'DAILY',verify_remote=False)
    for day in DAYS:
        path=input_dir/(day+'.json');raw=path.read_bytes();x=json.loads(raw)
        day_date=date.fromisoformat(day);metadata=dict(x['metadata'])
        if history_dir:
            external_prior,history=load_promotion_history(history_dir,day_date)
            prior=[*external_prior,*replay_prior]
        else:
            prior=list(replay_prior)
            history={'mode':'PREVIOUS_REPLAY_DAYS_ONLY','missing_prior_to_incident':True}
        records=[]
        for original in x['records']:
            fields={k:v for k,v in original.items() if k in PaperRecord.model_fields}
            record=bind_source_evidence(PaperRecord(**fields))
            record=enrich_record_for_daily_radar(record,day_date,
                coverage_start=datetime.fromisoformat(metadata['coverage_start']),
                coverage_end=datetime.fromisoformat(metadata['coverage_end']))
            records.append(record)
        records=apply_promotion_history(records,prior)
        metadata.update(candidate_provenance)
        metadata.update({'replay_source_runtime_git_head':x['metadata'].get('runtime_git_head'),
                         'replay_source_runtime_manifest_sha256':x['metadata'].get('runtime_code_manifest_sha256'),
                         'source_health_count_semantics':'FROZEN_ORIGINAL_PIPELINE_COUNTS_NOT_NEW_DAILY_EVENTS',
                         'offline_replay':True,'publication_method':'P0_OFFLINE_CANDIDATE_NOT_PUBLISHED',
                         'quality_status':'unverified_candidate','_publication_prior':prior})
        payload=build_daily_payload(records,output_dir/'data',day_date,x['source_health'],x.get('warnings'),metadata['since_window'],metadata)
        payload['metadata'].pop('markdown_sha256',None)
        payload['metadata'].pop('generation_id',None)
        payload['metadata']['replay_source_generation_id']=x['metadata'].get('generation_id')
        md=render_scientific_daily(payload)
        payload['metadata']['semantic_qa']={'status':'UNKNOWN'}
        qa=semantic_qa(payload,md,candidate=True)
        payload['metadata']['semantic_qa']={k:v for k,v in qa.items() if k!='derived_authority'}
        payload['metadata']['markdown_sha256']=hashlib.sha256(md.encode()).hexdigest()
        payload['metadata']['publication_state']='OFFLINE_REPLAY_QA_PASSED' if qa['status']=='PASS' else 'OFFLINE_REPLAY_FAILED'
        (output_dir/(day+'.json')).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
        (output_dir/(day+'.md')).write_text(md,encoding='utf-8')
        decisions=payload['publication_event_ledger']['decisions'];day_audits=[]
        for original,row,event in zip(x['records'],payload['records'],decisions):
            decision=evaluate_scope(row);identity=canonical_identity(row)
            existing=next((key for key,keys in identities.items() if keys & identity_keys(row)),None)
            group=existing or identity;identities.setdefault(group,set()).update(identity_keys(row))
            result=('DATE_UNCERTAIN' if event['reason'].startswith('DATE_UNCERTAIN') else
                    'IDENTITY_UNCERTAIN' if event['reason'].startswith('IDENTITY_UNCERTAIN') else
                    'KEEP_FOUNDATIONAL' if decision['scientific_scope']==ScientificScope.FOUNDATION else
                    'KEEP_CORE' if decision['lattice_relevance_qualified'] else
                    'DOWNGRADE_ADJACENT' if decision['scientific_scope']==ScientificScope.ADJACENT else
                    'BACKGROUND_ONLY' if decision['scientific_scope']==ScientificScope.GENERAL else 'OUT_OF_SCOPE')
            day_audits.append({'day':day,'row_index':event['row_index'],'canonical_identity':identity,'cross_day_identity_group':group,
                'source_version':event['source_version'],'source_content_sha256':event['source_content_sha256'],
                'title':row['title'],'source_url':row['source_url'],'decision':result,
                'provenance_label':original.get('relevance_label'),'provenance_score':original.get('relevance_score'),
                'scope':decision['scientific_scope'],'label':row['relevance_label'],'score':row['relevance_score'],
                'source_relations':decision['source_relation_roles'],'event_collection':event['collection'],
                'event_reason':event['reason'],'publication_date':row.get('publication_date'),
                'publication_timestamp':row.get('publication_timestamp'),'publication_date_kind':row.get('publication_date_kind'),
                'date_evidence':row.get('date_evidence',[]),'remaining_uncertainty':decision['remaining_uncertainty'],
                'audit_status':'MODEL_RULE_AUDIT_NOT_HUMAN_GOLD'})
        all_audits.extend(day_audits)
        before_after.append({'day':day,'input_sha256':hashlib.sha256(raw).hexdigest(),
            'before':x['metadata']['selection_counts'],'after':payload['publication_event_ledger']['counts'],
            'decisions':dict(Counter(r['decision'] for r in day_audits)),'semantic_qa':qa,'history':history,
            'critical_watch_count':len(payload['publication_event_ledger']['critical_watch'])})
        loaded.append((day_date,payload));replay_prior.extend(payload['records'])
    period={'event_views':period_views(loaded),'weekly_unique_identities':len(weekly_records(loaded)),
            'monthly_unique_identities':len(monthly_records(loaded)),
            'cross_day_observed_unique_identities':len(identities)}
    result={'days':before_after,'period':period,'human_adjudicated_gold':[],
            'human_gold_status':'NOT_AVAILABLE_NOT_FABRICATED',
            'all_rows_audited':len(all_audits),'provenance':'immutable local source metadata; no new source or PDF verification'}
    (output_dir/'row-audit.json').write_text(json.dumps(all_audits,ensure_ascii=False,indent=2),encoding='utf-8')
    (output_dir/'replay-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--history-dir',type=Path)
    args=parser.parse_args();result=replay(args.input_dir,args.output_dir,args.history_dir)
    print(json.dumps({'days':[{k:d[k] for k in ('day','before','after','decisions')} for d in result['days']],
                      'period_counts':{k:v for k,v in result['period'].items() if k!='event_views'},'all_rows_audited':result['all_rows_audited']},ensure_ascii=False))
    return 0 if all(d['semantic_qa']['status']=='PASS' for d in result['days']) else 2


if __name__=='__main__':raise SystemExit(main())
