"""Offline boundary matrix; conftest blocks all real provider transports."""
import copy
import json
import time
from pathlib import Path

import pytest
from game import gm
from game.defaults import (default_campaign, default_world, default_session,
                           default_character, default_combat)
from game.immutable_valid_response import validate_generated_response, run_preserve_if_valid
from game.mechanical_claims import audit_mechanical_claims, mechanical_outcome

OUT = Path(__file__).resolve().parents[1] / 'artifacts/pr_play_45'
CLUE = 'The tracks may belong to a large animal; species and direction remain unclear.'


def result(**kwargs):
    return {'kind': 'investigate', 'success': True, 'state_changes': {}, **kwargs}


def discovery():
    return result(kind='discover_clue', clue_text=CLUE, discovered_clues=[CLUE],
                  state_changes={'clue_revealed': True})


def messages(monkeypatch, outcome=None, known=False):
    scene = {'scene': {'id': 'observatory', 'location': 'Observatory',
        'summary': 'Rain darkens the stones.', 'visible_facts': ['A brass dial stands on a plinth.'],
        'hidden_facts': ['CANARY_PRIVATE_PATRON'], 'gm_notes': ['CANARY_GM_NOTE'],
        'discoverable_clues': [{'id': 'tracks', 'text': CLUE},
                               {'id': 'secret', 'text': 'CANARY_UNSEEN_CHAMBER'}],
        'exits': [], 'interactables': [{'id': 'dial', 'label': 'dial',
                                       'secret_motivation': 'CANARY_INTERACTABLE'}]}}
    monkeypatch.setattr(gm, 'get_effective_scene', lambda *_: scene)
    session = default_session()
    session.update(active_scene_id='observatory', campaign_started=True)
    world = default_world()
    world['event_log'] = ['CANARY_UNOBSERVED_EVENT']
    world['world_state'] = {'clocks': {'private': {'value': 3, 'description': 'CANARY_CLOCK'}}}
    campaign = default_campaign()
    campaign['gm_guidance'] = ['CANARY_GUIDANCE']
    campaign['world_pressures'] = ['CANARY_PRESSURE']
    runtime = {'discovered_clues': [CLUE]} if known else {}
    return gm.build_messages(campaign, world, session, default_character(), scene,
        default_combat(), [], 'I examine the dial.', outcome or result(), scene_runtime=runtime)


def checked(text, outcome, accepted):
    before = copy.deepcopy(outcome)
    verdict = validate_generated_response(text, resolution=outcome)
    assert verdict['hard_valid'] is accepted, verdict
    assert outcome == before
    return verdict


def fallback(text, outcome):
    state = {'inventory': [], 'currency': 0, 'hp': 12, 'active_scene_id': 'observatory'}
    before = copy.deepcopy((outcome, state))
    retries = []
    output = run_preserve_if_valid({'player_facing_text': text, 'metadata': {}},
        resolution=outcome, player_text='I examine the dial.', regenerate=lambda _: retries.append(True))
    assert (outcome, state) == before
    assert retries == []
    assert text in output['metadata']['rejected_mechanical_draft']
    return output


def test_A_hidden_clue_isolation(monkeypatch):
    ms = messages(monkeypatch)
    (OUT / 'isolation_attempt.json').write_text(json.dumps(ms, indent=2), encoding='utf-8')
    assert 'CANARY_' not in json.dumps(ms)
    assert 'brass dial' in json.dumps(ms)
    OUT.mkdir(exist_ok=True)
    (OUT / 'isolated_messages.json').write_text(json.dumps(ms, indent=2), encoding='utf-8')


def test_B_gm_notes_isolation(monkeypatch):
    ms = messages(monkeypatch)
    assert 'CANARY_GM_NOTE' not in json.dumps(ms)
    assert 'Rain darkens' in json.dumps(ms)


def test_C_newly_revealed_clue(monkeypatch):
    payload = json.loads(messages(monkeypatch, discovery())[-1]['content'])
    assert payload['authorized_information'][0]['text'] == CLUE
    output = fallback('You receive a jeweled cup.', discovery())
    assert CLUE in output['player_facing_text']


def test_D_previously_known_information(monkeypatch):
    payload = json.loads(messages(monkeypatch, result(kind='already_searched'), known=True)[-1]['content'])
    assert CLUE in json.dumps(payload['scene']['discovered_clues'])
    assert payload['authorized_information'] == []


def test_E_unsupported_inventory_gain():
    checked('You receive a silver key.', result(), False)
    assert 'silver key' not in fallback('You receive a silver key.', result())['player_facing_text']


def test_F_unsupported_currency_gain():
    checked('You collect fifty gold coins.', result(), False)
    assert 'fifty gold' not in fallback('You collect fifty gold coins.', result())['player_facing_text']


def test_G_supported_inventory_gain():
    checked('You receive a silver key.', result(state_changes={'items_added': [{'id': 'silver_key', 'name': 'silver key'}]}), True)


def test_H_unsupported_damage():
    checked('You suffer 4 damage.', result(), False)
    fallback('You suffer 4 damage.', result())


def test_I_supported_damage():
    checked('You suffer 4 damage.', result(kind='enemy_attack', combat={'damage_dealt': 4}), True)


def test_J_unsupported_travel():
    r = result(kind='travel', success=False, resolved_transition=False, target_scene_id='glass_hall')
    checked('You arrive at the glass hall.', r, False)
    fallback('You arrive at the glass hall.', r)


def test_K_supported_travel():
    checked('You arrive at the glass hall.', result(kind='travel', resolved_transition=True, target_scene_id='glass_hall'), True)


def test_L_unsupported_clue_discovery():
    checked('You discover a secret chamber.', result(), False)


def test_M_atmospheric_texture():
    checked('Rain patters on the stone, dust stirs, and footsteps echo.', result(), True)


def test_N_figurative_language():
    checked('The sunset glows like gold; the silence feels like a wound. Your thoughts travel like birds.', result(), True)


def test_O_npc_speculation():
    checked('The sailor says, "Perhaps you receive a silver key if you return tomorrow."', result(), True)


def test_P_mixed_claims_preserve_clue():
    text = CLUE + ' You receive a silver key.'
    output = fallback(text, discovery())
    assert CLUE in output['player_facing_text']
    assert 'silver key' not in output['player_facing_text']
    (OUT / 'rejection_fallback.json').write_text(json.dumps(output, indent=2), encoding='utf-8')


@pytest.mark.parametrize('scenario,outcome,good,bad', [
    ('merchant', result(state_changes={'items_added': ['linen cloak'], 'currency_spent': ['3 copper coins']}),
     'You receive a linen cloak. You spend 3 copper coins.', 'You receive a bonus ruby.'),
    ('wilderness', result(state_changes={'damage_taken': 3}), 'You suffer 3 damage.', 'You suffer 7 damage.'),
    ('dungeon', result(), 'Dust hangs over the brass dial.', 'You discover a secret staircase.'),
    ('conversation', result(kind='social'), 'The sailor says, "I saw the ferry at dusk."', 'You receive a compass.'),
    ('failed_travel', result(kind='travel', success=False), 'The route remains blocked.', 'You arrive at the ice lake.'),
    ('partial_discovery', discovery(), CLUE, 'The tracks definitely belong to wolves.'),
])
def test_cross_scenario(scenario, outcome, good, bad):
    checked(good, outcome, True)
    checked(bad, outcome, False)


@pytest.mark.parametrize('text', [
    'You lose a rope.', 'You spend 5 copper coins.', 'You regain 5 health.',
    'You become poisoned.', 'You are no longer poisoned.', 'You unlock the west route.',
    'You complete the rescue objective.', 'Two hours pass.', 'Combat begins.',
    'The ferryman dies.', 'The basalt guild declares war.',
    'You receive a silver key and you collect fifty gold coins.',
    'You suffer 5 damage but you receive a key.',
    'A silver key is added to your inventory.',
    'The merchant hands you a compass.',
    'You now own a jeweled cup.',
    'Arden receives a silver key.',
])
def test_additional_unsupported_categories(text):
    checked(text, result(), False)


@pytest.mark.parametrize('text', [
    'Gold light falls on the door.', 'You see a silver key on a shelf.',
    'If you receive a key, the door could open.', 'You do not receive a silver key.',
    'You receive a glimpse of the horizon.',
])
def test_nonchanges(text):
    checked(text, result(), True)


def test_supported_does_not_grant_extra_amount_or_item():
    r = result(state_changes={'items_added': ['linen cloak'], 'currency_gained': ['5 gold coins']})
    checked('You collect 50 gold coins.', r, False)
    checked('You receive a linen cloak and a ruby.', r, False)
    checked('You collect five gold coins.', r, True)


def test_deterministic_overhead():
    start = time.perf_counter()
    for _ in range(1000):
        audit_mechanical_claims('Rain falls. You receive a silver key.', result())
    (OUT / 'validation_timing.json').write_text(json.dumps({
        'iterations': 1000, 'elapsed_seconds': time.perf_counter() - start,
        'method': 'local wall time; not a latency guarantee'}), encoding='utf-8')


def test_synthetic_transaction_applies_once_then_narration_is_read_only():
    character = {'inventory': [], 'coins': 8}
    def resolve_exchange():
        character['coins'] -= 3
        character['inventory'].append({'id': 'linen_cloak', 'name': 'linen cloak'})
        return result(state_changes={'items_added': ['linen cloak'], 'currency_spent': ['3 copper coins']})
    outcome = resolve_exchange()
    before = copy.deepcopy((character, outcome))
    output = run_preserve_if_valid({'player_facing_text': 'You receive a linen cloak. You spend 3 copper coins.', 'metadata': {}},
        resolution=outcome, player_text='I buy the cloak.', regenerate=None)
    assert output['metadata']['accepted_response']['immutable'] is True
    assert (character, outcome) == before
    assert character['coins'] == 5 and len(character['inventory']) == 1
    (OUT / 'transaction_integrity.json').write_text(json.dumps({'before_narration': before,
        'after_narration': [character, outcome], 'output': output}, indent=2), encoding='utf-8')


def test_production_damage_is_not_applied_twice(monkeypatch):
    from game.combat import enemy_take_turn
    from game.defaults import default_conditions
    import game.combat as combat_engine
    enemy = {'id': 'thorn_beast', 'name': 'Thorn Beast', 'conditions': [],
             'attacks': [{'name': 'Claw', 'attack_bonus': 5,
                          'damage': {'dice_count': 1, 'dice_sides': 4, 'bonus': 0}}]}
    scene = {'scene': {'enemies': [enemy]}}
    character = default_character()
    monkeypatch.setattr(combat_engine, 'roll_die', lambda sides: 18 if sides == 20 else 3)
    outcome = enemy_take_turn(character, scene, {'active_actor_id': 'thorn_beast'}, default_conditions())
    assert character['hp']['current'] == 5
    before = copy.deepcopy((character, scene, outcome))
    checked('You suffer 3 damage.', outcome, True)
    checked('You suffer 5 damage.', outcome, False)
    assert (character, scene, outcome) == before


def test_npc_private_profile_cannot_bypass_projection(monkeypatch):
    from tests.test_prompt_context import _narration_minimal_kwargs
    from game.prompt_context import build_narration_context
    kwargs = _narration_minimal_kwargs()
    kwargs['session'].update(turn_counter=4, interaction_context={'active_interaction_target_id': 'sailor'})
    kwargs['world']['npcs'] = [{'id': 'sailor', 'name': 'Sailor', 'location': 'frontier_gate',
        'knowledge_scope': ['CANARY_PRIVATE_KNOWLEDGE'], 'current_agenda': 'CANARY_PRIVATE_AGENDA',
        'affiliation': 'CANARY_PRIVATE_FACTION', 'hidden_motivation': 'CANARY_PRIVATE_MOTIVE'}]
    payload = build_narration_context(**kwargs)
    assert 'CANARY_' not in json.dumps(payload)


def test_provider_declarations_and_private_metadata_cannot_grant_effects():
    outcome = result(metadata={'items_added': ['silver key']}, hint='You receive a silver key.')
    verdict = validate_generated_response('You receive a silver key.', resolution=outcome,
                                          declared_claims=[{'text': 'You receive a silver key.'}])
    assert verdict['hard_valid'] is False


def test_mechanical_retry_is_rejected_without_sentence_salvage():
    retries = []
    def regenerate(_):
        retries.append(True)
        return {'player_facing_text': 'Rain falls. You receive a silver key.', 'metadata': {}}
    output = run_preserve_if_valid({'player_facing_text': 'The secret is a private plan.', 'metadata': {}},
        player_text='I examine the dial.', resolution=discovery(), regenerate=regenerate)
    assert retries == [True]
    assert 'silver key' not in output['player_facing_text']
    assert CLUE in output['player_facing_text']
    assert output['metadata']['rejected_provider_output'] == 'Rain falls. You receive a silver key.'


@pytest.mark.parametrize('changes,text', [
    ({'health_recovered': 3}, 'You recover 3 health.'),
    ({'conditions_applied': ['poisoned']}, 'You become poisoned.'),
    ({'conditions_removed': ['poisoned']}, 'You are no longer poisoned.'),
    ({'routes_unlocked': ['west route']}, 'You unlock the west route.'),
    ({'objectives_completed': ['rescue objective']}, 'You complete the rescue objective.'),
    ({'time_advanced': 'two hours'}, 'Two hours pass.'),
])
def test_supported_additional_categories(changes, text):
    checked(text, result(state_changes=changes), True)


def test_nested_planner_clock_and_pressure_are_excluded():
    from game.narration_authorization import project_narration_payload
    value = {'narrative_plan': {'active_pressures': {'world_pressure': {'plot': 'CANARY_OFFSCREEN'},
                                                   'clock_summaries': ['CANARY_CLOCK']}}}
    before = copy.deepcopy(value)
    projected = project_narration_payload(value, result())
    assert 'CANARY_' not in json.dumps(projected)
    assert projected['narrative_plan']['active_pressures'] == {'world_pressure': None, 'clock_summaries': []}
    assert value == before
