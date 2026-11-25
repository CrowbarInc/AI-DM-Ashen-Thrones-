"""Inventory identity is informational authority, never physical permission."""
import copy

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.integrated_play import _LANES
from game.provider_budget import snapshot
from tests.pr_play_79df3_harness import seed_gate
from tests.test_grounded_marking_removal import _ready
from tests.test_ordinary_semantic_admission import state


@pytest.fixture
def client(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    _LANES.clear()
    _ready()
    for key in ('ASHEN_DISABLE_PROVIDER_CALLS', 'ASHEN_DISABLE_LIVE_INTERPRETATION',
                'ASHEN_DISABLE_EXPRESSION_GENERATION', 'ASHEN_DISABLE_PROVIDER_RETRIES'):
        monkeypatch.setenv(key, '1')
    monkeypatch.delenv('ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION', raising=False)
    with TestClient(app) as http:
        yield http


def send(client, text, key='one'):
    before = state()
    providers = len(snapshot()['records'])
    response = client.post('/api/chat?ui_mode=player', json={'text': text, 'client_request_id': key})
    after = state()
    assert response.status_code == 200
    assert len(snapshot()['records']) == providers
    assert all(before[k] == after[k] for k in ('character', 'world', 'scene', 'combat'))
    assert all(before['session'].get(k) == after['session'].get(k)
               for k in ('turn_counter', 'clocks', 'scene_state', 'active_scene_id', 'last_publication'))
    return response.json()['gm_output']['player_facing_text']


@pytest.mark.parametrize('text', [
    'I examine my coat.', 'I examine my travel coat.', 'I examine my TRAVEL COAT.',
    'I inspect the coat in my pack.', 'I inspect my travel coats.',
    'Tell me what I know about the coat.', 'What condition is my coat in?',
    'What color is my coat?', 'Am I wearing my coat?', "What is in my coat's pockets?",
])
def test_identity_does_not_invent_properties(client, text):
    character = storage.load_character()
    character['inventory'][0].update(description='CANARY_PRIVATE_DESCRIPTION', color='CANARY_COLOR',
                                     condition='CANARY_CONDITION', equipped=True, contents=['CANARY_CONTENTS'])
    storage.save_character(character)
    visible = send(client, text)
    assert 'Travel coat' in visible
    assert 'notice board' not in visible.casefold()
    assert 'CANARY_' not in visible
    assert 'not established' in visible


def test_authored_alias(client):
    character = storage.load_character()
    character['inventory'][0]['aliases'] = ['overcoat']
    storage.save_character(character)
    assert 'Travel coat' in send(client, 'Examine my overcoat.')


def test_context_current_identity_and_quantity(client):
    assert 'Travel coat' in send(client, 'Do I have my coat?', 'possess')
    assert 'Travel coat' in send(client, 'Examine it.', 'inspect')
    assert 'Travel coat' in send(client, 'What condition is it in?', 'condition')
    character = storage.load_character()
    character['inventory'][0]['quantity'] = 0
    storage.save_character(character)
    assert 'records no' in send(client, 'Examine it.', 'zero')
    assert 'records no' in send(client, 'Do I still have it?', 'followzero')


@pytest.mark.parametrize('change', ['remove', 'duplicate', 'replace_instance'])
def test_context_rejects_stale_or_ambiguous_identity(client, change):
    send(client, 'Do I have my coat?', 'possess')
    character = storage.load_character()
    if change == 'remove':
        character['inventory'].pop(0)
    elif change == 'duplicate':
        character['inventory'].append(copy.deepcopy(character['inventory'][0]))
    else:
        character['inventory'][0]['instance_id'] = str(__import__('uuid').uuid4())
    storage.save_character(character)
    text = send(client, 'Examine it.', 'follow')
    assert 'notice board' not in text.casefold()
    assert 'Which' in text or 'cannot establish' in text


def test_explicit_switch_and_reload(client):
    send(client, 'Do I have my coat?', 'possess')
    assert 'Paper' in send(client, 'Examine my paper.', 'paper')
    _LANES.clear()
    storage.load_session()
    assert 'Paper' in send(client, 'Examine it.', 'reload')
    assert 'Paper' in send(client, 'What is this item?', 'identity')


def test_unrelated_topic_invalidates_reference(client):
    send(client, 'Do I have my coat?', 'possess')
    client.post('/api/chat?ui_mode=player', json={'text': 'Where am I?', 'client_request_id': 'topic'})
    text = send(client, 'Examine it.', 'follow')
    assert 'Travel coat' not in text
    assert 'notice board' not in text.casefold()


@pytest.mark.parametrize('text', ['Put on my coat.', 'Drop my coat.',
                                 'Use the coat to cover the lantern.', 'Tear the coat into strips.'])
def test_information_does_not_grant_manipulation(client, text):
    send(client, 'Do I have my coat?', 'possess')
    before = state()
    response = client.post('/api/chat?ui_mode=player', json={'text': text, 'client_request_id': 'action'})
    assert response.status_code == 200
    after = state()
    assert all(before[k] == after[k] for k in ('character', 'world', 'scene', 'combat'))
    assert before['session'].get('turn_counter') == after['session'].get('turn_counter')
    decision = (storage.load_log()[-1]['resolution'].get('metadata') or {}).get('conversational_decision') or {}
    assert decision.get('intent_family') != 'inventory_inspection'


def test_search_keeps_existing_physical_owner(client):
    from game.conversational_orchestration import _inventory_inspection_decision
    assert _inventory_inspection_decision("Search the coat's pockets.", character=storage.load_character(),
        session=storage.load_session(), scene=storage.load_active_scene(), world=storage.load_world(), log=[]) is None


def test_supported_visible_markings_only(client):
    from tests.test_grounded_marking_action import ACTION, WARNING
    response = client.post('/api/chat?ui_mode=player', json={'text': ACTION, 'client_request_id': 'mark'})
    assert response.status_code == 200
    text = send(client, 'Examine my coat.', 'inspect')
    assert WARNING in text
    assert 'Travel coat' in text


def test_duplicate_request_is_identical(client):
    first = client.post('/api/chat?ui_mode=player', json={'text': 'Examine my coat.', 'client_request_id': 'retry'})
    before = state()
    second = client.post('/api/chat?ui_mode=player', json={'text': 'Examine my coat.', 'client_request_id': 'retry'})
    assert first.json() == second.json()
    assert state() == before


@pytest.mark.parametrize('access', [True, False])
def test_visible_and_hidden_marking_authority(client, access):
    from tests.test_player_marking_observation import _add
    _add('A public inscription.', 'public', visibility='visible')
    _add('CANARY_HIDDEN_MARK', 'hidden', visibility='concealed')
    _add('CANARY_RESTRICTED_MARK', 'restricted', visibility='restricted', scope='gm')
    if not access:
        c = storage.load_character()
        c['inventory'][0]['marking_surfaces'][0]['accessible'] = False
        storage.save_character(c)
    text = send(client, 'Examine my coat.', 'inspect')
    assert ('A public inscription.' in text) == access
    assert 'CANARY_' not in text


def test_scene_inventory_collision(client):
    c = storage.load_character()
    c['inventory'].append({'id': 'carried_bag', 'name': 'Bag', 'quantity': 1})
    storage.save_character(c)
    scene = storage.load_active_scene()
    scene['scene']['interactables'].append({'id': 'gate_bag', 'name': 'Bag', 'aliases': ['bag'],
        'label': 'bag beside the gate', 'reveals_clue': 'bag_tag'})
    scene['scene'].setdefault('discoverable_clues', []).append({'id': 'bag_tag', 'text': 'The gate bag has an authored tag.'})
    storage.save_scene(scene)
    assert 'Which object' in send(client, 'Examine the bag.', 'ambiguous')
    assert 'records Bag' in send(client, 'Examine the bag in my pack.', 'carried')
    r = client.post('/api/chat?ui_mode=player', json={'text': 'Examine the bag beside the gate.', 'client_request_id': 'scene'})
    assert 'authored tag' in r.json()['gm_output']['player_facing_text']


def test_unbound_reference_does_not_substitute_scenery(client):
    # "book" is not an authored alias of Spellbook. Do not invent that binding.
    from game.referenced_surface import render_referenced_surface_inspection_line
    for authority in ('unsupported', 'authored_hidden'):
        text = render_referenced_surface_inspection_line({'authority': authority}, storage.load_active_scene())
        assert 'Which established object' in text
        assert 'notice board' not in text.casefold()
