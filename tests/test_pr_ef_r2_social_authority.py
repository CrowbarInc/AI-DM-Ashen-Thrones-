"""Resolver identity, knowledge, emission and incidental intent boundaries."""
import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from game import storage
from game.api import app
from game.immutable_valid_response import validate_generated_response, safe_nonresolution
from game.live_chat_interpretation import normalize_social_scope
from game.conversational_orchestration import deterministic_conversational_decision, public_conversation_evidence
from tests.test_pr_ef_gm_authority import seed_scene, raw_record
from tests.test_pr_du_player_pipeline import _fake_gm_for_resolution


@pytest.mark.parametrize("index", [2, 10, 14])
def test_original_captured_failures_preserve_authority(tmp_path, monkeypatch, index):
    seed_scene(tmp_path, monkeypatch)
    source = Path(__file__).resolve().parents[1] / 'artifacts/pr_ef_r1/holdouts_1.json'
    row = json.loads(source.read_text(encoding='utf-8'))['rows'][index]
    monkeypatch.setenv('ASHEN_DISABLE_PROVIDER_CALLS', '0')
    monkeypatch.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION', '0')
    monkeypatch.setattr('game.live_chat_interpretation.request_interpretation',
                        lambda *a, **kw: dict(ok=True, sent=False, text=row['isolated_interpretation']['raw_interpretation']))
    monkeypatch.setattr('game.api.call_gpt', _fake_gm_for_resolution)
    before = copy.deepcopy(storage.load_world())
    data = TestClient(app).post('/api/chat', json={'text': row['player']}).json()
    result = data['resolution']
    assert result['social']['npc_id'] == 'sergeant_mara'
    assert result['social']['target_resolved'] is True
    contract = result['metadata']['resolution_contract']
    assert contract['operation'] == 'ask'
    assert contract['interlocutor_id'] == 'sergeant_mara'
    assert result['metadata']['authoritative_result']['target_id'] == 'sergeant_mara'
    text = data['gm_output']['player_facing_text']
    assert 'Sergeant Mara' in text
    assert 'cannot be identified' not in text and 'No one here' not in text
    if index != 14:
        assert result['social']['topic_revealed'] is None
        assert 'north road' not in text  # invalid narration stub must remain rejected
    else:
        assert 'north road' in text
        record = result['metadata']['live_chat_interpretation']['record']
        assert record['incidental_context'] == ['Turn to Sergeant Mara']
    after_world = storage.load_world()
    # A committed social turn runs the existing passive faction clock. NPC
    # knowledge and all other world domains must stay intact.
    assert {k:v for k,v in after_world.items() if k not in {'factions', 'event_log'}} == {
        k:v for k,v in before.items() if k not in {'factions', 'event_log'}}
    session = copy.deepcopy(storage.load_session())
    storage.save_session(session)
    reloaded = storage.load_session()
    assert {k:v for k,v in reloaded.items() if k != 'last_saved_at'} == {
        k:v for k,v in session.items() if k != 'last_saved_at'}
    assert session['turn_counter'] == 1


def authority():
    return ({'operation': 'ask', 'interlocutor_id': 'sergeant_mara',
             'construction': {'entity_binding': {'status': 'bound_canonical', 'label': 'Sergeant Mara'}}},
            {'social': {'npc_id': 'sergeant_mara', 'npc_name': 'Sergeant Mara', 'target_resolved': True}})


@pytest.mark.parametrize('text,reason', [
    ('No one here can answer that from what is settled here.', 'authoritative_target_contradiction'),
    ('The person you addressed cannot be identified clearly enough to answer.', 'authoritative_target_contradiction'),
    ('Captain Sella says, "I do not know."', 'wrong_interlocutor'),
    ('The secret is hidden fact: a spy.', 'hidden_information'),
])
def test_known_target_keeps_legitimate_emission_safeguards(text, reason):
    contract, result = authority()
    verdict = validate_generated_response(text, contract=contract, resolution=result)
    assert not verdict['hard_valid']
    assert reason in verdict['reasons']


def test_known_target_unknown_answer_remains_known():
    contract, result = authority()
    text = safe_nonresolution(contract, resolution=result)
    assert text.startswith('Sergeant Mara says,')
    assert validate_generated_response(text, contract=contract, resolution=result)['hard_valid']
    unknown = {'operation': 'ask', 'construction': {'entity_binding': {
        'status': 'unresolved', 'explicit_new_interlocutor': True, 'proposed_interlocutor': 'Sella'}}}
    assert 'cannot be identified' in safe_nonresolution(unknown, resolution=result)


@pytest.mark.parametrize('gesture,incidental', [
    ('Turn toward Sergeant Mara', True), ('Glance at Sergeant Mara', True),
    ('Incline head to Sergeant Mara as a social signal.', True),
    ('Draw my sword and face Sergeant Mara', False), ('Unlock the door', False),
    ('Turn toward Sergeant Mara then leave', False), ('Threaten Sergeant Mara', False),
])
def test_only_bounded_posture_is_incidental(gesture, incidental):
    payload = raw_record('NPC', components=[('SOCIAL_SIGNAL', 'sergeant_mara'), ('ASK', 'sergeant_mara')])
    payload['action_components'][0]['description'] = gesture
    communication = payload.pop('communication')
    normalized, context = normalize_social_scope(payload, communication)
    assert bool(context) == incidental
    assert len(normalized['action_components']) == (1 if incidental else 2)
    assert len(payload['action_components']) == 2


def test_subject_unknown_does_not_clear_unknown_addressee_or_secondary_move():
    payload = raw_record('NPC', components=[('ASK', 'sergeant_mara')])
    communication = payload.pop('communication'); communication['subject'] = 'distant kingdom'
    payload['references']['unresolved_references'] = ['distant kingdom', 'unknown captain']
    normalized, _ = normalize_social_scope(payload, communication)
    # Provider subject wording is not authoritative grounding.
    assert normalized['references']['unresolved_references'] == ['distant kingdom', 'unknown captain']
    payload['action_components'].append(dict(order=2, description='Leave', operation_class='MOVE', target_ref='courtyard_gate'))
    normalized, _ = normalize_social_scope(payload, communication)
    assert normalized['references']['unresolved_references'] == ['distant kingdom', 'unknown captain']
    assert len(normalized['action_components']) == 2


@pytest.mark.parametrize('success,text', [(False, 'You succeed.'), (True, 'You fail to hit.')])
def test_mechanical_outcome_still_validates(success, text):
    verdict = validate_generated_response(text, contract={'operation': 'act'}, resolution={'mechanical_success': success})
    assert not verdict['hard_valid']


def test_possessive_body_part_does_not_select_movement(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    monkeypatch.setenv('ASHEN_DISABLE_PROVIDER_CALLS', '0')
    monkeypatch.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION', '0')
    decision = deterministic_conversational_decision(
        player_text='I incline my head to Mara and inquire about the patrol.',
        scene=storage.load_active_scene(), world=storage.load_world(), session=storage.load_session())
    assert decision is None  # the existing semantic call owns this wording


def test_latest_unknown_statement_is_public_continuation_evidence():
    log = [dict(player_facing_text='Mara says, "Road details."', resolution={'social': {
        'target_resolved': True, 'npc_id': 'mara', 'topic_revealed': {'id': 'road', 'text': 'Road details.'}}}),
        dict(player_facing_text='Mara says, "I do not know who forged it."', resolution={'social': {
            'target_resolved': True, 'npc_id': 'mara', 'topic_revealed': None}})]
    evidence = public_conversation_evidence(None, log)
    assert evidence['npc_latest_reply'] == log[-1]['player_facing_text']
    assert evidence['npc:mara:road'] == 'Road details.'


@pytest.mark.parametrize('regenerate', [None, lambda feedback: {'player_facing_text': 'Captain says, "Yes."'}])
def test_conflicting_authorities_cannot_be_sealed_as_valid(regenerate):
    from game.immutable_valid_response import run_preserve_if_valid, effects_allowed
    contract, result = authority()
    contract['contract_id'] = 'conflict'
    contract['construction']['authority_conflict'] = {'contract_target': 'mara', 'social_target': 'sella'}
    result['metadata'] = {'resolution_contract': contract}
    out = run_preserve_if_valid({'player_facing_text': 'Captain says, "Yes."'},
                                regenerate=regenerate, resolution=result, player_text='I ask Mara.', referents=[])
    # The NPC candidate remains rejected; the fixed host safety response now
    # has its own immutable adoption so downstream helpers cannot replace it.
    accepted = out['metadata']['accepted_response']
    assert accepted['immutable'] is True
    assert accepted['candidate_disposition'] == 'rejected'
    assert accepted['authorization_source'] == 'host_terminal_safety'
    assert 'conflicting_target_authorities' in accepted['rejected_candidate']['hard_invalid_reasons']
    assert not effects_allowed(out)
    assert out['player_facing_text'] == 'I cannot provide a validated response to that request.'
