"""Strict public-only projection. Canonical prose is never a renderer extension."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from typing import Literal

from lattice_digest.report_gate import VerifiedPair, GateError, encoded, fail, sha, verify, safe_file, strict_json

VERSION = 'public-literature-v1'
MAX_PUBLIC_BYTES = 1024 * 1024
QUALITY = {'PROVISIONAL_PUBLIC': 0, 'VALID_DEGRADED_AUTHORITATIVE': 1, 'VERIFIED_AUTHORITATIVE': 2}
PUBLIC_TOPICS = {'LWE','RLWE','MLWE','PLWE','LWR','SIS','Module-SIS','NTRU','Lattice Isomorphism',
    'Module-LIP','ML-KEM','ML-DSA','Falcon','HAWK','Lattice Reduction','Cryptanalysis','PQC Implementation',
    'Lattice Signatures','Ring Signatures','FHE','AI4Lattice','Lattice ZK','Fiat-Shamir with Aborts',
    'Sampling','Module Lattice','SVP','Lattice Trapdoor','Anonymous Broadcast','Commitments'}


def guide_for(topics, grade):
    if not isinstance(topics,list) or len(topics)>8 or any(t not in PUBLIC_TOPICS for t in topics):
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'unreviewed topic vocabulary')
    topic_text = '、'.join(topics) or '密码学背景'
    return (f'公开标题及摘要涉及{topic_text}。建议对照原文核对问题设定、假设、参数与实验范围。' if grade == 'E3'
            else f'公开标题涉及{topic_text}；当前仅有元数据，需先核对公开摘要与原文。')


def limits_for(grade, precision):
    values = ['E3：仅依据公开标题与摘要；未核验全文证明、参数或实验。' if grade == 'E3'
              else 'E2：仅有公开元数据；不能据此确认方法、性能或安全结论。']
    if precision == 'DATE_ONLY':
        values.append('日期仅精确到日，不能建立精确发布时间或日内截止归属。')
    return values
# Defense in depth. The primary boundary is construction from public source fields.
SUSPICIOUS = re.compile(
    r'(?i)(?:[a-z]:[\\/]|\\\\|(?:/home/|/users/)|\b(?:gmail|oauth|refresh_token|access_token)\b|'
    r'gh[pousr]_[a-z0-9]{20,}|sk-(?:proj-)?[a-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY|'
    r'[\w.+-]+@[\w.-]+\.[a-z]{2,}|博士申请|推荐信|个人陈述|私密|statement of purpose|'
    r'ignore (?:all |previous )?instructions|<script|<!--|\]\(|https?://)')


def text(value: str, maximum: int = 600) -> str:
    if not isinstance(value, str):
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'public text must be a string')
    normalized = unicodedata.normalize('NFKC', value)
    if not value or len(value) > maximum or SUSPICIOUS.search(normalized) or any(
            unicodedata.category(c) in ('Cc', 'Cf', 'Cs') for c in value):
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'suspicious or oversized public source field; content redacted')
    return value


def source_url(value: str) -> str:
    if not isinstance(value, str) or len(value) > 300 or any(unicodedata.category(c) in ('Cc','Cf','Cs') for c in value):
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'invalid public source URL')
    u = urlsplit(value)
    if u.scheme != 'https' or u.username or u.password or u.query or u.fragment or u.port or '%' in u.path:
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'public URLs must be canonical HTTPS without tracking')
    if any(part in ('.','..') for part in u.path.split('/')) or SUSPICIOUS.search(unicodedata.normalize('NFKC',u.path)):
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'suspicious or noncanonical public URL path')
    hosts = {
        'arxiv.org': r'/abs/(?:\d{4}\.\d{4,5}(?:v\d+)?|[a-z.-]+/\d{7}(?:v\d+)?)',
        'eprint.iacr.org': r'/\d{4}/[1-9]\d*',
        'doi.org': r'/10\.\d{4,9}/[A-Za-z0-9._;()/:-]+',
    }
    if u.hostname not in hosts or not re.fullmatch(hosts[u.hostname], u.path):
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'source URL is outside reviewed primary identifier routes')
    return value


def normalized_source_url(value: str) -> str:
    # Historical arXiv API metadata used HTTP. Upgrade only a canonical identifier
    # on an already reviewed official host; tracking/auth/unknown hosts still fail.
    if isinstance(value,str) and value.startswith('http://'):
        parsed=urlsplit(value)
        if parsed.hostname in ('arxiv.org','eprint.iacr.org','doi.org'):
            value='https://'+value[len('http://'):]
    return source_url(value)


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class PublicPaper(Strict):
    title: str = Field(min_length=1, max_length=600)
    source_url: str
    public_identifier: str
    public_canonical_id: str
    authors: list[str] = Field(max_length=100)
    event_kind: Literal['primary_publication_events', 'revision_events', 'new_critical_verify_events']
    event_id: str = Field(pattern=r'^[a-f0-9]{64}$')
    verified_date: str
    date_precision: Literal['DATE_ONLY', 'TIMESTAMP']
    date_timezone: Literal['UNSPECIFIED_BY_SOURCE', 'SOURCE_OFFSET']
    event_evidence: Literal['VERIFIED_CURRENT_SCHEMA_EVENT', 'DERIVED_HISTORICAL_EVENT_CANDIDATE']
    evidence_grade: Literal['E2', 'E3']
    lattice_category: Literal['A', 'B', 'C']
    source_topics: list[str] = Field(max_length=8)
    technical_guide_zh: str
    limitations_zh: list[str]

    @field_validator('source_url')
    @classmethod
    def url_check(cls, value):
        return source_url(value)

    @field_validator('title', 'public_identifier', 'verified_date', 'technical_guide_zh')
    @classmethod
    def text_check(cls, value):
        return text(value)

    @field_validator('public_canonical_id')
    @classmethod
    def identity_check(cls,value):
        if (re.fullmatch(r'arxiv:(?:\d{4}\.\d{4,5}|[a-z.-]+/\d{7})',value) or
            re.fullmatch(r'eprint:\d{4}/[1-9]\d*',value) or
            re.fullmatch(r'doi:10\.\d{4,9}/[a-zA-Z0-9._;()/:-]+',value)):
            return value
        if value.startswith('url:'):
            source_url(value[4:])
            return value
        fail('PUBLIC_PRIVACY_GATE_FAILED','canonical identity is not a reviewed public identifier')

    @field_validator('authors', 'limitations_zh')
    @classmethod
    def list_check(cls, values):
        return [text(v, 300) for v in values]


class PublicInputEvidence(Strict):
    date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    json_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    markdown_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    event_evidence: Literal['VERIFIED_CURRENT_SCHEMA_EVENT', 'DERIVED_HISTORICAL_EVENT_CANDIDATE',
                            'NONCONTRIBUTING_HISTORICAL_INPUT', 'MISSING_CANONICAL_INPUT']


class PublicReport(Strict):
    public_schema_version: Literal['public-literature-v1']
    readable_contract_version: Literal['public-readable-v1']
    report_type: Literal['daily', 'weekly', 'monthly']
    report_period: str
    period_start: str
    period_end: str
    title: str
    quality: Literal['VERIFIED_AUTHORITATIVE', 'VALID_DEGRADED_AUTHORITATIVE', 'PROVISIONAL_PUBLIC']
    source_coverage_state: Literal['AUTHORITATIVE_COMPLETE', 'AUTHORITATIVE_DEGRADED', 'PARTIAL_VERIFY_FIRST', 'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS']
    source_policy_version: Literal['scientific-publication-v4-v3', 'scientific-publication-v3-v2', 'scientific-publication-p0-v1', 'period-event-evidence-v1']
    input_evidence: list[PublicInputEvidence]
    source_generation_ids: list[str]
    canonical_pair_sha256: dict[str, str]
    public_generation_id: str
    entry_count: int = Field(ge=0, le=2000)
    historical_candidate_count: int = Field(ge=0, le=2000)
    event_count: int = Field(ge=0, le=2000)
    omitted_event_count: int = Field(ge=0)
    papers: list[PublicPaper] = Field(max_length=2000)
    limitations_zh: list[str]


class PublicPaperV2(PublicPaper):
    technical_detail: dict
    scientific_domain: Literal['DIRECT_LATTICE_MATH','LATTICE_CRYPTANALYSIS','LATTICE_PRIMITIVE',
        'LATTICE_IMPLEMENTATION','LATTICE_APPLICATION','ADJACENT_PQC','NON_LATTICE','VERIFY_FIRST']


class PublicObservation(Strict):
    title: str
    source_url: str
    observation_status: Literal['RETROSPECTIVE_SCOPE_CORRECTION_NONCOUNTING','LATE_OBSERVED_NONCOUNTING']
    technical_detail: dict
    source_topics: list[str]


class PublicReportV2(PublicReport):
    public_schema_version: Literal['public-literature-v2']
    readable_contract_version: Literal['public-readable-v2']
    papers: list[PublicPaperV2] = Field(max_length=2000)
    temporal_evidence: dict
    revision_reason: Literal['SOURCE_GROUNDED_READABILITY_AND_CLOCK_DISCLOSURE_V2']
    noncounting_observations: list[PublicObservation] = Field(max_length=2000)


def temporal_evidence(meta):
    from datetime import datetime
    cloud = meta.get('cloud_execution', {})
    def clock(value):
        if value in (None, '', 'UNKNOWN'): return 'UNKNOWN'
        try:
            parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            if not parsed.tzinfo: raise ValueError
            return parsed.isoformat()
        except (ValueError, TypeError):
            fail('EVENT_OWNERSHIP_INVALID', 'invalid source execution clock')
    attempts = meta.get('source_query_runtime', [])
    if not isinstance(attempts, list) or len(attempts)>2000:
        fail('PAYLOAD_SIZE_INVALID', 'unbounded source timing')
    starts = [clock(a.get('started_at')) for a in attempts if isinstance(a, dict)]
    ends = [clock(a.get('finished_at')) for a in attempts if isinstance(a, dict)]
    def edge(values, fn):
        stamps = [datetime.fromisoformat(v) for v in values if v != 'UNKNOWN']
        return fn(stamps).isoformat() if stamps else 'UNKNOWN'
    return dict(nominal_scheduled_time=clock(cloud.get('scheduled_for', meta.get('scheduled_for'))),
        scheduler_event_time=clock(cloud.get('scheduler_event_time')),
        actual_process_start=clock(cloud.get('actual_start', meta.get('run_started_at'))),
        actual_collection_start=edge(starts, min), actual_collection_end=edge(ends, max),
        source_retrieval_cutoff=clock(meta.get('coverage_end')),
        retrospective_reconstruction_time=clock(meta.get('repair_executed_at')),
        publication_first_available_time='UNKNOWN', public_revision_time='UNKNOWN')


DAILY_TOP = {'late_arrivals', 'chronology_v3', 'publication_event_ledger', 'publication_history_evidence',
             'metadata', 'records', 'source_health', 'warnings', 'schema_version'}
WEEKLY_TOP = {'provenance_label_counts', 'validated_label_counts', 'classification_conflict_count',
    'classification_conflicts', 'classification_quality_state', 'publication_event_views', 'schema_version',
    'week_id', 'from_date', 'to_date', 'generated_at', 'coverage', 'label_counts', 'sections', 'report_buckets',
    'idea_bank_candidates', 'paper_plan_candidates', 'source_health_summary', 'metadata'}
MONTHLY_TOP = {'provenance_label_counts', 'validated_label_counts', 'classification_conflict_count',
    'classification_conflicts', 'classification_quality_state', 'publication_event_views', 'schema_version',
    'month', 'generated_at', 'input_daily_files', 'input_weekly_files', 'missing_days', 'input_quality',
    'paper_index', 'translation_status', 'bilingual_release_status', 'total_unique_records', 'class_counts',
    'direction_counts', 'source_health_summary', 'core_papers', 'reading_priority', 'trend_summary',
    'rationale_policy', 'TODO_VERIFY', 'metadata', 'repair_receipt'}
ENRICHED = {'date', 'year', 'url', 'tags', 'research_tags', 'priority', 'reading_priority_score', 'priority_label',
    'reason_for_priority', 'why_it_matters', 'suggested_action', 'research_hooks', 'advisor_questions',
    'source_health_ref', 'ranking_explanation', 'research_sections', 'report_buckets', 'research_idea_status'}


PUBLIC_ADAPTERS = frozenset(('arxiv', 'iacr_eprint', 'crossref', 'dblp', 'openalex', 'semantic_scholar'))


def reviewed_public_adapters(value: str) -> tuple[str, ...]:
    # The deployed deduplicator joins corroborating public adapters with ", ".
    # Accept exactly that bounded contract, never arbitrary source prose or mail.
    if not isinstance(value,str) or not 1<=len(value)<=120:
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'invalid public source adapter identity')
    names=tuple(value.split(', '))
    if len(names)!=len(set(names)) or any(name not in PUBLIC_ADAPTERS for name in names):
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'unreviewed source adapter')
    return names


def project(pair: VerifiedPair, *, readable_version: int = 2) -> dict:
    if readable_version not in (1, 2):
        fail('SCHEMA_VERSION_UNSUPPORTED', 'unsupported public readable version')
    allowed = {'daily': DAILY_TOP, 'weekly': WEEKLY_TOP, 'monthly': MONTHLY_TOP}[pair.kind]
    if set(pair.payload) - allowed:
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'unknown canonical root extension')
    from lattice_digest.models import PaperRecord
    from lattice_digest.evidence_contract import source_topics, source_scope_score, score_to_label
    known_rows = set(PaperRecord.model_fields) | ENRICHED
    papers = []
    seen = set()
    for event in sorted(pair.events, key=lambda e: e['event_id']):
        row = pair.source_rows[event['row_index']]
        # Mailbox records are never public evidence, even if their link looks public.
        if 'gmail' in str(row.get('source', '')).lower():
            continue
        if set(row) - known_rows:
            fail('PUBLIC_PRIVACY_GATE_FAILED', 'unknown canonical record extension')
        if event['event_id'] in seen:
            fail('EVENT_OWNERSHIP_INVALID', 'duplicate event in export')
        seen.add(event['event_id'])
        # Only reviewed primary source fields enter classification and the renderer.
        public_source = {k: row.get(k) for k in ('title', 'abstract', 'source', 'source_url')}
        reviewed_public_adapters(public_source['source'])
        title = text(row['title'])
        abstract = row.get('abstract') or ''
        # Scan source input without copying it. Complete abstracts are never emitted.
        if not isinstance(abstract, str) or len(abstract) > 50000:
            fail('PUBLIC_PRIVACY_GATE_FAILED', 'invalid public abstract input')
        # URL/email patterns inside a public abstract need explicit source review too.
        if (SUSPICIOUS.search(unicodedata.normalize('NFKC', abstract)) or
                any(unicodedata.category(c) in ('Cf', 'Cs') or
                    (unicodedata.category(c) == 'Cc' and c not in '\n\r\t') for c in abstract)):
            fail('PUBLIC_PRIVACY_GATE_FAILED', 'suspicious source abstract; content redacted')
        url = normalized_source_url(row['source_url'])
        _, score = source_scope_score(public_source)
        category = score_to_label(score)
        if category == 'D':
            continue
        topics = source_topics(public_source)
        # A fixed vocabulary extracted solely from source title/abstract, never user priorities.
        grade = 'E3' if abstract.strip() else 'E2'
        guide = guide_for(topics[:8], grade)
        value = event.get('event_date')
        try:
            from lattice_digest.publication_events import timestamp
            parsed = timestamp(value)
            if not parsed:
                raise ValueError
        except (ValueError, TypeError):
            fail('EVENT_OWNERSHIP_INVALID', 'event lacks a verified source date')
        precision = 'DATE_ONLY' if re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(value)) else 'TIMESTAMP'
        verified_date = str(value) if precision == 'DATE_ONLY' else parsed.isoformat()
        limits = limits_for(grade, precision)
        papers.append(PublicPaper(title=title, source_url=url, public_identifier=urlsplit(url).path.lstrip('/'),
            public_canonical_id=event['canonical_identity'],
            authors=[text(a, 160) for a in row.get('authors', [])], event_kind=event['collection'],
            event_id=event['event_id'], verified_date=verified_date, date_precision=precision,
            date_timezone='UNSPECIFIED_BY_SOURCE' if precision == 'DATE_ONLY' else 'SOURCE_OFFSET',
            event_evidence=event.get('event_evidence', 'VERIFIED_CURRENT_SCHEMA_EVENT'),
            evidence_grade=grade, lattice_category=category, source_topics=topics[:8],
            technical_guide_zh=guide, limitations_zh=limits).model_dump())
    meta = pair.payload['metadata']
    public = dict(public_schema_version=VERSION, readable_contract_version='public-readable-v1',
        report_type=pair.kind, report_period=pair.period, period_start=pair.start, period_end=pair.end,
        title=f'格密码公开文献报告 {pair.period}', quality=pair.quality,
        source_coverage_state=pair.coverage_state,
        source_policy_version=meta.get('publication_policy_version', 'period-event-evidence-v1'),
        source_generation_ids=[meta['generation_id']], input_evidence=[PublicInputEvidence.model_validate(i).model_dump() for i in pair.input_provenance],
        canonical_pair_sha256={'json': pair.json_sha256, 'markdown': pair.markdown_sha256},
        public_generation_id='', entry_count=len(papers),
        event_count=sum(p['event_evidence']=='VERIFIED_CURRENT_SCHEMA_EVENT' for p in papers),
        historical_candidate_count=sum(p['event_evidence']=='DERIVED_HISTORICAL_EVENT_CANDIDATE' for p in papers),
        omitted_event_count=len(pair.events)-len(papers),
        papers=papers, limitations_zh=['来源覆盖受限时，报告不能用于断言该时期没有相关新论文。',
            '公开导出只覆盖通过来源与隐私门禁的事件；不代表全部检索记录或领域总体趋势。'])
    if readable_version == 2:
        from lattice_digest.public_technical import detail, domain
        by_event = {e['event_id']: pair.source_rows[e['row_index']] for e in pair.events}
        for paper in papers:
            paper['scientific_domain']=domain(paper['title'],paper['source_topics'])
            paper['technical_detail'] = detail(by_event[paper['event_id']].get('abstract') or '',
                                               paper['source_url'], paper['source_topics'])
        public.update(public_schema_version='public-literature-v2', readable_contract_version='public-readable-v2',
            temporal_evidence=temporal_evidence(meta),
            revision_reason='SOURCE_GROUNDED_READABILITY_AND_CLOCK_DISCLOSURE_V2', noncounting_observations=[])
        # Correct recognition without silently rebuilding a frozen source ledger.
        if pair.kind == 'daily':
            from lattice_digest.publication_events import scope_evaluator_for_policy, POLICY_VERSION
            old_policy=meta.get('publication_policy_version')
            from lattice_digest.scientific_scope import evaluate_scope
            selected={p['source_url'] for p in papers}
            candidates={}
            if old_policy and old_policy != POLICY_VERSION:
                frozen=scope_evaluator_for_policy(old_policy)
                candidates={i:'RETROSPECTIVE_SCOPE_CORRECTION_NONCOUNTING' for i,row in enumerate(pair.source_rows)
                    if evaluate_scope(row)['lattice_relevance_qualified'] and not frozen(row)['lattice_relevance_qualified']}
            from lattice_digest.publication_events import canonical_identity
            for item in pair.payload.get('late_arrivals',[]):
                i=item.get('row_index')
                if (type(i) is not int or not 0<=i<len(pair.source_rows) or
                        item.get('counts_as_new_publication') is not False or item.get('status')!='LATE_ARRIVAL'):
                    fail('EVENT_OWNERSHIP_INVALID','invalid noncounting late input')
                if canonical_identity(pair.source_rows[i]) != item.get('canonical_identity'):
                    fail('EVENT_OWNERSHIP_INVALID','late input source identity mismatch')
                if evaluate_scope(pair.source_rows[i])['lattice_relevance_qualified']:
                    candidates.setdefault(i,'LATE_OBSERVED_NONCOUNTING')
            for i,status in sorted(candidates.items()):
                    row=pair.source_rows[i]
                    if row.get('source_url') in selected: continue
                    selected.add(row.get('source_url'))
                    # Apply the same input safety checks even for noncounting text.
                    if set(row)-known_rows:
                        fail('PUBLIC_PRIVACY_GATE_FAILED','unknown retrospective source extension')
                    reviewed_public_adapters(row['source'])
                    url=normalized_source_url(row['source_url']); title=text(row['title'])
                    abstract=row.get('abstract') or ''
                    if (not isinstance(abstract,str) or len(abstract)>50000 or
                            SUSPICIOUS.search(unicodedata.normalize('NFKC',abstract)) or
                            any(unicodedata.category(c) in ('Cf','Cs') or
                                (unicodedata.category(c)=='Cc' and c not in '\n\r\t') for c in abstract)):
                        fail('PUBLIC_PRIVACY_GATE_FAILED','unsafe retrospective source input')
                    topics=source_topics(row)[:8]
                    public['noncounting_observations'].append(dict(title=title,source_url=url,source_topics=topics,
                        observation_status=status,
                        technical_detail=detail(abstract,url,topics)))
    public['public_generation_id'] = sha(encoded(public))
    return validate_public(public)


def validate_public(public: dict) -> dict:
    try:
        model = PublicReportV2 if public.get('public_schema_version') == 'public-literature-v2' else PublicReport
        validated = model.model_validate(public).model_dump()
    except (ValidationError, ValueError):
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'public schema rejected fields or content; details redacted')
    from lattice_digest.report_gate import period_bounds
    first,last=period_bounds(validated['report_type'], validated['report_period'])
    if (validated['entry_count'] != len(validated['papers']) or
            len({p['event_id'] for p in validated['papers']}) != validated['entry_count'] or
            validated['event_count'] != sum(p['event_evidence']=='VERIFIED_CURRENT_SCHEMA_EVENT' for p in validated['papers']) or
            validated['historical_candidate_count'] != sum(p['event_evidence']=='DERIVED_HISTORICAL_EVENT_CANDIDATE' for p in validated['papers'])):
        fail('EVENT_OWNERSHIP_INVALID', 'public event count mismatch')
    if any(p['event_evidence']=='DERIVED_HISTORICAL_EVENT_CANDIDATE' for p in validated['papers']) and validated['quality']!='PROVISIONAL_PUBLIC':
        fail('EVENT_OWNERSHIP_INVALID', 'historical reconstruction cannot assert current event authority')
    for evidence in validated['input_evidence']:
        from datetime import date
        try: date.fromisoformat(evidence['date'])
        except ValueError: fail('PERIOD_IDENTITY_INVALID', 'invalid source evidence date')
        missing=evidence['event_evidence']=='MISSING_CANONICAL_INPUT'
        if ((missing and (evidence['json_sha256'] is not None or evidence['markdown_sha256'] is not None)) or
                (not missing and (evidence['json_sha256'] is None or evidence['markdown_sha256'] is None))):
            fail('PAIR_HASH_MISMATCH', 'source input evidence hashes missing or unexpected')
    if (len({i['date'] for i in validated['input_evidence']}) != len(validated['input_evidence']) or
            any(not str(first)<=i['date']<=str(last) for i in validated['input_evidence'])):
        fail('PERIOD_IDENTITY_INVALID', 'period input evidence is duplicated or outside the report period')
    for name in ('period_start', 'period_end', 'title', 'source_coverage_state', 'source_policy_version'):
        text(validated[name])
    from datetime import datetime, date
    first,last = period_bounds(validated['report_type'],validated['report_period'])
    try:
        if validated['report_type']=='daily':
            start=datetime.fromisoformat(validated['period_start'])
            end=datetime.fromisoformat(validated['period_end'])
            if not start.tzinfo or not end.tzinfo or start>=end:
                raise ValueError
            from zoneinfo import ZoneInfo
            from datetime import timedelta
            local_end=end.astimezone(ZoneInfo('Asia/Singapore'))
            if local_end.date()!=last and not (local_end.date()==last+timedelta(days=1) and local_end.time()==datetime.min.time()):
                raise ValueError
        elif (validated['period_start'],validated['period_end'])!=(str(first),str(last)):
            raise ValueError
    except (ValueError,TypeError):
        fail('PERIOD_IDENTITY_INVALID','invalid public period bounds')
    if validated['quality']=='VERIFIED_AUTHORITATIVE' and validated['source_coverage_state']!='AUTHORITATIVE_COMPLETE':
        fail('EVENT_OWNERSHIP_INVALID','degraded coverage cannot claim the highest quality tier')
    if validated['title'] != f"格密码公开文献报告 {validated['report_period']}" or validated['source_coverage_state'] not in (
            'AUTHORITATIVE_COMPLETE','AUTHORITATIVE_DEGRADED','PARTIAL_VERIFY_FIRST','INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'):
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'unreviewed report title or coverage state')
    for paper in validated['papers']:
        if validated['public_schema_version'] == 'public-literature-v2':
            from lattice_digest.public_technical import check_detail, domain
            try: check_detail(paper['technical_detail'], paper['source_url'], paper['source_topics'])
            except (ValueError, KeyError, TypeError):
                fail('PUBLIC_PRIVACY_GATE_FAILED', 'unreviewed technical detail')
            if paper['scientific_domain'] != domain(paper['title'],paper['source_topics']):
                fail('PUBLIC_PRIVACY_GATE_FAILED','arbitrary scientific grouping')
        if paper['public_identifier'] != urlsplit(paper['source_url']).path.lstrip('/'):
            fail('PUBLIC_PRIVACY_GATE_FAILED','public identifier must match its reviewed source URL')
        try:
            if paper['date_precision']=='DATE_ONLY':
                date.fromisoformat(paper['verified_date'])
                if paper['date_timezone']!='UNSPECIFIED_BY_SOURCE':raise ValueError
            else:
                if not datetime.fromisoformat(paper['verified_date']).tzinfo or paper['date_timezone']!='SOURCE_OFFSET':raise ValueError
        except (ValueError,TypeError):
            fail('EVENT_OWNERSHIP_INVALID','public date precision/timezone mismatch')
        if paper['technical_guide_zh'] != guide_for(paper['source_topics'],paper['evidence_grade']) or paper['limitations_zh'] != limits_for(paper['evidence_grade'],paper['date_precision']):
            fail('PUBLIC_PRIVACY_GATE_FAILED', 'arbitrary guide or limitation prose is forbidden')
    if set(validated['canonical_pair_sha256']) != {'json', 'markdown'} or any(
            not re.fullmatch(r'[a-f0-9]{64}', v) for v in validated['canonical_pair_sha256'].values()):
        fail('PAIR_HASH_MISMATCH', 'invalid source provenance hashes')
    if not validated['source_generation_ids'] or any(not re.fullmatch(r'[a-f0-9]{32}', g) for g in validated['source_generation_ids']):
        fail('PAIR_GENERATION_INVALID', 'invalid source provenance generation')
    if validated['limitations_zh'] != ['来源覆盖受限时，报告不能用于断言该时期没有相关新论文。',
            '公开导出只覆盖通过来源与隐私门禁的事件；不代表全部检索记录或领域总体趋势。']:
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'unreviewed public limitations extension')
    original = dict(validated, public_generation_id='')
    if validated['public_schema_version'] == 'public-literature-v2':
        from lattice_digest.public_technical import check_detail
        seen=set()
        for row in validated['noncounting_observations']:
            text(row['title']);source_url(row['source_url'])
            guide_for(row['source_topics'],'E3')
            try: check_detail(row['technical_detail'],row['source_url'],row['source_topics'])
            except (ValueError,KeyError,TypeError):
                fail('PUBLIC_PRIVACY_GATE_FAILED','unreviewed retrospective technical detail')
            if row['source_url'] in seen or any(r['source_url']==row['source_url'] for r in validated['papers']):
                fail('EVENT_OWNERSHIP_INVALID','duplicate retrospective observation')
            seen.add(row['source_url'])
        clocks = validated['temporal_evidence']
        expected = set(temporal_evidence({}))
        if set(clocks) != expected:
            fail('PUBLIC_PRIVACY_GATE_FAILED', 'unknown temporal field')
        for value in clocks.values():
            if value == 'UNKNOWN': continue
            try:
                stamp = datetime.fromisoformat(value)
                if not stamp.tzinfo: raise ValueError
            except (ValueError, TypeError):
                fail('EVENT_OWNERSHIP_INVALID', 'invalid public clock')
        a,b = clocks['actual_collection_start'],clocks['actual_collection_end']
        if a != 'UNKNOWN' and b != 'UNKNOWN' and datetime.fromisoformat(a)>datetime.fromisoformat(b):
            fail('EVENT_OWNERSHIP_INVALID', 'reversed source retrieval clocks')
        cutoff=clocks['source_retrieval_cutoff']
        if cutoff != 'UNKNOWN' and b != 'UNKNOWN' and datetime.fromisoformat(cutoff)>datetime.fromisoformat(b):
            fail('EVENT_OWNERSHIP_INVALID','retrieval ended before claimed cutoff')
    if sha(encoded(original)) != validated['public_generation_id']:
        fail('PAIR_HASH_MISMATCH', 'public generation content hash mismatch')
    if len(encoded(validated)) > MAX_PUBLIC_BYTES:
        fail('PAYLOAD_SIZE_INVALID', 'public JSON exceeds one MiB')
    return validated


def render(public: dict) -> bytes:
    p = validate_public(public)
    def escape(value):
        return re.sub(r'([\\`*_[\]{}()#!|>])', r'\\\1', html.escape(value))
    v2 = p['public_schema_version'] == 'public-literature-v2'
    lines = [f"# {p['title']}", '', '<!-- '+p['readable_contract_version']+' -->',
        f"报告：{p['report_type']} / {p['report_period']}", f"执行质量：{p['quality']}",
        f"来源覆盖：{p['source_coverage_state']}", f"公开条目：{p['entry_count']}；当前模式已核验事件：{p['event_count']}；历史重建候选：{p['historical_candidate_count']}；未导出条目：{p['omitted_event_count']}", '',
        '## 来源与限制', *('- ' + s for s in p['limitations_zh']), '', '## 公开文献事件']
    if v2:
        lines[2:2] = ['## 执行摘要',
            f"本期列出 {p['entry_count']} 项文献；核验事件 {p['event_count']} 项，历史候选 {p['historical_candidate_count']} 项。下文主题讨论不增加首发计数。",
            '技术说明仅归纳已核对的公开摘要；数值和安全结论均归于作者，不代表独立复现或全文证明核验。', '']
        labels = dict(nominal_scheduled_time='名义计划时间', scheduler_event_time='实际调度事件时间',
            actual_process_start='实际进程开始', actual_collection_start='实际检索开始',
            actual_collection_end='实际检索结束', source_retrieval_cutoff='检索窗口截止',
            retrospective_reconstruction_time='回溯重建时间', publication_first_available_time='首次公开可用时间',
            public_revision_time='公开修订时间')
        lines.extend(['', '### 时间与覆盖', f"名义报告区间：{p['period_start']} 至 {p['period_end']}",
            *[f"- {label}：{p['temporal_evidence'][k]}" for k,label in labels.items()],
            'UNKNOWN 表示缺乏可用证据。36 小时重叠是发现窗口，不是完整性证明；迟到检索不等于截止前已观察。',
            '首次公开可用及后续修订以 Git 历史和独立发布回执核验，不从源论文日期推算。'])
        primary = [r for r in p['papers'] if r['event_evidence']=='VERIFIED_CURRENT_SCHEMA_EVENT' and r['event_kind']=='primary_publication_events']
        revisions = [r for r in p['papers'] if r['event_evidence']=='VERIFIED_CURRENT_SCHEMA_EVENT' and r['event_kind']=='revision_events']
        lines.extend(['', '### 事件与主题分开解读',
            f"当前模式首发事件：{len(primary)}；修订事件：{len(revisions)}；历史候选：{p['historical_candidate_count']}。修订不作为新增论文身份。"])
        groups = [('格算法与密码分析', {'Lattice Reduction','Cryptanalysis','SVP','Module Lattice'}),
                  ('格原语与隐私协议', {'LWE','MLWE','SIS','Module-SIS','Lattice Signatures','ML-DSA','Lattice ZK'}),
                  ('同态计算', {'FHE'}), ('实现与部署', {'PQC Implementation','Sampling','ML-KEM','Falcon'})]
        for label,topics in groups:
            rows = [r for r in p['papers'] if set(r['source_topics']) & topics]
            if rows:
                lines.append('- '+label+'：'+'；'.join(r['source_url'] for r in rows)+'。主题可交叉，不能相加为事件总数。')
        if p['report_type'] != 'daily':
            lines.append('本期仅按已验证来源组织技术线索；未核实方法、假设与指标可比时，不给出跨论文性能排名或趋势性结论。')
    if p['input_evidence']:
        gaps=[i['date'] for i in p['input_evidence'] if i['event_evidence'] in ('MISSING_CANONICAL_INPUT','NONCONTRIBUTING_HISTORICAL_INPUT')]
        if gaps: lines.extend(['来源输入限制日期：'+ '、'.join(gaps), '这些日期未通过当前模式事件核验；不能解释为没有新论文。'])
    if not p['papers']:
        lines.append('本报告没有可公开列出的已验证事件；请结合来源覆盖状态解读。')
    for row in p['papers']:
        # Escape Markdown/HTML metacharacters in public source strings.
        lines.extend(['', '### ' + escape(row['title']), row['source_url'],
            '作者：' + (escape('、'.join(row['authors'])) or '公开元数据未提供'),
            f"事件：{row['event_kind']}；日期：{row['verified_date']}；{row['date_precision']} / {row['date_timezone']}",
            f"证据：{row['evidence_grade']}；事件证据：{row['event_evidence']}；相关性：{row['lattice_category']}",
            *(['历史重建候选：由已保存来源窗口推导，不代表原运行时已观察到的当前模式事件。'] if row['event_evidence']=='DERIVED_HISTORICAL_EVENT_CANDIDATE' else []), row['technical_guide_zh'],
            *('- ' + s for s in row['limitations_zh'])])
        if v2:
            d = row['technical_detail']
            lines.extend(['- 技术分组：'+row['scientific_domain']+'（公开标题与来源主题的描述分组，不增加事件计数）',
                '- 技术证据状态：'+d['status'],
                '- 数学／安全对象：'+escape(d['object_zh']), '- 问题：'+escape(d['problem_zh']),
                '- 方法：'+escape(d['method_zh']), '- 作者报告的结果：'+escape(d['result_zh']),
                '- 条件与局限：'+escape(d['assumptions_zh']), '- 格密码意义：'+escape(d['significance_zh']),
                *('- 技术核验问题：'+escape(q) for q in d['verification_questions_zh'])])
    if v2 and p['noncounting_observations']:
        lines.extend(['','## 迟到发现与回溯范围更正（不计入本期首发或修订事件）',
            '以下条目来自已保存的公开来源：LATE_OBSERVED 表示当前检索才观察到的较早论文；RETROSPECTIVE_SCOPE_CORRECTION 表示新版规则补识别的原分类漏项。保留原 canonical 事件历史，不声称原期间已正确选入。'])
        for row in p['noncounting_observations']:
            d=row['technical_detail']
            lines.extend(['','### '+escape(row['title']),row['source_url'],
                row['observation_status'], '- 数学／安全对象：'+escape(d['object_zh']),
                '- 问题：'+escape(d['problem_zh']),'- 方法：'+escape(d['method_zh']),
                '- 作者报告的结果：'+escape(d['result_zh']),'- 条件与局限：'+escape(d['assumptions_zh'])])
    lines.extend(['', '<!-- public-generation:' + p['public_generation_id'] + ' -->', ''])
    result = '\n'.join(lines).encode('utf-8')
    if len(result) > MAX_PUBLIC_BYTES:
        fail('PAYLOAD_SIZE_INVALID', 'public Markdown exceeds one MiB')
    return result


def report_paths(public: dict) -> tuple[str, str]:
    p = validate_public(public)
    stem = f"{p['report_type']}/{p['report_period'][:4]}/{p['report_period']}"
    return stem + '.json', stem + '.md'


def export(root: Path, kind: str, period: str, output: Path) -> dict:
    from lattice_digest.public_contract import _reject_redirects
    public = project(verify(root, kind, period))
    j, m = report_paths(public)
    _reject_redirects(output.absolute())
    # A candidate directory is create-only. A failed promotion leaves an ineligible tree.
    if output.exists():
        fail('PUBLISH_CONFLICT', 'candidate directory already exists')
    output.mkdir(parents=True)
    for name, content in ((j, encoded(public) + b'\n'), (m, render(public))):
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    manifest = {'schema_version': 'public-manifest-v1', 'reports': {kind + ':' + period: {
        'json': j, 'markdown': m, 'json_sha256': sha((output/j).read_bytes()),
        'markdown_sha256': sha((output/m).read_bytes()), 'quality': public['quality'],
        'public_generation_id': public['public_generation_id']}}}
    (output/'manifest.json').write_bytes(encoded(manifest)+b'\n')
    (output/'index.md').write_bytes(index_bytes(manifest))
    inspect_tree(output)
    return manifest


def index_bytes(manifest: dict) -> bytes:
    return ('# 格密码公开文献报告\n\n' + '\n'.join(
        f"- [{key}]({entry['markdown']}) — {entry['quality']}" for key,entry in sorted(manifest['reports'].items()))+'\n').encode('utf-8')


def validate_catalog(manifest: dict, files: dict[str, bytes]) -> None:
    """A cloud rerun has no local DB; public history still owns Daily identities."""
    owners = {}
    for key,entry in sorted(manifest['reports'].items()):
        if not key.startswith('daily:'):
            continue
        report=validate_public(strict_json(files[entry['json']]))
        for paper in report['papers']:
            if paper['event_kind']!='primary_publication_events':
                continue
            url=paper['source_url'].lower()
            url_identity=re.sub(r'v\d+$','',url) if url.startswith('https://arxiv.org/') else url
            for identity in (url_identity,paper['public_canonical_id']):
                if identity in owners and owners[identity]!=key:
                    fail('EVENT_OWNERSHIP_INVALID','public Daily identity already belongs to another period')
                owners[identity]=key


def inspect_tree(root: Path) -> tuple[dict, dict[str, bytes]]:
    manifest = strict_json(safe_file(root, root/'manifest.json', MAX_PUBLIC_BYTES))
    if not isinstance(manifest, dict) or set(manifest) != {'schema_version', 'reports'} or manifest['schema_version'] != 'public-manifest-v1' or not isinstance(manifest['reports'], dict):
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'invalid public manifest')
    files = {'manifest.json': (root/'manifest.json').read_bytes(), 'index.md': safe_file(root, root/'index.md', MAX_PUBLIC_BYTES)}
    if files['index.md'] != index_bytes(manifest):
        fail('PAIR_HASH_MISMATCH', 'index differs from deterministic manifest')
    for key, entry in manifest['reports'].items():
        if not isinstance(entry, dict) or set(entry) != {'json', 'markdown', 'json_sha256', 'markdown_sha256', 'quality', 'public_generation_id'}:
            fail('PUBLIC_PRIVACY_GATE_FAILED', 'unreviewed manifest entry')
        # Validate the path BEFORE any open, including Windows drives and traversal.
        match = re.fullmatch(r'(daily|weekly|monthly):(\d{4}-(?:\d{2}-\d{2}|W\d{2}|\d{2}))', key)
        if not match:
            fail('ARTIFACT_PATH_MISMATCH', 'invalid manifest period key')
        kind, period = match.groups()
        stem = f'{kind}/{period[:4]}/{period}'
        if entry['json'] != stem+'.json' or entry['markdown'] != stem+'.md':
            fail('ARTIFACT_PATH_MISMATCH', 'manifest path differs from exact allowlist')
        jb = safe_file(root, root/entry['json'], MAX_PUBLIC_BYTES)
        mb = safe_file(root, root/entry['markdown'], MAX_PUBLIC_BYTES)
        public = validate_public(strict_json(jb))
        if key != public['report_type']+':'+public['report_period'] or entry['quality'] != public['quality'] or entry['public_generation_id'] != public['public_generation_id']:
            fail('PERIOD_IDENTITY_INVALID', 'manifest identity or quality mismatch')
        if sha(jb) != entry['json_sha256'] or sha(mb) != entry['markdown_sha256'] or mb != render(public):
            fail('PAIR_HASH_MISMATCH', 'manifest pair or deterministic render mismatch')
        files[entry['json']], files[entry['markdown']] = jb, mb
    actual = set()
    for path in root.rglob('*'):
        from lattice_digest.public_contract import _reject_redirects
        try:
            _reject_redirects(path)
        except ValueError:
            fail('ARTIFACT_PATH_MISMATCH', 'redirected publication tree member')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != set(files):
        fail('PUBLIC_PRIVACY_GATE_FAILED', 'unexpected file in public tree')
    validate_catalog(manifest,files)
    return manifest, files


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--type', choices=('daily','weekly','monthly'), required=True)
    parser.add_argument('--period', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        export(args.root, args.type, args.period, args.output)
        print(json.dumps({'gate': 'PUBLIC_PRIVACY_GATE', 'status': 'PASS'}))
        return 0
    except (ValueError, OSError, KeyError, TypeError):
        import sys
        exc = sys.exception()
        print(json.dumps({'gate': 'PUBLIC_PRIVACY_GATE', 'status': 'FAIL',
                          'code': exc.code if isinstance(exc, GateError) else 'PUBLIC_PRIVACY_GATE_FAILED'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
