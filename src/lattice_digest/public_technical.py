"""Reviewed abstract-bound Chinese cards; conservative fallback, no text backend.

Cards are indexed by the exact public abstract, never by a target title or a
classifier decision. Missing/changed abstracts cannot inherit a reviewed claim.
The bounded source excerpts are supporting evidence, not full-text verification.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re

CARD_PATH = Path(__file__).resolve().parents[2] / 'config/public_technical_cards.json'
PENDING = 'TECHNICAL_DETAIL_PENDING_PRIMARY_SOURCE'
FIELDS = ('object_zh', 'problem_zh', 'method_zh', 'result_zh', 'assumptions_zh',
          'significance_zh', 'verification_questions_zh')


def domain(title, topics):
    """Public descriptive grouping; never supplies event or relevance evidence."""
    if re.search(r'\b(?:side.channel|single.trace|fault|implementation|FPGA|sampling)\b',title,re.I):
        return 'LATTICE_IMPLEMENTATION'
    if re.search(r'\b(?:attack|cryptanalysis|key recovery)\b',title,re.I):
        return 'LATTICE_CRYPTANALYSIS'
    if re.search(r'\b(?:reduction|lattice|LWE|SVP|CVP)\b',title,re.I) and re.search(r'\b(?:reduction|bounds|adelic|SVP|CVP)\b',title,re.I):
        return 'DIRECT_LATTICE_MATH'
    if re.search(r'\b(?:IPsec|TLS|credentials|aggregation|deployment)\b',title,re.I):
        return 'LATTICE_APPLICATION' if topics else 'ADJACENT_PQC'
    return 'LATTICE_PRIMITIVE' if topics else 'VERIFY_FIRST'


def abstract_hash(abstract):
    return hashlib.sha256(' '.join(abstract.split()).encode('utf-8')).hexdigest()


def cards():
    value = json.loads(CARD_PATH.read_text('utf-8'))
    if value.get('schema_version') != 'public-technical-cards-v1':
        raise ValueError('unreviewed technical card schema')
    return value['cards']


def detail(abstract, url, topics):
    digest = abstract_hash(abstract)
    card = cards().get(digest)
    if card and card['source_url'] == url:
        return dict(status='REVIEWED_PUBLIC_ABSTRACT', abstract_sha256=digest,
                    **{k: card[k] for k in FIELDS})
    return dict(status=PENDING, abstract_sha256=digest,
        object_zh='、'.join(topics) or '公开元数据尚不足以确认数学对象',
        problem_zh=PENDING, method_zh=PENDING, result_zh=PENDING,
        assumptions_zh='尚未核验全文的安全模型、参数条件、证明或实验设置。',
        significance_zh='仅确认来源主题；科学贡献与适用边界待一手原文核验。',
        verification_questions_zh=['原文的数学对象、假设和结论分别是什么？',
                                   '实验或定理结论适用于哪些参数与威胁模型？'])


def check_detail(value, url, topics):
    from lattice_digest.public_report import text
    if set(value) != {'status', 'abstract_sha256', *FIELDS}:
        raise ValueError('unknown technical detail field')
    if not re.fullmatch('[a-f0-9]{64}', value['abstract_sha256']):
        raise ValueError('invalid abstract evidence hash')
    if value['status'] == 'REVIEWED_PUBLIC_ABSTRACT':
        card = cards().get(value['abstract_sha256'])
        if not card or card['source_url'] != url or any(value[k] != card[k] for k in FIELDS):
            raise ValueError('unreviewed or changed technical claim')
    elif value['status'] == PENDING:
        expected = detail('', url, topics)
        if any(value[k] != expected[k] for k in FIELDS):
            raise ValueError('arbitrary pending detail')
    else:
        raise ValueError('invalid technical detail status')
    for k in FIELDS:
        if k == 'verification_questions_zh':
            if not isinstance(value[k], list) or not 1 <= len(value[k]) <= 2:
                raise ValueError('invalid verification questions')
            for question in value[k]: text(question, 250)
        else: text(value[k], 600)
    return value
