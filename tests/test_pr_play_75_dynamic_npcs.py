"""Dynamic NPC authority, dialogue and real session persistence development checks."""
import copy, json
import pytest
from fastapi.testclient import TestClient
from game import api, storage, bounded_improvisation as b, expressive_dialogue as e
from game.dialogue_authority import background_history
from tests.test_pr_play_71_lifecycle import configure, create, start, reach, choose, chat, safe


def context():
    return ({'campaign_run_id':'alpha','active_scene_id':'harbor','turn_counter':1},
            {'scene':{'id':'harbor','visible_facts':['Workers and travelers gather by the quay.']}}, {'npcs':[]})


def proposal(session=None,scene=None):
    s,sc,_=context();session=session or s;scene=scene or sc
    return dict(campaign_id=session['campaign_run_id'],scene_id=scene.get('scene',scene)['id'],anchor=b._population_anchor(scene),
                role='traveler',name='Mara',appearance='weathered cloak',demeanor='reserved',visibility='public')


def enable(mp):
    mp.setenv(b.NPC_GATE,'1');mp.setenv(b.WORLD_FACT_GATE,'1');mp.setenv('ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE','1')
    mp.setenv('ASHEN_EXPERIMENTAL_BRANCHING','1');mp.setenv('ASHEN_EXPERIMENTAL_BRANCHING_SESSION','alpha')


@pytest.mark.parametrize('field', ['quest','authority','id','world_updates','secret','knowledge','description','provenance','inventory','social_receipts'])
@pytest.mark.parametrize('value',[True,{'secret':'SENTINEL_PRIVATE'}])
def test_extra_fields_fail_closed(field,value):
    s,sc,w=context();p=proposal();p[field]=value;before=copy.deepcopy((s,sc,w))
    assert not b.validate_npc_proposal(p,session=s,scene=sc,world=w)['accepted'];assert (s,sc,w)==before


@pytest.mark.parametrize('field,value',[('campaign_id','other'),('scene_id','elsewhere'),('anchor',True),('anchor',-1),('anchor',1),('visibility','hidden'),('role','king'),('name','Secret'),('name','Mara hides gold'),('appearance','holds a relic'),('demeanor','loyal forever')])
def test_bad_proposals(field,value):
    s,sc,w=context();p=proposal();p[field]=value
    assert not b.validate_npc_proposal(p,session=s,scene=sc,world=w)['accepted']


@pytest.mark.parametrize('public',['An empty room.','No people gather here.','An abandoned market.','A deserted road.','A stone milestone.'])
def test_population(public):
    s,sc,w=context();sc['scene']['visible_facts']=[public]
    assert not b.validate_npc_proposal(proposal(),session=s,scene=sc,world=w)['accepted']


def test_existing_identity_and_authored_preservation():
    s,sc,w=context();w['npcs']=[dict(id='authored',name='Mara',location='harbor')]
    before=copy.deepcopy(w);assert not b.validate_npc_proposal(proposal(),session=s,scene=sc,world=w)['accepted'];assert w==before
    w['npcs']=[];r=b.validate_npc_proposal(proposal(),session=s,scene=sc,world=w);assert r['accepted']
    s[b.LEDGER_KEY]={'entries':[r['entry']]};p=proposal();p['name']='Jon';p['role']='laborer'
    assert b.validate_npc_proposal(p,session=s,scene=sc,world=w)['entry']==r['entry']
    s['campaign_run_id']='beta';assert b.dynamic_npcs(s)==[]
    assert b.dynamic_npcs(s,'other')==[]


@pytest.mark.parametrize('text',['Ask her again.','Talk to that traveler.','The person I spoke to earlier.'])
def test_missing_reference(text,monkeypatch):
    enable(monkeypatch);s,sc,w=context();before=copy.deepcopy(s)
    plan=b.npc_request(text,session=s,scene=sc,world=w)
    assert plan is None or plan['mode']=='clarify';assert s==before


@pytest.mark.parametrize('raw',[None,[],{},'not json',{'role':'king'}])
def test_provider_malformed(raw):
    s,sc,w=context();before=copy.deepcopy(s)
    r=b.provider_npc_proposal(session=s,scene=sc,world=w,invoke=lambda *a:raw)
    assert not r['validation']['accepted'];assert s==before


def test_provider_timeout():
    s,sc,w=context();calls=[]
    def fail(*a):calls.append(1);raise TimeoutError()
    assert not b.provider_npc_proposal(session=s,scene=sc,world=w,invoke=fail)['validation']['accepted'];assert len(calls)==1


@pytest.mark.parametrize('unsafe',['I grant you a quest and gold.','The secret passage leads north.','I am King Mara.','Workers gather here and I own them.','SENTINEL_PRIVATE','I will send soldiers.','There are no workers by the quay.'])
def test_unsafe_dialogue(unsafe,monkeypatch):
    s,sc,w=context();npc=b.validate_npc_proposal(proposal(),session=s,scene=sc,world=w)['entry']
    monkeypatch.setattr(e,'expression_generation_disabled',lambda:False)
    monkeypatch.setattr(e,'request_expression',lambda c:dict(ok=True,text=unsafe))
    out=e.background_conversation(npc,session=s,scene=sc,player_text='What do you know about this area?')
    assert unsafe not in out;assert not s['last_background_expression']['adopted']
    assert background_history(s,npc['id'])[-1]['text']==sc['scene']['visible_facts'][0]


@pytest.mark.parametrize('branch',['survey','report'])
def test_full_normal_lifecycle(tmp_path,monkeypatch,branch):
    configure(tmp_path,monkeypatch);enable(monkeypatch);monkeypatch.delenv('ASHEN_EXPERIMENTAL_BRANCHING_SESSION',raising=False)
    monkeypatch.setattr(b,'provider_npc_proposal',lambda **kw: b._test_provider(**kw))
    with TestClient(api.app) as cl:
        cid=create(cl);start(cl);reach(cl);choose(cl,branch)
        if branch=='survey':chat(cl,'I return to Cinderwatch Gate.')
        assert storage.load_session()['active_scene_id']=='frontier_gate'
        out=chat(cl,'Introduce an ordinary traveler to speak with.')
        entries=b.dynamic_npcs(storage.load_session());assert len(entries)==1,out['gm_output']['player_facing_text']
        npc=copy.deepcopy(entries[0]);flags=copy.deepcopy(storage.load_world()['world_state']['flags'])
        for text in ['Hello.','Who are you?','What do you know about this area?','What did you mean by that?','Thanks. I will come back later.']:
            out=chat(cl,text);assert 'SENTINEL_' not in json.dumps(out)
            assert b.dynamic_npcs(storage.load_session())[0]['id']==npc['id']
        s=storage.load_session();hist=background_history(s,npc['id']);assert len(hist)==5
        assert b.dynamic_npcs(s)[0]['social_receipts']==['greeted','thanked']
        snap=safe(cl.post('/api/snapshots',json={'label':'npc'}))['snapshot']['id']
        create(cl);assert b.dynamic_npcs(storage.load_session())==[]
        safe(cl.post('/api/snapshots/load',json={'snapshot_id':snap}))
        assert background_history(storage.load_session(),npc['id'])==hist
        out=chat(cl,'Talk to that traveler again.');assert len(b.dynamic_npcs(storage.load_session()))==1
        assert len(background_history(storage.load_session(),npc['id']))==len(hist)+1
        assert npc['name'] in out['gm_output']['player_facing_text']
        assert flags==storage.load_world()['world_state']['flags']
        assert b.dynamic_npcs(storage.load_session())[0]['name']==npc['name']


# A deterministic transport only, not evidence of live provider success.
def _fixture(**kw):
    return b.provider_npc_proposal_original(**kw,invoke=lambda *a:proposal(kw['session'],kw['scene']))
b.provider_npc_proposal_original=b.provider_npc_proposal
b._test_provider=_fixture

@pytest.mark.parametrize('unsafe',['Workers and travelers do not gather by the quay.','Workers and travelers gather by the quay for me.','Workers and travelers gather by the quay if I promise.'])
def test_relation_and_polarity(unsafe,monkeypatch):
    s,sc,w=context();npc=b.validate_npc_proposal(proposal(),session=s,scene=sc,world=w)['entry']
    monkeypatch.setattr(e,'expression_generation_disabled',lambda:False)
    monkeypatch.setattr(e,'request_expression',lambda c:dict(ok=True,text=unsafe))
    assert unsafe not in e.background_conversation(npc,session=s,scene=sc,player_text='What do you know about this area?')
    assert not s['last_background_expression']['adopted']


def test_readonly_and_ambiguity(monkeypatch):
    enable(monkeypatch);s,sc,w=context();npc=b.validate_npc_proposal(proposal(),session=s,scene=sc,world=w)['entry']
    s[b.LEDGER_KEY]={'entries':[npc], 'npc_focus':npc['id']};before=copy.deepcopy(s)
    assert b.npc_request('Is that traveler still here?',session=s,scene=sc,world=w)['mode']=='answer';assert s==before
    duplicate=copy.deepcopy(npc);duplicate['id']='second';s[b.LEDGER_KEY]['entries'].append(duplicate)
    assert b.npc_request('Talk to the traveler.',session=s,scene=sc,world=w)['mode']=='clarify'


def test_memory_bounded_idempotent(monkeypatch):
    from game.dialogue_authority import remember_background_exchange,MAX_PER_NPC
    s,sc,w=context()
    for i in range(30):
        s['turn_counter']=i
        for repeat in range(2):remember_background_exchange(s,npc_id='npc',player_text='Hello.',response='Hello.')
    assert len(background_history(s,'npc'))==MAX_PER_NPC
    assert len(s['conversational_context']['dialogue_commitments'])==MAX_PER_NPC


def test_routine_accessibility_and_no_check(tmp_path,monkeypatch):
    configure(tmp_path,monkeypatch);enable(monkeypatch);monkeypatch.delenv('ASHEN_EXPERIMENTAL_BRANCHING_SESSION',raising=False)
    with TestClient(api.app) as cl:
        create(cl);start(cl);reach(cl)
        chat(cl,'Is there anything nearby I could sit on?')
        before=copy.deepcopy(storage.load_world());out=chat(cl,'I sit on the stone seat.')
        assert 'You sit' in out['gm_output']['player_facing_text'];assert before==storage.load_world()
        assert storage.load_session()[b.LEDGER_KEY]['posture']['kind']=='sitting'
        count=len(b.controlled_facts(storage.load_session()));chat(cl,'I sit on it.')
        assert count==len(b.controlled_facts(storage.load_session()))
        chat(cl,'I return to Cinderwatch Gate.');before=storage.load_session()
        plan=b.controlled_request('I sit on it.',session=before,scene=storage.load_scene('frontier_gate'),world=storage.load_world())
        assert plan is None or plan.get('routine')!='sit'


@pytest.mark.parametrize('text',['What do I know about this area?','What have I learned?','What is my inventory?','Remind me what happened.'])
def test_player_information_is_not_npc_speech(text,monkeypatch):
    enable(monkeypatch);s,sc,w=context();npc=b.validate_npc_proposal(proposal(),session=s,scene=sc,world=w)['entry']
    s[b.LEDGER_KEY]={'entries':[npc],'npc_focus':npc['id']};before=copy.deepcopy(s)
    assert b.npc_request(text,session=s,scene=sc,world=w) is None;assert s==before


def test_stale_scene_does_not_grant_npc(monkeypatch):
    enable(monkeypatch);s,sc,w=context();npc=b.validate_npc_proposal(proposal(),session=s,scene=sc,world=w)['entry']
    s[b.LEDGER_KEY]={'entries':[npc],'npc_focus':npc['id']};s['active_scene_id']='elsewhere'
    assert b.npc_request('Who are you?',session=s,scene=sc,world=w) is None
