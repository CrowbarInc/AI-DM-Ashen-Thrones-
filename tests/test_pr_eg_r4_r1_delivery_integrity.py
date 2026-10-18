"""Frozen R4 failure, final delivery authority, history, and wire regressions."""
import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from game import api, storage
from game.conversational_continuity import record_delivered_exchange
from game.immutable_valid_response import (run_preserve_if_valid, restore_accepted_text,
    seal_host_speech, accepted_record)
from tests.test_pr_ef_gm_authority import seed_scene, raw_record
from tests.test_pr_eg_r2c_speech_adoption import resolution, ADVERSARIAL

ROOT=Path(__file__).resolve().parents[1]

def original():
    from tools.qualify_pr_eg_r4_r1 import frozen
    row=frozen()
    evidence=json.loads((ROOT/'artifacts/pr_eg_r4/critical_stop_evidence.json').read_text())
    return row['response']['resolution'],evidence

def test_original_failure_frozen_production_finalization(tmp_path,monkeypatch):
    from tools.qualify_pr_eg_r4_r1 import replay
    row=replay('test_repaired_reproduction.json')
    assert row['gate']['provenance']=='safe_nonresolution'
    assert row['gate']['immutable']
    assert row['gate']['speaker']=='GM'
    assert set(row['final']['metadata']['hard_validation_attempt_1']['reasons']) >= {'wrong_interlocutor','conflicting_target_authorities'}
    assert row['final']['player_facing_text']==row['gate']['text']==row['delivered_history']['delivered_text']
    assert row['delivered_history']['ownership']=='gm'
    assert not row['delivered_history']['authorized_proposition']
    assert 'harbor bell' not in row['final']['player_facing_text']

@pytest.mark.parametrize('candidate',ADVERSARIAL)
def test_adversarial_candidate_never_enters_delivery_or_history(candidate,monkeypatch):
    monkeypatch.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION','1')
    question='What do you personally enjoy about the evening?'
    res=resolution(question)
    session={}
    gm=run_preserve_if_valid(dict(player_facing_text=candidate,metadata={}),regenerate=None,
                            resolution=res,player_text=question,session=session)
    adopted=accepted_record(gm)
    row=record_delivered_exchange(session,player_text=question,delivered_text=gm['player_facing_text'],social=res['social'],adoption=adopted)
    assert candidate not in json.dumps(session)
    assert row['delivered_text']==adopted['text']==gm['player_facing_text']
    assert not gm.get('world_updates')

@pytest.mark.parametrize('field,value',[('text','Keeper Nara promises ten silver.'),('speaker','Keeper Nara'),
    ('speaker_id','keeper_nara'),('addressee','clerk_oren'),('subject','password'),('provenance','provider'),
    ('authorization_source','provider'),('immutable',False)])
def test_contract_metadata_and_text_are_bound(field,value):
    gm=seal_host_speech({},text='Clerk Oren says, "I prefer the morning."',source='host',
        speaker_id='clerk_oren',speaker_name='Clerk Oren',resolution=None,player_text='Do you prefer morning?')
    expected=copy.deepcopy(accepted_record(gm))
    gm['metadata']['accepted_response'][field]=value
    gm['player_facing_text']='Keeper Nara promises ten silver.'
    restore_accepted_text(gm)
    assert gm['player_facing_text']==expected['text']
    assert accepted_record(gm)==expected
    assert gm['metadata']['accepted_response']['integrity_digest']==expected['integrity_digest']

@pytest.mark.parametrize('text',['  Clerk Oren says, "Yes."\n\n','**Clerk Oren** says, "Yes."'])
def test_exact_text_survives_history_json_roundtrip(text):
    gm=seal_host_speech({},text=text,source='host',speaker_id='clerk_oren',speaker_name='Clerk Oren',resolution=None,player_text='Yes?')
    gm['player_facing_text']='Clerk Oren says, "Yes."'
    restore_accepted_text(gm)
    session={}
    row=record_delivered_exchange(session,player_text='Yes?',delivered_text=gm['player_facing_text'],
        social=dict(npc_id='clerk_oren',npc_name='Clerk Oren'),adoption=accepted_record(gm))
    assert row['delivered_text']==text
    assert json.loads(json.dumps(session))==session

def test_history_refuses_divergent_speech():
    gm=seal_host_speech({},text='Clerk Oren says, "Yes."',source='host',speaker_id='clerk_oren',speaker_name='Clerk Oren',resolution=None,player_text='Yes?')
    with pytest.raises(ValueError):
        record_delivered_exchange({},player_text='Yes?',delivered_text='Keeper Nara says, "Yes."',adoption=accepted_record(gm))

def test_commitment_preserves_exact_authorized_speech():
    from game.dialogue_authority import remember_dialogue_commitment
    line='Clerk Oren says, "I do not know.\n'+('I cannot promise that. '*15)+'"'
    session={}
    row=remember_dialogue_commitment(session,social=dict(npc_id='clerk_oren',dialogue_authority=dict(
        npc_id='clerk_oren',knowledge_posture='withheld',subject='reward')),player_text='Promise a reward?',line=line,turn=1)
    assert row['text']==line

def test_snapshot_restores_exact_delivered_contract(tmp_path,monkeypatch):
    seed_scene(tmp_path,monkeypatch)
    monkeypatch.setattr(storage,'SNAPSHOTS_DIR',tmp_path/'snapshots')
    res,evidence=original()
    gm=run_preserve_if_valid(dict(player_facing_text=evidence['exact_rejected_candidate']),regenerate=None,
        resolution=res,player_text=evidence['player'])
    session=storage.load_session()
    record_delivered_exchange(session,player_text=evidence['player'],delivered_text=gm['player_facing_text'],
        social=res['social'],adoption=accepted_record(gm))
    storage.save_session(session)
    expected=copy.deepcopy(storage.load_session()['conversational_context'])
    snapshot=storage.create_snapshot(label='R4-R1 exact delivery')
    session['conversational_context']={};storage.save_session(session)
    assert storage.load_snapshot(snapshot['id'])
    assert storage.load_session()['conversational_context']==expected

def test_structured_action_records_authorized_delivery(tmp_path,monkeypatch):
    from tests.test_turn_pipeline_shared import _seed_runner_dialogue_context, _gm_response
    _seed_runner_dialogue_context(tmp_path,monkeypatch)
    monkeypatch.setattr(api,'call_gpt',lambda *a,**k:_gm_response('The action resolves.'))
    response=TestClient(api.app).post('/api/action',json=dict(action_type='exploration',intent='I investigate the desk.',
        exploration_action=dict(id='inv-desk',label='Investigate the desk',type='investigate',prompt='I investigate the desk.')))
    assert response.status_code==200
    gm=response.json()['gm_output']
    assert storage.load_session()['conversational_context']['delivered_exchanges'][-1]['delivered_text']==gm['player_facing_text']==gm['metadata']['accepted_response']['text']

def test_selected_clue_does_not_license_added_relationship():
    from game.gm_resolution_decision import _decision_authorizes_relation
    decision=dict(proposed_facts=[dict(text='A map indicates patrol locations.',authorized=True,
        provenance='authored_world_fact',authority='world_truth',source_ref='resolution.clue_text')])
    assert _decision_authorizes_relation('A map indicates patrol locations.',decision,'evidential')
    assert not _decision_authorizes_relation('A map indicates patrol locations and proves the gate is unguarded.',decision,'evidential')

def test_legacy_retry_cannot_skip_adoption(tmp_path,monkeypatch):
    seed_scene(tmp_path,monkeypatch)
    rows=json.loads((ROOT/'artifacts/pr_eg_r4_r1/failed_first_live/live_turns.json').read_text())
    failed=rows[-1]
    gm=copy.deepcopy(failed['response']['gm_output'])
    assert not gm.get('metadata',{}).get('accepted_response')
    res=copy.deepcopy(failed['response']['resolution'])
    world=copy.deepcopy(failed['before']['world'])
    final,_=api._finalize_player_facing_for_turn(gm,resolution=res,session=copy.deepcopy(failed['before']['session']),
        scene=storage.load_active_scene(),world=world)
    record=accepted_record(final)
    assert record and record['immutable']
    assert final['player_facing_text']==record['text']
    assert record['provenance']=='safe_nonresolution'

@pytest.mark.parametrize('helper',[
    '_preserve_authoritative_resolution_facts_after_gate','_preserve_accepted_bounded_resolution_after_gate',
    '_preserve_physical_action_resolution_after_gate','preserve_interaction_obligation_after_gate',
    '_preserve_resolution_contract_after_gate'])
def test_post_gate_helpers_cannot_replace_safe_response(helper):
    from game import api_turn_support as support
    import inspect
    res,evidence=original()
    gm=run_preserve_if_valid(dict(player_facing_text=evidence['exact_rejected_candidate']),regenerate=None,
        resolution=res,player_text=evidence['player'])
    method=getattr(support,helper)
    possible=dict(resolution=res,scene={},world={},before_text=evidence['exact_rejected_candidate'],after_text='')
    method(gm,**{k:v for k,v in possible.items() if k in inspect.signature(method).parameters})
    assert gm['player_facing_text']==evidence['accepted_response']['text']

def test_consequential_disclosure_http_and_persistence(tmp_path,monkeypatch):
    seed_scene(tmp_path,monkeypatch)
    world=storage.load_world()
    world['factions']=[]
    next(n for n in world['npcs'] if n['id']=='sergeant_mara')['topics']=[dict(id='watch',text='Guards watch the north gate throughout the night.')]
    storage.save_world(world)
    monkeypatch.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0')
    monkeypatch.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION','1')
    monkeypatch.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
    monkeypatch.setattr('game.live_chat_interpretation.request_interpretation',lambda *a,**k:dict(ok=True,sent=False,text=json.dumps(raw_record('NPC',components=[('ASK','sergeant_mara')]))))
    response=TestClient(api.app).post('/api/chat?ui_mode=player',json=dict(text='I ask Sergeant Mara whether guards watch the north gate throughout the night.',ui_mode='player'))
    assert response.status_code==200
    gm=response.json()['gm_output']; record=gm['metadata']['accepted_response']
    assert 'guards watch the north gate throughout the night.' in gm['player_facing_text'].lower()
    assert gm['player_facing_text']==record['text']
    assert record['speaker_id']=='sergeant_mara'
    saved=storage.load_session()
    assert saved['conversational_context']['delivered_exchanges'][-1]['delivered_text']==record['text']
    storage.save_session(copy.deepcopy(saved))
    assert storage.load_session()['conversational_context']==saved['conversational_context']

def test_original_failure_http(tmp_path,monkeypatch):
    seed_scene(tmp_path,monkeypatch)
    res,evidence=original()
    from tools.qualify_pr_eg_r4 import SCENES
    world=storage.load_world(); world['npcs']=copy.deepcopy(SCENES['B']['npcs']);world['factions']=[]
    storage.save_world(world)
    monkeypatch.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0')
    monkeypatch.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
    monkeypatch.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION','1')
    monkeypatch.setattr('game.live_chat_interpretation.request_interpretation',lambda *a,**k:dict(ok=True,sent=False,text=json.dumps(raw_record('NPC',components=[('ASK','clerk_oren')]))))
    monkeypatch.setattr(api,'_resolve_engine_noncombat_seam',lambda *a,**k:copy.deepcopy(res))
    monkeypatch.setattr(api,'call_gpt',lambda *a,**k:dict(player_facing_text=evidence['exact_rejected_candidate'],tags=[],metadata={}))
    # Freeze the authority/candidate input at the validation seam, retaining
    # real finalization, persistence and HTTP serialization downstream.
    finalize=api._finalize_player_facing_for_turn
    def frozen_validation_input(gm,**kwargs):
        sealed=run_preserve_if_valid(dict(player_facing_text=evidence['exact_rejected_candidate'],metadata={}),
            regenerate=None,resolution=copy.deepcopy(res),player_text=evidence['player'],
            session=kwargs['session'],world=kwargs['world'],scene=kwargs['scene'])
        return finalize(sealed,**{**kwargs,'resolution':copy.deepcopy(res)})
    monkeypatch.setattr(api,'_finalize_player_facing_for_turn',frozen_validation_input)
    response=TestClient(api.app).post('/api/chat?ui_mode=player',json=dict(text='I ask Clerk Oren what the harbor bell is called.',ui_mode='player'))
    assert response.status_code==200
    gm=response.json()['gm_output'];record=gm['metadata']['accepted_response']
    assert record['provenance']=='safe_nonresolution'
    assert gm['player_facing_text']==record['text']==evidence['accepted_response']['text']
    history=storage.load_session()['conversational_context']['delivered_exchanges'][-1]
    assert history['delivered_text']==record['text']
    assert history['ownership']=='gm'
