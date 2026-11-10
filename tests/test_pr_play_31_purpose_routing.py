"""Offline purpose routing, authority negatives, and staged application replay."""
import copy
import json
import shutil
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import api, storage as st
from game.conversational_orchestration import (
    _destination_phrase, _movement_and_purpose, _analyze_clause,
    deterministic_conversational_decision, _operation_record,
)
from game.player_interpretation_bridge import normalized_action_from_interpretation
from tests.test_pr_play_04_opening_integrity import opening_world
from tests.test_pr_play_25_public_fact_dialogue import (
    _transport, plan_selecting_required, _enable_live, _install_interpretation, state,
)
from tests.test_pr_dy_live_gameplay import _payload
from tools.atgb.baseline import load_baseline
from tools.playtest import gameplay as g
from tests.test_five_turn_gameplay import action

OUT = Path('artifacts/pr_play_31')
TEXT = 'I head northwest of the crates to investigate the muddy footprints.'


@pytest.mark.parametrize('text,destination,purpose', [
    ('I go to the market.', 'the market', ''),
    ('I go to the market to buy supplies.', 'the market', 'buy supplies'),
    ('I approach the guard to ask about the patrol.', 'the guard', 'ask about the patrol'),
    ('I head toward the gate to speak with the watch.', 'the gate', 'speak with the watch'),
    ('I follow the road to investigate the smoke.', 'the road', 'investigate the smoke'),
    ('I move beside the wagon to inspect its wheels.', 'beside the wagon', 'inspect its wheels'),
    (TEXT, 'northwest of the crates', 'investigate the muddy footprints'),
    ('I go to the gate beside the road to inspect the cart by the wall.', 'the gate beside the road', 'inspect the cart by the wall'),
    ('I head to the market or the docks to buy rope.', 'the market or the docks', 'buy rope'),
    ('I go to the market in order to buy rope for the guard.', 'the market', 'buy rope for the guard'),
    ('I go to the road to the west.', 'the road to the west', ''),
    ('I head to the docks to rest.', 'the docks', 'rest'),
])
def test_extraction(text, destination, purpose):
    assert _destination_phrase(text) == destination
    assert _movement_and_purpose(text)[1] == purpose


@pytest.mark.parametrize('verb', ['investigate', 'examine', 'inspect', 'look for', 'search for', 'check'])
def test_inspection_cues(verb):
    assert _analyze_clause(f'I {verb} the tracks.', [])['operation'] == 'INSPECT'


def synthetic():
    scene = {'scene': {'id': 'square', 'exits': [
        dict(id='road', label='North road', target_scene_id='hill'),
        dict(id='market', label='Market', target_scene_id='market'),
    ], 'interactables': []}}
    session = {'active_scene_id': 'square', 'clue_knowledge': {
        'smoke_rumor': dict(state='discovered', text='Smoke rises beyond the crates.')
    }}
    return scene, session


def decide(text, scene, session):
    return deterministic_conversational_decision(player_text=text, scene=scene, world={}, session=session, log=[])


@pytest.mark.parametrize('variant', ['unique', 'multiple', 'hidden', 'invisible', 'locked', 'unavailable',
                                     'inaccessible', 'undiscovered', 'wrong_scene', 'missing', 'unrelated', 'similar'])
def test_route_authority(variant):
    scene, session = synthetic()
    route = scene['scene']['exits'][0]
    text = 'I head to the north road to investigate the smoke.'
    if variant == 'multiple':
        scene['scene']['exits'].append(dict(route, id='other', target_scene_id='other'))
    elif variant == 'hidden': route['hidden'] = True
    elif variant == 'invisible': route['visible'] = False
    elif variant == 'locked': route['locked'] = True
    elif variant == 'unavailable': route['available'] = False
    elif variant == 'inaccessible': route['accessible'] = False
    elif variant == 'undiscovered': route['conditions'] = {'requires_clues': ['unknown']}
    elif variant == 'wrong_scene': route['source_scene_id'] = 'elsewhere'
    elif variant == 'missing': scene['scene']['exits'] = []
    elif variant == 'unrelated':
        text = 'I head beyond the crates to investigate the diamonds.'
    elif variant == 'similar':
        route['label'] = 'Follow the smoke rumor'
        text = 'I head beyond the crates to investigate the smoke.'
    before = copy.deepcopy((scene, session))
    decision = decide(text, scene, session)
    assert (scene, session) == before
    assert decision.secondary_intentions[0]['status'] == 'pending'
    assert decision.proposed_operation == ('MOVE' if variant == 'unique' else None)
    if variant == 'unique':
        assert decision.authorization['route_decision'] == 'UNIQUE_AUTHORIZED_ROUTE'
    if variant in {'hidden', 'invisible', 'wrong_scene'}:
        assert 'North road' not in decision.player_facing_text
    if variant == 'similar':
        assert decision.reason == 'clue_route_clarification'
        assert not decision.requires_authoritative_execution


@pytest.mark.parametrize('variant', ['hidden', 'locked', 'undiscovered', 'wrong_scene'])
def test_bridge_rechecks_route(variant):
    scene, session = synthetic()
    route = scene['scene']['exits'][0]
    if variant == 'hidden': route['hidden'] = True
    if variant == 'locked': route['locked'] = True
    if variant == 'undiscovered': route['conditions'] = {'requires_clues': ['unknown']}
    if variant == 'wrong_scene': route['source_scene_id'] = 'elsewhere'
    record = _operation_record(operation='MOVE', target_id='road', player_text='I go to the road.')
    resolved, meta = normalized_action_from_interpretation(record, scene=scene, world={}, session=session,
                                                          player_text='I go to the road.', known_scene_ids=lambda: ['hill'])
    assert resolved is None and not meta['accepted']


@pytest.mark.parametrize('variant', ['cross_scene', 'invisible', 'inaccessible', 'unsupported', 'known_only'])
def test_inspection_cannot_use_knowledge_as_physical_access(variant):
    scene, session = synthetic()
    target = dict(id='tracks', label='Tracks', reveals_clue='physical_tracks')
    if variant in {'invisible', 'inaccessible'}:
        target['visible' if variant == 'invisible' else 'accessible'] = False
        scene['scene']['interactables'] = [target]
    # Cross-scene / unknown / known-only targets are absent from current scene.
    record = _operation_record(operation='INSPECT', target_id='tracks', player_text='I investigate the tracks.')
    before = copy.deepcopy((scene, session))
    result, meta = normalized_action_from_interpretation(record, scene=scene, world={}, session=session,
                                                       player_text='I investigate the tracks.')
    assert result is None and not meta['accepted']
    assert (scene, session) == before


def captured(n):
    p = Path('artifacts/atgb/pr_play_29/live/diagnostics') / f'response_{n:02}.json'
    d = json.loads(p.read_text())['response']
    return json.loads(next(c['text'] for o in d['output'] for c in o.get('content', []) if c.get('type') == 'output_text'))


def save(name, value):
    OUT.mkdir(exist_ok=True)
    (OUT/name).write_text(json.dumps(value, indent=2, default=str), encoding='utf-8')


def test_application_conversation_clarification_and_staged_control(opening_world, monkeypatch):
    root, manifest = load_baseline(Path.cwd())
    for name in manifest['files']:
        dest = st.DATA_DIR/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root/name, dest)
    monkeypatch.setenv('ASHEN_OPENING_RENDERER', '1')
    opening_calls = []
    _transport(monkeypatch, opening_calls, lambda kw: plan_selecting_required(kw['input']))
    calls, rows, resolver_traces = [], [], []
    skips = []
    skip_original = api.deterministic_provider_skip_line
    def skip_observer(**kw):
        result = skip_original(**kw)
        skips.append(dict(result=result, context=copy.deepcopy((kw.get('session') or {}).get('conversational_context'))))
        save('skip_trace.json', skips)
        return result
    monkeypatch.setattr(api, 'deterministic_provider_skip_line', skip_observer)
    import game.exploration as ex
    original = ex.resolve_exploration_action
    def observe(*args, **kwargs):
        result = original(*args, **kwargs)
        resolver_traces.append(copy.deepcopy(result))
        return result
    monkeypatch.setattr(ex, 'resolve_exploration_action', observe)
    if hasattr(api, 'resolve_exploration_action'):
        monkeypatch.setattr(api, 'resolve_exploration_action', observe)
    with TestClient(api.app) as client:
        opening = client.post('/api/start_campaign?ui_mode=player')
        assert opening.status_code == 200
        save('opening.json', dict(response=opening.json(), after=state(), mocked_selector_requests=opening_calls))
        _enable_live(monkeypatch)
        monkeypatch.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION', '1')
        narration = {'text': 'You arrive at the Old Milestone beside the northwest mud track.'}
        def gm(*args, **kwargs):
            return dict(player_facing_text=narration['text'], tags=[], scene_update=None,
                        activate_scene_id=None, new_scene_draft=None, world_updates=None,
                        suggested_action=None, debug_notes='PR-PLAY-31 deterministic narration mock')
        monkeypatch.setattr(api, 'call_gpt', gm)
        texts = ["I approach the tavern runner and ask what they're offering.",
                 'What sort of rumors have you heard?', TEXT,
                 'I go to Follow the missing patrol rumor.', 'I examine the footprints.',
                 'I examine the footprints.']
        for i, text in enumerate(texts):
            if i < 2:
                record = captured(2 if i == 0 else 4)
            else:
                record = _payload('IN_WORLD_ACTION', 'INTERPRETED', [('INSPECT', 'prints')])
                record['player_intent']['summary'] = text
                record['action_components'][0]['description'] = text
            _install_interpretation(monkeypatch, record, calls)
            if i >= 4:
                narration['text'] = ('Faint overlapping prints mark the mud around the old milestone, '
                                     'but their number, origin, and direction stay unclear.')
            before = state(); logs_before = st.load_log(); scene = st.load_active_scene()
            decision = deterministic_conversational_decision(player_text=text, scene=scene, world=before['world'], session=before['session'], log=logs_before)
            count = len(calls); started = time.perf_counter()
            reply = client.post('/api/chat?ui_mode=player', json={'text': text})
            after = state(); internal = st.load_log()[-1]
            def docs(s, logs):
                return {**{k+'.json': v for k, v in s.items()}, 'session_log.jsonl': logs,
                        'scenes/'+scene['scene']['id']+'.json': scene}
            a = action(); a.update(step_id=f'T{i+1}', player_input=text, subject_terms=['stew', 'rumors', 'patrol', 'prints', 'pending'], requires_substantive_answer=i < 2,
                                  interaction_category='interaction' if i < 2 else 'movement' if i == 3 else 'investigate',
                                  allowed_destinations=['old_milestone'] if i == 3 else [])
            evaluation = g.evaluate(a, reply.status_code, reply.json(), docs(before, logs_before), docs(after, st.load_log()), [])
            row = dict(turn=i+1, player=text, response=reply.json(), status=reply.status_code,
                       before=before, after=after, internal=internal, mock_interpretation=record,
                       router=decision.to_public_dict() if decision else None,
                       mocked_interpretation_calls=len(calls)-count, evaluation=evaluation,
                       state_diff=g.diff(docs(before, logs_before), docs(after, st.load_log())),
                       elapsed_seconds=time.perf_counter()-started)
            rows.append(row)
            save('integration.json', dict(turns=rows, resolver_traces=resolver_traces, live_provider_requests=0))
            assert reply.status_code == 200
            assert not evaluation['stop'], evaluation['findings']
            public_text = reply.json()['gm_output']['player_facing_text']
            for internal_id in ('muddy_footprints_northwest', 'milestone_mud_prints', 'leave_for_follow_the_missing_patrol_rumor'):
                assert internal_id not in public_text
            if i == 1:
                assert internal['resolution']['social']['topic_revealed']['id'] == 'patrol_rumor'
                assert 'muddy_footprints_northwest' in after['session']['clue_knowledge']
            if i == 2:
                assert decision.reason == 'clue_route_clarification'
                assert row['mocked_interpretation_calls'] == 0
                assert 'Follow the missing patrol rumor' in reply.json()['gm_output']['player_facing_text']
                assert before['character'] == after['character']
                assert before['world'] == after['world']
                assert before['session']['turn_counter'] == after['session']['turn_counter']
                assert before['session']['clue_knowledge'] == after['session']['clue_knowledge']
            if i == 3:
                assert after['session']['active_scene_id'] == 'old_milestone'
                assert 'milestone_mud_prints' not in after['session']['clue_knowledge']
                assert after['session']['conversational_context']['pending_clarification']['steps'][0]['text'] == 'investigate the muddy footprints'
                assert 'pending' in reply.json()['gm_output']['player_facing_text']
            if i >= 4:
                assert after['session']['active_scene_id'] == 'old_milestone'
                assert 'milestone_mud_prints' in after['session']['clue_knowledge']
                assert 'muddy_footprints_northwest' in after['session']['clue_knowledge']
            if i != 2:
                assert after['session']['turn_counter'] == before['session']['turn_counter'] + 1
                assert after['session']['clocks']['time_pressure'] == before['session']['clocks']['time_pressure'] + 1
        assert any(t['kind'] == 'discover_clue' and t.get('clue_id') == 'milestone_mud_prints' for t in resolver_traces)
        assert resolver_traces[-1]['kind'] == 'already_searched'


@pytest.mark.parametrize('purpose', ['inspect the footprints', 'buy supplies', 'rest'])
def test_explicit_route_executes_only_travel(tmp_path, monkeypatch, purpose):
    from tests.test_pr_ec_movement_partial_intent import _install_routes, _no_provider, _narrate
    from game.models import ChatRequest
    _install_routes(tmp_path, monkeypatch)
    _no_provider(monkeypatch); _narrate(monkeypatch)
    before = state()
    reply = api.chat(ChatRequest(text=f'I go to the docks to {purpose}.', ui_mode='player'))
    after = state()
    assert reply['resolution']['resolved_transition'] is True
    assert after['character'] == before['character']
    assert after['session'].get('clue_knowledge') == before['session'].get('clue_knowledge')
    assert after['session']['turn_counter'] == before['session']['turn_counter'] + 1
    pending = after['session']['conversational_context']['pending_clarification']
    assert pending['kind'] == 'deferred_intentions' and pending['steps'][0]['text'] == purpose
    assert 'pending' in reply['gm_output']['player_facing_text']


@pytest.mark.parametrize('verb,op,target,label', [('ask', 'ASK', 'tavern_runner', 'tavern runner'),
                                               ('investigate', 'INSPECT', 'notice_board', 'notice board')])
def test_to_purpose_local_approach(opening_world, verb, op, target, label):
    from game.local_interaction import normalize_local_approach
    from tests.test_pr_play_23_local_interaction import authored_scene
    scene = authored_scene()
    world = json.loads(Path('artifacts/pr_play_30/verified_fixture/world.json').read_text())
    text = f'I approach the {label} to {verb} about the patrol.'
    record = _payload('IN_WORLD_ACTION', 'INTERPRETED', [('MOVE', target), (op, target)])
    record['action_components'][0]['description'] = f'approach the {label}'
    result = normalize_local_approach(record, player_text=text, scene=scene, world=world, session=st.load_session())
    assert len(result['action_components']) == 1
    assert result['local_approach_normalization']['movement_executed'] is False


def test_failed_examination_cannot_discover(monkeypatch):
    import game.exploration as ex
    scene = {'scene': dict(id='square', exits=[], visible_facts=[],
                          interactables=[dict(id='tracks', label='tracks', reveals_clue='evidence')],
                          discoverable_clues=[dict(id='evidence', text='Authored physical marks.')])}
    session = {'active_scene_id': 'square'}
    monkeypatch.setattr(ex, 'should_trigger_check', lambda *a, **kw: dict(requires_check=True, skill='investigation', difficulty=20))
    monkeypatch.setattr(ex, 'resolve_skill_check', lambda *a, **kw: dict(success=False, roll=1, modifier=0, total=1, difficulty=20))
    before = copy.deepcopy(session)
    result = ex.resolve_exploration_action(scene, session, {}, dict(type='investigate', id='tracks', target_id='tracks', prompt='I examine the tracks.'),
                                           character={'name': 'Test'}, raw_player_text='I examine the tracks.')
    assert result['success'] is False
    assert not result['clue_id'] and not result['discovered_clues']
    assert session.get('clue_knowledge') == before.get('clue_knowledge')


@pytest.mark.parametrize('variant', ['valid', 'extra_overlay', 'other_scene_overlay', 'unknown_clue', 'hidden',
                                     'unavailable', 'failed', 'rejected_text', 'missing_resolution', 'wrong_scene',
                                     'unpersisted', 'unresolved_target', 'log_mismatch'])
def test_investigation_overlay_evaluator_fails_closed(variant):
    from tools.playtest.overlays import compare_overlays, empty_overlay
    scene = {'scene': dict(id='square', interactables=[dict(id='tracks', reveals_clue='evidence')],
                          discoverable_clues=[dict(id='evidence', text='Authored marks.')])}
    a = {'session.json': dict(campaign_started=True, active_scene_id='square', turn_counter=1,
                             runtime_scene_overlays={'square': empty_overlay('square')}),
         'session_log.jsonl': [], 'scenes/square.json': scene}
    res = dict(kind='discover_clue', success=True, action_id='tracks', interactable_id='tracks',
               clue_id='evidence', clue_text='Authored marks.', discovered_clues=['Authored marks.'])
    gm = dict(metadata={'accepted_response': dict(hard_validation=dict(hard_valid=True))})
    response = dict(resolution=copy.deepcopy(res), gm_output=copy.deepcopy(gm))
    b = copy.deepcopy(a); s = b['session.json']; s['turn_counter'] = 2
    s.update(clue_knowledge={'evidence': dict(state='discovered', text='Authored marks.')},
             scene_runtime={'square': dict(discovered_clue_ids=['evidence'], resolved_interactables=['tracks'])})
    s['runtime_scene_overlays']['square']['discovered_clues'] = ['Authored marks.']
    b['session_log.jsonl'] = [dict(player_input='I examine the tracks.', resolution=res, gm_output=gm)]
    if variant == 'extra_overlay': s['runtime_scene_overlays']['square']['state_flags']['free_reward'] = True
    if variant == 'other_scene_overlay': s['runtime_scene_overlays']['other'] = empty_overlay('other')
    if variant == 'unknown_clue': res['clue_id'] = response['resolution']['clue_id'] = 'invented'
    if variant == 'hidden': scene['scene']['interactables'][0]['hidden'] = True
    if variant == 'unavailable': scene['scene']['interactables'][0]['accessible'] = False
    if variant == 'failed': res['success'] = response['resolution']['success'] = False
    if variant == 'rejected_text': gm['metadata']['accepted_response']['hard_validation']['hard_valid'] = False
    if variant == 'missing_resolution': response['resolution'] = {}
    if variant == 'wrong_scene': s['active_scene_id'] = 'other'
    if variant == 'unpersisted': s['clue_knowledge'] = {}
    if variant == 'unresolved_target': s['scene_runtime']['square']['resolved_interactables'] = []
    if variant == 'log_mismatch': b['session_log.jsonl'][0]['player_input'] = 'I buy a sword.'
    result = compare_overlays(a, b, ordinary_action=dict(interaction_category='investigate', player_input='I examine the tracks.'), turn_response=response)
    assert result['integrity'] is (variant == 'valid')
