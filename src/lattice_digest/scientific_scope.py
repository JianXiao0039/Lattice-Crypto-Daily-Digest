"""Primary-object scope from quoted original source fields, never generated tags.

Roles are auditable deterministic interpretations, not verified paper theorems.
Unknown relations stay background; ontology neighbors cannot supply evidence.
"""
from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from functools import lru_cache
from enum import StrEnum
from typing import Any


class RelationRole(StrEnum):
    PRIMARY_RESEARCH_OBJECT = 'PRIMARY_RESEARCH_OBJECT'
    LATTICE_HARDNESS_ASSUMPTION = 'LATTICE_HARDNESS_ASSUMPTION'
    SECURITY_TARGET = 'SECURITY_TARGET'
    IMPLEMENTED_PRIMITIVE = 'IMPLEMENTED_PRIMITIVE'
    ATTACK_TARGET = 'ATTACK_TARGET'
    METHOD_SUBROUTINE = 'METHOD_SUBROUTINE'
    COMPARISON_BASELINE = 'COMPARISON_BASELINE'
    BACKGROUND_MENTION = 'BACKGROUND_MENTION'
    ONTOLOGY_NEIGHBOR = 'ONTOLOGY_NEIGHBOR'
    USER_RESEARCH_HYPOTHESIS = 'USER_RESEARCH_HYPOTHESIS'


class ScientificScope(StrEnum):
    CORE = 'CORE_LATTICE_CRYPTO'
    FOUNDATION = 'FOUNDATIONAL_LATTICE_THEORY'
    IMPLEMENTATION = 'LATTICE_RELEVANT_IMPLEMENTATION'
    ADJACENT = 'ADJACENT_PQC'
    GENERAL = 'GENERAL_CRYPTO_BACKGROUND'
    OUT = 'OUT_OF_SCOPE'


QUALIFIED_SCOPES = {ScientificScope.CORE, ScientificScope.FOUNDATION, ScientificScope.IMPLEMENTATION}
CORE = r'\b(?:[krmpt]?lwe|mlwe|learning[ -]with[ -]errors|learning[ -]with[ -]rounding|lwr|(?:module[ -]|ring[ -])?sis|short[ -]integer[ -]solution|ntru(?:encrypt)?|kyber|ml[ -]kem|dilithium|ml[ -]dsa|falcon|fn[ -]dsa|frodokem|(?:light|fire)?saber|newhope|qtesla|hawk|haetae|raccoon|(?:module[ -])?lip|lattice[ -]isomorphism|lattice[ -]based|lattice[ -](?:cryptography|signatures?|commitments?|trapdoors?)|fully[ -]homomorphic[ -]encryption|fhe|ckks|bfv|bgv|tfhe|gsw)\b'
FOUNDATION = r'\b(?:[hu]?svp|sivp|gapsvp|gapcvp|cvp|bdd|shortest[ -]vector[ -]problem|closest[ -]vector[ -]problem|bounded[ -]distance[ -]decoding|bkz|lll|g6k|fplll|lattice[ -](?:reduction|sieving|decoding|problems?)|(?:module|ideal|q[ -]ary|structured)[ -]lattices?)\b'
NONLATTICE = r'\b(?:hqc|bike|mceliece|code[ -]based|isogen(?:y|ies)|sqisign|schnorr|rsa|ecdsa|elliptic[ -]curve|hidden[ -]subgroup|universal[ -]algebras?|blockchain)\b'
METHOD = r'\b(?:using|use|via|subroutine|inspired|based on|with the help)\b'
INTENT = r'\b(?:we (?:show|give|study|propose|present|introduce|develop|construct|analyze|analyse|optimize|implement|find|prove|obtain|use|derive|specialize|instantiate|formalise|formalize|achieve)|our (?:algorithm|attack|construction|scheme|implementation)|this (?:work|paper))\b'
COMPONENT = r'\b(?:iot|gateway|hybrid[ -](?:authenticated|ake)|authenticated[ -]key[ -]exchange|network protocol|blockchain|edge networks?)\b'
COMPARE = r'\b(?:compar(?:e|es|ed|ing|ison)|baseline|beyond|diversity|versus|vs\.?|related work|background|unlike)\b'
NON_CRYPTO_DOMAIN = r'\b(?:Landau[ -]levels?|Bose[ -](?:Einstein|gas)|Chern[ -]insulator|quantum[ -]Hall|Hubbard[ -]model|phonons?|ferroic|ferroelectric|electron[ -]microscopy|Steinberg[ -]algebras?|Leavitt[ -]path[ -]algebras?|Gibbsian[ -]particle|crystal[ -]lattice|lattice[ -]QCD|lattice[ -]Boltzmann|interatomic[ -]potentials?)\b'
CRYPTO_CONTEXT = r'\b(?:cryptograph\w*|cryptanalysis|ml[ -]kem|ml[ -]dsa|fn[ -]dsa|kyber|dilithium|ntru|learning[ -]with[ -]errors|lattice[ -](?:signatures?|trapdoors?|encryption))\b'
PHYSICAL = r'\b(?:side[ -]channel|leakage|hint weight|statistical fingerprint|fault|implementation|implement|masking|power|timing|cache|avx|fpga|cortex)\b'


def _field(row: Any, key: str, default=''):
    return row.get(key, default) if isinstance(row, dict) else getattr(row, key, default)


def evaluate_scope(row: Any) -> dict:
    return deepcopy(_evaluate_scope(str(_field(row,'title') or ''),
                                   str(_field(row,'abstract') or ''),
                                   str(_field(row,'source_url') or '')))


@lru_cache(maxsize=4096)
def _evaluate_scope(title: str, abstract: str, source_url: str) -> dict:
    row={'title':title,'abstract':abstract,'source_url':source_url}
    # conclusion is frequently generated and has no source-location provenance.
    fields = {key: str(_field(row, key) or '') for key in ('title', 'abstract')}
    fields = {k: ('' if re.match(r'(?i)\s*(?:todo_verify|model-generated|generated|系统生成)', v) else v) for k,v in fields.items()}
    title = fields['title']
    title_core = bool(re.search(CORE, title, re.I))
    title_foundation = bool(re.search(FOUNDATION, title, re.I))
    noncrypto_domain=bool(re.search(NON_CRYPTO_DOMAIN,title+' '+fields['abstract'],re.I))
    crypto_context=bool(re.search(CRYPTO_CONTEXT,title+' '+fields['abstract'],re.I))
    other_target = bool(re.search(NONLATTICE, title, re.I) or re.search(NON_CRYPTO_DOMAIN,title,re.I))
    generic_component = bool(re.search(COMPONENT, title, re.I)) and not title_core
    roles = []
    for name, text in fields.items():
        for sentence in re.split(r'(?<=[.!?])\s+', text):
            for match in re.finditer(f'(?:{CORE})|(?:{FOUNDATION})', sentence, re.I):
                term = match.group()
                lattice_core = bool(re.fullmatch(CORE, term, re.I))
                role = RelationRole.BACKGROUND_MENTION
                if term.lower() in {'lattice-based','lattice based','falcon','hawk','sis','lip'} and not re.search(r'\b(?:cryptograph\w*|cryptanalysis|signature|signatures|encryption|kem|security|trapdoor|learning|hardness|module[ -]sis|dual attacks?|lattice settings)\b',title+' '+sentence,re.I):
                    continue
                # Negative applicability does not establish an independent target.
                negative = bool(re.search(r'\b(?:not (?:directly )?(?:apply|applicable|about)|unrelated|not covered|without (?:cryptography|cryptanalysis|LWE)|no (?:lattice|cryptographic) (?:context|relevance))\b', sentence, re.I))
                local = sentence[max(0,match.start()-110):min(len(sentence),match.end()+110)]
                if negative:
                    role = RelationRole.BACKGROUND_MENTION
                elif re.search(r'\b(?:algorithm|result|reductions?)\b.{0,400}\b(?:yields?|solves?|solving|implies|imply|consequences)\b',sentence,re.I) and re.search(r'\b(?:lattice|lattices|LWE|SIS|SVP)\b',sentence,re.I):
                    role = RelationRole.SECURITY_TARGET
                elif other_target or generic_component:
                    if re.search(COMPARE, sentence, re.I):
                        role = RelationRole.COMPARISON_BASELINE
                    elif lattice_core and generic_component:
                        role = RelationRole.IMPLEMENTED_PRIMITIVE
                    elif re.search(METHOD, sentence, re.I) or (not lattice_core and re.search(r'\b(?:perform|part of|response sampling)\b',sentence,re.I)):
                        role = RelationRole.METHOD_SUBROUTINE
                    # A distinct lattice contribution must explicitly be claimed,
                    # rather than inferred from a reference to an earlier technique.
                    elif re.search(INTENT, sentence, re.I) and re.search(r'\b(?:new|novel|improved)\b.{0,35}(?:lattice|LWE|BKZ|SVP)', sentence, re.I):
                        role = RelationRole.PRIMARY_RESEARCH_OBJECT
                elif name != 'title' and re.search(COMPARE,sentence,re.I) and not re.search(INTENT,sentence,re.I):
                    role = RelationRole.COMPARISON_BASELINE
                elif name == 'title' or re.search(INTENT, sentence, re.I):
                    if re.search(r'\b(?:attack|break|cryptanalysis)\b', local, re.I):
                        role = RelationRole.ATTACK_TARGET
                    elif re.search(r'\b(?:assum(?:e|es|ing|ption)|based on|under)\b', local, re.I) and lattice_core:
                        role = RelationRole.LATTICE_HARDNESS_ASSUMPTION
                    elif re.search(PHYSICAL, local, re.I) and lattice_core:
                        role = RelationRole.SECURITY_TARGET
                    else:
                        role = RelationRole.PRIMARY_RESEARCH_OBJECT
                elif (title_core and lattice_core) or (title_foundation and not lattice_core):
                    role = RelationRole.PRIMARY_RESEARCH_OBJECT
                elif lattice_core and re.search(r'\b(?:under|assuming|based on)\b', local, re.I) and re.search(r'\b(?:signature|encryption|trapdoor|commitment|zero[ -]knowledge)\b', title+' '+sentence, re.I):
                    role = RelationRole.LATTICE_HARDNESS_ASSUMPTION
                roles.append({'role':role.value,'technical_target':term,'source_field':name,'negative_applicability':negative,
                              'source_excerpt':sentence,'source_url':_field(row,'source_url'),
                              'source_sha256':hashlib.sha256(text.encode()).hexdigest(),
                              'evidence_status':'SOURCE_SPAN_MODEL_INTERPRETATION',
                              'is_core_term':lattice_core,'rule':'primary-object-role-v1'})
    qualifying = [r for r in roles if r['role'] in {
        RelationRole.PRIMARY_RESEARCH_OBJECT, RelationRole.ATTACK_TARGET,
        RelationRole.SECURITY_TARGET, RelationRole.LATTICE_HARDNESS_ASSUMPTION}]
    # A generic proof merely assuming LWE is not a lattice construction.
    # Concrete lattice instantiation, direct target, or a lattice primary title
    # must establish the object independently of the assumption mention.
    qualifying=[r for r in qualifying if r['role']!=RelationRole.LATTICE_HARDNESS_ASSUMPTION or
        title_core or re.search(r'\bwe (?:also |first |next |then )?(?:construct|instantiate|design|develop|propose|present|give)\b',r['source_excerpt'],re.I)]
    if noncrypto_domain and not crypto_context:
        qualifying=[]
    for relation in roles:
        relation['qualifies_lattice_scope']=relation in qualifying
    core = any(r['is_core_term'] for r in qualifying)
    foundational = any(not r['is_core_term'] for r in qualifying)
    if noncrypto_domain and not crypto_context:
        scope = ScientificScope.OUT
    elif core:
        scope = ScientificScope.IMPLEMENTATION if re.search(PHYSICAL, title, re.I) else ScientificScope.CORE
    elif foundational and any(r['role']=='ATTACK_TARGET' for r in qualifying):
        scope = ScientificScope.CORE
    elif foundational:
        scope = ScientificScope.FOUNDATION
    elif roles and all(r['negative_applicability'] for r in roles):
        scope = ScientificScope.OUT
    elif re.search(r'\b(?:post[ -]quantum|pqc|hqc|bike|mceliece|sqisign|isogeny|code[ -]based)\b', ' '.join(fields.values()), re.I):
        scope = ScientificScope.ADJACENT
    elif roles or re.search(r'\b(?:cryptograph\w*|cryptanalysis|signature|encryption|schnorr|rsa|ecdsa)\b', ' '.join(fields.values()), re.I):
        scope = ScientificScope.GENERAL
    else:
        scope = ScientificScope.OUT
    score = (82 if scope == ScientificScope.FOUNDATION else 90) if fields['abstract'] else (70 if scope == ScientificScope.FOUNDATION else 80)
    if scope not in QUALIFIED_SCOPES:
        score = 49 if scope in {ScientificScope.ADJACENT,ScientificScope.GENERAL} and roles else 45 if scope == ScientificScope.ADJACENT else 0
    return {'scientific_scope':scope.value, 'score':score, 'source_relation_roles':roles,
            'lattice_relevance_qualified':scope in QUALIFIED_SCOPES,
            'scope_reason':('NON_CRYPTO_DOMAIN_EXCLUDED; ' if noncrypto_domain and not crypto_context else '')+'primary-object-role-v1; qualifying roles='+','.join(sorted({r['role'] for r in qualifying})),
            'remaining_uncertainty':'Deterministic source interpretation; no human adjudication or proof verification.'}
