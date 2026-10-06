"""One-way source evidence contract. Derived fields are never extraction inputs.

Legacy taxonomy/reasons remain readable for provenance, not classification.
This is deterministic scope interpretation, not a proof of a paper's claims.
"""
from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
import re
from typing import Any

from lattice_digest.ontology_v3 import load_ontology_v3, _contains_phrase

POLICY_VERSION = 'evidence-bound-v2'

class EvidenceType(StrEnum):
    SOURCE_EXPLICIT = 'SOURCE_EXPLICIT'
    SOURCE_STRUCTURAL = 'SOURCE_STRUCTURAL'
    SOURCE_RELATION = 'SOURCE_RELATION'
    MODEL_INFERENCE = 'MODEL_INFERENCE'
    USER_RESEARCH_HYPOTHESIS = 'USER_RESEARCH_HYPOTHESIS'
    GENERATED_PROSE = 'GENERATED_PROSE'

class Scope(StrEnum):
    DIRECT_LATTICE_CRYPTO = 'DIRECT_LATTICE_CRYPTO'
    DIRECT_LATTICE_HARDNESS_THEORY = 'DIRECT_LATTICE_HARDNESS_THEORY'
    LATTICE_METHOD_IN_ADJACENT_CRYPTO = 'LATTICE_METHOD_IN_ADJACENT_CRYPTO'
    ADJACENT_PQC = 'ADJACENT_PQC'
    INDIRECT_RESEARCH_HYPOTHESIS = 'INDIRECT_RESEARCH_HYPOTHESIS'
    OUT_OF_SCOPE = 'OUT_OF_SCOPE'

def field(record: Any, name: str, default=''):
    return record.get(name, default) if isinstance(record, dict) else getattr(record, name, default)

def source_fields(record: Any) -> dict[str, str]:
    """Only original paper fields; no summary, tags, rationale, or conclusion_en."""
    result = {}
    for name in ('title', 'abstract', 'conclusion'):
        value = str(field(record, name) or '').strip()
        if value.lower().startswith(('todo_verify', 'generated', 'model-generated', '系统生成', '机器生成')):
            value = ''
        result[name] = value
    return result

def source_text(record: Any) -> str:
    return ' '.join(source_fields(record).values()).lower()

def positive_source_fields(record: Any) -> dict[str, str]:
    # Negative applicability is preserved separately and cannot become a target.
    return {name: ' '.join(s for s in re.split(r'(?<=[.!?])\s+', value)
                           if not re.search(r'\b(?:(?:does? not|cannot|not directly)\b[^.!?]{0,100}\bapply|not covered|no applicability|not about|unrelated to|without (?:cryptography|cryptanalysis|LWE)|no (?:post-quantum|lattice|cryptographic) (?:or |component|context|relevance))\b', s, re.I))
            for name, value in source_fields(record).items()}

def positive_source_text(record: Any) -> str:
    return ' '.join(positive_source_fields(record).values()).lower()

def score_to_label(score: int) -> str:
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        raise ValueError('relevance score must be an integer in 0..100')
    return 'A' if score >= 80 else 'B' if score >= 60 else 'C' if score >= 40 else 'D'

TOPICS = {
    'FND.LWE':'LWE', 'FND.RLWE':'RLWE', 'FND.MLWE':'MLWE', 'FND.PLWE':'PLWE',
    'FND.LWR':'LWR', 'FND.SIS':'SIS', 'FND.MSIS':'Module-SIS', 'FND.NTRU':'NTRU',
    'FND.LIP':'Lattice Isomorphism', 'FND.MLIP':'Module-LIP',
    'PRIM.ML_KEM':'ML-KEM', 'PRIM.ML_DSA':'ML-DSA', 'PRIM.FN_DSA':'Falcon',
    'PRIM.HAWK':'HAWK', 'ATTACK.LATTICE_REDUCTION':'Lattice Reduction',
    'ATTACK.PRIMAL_DUAL_HYBRID':'Cryptanalysis', 'ATTACK.PHYSICAL':'PQC Implementation',
    'PRIM.LATTICE_SIGNATURE':'Lattice Signatures', 'PRIM.PRIVACY_SIGNATURE':'Ring Signatures',
}
STRUCTURAL_TERMS = ('module lattice', 'module lattices', 'ideal lattice', 'ideal lattices',
                    'structured lattice', 'lattice reduction', 'SVP', 'shortest vector problem',
                    'CVP', 'closest vector problem', 'lattice sieving')

@lru_cache(maxsize=2048)
def _analyze(title: str, abstract: str, conclusion: str):
    return load_ontology_v3().analyze_fields(title=title, abstract=abstract, conclusion=conclusion)

def analyze_source(record: Any, ontology=None):
    values=positive_source_fields(record)
    return ontology.analyze_fields(**values) if ontology else _analyze(**values)

def source_topics(record: Any) -> list[str]:
    analysis=analyze_source(record)
    topics=[TOPICS[c] for c in analysis.source_concept_ids if c in TOPICS]
    text=positive_source_text(record)
    ids=set(analysis.source_concept_ids)
    lattice_target=any(c.startswith(('FND.', 'PRIM.', 'HARD.')) for c in ids) or 'lattice' in text
    if any(c.startswith('FHE.') for c in ids): topics.append('FHE')
    if any(c.startswith('AI4LC.') for c in ids): topics.append('AI4Lattice')
    if _contains_phrase(text,'AI-assisted lattice attack') and _contains_phrase(text,'lattice cryptography'):
        topics.append('AI4Lattice')
    if ids & {'PROOF.LATTICE_ZK','PROOF.THRESHOLD_ZK'}: topics.append('Lattice ZK')
    if 'PROOF.FIAT_SHAMIR' in ids: topics.append('Fiat-Shamir with Aborts')
    if ids & {'IMPL.GAUSSIAN','IMPL.REJECTION'}: topics.append('Sampling')
    if any(c.startswith('IMPL.') and c not in {'IMPL.GAUSSIAN','IMPL.REJECTION'} for c in ids): topics.append('PQC Implementation')
    if any(_contains_phrase(text,t) for t in ('module lattice','module lattices')): topics.append('Module Lattice')
    if any(_contains_phrase(text,t) for t in ('SVP','shortest vector problem')) and 'lattice' in text: topics.append('SVP')
    if lattice_target:
        for topic,terms in [('Lattice Trapdoor',('trapdoor','trapdoors')),
                            ('Sampling',('projective sampling','gaussian sampling','rejection sampling')),
                            ('Anonymous Broadcast',('anonymous broadcast',)),
                            ('Commitments',('lattice commitment','sis commitment','chameleon hash')),
                            ('PQC Implementation',('implementation','side-channel','power trace','fault attack','constant-time'))]:
            if topic=='PQC Implementation' and classify_scope(record,analysis)[0]!=Scope.DIRECT_LATTICE_CRYPTO:
                continue
            if any(_contains_phrase(text,t) for t in terms):topics.append(topic)
    return list(dict.fromkeys(topics))

def classify_scope(record: Any, analysis=None, edges=()) -> tuple[str,int]:
    analysis=analysis or analyze_source(record)
    ids=set(analysis.source_concept_ids)
    text=positive_source_text(record)
    from urllib.parse import urlparse
    url=urlparse(str(field(record,'source_url') or field(record,'url') or ''))
    offline_fixture = url.scheme == 'offline' and field(record,'provenance_strength') == 'offline_fixture'
    if not field(record,'source') or not url.netloc or not (url.scheme in {'http','https'} or offline_fixture):return Scope.OUT_OF_SCOPE,0
    direct=any(c.startswith(('FND.LW','FND.RL','FND.MLW','FND.PLW','FND.SIS','FND.MSIS','FND.NTRU','FND.LIP','FND.MLIP','PRIM.','FHE.','PROOF.','AI4LC.','IMPL.')) for c in ids)
    direct = direct or (_contains_phrase(text,'AI-assisted lattice attack') and _contains_phrase(text,'lattice cryptography'))
    if analysis.hard_negative_matches and not direct:
        return Scope.OUT_OF_SCOPE,0
    if not direct and any(_contains_phrase(text,t) for t in ('lowest Landau level','layered Lieb lattice','remote sensing','integer images','Hubbard model','Bose gas','Bose-Einstein condensate')):
        return Scope.OUT_OF_SCOPE,0
    adjacent=any(_contains_phrase(text,t) for t in ('SQIsign','isogeny','isogeny-based','Schnorr','ECDSA','factoring','Coppersmith','RSA'))
    structural=any(_contains_phrase(text,t) for t in STRUCTURAL_TERMS) or 'ATTACK.LATTICE_REDUCTION' in ids
    if adjacent and not direct:
        return (Scope.LATTICE_METHOD_IN_ADJACENT_CRYPTO,49) if structural else ((Scope.ADJACENT_PQC,45) if 'post-quantum' in text else (Scope.OUT_OF_SCOPE,0))
    direct = direct or any(e.get('evidence_state') in {'SOURCE_ASSERTED','SOURCE_CITED','INDEPENDENTLY_VERIFIED'} and str(e.get('target_node','')).startswith(('PRIM.','PROOF.','FHE.')) for e in edges)
    if direct:
        return Scope.DIRECT_LATTICE_CRYPTO,90 if field(record,'abstract') else 80
    typed=any(e.get('evidence_state') in {'SOURCE_ASSERTED','SOURCE_CITED','INDEPENDENTLY_VERIFIED'} and e.get('relation_type') != 'MENTIONS' and str(e.get('target_node','')).startswith(('FND.','HARD.')) for e in edges)
    grounded_reduction = any(c.startswith(('RED.','ATTACK.PRIMAL_DUAL_HYBRID')) for c in ids) and 'lattice' in text
    foundational = any(_contains_phrase(text,t) for t in ('SVP','CVP','shortest vector problem','closest vector problem','lattice reduction','lattice sieving','LLL','BKZ','enumeration','sieve algorithms','hardness'))
    if typed or grounded_reduction or structural and foundational and ('lattice' in text or 'cryptograph' in text or 'cryptanalysis' in text) or any(c.startswith(('HARD.SVP','HARD.CVP','HARD.STRUCTURED_CVP','ATTACK.QUATERNION')) for c in ids):
        if analysis.hard_negative_matches and not ids:return Scope.OUT_OF_SCOPE,0
        return Scope.DIRECT_LATTICE_HARDNESS_THEORY,82 if field(record,'abstract') else 70
    if any(c.startswith('STD.') for c in ids):return Scope.ADJACENT_PQC,55
    if any(_contains_phrase(text,t) for t in ('post-quantum','PQC','quantum-safe')):return Scope.ADJACENT_PQC,45
    return Scope.OUT_OF_SCOPE,0

def source_scope_score(record, analysis=None, edges=()):
    """The final source classification, including independently extracted critical claims."""
    analysis=analysis or analyze_source(record)
    source_url=str(field(record,'source_url') or field(record,'url') or '')
    if not source_url or not field(record,'source'):
        return Scope.OUT_OF_SCOPE,0
    if not edges:
        from lattice_digest.consequence_graph_v3 import extract_record_edges
        edges=[e.model_dump(mode='json') for e in extract_record_edges(
            paper_node='paper:source-validation', **positive_source_fields(record),
            source_url=source_url, source_concept_ids=analysis.source_concept_ids)]
    scope,score=classify_scope(record,analysis,edges)
    from lattice_digest.critical_security import analyze_critical_security_signal
    from types import SimpleNamespace
    original=SimpleNamespace(**positive_source_fields(record),TODO_VERIFY_flags=[],venue='')
    critical=analyze_critical_security_signal(original).is_critical or any(
        e.get('critical_eligible') and e.get('evidence_state') in {'SOURCE_ASSERTED','SOURCE_CITED','INDEPENDENTLY_VERIFIED'} for e in edges)
    if scope in {Scope.DIRECT_LATTICE_CRYPTO, Scope.DIRECT_LATTICE_HARDNESS_THEORY} and critical:
        score=100
    return scope,score

def bind_source_evidence(record, analysis=None, edges=()):
    analysis=analysis or analyze_source(record)
    scope,score=source_scope_score(record,analysis,edges)
    topics=source_topics(record)
    structural=scope==Scope.DIRECT_LATTICE_HARDNESS_THEORY
    items=[{'evidence_type': EvidenceType.SOURCE_STRUCTURAL if structural else EvidenceType.SOURCE_EXPLICIT,
            'concept_id':m.concept_id,'source_field':m.source_field,'source_span':m.source_span,
            'source_term':m.source_term,'source_url':record.source_url} for m in analysis.source_evidence]
    relations=[{'topic':topic,'strength':'STRUCTURAL' if structural else 'DIRECT',
                'evidence_type':EvidenceType.SOURCE_STRUCTURAL if structural else EvidenceType.SOURCE_EXPLICIT,
                'source_url':record.source_url} for topic in topics]
    limitations=[s for s in re.split(r'(?<=[.!?])\s+',source_text(record)) if re.search(r'\b(?:does? not|cannot|not directly|not covered)\b',s)]
    hypotheses=[]
    if structural:
        hypotheses=[{'topic':'classical lattice attack baselines','strength':'INDIRECT',
                     'evidence_type':EvidenceType.USER_RESEARCH_HYPOTHESIS,
                     'status':'RESEARCH_HYPOTHESIS_NOT_PAPER_CLAIM',
                     'text':'这可能为经典格攻击的约简基线提供间接研究启发，但论文自身没有建立该联系。'}]
    return record.model_copy(update={'evidence_policy_version':POLICY_VERSION,'evidence_items':items,
        'consequence_edges':[dict(e, evidence_type=EvidenceType.SOURCE_RELATION if e.get('evidence_state') in {'SOURCE_ASSERTED','SOURCE_CITED','INDEPENDENTLY_VERIFIED'} else EvidenceType.MODEL_INFERENCE) for e in edges],
        'source_concept_ids':list(analysis.source_concept_ids),'source_evidence_terms':list(dict.fromkeys(m.source_term for m in analysis.source_evidence)),
        'source_taxonomy_tags':topics,'ontology_neighbor_tags':[t for t in analysis.inferred_tags if t.startswith('neighbor:')],
        'research_relations':relations,'user_research_hypotheses':hypotheses,'source_limitations':limitations,
        'relevance_scope':str(scope),'relevance_score':score,'relevance_label':score_to_label(score),
        'reading_priority':{'A':1,'B':2,'C':3,'D':99}[score_to_label(score)]})

def render_research_relations(record: Any, language='zh') -> str:
    scope,_=classify_scope(record)
    topics=source_topics(record)
    text=positive_source_text(record)
    if 'homomorphic encryption' in text and any(t in text for t in ('healthcare','analytics','gbdt','gradient boosting')) and not any(t in text for t in ('cryptanalysis','attack','hardness reduction')):
        return ('Relevant as peripheral FHE/privacy-computing background; not a core lattice attack or parameter result.' if language=='en' else
                '来源支持同态加密应用背景；作为 peripheral/temporary track，而不是核心格攻击或参数估计结果。')
    if language == 'en':
        prefix='Source-supported lattice reduction/hardness theory: ' if scope==Scope.DIRECT_LATTICE_HARDNESS_THEORY else 'Source-supported topics: '
        text=prefix+', '.join(topics)+'.' if topics else 'No direct lattice-cryptography relationship established by the source.'
        limits=[s for s in re.split(r'(?<=[.!?])\s+',source_text(record)) if re.search(r'\b(?:does? not|not directly|not covered)\b',s)]
        return text+' Source limitations: '+' '.join(limits) if limits else text
    prefix='论文直接贡献于格约简/格困难性研究：' if scope==Scope.DIRECT_LATTICE_HARDNESS_THEORY else '论文直接研究：'
    text=prefix+'、'.join(topics)+'。' if topics else '来源未建立直接格密码联系；仅作背景线索。'
    for sentence in re.split(r'(?<=[.!?])\s+',source_text(record)):
        if re.search(r'\b(?:does? not|not directly|not covered)\b',sentence):text+='来源限制：'+sentence+' '
    if scope==Scope.DIRECT_LATTICE_HARDNESS_THEORY:
        text+=' RESEARCH_HYPOTHESIS_NOT_PAPER_CLAIM：这可能为经典格攻击的约简基线提供间接研究启发，但论文自身没有建立该联系。'
    return text

def propagate_source_health(records, health_rows):
    observed={str(r.get('source')):dict(r) for r in health_rows if isinstance(r,dict)}
    result=[]
    for record in records:
        sources=set(s.strip() for s in record.source.split(',') if s.strip())
        sources.update(str(s.get('source')) for s in record.source_ids if s.get('source'))
        existing=field(record,'source_health_provenance',{})
        provenance={s:observed.get(s,existing.get(s,{'source':s,'health_status':field(record,'source_health') or 'unknown','observed':bool(field(record,'source_health'))})) for s in sorted(sources)}
        statuses=[str(p.get('health_status') or p.get('status') or 'unknown') for p in provenance.values()]
        status=max(statuses,key=lambda s:{'green':0,'yellow':1,'unknown':2,'red':3}.get(s,2)) if statuses else 'unknown'
        result.append(record.model_copy(update={'source_health':status,'source_health_provenance':provenance}))
    return result

def classification_summary(records):
    from collections import Counter
    provenance=Counter();validated=Counter();conflicts=[]
    for row in records:
        old=str(field(row,'relevance_label') or 'D');score=field(row,'relevance_score',0)
        scope,new_score=source_scope_score(row);new=score_to_label(new_score)
        provenance[old]+=1;validated[new]+=1
        if old!=new or score!=new_score:
            conflicts.append({'title':field(row,'title'),'source_url':field(row,'source_url'),
                              'provenance_label':old,'provenance_score':score,'validated_label':new,
                              'validated_score':new_score,'validated_scope':str(scope)})
    return {'provenance_label_counts':dict(provenance),'validated_label_counts':dict(validated),
            'classification_conflict_count':len(conflicts),'classification_conflicts':conflicts,
            'classification_quality_state':'CONFLICTS_VERIFY_FIRST' if conflicts else 'VALIDATED_CONSISTENT'}

def evidence_quality_issues(record: Any) -> list[str]:
    issues=[]
    score=field(record,'relevance_score',0)
    try:
        if score_to_label(score)!=field(record,'relevance_label'):issues.append('RELEVANCE_SCORE_LABEL_INCONSISTENT')
    except ValueError:issues.append('RELEVANCE_SCORE_LABEL_INCONSISTENT')
    if field(record,'evidence_policy_version')!=POLICY_VERSION:return issues
    scope,_=classify_scope(record)
    cap={Scope.DIRECT_LATTICE_CRYPTO:100,Scope.DIRECT_LATTICE_HARDNESS_THEORY:100,
         Scope.LATTICE_METHOD_IN_ADJACENT_CRYPTO:59,Scope.ADJACENT_PQC:59,
         Scope.INDIRECT_RESEARCH_HYPOTHESIS:59,Scope.OUT_OF_SCOPE:39}[scope]
    if isinstance(score,int) and score>cap:issues.append('ONTOLOGY_COANCHOR_POLICY_VIOLATION')
    expected=analyze_source(record);ids=set(expected.source_concept_ids)
    if set(field(record,'source_evidence_terms',[])) != {m.source_term for m in expected.source_evidence}:
        issues.append('INFERENCE_TO_EVIDENCE_FEEDBACK')
    if set(field(record,'source_concept_ids',[]))!=ids:issues.append('INFERENCE_TO_EVIDENCE_FEEDBACK')
    topics=set(source_topics(record))
    if set(field(record,'source_taxonomy_tags',[]))!=topics:issues.append('INFERENCE_TO_EVIDENCE_FEEDBACK')
    for item in field(record,'evidence_items',[]):
        if item.get('evidence_type') not in {e.value for e in EvidenceType if e.value.startswith('SOURCE_')}:
            issues.append('GENERATED_PROSE_AS_SOURCE_EVIDENCE')
        if item.get('concept_id') not in ids:issues.append('ONTOLOGY_COANCHOR_POLICY_VIOLATION')
        original=source_fields(record).get(item.get('source_field'), '')
        if not item.get('source_span') or not _contains_phrase(original,str(item.get('source_span',''))):issues.append('GENERATED_PROSE_AS_SOURCE_EVIDENCE')
    for relation in field(record,'research_relations',[]):
        if relation.get('strength') in {'DIRECT','STRUCTURAL'} and (relation.get('topic') not in topics or relation.get('evidence_type') not in {'SOURCE_EXPLICIT','SOURCE_STRUCTURAL','SOURCE_RELATION'}):
            issues.append('UNSUPPORTED_DIRECT_RESEARCH_RELATION')
    provenance=field(record,'source_health_provenance',{})
    if field(record,'relevance_label') in {'A','B','C'} and (not provenance or field(record,'source_health') not in {'green','yellow','red'} or any(p.get('health_status',p.get('status')) not in {'green','yellow','red'} for p in provenance.values())):
        issues.append('SOURCE_HEALTH_PROVENANCE_MISSING_FOR_SELECTED')
    return sorted(set(issues))

def quality_gate_report(records, *, missing_days=(), period_authority=None):
    """Measured invariants over records, separate from source coverage authority."""
    from collections import Counter
    rows=list(records)
    counts=Counter(issue for row in rows for issue in evidence_quality_issues(row))
    total=len(rows)
    return {
        'evaluated_records':total,
        'RELEVANCE_SCORE_LABEL_CONSISTENCY':100.0*(total-counts['RELEVANCE_SCORE_LABEL_INCONSISTENT'])/total if total else 100.0,
        'INFERENCE_TO_EVIDENCE_FEEDBACK':counts['INFERENCE_TO_EVIDENCE_FEEDBACK'],
        'GENERATED_PROSE_AS_SOURCE_EVIDENCE':counts['GENERATED_PROSE_AS_SOURCE_EVIDENCE'],
        'ONTOLOGY_COANCHOR_POLICY_VIOLATIONS':counts['ONTOLOGY_COANCHOR_POLICY_VIOLATION'],
        'UNSUPPORTED_DIRECT_RESEARCH_RELATION':counts['UNSUPPORTED_DIRECT_RESEARCH_RELATION'],
        'SOURCE_HEALTH_PROVENANCE_MISSING_FOR_SELECTED':counts['SOURCE_HEALTH_PROVENANCE_MISSING_FOR_SELECTED'],
        'PERIOD_MISSING_INPUT_FALSE_DEGRADED':int(bool(missing_days) and period_authority=='AUTHORITATIVE_DEGRADED'),
    }

def assert_quality_gates(report):
    failures={key:value for key,value in report.items() if key!='evaluated_records' and
              value != (100.0 if key=='RELEVANCE_SCORE_LABEL_CONSISTENCY' else 0)}
    if failures:raise ValueError('Evidence-bound quality gates failed: '+str(failures))
