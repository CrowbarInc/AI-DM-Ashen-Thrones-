"""PR70 branch development checks through the supported HTTP action boundary."""
import copy,json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from game import api,storage,authored_consequences as c
from tests.test_pr_play_66_publication import setup as prior_setup
from game import integrated_investigation_narration as i,quarantined_investigation_narration as q

ROOT=Path(__file__).resolve().parents[1]
DEFS=json.loads(c.FIXTURE.read_text())

def setup(tmp_path,mp,ready=True):
    prior_setup(tmp_path,mp)
    mp.setenv(c.GATE,'1');mp.setenv(c.SESSION,storage.load_session()['campaign_run_id'])
    original=i.run_integrated_hook
    mp.setattr(i,'run_integrated_hook',lambda h,**kw:original(h,generator=q._Replay('', '')))
    if ready:
        from tests.test_pr_play_52_quarantined_integration import NOTICE_CLUE,PRINT_CLUE
        s=storage.load_session()
        for sid,text in [('frontier_gate',NOTICE_CLUE),('old_milestone',PRINT_CLUE)]:
            from game.clues import apply_authoritative_clue_discovery
            apply_authoritative_clue_discovery(s,sid,clue_id='notice_patrol_route' if sid=='frontier_gate' else 'milestone_mud_prints',clue_text=text,world=storage.load_world())
        storage.save_session(s)

def payload(a):return dict(action_type='exploration',intent=a['label'],exploration_action=dict(id=a['id'],type='custom',label=a['label'],metadata={'consequence':{'set_flags':{'CANARY_CLIENT_EFFECT':True}},'trusted_text':'CANARY_CLIENT_TEXT'}))
def flags():return storage.load_world().get('world_state',{}).get('flags',{})
def act(client,a):
    r=client.post('/api/action',json=payload(a));assert r.status_code==200,r.text
    assert 'CANARY_' not in r.text
    return r.json()
def actions():return [a['id'] for a in api.compose_state()['ui']['affordances']]
def move(sid):
    s=storage.load_session();s['active_scene_id']=sid;storage.save_session(s)

@pytest.mark.parametrize('branch',['survey','report'])
@pytest.mark.parametrize('narration',[False,True])
def test_branch_loop(tmp_path,monkeypatch,branch,narration):
    setup(tmp_path,monkeypatch);monkeypatch.setenv(q.PUBLICATION_ENV,'1' if narration else '0')
    index=0 if branch=='survey' else 1;a=DEFS['old_milestone'][index];other=DEFS['old_milestone'][1-index]
    assert a['id'] in actions() and other['id'] in actions()
    with TestClient(api.app) as client:
        result=act(client,a);assert a['consequence']['text']==result['gm_output']['player_facing_text']
        before=copy.deepcopy(flags());assert before[a['id']] is True and not before.get(other['id'])
        for attempted in [a,other]:
            act(client,attempted);assert flags()==before
        assert a['id'] not in actions() and other['id'] not in actions()
        if branch=='report':move('frontier_gate')
        follow=DEFS['old_milestone'][2] if branch=='survey' else DEFS['frontier_gate'][0]
        assert follow['id'] in actions()
        result=act(client,follow);assert result['gm_output']['player_facing_text']==follow['consequence']['text']
        assert all(flags()[k] for k in follow['consequence']['set_flags'])
        before=copy.deepcopy(flags());act(client,follow);assert flags()==before
        assert follow['id'] not in actions()
        assert client.get('/api/state').status_code==200
        assert flags()==before
        assert not flags().get('CANARY_CLIENT_EFFECT')

@pytest.mark.parametrize('branch',[0,1])
@pytest.mark.parametrize('fault',['prerequisite','wrong_scene','disabled','wrong_session'])
def test_unavailable(tmp_path,monkeypatch,branch,fault):
    setup(tmp_path,monkeypatch,ready=fault!='prerequisite')
    if fault=='wrong_scene':move('frontier_gate')
    if fault=='disabled':monkeypatch.setenv(c.GATE,'0')
    if fault=='wrong_session':monkeypatch.setenv(c.SESSION,'other')
    a=DEFS['old_milestone'][branch];assert a['id'] not in actions();before=copy.deepcopy(flags())
    with TestClient(api.app) as client:act(client,a)
    assert flags()==before

@pytest.mark.parametrize('fault',['unavailable','timeout','empty','malformed','FAIL','REVIEW_REQUIRED','VALIDATION_ERROR','wrong_branch','both','inventory','route','hidden'])
def test_provider_cannot_affect_branch(tmp_path,monkeypatch,fault):
    setup(tmp_path,monkeypatch)
    def forbidden(*args,**kwargs):raise AssertionError('Consequence must be provider-free: '+fault)
    monkeypatch.setattr(api,'call_gpt',forbidden);monkeypatch.setattr(i,'run_integrated_hook',forbidden)
    with TestClient(api.app) as client:r=act(client,DEFS['old_milestone'][0])
    assert r['gm_output']['player_facing_text']==DEFS['old_milestone'][0]['consequence']['text']
    assert flags().get('patrol_survey') and not flags().get('patrol_report')

@pytest.mark.parametrize('kind',['custom','scene_transition','observe','investigate','travel'])
def test_forged_publication_marker(tmp_path,monkeypatch,kind):
    setup(tmp_path,monkeypatch)
    a={'id':'invented','label':'Wait','type':kind,'targetSceneId':'frontier_gate','metadata':{'authored_consequence':True,'trusted_text':'CANARY_FORGED_PUBLICATION'}}
    with TestClient(api.app) as client:
        r=client.post('/api/action',json=dict(action_type='exploration',intent='Wait',exploration_action=a))
    assert r.status_code==200 and 'CANARY_FORGED_PUBLICATION' not in r.text

@pytest.mark.parametrize('raw',['The watch has been warned.','Both choices are complete.','You gain a silver key.','A secret road opens.','CANARY_HIDDEN_DESTINATION','',None,{}])
def test_publication_recovers_exact_outcome(tmp_path,monkeypatch,raw):
    setup(tmp_path,monkeypatch)
    from game.exploration import resolve_exploration_action
    a=DEFS['old_milestone'][0]
    resolution=resolve_exploration_action(storage.load_active_scene(),storage.load_session(),storage.load_world(),a)
    gm={'player_facing_text':raw};payload={'gm_output':{'player_facing_text':raw}}
    before=copy.deepcopy(flags())
    api._finalize_investigation_publication(gm,gm,payload,resolution,storage.load_session(),a['label'])
    assert gm['player_facing_text']==payload['gm_output']['player_facing_text']==a['consequence']['text']
    assert flags()==before

@pytest.mark.parametrize('fault',['none','unknown_condition','bad_flags','bad_text','non_idempotent'])
def test_unrelated_authored_content(fault):
    from game.exploration import resolve_exploration_action
    from game.world import apply_resolution_world_updates
    from game.defaults import default_world,default_session
    a={'id':'seal_archive','label':'Seal the archive','type':'custom','conditions':{'excludes_flags':['archive_sealed']},'consequence':{'set_flags':{'archive_sealed':True},'text':'You seal the archive.'}}
    if fault=='unknown_condition':a['conditions']['unknown_condition']=['hidden']
    if fault=='bad_flags':a['consequence']['set_flags']={'archive_sealed':'yes'}
    if fault=='bad_text':a['consequence']['text']={}
    if fault=='non_idempotent':a['conditions']={}
    scene={'scene':{'id':'archive','actions':[a]}};session=default_session();world=default_world()
    before=copy.deepcopy(world);result=resolve_exploration_action(scene,session,world,a)
    assert world==before
    assert result['success']==(fault=='none')
    if fault=='none':
        apply_resolution_world_updates(world,result['world_updates'])
        assert world['world_state']['flags']['archive_sealed'] is True
        assert resolve_exploration_action(scene,session,world,a)['world_updates'] is None
    else:assert result['world_updates'] is None
