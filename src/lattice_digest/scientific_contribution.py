"""Versioned, source-grounded reading taxonomy; never changes selection scores.

Categories describe contribution objects, not verified theorem/security status.
Only original title/abstract fields are considered. Generated tags and owner notes
cannot establish a lattice relationship or a technical contribution.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from enum import StrEnum

from lattice_digest.scientific_scope import evaluate_scope

VERSION = 'scientific-contribution-v3.1'


class Contribution(StrEnum):
    FOUNDATIONS = 'LATTICE_FOUNDATIONS'
    ALGORITHMS = 'LATTICE_ALGORITHMS'
    CRYPTANALYSIS = 'LATTICE_CRYPTANALYSIS'
    PRIMITIVES = 'LATTICE_PRIMITIVES'
    IMPLEMENTATIONS = 'LATTICE_IMPLEMENTATIONS'
    APPLICATIONS = 'LATTICE_APPLICATIONS'
    ADJACENT = 'ADJACENT_PQC'
    NON_LATTICE = 'NON_LATTICE'
    VERIFY_FIRST = 'VERIFY_FIRST'


LABELS = {
    Contribution.FOUNDATIONS: '格数学与困难性基础',
    Contribution.ALGORITHMS: '格算法与约简',
    Contribution.CRYPTANALYSIS: '格密码分析',
    Contribution.PRIMITIVES: '基于格的密码原语与方案',
    Contribution.IMPLEMENTATIONS: '格方案实现与物理安全',
    Contribution.APPLICATIONS: '格方案接口与应用',
    Contribution.ADJACENT: '邻接 PQC 与综述背景',
    Contribution.NON_LATTICE: '非格研究',
    Contribution.VERIFY_FIRST: '技术对象待核验',
}

_APPLICATION = r'\b(?:blockchains?|TLS|network protocols?|e[ -]voting|device binding|Internet of Things|IoT|applications?|deployment|migration)\b'
_IMPLEMENTATION = r'\b(?:implementation|implementing|implemented|key generation|side[ -]channel|single[ -]trace|leakage|masking|fault|hardware|fixed[ -]point|FPGA|AVX|RNS|NTT)\b'
_ATTACK = r'\b(?:cryptanalysis|cryptanalytic|attacks?|key recovery|collision attacks?|dual lattice|MATZOV)\b'
_ALGORITHM = r'\b(?:SVP|CVP|BDD|BKZ|LLL|algorithms?|sieving|enumeration|lattice reduction|shortest vector|polynomial space)\b'
_FOUNDATION = r'\b(?:hardness|isomorphisms?|reductions?|space[ -]time|hinted ISIS|module[ -](?:SIS|LWE))\b'
_PRIMITIVE = r'\b(?:construct\w*|signatures?|commitments?|encryption|KEM|ABE|SNARKs?|proof systems?|pseudorandom codes?|polynomial commitment|bootstrapping|FHE)\b'


def _text(row, key):
    value = str(row.get(key) or '')
    return '' if re.match(r'(?i)\s*(?:TODO_VERIFY|model-generated|generated|系统生成)', value) else value


def contribution_view(row: dict) -> dict:
    """Explain a display decision without modifying row, event or frozen A/B/C/D."""
    title, abstract = _text(row, 'title'), _text(row, 'abstract')
    text = unicodedata.normalize('NFKC', title + ' ' + abstract)
    title_n = unicodedata.normalize('NFKC', title)
    decision = evaluate_scope({'title': title, 'abstract': abstract, 'source_url': row.get('source_url')})
    qualified = decision['lattice_relevance_qualified']
    kind = ('SURVEY_OR_SOK' if re.search(r'\b(?:SoK|survey|landscape|systematization)\b', title_n, re.I)
            else 'DISSERTATION' if row.get('document_type')=='dissertation' or re.search(r'\b(?:PhD|thesis|dissertation)\b', title_n, re.I)
            else 'RESEARCH_PAPER')
    rule = 'unverified-object'
    if not title or not row.get('source_url'):
        category = Contribution.VERIFY_FIRST
    elif not qualified:
        category = Contribution.ADJACENT if decision['scientific_scope'] == 'ADJACENT_PQC' else Contribution.NON_LATTICE
        rule = 'unqualified-original-source-scope'
    elif kind == 'SURVEY_OR_SOK':
        category, rule = Contribution.ADJACENT, 'survey-is-not-new-algorithm'
    elif kind == 'DISSERTATION':
        category, rule = Contribution.FOUNDATIONS, 'source-identified-dissertation-synthesis'
    elif re.search(_ATTACK, title_n, re.I):
        category, rule = Contribution.CRYPTANALYSIS, 'qualified-primary-attack-target'
    elif decision['scientific_scope'] == 'LATTICE_RELEVANT_IMPLEMENTATION' or re.search(_IMPLEMENTATION, title_n, re.I):
        category, rule = Contribution.IMPLEMENTATIONS, 'qualified-implementation-or-physical-target'
    elif re.search(r'\b(?:bootstrapping|CKKS|FHE)\b',title_n,re.I) and re.search(r'\bimplementation\b',abstract,re.I) and re.search(r'\b(?:latency|throughput|milliseconds?|ms)\b',abstract,re.I):
        category, rule = Contribution.IMPLEMENTATIONS, 'qualified-homomorphic-implementation-performance'
    elif re.search(_ALGORITHM, title_n, re.I):
        category, rule = Contribution.ALGORITHMS, 'qualified-primary-lattice-algorithm'
    elif kind == 'DISSERTATION' or re.search(_FOUNDATION, title_n, re.I):
        category, rule = Contribution.FOUNDATIONS, 'qualified-foundational-object'
    elif re.search(_APPLICATION, title_n, re.I) and re.search(r'\b(?:ML[ -]KEM|ML[ -]DSA|TLS|blockchains?|deployment|migration|IoT|device binding)\b',title_n,re.I):
        category, rule = Contribution.APPLICATIONS, 'qualified-application-interface'
    elif re.search(_PRIMITIVE, text, re.I):
        category, rule = Contribution.PRIMITIVES, 'qualified-construction-object'
    else:
        category, rule = Contribution.VERIFY_FIRST, 'qualified-scope-contribution-not-resolved'
    spans = []
    seen = set()
    for role in decision['source_relation_roles']:
        if not role.get('qualifies_lattice_scope'):
            continue
        key = (role['source_field'], role['source_excerpt'])
        if key in seen:
            continue
        seen.add(key)
        spans.append({k: role[k] for k in ('source_field', 'source_excerpt', 'source_sha256', 'source_url')})
    if not spans and title:
        spans = [{'source_field': 'title', 'source_excerpt': title,
                  'source_sha256': hashlib.sha256(title.encode()).hexdigest(), 'source_url': row.get('source_url')}]
    assumptions = list(dict.fromkeys(r['technical_target'] for r in decision['source_relation_roles']
        if r['role'] == 'LATTICE_HARDNESS_ASSUMPTION' and r.get('qualifies_lattice_scope')))
    return {'taxonomy_version': VERSION, 'category': category.value, 'category_zh': LABELS[category],
            'contribution_kind': kind, 'classification_rule': rule, 'source_spans': spans,
            'assumptions_from_source': assumptions,
            'evidence_confidence': 'E2_ABSTRACT_BASED_SOURCE_INTERPRETATION' if abstract else 'E1_TITLE_ONLY_VERIFY_FIRST',
            'verification_boundary': 'SOURCE_STATEMENT_NOT_INDEPENDENT_PROOF; TODO_VERIFY_TRANSLATION; E3_FULLTEXT_NOT_VERIFIED',
            'frozen_selection_changed': False}


def role_summary(row: dict) -> str:
    roles = row.get('source_relation_roles') or []
    return '; '.join(dict.fromkeys(str(r.get('role')) + ': ' + str(r.get('technical_target'))
                                  for r in roles if isinstance(r, dict))) or '来源角色待核验'


def abstract_guide(row: dict) -> str:
    """Conservative Chinese reading directions, explicitly not a paper translation."""
    view = contribution_view(row)
    if not _text(row, 'abstract'):
        return '仅有标题级信息（E1），无法建立摘要级技术导读；请先取得官方摘要。TODO_VERIFY_TRANSLATION；E3 全文、证明与实验尚未核验。'
    decision = evaluate_scope(row)
    targets = list(dict.fromkeys(r['technical_target'] for r in decision['source_relation_roles']
        if r.get('qualifies_lattice_scope')))
    target = '、'.join(targets[:5]) or '尚未建立直接格关联的技术对象'
    questions = {
        Contribution.FOUNDATIONS.value: '核查困难性条件、归约方向、结构限制与参数适用范围',
        Contribution.ALGORITHMS.value: '核查算法模型、时间与空间复杂度，以及最坏情况或平均情况边界',
        Contribution.CRYPTANALYSIS.value: '核查攻击目标、所需信息、参数范围与攻击成本，区分渐近结果和实用攻击',
        Contribution.PRIMITIVES.value: '核查构造接口、依赖假设、正确性与安全归约，以及与既有方案的差异',
        Contribution.IMPLEMENTATIONS.value: '核查实现精度、采样或泄漏模型、测量平台与对照条件',
        Contribution.APPLICATIONS.value: '核查格方案在协议中的接口、组合安全和部署条件；应用不等同于新格算法',
        Contribution.ADJACENT.value: '辨认综述、比较或邻接方案的证据；不能直接当作新的格安全定理',
        Contribution.NON_LATTICE.value: '先确认与格密码的实际关系，不能由密码学或神经网络措辞推导 LWE 攻击',
        Contribution.VERIFY_FIRST.value: '先核实主技术对象与原文贡献，再决定是否进入格研究阅读队列',
    }
    return (f'摘要级研究指南（E2，非全文翻译）：来源涉及{target}，阅读归类为“{view["category_zh"]}”。'
            f'{questions[view["category"]]}。这里只提供来源支持的阅读方向；作者主张尚非独立验证。'
            'TODO_VERIFY_TRANSLATION；E3 全文、证明与实验尚未核验。')
