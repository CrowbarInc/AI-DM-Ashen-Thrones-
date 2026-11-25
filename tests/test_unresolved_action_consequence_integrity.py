"""Whole requests and grounded inspections acquire consequences only after admission."""
import copy
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import api, storage, conversational_orchestration as co
from game.integrated_play import _LANES
from game.provider_budget import snapshot
from tests.pr_play_79df3_harness import seed_gate
from tests.test_ordinary_semantic_admission import state

HISTORICAL = Path(__file__).resolve().parents[1] / 'artifacts/pr_play_pre_model_routing_assessment'
E02 = json.loads((HISTORICAL / 'E02_disabled.json').read_text())['text']
G02 = json.loads((HISTORICAL / 'G02_disabled.json').read_text())['text']
CLUE = 'northwest mud track'
SESSION_AUTHORITY = (
    'turn_counter', 'clocks', 'active_scene_id', 'scene_state', 'scene_runtime',
    'clue_knowledge', 'discovered_clues', 'npc_runtime', 'mechanical_action_receipts',
    'bounded_improvisation', 'interaction_context',
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    _LANES.clear()
    for key in ('ASHEN_DISABLE_PROVIDER_CALLS', 'ASHEN_DISABLE_LIVE_INTERPRETATION',
                'ASHEN_DISABLE_EXPRESSION_GENERATION', 'ASHEN_DISABLE_PROVIDER_RETRIES'):
        monkeypatch.setenv(key, '1')
    monkeypatch.delenv('ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION', raising=False)
    with TestClient(api.app) as http:
        yield http
    _LANES.clear()


def send(client, text, key='one'):
    before = state()
    providers = len(snapshot()['records'])
    response = client.post('/api/chat?ui_mode=player', json={'text': text, 'client_request_id': key})
    assert response.status_code == 200
    after = state()
    assert len(snapshot()['records']) == providers
    row = {'text': text, 'before': before, 'after': after, 'response': response.json(),
           'log': storage.load_log()[-1], 'provider_delta': 0}
    directory = os.environ.get('ASHEN_CONSEQUENCE_EVIDENCE')
    if directory:
        target = Path(directory); target.mkdir(parents=True, exist_ok=True)
        import hashlib
        name = hashlib.sha256((text + key).encode()).hexdigest()[:20]
        path = target / (name + '.json')
        ordinal = 2
        while path.exists():
            path = target / (name + '-' + str(ordinal) + '.json')
            ordinal += 1
        path.write_text(json.dumps(row, indent=2), encoding='utf-8')
    return row


def quiet(row):
    for domain in ('character', 'world', 'scene', 'combat'):
        assert row['before'][domain] == row['after'][domain], domain
    for field in SESSION_AUTHORITY:
        assert row['before']['session'].get(field) == row['after']['session'].get(field), field
    for field in set(row['before']['session']) | set(row['after']['session']):
        if field not in {'conversational_context', 'last_publication', 'last_saved_at'}:
            assert row['before']['session'].get(field) == row['after']['session'].get(field), field
    assert (row['before']['session'].get('conversational_context') or {}).get('last_executed_intention') == (
        row['after']['session'].get('conversational_context') or {}).get('last_executed_intention')


def visible(row):
    return row['response']['gm_output']['player_facing_text']


@pytest.mark.parametrize('text', [E02, G02], ids=['E02', 'G02'])
def test_historical_and_replay(client, monkeypatch, text):
    calls = []
    original = api._resolve_engine_noncombat_seam
    def resolve(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(api, '_resolve_engine_noncombat_seam', resolve)
    row = send(client, text)
    quiet(row)
    assert not calls
    assert CLUE not in visible(row)
    assert text == row['log']['request']['chat']
    first = copy.deepcopy(row['after'])
    replay = send(client, text)
    quiet(replay)
    assert replay['response'] == row['response']
    assert replay['after'] == first
    _LANES.clear()
    replay = send(client, text, 'fresh-request')
    quiet(replay)
    assert CLUE not in visible(replay)
    if text == G02:
        auth = row['log']['resolution']['metadata']['conversational_decision']['authorization']
        assert auth['original_text'] == text
        assert auth['actionable_coverage']['conditional']


@pytest.mark.parametrize('text', [
    'I search the absent astrolabe.',
    'I search for the silver astrolabe.',
    'I search the sealed chest behind the locked gate.',
    'I investigate fabricated_object_999.',
    'I examine it.',
])
def test_unresolved_inspections(client, text):
    row = send(client, text)
    quiet(row)
    assert CLUE not in visible(row)
    assert 'You examine' not in visible(row)


@pytest.mark.parametrize('text', [
    G02,
    'I examine the notice board if the captain beckons.',
    'I examine the notice board unless the captain objects.',
    'If the crowd has cleared, I examine the notice board.',
    'I examine the notice board when the crowd has not cleared.',
    'I examine the notice board if the crowd clears and the captain beckons.',
    'I examine the notice board if the captain beckons; otherwise I open the gate.',
    'I examine the notice board if the unknown herald approves.',
    'If the captain beckons, I teleport to the moon.',
    'I would examine the notice board if the crowd cleared.',
    'If the crowd clears, what spells do I have prepared?',
    'I examine the notice board and then teleport to the moon.',
])
def test_conditional_and_incomplete_requests(client, text):
    row = send(client, text)
    quiet(row)
    assert CLUE not in visible(row)


@pytest.mark.parametrize('truth', [False, True])
def test_condition_truth_requires_supported_host_owner(client, truth):
    # Host data can record a fact without having a contract to evaluate English
    # conditions. Neither a true flag nor a false flag authorizes truncation.
    world = storage.load_world()
    world.setdefault('world_state', {}).setdefault('flags', {})['crowd_cleared'] = truth
    storage.save_world(world)
    assert storage.load_world()['world_state']['flags']['crowd_cleared'] is truth
    row = send(client, 'I examine the notice board if the crowd has cleared.')
    quiet(row)
    assert CLUE not in visible(row)


@pytest.mark.parametrize('text', [E02, G02], ids=['E02', 'G02'])
@pytest.mark.parametrize('failure', ['unavailable', 'budget', 'failure', 'invalid', 'narration'])
def test_provider_failure_cannot_admit(client, monkeypatch, text, failure):
    def interpret(**kwargs):
        if failure == 'failure':
            return {'status': 'error', 'reason': 'provider_failure'}
        if failure == 'budget':
            return {'status': 'skipped', 'reason': 'provider_budget_refusal'}
        if failure == 'invalid':
            return {'status': 'blocked', 'reason': 'invalid_model_response', 'record': {'unsafe': True}}
        return {'status': 'skipped', 'reason': 'unavailable'}
    monkeypatch.setattr(api, 'interpret_production_turn', interpret)
    def forbidden(**kwargs):
        raise AssertionError('unadmitted request reached narration')
    monkeypatch.setattr(api, '_build_gpt_narration_from_authoritative_state', forbidden)
    row = send(client, text)
    quiet(row)
    assert CLUE not in visible(row)


@pytest.mark.parametrize('text', [
    'I examine the notice board.', 'I search the notice board.',
    'I investigate the notice board.',
])
def test_valid_inspection_commits_exactly_once(client, text):
    row = send(client, text)
    assert row['after']['session']['turn_counter'] == row['before']['session']['turn_counter'] + 1
    assert CLUE in visible(row)
    assert row['before']['character'] == row['after']['character']
    assert row['before']['combat'] == row['after']['combat']
    first = copy.deepcopy(row['after'])
    replay = send(client, text)
    assert replay['response'] == row['response']
    assert replay['after'] == first


def test_target_admission_reuses_surface_authority():
    scene = {'scene': {'id': 'yard', 'visible_facts': ['A rain barrel stands beside the wall.'],
                      'hidden_facts': ['A secret cache is under the paving.'],
                      'interactables': [{'id': 'notice_board', 'label': 'Notice board'}]}}
    for target in ('notice board', 'rain barrel'):
        assert co.inspection_action_admission('I search the ' + target + '.', {'type': 'investigate'},
            scene=scene, world={}, character={}) is None
    for target in ('secret cache', 'absent astrolabe', 'fabricated_object_999'):
        decision = co.inspection_action_admission('I search the ' + target + '.', {'type': 'investigate'},
            scene=scene, world={}, character={})
        assert decision is not None
        assert not decision.requires_authoritative_execution
        assert decision.authorization['turn_advancement'] is False
        assert 'under the paving' not in json.dumps(decision.to_public_dict())


def test_stored_singleton_cannot_erase_condition(client, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('conditional request consulted a singleton proposal')
    monkeypatch.setattr(api, '_stored_interpretation_for_player_text', forbidden)
    row = send(client, G02)
    quiet(row)
    assert CLUE not in visible(row)


@pytest.mark.parametrize('kind', ['hidden', 'inaccessible', 'ambiguous'])
def test_authored_unavailable_or_ambiguous_object(client, monkeypatch, kind):
    scene = storage.load_active_scene()
    rows = [{'id': 'red_crate', 'label': 'Red crate', 'aliases': ['crate'],
             'reveals_clue': 'notice_patrol_route'}]
    if kind == 'hidden':
        rows[0]['hidden'] = True
    elif kind == 'inaccessible':
        rows[0]['accessible'] = False
    else:
        rows.append({'id': 'blue_crate', 'label': 'Blue crate', 'aliases': ['crate'],
                     'reveals_clue': 'notice_patrol_route'})
    scene['scene']['interactables'] = rows
    monkeypatch.setattr(api, 'load_active_scene', lambda: copy.deepcopy(scene))
    monkeypatch.setattr(storage, 'load_active_scene', lambda: copy.deepcopy(scene))
    row = send(client, 'I search the crate.')
    quiet(row)
    assert CLUE not in visible(row)
    if kind != 'ambiguous':
        assert 'Red crate' not in visible(row)
    else:
        assert 'Red crate' in visible(row) and 'Blue crate' in visible(row)
