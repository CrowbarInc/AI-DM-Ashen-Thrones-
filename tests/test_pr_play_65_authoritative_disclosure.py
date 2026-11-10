"""Complete-hook development controls; frozen holdout is not imported here."""
import copy
import json
import pytest
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q
from tests.test_pr_play_57_integrated_narration import hook, ROUTE
from tests.pr_play_58_development import PRINTS

@pytest.fixture(autouse=True)
def flags(monkeypatch):
    monkeypatch.setenv(i.DISCLOSURE_ENV,'1')
    monkeypatch.setenv(q.PUBLICATION_ENV,'1')

def run(text='You examine the notice board.', h=None, fault=''):
    h = h or hook()
    before=copy.deepcopy(h)
    row=i.run_integrated_hook(h,generator=q._Replay(text,fault))
    assert h==before
    c,r=i.outcome_contract(h)
    assert i.validate_integrated(c,r,row['assembled'])['decision']=='PASS'
    assert i.mandatory_coverage(row['assembled'],r)['decision']=='PASS'
    return row

@pytest.mark.parametrize('text',[
    'You examine the notice board.', 'Rain falls around the notice board.',
    'You inspect the notice board.', 'You focus on the notice board.',
])
def test_optional_prose_need_not_repeat_discovery(text):
    row=run(text)
    assert not row['used_fallback']
    assert row['trusted_disclosure']==ROUTE
    assert row['assembled']==text+' '+ROUTE
    assert row['validation']['presentation']['decision']=='PASS'
    assert 'SECRET' not in json.dumps(row)

@pytest.mark.parametrize('text',[
    'You discover a second patrol route.', 'The patrol took the southeast road.',
    'The gate is permanently open.', 'You acquire a silver compass.',
    'The guard captain dies where he stands.', 'You gain 10 gold coins.',
    'You find a hidden passage.', 'SECRET is behind the gate.',
    'The missing patrol definitely reached the milestone.',
    'The missing patrol was not last seen taking the northwest mud track past the crates.',
    'You take the iron key.', 'You discover a red ribbon beneath the board.',
    'The patrol was last seen taking the northeast mud track.',
])
def test_unsafe_optional_prose_rejected(text):
    row=run(text)
    assert row['used_fallback']
    assert text not in row['assembled']

@pytest.mark.parametrize('text',[ROUTE,'You examine the notice board. '+ROUTE,
    'You learn that the missing patrol was last seen taking the northwest mud track past the crates.'])
def test_duplicate_omits_entire_optional_segment(text):
    row=run(text)
    assert row['used_fallback'] and row['assembled'].count(ROUTE)==1

@pytest.mark.parametrize('text,fault',[('', ''),({},''),(None,''),('unfinished',''),
                                     (None,'timeout'),(None,'provider_error')])
def test_provider_failure_still_delivers(text,fault):
    assert run(text,fault=fault)['used_fallback']

@pytest.mark.parametrize('decision',['FAIL','REVIEW_REQUIRED','VALIDATION_ERROR'])
def test_nonpass_safety_never_composed(monkeypatch,decision):
    monkeypatch.setattr(i.semantic,'validate_consequential_narration',
        lambda *a:{'decision':decision,'reasons':['injected'],'claims':[]})
    row=i.run_integrated_hook(hook(),generator=q._Replay('You examine the notice board.',''))
    assert row['used_fallback'] and ROUTE in row['assembled']

def test_multiple_disclosures():
    row=run(h=hook(clues=[ROUTE,PRINTS]))
    assert not row['used_fallback'] and PRINTS in row['assembled']

@pytest.mark.parametrize('kind',['investigate','already_searched','observe'])
def test_prior_information_not_automatically_repeated(kind):
    row=run('You examine the notice board again.',hook(kind=kind,clues=[],known=(ROUTE,)))
    assert ROUTE not in row['assembled']
    assert all(f['source']!='player_knowledge' for f in row['trusted_facts'])

def test_current_and_historical_provenance():
    row=run(h=hook(known=(ROUTE,PRINTS)))
    assert ROUTE in row['assembled'] and PRINTS not in row['assembled']

def test_authorized_context_without_new_disclosure():
    row=run('No new clue is established. '+ROUTE,
            hook(kind='investigate',clues=[],known=(ROUTE,)))
    # Current status duplicated -> optional omitted, historical context never mandatory.
    assert row['used_fallback']
    c,r=i.outcome_contract(hook(kind='investigate',clues=[],known=(ROUTE,)))
    a,_=i.compose_authoritative(c,r,ROUTE,i.trusted_disclosure(r))
    assert a['decision']=='PASS'

def test_generator_cannot_mutate_projection():
    class Mutator:
        def generate(self,request):
            request['must_communicate'][0]['text']='You acquire a crown.'
            return 'You examine the notice board.'
    row=i.run_integrated_hook(hook(),generator=Mutator())
    assert row['trusted_disclosure']==ROUTE and 'crown' not in row['assembled']

def test_forged_trusted_segment_refused():
    c,r=i.outcome_contract(hook())
    with pytest.raises(ValueError,match='provenance'):
        i.compose_authoritative(c,r,'You examine the notice board.','You acquire a crown.')

def test_flag_disabled_preserves_legacy(monkeypatch):
    monkeypatch.delenv(i.DISCLOSURE_ENV)
    row=i.run_integrated_hook(hook(),generator=q._Replay('You examine the notice board.',''))
    assert row['used_fallback'] and 'trusted_disclosure' not in row

def test_no_cross_session_or_campaign_authority():
    prior=run(h=hook(known=(PRINTS,)))
    fresh=run(PRINTS,hook(clues=[]))
    assert prior['trusted_disclosure']==ROUTE
    assert fresh['used_fallback'] and PRINTS not in fresh['assembled']

def test_publication_requires_bound_session_and_validated_composition(monkeypatch):
    q.clear_evidence()
    monkeypatch.setenv(q.GATE_ENV,'1');monkeypatch.setenv(q.MODE_ENV,'integrated')
    monkeypatch.setenv(q.PUBLICATION_SESSION_ENV,'bound')
    row=run();row['player_text']='examine'
    q._MEMORY.append(row)
    assert q.validated_player_text('examine',session_id='other',kind='investigate') is None
    assert q.validated_player_text('examine',session_id='bound',kind='investigate')==row['assembled']
    assert not row.get('player_facing_published')
    row['assembled']='You acquire a crown. '+ROUTE
    assert q.validated_player_text('examine',session_id='bound',kind='investigate') is None
    q.clear_evidence()
