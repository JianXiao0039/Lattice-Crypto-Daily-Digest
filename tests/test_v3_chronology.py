from datetime import datetime,timezone,timedelta
from lattice_digest.publication_chronology import late_discoveries,precision
from lattice_digest.publication_events import canonical_identity,event_id

START=datetime(2026,10,16,20,18,41,tzinfo=timezone.utc)
END=datetime(2026,10,18,8,18,41,tzinfo=timezone.utc)
OBS=END+timedelta(seconds=4)
def record(**kw):
    return dict(title='Lattice-based threshold signature construction',
        abstract='We construct a threshold signature from Module-SIS.',
        source_url='https://eprint.iacr.org/2026/1000',eprint_id='2026/1000',
        publication_timestamp='Thu, 15 Oct 2026 06:55:07 +0000',
        source_observed_at=OBS.isoformat(),**kw)
def late(rows,prior=()):
    return late_discoveries(rows,prior,START,END,canonical_identity,event_id,
                           observed_through=OBS+timedelta(seconds=1))
def test_rfc_feed_date_and_post_cutoff_fetch_are_late_not_new_publication():
    result=late([record()]);assert len(result)==1
    assert result[0]['counts_as_new_publication'] is False
    assert result[0]['observed_after_publication_cutoff'] is True
    assert result[0]['first_publication_time']=='Thu, 15 Oct 2026 06:55:07 +0000'
def test_prior_identity_suppresses_reopening_and_stable_ids_ignore_retrieval_time():
    row=record();assert late([row],[row])==[]
    first=late([row])[0]['event_id']
    row['source_observed_at']=(OBS-timedelta(seconds=2)).isoformat()
    assert late([row])[0]['event_id']==first
def test_future_observation_and_old_library_population_do_not_become_late_news():
    row=record();row['source_observed_at']=(OBS+timedelta(days=2)).isoformat()
    assert late([row])==[]
    row=record();row['publication_timestamp']='2024-10-15T06:00:00Z';assert late([row])==[]
def test_date_only_precision_never_becomes_fictitious_second_timestamp():
    assert precision('2026-10-15')=='DATE_ONLY'
    row=record();row['publication_timestamp']='2026-10-15'
    r=late([row]);assert r[0]['first_publication_time']=='2026-10-15'
    assert r[0]['publication_time_precision']=='DATE_ONLY'
    row['publication_timestamp']='2026-10-16';assert late([row])==[]
