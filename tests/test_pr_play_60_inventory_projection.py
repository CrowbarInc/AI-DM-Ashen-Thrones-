"""Resolver-supplied inventory projections through every integrated gate."""
import copy
import json
from dataclasses import replace
import pytest
from artifacts.pr_play_60.evaluate import development_cases, run
from game import integrated_investigation_narration as i
from game import anchored_investigation_narration as a
from game import quarantined_investigation_narration as q
from tests.test_pr_play_57_integrated_narration import hook, ROUTE

@pytest.mark.parametrize('case',development_cases(),ids=lambda c:c['id'])
def test_complete_pipeline(case):
    row=run(case)
    assert row['actual']==case['expected']
    assert row['state_unchanged']

def test_original_d25_text_is_not_a_structured_grant():
    h=hook();contract,request=i.outcome_contract(h)
    contract=replace(contract,outcome=replace(contract.outcome,consequences='You pick up the key.'))
    assert i.validate_integrated(contract,request,ROUTE+' You pick up the key and place it in your pack.')['decision']=='FAIL'

def test_no_effect_from_observation_or_payload_or_request():
    h=hook();h['narration_payload']['authorized_mechanical_outcome']={'items_added':['iron key']}
    h['narration_payload']['scene']['public']['visible_facts']=['An iron key lies on the table.']
    contract,request=i.outcome_contract(h)
    request['authorized_consequences']={'items_added':['iron key']}
    assert a._resolution(contract)['state_changes']=={}
    assert i.validate_integrated(contract,request,ROUTE+' You acquire the iron key.')['decision']=='FAIL'

def test_inventory_projection_detaches_and_keeps_identity_quantity():
    h=hook();h['resolution']['state_changes']={'items_added':[{'id':'iron_key','name':'iron key','quantity':2,'secret':'PRIVATE'}]}
    before=copy.deepcopy(h);c,r=i.outcome_contract(h)
    assert h==before
    assert a._resolution(c)['state_changes']['items_added']==[{'id':'iron_key','name':'iron key','quantity':2}]
    assert 'PRIVATE' not in json.dumps(r)
    r['authorized_consequences']['items_added'][0]['quantity']=200
    assert json.loads(c.outcome.inventory_effects_json)['items_added'][0]['quantity']==2

def test_runtime_hook_still_rejects_effects(monkeypatch):
    monkeypatch.setenv(q.MODE_ENV,'integrated')
    with pytest.raises(ValueError,match='side_effects'):
        q.build_hook_input(resolution={'kind':'investigate','state_changes':{'items_added':['key']}},scene={},known_clue_texts=[],player_text='Take it.')

def test_unknown_effect_not_projected_as_inventory():
    h=hook();h['resolution']['state_changes']={'items_transferred':['key'],'equipment_changed':['sword']}
    c,r=i.outcome_contract(h)
    assert a._resolution(c)['state_changes']=={}
    assert i.validate_integrated(c,r,ROUTE+' You transfer the key to Mira.')['decision']=='FAIL'

@pytest.mark.parametrize('text',[ROUTE+' You acquire a ruby.',ROUTE+' The gate is permanently open.','Rain falls.','',{},'unfinished'])
def test_quarantine_failure_preserves_input_and_fallback(text):
    h=hook();before=copy.deepcopy(h)
    result=i.run_integrated_hook(h,generator=q._Replay(text,''))
    assert h==before and result['promoted'] is False and result['used_fallback']
    assert result['assembled']==a.fallback(i.outcome_contract(h)[0])
