"""Retrospective radar scope corrections; frozen publication policies stay intact."""
import hashlib
import re

from lattice_digest.scientific_scope import evaluate_scope as frozen_scope


def evaluate_scope(row):
    result = frozen_scope(row)
    get = row.get if isinstance(row, dict) else lambda key, default='': getattr(row, key, default)
    title, abstract = str(get('title') or ''), str(get('abstract') or '')
    positive = ' '.join(sentence for sentence in re.split(r'(?<=[.!?])\s+', abstract)
                        if not re.search(r'\b(?:unrelated|baseline|background|not our|not (?:evaluate|study|implement|concern))\b', sentence, re.I))
    if (re.search(r'\b(?:block (?:code )?basis reduction|code basis reduction)\b', title, re.I)
            and re.search(r'\b(?:MWC|minimum weight codeword)\b', abstract, re.I)
            and not re.search(r'\b(?:lattices?|LWE|SIS|NTRU|CVP|SVP)\b', title, re.I)):
        result.update(scientific_scope='GENERAL_CRYPTO_BACKGROUND', score=49,
                      lattice_relevance_qualified=False,
                      scope_reason='V44_CODE_REDUCTION_ANALOGY: primary object is linear codes; lattice-inspired algorithm is not a lattice result')
        for role in result['source_relation_roles']:
            role['qualifies_lattice_scope'] = False
        return result
    structured_hints = (re.search(r'\bhints?\b', title, re.I)
                        and re.search(r'\bLWE\b', positive)
                        and re.search(r'\bWe illustrate\b.{0,200}\bstructured leakage\b.{0,200}\bring and module lattice implementations\b', positive, re.I))
    implementation = (re.search(r'\b(?:SIMD|SHAKE|Keccak)\b', title, re.I)
                      and re.search(r'\bWe evaluate\b.{0,80}\b(?:ML[ -](?:KEM|DSA)|Kyber|Dilithium|HAETAE)\b', positive, re.I)
                      and re.search(r'\b(?:ML[ -](?:KEM|DSA)|HAETAE)\b.{0,50}\b(?:speedups|signing|verification)\b', positive, re.I))
    if structured_hints or implementation:
        result['source_relation_roles'].append({
            'role': 'ATTACK_TARGET' if structured_hints else 'PRIMARY_RESEARCH_OBJECT',
            'technical_target': 'structured lattice hints' if structured_hints else 'named lattice scheme SIMD implementation',
            'source_field': 'abstract', 'source_excerpt': abstract, 'source_url': get('source_url'),
            'source_sha256': hashlib.sha256(abstract.encode()).hexdigest(),
            'evidence_status': 'SOURCE_SPAN_MODEL_INTERPRETATION', 'qualifies_lattice_scope': True,
            'is_core_term': True, 'negative_applicability': False,
            'rule': 'radar-scope-v44-explicit-structured-hints-or-measured-implementation'})
        result.update(scientific_scope='CORE_LATTICE_CRYPTO' if structured_hints else 'LATTICE_RELEVANT_IMPLEMENTATION',
                      score=90, lattice_relevance_qualified=True,
                      scope_reason='RETROSPECTIVE_SCOPE_CORRECTION_V44: explicit source-backed lattice target; author-reported results only')
        return result
    if result['lattice_relevance_qualified']:
        return result
    if not (re.search(r'\b(?:NTT|number[ -]theoretic[ -]transform)', title, re.I)
            and re.search(r'\bfaults?\b', title, re.I)):
        return result
    for sentence in re.split(r'(?<=[.!?])\s+', abstract):
        if (re.search(r'\b(?:ML[ -](?:KEM|DSA)|Kyber|Dilithium)\b', sentence, re.I)
                and re.search(r'\bcompute\w*\b.{0,100}\b(?:number[ -]theoretic[ -]transforms?|NTT)\b.{0,60}\bsecret\b', sentence, re.I)
                and not re.search(r'\b(?:not|unrelated|without|comparison|baseline)\b', sentence, re.I)):
            result['source_relation_roles'].append({
                'role': 'ATTACK_TARGET', 'technical_target': 'secret NTT of named ML-KEM/ML-DSA primitive',
                'source_field': 'abstract', 'source_excerpt': sentence,
                'source_url': get('source_url'), 'source_sha256': hashlib.sha256(abstract.encode()).hexdigest(),
                'evidence_status': 'SOURCE_SPAN_MODEL_INTERPRETATION',
                'qualifies_lattice_scope': True, 'is_core_term': True,
                'negative_applicability': False, 'rule': 'radar-scope-v44-source-bound-ntt-fault-target'})
            result.update(scientific_scope='LATTICE_RELEVANT_IMPLEMENTATION', score=90,
                          lattice_relevance_qualified=True,
                          scope_reason='RETROSPECTIVE_SCOPE_CORRECTION_V44: named lattice primitive secret transform is explicit fault target; no mathematical break claim')
            break
    return result
