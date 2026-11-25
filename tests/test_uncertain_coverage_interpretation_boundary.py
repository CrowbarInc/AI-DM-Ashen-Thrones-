"""Read-only interpretation must not remove whole-request execution authority."""
import copy
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from game import api, storage, conversational_orchestration as co, live_chat_interpretation as live
from game.integrated_play import _LANES
from game.provider_budget import snapshot
from tests.pr_play_79df3_harness import seed_gate, CANARIES
from tests.test_ordinary_semantic_admission import state

A4 = 'I keep my hands off it and only ask what I could cast if trouble starts.'
B1 = 'I turn to the officer keeping this gate and ask what became of the missing soldiers.'

def record(npc=False, target='guard_captain'):
    return {'interpretation_status': 'INTERPRETED', 'communication_mode': 'IN_WORLD_ACTION' if npc else 'OTHER',
            'communication': {'recipient': 'NPC' if npc else 'GM', 'purpose': 'QUESTION',
                              'subject': 'missing soldiers' if npc else 'possible spells if trouble starts', 'evidence_refs': []},
            'action_components': [{'operation_class':'ASK','target_ref':target,'description':'Ask about missing soldiers'}] if npc else [],
            'player_intent': {'summary':'ask a question'}, 'incidental_context':['orientation' if npc else 'no contact; hypothetical condition']}

@pytest.fixture
def setup(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch); _LANES.clear()
    for key in ('ASHEN_DISABLE_PROVIDER_CALLS','ASHEN_DISABLE_LIVE_INTERPRETATION','ASHEN_DISABLE_EXPRESSION_GENERATION','ASHEN_DISABLE_PROVIDER_RETRIES'):
        monkeypatch.setenv(key,'1')
    monkeypatch.delenv('ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION',raising=False)
    return tmp_path

def assert_integrity(before, after):
    for k in ('character','world','scene','combat'): assert before[k] == after[k], k
    for k in ('turn_counter','clocks','scene_state','active_scene_id','clue_knowledge','last_publication'):
        assert before['session'].get(k)==after['session'].get(k),k

def evidence(name, data):
    out=os.environ.get('ASHEN_UNCERTAIN_EVIDENCE')
    if out:
        p=Path(out);p.mkdir(parents=True,exist_ok=True)
        (p/(name+'.json')).write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')

@pytest.mark.parametrize('text',[A4,B1],ids=['A4','B1'])
@pytest.mark.parametrize('source',['scripted','stored','disabled'])
def test_exact_boundary(setup,monkeypatch,text,source):
    npc=text==B1; calls=[]; proposal=record(npc)
    def interpret(**kw):
        calls.append(copy.deepcopy(kw))
        # An interpreter can scribble on its inputs without touching host state.
        kw['character']['inventory']=[];kw['session']['turn_counter']=999
        return {'status':'accepted','reason':'eligible_for_bridge','record':copy.deepcopy(proposal)}
    if source=='scripted': monkeypatch.setattr(api,'interpret_production_turn',interpret)
    if source=='stored': monkeypatch.setattr(api,'_stored_interpretation_for_player_text',lambda *a:copy.deepcopy(proposal))
    def forbidden(*a,**kw): raise AssertionError('uncertain request escaped to execution/fallback')
    monkeypatch.setattr(api,'deterministic_conversational_decision',forbidden)
    monkeypatch.setattr(api,'normalized_action_from_interpretation',forbidden)
    before=state(); providers=len(snapshot()['records'])
    with TestClient(api.app) as c:
        payload={'text':text,'client_request_id':'exact'}
        first=c.post('/api/chat?ui_mode=player',json=payload)
        replay=c.post('/api/chat?ui_mode=player',json=payload)
    after=state(); assert first.status_code==200;assert first.json()==replay.json()
    assert_integrity(before,after);assert len(snapshot()['records'])==providers
    d=storage.load_log()[-1]['resolution']['metadata']['conversational_decision']
    coverage=d['authorization']['coverage'];visible=first.json()['gm_output']['player_facing_text']
    assert coverage==co.actionable_coverage(text,scene=before['scene'])
    assert coverage['classification']=='UNCERTAIN'; assert d['primary_intention']==text
    assert d['authorization']['execution_withheld'] and not d['authorization']['mutation_eligibility']
    assert all(canary not in visible for canary in CANARIES)
    if source=='scripted':
        assert len(calls)==1 and calls[0]['player_text']==text
        assert calls[0]['coverage_restriction']['coverage']==coverage
    if source!='disabled':
        assert 'Which single action' not in visible
        if not npc:
            assert 'hypothetical' in visible and 'hands off' in visible
            assert 'prepared' in visible and 'not a complete list' in visible
            from game.carried_object_grounding import prepared_spell_rows
            assert all(r['name'] in visible for r in prepared_spell_rows(before['character']))
        else: assert 'officer' in visible.lower() or 'person' in visible.lower()
    evidence(('B1' if npc else 'A4')+'_'+source,{'request':text,'calls':calls,'coverage':coverage,'decision':d,'response':first.json(),'before':before,'after':after,'provider_calls':0,'duplicate_equal':first.json()==replay.json()})

@pytest.mark.parametrize('failure',['unavailable','timeout','budget','invalid_json','invalid_schema','context_leak','missing_context','bridge_rejected','narration_failed'])
@pytest.mark.parametrize('text',[A4,B1],ids=['A4','B1'])
def test_failure_cannot_fall_through(setup,monkeypatch,text,failure):
    outcome={'status':'blocked','reason':failure,'record':record(text==B1),'player_facing_text':'Unsupported fabricated consequence'}
    monkeypatch.setattr(api,'interpret_production_turn',lambda **kw:copy.deepcopy(outcome))
    def forbidden(*a,**kw): raise AssertionError('fallback or bridge reached')
    monkeypatch.setattr(api,'deterministic_conversational_decision',forbidden)
    monkeypatch.setattr(api,'normalized_action_from_interpretation',forbidden)
    before=state()
    with TestClient(api.app) as c:r=c.post('/api/chat?ui_mode=player',json={'text':text,'client_request_id':failure})
    assert r.status_code==200;assert_integrity(before,state())
    assert 'Unsupported fabricated consequence' not in r.json()['gm_output']['player_facing_text']
    evidence(('B1' if text==B1 else 'A4')+'_'+failure,{'request':text,'outcome':outcome,'response':r.json(),'integrity':True})

@pytest.mark.parametrize('variant',['unique','ambiguous','fabricated','offscene'])
def test_b1_grounding(setup,monkeypatch,variant):
    scene=storage.load_active_scene();world=storage.load_world();session=storage.load_session()
    from game.ordinary_semantic_ownership import _visible_npcs
    people=_visible_npcs(scene,world)
    # Grounding receives real fixture catalogs. Supply a public alias in variations,
    # leaving the exact canonical case above unchanged.
    if variant in {'unique','ambiguous'}:
        for i,n in enumerate(people):
            if i==0 or variant=='ambiguous': n['aliases']=list(n.get('aliases') or [])+['officer keeping this gate']
        monkeypatch.setattr('game.ordinary_semantic_ownership._visible_npcs',lambda *a:copy.deepcopy(people))
    target='invented_officer' if variant=='fabricated' else 'off_scene_officer' if variant=='offscene' else people[0]['id']
    restriction=co.full_request_admission(B1,scene=scene,world=world,session=session)
    d=co.decision_from_uncertain_interpretation(restriction,record(True,target),scene=scene,world=world,session=session)
    assert d.category==co.ConversationalDecisionCategory.CLARIFY
    assert d.authorization['coverage']==restriction.authorization['coverage']
    assert not d.authorization['mutation_eligibility']; assert d.proposed_operation is None
    grounding=d.authorization['addressee_grounding']
    if variant=='unique':
        assert grounding['target_id']==people[0]['id']
        assert grounding['target_resolution'] in {'explicit','contextual'}
    else:
        assert grounding['target_id'] is None
        assert grounding['target_resolution'] in {'ambiguous','unresolved'}
    evidence('grounding_'+variant,{'request':B1,'target':target,'decision':d.to_public_dict()})

COMPOUNDS=[
'I examine the notice board and enter Cinderwatch.',
'I throw my coat onto the ground and enter Cinderwatch.',
'I handle my belongings and enter Cinderwatch.',
'I unlock the gate and then enter Cinderwatch.',
'I enter Cinderwatch or take the northwest road.',
'If trouble starts, I cast Shield.',
'I turn toward the officer and ask about the patrol.',
'I juggle my coat and ask what spells I have prepared.',
'I keep my hands off it and only ask what I could cast if trouble starts and I take the book.',
]
@pytest.mark.parametrize('text',COMPOUNDS)
def test_compound_omission_is_not_permission(setup,monkeypatch,text):
    monkeypatch.setattr(api,'interpret_production_turn',lambda **kw:{'status':'accepted','reason':'eligible_for_bridge','record':record()})
    before=state()
    with TestClient(api.app) as c:r=c.post('/api/chat?ui_mode=player',json={'text':text,'client_request_id':'compound'})
    assert r.status_code==200;assert_integrity(before,state())
    assert 'has these spells prepared' not in r.json()['gm_output']['player_facing_text']

@pytest.mark.parametrize('bad',[None,{}, {'interpretation_status':'INTERPRETED'}, {**record(),'action_components':[{'operation_class':'CAST','target_ref':'shield'}]}, {**record(),'interpretation_status':'NEEDS_CLARIFICATION'}, {**record(),'communication':{**record()['communication'],'evidence_refs':['secret']}}])
def test_malformed_or_executable_record_cannot_answer(setup,bad):
    b=state();restriction=co.full_request_admission(A4,scene=b['scene'],world=b['world'],session=b['session'])
    d=co.decision_from_uncertain_interpretation(restriction,bad,scene=b['scene'],world=b['world'],session=b['session'],character=b['character'])
    assert d.category==co.ConversationalDecisionCategory.CLARIFY
    assert d.authorization['coverage']==restriction.authorization['coverage']
