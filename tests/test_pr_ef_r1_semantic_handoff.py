"""Authority and persistence regressions for semantic control and bridge handoff."""
import copy, json
import pytest
from fastapi.testclient import TestClient
from game.api import app
from game import storage
from tests.test_pr_ef_gm_authority import seed_scene, raw_record
from tests.test_pr_du_player_pipeline import _fake_gm_for_resolution
from game.conversational_orchestration import decision_from_interpretation_record

@pytest.fixture
def campaign(tmp_path, monkeypatch):
 seed_scene(tmp_path, monkeypatch)
 monkeypatch.setenv('ASHEN_DISABLE_PROVIDER_CALLS','0'); monkeypatch.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION','0')
 monkeypatch.setattr('game.api.call_gpt',_fake_gm_for_resolution)
 return TestClient(app)

def wire(monkeypatch, record):
 monkeypatch.setattr('game.live_chat_interpretation.request_interpretation',lambda *a,**kw: {'ok':True,'sent':False,'text':json.dumps(record)})

def test_grounded_movement_survives_legacy_reparse(campaign,monkeypatch):
 before=storage.load_session()
 data=campaign.post('/api/chat',json={'text':'I make for the courtyard gate.'}).json()
 assert data['resolution']['kind']=='scene_transition'
 assert storage.load_session()['active_scene_id']=='waystation_street'
 assert storage.load_session()['turn_counter']==before['turn_counter']+1
 contract=data['resolution']['metadata']['resolution_contract']
 assert contract['operation'] in {'act','follow'}
 assert contract['raw_input']=='I make for the courtyard gate.'
 assert contract['construction']['bridge_processing_input']

@pytest.mark.parametrize('owner,purpose,components',[('GM','EXPLANATION',[]),('SESSION','RULES',[]),('AMBIGUOUS','CLARIFICATION',[]),('MIXED','QUESTION',[('PERCEIVE','courtyard_lantern'),('ASK','sergeant_mara')])])
def test_semantic_ownership_precedes_active_npc(campaign,monkeypatch,owner,purpose,components):
 session=storage.load_session(); session['interaction_context']={'active_interaction_kind':'social','active_interaction_target_id':'sergeant_mara'}; storage.save_session(session)
 before=storage.load_session(); world=storage.load_world()
 wire(monkeypatch,raw_record(owner,purpose,components=components))
 data=campaign.post('/api/chat',json={'text':'Could you interpret the situation for me?'}).json()
 assert storage.load_world()==world
 assert storage.load_session()['turn_counter']==before['turn_counter']
 assert not data['resolution'].get('social')
 assert data['resolution']['metadata']['resolver_invoked'] is False


def test_npc_action_purpose_does_not_change_recipient(campaign,monkeypatch):
 wire(monkeypatch,raw_record('NPC','ACTION',components=[('ASK','sergeant_mara')]))
 data=campaign.post('/api/chat',json={'text':'I address Mara about the road.'}).json()
 record=data['resolution']['metadata']['live_chat_interpretation']['record']
 assert record['communication']['recipient']=='NPC'
 assert data['resolution']['social']['npc_id']=='sergeant_mara'


def test_semantic_confirmation_uses_saved_pending_once(campaign,monkeypatch):
 campaign.post('/api/chat',json={'text':'I inspect the courtyard lantern, then I walk through the courtyard gate.'})
 session=copy.deepcopy(storage.load_session()); storage.save_session(session)
 wire(monkeypatch,raw_record('GM','CONFIRMATION'))
 data=campaign.post('/api/chat',json={'text':'Please carry out the first proposed step.'}).json()
 assert data['resolution']['action_id']=='courtyard_lantern'
 after=storage.load_session(); pending=after['conversational_context']['pending_clarification']
 assert len(pending['steps'])==1 and pending['steps'][0]['operation']=='MOVE'
 assert after['turn_counter']==session['turn_counter']+1
 # Withdraw after disk round-trip; later assent must not execute the canceled move.
 storage.save_session(copy.deepcopy(after)); wire(monkeypatch,raw_record('GM','WITHDRAWAL'))
 campaign.post('/api/chat',json={'text':'Drop the remainder of my request.'})
 world=storage.load_world(); count=storage.load_session()['turn_counter']
 wire(monkeypatch,raw_record('GM','CONFIRMATION'))
 again=campaign.post('/api/chat',json={'text':'Please proceed with it.'}).json()
 assert again['resolution']['kind']=='conversational_clarify'
 assert storage.load_session()['turn_counter']==count
 assert storage.load_world()==world
 assert storage.load_session()['active_scene_id']=='waystation_courtyard'


def test_semantic_confirmation_rejects_stale_scene(campaign,monkeypatch):
 campaign.post('/api/chat',json={'text':'I inspect the courtyard lantern, then I walk through the courtyard gate.'})
 session=storage.load_session(); session['conversational_context']['pending_clarification']['scene_id']='other_scene'; storage.save_session(session)
 wire(monkeypatch,raw_record('GM','CONFIRMATION'))
 data=campaign.post('/api/chat',json={'text':'Please carry it out.'}).json()
 assert data['resolution']['kind']=='conversational_clarify'
 assert storage.load_session()['turn_counter']==session['turn_counter']


def test_semantic_correction_revises_pending_without_execution(campaign,monkeypatch):
 campaign.post('/api/chat',json={'text':'I inspect the courtyard lantern, then I walk through the courtyard gate.'})
 before=storage.load_session(); world=storage.load_world()
 wire(monkeypatch,raw_record('GM','CORRECTION',components=[('ASK','sergeant_mara')]))
 data=campaign.post('/api/chat',json={'text':'Replace the first step with a question to Mara.'}).json()
 assert data['resolution']['kind']=='conversational_clarify'
 pending=storage.load_session()['conversational_context']['pending_clarification']
 assert [s['operation'] for s in pending['steps']]==['ASK','MOVE']
 assert storage.load_session()['turn_counter']==before['turn_counter']
 assert storage.load_world()==world


def test_unknown_destination_does_not_invent_route(campaign,monkeypatch):
 scene=storage.load_active_scene(); scene['scene']['exits'][0]['target_scene_id']='not_authored'; storage.save_scene(scene)
 before=storage.load_session(); world=storage.load_world()
 wire(monkeypatch,raw_record('CHARACTER','ACTION',components=[('MOVE','courtyard_gate')]))
 data=campaign.post('/api/chat',json={'text':'I proceed through the courtyard gate.'}).json()
 assert data['resolution']['kind']=='conversational_clarify'
 assert 'not an established place' in data['gm_output']['player_facing_text']
 assert storage.load_session()['active_scene_id']==before['active_scene_id']
 assert storage.load_session()['turn_counter']==before['turn_counter']
 assert storage.load_world()==world


def test_causal_answer_uses_resolution_provenance(campaign,monkeypatch):
 wire(monkeypatch,raw_record('CHARACTER','ACTION',components=[('INSPECT','courtyard_lantern')]))
 campaign.post('/api/chat',json={'text':'I examine the courtyard lantern.'})
 wire(monkeypatch,raw_record('GM','EXPLANATION',refs=['cause:reply:0']))
 before=storage.load_session(); world=storage.load_world()
 result=campaign.post('/api/chat',json={'text':'Why did that examination reveal a mark?'}).json()
 answer=result['gm_output']['player_facing_text']
 assert 'inspection' in answer and 'origin or purpose has not been established' in answer
 assert storage.load_session()['turn_counter']==before['turn_counter']
 assert storage.load_world()==world


def test_speech_about_travel_is_not_executed_as_movement(campaign,monkeypatch):
 wire(monkeypatch,raw_record('NPC','QUESTION',components=[('ASK','sergeant_mara')]))
 before=storage.load_session()
 data=campaign.post('/api/chat',json={'text':'I ask Mara where the road outside the gate goes.'}).json()
 assert data['resolution']['social']['npc_id']=='sergeant_mara'
 assert storage.load_session()['active_scene_id']==before['active_scene_id']
 assert data['resolution']['kind']!='scene_transition'


def test_gm_clarification_with_public_answer_is_answered():
 record=raw_record('GM','CLARIFICATION')
 record['public_evidence']={'npc:sergeant_mara:street':'The street beyond the gate is the north road.'}
 result=decision_from_interpretation_record(record,player_text='Explain what she meant.')
 assert result.category.value=='ANSWER'
 assert 'north road' in result.player_facing_text


def test_mixed_gm_observation_and_npc_question_retains_both():
 record=raw_record('GM','DESCRIPTION',components=[('INSPECT','sergeant_mara'),('ASK','sergeant_mara')])
 result=decision_from_interpretation_record(record,player_text='Describe her posture; then I ask about the road.')
 assert result.communication_owner=='MIXED'
 assert len(result.secondary_intentions)==2
 assert not result.requires_authoritative_execution


def test_resolved_discovery_delivers_clue_without_narration(campaign,monkeypatch):
 wire(monkeypatch,raw_record('CHARACTER','ACTION',components=[('INSPECT','courtyard_lantern')]))
 def forbidden(*args,**kwargs):
  raise AssertionError('A complete resolver-owned clue result needs no narration retry')
 monkeypatch.setattr('game.api.call_gpt',forbidden)
 data=campaign.post('/api/chat',json={'text':'I inspect the courtyard lantern.'}).json()
 assert data['resolution']['kind']=='discover_clue'
 assert "maker's mark" in data['gm_output']['player_facing_text']

@pytest.mark.parametrize('purpose,target',[('RECALL','courtyard_lantern'),('QUESTION','sergeant_mara')])
def test_single_gm_question_component_stays_informational(purpose,target):
 record=raw_record('GM',purpose,components=[('ASK',target)])
 record['public_evidence']={'visible:0':'A public observation.'}
 result=decision_from_interpretation_record(record,player_text='Explain the observation.')
 assert result.category.value=='ANSWER'
 assert result.communication_owner=='GM'
 assert not result.requires_authoritative_execution


def test_ambiguous_reference_with_scene_evidence_still_clarifies():
 record=raw_record('GM','CLARIFICATION')
 record['interpretation_status']='CLARIFICATION_REQUIRED'
 record['references']['unresolved_references']=['a demonstrative']
 record['public_evidence']={'scene':'A gate and a lantern.'}
 result=decision_from_interpretation_record(record,player_text='The nearer one.')
 assert result.category.value=='CLARIFY'
 assert not result.requires_authoritative_execution
