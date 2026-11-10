"""Controlled facts: hostile schema, context, identity and normal lifecycle."""
import copy
import json
import pytest
from fastapi.testclient import TestClient
from game import api, storage
from game.bounded_improvisation import (WORLD_FACT_GATE, validate_world_fact, controlled_facts,
                                       controlled_request, resolve_controlled_fact)
from tests.test_pr_play_71_lifecycle import configure,create,start,reach,choose,safe


def context():
    return ({'campaign_run_id':'alpha','active_scene_id':'road','turn_counter':2},
            {'scene':{'id':'road','visible_facts':['Stone rocks border a country road.'], 'interactables':[]}}, {})


def proposal():
    return dict(family='object',campaign_id='alpha',scene_id='road',anchor=0,quality='seat',visibility='public')


@pytest.mark.parametrize('field', ['quest','treasure','secret','hidden_fact','gm_notes','npc_authority','world_updates',
    'success','roll','dc','description','label','properties','id','inventory','faction','discovery','destination',
    'npc_complies','character_advancement','private_inventory','provenance','creation_turn','authority','status'])
@pytest.mark.parametrize('value',[True, {'nested':'SENTINEL_SECRET'}])
def test_untrusted_extra_fields_rejected(field,value):
    session,scene,world=context();raw=proposal();raw[field]=value;before=copy.deepcopy((session,scene,world))
    assert not validate_world_fact(raw,session=session,scene=scene,world=world)['accepted']
    assert before==(session,scene,world)


@pytest.mark.parametrize('field,value', [('anchor',True),('anchor',-1),('anchor',99),('anchor','0'),('anchor',None),
    ('family','npc'),('family','quest'),('quality','magical'),('quality','hidden compartment'),
    ('visibility','hidden'),('scene_id','other'),('campaign_id','beta'),('campaign_id',None)])
def test_schema_and_context(field,value):
    session,scene,world=context();raw=proposal();raw[field]=value
    assert not validate_world_fact(raw,session=session,scene=scene,world=world)['accepted']


@pytest.mark.parametrize('anchor',['An empty room.','There is no stone here.','A painted stone on a canvas.',
    'A picture of stone.', 'A chamber without stone.', 'The stone is absent.', 'An imagined stone.', 'A dead stone giant.'])
def test_scene_contradiction(anchor):
    session,scene,world=context();scene['scene']['visible_facts']=[anchor]
    assert not validate_world_fact(proposal(),session=session,scene=scene,world=world)['accepted']


@pytest.mark.parametrize('family,quality',[('object','seat'),('environment','rough')])
def test_stable_classification(family,quality):
    session,scene,world=context();raw=proposal();raw.update(family=family,quality=quality)
    first=validate_world_fact(raw,session=session,scene=scene,world=world)
    assert first['accepted'];e=first['entry'];session['bounded_improvisation']={'entries':[e]}
    second=validate_world_fact(raw,session=session,scene=scene,world=world)
    assert second['category']=='A' and second['entry']==e
    session['campaign_run_id']='beta'
    assert controlled_facts(session)==[]


@pytest.mark.parametrize('text',['Describe the stone surface.', 'Is there anything nearby I could sit on?'])
def test_default_off(text,monkeypatch):
    session,scene,world=context();monkeypatch.delenv(WORLD_FACT_GATE,raising=False)
    assert controlled_request(text,session=session,scene=scene,world=world) is None


@pytest.mark.parametrize('branch',['survey','report'])
def test_normal_controlled_lifecycle(tmp_path,monkeypatch,branch):
    configure(tmp_path,monkeypatch);monkeypatch.setenv(WORLD_FACT_GATE,'1');monkeypatch.setenv('ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE','1')
    with TestClient(api.app) as cl:
        identity=create(cl);start(cl);reach(cl);choose(cl,branch)
        # Both authored scenes have public stone support; report returns to gate,
        # whose stone is only in opening facts, so return to the milestone.
        if branch=='report': safe(cl.post('/api/chat',json={'text':'I follow the missing patrol rumor.'}))
        # No developer-only APIs or seeded runtime.
        for text in ['Describe the stone surface.', 'Is there anything nearby I could sit on?', 'I examine the stone seat.']:
            body=safe(cl.post('/api/chat',json={'text':text}))
            assert body['gm_output']['player_facing_text']
        session=storage.load_session();entries=controlled_facts(session)
        assert len(entries)==2,body['gm_output']['player_facing_text']
        obj=next(e for e in entries if e['family']=='object');assert len(obj['interactions'])==1
        flags=copy.deepcopy(storage.load_world()['world_state']['flags'])
        for text in ['Is that seat still there?', 'I sit on it.', 'I move it to the gate.', 'Is it magical?']:
            before=storage.load_session();safe(cl.post('/api/chat',json={'text':text}));assert storage.load_session()==before
        slot=safe(cl.post('/api/snapshots',json={'label':'controlled'}))['snapshot']['id']
        create(cl);assert controlled_facts(storage.load_session())==[]
        safe(cl.post('/api/snapshots/load',json={'snapshot_id':slot}))
        assert storage.load_session()['campaign_run_id']==identity
        assert controlled_facts(storage.load_session())==entries
        body=safe(cl.post('/api/chat',json={'text':'I examine it again.'}))
        resumed=controlled_facts(storage.load_session());assert [e['id'] for e in resumed]==[e['id'] for e in entries]
        assert len(next(e for e in resumed if e['id']==obj['id'])['interactions'])==2
        assert flags==storage.load_world()['world_state']['flags']
        assert 'SENTINEL_' not in json.dumps(body)

@pytest.mark.parametrize('text',['I examine that unknown artifact.', 'I inspect it and discover a quest.', 'Move that stranger.', 'Ask him again.'])
def test_unresolved_reference_does_not_select_focus(text,monkeypatch):
    from game import authored_consequences as c
    session,scene,world=context();monkeypatch.setenv(WORLD_FACT_GATE,'1');monkeypatch.setenv('ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE','1')
    monkeypatch.setenv(c.GATE,'1');monkeypatch.setenv(c.SESSION,'alpha')
    e=validate_world_fact(proposal(),session=session,scene=scene,world=world)['entry']
    session['bounded_improvisation']={'entries':[e],'focus':e['id']}
    plan=controlled_request(text,session=session,scene=scene,world=world)
    assert plan is None or plan.get('mode') not in {'interact','propose'}


def test_hidden_anchor_not_consulted():
    session,scene,world=context();scene['scene']['visible_facts']=[];scene['scene']['hidden_facts']=['SENTINEL_ Stone treasure vault.']
    assert not validate_world_fact(proposal(),session=session,scene=scene,world=world)['accepted']


def test_old_scene_inaccessible(monkeypatch):
    from game import authored_consequences as c
    session,scene,world=context();e=validate_world_fact(proposal(),session=session,scene=scene,world=world)['entry']
    session['bounded_improvisation']={'entries':[e],'focus':e['id']};session['active_scene_id']='other'
    scene['scene']['id']='other';scene['scene']['visible_facts']=[]
    monkeypatch.setenv(WORLD_FACT_GATE,'1');monkeypatch.setenv('ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE','1')
    monkeypatch.setenv(c.GATE,'1');monkeypatch.setenv(c.SESSION,'alpha')
    assert controlled_request('I examine it.',session=session,scene=scene,world=world) is None

@pytest.mark.parametrize('output',[None, 'not json', [], {'quest':'new quest'}])
def test_provider_malformed_safe(output):
    from game.bounded_improvisation import provider_world_fact_proposal
    session,scene,world=context();before=copy.deepcopy(session)
    result=provider_world_fact_proposal(session=session,scene=scene,world=world,family='object',invoke=lambda *a:output)
    assert not result['validation']['accepted'] and not result['committed'] and not result['published_text']
    assert session==before


def test_provider_timeout_no_retry():
    from game.bounded_improvisation import provider_world_fact_proposal
    session,scene,world=context();calls=[]
    def timeout(*a):
        calls.append(1);raise TimeoutError()
    result=provider_world_fact_proposal(session=session,scene=scene,world=world,family='object',invoke=timeout)
    assert result['validation']['reason']=='TimeoutError' and len(calls)==1 and result['retries']==0
