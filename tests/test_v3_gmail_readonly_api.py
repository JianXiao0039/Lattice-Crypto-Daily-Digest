"""Independent Gmail REST/privacy canaries with injected offline transports only."""
import io
import json
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from lattice_digest.iacr_mail import GmailReadonlyAPI, MailFailure, QUERY, _NoRedirect

SCOPE=GmailReadonlyAPI.SCOPE


class Response:
    def __init__(self,payload=None,*,status=200,content_type='application/json',body=None):
        self.status=status;self.headers={'Content-Type':content_type}
        self.body=body if body is not None else json.dumps(payload or {}).encode()
        self.read_limits=[]
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,limit):self.read_limits.append(limit);return self.body[:limit]


def api(opener,token=lambda:'MOCK_ONLY_NOT_A_REAL_TOKEN',**kwargs):
    return GmailReadonlyAPI(token,granted_scopes=[SCOPE],opener=opener,**kwargs)


def test_api_is_get_only_fixed_host_explicit_scoped_query_and_no_disk_cache(tmp_path):
    calls=[];response=Response({'messages':[{'id':'18abc'}]})
    def opener(request,timeout):calls.append((request,timeout));return response
    client=api(opener)
    result=client.list_messages(query=QUERY+' after:1 before:100',max_results=20)
    assert result=={'message_ids':['18abc'],'next_page_token':None}
    request,timeout=calls[0]
    assert request.get_method()=='GET'
    assert request.full_url.startswith('https://gmail.googleapis.com/gmail/v1/users/me/messages?')
    assert request.get_header('Authorization')=='Bearer MOCK_ONLY_NOT_A_REAL_TOKEN'
    assert request.get_header('Accept')=='application/json' and timeout==12
    assert response.read_limits==[2_000_001]
    assert not list(tmp_path.iterdir())
    assert not any(hasattr(client,name) for name in ('send_message','modify_message','delete_message'))


@pytest.mark.parametrize('scopes',[[],['https://www.googleapis.com/auth/gmail.modify'],
    ['https://mail.google.com/'],[SCOPE,'https://www.googleapis.com/auth/gmail.send']])
def test_only_explicit_least_privilege_grant_accepted(scopes):
    with pytest.raises(ValueError,match='gmail.readonly'):
        GmailReadonlyAPI(lambda:'MOCK',granted_scopes=scopes)


@pytest.mark.parametrize('query',[
    QUERY+' after:1 before:100 OR from:unrelated@example.invalid',
    QUERY+' after:0 OR in:anywhere',QUERY+' after:100 before:1',
    'in:inbox after:1 before:100',QUERY+' after:1 before:100\nOR in:anywhere'])
def test_query_expansion_and_invalid_horizon_rejected_before_read(query):
    calls=[]
    client=api(lambda *a,**kw:calls.append(a))
    with pytest.raises(ValueError,match='newsletter query scope'):
        client.list_messages(query=query)
    assert calls==[]


@pytest.mark.parametrize('identity',['../profile','abc?token=PRIVATE','abc/elsewhere','abc#fragment'])
def test_message_identity_cannot_change_rest_path(identity):
    calls=[];client=api(lambda *a,**kw:calls.append(a))
    with pytest.raises(ValueError):client.get_message(identity)
    assert not calls


@pytest.mark.parametrize('status,code',[(401,'AUTH_REVOKED'),(403,'AUTH_REVOKED'),(429,'HTTP_429'),(302,'HTTP_302')])
def test_http_error_body_is_never_read_or_leaked(status,code):
    class PrivateBody(io.BytesIO):
        def read(self,*args):pytest.fail('private HTTP body must not be read')
    def opener(request,timeout):
        raise HTTPError(request.full_url,status,'private-token-in-reason',{},PrivateBody(b'private-token-in-body'))
    with pytest.raises(MailFailure) as caught:api(opener).get_message('18abc')
    assert caught.value.code==code
    assert 'private-token' not in str(caught.value)
    assert caught.value.__suppress_context__


def test_vault_error_is_redacted_without_ambient_credentials(monkeypatch):
    monkeypatch.setenv('GOOGLE_ACCESS_TOKEN','PRIVATE_AMBIENT_SENTINEL')
    def vault():raise RuntimeError('PRIVATE_VAULT_SENTINEL')
    with pytest.raises(MailFailure) as caught:api(None,token=vault).get_message('18abc')
    assert caught.value.code=='TOKEN_PROVIDER_UNAVAILABLE'
    assert 'PRIVATE' not in str(caught.value) and caught.value.__suppress_context__


def test_missing_token_is_expired_not_ambient_authorization(monkeypatch):
    monkeypatch.setenv('GOOGLE_ACCESS_TOKEN','PRIVATE_AMBIENT_SENTINEL')
    with pytest.raises(MailFailure,match='AUTH_EXPIRED'):
        api(None,token=lambda:None).get_message('18abc')


@pytest.mark.parametrize('response,expected',[
    (Response(status=202,content_type='text/html',body=b'anti-bot challenge'),'INVALID_RESPONSE_TYPE'),
    (Response(body=b'PRIVATE_INVALID_JSON'),'TRANSPORT_OR_JSON_FAILURE'),
    (Response(body=b'[]'),'INVALID_RESPONSE_SCHEMA'),
    (Response(body=b'x'*2_000_001),'RESPONSE_SIZE_BUDGET_EXHAUSTED')])
def test_provider_response_type_schema_and_size_are_bounded(response,expected):
    with pytest.raises(MailFailure) as caught:
        api(lambda *a,**kw:response).get_message('18abc')
    assert caught.value.code==expected
    assert 'PRIVATE_INVALID_JSON' not in str(caught.value)


def test_redirect_handler_does_not_forward_bearer_token():
    request=Request('https://gmail.googleapis.com/gmail/v1/users/me/messages',headers={'Authorization':'Bearer MOCK'})
    with pytest.raises(MailFailure,match='UNEXPECTED_REDIRECT'):
        _NoRedirect().redirect_request(request,None,302,'redirect',{},'https://evil.invalid/')


def test_history_without_explicit_iacr_label_falls_back_without_mailbox_scan():
    calls=[];client=api(lambda *a,**kw:calls.append(a))
    with pytest.raises(MailFailure,match='HISTORY_CHECKPOINT_EXPIRED'):
        client.history('12345')
    assert not calls


def test_paginated_label_history_is_incomplete_and_forces_bounded_resync():
    calls=[]
    def opener(request,timeout):
        calls.append(request.full_url)
        return Response({'historyId':'88','nextPageToken':'more'})
    client=api(opener,label_id='IACR_APPROVED_LABEL')
    with pytest.raises(MailFailure,match='HISTORY_CHECKPOINT_EXPIRED'):
        client.history('12345')
    assert len(calls)==1 and 'labelId=IACR_APPROVED_LABEL' in calls[0]
