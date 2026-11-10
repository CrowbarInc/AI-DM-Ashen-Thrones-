"""Complete-payload HTTP assertions for the server/player trust boundary."""
import copy
import json
import pytest
from fastapi.testclient import TestClient
from game import api, storage
from game.player_http_projection import project_player_response, project_player_state
from tests.test_pr_play_66_publication import setup as setup_publication

HIDDEN_PATHS = [
    ('session','gm_notes'),('world','gm_only'),('scene','scene','discoverable_clues'),
    ('scene','scene','gm_notes'),('scene','scene','private_notes'),
    ('campaign','objectives'),('world','npcs'),('world','locations'),('world','triggers'),
    ('session','resolver_metadata'),('gm_output','prompt'),('gm_output','validation'),
    ('resolution','state_changes'),('session','future_field'),('optional_metadata',),
    ('scene','scene','future_field'),('journal','future_field'),('character','future_field'),
    ('ui','future_field'),('world','public_looking_field'),
]
def put(data,path,value):
    node=data
    for key in path[:-1]: node=node.setdefault(key,{})
    node[path[-1]]=value

@pytest.mark.parametrize('path',HIDDEN_PATHS)
def test_unknown_and_internal_sources_fail_closed(path):
    data={'gm_output':{'player_facing_text':'Visible narration'},'character':{'name':'Galinor'}}
    put(data,path,{'innocuous':'SECRET_SENTINEL_ALPHA'})
    before=copy.deepcopy(data)
    result=project_player_response(data)
    assert 'SECRET_SENTINEL_ALPHA' not in json.dumps(result)
    assert result['gm_output']['player_facing_text']=='Visible narration'
    assert data==before

@pytest.mark.parametrize('path',[
    ('character','hp'),('scene','scene','summary'),('session','active_scene_id'),
    ('ui','affordances'),('journal','known_facts'),('gm_output','player_facing_text'),
])
def test_object_under_public_scalar_never_stringified(path):
    data={};put(data,path,{'text':'SECRET_SENTINEL_ALPHA'})
    assert 'SECRET_SENTINEL_ALPHA' not in json.dumps(project_player_response(data))

@pytest.mark.parametrize('enabled',[False,True])
def test_real_http_state_and_gameplay_preserve_secrets(tmp_path,monkeypatch,enabled):
    setup_publication(tmp_path,monkeypatch)
    from game import quarantined_investigation_narration as q
    if not enabled: monkeypatch.setenv(q.GATE_ENV,'0')
    monkeypatch.setattr(storage,'SNAPSHOTS_DIR',tmp_path/'snapshots')
    scene_before=storage.scene_path('old_milestone').read_bytes()
    with TestClient(api.app,raise_server_exceptions=False) as client:
        for path,payload in [('/api/state',None),('/api/chat',{'text':'I examine the weathered milestone.'}),('/api/state',None),('/api/response_mode',{'mode':'vivid'})]:
            response=client.get(path) if payload is None else client.post(path,json=payload)
            assert response.status_code==200,response.text
            assert 'CANARY_' not in response.text
            assert 'discoverable_clues' not in response.text
    assert storage.load_session()['gm_notes']==['CANARY_GM_NOTE']
    assert storage.load_world()['gm_only']['motivation']=='CANARY_NPC_MOTIVE'
    assert storage.scene_path('old_milestone').read_bytes()==scene_before

@pytest.mark.parametrize('fault',['initialization','resolution','validation','malformed_response','nested_error','serialization'])
def test_http_failures_never_publish_internal_details(tmp_path,monkeypatch,fault):
    setup_publication(tmp_path,monkeypatch)
    def fail(*a,**k): raise RuntimeError('SECRET_SENTINEL_ERROR')
    if fault=='initialization': monkeypatch.setattr(api,'load_campaign',fail)
    if fault=='resolution': monkeypatch.setattr(api,'_resolve_engine_noncombat_seam',fail)
    if fault=='malformed_response': monkeypatch.setattr(api,'chat',lambda *a,**k:{'status':{'secret':'SECRET_SENTINEL_ERROR'}})
    if fault=='nested_error': monkeypatch.setattr(api,'chat',lambda *a,**k:{'ok':False,'error':{'text':'SECRET_SENTINEL_ERROR'},'world':storage.load_world()})
    if fault=='serialization':
        from starlette.responses import JSONResponse
        original=JSONResponse.render
        def render(self,content):
            if isinstance(content,dict) and 'gm_output' in content: raise TypeError('SECRET_SENTINEL_ERROR')
            return original(self,content)
        monkeypatch.setattr(JSONResponse,'render',render)
    with TestClient(api.app,raise_server_exceptions=False) as client:
        response=client.post('/api/chat',json={'text':{'secret':'SECRET_SENTINEL_ERROR'}} if fault=='validation' else {'text':'I examine the weathered milestone.'})
    assert 'SECRET_SENTINEL' not in response.text and 'CANARY_' not in response.text
    if fault in {'initialization','resolution','serialization'}: assert response.status_code==500
    if fault=='validation': assert response.status_code==422

@pytest.mark.parametrize('name',['public_fields','known_discovery','inventory','affordances','visited_scenes','pure_projection','repeat','isolation'])
def test_frontend_and_authority_contract(tmp_path,monkeypatch,name):
    setup_publication(tmp_path,monkeypatch)
    state=api.compose_state(); before=copy.deepcopy(state)
    projected=project_player_state(state)
    assert state==before
    assert projected['character']['name']==state['character']['name']
    assert projected['character']['inventory']==[{'id':'spellbook','name':'Spellbook','quantity':1,'usable':False}]
    assert projected['ui']['scene_ids']==['old_milestone']
    assert projected['scene']['scene']['id']=='old_milestone'
    assert 'CANARY_' not in json.dumps(projected)
    assert project_player_state(projected)==projected
    projected['character']['inventory'][0]['name']='changed'
    assert storage.load_character()['inventory'][0]['name']=='Spellbook'
    with TestClient(api.app) as client:
        first=client.post('/api/chat',json={'text':'I examine the weathered milestone.'})
        assert first.status_code==200
        from tests.test_pr_play_52_quarantined_integration import PRINT_CLUE
        assert PRINT_CLUE in first.json()['gm_output']['player_facing_text']
        second=client.post('/api/chat',json={'text':'I examine the weathered milestone again.'})
        assert second.status_code==200 and 'CANARY_' not in second.text
        visible=client.get('/api/state').json()['public_state']
        assert PRINT_CLUE in visible['journal']['discovered_clues']
        for mode in ['author','debug']:
            denied=client.get('/api/state?ui_mode='+mode)
            assert denied.status_code==403 and 'CANARY_' not in denied.text
