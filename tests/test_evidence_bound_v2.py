from datetime import date
import json
from pathlib import Path

import pytest

from lattice_digest.authority import derive_authority, semantic_qa
from lattice_digest.config import load_config_bundle
from lattice_digest.daily_inputs import summarize_daily_inputs
from lattice_digest.digest import research_tags, why_it_matters
from lattice_digest.evidence_contract import (
    EvidenceType, Scope, analyze_source, bind_source_evidence, classification_summary,
    evidence_quality_issues, propagate_source_health, score_to_label, source_topics,
)
from lattice_digest.models import make_paper_record
from lattice_digest.ontology_v3 import load_ontology_v3
from lattice_digest.ranker import rank_records
from lattice_digest.recommendation_calibration import calibrate_recommendation
from lattice_digest.report_quality import record_text
from lattice_digest.retrieval_v3 import apply_semantic_consequence_analysis_v3

FIXTURES=json.loads((Path(__file__).parent/'fixtures/evidence_bound_v2_canaries.json').read_text(encoding='utf-8'))

def paper(title='LWE security', abstract='We study LWE security.', **kwargs):
    return make_paper_record(title=title,abstract=abstract,source='iacr_eprint',source_url='https://eprint.iacr.org/2026/1',**kwargs)

def evaluate(record):
    config=load_config_bundle()
    ranked=rank_records([record],config['taxonomy'],config['keywords'],config['negative'])
    return apply_semantic_consequence_analysis_v3(ranked)[0]

@pytest.mark.parametrize('fixture',FIXTURES,ids=[f['source_record']['title'] for f in FIXTURES])
def test_real_source_canaries(fixture):
    record=evaluate(make_paper_record(**fixture['source_record']))
    title=record.title.lower()
    assert record.relevance_label==score_to_label(record.relevance_score)
    topics=set(source_topics(record))
    if 'adelic' in title:
        assert record.relevance_scope==Scope.DIRECT_LATTICE_HARDNESS_THEORY
        assert not topics & {'LWE','MLWE','ML-KEM','Module-SIS','Cryptanalysis'}
        assert 'Lattice Reduction' in topics
        assert 'RESEARCH_HYPOTHESIS_NOT_PAPER_CLAIM' in why_it_matters(record)
    elif 'trapdoor projective' in title:
        assert record.relevance_label=='A' and 'LWE' in topics
        assert not topics & {'ML-KEM','Module-SIS','PQC Implementation','ML-DSA','Falcon','FHE'}
        assert 'ML-KEM' not in why_it_matters(record)
    elif 'sqisign' in title:
        assert record.relevance_scope==Scope.LATTICE_METHOD_IN_ADJACENT_CRYPTO
        assert record.relevance_label=='C' and record.relevance_score<=59
    elif 'ldvr' in title:
        assert record.relevance_label=='D'
    elif 'exact svp' in title:
        assert record.relevance_scope==Scope.DIRECT_LATTICE_HARDNESS_THEORY
        assert 'Cryptanalysis' not in topics
    else:
        assert record.relevance_label=='A'
        if 'ansa-ibs' in title:
            assert 'Lattice Trapdoor' in topics and 'Lattice Signatures' in topics
            assert 'Lattice ZK' not in topics
        if 'provable subexponential' in title:
            assert 'LWE' in topics and 'ML-KEM' not in topics and 'MLWE' not in topics
            assert any('does not directly apply to ml-kem' in s for s in record.source_limitations)
            assert 'does not directly apply to ml-kem' in why_it_matters(record)
    assert EvidenceType.MODEL_INFERENCE not in {i['evidence_type'] for i in record.evidence_items}

@pytest.mark.parametrize('method',['side-channel attack','fault injection','masking','hybrid attack','constant-time implementation','generic signature'])
def test_generic_methods_require_source_lattice_target(method):
    unrelated=paper('Threshold Schnorr signatures',f'We study {method} against Schnorr signatures.')
    poisoned=unrelated.model_copy(update={'taxonomy_tags':['ML-KEM','Module-SIS'],'source_evidence_terms':['LWE'],
        'inferred_topic_tags':['neighbor:FND.LWE'],'reason':'LWE attack','user_relevance_tags':['LWE']})
    assert evaluate(poisoned).relevance_label=='D'
    assert 'ML-KEM' not in research_tags(poisoned)
    assert evaluate(paper('ML-KEM security',f'We study {method} against ML-KEM.')).relevance_label=='A'

def test_generated_prose_is_not_source_evidence():
    row={'title':'Enterprise monitoring','abstract':'A generic database system.',
         'reason':'LWE','why_it_matters':'Module-SIS','reason_for_priority':'ML-KEM',
         'research_hooks':['BKZ'],'advisor_questions':['NTRU'],'taxonomy_tags':['LWE']}
    assert record_text(row)=='enterprise monitoring a generic database system. '
    assert not any(t in record_text(row) for t in ['lwe','module-sis','ml-kem','bkz','ntru'])

@pytest.mark.parametrize('score,label',[(0,'D'),(39,'D'),(40,'C'),(59,'C'),(60,'B'),(79,'B'),(80,'A'),(100,'A')])
def test_single_score_label_mapping(score,label):
    assert score_to_label(score)==label

@pytest.mark.parametrize('score,label',[(80,'B'),(60,'C'),(40,'D')])
def test_semantic_verifier_rejects_inconsistent_pair(score,label):
    row=paper(relevance_score=score,relevance_label=label).model_dump()
    qa=semantic_qa({'records':[row]},'# Daily',candidate=True)
    assert qa['status']=='FAIL' and 'RELEVANCE_SCORE_LABEL_INCONSISTENT' in qa['issues']

def test_aliases_stay_in_inference_and_never_source_taxonomy():
    record=evaluate(paper('LWE cryptanalysis with BKZ','LWE lattice cryptanalysis using BKZ.'))
    assert 'lattice_reduction_cryptanalysis' in ' '.join(record.inferred_topic_tags)
    assert 'lattice_reduction_cryptanalysis' not in record.taxonomy_tags
    assert 'lattice_reduction_cryptanalysis' not in record.source_taxonomy_tags

def test_recency_is_not_an_intrinsic_value_floor():
    record=evaluate(paper('Structured module lattices','LLL reduction of module lattices and SVP.'))
    common=dict(selected_date_basis='publication_date',venue_status='preprint')
    fresh=calibrate_recommendation(record,freshness_bucket='primary_today_new',primary_today_new_eligible=True,**common)
    old=calibrate_recommendation(record,freshness_bucket='historical_backfill',primary_today_new_eligible=False,**common)
    assert fresh.research_value_score==old.research_value_score
    assert fresh.recommendation_score<=fresh.research_value_score
    assert fresh.recommendation_level!='Strong' if fresh.research_value_score<85 else True
    assert fresh.freshness_urgency==100 and old.freshness_urgency==0

def test_single_and_merged_health_provenance():
    record=paper(source_ids=[{'source':'iacr_eprint'},{'source':'arxiv'}])
    rows=[{'source':'iacr_eprint','health_status':'green'},{'source':'arxiv','health_status':'red'}]
    merged=propagate_source_health([record],rows)[0]
    assert merged.source_health=='red' and set(merged.source_health_provenance)=={'arxiv','iacr_eprint'}
    single=propagate_source_health([paper()],rows)[0]
    assert single.source_health=='green'
    result=calibrate_recommendation(merged,freshness_bucket='primary_today_new',primary_today_new_eligible=True,selected_date_basis='publication_date')
    assert 'source_health_red' in result.recommendation_risk_flags

def quality(day,status='PASS',structural=True,degraded=True):
    return (date.fromisoformat(day),{'records':[{'title':'preserved LWE evidence'}], '_daily_input_quality':{
        'date':day,'structural_valid':structural,'semantic_valid':status=='PASS','semantic_status':status,
        'source_degraded':degraded,'fully_valid':structural and status=='PASS' and not degraded,'legacy_fallback':False}})

@pytest.mark.parametrize('status,structural,expected',[
    ('PASS',True,'AUTHORITATIVE_DEGRADED'),('PASS',False,'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'),
    ('UNKNOWN',True,'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'),('FAIL',True,'PARTIAL_VERIFY_FIRST')])
def test_period_authority_states(status,structural,expected):
    assert summarize_daily_inputs([quality('2026-09-21',status,structural)],[])['authority_state']==expected

def test_w39_missing_and_w40_valid_degraded():
    w39=[quality(f'2026-09-{d:02d}') for d in [21,22,23,24,26]]
    assert summarize_daily_inputs(w39,['2026-09-25','2026-09-27'])['authority_state']=='INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'
    w40=[quality(f'2026-09-{d:02d}') for d in [28,29,30]]+[quality(f'2026-10-{d:02d}') for d in [1,2,3,4]]
    assert summarize_daily_inputs(w40,[])['authority_state']=='AUTHORITATIVE_DEGRADED'

def test_secondary_and_enrichment_failures_visible_but_not_required():
    config=[{'name':'renamed_primary','source_roles':['DISCOVERY_PRIMARY']},
            {'name':'renamed_secondary','source_roles':['DISCOVERY_SECONDARY'],'required_for_authority':False},
            {'name':'renamed_metadata','source_roles':['METADATA_ENRICHMENT']}]
    rows=[{'source':'renamed_primary','health_status':'green','runtime_state':'complete'}]
    decision=derive_authority([],rows,source_configs=config)
    assert not decision['source_coverage']['incomplete_required_sources']
    assert set(decision['source_coverage']['degraded_sources'])=={'renamed_secondary','renamed_metadata'}

def test_raw_and_validated_classification_are_separate():
    fixture=next(f for f in FIXTURES if f['source_record']['title'].startswith('Adelic'))
    row={**fixture['source_record'],'relevance_score':80,'relevance_label':'B'}
    original=dict(row)
    report=classification_summary([row])
    assert row==original and report['provenance_label_counts']=={'B':1}
    assert report['validated_label_counts']=={'A':1}
    assert report['classification_conflict_count']==1
    assert report['classification_quality_state']=='CONFLICTS_VERIFY_FIRST'

def test_machine_gates_reject_inference_and_unsupported_direct_relations():
    record=propagate_source_health([evaluate(paper())],[{'source':'iacr_eprint','health_status':'green'}])[0]
    assert not evidence_quality_issues(record)
    corrupt=record.model_copy(update={'source_concept_ids':['PRIM.ML_KEM'],
        'research_relations':[{'topic':'ML-KEM','strength':'DIRECT'}],
        'evidence_items':[{'concept_id':'PRIM.ML_KEM','evidence_type':'MODEL_INFERENCE'}]})
    issues=evidence_quality_issues(corrupt)
    assert {'INFERENCE_TO_EVIDENCE_FEEDBACK','GENERATED_PROSE_AS_SOURCE_EVIDENCE',
            'ONTOLOGY_COANCHOR_POLICY_VIOLATION','UNSUPPORTED_DIRECT_RESEARCH_RELATION'}<=set(issues)

def test_typed_relations_do_not_expand_mentions_into_claims():
    record=evaluate(paper('Structured module lattices','We study module lattices and generalized LLL.'))
    assert all(edge['relation_type']=='MENTIONS' for edge in record.consequence_edges)
    assert all(edge['evidence_type']=='SOURCE_RELATION' for edge in record.consequence_edges)
    adjacent=evaluate(paper('Quaternion ideals for SQIsign','We use quaternion lattice reduction and BKZ in SQIsign.'))
    assert adjacent.relevance_label=='C'
    assert not any(edge['target_node']=='FND.MLIP' for edge in adjacent.consequence_edges)
    incidental=evaluate(paper('Image recovery','A lattice-based reconstruction algorithm makes integer images recoverable using LLL.'))
    assert not any(edge['target_node']=='PRIM.AKE' for edge in incidental.consequence_edges)

def test_negative_applicability_is_distinct_from_negative_security_conditions():
    contribution=evaluate(paper('LWE protocol','We construct an LWE protocol that does not require a trusted setup.'))
    assert contribution.relevance_label=='A' and 'LWE' in source_topics(contribution)
    negative=evaluate(paper('Generic machine learning','We study learning without cryptography, LWE, or lattice cryptanalysis.'))
    assert negative.relevance_label=='D' and not source_topics(negative)

def test_source_health_is_preserved_when_no_new_observation_exists():
    record=propagate_source_health([evaluate(paper())],[{'source':'iacr_eprint','health_status':'green'}])[0]
    again=propagate_source_health([record],[])[0]
    assert again.source_health_provenance==record.source_health_provenance
    assert again.source_health=='green'
    missing=propagate_source_health([evaluate(paper())],[])[0]
    assert 'SOURCE_HEALTH_PROVENANCE_MISSING_FOR_SELECTED' in evidence_quality_issues(missing)
