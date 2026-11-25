"""Turn authority at the ordinary HTTP narration fallback; no live providers."""
import copy
import json
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from game import api, storage
from game.integrated_play import _LANES
from game.provider_budget import snapshot
from tests.pr_play_79df3_harness import seed_gate
from tests.test_ordinary_semantic_admission import state

@pytest.fixture
def client(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    _LANES.clear()
    from tests.helpers.live_model_guard import production_call_gpt
    monkeypatch.setattr(api, 'call_gpt', production_call_gpt())
    for key in ('ASHEN_DISABLE_PROVIDER_CALLS','ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION','ASHEN_DISABLE_PROVIDER_RETRIES'):
        monkeypatch.setenv(key,'1')
    monkeypatch.delenv('ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION',raising=False)
    with TestClient(api.app) as http:
        yield http

def post(client, text, key):
    before=state(); providers=len(snapshot()['records']); start=time.perf_counter()
    response=client.post('/api/chat?ui_mode=player',json={'text':text,'client_request_id':key})
    row={'input':text,'before':before,'after':state(),'body':response.json(),'status':response.status_code,
         'elapsed_ms':(time.perf_counter()-start)*1000,'provider_delta':len(snapshot()['records'])-providers,
         'log':storage.load_log()[-1] if storage.load_log() else {}}
    directory=os.environ.get('ASHEN_NARRATION_INTEGRITY_EVIDENCE')
    if directory:
        target=Path(directory);target.mkdir(parents=True,exist_ok=True)
        path=target/(key+'.json')
        ordinal=2
        while path.exists():
            path=target/(key+'-'+str(ordinal)+'.json');ordinal+=1
        path.write_text(json.dumps(row,indent=2),encoding='utf8')
    assert response.status_code==200
    assert row['provider_delta']==0
    return row

def quiet(row):
    for domain in ('character','world','scene','combat'):
        assert row['before'][domain]==row['after'][domain],domain
    for field in ('turn_counter','clocks','active_scene_id','mechanical_action_receipts','npc_runtime'):
        assert row['before']['session'].get(field)==row['after']['session'].get(field),field

def visible(row):
    return row['body']['gm_output']['player_facing_text']

@pytest.mark.parametrize('text,key',[
    ('I look around.','disabled'),
    ('I equip the travel coat.','unsupported'),
    ('I examine the silver astrolabe.','object'),
    ('I ask the threadbare watcher about the patrol.','person'),
    ('I do not persuade the guard captain.','negated'),
    ('If he is listening, I try to persuade the guard captain.','conditional'),
    ('Describe the scene.','description'),
])
def test_unfulfilled_request_has_no_action_time(client,text,key):
    row=post(client,text,key);quiet(row)
    if key in ('disabled','unsupported'):
        assert 'not completed' in visible(row).lower()
        assert row['log']['resolution']['metadata']['conversational_decision']['authorization']['commit_status']=='not_committed'
        assert row['after']['session'].get('conversational_context',{}).get('last_executed_intention')==row['before']['session'].get('conversational_context',{}).get('last_executed_intention')

@pytest.mark.parametrize('mode',['failure','timeout','error_envelope'])
def test_provider_failure_before_commit(client,monkeypatch,mode):
    def fail(**kwargs):
        if mode=='error_envelope':
            return {'player_facing_text':'Provider unavailable.','tags':['fast_fallback'], 'metadata':{'upstream_api_error':{'failure_class':'connection'}}}
        raise TimeoutError('controlled timeout') if mode=='timeout' else RuntimeError('controlled provider failure')
    monkeypatch.setattr(api,'_build_gpt_narration_from_authoritative_state',fail)
    row=post(client,'I look around.','pre-'+mode);quiet(row)
    assert 'not completed' in visible(row).lower()
    duplicate=post(client,'I look around.','pre-'+mode)
    assert duplicate['body']==row['body'];quiet(duplicate)
    recovered=post(client,'What happened?','follow-'+mode);quiet(recovered)
    assert 'you looked around' not in visible(recovered).lower()

@pytest.mark.parametrize('mode',['disabled','failure','timeout','success'])
def test_resolved_action_keeps_its_time(client,monkeypatch,mode):
    calls=[]
    if mode in ('failure','timeout'):
        def fail(**kwargs):
            calls.append(1)
            raise TimeoutError('controlled timeout') if mode=='timeout' else RuntimeError('controlled failure')
        monkeypatch.setattr(api,'_build_gpt_narration_from_authoritative_state',fail)
    elif mode=='success':
        monkeypatch.setattr(api,'_build_gpt_narration_from_authoritative_state',lambda **kw: {'player_facing_text':'You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.','tags':[]})
    row=post(client,'I examine the notice board.','resolved-'+mode)
    assert row['after']['session']['turn_counter']==row['before']['session']['turn_counter']+1
    assert row['after']['session']['scene_runtime']['frontier_gate']['recent_player_actions'][-1]['turn']==row['after']['session']['turn_counter']
    assert 'northwest mud track' in visible(row)
    first=copy.deepcopy(row['after'])
    duplicate=post(client,'I examine the notice board.','resolved-'+mode)
    assert duplicate['body']==row['body'];assert duplicate['after']==first
    if mode in ('failure','timeout'): assert len(calls)==1
    # Reload the actual envelope through the persistence owner.
    assert storage.load_session()['turn_counter']==first['session']['turn_counter']
    assert storage.load_world()==first['world']

@pytest.mark.parametrize('mode',['failure','timeout','success'])
def test_durable_mechanical_commit_survives_publication_failure(client,monkeypatch,mode):
    import game.immutable_valid_response as publication
    original_seal=publication.seal_host_speech
    if mode!='success':
        def fail(*args,**kwargs):
            if kwargs.get('source')!='social_skill_check':
                return original_seal(*args,**kwargs)
            # The real receipt and NPC mutation must already be durable here.
            assert storage.load_session().get('mechanical_action_receipts')
            raise TimeoutError('controlled timeout') if mode=='timeout' else RuntimeError('controlled publication failure')
        monkeypatch.setattr(publication,'seal_host_speech',fail)
    row=post(client,'I try to persuade the guard captain.','mechanical-'+mode)
    after=row['after'];assert after['session'].get('mechanical_action_receipts')
    assert 'vs DC' in visible(row)
    assert row['log']['resolution']['metadata']['commit_status']=='committed'
    assert row['log']['resolution']['metadata']['publication_failure'] is (mode!='success')
    # This existing mechanical owner consumes no ordinary chat turn.
    assert after['session']['turn_counter']==row['before']['session']['turn_counter']
    duplicate=post(client,'I try to persuade the guard captain.','mechanical-'+mode)
    assert duplicate['body']==row['body'];assert duplicate['after']==after
    # A fresh lane must still use the durable action receipt on repetition.
    _LANES.clear()
    replay=post(client,'I try to persuade the guard captain.','durable-'+mode)
    assert replay['after']['session']['mechanical_action_receipts']==after['session']['mechanical_action_receipts']
    assert replay['after']['session']['npc_runtime']==after['session']['npc_runtime']
    follow=post(client,'Did I persuade the guard captain?','recall-'+mode)
    assert 'check' in visible(follow).lower()
    assert follow['after']['session']['npc_runtime']==after['session']['npc_runtime']

@pytest.mark.parametrize('ruleset',['pf1e','rules_light','scifi'])
def test_provider_fallback_does_not_borrow_ruleset(client,ruleset):
    from game.persistence_contract import wrap_runtime_payload
    session=storage.load_session();session['ruleset_binding']={'ruleset_id':ruleset,'ruleset_version':'1','binding_version':1}
    storage._atomic_save_json(storage.SESSION_PATH,wrap_runtime_payload(kind='session',payload=session,saved_at='test',include_integrity=True))
    row=post(client,'I look around.','ruleset-'+ruleset);quiet(row)
    assert row['after']['session']['ruleset_binding']==session['ruleset_binding']


def test_admitted_social_exchange_keeps_existing_time(client):
    row=post(client,'Knowing the road is dangerous, I ask the guard.','fronted')
    assert row['after']['session']['turn_counter']==row['before']['session']['turn_counter']+1
    assert row['log']['resolution']['social']['target_resolved'] is True


def test_successful_narration_dependent_observation_commits_once(client,monkeypatch):
    calls=[]
    def narrate(**kw):
        calls.append(kw['session']['turn_counter'])
        return {'player_facing_text':'Rain falls over the gate district.','tags':[]}
    monkeypatch.setattr(api,'_build_gpt_narration_from_authoritative_state',narrate)
    row=post(client,'I look around.','successful-observation')
    assert row['after']['session']['turn_counter']==row['before']['session']['turn_counter']+1
    assert len(calls)==1
    duplicate=post(client,'I look around.','successful-observation')
    assert duplicate['body']==row['body']
    assert duplicate['after']==row['after']
    assert len(calls)==1


@pytest.mark.parametrize('mode',['disabled','failure','timeout'])
def test_committed_visible_feature_inspection_distinguishes_missing_narration(client,monkeypatch,mode):
    if mode!='disabled':
        def fail(**kw):
            raise TimeoutError('controlled timeout') if mode=='timeout' else RuntimeError('controlled failure')
        monkeypatch.setattr(api,'_build_gpt_narration_from_authoritative_state',fail)
    row=post(client,'I inspect the rain barrel.','barrel-'+mode)
    assert row['after']['session']['turn_counter']==row['before']['session']['turn_counter']+1
    assert 'i_inspect_the_rain_barrel' in row['after']['session']['scene_runtime']['frontier_gate']['searched_targets']
    # The existing referenced-surface publication owner can deliver this exact
    # authored visible fact even when optional narration is unavailable.
    assert visible(row) == 'A tavern runner trades hot stew and rumors near the rain barrel.'
    assert 'not completed' not in visible(row)
    assert row['log']['resolution']['metadata']['narration_failure']['timing']=='after_resolution'


@pytest.mark.parametrize('disclosure',[True,False])
def test_disclosure_composition_authority_does_not_depend_on_spent_turn(monkeypatch,disclosure):
    from game.response_policy_enforcement import enforce_scene_momentum
    monkeypatch.setattr('game.gm._scene_momentum_due',lambda *args:False)
    def forbidden(*args,**kwargs):
        raise AssertionError('No synthetic scene beat is due')
    monkeypatch.setattr('game.diegetic_fallback_narration.render_scene_momentum_diegetic_append',forbidden)
    fact='The patrol took the northwest track.'
    gm={'player_facing_text':fact if disclosure else 'Rain falls.','tags':[],'metadata':{}}
    before=copy.deepcopy(gm)
    resolution={'kind':'discover_clue','success':True,'clue_text':fact} if disclosure else {'kind':'observe','success':True}
    result=enforce_scene_momentum(gm,session={},scene_envelope={'scene':{'id':'gate'}},resolution=resolution)
    assert gm==before
    assert result['player_facing_text']==gm['player_facing_text']
    if disclosure:
        assert result['metadata']['emission_debug']['scene_momentum_composition']['appended'] is False
        assert 'scene_momentum:new_information' in result['tags']
    else:
        assert result==gm
