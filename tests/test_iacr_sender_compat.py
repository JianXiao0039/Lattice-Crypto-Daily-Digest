"""Single-mailbox security checks also hold with Python3.11's lenient parser."""
import pytest
from lattice_digest import iacr_mail


def parse(sender):
    return iacr_mail.parse_newsletter(sender=sender,
        subject='Your IACR news update: ePrint Report (x0)',body='Contents:\n\n----------\n',
        message_id='local-test-only',received_at='2026-10-19T01:00:00Z',
        ingested_at='2026-10-19T01:01:00Z')


VALID=['newbounce@iacr.org','NEWBOUNCE@IACR.ORG',' newbounce@iacr.org ',
       'IACR <newbounce@iacr.org>','IACR ePrint News <newbounce@iacr.org>',
       '"IACR, ePrint" <newbounce@iacr.org>','"IACR \\"news\\"" <newbounce@iacr.org>']


BAD=['newbounce@iacr.org <attacker@evil.invalid>',
     '"newbounce@iacr.org" <attacker@evil.invalid>',
     '"attacker@evil.invalid" <newbounce@iacr.org>',
     'newbounce@iacr.org, attacker@evil.invalid',
     'IACR <newbounce@iacr.org>, Attacker <attacker@evil.invalid>',
     'IACR <newbounce@iacr.org> attacker@evil.invalid',
     'IACR <newbounce@iacr.org> <attacker@evil.invalid>',
     'IACR <<newbounce@iacr.org>>','IACR <newbounce@iacr.org',
     'IACR newbounce@iacr.org>','<newbounce@iacr.org>',
     'IACR <newbounce@iacr.org> trailing',
     'IACR (attacker) <newbounce@iacr.org>',
     'Group: newbounce@iacr.org;','IACR <newbounce@iacr.org;>',
     'IACR <newbounce@iacr.org\x00>','IACR\r\n <newbounce@iacr.org>',
     'newbounce@iacr.org\r\nBcc: attacker@evil.invalid',
     'IACR\t<newbounce@iacr.org>','IACR <newbounce@iacr.org>\x7f',
     'IACR <newbounce@iacr.org.evil.invalid>','IACR <newbounce@iacr.org >',
     '"unterminated IACR <newbounce@iacr.org>','IACR"name <newbounce@iacr.org>']


@pytest.mark.parametrize('sender',VALID)
def test_single_explicit_public_sender_and_legal_display_names(sender):
    assert parse(sender)['status']=='PARSED'


@pytest.mark.parametrize('sender',BAD)
def test_spoof_multi_address_and_malformed_sender_rejected(sender):
    with pytest.raises(ValueError,match='^NOT_IACR_EPRINT_NEWSLETTER$'):
        parse(sender)


@pytest.mark.parametrize('sender',BAD)
def test_legacy_lenient_parser_cannot_accept_invalid_whole_header(sender,monkeypatch):
    # Simulate the vulnerable3.11 prefix extraction independently of the host
    # interpreter: every malformed input appears to parse to the allowed sender.
    monkeypatch.setattr(iacr_mail,'parseaddr',lambda value:('',iacr_mail.SENDER))
    with pytest.raises(ValueError,match='^NOT_IACR_EPRINT_NEWSLETTER$'):
        parse(sender)
