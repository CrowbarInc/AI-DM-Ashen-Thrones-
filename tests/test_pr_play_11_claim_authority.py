"""Offline historical opening replay through production parsing and authority owners."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from tests.test_pr_play_04_opening_integrity import opening_world, _start, _snap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/pr_play_11'
RUNS = ROOT / 'artifacts/atgb/automated_playtests'
REJECTED = '20261031T015747Z-5a6c03c902e3'
ACCEPTED = '20261030T191257Z-ecc1b6062bdc'


def install_history(opening_world, monkeypatch, run=REJECTED):
    import game.api as api
    import game.storage as st
    import game.immutable_valid_response as ivr
    import openai
    path = RUNS / run
    before = json.loads((path / 'baseline/documents.json').read_text())
    st._save_json(st.scene_path('frontier_gate'), before['scenes/frontier_gate.json'])
    api.compose_state()
    capture = next((path / 'opening_response_evidence').glob('*.json'))
    parsed = json.loads(capture.read_text())['parsed_response']
    opening_world['state']['text'] = json.dumps(parsed)
    traces, requests = [], []
    original = ivr.validate_generated_response
    def observe(text, **kwargs):
        result = original(text, **kwargs)
        traces.append(copy.deepcopy(dict(text=text, inputs=kwargs, result=result)))
        return result
    monkeypatch.setattr(ivr, 'validate_generated_response', observe)
    ctor = openai.OpenAI
    def observe_ctor(**kwargs):
        client = ctor(**kwargs)
        create = client.responses.create
        def observe_create(**request):
            requests.append(copy.deepcopy(request))
            return create(**request)
        client.responses.create = observe_create
        return client
    monkeypatch.setattr(openai, 'OpenAI', observe_ctor)
    return parsed, traces, requests


@pytest.mark.parametrize('run,expected', [(REJECTED, 422), (ACCEPTED, 200),
    ('20261030T183848Z-5fe421902485', 200)])
def test_historical_production_replay(opening_world, monkeypatch, run, expected):
    parsed, traces, requests = install_history(opening_world, monkeypatch, run)
    before = _snap()
    body, status = _start()
    after = _snap()
    assert status == expected, body
    assert len(opening_world['calls']) == 1
    assert traces[0]['inputs']['declared_claims'] == parsed['declared_claims']
    if expected == 422:
        assert 'unauthorized_resolution_decision_fact' in traces[0]['result']['reasons']
        audit = traces[0]['result']['gm_resolution_decision_audit']
        assert audit['declaration_validation']['rejected_claims'] == []
        assert len(audit['declaration_validation']['accepted_claims']) == 7
        assert len(audit['violations']) == 1
        assert audit['violations'][0]['reason_codes'] == ['notice_roster_history']
        assert audit['violations'][0]['text'].startswith('The board itself lists grim new taxes')
        assert before == after
        assert after['can_start']
    else:
        assert after['turn_counter'] == before['turn_counter'] + 1
        assert _start()[1] == 409
        assert len(opening_world['calls']) == 1
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / (run + '_replay.json')).write_text(json.dumps(dict(
        status=status, before=before, after=after, traces=traces,
        requests=requests, response=body, synthetic_dispatches=len(opening_world['calls']),
        live_dispatches=0, parsed_response_equal=True), indent=2), encoding='utf-8')


def test_notice_claim_causal_metadata_controls(opening_world, monkeypatch):
    from game.gm_resolution_decision import validate_declared_claims_against_decision
    parsed, traces, _ = install_history(opening_world, monkeypatch)
    assert _start()[1] == 422
    decision = traces[0]['inputs']['decision']
    original = parsed['declared_claims'][0]
    outcomes = {}
    for key in ('original', 'id_only', 'role_only', 'provenance_only'):
        row = copy.deepcopy(original)
        source = next(c for c in decision['realization_claims'] if c['claim_id'] == original['declaration_id'])
        if key == 'id_only': row['source_claim_id'] = source['claim_id']
        if key == 'role_only': row['realization_role'] = 'MAY_STATE'
        if key == 'provenance_only': row['provenance_requested'] = 'bounded_incidental'
        result = validate_declared_claims_against_decision([row], decision=decision)
        outcomes[key] = result
        assert result['hard_valid']  # none of these fields caused the historical rejection
    from game.immutable_valid_response import validate_generated_response
    context = copy.deepcopy(traces[0]['inputs'])
    for row in context['declared_claims']:
        row['source_claim_id'] = row['declaration_id']
    sourced = validate_generated_response(parsed['narration'], **context)
    assert not sourced['hard_valid']
    assert sourced['gm_resolution_decision_audit']['declaration_validation']['hard_valid']
    outcomes['all_source_ids_with_original_prose'] = sourced
    (OUT/'causal_controls.json').write_text(json.dumps(outcomes, indent=2))


def test_conservative_generation_contract(opening_world, monkeypatch):
    parsed, traces, requests = install_history(opening_world, monkeypatch)
    old = 'The board itself lists grim new taxes, curfew regulations, and a posted warning about a patrol that has gone missing.'
    new = parsed['declared_claims'][0]['text']
    for field in ('narration', 'player_facing_text'):
        assert old in parsed[field]
        parsed[field] = parsed[field].replace(old, new)
    opening_world['state']['text'] = json.dumps(parsed)
    body, status = _start()
    assert status == 200, body
    assert len(opening_world['calls']) == 1
    assert traces[0]['result']['gm_resolution_decision_audit']['hard_valid']
    (OUT/'conservative_generation.json').write_text(json.dumps(dict(
        status=status, changed_fields=['narration', 'player_facing_text'],
        replacement=dict(before=old, after=new), traces=traces,
        response=body, requests=requests), indent=2))
    prompt = json.dumps(requests)
    assert 'use its exact text as a separate narration sentence' in prompt
    assert 'rc_a83c5bcfc65e' in prompt


@pytest.mark.parametrize('case,expected', [
    ('C4', True), ('C5', False), ('C6', False), ('C7', False),
    ('C8', True), ('C9', True), ('C10', False), ('C11', False),
    ('C12', False), ('C13', False), ('C14', False), ('C15', True),
    ('C16', False), ('C17', False),
])
def test_authority_matrix(case, expected):
    from game.immutable_valid_response import validate_generated_response
    context = json.loads((ROOT/'tests/fixtures/pr_play_11/opening_context.json').read_text())
    source = context['decision']['realization_claims'][0]
    row = copy.deepcopy(context['declared_claims'][0])
    row['source_claim_id'] = source['claim_id']
    text = row['text']
    claims = [row]
    if case in {'C5', 'C6'}:
        row.update(text='The notice board names Varek as the murderer.', source_claim_id=None if case == 'C5' else 'rc_invalid')
        text = row['text']
    if case == 'C7':
        text = 'The notice board does not list taxes, curfew rules, or a warning about a missing patrol.'
        row.update(text=text, source_claim_id=None)
    if case == 'C8':
        text = source['text']
        claims = []  # Existing authored evidence remains authoritative without a declaration.
    if case == 'C9':
        text = 'Rain patters on a worn cloak.'
        claims = []
    if case in {'C10', 'C11', 'C12'}:
        text = {'C10':'You persuade the guards and enter the fortress.',
                'C11':'You gain 100 gold and recover 5 HP.',
                'C12':'The Ash Compact has closed the gate permanently.'}[case]
        row.update(text=text, source_claim_id=None)
    if case == 'C13':
        text = 'GM-only: the hidden_facts reveal the murderer.'
        claims = []
    if case == 'C14':
        row.update(declaration_mode='propose', provenance_requested='authored_world_fact', modality='established')
    if case == 'C15':
        # Empty premises and absent source ID are valid for an exact authored fact.
        row.update(source_claim_id=None)
    if case in {'C16', 'C17'}:
        claims = [row, dict(row, declaration_id='invalid_1', source_claim_id=None,
                           text='The notice board names Varek as the murderer.')]
        if case == 'C17':
            claims.append(dict(row, declaration_id='invalid_2', source_claim_id=None,
                               text='The guards award you 100 gold.'))
    context['declared_claims'] = claims
    result = validate_generated_response(text, **context)
    (OUT/(case+'.json')).write_text(json.dumps(dict(case=case, expected=expected, text=text, claims=claims, result=result), indent=2))
    assert result['hard_valid'] == expected, result
    if case == 'C17':
        assert len(result['gm_resolution_decision_audit']['declaration_validation']['rejected_claims']) == 2


def test_mixed_opening_atomicity_and_retryability(opening_world, monkeypatch):
    parsed, traces, _ = install_history(opening_world, monkeypatch, ACCEPTED)
    parsed['declared_claims'].append(dict(parsed['declared_claims'][0],
        declaration_id='invalid_1', source_claim_id=None, semantic_identity={},
        text='The notice board names Varek as the murderer.'))
    opening_world['state']['text'] = json.dumps(parsed)
    before = _snap()
    body, status = _start()
    assert status == 422 and _snap() == before and before['can_start']
    parsed['declared_claims'].pop()
    opening_world['state']['text'] = json.dumps(parsed)
    assert _start()[1] == 200
    assert _snap()['turn_counter'] == before['turn_counter'] + 1
    assert len(opening_world['calls']) == 2


def test_capture_fidelity():
    capture = OUT/'historical/rejected_capture.json'
    fidelity = json.loads((OUT/'capture_fidelity.json').read_text())
    assert hashlib.sha256(capture.read_bytes()).hexdigest() == fidelity['capture_sha256']
    assert json.loads(capture.read_text())['parsed_response'] == json.loads((ROOT/'tests/fixtures/pr_play_11/rejected_opening.json').read_text())


def test_source_id_is_not_exclusive_evidence():
    from game.gm_resolution_decision import validate_declared_claims_against_decision
    context = json.loads((ROOT/'tests/fixtures/pr_play_11/opening_context.json').read_text())
    row = copy.deepcopy(context['declared_claims'][0])
    row['source_claim_id'] = 'rc_invalid'
    result = validate_declared_claims_against_decision([row], decision=context['decision'])
    assert result['hard_valid']  # The existing contract falls back to exact authored text.
    (OUT/'source_id_fallback.json').write_text(json.dumps(dict(row=row, result=result), indent=2))
