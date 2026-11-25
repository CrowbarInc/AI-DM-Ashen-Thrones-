"""Captured provider envelopes and adversarial communication/action conflicts."""
import copy
import json
from pathlib import Path

import pytest
from game import api, storage, conversational_orchestration as co, live_chat_interpretation as live
from game.player_interpretation_bridge import normalized_action_from_interpretation
from tests.test_unresolved_action_consequence_integrity import client, send, quiet, visible

OLD = Path(__file__).resolve().parents[1] / 'artifacts/pr_play_foundational_live_interpretation_validation'

def captured(case):
    trace = json.loads((OLD / (case + '_trace.json')).read_text(encoding='utf-8'))
    return trace['text'], trace['interpretation_outcomes'][0]['raw_interpretation']

def stub(monkeypatch, raw):
    calls = []
    monkeypatch.setattr(live, 'production_live_interpretation_enabled', lambda: True)
    def response(*a, **kw):
        calls.append(1)
        return {'ok': True, 'sent': False, 'text': raw}
    monkeypatch.setattr(live, 'request_interpretation', response)
    return calls

@pytest.mark.parametrize('case', ['A4', 'B1', 'E02', 'N1'])
def test_exact_raw_replay(client, monkeypatch, case):
    text, raw = captured(case)
    calls = stub(monkeypatch, raw)
    ticks = []
    original = api.advance_world_tick
    def tick(*a, **kw):
        ticks.append(1)
        return original(*a, **kw)
    monkeypatch.setattr(api, 'advance_world_tick', tick)
    row = send(client, text, case)
    response = visible(row)
    if case == 'N1':
        assert row['after']['session']['turn_counter'] - row['before']['session']['turn_counter'] == 1
        assert len(ticks) == 1
        assert 'northwest mud track' in response
        assert 'notice_patrol_route' in json.dumps(row['after']['session'])
        assert row['after']['character'] == row['before']['character']
        # Check persisted, freshly loaded consequence and the established bridge.
        assert storage.load_session() == row['after']['session']
    else:
        quiet(row)
        assert not ticks
        assert 'northwest mud track' not in response
        assert 'Which single action' not in response
        if case == 'A4':
            from game.carried_object_grounding import prepared_spell_rows
            assert all(r['name'] in response for r in prepared_spell_rows(row['before']['character']))
            assert all(s in response for s in ('hands off', 'hypothetical', 'no spell slot', 'not a complete list'))
        if case == 'B1':
            d = row['log']['resolution']['metadata']['conversational_decision']
            assert d['communication_owner'] == 'NPC'
            assert d['primary_intention'] == text and d['incidental_context']
            assert d['authorization']['addressee_grounding']['target_id'] is None
            assert 'officer' in response and 'Which established person' in response
            assert response.count('Nothing has been attempted.') == 1
        if case == 'E02':
            assert 'surroundings for signs of danger' in response
            assert 'Notice board' in response
    replay = send(client, text, case)
    assert row['response'] == replay['response'] and row['after'] == replay['after']
    assert len(calls) == 1

NEGATIVES = [
    ('description_no_action', 'Describe the notice board.'),
    ('fabricated', 'Describe the notice board.'),
    ('inaccessible', 'I take a good look at the notice board.'),
    ('hidden', 'I take a good look at the notice board.'),
    ('ambiguous', 'I take a good look at the board.'),
    ('negated', 'I do not examine the notice board.'),
    ('hypothetical', 'I might examine the notice board.'),
    ('deferred', 'I will examine the notice board when the crowd clears.'),
    ('two_actions', 'I examine the notice board and enter Cinderwatch.'),
    ('unsupported_tail', 'I examine the notice board and teleport to the moon.'),
    ('unaccounted_modifier', 'I examine the notice board inside a locked chest.'),
]

@pytest.mark.parametrize('kind,text', NEGATIVES, ids=[r[0] for r in NEGATIVES])
def test_n1_negative_controls(client, monkeypatch, kind, text):
    payload = json.loads(captured('N1')[1])
    if kind == 'description_no_action':
        payload['action_components'] = []
    if kind in {'hidden', 'inaccessible', 'ambiguous'}:
        scene = storage.load_active_scene()
        inner = scene.get('scene', scene)
        board = next(r for r in inner['interactables'] if r['id'] == 'notice_board')
        if kind == 'ambiguous':
            other = copy.deepcopy(board)
            other.update(id='second_board', name='Other board', label='Other board')
            inner['interactables'].append(other)
        else:
            board['hidden' if kind == 'hidden' else 'accessible'] = kind == 'hidden'
        storage.save_scene(scene)
    stub(monkeypatch, json.dumps(payload))
    row = send(client, text, kind)
    quiet(row)
    assert 'northwest mud track' not in visible(row)
    # Also exercise stored-record decision and bridge, independently of a
    # deterministic early intercept or adapter rejection of hidden catalog ids.
    b = row['before']
    decision = co.decision_from_interpretation_record(payload, player_text=text,
        scene=b['scene'], world=b['world'], session=b['session'], character=b['character'])
    if decision.category == co.ConversationalDecisionCategory.EXECUTE:
        action, metadata = normalized_action_from_interpretation(decision.proposed_record,
            scene=b['scene'], world=b['world'], session=b['session'], player_text=text)
        assert action is None and metadata.get('accepted') is not True

@pytest.mark.parametrize('text,executes', [
    ('What does the board say?', False), ('Describe the board.', False),
    ('What can I see on the board?', False), ('I examine the board.', True),
    ('I take a closer look at the board.', True), ('I inspect the board for hidden markings.', True),
    ('I might examine the board later.', False), ('I do not examine the board.', False),
    ('Can I examine the board?', False),
])
def test_information_action_distinction(client, monkeypatch, text, executes):
    stub(monkeypatch, captured('N1')[1])
    row = send(client, text)
    if executes:
        assert row['after']['session']['turn_counter'] - row['before']['session']['turn_counter'] == 1
        assert 'northwest mud track' in visible(row)
    else:
        quiet(row)
        assert 'northwest mud track' not in visible(row)

@pytest.mark.parametrize('case', ['A4', 'B1'])
@pytest.mark.parametrize('bad', ['invalid_json', 'invalid_schema', 'unknown_id', 'invalid_evidence', 'timeout'])
def test_invalid_records_cannot_gain_permission(client, monkeypatch, case, bad):
    text, raw = captured(case)
    payload = json.loads(raw)
    if bad == 'unknown_id': payload['references']['permitted_entity_ids'].append('fabricated_officer')
    if bad == 'invalid_evidence': payload['communication']['evidence_refs'] = ['hidden:secret']
    raw = '{' if bad == 'invalid_json' else '{}' if bad == 'invalid_schema' else json.dumps(payload)
    stub(monkeypatch, raw)
    if bad == 'timeout': monkeypatch.setattr(live, 'request_interpretation', lambda *a, **kw: {'ok':False, 'sent':False, 'reason':'provider_failure'})
    row = send(client, text)
    quiet(row)
    assert 'northwest mud track' not in visible(row)
    assert 'has these spells prepared' not in visible(row)

def test_a4_missing_sheet_does_not_invent_information(client, monkeypatch):
    character = storage.load_character()
    character.pop('spells', None)
    storage.save_character(character)
    text, raw = captured('A4')
    stub(monkeypatch, raw)
    row = send(client, text)
    quiet(row)
    assert 'does not list any prepared spells' in visible(row)
    assert 'Magic Missile' not in visible(row)

@pytest.mark.parametrize('text,executes', [
    (captured('A4')[0], False), (captured('B1')[0], False), (captured('E02')[0], False),
    ('What spells do I have prepared?', False), ('I examine the notice board.', True),
    ('I will examine the notice board when the crowd clears.', False),
])
def test_provider_disabled(client, text, executes):
    row = send(client, text)
    if executes:
        assert row['after']['session']['turn_counter'] - row['before']['session']['turn_counter'] == 1
        assert 'northwest mud track' in visible(row)
    else:
        quiet(row)
        assert 'northwest mud track' not in visible(row)

@pytest.mark.parametrize('mode', ['failure', 'timeout'])
def test_n1_consequence_does_not_depend_on_optional_narration(client, monkeypatch, mode):
    text, raw = captured('N1')
    stub(monkeypatch, raw)
    def fail(**kw):
        raise TimeoutError('offline timeout') if mode == 'timeout' else RuntimeError('offline failure')
    monkeypatch.setattr(api, '_build_gpt_narration_from_authoritative_state', fail)
    row = send(client, text, mode)
    assert row['after']['session']['turn_counter'] == row['before']['session']['turn_counter'] + 1
    assert 'northwest mud track' in visible(row)
    assert 'notice_patrol_route' in json.dumps(row['after']['session'])
    replay = send(client, text, mode)
    assert row['response'] == replay['response'] and row['after'] == replay['after']
