"""Optional, read-only IACR mail reconciliation. Never stores raw mail or secrets.

The caller owns interactive authorization and an OS-backed credential provider.
This module does not read browser sessions, environment tokens or repository secrets.
Mail is candidate evidence; public publication metadata remains authoritative.
"""
from __future__ import annotations

import base64
import hashlib
import re
import json
import unicodedata
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr
from typing import Protocol

VERSION = 'iacr-newsletter-v1'
SENDER = 'newbounce@iacr.org'
SUBJECT = re.compile(r'^Your IACR news update: ePrint Report \(x(\d+)\)$')
LINK = re.compile(r'https://eprint\.iacr\.org/(\d{4}/\d+)(?![\w/])')
QUERY = 'from:newbounce@iacr.org subject:"Your IACR news update: ePrint Report"'
STATUSES = ('EMAIL_AND_PUBLIC_MATCH', 'EMAIL_ONLY_PENDING_PUBLIC',
            'PUBLIC_ONLY_NO_MATCHING_EMAIL', 'EMAIL_PARSE_FAILURE',
            'EMAIL_DELAYED_ARRIVAL', 'EMAIL_DUPLICATE', 'SCIENTIFIC_FALSE_NEGATIVE',
            'CORRECT_NON_CORE_EXCLUSION', 'UNRESOLVED_PUBLICATION_TIME')


def digest(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _aware(value: str) -> datetime:
    out = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if out.tzinfo is None:
        raise ValueError('received timestamp requires an explicit timezone')
    return out


def _is_iacr_sender(value: str) -> bool:
    """Accept one explicit mailbox, independent of parseaddr's version defaults.

    Older Python can treat an email-shaped display name as the mailbox and
    ignore an attacker-controlled angle address. Validate the entire header's
    narrow single-address grammar before consulting the compatibility parser.
    Comments, groups and folded headers are unnecessary for this newsletter.
    """
    if not isinstance(value,str) or any(ord(char)<32 or ord(char)==127 for char in value):
        return False
    text=value.strip(' ')
    if text.lower()==SENDER:
        return True
    match=re.fullmatch(r'([^<>]+?) *<([^<>]+)>',text)
    if not match or match[2].lower()!=SENDER:
        return False
    display=match[1].strip(' ')
    if not display or '@' in display:
        return False
    if display.startswith('"'):
        if not re.fullmatch(r'"(?:[^"\\]|\\["\\])*"',display):
            return False
    elif any(char in display for char in ',;:"\\()[]'):
        return False
    # Entire-input grammar and exact angle mailbox checks above are the gate;
    # parseaddr remains only a secondary check, never a sender-prefix extractor.
    return parseaddr(text)[1].lower()==SENDER


def _person_line(line: str) -> bool:
    # Deliberately conservative: preserve unresolved lines rather than invent authors.
    if any(c in line for c in ':$()='):
        return False
    stop = {'from','with','without','and','for','the','in','of','on','via','using',
            'efficient','cryptography','signature','signatures','quantum','lattice',
            'security','proofs','problems','model','complexity','attack','attacks',
            'polynomial','commitment','scheme','algorithms','implementation',
            'protocols','keys','recovery','aggregation','numbers','analysis'}
    tokens = re.findall(r"[^\W\d_]+(?:[-’'][^\W\d_]+)*\.?", line, re.UNICODE)
    if not tokens or any(t.lower().strip('.') in stop for t in tokens):
        return False
    groups = [x.strip() for x in line.rstrip(',').split(',')]
    # Comma-separated author lists may wrap in the middle of a name, and real
    # authors need not capitalize every name. Keep single-line ambiguity flagged.
    return all((1 if ',' in line else 2) <= len(x.split()) <= 6
               for x in groups if x)


def parse_newsletter(*, sender: str, subject: str, body: str,
                     message_id: str, received_at: str, ingested_at: str,
                     rfc_message_id: str | None = None) -> dict:
    """Parse only Contents entries; abstract repetitions and footer links are ignored.

    Result is private derived evidence: raw IDs, body and unsubscribe links omitted.
    Unverified title/author text must never be copied into public release bundles.
    Actual private message IDs belong only in the caller's restricted checkpoint.
    """
    if not _is_iacr_sender(sender) or not SUBJECT.fullmatch(subject):
        raise ValueError('NOT_IACR_EPRINT_NEWSLETTER')
    _aware(received_at); _aware(ingested_at)
    advertised = int(SUBJECT.fullmatch(subject)[1])
    text = body.replace('\r\n', '\n').replace('\r', '\n')
    start = re.search(r'^Contents:\s*$', text, re.M)
    warnings = []
    entries = []
    if not start:
        warnings.append('CONTENTS_SECTION_MISSING')
    else:
        toc = re.split(r'^-{10,}\s*$', text[start.end():], maxsplit=1, flags=re.M)[0]
        blocks = re.split(r'^\s*\* \[ePrint Report\]\s*', toc, flags=re.M)[1:]
        seen = set()
        for block in blocks:
            links = list(LINK.finditer(block))
            if len(links) != 1:
                warnings.append('ENTRY_LINK_MISSING_OR_AMBIGUOUS'); continue
            match = links[0]; identity = match[1]
            if identity in seen:
                warnings.append('DUPLICATE_CONTENTS_ID'); continue
            seen.add(identity)
            lines = [x.strip() for x in block[:match.start()].splitlines() if x.strip()]
            if not lines:
                warnings.append('ENTRY_TITLE_MISSING'); continue
            boundary = next((i for i,x in enumerate(lines[1:], 1) if _person_line(x)), None)
            title_lines = lines if boundary is None else lines[:boundary]
            author_text = '' if boundary is None else ' '.join(lines[boundary:])
            if boundary is None:
                warnings.append('AUTHOR_BOUNDARY_UNRESOLVED:'+identity)
            entries.append({'eprint_id':identity, 'source_url':'https://eprint.iacr.org/'+identity,
                            'title':' '.join(title_lines),
                            'authors':[x.strip() for x in author_text.split(',') if x.strip()],
                            'bibliographic_lines':lines,
                            'boundary_status':'HEURISTIC_PUBLIC_VERIFICATION_REQUIRED',
                            'identity_status':'EMAIL_OBSERVED_PENDING_PUBLIC_VERIFICATION',
                            'gmail_received_at':received_at})
    if advertised != len(entries):
        warnings.append('ADVERTISED_CONTENTS_COUNT_MISMATCH')
    return {'parser_version':VERSION, 'message_ref':digest(message_id),
            'rfc_message_ref':digest(rfc_message_id) if rfc_message_id else None,
            'received_at':received_at,'ingested_at':ingested_at,
            'advertised_count':advertised,'contents_count':len(entries),
            'body_sha256':digest(body),'entries':entries,'warnings':sorted(set(warnings)),
            'status':'EMAIL_PARSE_FAILURE' if warnings else 'PARSED',
            'publication_time_authority':False}


def decode_gmail_message(message: dict) -> dict:
    """Decode supported Gmail API text/plain MIME; do not fetch attachments/HTML links."""
    headers = {h['name'].lower():h['value'] for h in message.get('payload',{}).get('headers',[])}
    texts = []
    def visit(part):
        if part.get('mimeType', part.get('mime_type')) == 'text/plain':
            body = part.get('body',{})
            if 'content' in body:
                texts.append(body['content'])
            elif body.get('data'):
                data=body['data'];texts.append(base64.urlsafe_b64decode(data+'='*(-len(data)%4)).decode('utf-8'))
        for child in part.get('parts') or []:
            visit(child)
    visit(message.get('payload',{}))
    if not texts:
        raise ValueError('SUPPORTED_TEXT_PLAIN_BODY_UNAVAILABLE')
    stamp=message.get('internalDate', message.get('internal_date'))
    return dict(sender=headers.get('from',''),subject=headers.get('subject',''),
                body='\n'.join(texts),message_id=message['id'],
                rfc_message_id=headers.get('message-id'),
                received_at=datetime.fromtimestamp(int(stamp)/1000,timezone.utc).isoformat())


class MailProvider(Protocol):
    """Injected authorized read-only transport; implementations must never log bodies."""
    def list_messages(self, *, query: str, page_token: str | None, max_results: int) -> dict: ...
    def get_message(self, message_id: str) -> dict: ...
    def history(self, checkpoint: str) -> dict: ...


class MailFailure(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise MailFailure('UNEXPECTED_REDIRECT')


class GmailReadonlyAPI:
    """Supported REST adapter with injected, explicitly authorized OS-vault tokens.

    gmail.readonly is mailbox-wide, NOT sender-limited. Query/header checks enforce
    application scope. This adapter never refreshes/persists credentials itself.
    No modify/send/delete endpoints, generic HTTP cache, redirects or raw diagnostics.
    """
    SCOPE='https://www.googleapis.com/auth/gmail.readonly'
    def __init__(self, token_provider, *, granted_scopes, opener=None, label_id=None):
        if set(granted_scopes)!={self.SCOPE}:
            raise ValueError('explicit least-privilege gmail.readonly grant required')
        self._token_provider=token_provider
        self._opener=opener or build_opener(_NoRedirect()).open
        self._label=label_id

    def _get(self, path, params=None):
        try:token=self._token_provider()
        except Exception:raise MailFailure('TOKEN_PROVIDER_UNAVAILABLE') from None
        if not isinstance(token,str) or not token:raise MailFailure('AUTH_EXPIRED')
        url='https://gmail.googleapis.com/gmail/v1/users/me/'+path
        if params:url+='?'+urlencode(params)
        request=Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/json'},method='GET')
        try:
            with self._opener(request,timeout=12) as response:
                if response.status!=200 or 'json' not in response.headers.get('Content-Type','').lower():
                    raise MailFailure('INVALID_RESPONSE_TYPE')
                data=response.read(2_000_001)
                if len(data)>2_000_000:raise MailFailure('RESPONSE_SIZE_BUDGET_EXHAUSTED')
                obj=json.loads(data)
                if not isinstance(obj,dict):raise MailFailure('INVALID_RESPONSE_SCHEMA')
                return obj
        except HTTPError as exc:
            # Intentionally never read or serialize the private HTTP error body.
            if exc.code in (401,403):raise MailFailure('AUTH_REVOKED') from None
            if exc.code==404 and path=='history':raise MailFailure('HISTORY_CHECKPOINT_EXPIRED') from None
            raise MailFailure('HTTP_'+str(exc.code)) from None
        except (URLError,OSError,ValueError):raise MailFailure('TRANSPORT_OR_JSON_FAILURE') from None

    def list_messages(self, *, query, page_token=None, max_results=50):
        bounds=re.fullmatch(re.escape(QUERY)+r' after:(\d+) before:(\d+)',query)
        if not bounds or int(bounds[1])>=int(bounds[2]) or not 1<=max_results<=100:
            raise ValueError('newsletter query scope required')
        params={'q':query,'maxResults':max_results}
        if page_token:params['pageToken']=page_token
        if self._label:params['labelIds']=self._label
        obj=self._get('messages',params)
        messages=obj.get('messages',[])
        if not isinstance(messages,list) or any(not isinstance(m,dict) or not re.fullmatch(r'[A-Za-z0-9_-]+',str(m.get('id',''))) for m in messages):
            raise MailFailure('INVALID_RESPONSE_SCHEMA')
        return {'message_ids':[m['id'] for m in messages],'next_page_token':obj.get('nextPageToken')}

    def get_message(self, message_id):
        if not re.fullmatch(r'[A-Za-z0-9_-]+',message_id):raise ValueError('invalid message identity')
        return self._get('messages/'+message_id,{'format':'full'})

    def history(self, checkpoint):
        # Never enumerate unrelated mailbox history. A user-configured newsletter
        # label is required; otherwise bounded sender-scoped resync is safer.
        if not self._label:raise MailFailure('HISTORY_CHECKPOINT_EXPIRED')
        obj=self._get('history',{'startHistoryId':checkpoint,'labelId':self._label,'historyTypes':'messageAdded','maxResults':100})
        if obj.get('nextPageToken'):raise MailFailure('HISTORY_CHECKPOINT_EXPIRED')
        return {'history_id':obj.get('historyId',checkpoint)}


def sync_mail(provider: MailProvider | None, state: dict, *, now: datetime,
              horizon_days: int = 14, overlap_hours: int = 48, max_pages: int = 4,
              page_size: int = 50) -> tuple[dict,dict]:
    """Bounded/idempotent synchronization. Caller commits checkpoint after report QA.

    State contains private stable IDs and must be kept outside public artifacts.
    No checkpoint advances after partial fetch, auth failure or exhausted pagination.
    """
    if now.tzinfo is None or not (1 <= horizon_days <= 90 and 1 <= max_pages <= 20
                                and 1 <= page_size <= 100 and 1 <= overlap_hours <= 168):
        raise ValueError('invalid bounded synchronization settings')
    public={'status':'GMAIL_AUTHORIZATION_REQUIRED','batches':[],
            'reconciliation_complete':False,'query_scope':QUERY}
    if provider is None:
        return public,dict(state)
    start=now-timedelta(days=horizon_days)
    if state.get('watermark'):
        start=max(start,_aware(state['watermark'])-timedelta(hours=overlap_hours))
    query=QUERY+f' after:{int(start.timestamp())} before:{int(now.timestamp())}'
    seen=set(state.get('message_ids',[])); fetched=[]; checkpoint=state.get('history_id')
    try:
        ids=[]
        if checkpoint:
            try:
                history=provider.history(checkpoint)
                # History is mailbox-wide: only list-scoped IDs below may be read.
                checkpoint=history.get('history_id',checkpoint)
            except MailFailure as exc:
                if exc.code!='HISTORY_CHECKPOINT_EXPIRED': raise
                public['history_fallback']='BOUNDED_RESYNCHRONIZATION'
                checkpoint=None
        token=None
        for _ in range(max_pages):
            page=provider.list_messages(query=query,page_token=token,max_results=page_size)
            ids.extend(page.get('message_ids',[]));token=page.get('next_page_token')
            if not token: break
        for identity in dict.fromkeys(ids):
            if identity in seen: continue
            envelope=decode_gmail_message(provider.get_message(identity))
            # Defense in depth: enforce sender/subject again after scoped search.
            batch=parse_newsletter(**envelope,ingested_at=now.isoformat())
            if not (start <= _aware(batch['received_at']) <= now):
                raise MailFailure('RECEIVED_TIME_OUTSIDE_SYNC_WINDOW')
            fetched.append(identity);public['batches'].append(batch)
        complete=not token and all(b['status']=='PARSED' for b in public['batches'])
        public.update(status='GMAIL_RECONCILED' if complete else 'GMAIL_PARTIAL',
                      reconciliation_complete=complete,
                      requested_start=start.isoformat(),requested_end=now.isoformat(),
                      duplicate_messages=len(set(ids)&seen),pagination_exhausted=not token)
        if not complete: return public,dict(state)
        return public,dict(state,message_ids=sorted(seen|set(fetched)),
                           watermark=now.isoformat(),history_id=checkpoint)
    except (MailFailure,TimeoutError,ConnectionError,ValueError) as exc:
        code=exc.code if isinstance(exc,MailFailure) else type(exc).__name__
        if isinstance(exc,MailFailure) and not re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}',code):
            code='SAFE_PROVIDER_FAILURE'
        public.update(status=('GMAIL_AUTHORIZATION_REQUIRED' if code in {
            'AUTH_REVOKED','AUTH_EXPIRED','PERMISSION_DENIED'} else 'GMAIL_UNAVAILABLE'),
            error_code=code)
        # Never include exception text: provider errors can contain private bodies/tokens.
        return public,dict(state)


def reconcile(batches: list[dict], public_rows: list[dict], *, scheduled_at: str | None) -> list[dict]:
    """Source identity reconciliation; never creates or upgrades publication events."""
    scheduled=_aware(scheduled_at) if scheduled_at else None
    known={str(r.get('eprint_id')):r for r in public_rows if r.get('eprint_id')}
    output=[];seen=set()
    for batch in batches:
        for entry in batch['entries']:
            identity=entry['eprint_id'];row=known.get(identity); codes=[]
            if identity in seen: codes.append('EMAIL_DUPLICATE')
            seen.add(identity)
            if not row:
                codes.append('EMAIL_ONLY_PENDING_PUBLIC')
            else:
                norm=lambda s: re.sub(r'\W+','',unicodedata.normalize('NFKC',s)).casefold()
                whole_mail=norm(' '.join(entry.get('bibliographic_lines') or
                    [entry['title'],','.join(entry.get('authors',[]))]))
                whole_public=norm(row.get('title','')+','.join(row.get('authors') or []))
                boundary_reconciled=bool(whole_mail and row.get('authors') and whole_mail==whole_public)
                if boundary_reconciled:
                    codes.append('EMAIL_AND_PUBLIC_MATCH')
                elif norm(entry['title']) != norm(row.get('title','')):
                    codes.append('EMAIL_PARSE_FAILURE')
                elif entry.get('authors') and row.get('authors') and norm(','.join(entry['authors']))!=norm(','.join(row['authors'])):
                    codes.append('EMAIL_PARSE_FAILURE')
                else:
                    codes.append('EMAIL_AND_PUBLIC_MATCH')
                if not row.get('publication_timestamp') and not row.get('publication_date'):
                    codes.append('UNRESOLVED_PUBLICATION_TIME')
                if row.get('scientific_exclusion_verified') is True:
                    codes.append('CORRECT_NON_CORE_EXCLUSION')
                if row.get('independently_verified_false_negative') is True:
                    codes.append('SCIENTIFIC_FALSE_NEGATIVE')
            if scheduled and _aware(batch['received_at']) > scheduled:
                codes.append('EMAIL_DELAYED_ARRIVAL')
            output.append({'eprint_id':identity,'message_ref':batch['message_ref'],
                           'statuses':codes,'received_at':batch['received_at'],
                           'title_author_boundary_status':('EMAIL_BOUNDARY_RECONCILED_FROM_PUBLIC_SOURCE'
                               if row and boundary_reconciled else 'PENDING_OR_EXPLICIT_FIELD_MATCH'),
                           'publication_time':(row or {}).get('publication_timestamp') or (row or {}).get('publication_date'),
                           'reason':'Mail receipt is observation evidence; event ownership requires official source verification.'})
    for identity in sorted(set(known)-seen):
        output.append({'eprint_id':identity,'statuses':['PUBLIC_ONLY_NO_MATCHING_EMAIL'],
                       'reason':'No matching email within the bounded queried horizon; absence is not publication evidence.'})
    return output


def optional_daily_stage(public_rows: list[dict], *, scheduled_at: str | None,
                         provider: MailProvider | None = None, state: dict | None = None,
                         now: datetime | None = None) -> tuple[dict,dict]:
    """Optional runner stage; missing mail never changes public source authority.

    No ambient credentials or filesystem checkpoint are loaded. An explicitly
    authorized integration injects provider/state and persists the returned private
    checkpoint only after public report acceptance. Pending mail never enters rank.
    """
    result, proposed=sync_mail(provider,state or {},now=now or datetime.now(timezone.utc))
    batches=result.pop('batches')
    result['reconciliation']=(reconcile(batches,public_rows,scheduled_at=scheduled_at)
        if result['reconciliation_complete'] else [])
    result['batch_receipts']=[{k:b[k] for k in ('message_ref','received_at','ingested_at',
        'advertised_count','contents_count','body_sha256','status')} for b in batches]
    if batches:proposed={**proposed,'pending_private_batches':batches}
    result['scheduled_run_at']=scheduled_at or 'UNKNOWN'
    result['affects_public_source_authority']=False
    return result,proposed
