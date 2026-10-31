"""Effective instruction contracts and controlled host compatibility, never live inference."""
import copy
import json
import re
from pathlib import Path

import pytest

from game import live_chat_interpretation as live
from game.conversational_orchestration import decision_from_interpretation_record
from tests.test_atgb_r1_07_correction_contract import interpret, corrected

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / 'artifacts/atgb/atgb_r2_03'


@pytest.fixture
def effective_contract(monkeypatch):
    _, request = interpret(monkeypatch, corrected())
    return request['messages'][0]['content'].casefold()


@pytest.mark.parametrize('concept,terms', [
    ('requested detail', ('subject', 'requested detail', 'time', 'location', 'not just the topic')),
    ('answer support', ('evidence_refs', 'supporting that detail', 'not merely', 'topic')),
    ('partial evidence', ('background', 'partial answer', 'must not stand in', 'missing detail')),
    ('subject continuity', ('preceding context', 'elliptical follow-ups', 'corrections')),
    ('rejected alternative', ('uniquely established subject', 'rejected interpretation', 'nearby alternative')),
    ('unavailable answer', ('understood question', 'no answer-bearing evidence', 'empty evidence_refs', 'honest limitation')),
    ('not evidence-driven clarification', ('not clarification solely', 'answer is unavailable')),
    ('genuine ambiguity', ('targeted question', 'meaningful ambiguity', 'competing subjects')),
    ('independent slots', ('unresolved subject', 'separately', 'established addressee', 'never guess')),
    ('authority', ('restricted or unestablished', 'not disclosure authority', 'unsupported facts')),
    ('mechanical revision', ('actual eligible pending intention', 'host checks', 'never invent pending work')),
    ('correction semantics', ('corrected meaning', 'interpreted', 'gm/correction', 'legacy other')),
])
def test_effective_instruction_distinctions(effective_contract, concept, terms):
    # Check a related clause, not unrelated words anywhere in the source file.
    clauses = re.split(r'(?<=[.])\s+', effective_contract)
    assert any(all(term in ' '.join(clauses[i:i + 3]) for term in terms)
               for i in range(len(clauses))), concept


def test_existing_communication_modes_in_effective_request(monkeypatch):
    _, request = interpret(monkeypatch, corrected())
    user = request['messages'][1]['content']
    for mode in ('IN_WORLD_ACTION', 'OUT_OF_CHARACTER_CORRECTION', 'RULES_QUESTION', 'CLARIFICATION', 'OTHER'):
        assert mode in user
    assert request['schema']['properties']['communication']['required'] == ['recipient', 'purpose', 'subject', 'evidence_refs']


@pytest.mark.parametrize('index', range(4))
def test_historical_control_through_current_request_and_host(monkeypatch, index):
    controls = json.loads((HISTORY/'adapter_controls.json').read_text(encoding='utf-8'))
    traces = json.loads((HISTORY/'historical_trace_excerpts.json').read_text(encoding='utf-8'))
    contexts = json.loads((HISTORY/'context_and_original_logs.json').read_text(encoding='utf-8'))
    row = controls[index]
    trace = next(r for r in traces if r['turn_id'] == row['turn_id'])
    context = next(r for r in contexts if r['turn_id'] == row['turn_id'])
    baseline = ROOT/'data/validation/atgb/baselines/frontier-gate-v1'
    scene = json.loads((baseline/'scenes/frontier_gate.json').read_text())
    world = json.loads((baseline/'world.json').read_text())
    session = {'active_scene_id': 'frontier_gate', 'turn_counter': 2,
               'clocks': {'suspicion': 0, 'unrest': 0, 'danger': 0},
               'interaction_context': {'active_interaction_target_id': 'tavern_runner',
                                       'active_interaction_kind': 'social',
                                       'interaction_mode': 'social', 'engagement_level': 'engaged'}}
    if row['turn_id'].startswith('S02'):
        session = {'active_scene_id': 'frontier_gate'}
    payload = copy.deepcopy(row['exact_substituted_raw'])
    before = copy.deepcopy((scene, world, session, payload))
    result, request = interpret(monkeypatch, payload, text=trace['player_input'], scene=scene,
                                world=world, session=session, log=context['preceding_log'])
    assert result['record'] is not None  # Adapter safe abstention is reconsidered by existing API ownership.
    assert result['record']['public_evidence'] == {}
    decision = decision_from_interpretation_record(result['record'], player_text=trace['player_input'],
                                                  scene=scene, world=world, session=session)
    expected = row['reconsidered_host_decision']
    assert decision.category.value == expected['category']
    assert decision.player_facing_text == expected['player_facing_text']
    assert not decision.requires_authoritative_execution
    assert decision.context_update is None
    assert (scene, world, session, payload) == before
    if row['turn_id'] == 'S05.3':
        assert session['interaction_context']['active_interaction_target_id'] == 'tavern_runner'
        assert 'runner' in decision.player_facing_text and 'notice board' in decision.player_facing_text
        assert 'who are you' not in decision.player_facing_text.casefold()
    else:
        assert 'not been established' in decision.player_facing_text
    public_request = json.dumps(request['messages'])
    assert 'northwest mud track' not in public_request


def test_invalid_evidence_still_rejected(monkeypatch):
    payload = corrected(['clue:notice_patrol_route'])
    result, _ = interpret(monkeypatch, payload)
    assert result['reason'] == 'malformed_communication'
