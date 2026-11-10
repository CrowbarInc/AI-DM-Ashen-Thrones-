"""PR-PLAY-25: offline authority, expression, HTTP publication and state checks."""
import copy
import importlib.util
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import api, storage as st
from game.dialogue_authority import attach_dialogue_authority, build_dialogue_authority, select_host_speech
from game.expressive_dialogue import build_expression_contract, validate_expression
from game.public_fact_dialogue import select_public_offering
from game.social import _next_topic_to_reveal
from tests.test_pr_play_04_opening_integrity import opening_world
from tests.test_pr_play_18_contract_alignment import _transport
from tests.test_pr_play_23_local_interaction import TEXT, raw_captured, state
from tests.test_pr_dy_live_gameplay import _enable_live, _install_interpretation
from game.opening_presentation_renderer import plan_selecting_required

EVIDENCE = Path('artifacts/pr_play_25')


def save(name, value):
    if os.environ.get('ASHEN_PR_PLAY_25_EVIDENCE') == '1':
        (EVIDENCE / name).write_text(json.dumps(value, indent=2, default=str), encoding='utf-8')


def fixture(name='Tavern Runner', items='hot stew and rumors', verb='offers'):
    npc = dict(id='seller', name=name, location='square', topics=[dict(id='weather', text='Rain falls at dusk.')])
    scene = {'scene': dict(id='square', visible_facts=[f'The {name.lower()} {verb} {items}.'],
                          hidden_facts=['SYNTHETIC_SECRET'], addressables=[
        dict(id='seller', name=name, kind='npc', scene_id='square', addressable=True)])}
    social = dict(npc_id='seller', npc_name=name, target_resolved=True, reply_plan_kind='genuine_uncertainty')
    return npc, scene, social


def authority(npc, scene, social, question):
    attach_dialogue_authority(social, question, npc, {}, scene)
    return social['dialogue_authority']


def test_original_reproduction():
    root = Path('artifacts/atgb/pr_play_24/live/turns/T1/before/persistent')
    scene = json.loads((root/'scenes/frontier_gate.json').read_text())
    world = json.loads((root/'world.json').read_text())
    npc = next(n for n in world['npcs'] if n['id'] == 'tavern_runner')
    before = copy.deepcopy((scene, npc))
    selection = {}
    assert _next_topic_to_reveal(npc, {}, player_text=TEXT, selection=selection) is None
    spec = importlib.util.spec_from_file_location('pr_play_25_before', EVIDENCE/'dialogue_authority.before.py')
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    social = dict(npc_id=npc['id'], npc_name=npc['name'], target_resolved=True, reply_plan_kind='genuine_uncertainty')
    previous = old.build_dialogue_authority(TEXT, npc=npc, scene=scene, social=social)
    assert not previous['authorized_proposition']
    assert old.select_host_speech({'social': dict(social, dialogue_authority=previous)}, player_text=TEXT)[0] == 'Tavern Runner says, "I couldn\'t tell you."'
    repaired = authority(npc, scene, social, TEXT)
    assert repaired['authorized_proposition'] == 'I offer hot stew and rumors.'
    assert (scene, npc) == before
    save('original_reproduction.json', dict(question=TEXT, npc=npc, scene=scene, topic_selection=selection,
                                          before=previous, after=repaired, live_provider_requests=0))


@pytest.mark.parametrize('name,items,verb,question', [
    ('Tavern Runner', 'hot stew and rumors', 'trades', 'What are you offering?'),
    ('Merchant', 'bread and lantern oil', 'sells', 'What do you sell?'),
    ('Innkeeper', 'rooms and breakfast', 'offers', 'What services do you offer?'),
    ('Potter', 'clay bowls', 'sells', "What's available?"),
    ('Cook', 'roast vegetables', 'serves', 'What are you serving?'),
])
def test_generalization(name, items, verb, question):
    npc, scene, social = fixture(name, items, verb)
    before = copy.deepcopy((npc, scene))
    result = authority(npc, scene, social, question)
    assert result['authorized_proposition'] == f'I offer {items}.'
    assert result['authorization_provenance']['source_id'] == 'scene:square:visible:0'
    assert result['authorization_provenance']['authority_category'] == 'world_source'
    assert (npc, scene) == before


@pytest.mark.parametrize('variant', ['unrelated', 'hidden', 'price', 'reward', 'empty', 'ambiguous_name',
    'ambiguous_facts', 'cross_scene', 'not_addressable', 'negated', 'quoted', 'conditional', 'extra_question',
    'restricted', 'restricted_item', 'conflict', 'provider_evidence', 'target_mismatch'])
def test_conservative_selection(variant):
    npc, scene, social = fixture()
    question = 'What are you offering?'
    env = scene['scene']
    if variant == 'unrelated':
        env['visible_facts'] = ['The merchant sells bread and lantern oil.']
    elif variant == 'hidden': question = 'Who do you secretly work for?'
    elif variant == 'price': question = 'How much does the stew cost?'
    elif variant == 'reward': question = 'What reward will you pay?'
    elif variant == 'empty': env['visible_facts'] = []
    elif variant == 'ambiguous_name': env['addressables'].append(dict(env['addressables'][0], id='other'))
    elif variant == 'ambiguous_facts': env['visible_facts'].append('The tavern runner sells bread.')
    elif variant == 'cross_scene': npc['location'] = 'elsewhere'
    elif variant == 'not_addressable': env['addressables'][0]['addressable'] = False
    elif variant == 'negated': env['visible_facts'] = ['The tavern runner does not offer stew.']
    elif variant == 'quoted': env['visible_facts'] = ['A guard says the tavern runner offers stew.']
    elif variant == 'conditional': env['visible_facts'] = ['The tavern runner offers stew if paid.']
    elif variant == 'extra_question': question = 'What are you offering and how much does it cost?'
    elif variant == 'provider_evidence':
        env['visible_facts'] = []
        social['public_conversation_evidence'] = {'visible:0': 'The tavern runner offers stew.'}
    elif variant == 'target_mismatch': social['npc_id'] = 'someone_else'
    elif variant in {'restricted', 'restricted_item'}:
        npc['topics'].append(dict(id='secret', text='I offer hot stew.' if variant == 'restricted' else 'The stew is private.', disclosure='restricted'))
    elif variant == 'conflict':
        npc['topics'].append(dict(id='other', text='I sell bread.'))
    record = authority(npc, scene, social, question)
    assert not record.get('public_fact_source')
    assert not record['authorized_proposition']
    save('negative_' + variant + '.json', dict(authority=record, question=question))


def test_authored_source_precedence():
    npc, scene, social = fixture()
    topic = dict(id='offerings', text='I sell bread.')
    npc['topics'].append(topic)
    social['topic_revealed'] = topic
    record = authority(npc, scene, social, 'What do you sell?')
    assert record['authorized_proposition'] == topic['text']
    assert not record['public_fact_source']


def test_other_registered_npc_does_not_receive_merchants_offerings():
    npc, scene, social = fixture('Guard')
    scene['scene']['visible_facts'] = ['The merchant sells bread and lantern oil.']
    scene['scene']['addressables'].append(dict(id='merchant', name='Merchant', kind='npc',
                                              scene_id='square', addressable=True))
    assert not authority(npc, scene, social, 'What do you sell?')['authorized_proposition']
    assert not authority(npc, scene, social, 'What is the merchant selling?')['authorized_proposition']


@pytest.mark.parametrize('candidate,accepted', [
    ("I've got hot stew and rumors.", True), ('I serve hot stew and rumors.', True),
    ('I sell hot stew and rumors for three copper.', False),
    ("I've got hot stew and rumors and a map to the missing patrol.", False),
    ('I offer hot stew and rumors and will pay a reward.', False),
    ("I don't offer hot stew and rumors.", False),
])
def test_expression(candidate, accepted):
    npc, scene, social = fixture()
    question = 'What are you offering?'
    authority(npc, scene, social, question)
    resolution = {'social': social}
    line, source = select_host_speech(resolution, player_text=question)
    contract = build_expression_contract(player_text=question, speaker_name=npc['name'], speaker_id=npc['id'],
                                         fallback_line=line, fallback_source=source, resolution=resolution)
    verdict = validate_expression(candidate, contract)
    save('expression_' + str(accepted) + '_' + str(len(candidate)) + '.json', dict(contract=contract, candidate=candidate, verdict=verdict))
    assert verdict['adopt'] == accepted, verdict


@pytest.mark.parametrize('case', ['offerings', 'host', 'price', 'unknown', 'embellishment', 'secret'])
def test_offline_opening_to_http(opening_world, monkeypatch, case):
    monkeypatch.setenv('ASHEN_OPENING_RENDERER', '1')
    _transport(monkeypatch, [], lambda kw: plan_selecting_required(kw['input']))
    secret = 'PR_PLAY_25_HIDDEN_SENTINEL'
    world = st.load_world()
    world['internal_state'] = {'secret': secret}
    st.save_world(world)
    # The shared opening fixture substitutes opening prose for visible facts.
    # Restore the actual captured public facts before rendering/initialization.
    scene = st.load_active_scene()
    captured_scene = json.loads(Path('artifacts/atgb/pr_play_24/live/turns/T1/before/persistent/scenes/frontier_gate.json').read_text())
    scene['scene']['visible_facts'] = captured_scene['scene']['visible_facts']
    st._save_json(st.scene_path(scene['scene']['id']), scene)
    with TestClient(api.app) as client:
        opening = client.post('/api/start_campaign?ui_mode=player')
        assert opening.status_code == 200
        assert 'hot stew' in opening.json()['gm_output']['player_facing_text'].lower()
        before = state()
        scene_before = st.load_active_scene()
        _enable_live(monkeypatch)  # Enables the adapter under synthetic transport only.
        record = raw_captured()
        text = TEXT
        if case not in {'offerings', 'host', 'embellishment'}:
            text = 'I ask the tavern runner ' + {'price': 'how much the stew costs.', 'unknown': 'about their favorite constellation.',
                    'secret': 'who they secretly work for.'}[case]
            record['action_components'] = record['action_components'][1:]
            record['action_components'][0]['description'] = text
            record['communication']['evidence_refs'] = []
            record['communication']['subject'] = text
            record['player_intent']['summary'] = text
            record['requested_outcomes'] = [{'text': text}]
        calls = []
        _install_interpretation(monkeypatch, record, calls)
        monkeypatch.setattr(api, 'call_gpt', lambda *a, **k: pytest.fail('unexpected narration call'))
        monkeypatch.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION', '1' if case == 'host' else '0')
        expressions = []
        def express(contract):
            expressions.append(contract)
            return dict(ok=True, sent=True, text=("I've got hot stew and rumors for three copper."
                if case == 'embellishment' else "I've got hot stew and rumors." if case == 'offerings'
                else "I couldn't tell you."), usage={}, latency_ms=0)
        monkeypatch.setattr('game.expressive_dialogue.request_expression', express)
        response = client.post('/api/chat?ui_mode=player', json={'text': text})
        after = state()
    body = response.json()
    internal = st.load_log()[-1]
    save('integration_' + case + '.json', dict(status=response.status_code, opening=opening.json(), response=body,
        internal=internal, before=before, after=after, expression_mock_captures=expressions,
        interpretation_mock_count=len(calls), live_provider_requests=0))
    assert response.status_code == 200 and len(calls) == 1
    said = body['gm_output']['player_facing_text']
    if case in {'offerings', 'host', 'embellishment'}:
        assert 'hot stew' in said and 'rumors' in said
        if case == 'host':
            assert not expressions
        else:
            assert expressions and expressions[0]['authorized_propositions'] == ['I offer hot stew and rumors.']
            audit = internal['gm_output']['metadata']['expression_generation']
            assert audit['decision'] == ('rejected' if case == 'embellishment' else 'adopted')
    else:
        assert not internal['resolution']['social']['dialogue_authority']['authorized_proposition']
        assert 'couldn' in said or 'cannot' in said
    assert 'copper' not in said and secret not in response.text
    assert body['gm_output']['player_facing_text'] == internal['gm_output']['player_facing_text']
    for name in ('character', 'campaign', 'combat', 'conditions'):
        assert before[name] == after[name]
    from game.world import advance_world_tick
    expected = copy.deepcopy(before['world'])
    advance_world_tick(expected, before['campaign'])
    assert after['world'] == expected
    assert after['session']['active_scene_id'] == before['session']['active_scene_id']
    prior_npc = before['session'].get('npc_runtime', {}).get('tavern_runner', {})
    next_npc = after['session'].get('npc_runtime', {}).get('tavern_runner', {})
    for key in ('attitude', 'trust', 'fear', 'suspicion', 'revealed_topics'):
        assert next_npc.get(key, [] if key == 'revealed_topics' else 0) == prior_npc.get(key, [] if key == 'revealed_topics' else 0)
    assert st.load_active_scene() == scene_before
    from game.state_channels import deep_project_public_payload
    assert body == deep_project_public_payload(body)
