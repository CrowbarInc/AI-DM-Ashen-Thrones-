"""Offline resolver-to-player contract; all transports blocked by conftest."""
import copy
import json
import os
import shutil
from pathlib import Path
import pytest

from fastapi.testclient import TestClient
from game import api, storage
from tests.test_pr_play_42_evidence_boundaries import _patch_storage, _quiet, _post, _facing
from tests.test_pr_play_42_evidence_boundaries import _action
from game.defaults import default_session, default_world, default_character
from game.immutable_valid_response import run_preserve_if_valid, validate_generated_response
from game.authorized_information import revealed_information, supplement_revealed_information
from game.gm_resolution_decision import attach_gm_resolution_decision
from game.upstream_response_repairs import build_minimal_action_outcome_contract_repair_text

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'artifacts/atgb/pr_play_43/live/20261102T225835Z-b91e96381683'
OUT = ROOT / 'artifacts/pr_play_44'
NOTICE = 'I examine the notice board.'


def test_saved_43_notice_delivery(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    dest = tmp_path / 'data'
    shutil.rmtree(dest)
    shutil.copytree(RUN / 'turns/T3/before/persistent', dest)
    record = json.loads((RUN / 'turns/T3/record.json').read_text(encoding='utf-8'))
    captured = record['engine']['live_interpretation']['record']
    calls = _quiet(monkeypatch, {NOTICE: {'status': 'accepted', 'record': captured, 'provider_requests': []}})
    stages = {}
    skip = api.deterministic_provider_skip_line
    def capture_skip(**kwargs):
        result = skip(**kwargs)
        stages['host_selection'] = result
        return result
    monkeypatch.setattr(api, 'deterministic_provider_skip_line', capture_skip)
    build = api.build_messages
    def capture_context(*args, **kwargs):
        result = build(*args, **kwargs)
        stages['messages'] = result
        return result
    monkeypatch.setattr(api, 'build_messages', capture_context)
    before = copy.deepcopy(storage.load_session())
    with TestClient(api.app) as client:
        body = _post(client, NOTICE)
    resolution = storage.load_log()[-1]['resolution']
    after = storage.load_session()
    evidence = {
        'replay': 'Exact saved PR-PLAY-43 T3 pre-action persistent state; captured interpretation substituted offline.',
        'player_input': NOTICE, 'calls': calls, 'resolution': resolution,
        'before_session': before, 'after_session': after, 'response': body, 'stages': stages,
    }
    OUT.mkdir(exist_ok=True)
    phase = os.environ.get('PR_PLAY_44_EVIDENCE_PHASE', 'after')
    (OUT / f'{phase}_notice.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    assert calls['exploration'] == [True]
    assert calls['narration'] == []
    assert resolution['clue_id'] == 'notice_patrol_route'
    assert resolution['success'] is True
    assert resolution['clue_text'] in _facing(body)
    assert after['active_scene_id'] == before['active_scene_id']
    assert after['turn_counter'] == before['turn_counter'] + 1


@pytest.mark.parametrize('target,text', [
    ('ledger', 'The ledger records twelve copper ingots arriving, but only nine entered stock.'),
    ('tracks', 'The tracks may belong to a large animal; their species and direction remain unclear.'),
    ('mechanism', 'The left lever disengages the ratchet. The mechanism remains inactive.'),
])
def test_unfamiliar_scenes_deliver_only_selected_information(tmp_path, monkeypatch, target, text):
    _patch_storage(tmp_path, monkeypatch)
    for sid in ('frontier_gate', 'market_quarter'):
        storage._save_json(storage.scene_path(sid), {'scene': {'id': sid, 'location': sid, 'summary': 'Unused.', 'visible_facts': [], 'exits': [], 'interactables': []}})
    scene = {'scene': {
        'id': 'unfamiliar', 'location': 'Unfamiliar Site', 'summary': 'Rain darkens the stones.',
        'visible_facts': [f'A {target} is visible.'], 'exits': [],
        'interactables': [{'id': target, 'label': target, 'type': 'investigate', 'reveals_clue': 'selected'}],
        'discoverable_clues': [{'id': 'selected', 'text': text}, {'id': 'secret', 'text': 'SECRET merchant faction rendezvous'}],
        'hidden_facts': ['SECRET patron controls the faction'],
    }}
    storage._save_json(storage.scene_path('unfamiliar'), scene)
    session = storage.load_session()
    session.update(active_scene_id='unfamiliar', visited_scene_ids=['unfamiliar'], campaign_started=True)
    storage.save_session(session)
    player = f'I examine the {target}.'
    calls = _quiet(monkeypatch, {player: {'status': 'accepted', 'record': _action('INSPECT', target, player, recipient='CHARACTER', purpose='ACTION'), 'provider_requests': []}})
    contexts = []
    build = api.build_messages
    def capture(*args, **kwargs):
        messages = build(*args, **kwargs)
        contexts.append(messages)
        return messages
    monkeypatch.setattr(api, 'build_messages', capture)
    with TestClient(api.app) as client:
        body = _post(client, player)
        first_resolution = copy.deepcopy(storage.load_log()[-1]['resolution'])
        assert calls['narration'] == []
        repeat = _post(client, player)
    assert text in _facing(body)
    assert 'SECRET' not in _facing(body)
    assert 'concrete clue' not in _facing(repeat)
    assert storage.load_session()['active_scene_id'] == 'unfamiliar'
    # A repeated search is eligible for narration; _quiet supplies a hostile
    # controlled draft and the normal validators must keep its inventions out.
    assert 'moon_gate' not in json.dumps(storage.load_world())
    assert body['resolution'] == repeat['resolution'] == {}
    assert first_resolution['success'] is True
    assert storage.load_log()[-1]['resolution']['state_changes'].get('already_searched') is True
    (OUT / f'scenario_{target}.json').write_text(json.dumps({'first': body, 'repeat': repeat, 'calls': calls, 'contexts': contexts,
        'legacy_context_contains_hidden_canary': 'SECRET' in json.dumps(contexts)}, indent=2), encoding='utf-8')


def _resolved(text='The ledger lists twelve ingots, with three missing.'):
    return {'kind': 'discover_clue', 'success': True, 'clue_id': 'selected', 'clue_text': text,
            'discovered_clues': [text], 'interactable_id': 'ledger', 'action_id': 'ledger',
            'state_changes': {'clue_revealed': True}, 'metadata': {}}


@pytest.mark.parametrize('kind,changes', [
    ('investigate', {'skill_check_failed': True}),
    ('already_searched', {'already_searched': True}),
])
def test_failed_and_known_results_do_not_reveal_stale_information(kind, changes):
    result = {**_resolved(), 'kind': kind, 'success': False, 'state_changes': changes}
    assert revealed_information(result) == []
    line = build_minimal_action_outcome_contract_repair_text(player_input='I inspect the ledger.', resolution=result)
    assert result['clue_text'] not in line
    assert 'concrete clue' not in line


def test_multiple_authorized_results_preserve_partial_uncertainty_and_exclude_secrets():
    result = _resolved('These may be animal tracks.')
    result['discovered_clues'].append('Neither species nor direction can be determined.')
    result['metadata']['hidden_faction'] = 'SECRET faction rendezvous'
    result['hidden_clues'] = ['SECRET creature identity']
    projected = revealed_information(result)
    assert len(projected) == 2
    assert 'SECRET' not in json.dumps(projected)
    line, added = supplement_revealed_information('You study the mud.', result)
    assert len(added) == 2
    assert 'Neither species nor direction' in line
    assert supplement_revealed_information(line, result) == (line, [])


def test_controlled_narration_texture_and_omission_before_sealing():
    from game.live_resolution import attach_interaction_obligation
    scene = {'scene': {'id': 'archive', 'location': 'Archive', 'summary': 'Rain falls outside.', 'visible_facts': ['A ledger rests on the table.'], 'interactables': [{'id': 'ledger', 'label': 'ledger'}]}}
    resolution = _resolved()
    session = default_session()
    attach_interaction_obligation(resolution, player_text='I inspect the ledger.', session=session,
        normalized_action={'type': 'investigate', 'target_id': 'ledger'}, scene_id='archive', scene=scene,
        world=default_world(), visible_turns=[], enable_model_interpretation=False)
    attach_gm_resolution_decision(resolution, session=session, scene=scene, world=default_world())
    before = copy.deepcopy(resolution)
    gm = run_preserve_if_valid({'player_facing_text': 'Rain falls outside as you study the ledger.', 'metadata': {}},
        regenerate=None, resolution=resolution, player_text='I inspect the ledger.', scene=scene, session=session, world=default_world())
    assert resolution['clue_text'] in gm['player_facing_text']
    assert 'Rain falls outside' in gm['player_facing_text']
    assert gm['metadata']['accepted_response']['immutable'] is True
    assert resolution == before
    (OUT / 'controlled_narration.json').write_text(json.dumps(gm, indent=2), encoding='utf-8')


def test_blocked_travel_contradiction_is_rejected_and_state_unchanged():
    result = {'kind': 'travel', 'success': False, 'resolved_transition': False, 'target_scene_id': 'tower'}
    before = copy.deepcopy(result)
    verdict = validate_generated_response('You arrive at the tower.', resolution=result)
    assert verdict['hard_valid'] is False
    assert result == before


def test_provider_unavailable_fallback_retains_discovery():
    from game.immutable_valid_response import safe_nonresolution
    result = _resolved()
    before = copy.deepcopy(result)
    text = safe_nonresolution({'operation': 'inspect'}, resolution=result)
    assert result['clue_text'] in text
    assert result == before


def test_contradictory_discovery_draft_falls_back_without_losing_information():
    from game.live_resolution import attach_interaction_obligation
    scene = {'scene': {'id': 'archive', 'location': 'Archive', 'visible_facts': ['A ledger is visible.'], 'interactables': [{'id': 'ledger', 'label': 'ledger'}]}}
    result = _resolved()
    session = default_session()
    attach_interaction_obligation(result, player_text='I inspect the ledger.', session=session,
        normalized_action={'type': 'investigate', 'target_id': 'ledger'}, scene_id='archive', scene=scene,
        world=default_world(), visible_turns=[], enable_model_interpretation=False)
    attach_gm_resolution_decision(result, session=session, scene=scene, world=default_world())
    before = copy.deepcopy(result)
    output = run_preserve_if_valid({'player_facing_text': 'You receive fifty gold coins and a silver key.', 'metadata': {}},
        regenerate=None, resolution=result, player_text='I inspect the ledger.', scene=scene, session=session, world=default_world())
    baseline_verdict = validate_generated_response('You receive fifty gold coins and a silver key.',
        resolution=result, decision=result['metadata']['gm_resolution_decision'])
    (OUT / 'contradiction.json').write_text(json.dumps({'output': output, 'unsupplemented_validator_verdict': baseline_verdict}, indent=2), encoding='utf-8')
    assert result['clue_text'] in output['player_facing_text']
    assert 'fifty gold' not in output['player_facing_text']
    assert result == before
    (OUT / 'contradiction.json').write_text(json.dumps(output, indent=2), encoding='utf-8')


def test_legacy_narrator_context_excludes_hidden_information():
    """Known open contract gap, retained as a failing probe rather than xfailed."""
    from game.defaults import default_campaign, default_combat, default_scene
    from game.gm import build_messages
    scene = default_scene('frontier_gate')
    scene['scene']['hidden_facts'] = ['SECRET unobserved faction rendezvous']
    scene['scene']['discoverable_clues'] = [{'id': 'unseen', 'text': 'SECRET undiscovered clue'}]
    messages = build_messages(default_campaign(), default_world(), default_session(), default_character(),
        scene, default_combat(), [], 'I inspect the ledger.', _resolved())
    (OUT / 'legacy_hidden_context.json').write_text(json.dumps(messages, indent=2), encoding='utf-8')
    assert 'SECRET' not in json.dumps(messages)


def test_failed_synthetic_check_reveals_nothing(monkeypatch):
    import game.exploration as exploration
    scene = {'scene': {'id': 'vault', 'location': 'Vault', 'visible_facts': ['A cipher plate hangs on the wall.'],
        'interactables': [{'id': 'plate', 'label': 'cipher plate', 'type': 'investigate', 'reveals_clue': 'cipher', 'skill_check': {'skill_id': 'investigation', 'dc': 18}}],
        'discoverable_clues': [{'id': 'cipher', 'text': 'SECRET opening sequence'}]}}
    monkeypatch.setattr(exploration, 'should_trigger_check', lambda *_args, **_kw: {'requires_check': True, 'skill': 'investigation', 'difficulty': 18})
    monkeypatch.setattr(exploration, 'resolve_skill_check', lambda *_args, **_kw: {'success': False, 'roll': 2, 'modifier': 0, 'total': 2, 'difficulty': 18})
    session = default_session()
    result = exploration.resolve_exploration_action(scene, session, default_world(),
        {'id': 'plate', 'type': 'investigate', 'target_id': 'plate', 'prompt': 'I examine the cipher plate.'},
        raw_player_text='I examine the cipher plate.', character=default_character())
    assert result['success'] is False
    assert result['discovered_clues'] == []
    line = build_minimal_action_outcome_contract_repair_text(player_input='I examine the cipher plate.', resolution=result)
    assert 'SECRET' not in line
    assert 'fails' in line


def test_synthetic_npc_information_delivery(tmp_path, monkeypatch):
    from tests.test_pr_play_42_evidence_boundaries import _market, _people
    _patch_storage(tmp_path, monkeypatch)
    for sid in ('frontier_gate', 'market_quarter'):
        storage._save_json(storage.scene_path(sid), {'scene': {'id': sid, 'location': sid, 'summary': 'Unused.', 'visible_facts': [], 'exits': []}})
    scene = _market(['Mira the merchant trades rumors from a blue stall.'])
    scene['scene']['exits'] = []
    storage._save_json(storage.scene_path('salt_market'), scene)
    world = _people()
    topic = 'Mira heard the ferryman stops service at sunset because the mooring rope is frayed.'
    world['npcs'][0]['topics'] = [{'id': 'ferry_news', 'discovery_categories': ['rumor'], 'text': topic}]
    world['npcs'][0]['hidden_motivation'] = 'SECRET sabotage'
    storage._save_json(storage.WORLD_PATH, world)
    session = storage.load_session()
    session.update(active_scene_id='salt_market', visited_scene_ids=['salt_market'], campaign_started=True)
    storage.save_session(session)
    player = 'Have you heard any interesting rumors lately?'
    _quiet(monkeypatch, {player: {'status': 'accepted', 'record': _action('ASK', 'mira_merchant', player, recipient='NPC', purpose='QUESTION'), 'provider_requests': []}})
    with TestClient(api.app) as client:
        body = _post(client, player)
    (OUT / 'scenario_npc.json').write_text(json.dumps(body, indent=2), encoding='utf-8')
    assert topic.casefold() in _facing(body).casefold()
    assert 'SECRET' not in _facing(body)
    (OUT / 'scenario_npc.json').write_text(json.dumps(body, indent=2), encoding='utf-8')


def test_npc_and_travel_from_saved_43(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    dest = tmp_path / 'data'
    shutil.rmtree(dest)
    shutil.copytree(RUN / 'turns/T2/before/persistent', dest)
    record = json.loads((RUN / 'turns/T2/record.json').read_text(encoding='utf-8'))['engine']['live_interpretation']['record']
    rumor = 'Have you heard any interesting rumors lately?'
    calls = _quiet(monkeypatch, {rumor: {'status': 'accepted', 'record': record, 'provider_requests': []}})
    with TestClient(api.app) as client:
        body = _post(client, rumor)
        rumor_resolution = copy.deepcopy(storage.load_log()[-1]['resolution'])
        moved = _post(client, 'I want to follow the trail connected to the missing patrol.')
    assert body['resolution'] == moved['resolution'] == {}
    assert rumor_resolution['social']['topic_revealed']['text'].casefold() in _facing(body).casefold()
    assert storage.load_log()[-1]['resolution']['target_scene_id'] == 'old_milestone'
    assert 'Old Milestone' in _facing(moved)
    assert calls['narration'] == []
    (OUT / 'npc_travel.json').write_text(json.dumps({'npc': body, 'travel': moved, 'calls': calls}, indent=2), encoding='utf-8')
