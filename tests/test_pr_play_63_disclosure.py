"""Disclosure boundary development controls; holdout evaluated separately once."""
import copy
import pytest
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q
from tests.test_pr_play_57_integrated_narration import hook, ROUTE
from tests.pr_play_58_development import PRINTS


def assess(h,text):
 c,r=i.outcome_contract(h)
 return c,r,i.validate_integrated(c,r,text)


def test_new_disclosure_survives_post_resolution_recording():
 h=hook(known=(ROUTE,));before=copy.deepcopy(h)
 c,r,a=assess(h,ROUTE)
 assert [f['text'] for f in r['must_communicate']]==[ROUTE]
 assert not r['may_reference']['continuity']
 assert a['decision']=='PASS'
 assert assess(h,'You examine the board.')[2]['decision']!='PASS'
 assert h==before


@pytest.mark.parametrize('text,expected',[
 ('You examine the rain barrel; no new clue is established.','PASS'),
 ('You examine the rain barrel; no new clue is established. '+ROUTE,'PASS'),
 ('The missing patrol was last seen taking the southeast mud track past the crates.','FAIL'),
 ('No new clue is established. The guard captain dies where he stands.','FAIL'),
 ('No new clue is established. You acquire a silver key.','FAIL'),
 ('You discover a red ribbon beneath the barrel.','FAIL'),
])
def test_prior_authorization_is_optional_but_safety_remains(text,expected):
 h=hook(kind='investigate',clues=[],known=(ROUTE,))
 c,r,a=assess(h,text)
 assert a['decision']==expected
 assert r['may_reference']['continuity']==[ROUTE]
 assert all(f['source']!='player_knowledge' for f in r['must_communicate'])


@pytest.mark.parametrize('text,passes',[
 ('You examine it again; nothing new is established.',True),
 ('You discover the route for the first time. '+ROUTE,False),
 ('You discover a hidden passage.',False),
 ('Nothing new is established.',False),
])
def test_repeat_preserves_continuity(text,passes):
 h=hook(kind='already_searched',success=False,clues=[],known=(ROUTE,))
 assert (assess(h,text)[2]['decision']=='PASS')==passes


def test_resolver_reconfirmation_and_mixed_disclosures():
 # Existing resolver selection, not natural-language inference or new parser.
 h=hook(known=(ROUTE,PRINTS))
 assert assess(h,ROUTE)[2]['decision']=='PASS'
 assert assess(h,'You examine the board.')[2]['decision']!='PASS'
 h=hook(clues=[ROUTE,PRINTS],known=(ROUTE,PRINTS))
 c,r,a=assess(h,ROUTE+' '+PRINTS)
 assert len(r['must_communicate'])==2
 assert a['decision']=='PASS'
 assert assess(h,ROUTE)[2]['decision']!='PASS'


@pytest.mark.parametrize('fault,text',[('provider_error',ROUTE),('timeout',ROUTE),('', ''),('',{}),('', 'You examine the board.'),('', 'You acquire a silver key.')])
def test_fallback_covers_current_disclosure(monkeypatch,fault,text):
 monkeypatch.setenv(q.PUBLICATION_ENV,'1')
 h=hook(known=(ROUTE,))
 row=i.run_integrated_hook(h,generator=q._Replay(text,fault))
 assert row['used_fallback']
 assert ROUTE in row['assembled']
 c,r=i.outcome_contract(h)
 assert i.validate_integrated(c,r,row['assembled'])['decision']=='PASS'


def test_unrelated_and_repeat_fallback_omit_prior_details():
 for kind in ('investigate','already_searched'):
  h=hook(kind=kind,success=False if kind=='already_searched' else True,clues=[],known=(ROUTE,))
  c,r=i.outcome_contract(h);text=i.action_fallback(c,h)
  assert ROUTE not in text
  assert i.validate_integrated(c,r,text)['decision']=='PASS'


def test_detached_campaign_context_does_not_accumulate():
 # Pure projection has no cache; same fact in one session cannot authorize another.
 prior=hook(kind='investigate',clues=[],known=(ROUTE,))
 fresh=hook(kind='investigate',clues=[],known=())
 assert assess(prior,'No new clue is established. '+ROUTE)[2]['decision']=='PASS'
 assert assess(fresh,'No new clue is established. '+ROUTE)[2]['decision']!='PASS'
 assert not i.outcome_contract(fresh)[1]['may_reference']['continuity']


def test_ambiguous_missing_resolution_not_inferred_from_known_state():
 h=hook(known=(ROUTE,));h['resolution']={}
 with pytest.raises(ValueError):i.outcome_contract(h)


@pytest.mark.parametrize('decision',['FAIL','REVIEW_REQUIRED','VALIDATION_ERROR'])
def test_non_pass_gates_still_force_fallback(monkeypatch,decision):
 monkeypatch.setenv(q.PUBLICATION_ENV,'1')
 monkeypatch.setattr(i.semantic,'validate_consequential_narration',lambda *a: {'decision':decision,'reasons':['injected'],'claims':[]})
 row=i.run_integrated_hook(hook(),generator=q._Replay(ROUTE,''))
 assert row['used_fallback'] and ROUTE in row['assembled']
 assert row['validation']['decision']==decision
