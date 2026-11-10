"""Persistent authority safety, authorization binding, and quarantine controls."""
import copy
import pytest
from game import consequential_narration_validation as s
from game import integrated_investigation_narration as i
from game import quarantined_investigation_narration as q
from game.persistent_consequence_claims import assertions
from tests.pr_play_59_development import cases
from tests.test_pr_play_57_integrated_narration import hook, ROUTE

@pytest.mark.parametrize('case',cases(),ids=lambda c:c['id'])
def test_development(case):
    authority=s.SemanticAuthority(**{k:tuple(v) for k,v in case['authority'].items()})
    before=copy.deepcopy(authority)
    assert s.validate_consequential_narration(case['text'],authority)['decision']==case['expected']
    assert authority==before

@pytest.mark.parametrize('text', ['You destroy the astrolabe.','They killed the sentinel.','You unlock the amber coffer.'])
def test_active_unfamiliar_entities(text):
    assert s.validate_consequential_narration(text,s.SemanticAuthority())['decision']=='FAIL'

@pytest.mark.parametrize('case',[c for c in cases() if c['group']=='authorized'],ids=lambda c:c['id'])
def test_positive_controls_are_extracted(case):
    assert assertions(case['text'])


def test_disclosure_not_entity_presence():
    a=s.SemanticAuthority(observable_scene=('The gate is open.',),restricted=('The gate is permanently open.',))
    assert s.validate_consequential_narration('The gate is permanently open.',a)['decision']=='FAIL'


def test_state_and_quarantine_failure_preserves_fallback():
    h=hook();before=copy.deepcopy(h)
    contract,request=i.outcome_contract(h)
    assert request['authorized_consequences']==[]
    text=ROUTE+' The gate is now permanently open.'
    v=i.validate_integrated(contract,request,text)
    assert v['coverage']['decision']=='PASS'
    assert v['semantic']['decision']=='FAIL'
    assert v['decision']=='FAIL'
    result=i.run_integrated_hook(h,generator=q._Replay(text,''))
    assert result['used_fallback'] and result['promoted'] is False
    assert 'permanently open' not in result['assembled']
    assert h==before


def test_exception_fails_closed(monkeypatch):
    def broken(*args):raise RuntimeError('synthetic validator fault')
    monkeypatch.setattr(s,'validate_persistent',broken)
    assert s.validate_consequential_narration('The gate opens.',s.SemanticAuthority())['decision']=='VALIDATION_ERROR'


def test_temporary_authority_does_not_grant_omitted_duration():
    a=s.SemanticAuthority(authorized_outcomes=('The gate opens temporarily.',))
    assert s.validate_consequential_narration('The gate opens.',a)['decision']=='FAIL'
