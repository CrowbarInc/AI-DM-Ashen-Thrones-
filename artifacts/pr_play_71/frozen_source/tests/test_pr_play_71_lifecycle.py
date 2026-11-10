"""Normal HTTP lifecycle using copied bootstrap content, never prestarted runtime."""
import copy,json,shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from game import api,storage,authored_consequences as c
from tests.helpers.turn_pipeline_http_fixtures import _patch_storage
from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
ROOT=Path(__file__).resolve().parents[1]
DEFS=json.loads(c.FIXTURE.read_text())

def configure(tmp_path,mp):
    _patch_storage(tmp_path,mp)
    mp.setattr(storage,'SNAPSHOTS_DIR',tmp_path/'snapshots')
    for p in (ROOT/'data/scenes').glob('*.json'):shutil.copy2(p,storage.SCENES_DIR/p.name)
    for name in ['campaign','character','world','conditions']:
        shutil.copy2(ROOT/'data'/f'{name}.json',storage.DATA_DIR/f'{name}.json')
    mp.setenv('ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT','1')
    mp.setenv('ASHEN_DISABLE_PROVIDER_CALLS','1')
    mp.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','1')
    mp.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION','1')
    mp.setenv(c.GATE,'1');mp.setenv(c.NEW_CAMPAIGNS,'1')
    mp.delenv(c.SESSION,raising=False)
    mp.setattr(api,'call_gpt',lambda *a,**k:copy.deepcopy(RICH_OPENING_GPT_RESPONSE))
    mp.setattr(api,'log_upstream_api_preflight_at_startup',lambda:None)

def safe(response):
    assert response.status_code==200,response.text
    assert 'CANARY_' not in response.text and c.ENROLLMENT not in response.text
    return response.json()

def create(client):
    r=safe(client.post('/api/new_campaign'))
    assert r['campaign_run_id'] and r['session_id']
    assert not storage.load_session()['campaign_started']
    return r['campaign_run_id']

def start(client):
    b=safe(client.post('/api/start_campaign'))
    assert b['ok'] and b['session']['campaign_started']
    assert b['session']['active_scene_id']=='frontier_gate'
    assert b['gm_output']['player_facing_text'] and b['ui']['affordances']
    return b

def chat(client,text):return safe(client.post('/api/chat',json={'text':text}))
def byid(aid):return next(a for arr in DEFS.values() for a in arr if a['id']==aid)
def act(client,aid):
    a=byid(aid)
    return safe(client.post('/api/action',json={'action_type':'exploration','intent':a['label'],'exploration_action':{'id':aid,'type':'custom','label':a['label']}}))
def flags():return storage.load_world().get('world_state',{}).get('flags',{})
def reach(client):
    notice=chat(client,'I examine the notice board.')
    from tests.test_pr_play_52_quarantined_integration import NOTICE_CLUE, PRINT_CLUE
    assert NOTICE_CLUE in notice['gm_output']['player_facing_text']
    chat(client,'I follow the missing patrol rumor.')
    b=chat(client,'I examine the weathered milestone.')
    assert PRINT_CLUE in b['gm_output']['player_facing_text']
    assert storage.load_session()['active_scene_id']=='old_milestone'
    state=safe(client.get('/api/state'))
    state=state.get('public_state',state)
    assert {'patrol_survey','patrol_report'} <= {a['id'] for a in state['ui']['affordances']}
    return b
def choose(client,branch):
    a='patrol_'+branch
    b=act(client,a)
    assert b['gm_output']['player_facing_text']==byid(a)['consequence']['text']
    assert flags()[a] and not flags().get('patrol_'+('report' if branch=='survey' else 'survey'))
    if branch=='report':chat(client,'I return to Cinderwatch Gate.')
    follow='patrol_record_survey' if branch=='survey' else 'patrol_warn_watch'
    b=act(client,follow)
    assert b['gm_output']['player_facing_text']==byid(follow)['consequence']['text']
    assert all(flags().get(f) for f in byid(follow)['consequence']['set_flags'])
    return follow

@pytest.mark.parametrize('branch',['survey','report'])
def test_normal_lifecycle(tmp_path,monkeypatch,branch):
    configure(tmp_path,monkeypatch)
    with TestClient(api.app) as cl:
        identity=create(cl);start(cl);reach(cl);follow=choose(cl,branch)
        before=copy.deepcopy(flags());session=storage.load_session();character=storage.load_character()
        snap=safe(cl.post('/api/snapshots',json={'label':branch}))['snapshot']['id']
        assert create(cl)!=identity
        safe(cl.post('/api/snapshots/load',json={'snapshot_id':snap}))
        assert storage.load_session()['campaign_run_id']==identity
        assert storage.load_session()['active_scene_id']==session['active_scene_id']
        assert storage.load_character()==character and flags()==before
        act(cl,follow);act(cl,'patrol_'+branch)
        act(cl,'patrol_'+('report' if branch=='survey' else 'survey'))
        assert flags()==before
        chat(cl,'I examine the mud prints.' if branch=='survey' else 'I examine the notice board.')
        assert flags()==before

@pytest.mark.parametrize('fault',['off','no_optin','other_identity'])
def test_enrollment_isolation(tmp_path,monkeypatch,fault):
    configure(tmp_path,monkeypatch)
    if fault=='no_optin':monkeypatch.delenv(c.NEW_CAMPAIGNS)
    with TestClient(api.app) as cl:
        create(cl)
        if fault=='off':monkeypatch.setenv(c.GATE,'0')
        s=storage.load_session()
        if fault=='other_identity':s[c.ENROLLMENT]='another-campaign'
        scene={'scene':{'id':'old_milestone','actions':[]}}
        assert c.overlay(scene,s)==scene

def test_duplicate_start(tmp_path,monkeypatch):
    configure(tmp_path,monkeypatch)
    with TestClient(api.app) as cl:
        identity=create(cl);start(cl);before=storage.load_session()
        r=cl.post('/api/start_campaign');assert r.status_code==409
        assert storage.load_session()['campaign_run_id']==identity
        assert storage.load_session()['turn_counter']==before['turn_counter']
