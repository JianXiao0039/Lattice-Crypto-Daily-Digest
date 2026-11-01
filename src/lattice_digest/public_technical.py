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
    if value.get('status') == 'SOURCE_GROUNDED_ABSTRACT_V44':
        excerpt = value.get('source_excerpt', '')
        text(excerpt, 500)
        expected = grounded_detail(excerpt, url, topics)
        if value != expected:
            raise ValueError('unsupported source-grounded technical claim')
        return value
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


def grounded_detail(abstract, url, topics):
    """Bounded literal evidence; E2 means abstract read, never full-text verified.

    This is deliberately extractive. Author statements remain quotations, not
    independently established results. No model, API key or hand-written card.
    The calling projection must bind the input to its verified source row.
    """
    normalized = ' '.join(abstract.split())
    bounded = ' '.join(normalized.split()[:24])
    excerpt = bounded[:500]
    if len(bounded) > 500:
        excerpt = excerpt.rsplit(' ', 1)[0]
    return dict(status='SOURCE_GROUNDED_ABSTRACT_V44',
        extraction_contract='literal-official-abstract-v1', evidence_level='E2',
        source_excerpt=excerpt, source_excerpt_sha256=abstract_hash(excerpt),
        object_zh='、'.join(topics) or '数学对象需对照下列作者摘要核验',
        problem_zh='作者摘要摘录给出问题与动机；未独立核验全文。',
        method_zh='方法仅以下列作者原文摘录为依据；未补充来源未述的算法。',
        result_zh='作者报告（原文有界摘录）：'+excerpt,
        assumptions_zh='摘要不能穷尽假设；安全模型、参数与定理条件须核对全文。',
        significance_zh='用于科研阅读定位；不构成独立证明、性能比较或标准安全裁决。',
        verification_questions_zh=['全文的问题、方法及结论是否支持摘要表述？',
                                   '最近工作、参数、基线与局限分别是什么？'])
