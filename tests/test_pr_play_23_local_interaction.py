"""Offline production orchestration/HTTP regressions for PR-PLAY-23."""
import copy
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import game.api as api
from game import storage as st
from game.conversational_orchestration import decision_from_interpretation_record, ConversationalDecisionCategory as Cat
from game.player_interpretation_bridge import normalized_action_from_interpretation
from game.local_interaction import normalize_local_approach
from game.opening_presentation_renderer import plan_selecting_required
from tests.test_pr_play_04_opening_integrity import opening_world
from tests.test_pr_play_18_contract_alignment import _transport
from tests.test_pr_dy_live_gameplay import _enable_live, _install_interpretation, _payload
from tests.helpers.turn_pipeline_http_fixtures import _gm_response
from tools.playtest.gameplay import classify_turn

EVIDENCE = Path('artifacts/pr_play_23')
ORIGINAL = Path('artifacts/atgb/pr_play_22/live/turns/T1')
TEXT = "I approach the tavern runner and ask what they're offering."


def captured():
    diag = json.loads((ORIGINAL/'parser_validation_diagnostics.json').read_text())
    return diag['resolution']['metadata']['live_chat_interpretation']['record']


def raw_captured():
    diag = json.loads((ORIGINAL/'parser_validation_diagnostics.json').read_text())
    return json.loads(diag['resolution']['metadata']['live_chat_interpretation']['raw_interpretation'])


def authored_scene():
    return json.loads((ORIGINAL/'before/persistent/scenes/frontier_gate.json').read_text())


def save(name, value):
    if os.environ.get('ASHEN_PR_PLAY_23_EVIDENCE') == '1':
        (EVIDENCE/name).write_text(json.dumps(value, indent=2, default=str), encoding='utf-8')


def state():
    return {name: getattr(st, 'load_'+name)() for name in ('world', 'session', 'character', 'campaign', 'combat', 'conditions')}


def test_original_failure_boundary(monkeypatch):
    record = captured()
    scene = json.loads((ORIGINAL/'before/persistent/scenes/frontier_gate.json').read_text())
    world = json.loads((ORIGINAL/'before/persistent/world.json').read_text())
    # Disable only the new normalization to reproduce the unchanged old path.
    monkeypatch.setattr('game.local_interaction.normalize_local_approach', lambda r, **kw: r)
    before = copy.deepcopy((scene, world, record))
    move = copy.deepcopy(record)
    move['action_components'] = [record['action_components'][0]]
    action, meta = normalized_action_from_interpretation(move, scene=scene, world=world, player_text=TEXT)
    decision = decision_from_interpretation_record(record, player_text=TEXT, scene=scene, world=world)
    save('original_reproduction.json', {'bridge': meta, 'decision': decision.to_dict() if hasattr(decision, 'to_dict') else vars(decision)})
    assert action is None and meta['reason'] == 'operation_incompatible_with_entity_kind'
    assert decision.reason == 'proposal_not_eligible'
    assert 'I have not done any of them yet.' in decision.player_facing_text
    assert (scene, world, record) == before


@pytest.mark.parametrize('name,first,second,op', [
    ('Tavern Runner', 'approach', "ask what they're offering", 'ASK'),
    ('Gate Guard', 'walk over to', 'ask about the missing patrol', 'ASK'),
    ('Notice board', 'walk over to', 'examine the notices', 'INSPECT'),
])
def test_general_local_targets(opening_world, name, first, second, op):
    scene = authored_scene()
    world = json.loads((ORIGINAL/'before/persistent/world.json').read_text())
    target = {'Tavern Runner': 'tavern_runner', 'Gate Guard': 'gate_guard', 'Notice board': 'notice_board'}[name]
    # Gate Guard is authored in the opening fixture, unlike data's captain.
    if name == 'Gate Guard':
        npc = next(n for n in world['npcs'] if n['id'] == target)
        assert npc['location'] == scene['scene']['id']
        # Explicit authored accessibility for this synthetic guard scenario.
        scene['scene']['addressables'].append({'id': target, 'name': name, 'scene_id': scene['scene']['id'], 'addressable': True, 'kind': 'npc'})
        world['npcs'] = [npc]
    text = f'I {first} the {name} and {second}.'
    record = _payload('IN_WORLD_ACTION', 'INTERPRETED', [('MOVE', target), (op, target)])
    record['action_components'][0]['description'] = f'{first} the {name}'
    result = normalize_local_approach(record, player_text=text, scene=scene, world=world, session=st.load_session())
    assert len(result['action_components']) == 1
    assert result['local_approach_normalization']['movement_executed'] is False


@pytest.mark.parametrize('variant', ['locked', 'cross_scene', 'unregistered', 'unknown_access', 'hostile', 'extra', 'raw_crossing', 'target_mismatch', 'theft', 'player_barrier', 'authored_access_false', 'travel'])
def test_consequential_or_uncertain_steps_preserved(opening_world, variant):
    scene, world = st.load_active_scene(), st.load_world()
    record = captured()
    text = TEXT
    npc = next(n for n in world['npcs'] if n['id'] == 'tavern_runner')
    if variant == 'locked':
        scene['scene']['visible_facts'].append('The runner is behind a locked gate.')
    elif variant == 'cross_scene':
        npc['location'] = 'market_quarter'
    elif variant in {'unregistered', 'unknown_access'}:
        scene['scene']['addressables'] = [a for a in scene['scene']['addressables'] if a['id'] != 'tavern_runner']
        if variant == 'unregistered':
            world['npcs'].remove(npc)
    elif variant == 'hostile':
        npc['stance_toward_player'] = 'hostile'
    elif variant == 'extra':
        record['action_components'].append({'order': 3, 'operation_class': 'ATTACK', 'target_ref': 'tavern_runner', 'description': 'attack'})
    elif variant == 'raw_crossing':
        text = 'I cross the ravine and approach the tavern runner and ask about prices.'
    elif variant == 'target_mismatch':
        record['action_components'][0]['target_ref'] = 'notice_board'
    elif variant == 'player_barrier':
        text = 'I approach the tavern runner behind the locked gate and ask a question.'
    elif variant == 'authored_access_false':
        next(a for a in scene['scene']['addressables'] if a['id'] == 'tavern_runner')['accessible'] = False
    elif variant == 'travel':
        text = 'I travel to the northern district and speak to the captain.'
        record['action_components'][0]['description'] = 'Travel to the northern district'
    else:
        record['action_components'][0]['operation_class'] = 'USE_VISIBLE_OBJECT'
        record['action_components'][0]['description'] = "Steal the runner's purse"
    original = copy.deepcopy(record)
    assert normalize_local_approach(record, player_text=text, scene=scene, world=world, session=st.load_session()) == original
    decision = decision_from_interpretation_record(record, player_text=text, scene=scene, world=world)
    assert decision.category != Cat.EXECUTE


@pytest.mark.parametrize('direct', [False, True])
def test_opening_to_interaction_publication(opening_world, monkeypatch, direct):
    monkeypatch.setenv('ASHEN_OPENING_RENDERER', '1')
    seen = []
    _transport(monkeypatch, seen, lambda kw: plan_selecting_required(kw['input']))
    secret = 'PR_PLAY_23_SYNTHETIC_HIDDEN_SENTINEL'
    world = st.load_world()
    world['internal_state'] = {'secret': secret}
    st.save_world(world)
    with TestClient(api.app) as client:
        opening = client.post('/api/start_campaign?ui_mode=player')
        assert opening.status_code == 200
        assert 'tavern runner' in opening.json()['gm_output']['player_facing_text'].lower()
        before = state()
        record = raw_captured()
        text = TEXT
        if direct:
            record['action_components'] = record['action_components'][1:]
            text = "I ask the tavern runner what they're offering."
        # Real interpretation request builder + parser; only transport is mocked.
        _enable_live(monkeypatch)
        calls = []
        _install_interpretation(monkeypatch, record, calls)
        narration = []
        def narrate(messages, **kw):
            narration.append(messages)
            return _gm_response('Tavern Runner says, "Hot stew and paid rumor."')
        monkeypatch.setattr(api, 'call_gpt', narrate)
        response = client.post('/api/chat?ui_mode=player', json={'text': text})
        body = response.json()
        after = state()
    internal = st.load_log()[-1]
    save('direct_integration.json' if direct else 'local_integration.json', {
        'status': response.status_code, 'response': body, 'resolution': internal.get('resolution'),
        'before': before, 'after': after, 'interpretation_mock_calls': len(calls),
        'narration_mock_calls': len(narration), 'classification': classify_turn(response.status_code, body), 'live_provider_requests': 0})
    assert response.status_code == 200 and len(calls) == 1
    # Existing knowledge authority may publish its deterministic NPC answer
    # without a narration provider; both are real execution/publication paths.
    assert narration or 'authorized_host_speech' in body['gm_output']['tags']
    assert internal['resolution']['kind'] in {'social_probe', 'social_exchange', 'question'}
    assert body['gm_output']['player_facing_text'] == internal['gm_output']['player_facing_text']
    assert body['gm_output']['player_facing_text']
    assert not internal['resolution'].get('resolved_transition')
    assert after['session']['active_scene_id'] == before['session']['active_scene_id']
    for name in ('character', 'campaign', 'combat', 'conditions'):
        assert after[name] == before[name]
    # Social runtime/log bookkeeping is permitted; authored world truth is not.
    from game.world import advance_world_tick
    expected_world = copy.deepcopy(before['world'])
    advance_world_tick(expected_world, before['campaign'])
    assert after['world'] == expected_world
    from game.state_channels import deep_project_public_payload
    assert body == deep_project_public_payload(body)
    assert secret not in response.text and after['world']['internal_state']['secret'] == secret
    assert classify_turn(200, body)['gameplay_completed']


def test_negative_http_no_later_action(opening_world, monkeypatch):
    _enable_live(monkeypatch)
    record = raw_captured()
    record['action_components'][0].update(operation_class='ATTACK', description='Steal the purse')
    calls = []
    _install_interpretation(monkeypatch, record, calls)
    monkeypatch.setattr(api, 'call_gpt', lambda *a, **kw: pytest.fail('later ASK executed'))
    before = state()
    with TestClient(api.app) as client:
        response = client.post('/api/chat', json={'text': "I steal the runner's purse and ask about prices."})
    after = state()
    body = response.json()
    classification = classify_turn(response.status_code, body)
    save('negative_integration.json', {'response': body, 'before': before, 'after': after, 'classification': classification})
    assert classification['stop'] and not classification['gameplay_completed']
    assert after['world'] == before['world'] and after['character'] == before['character']
    assert 'not done any' in body['gm_output']['player_facing_text']
