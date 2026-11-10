"""Semantic stop classifications and real offline controller termination."""
import copy
import ast
import json
from pathlib import Path

import pytest

from tools.playtest import gameplay as g, runner
from tests.test_five_turn_gameplay import action, state


def body(*, reason=None, partial=False, text='The guard declines to discuss that.'):
    return {'ok': True, 'gm_output': {'player_facing_text': text, 'metadata': {'accepted_response': {
        'speaker_id': 'guard', 'interaction_completion': not partial, 'hard_validation': {'hard_valid': True}}}},
        'resolution': {'kind': 'conversational_clarify' if reason else 'question', 'metadata': {
            'resolver_invoked': not bool(reason), 'conversational_decision': {'reason': reason} if reason else {}}}}


@pytest.mark.parametrize('reason', ['proposal_not_eligible', 'unsupported_compound_step', 'compound_intention_needs_confirmation'])
def test_http_200_refusal_stops(reason):
    result = g.classify_turn(200, body(reason=reason))
    assert result['transport_completed'] and result['pipeline_completed']
    assert result['stop'] and not result['gameplay_completed'] and not result['action_executed']


def test_exact_pr_play_22_response_stops():
    row = json.loads(Path('artifacts/atgb/pr_play_22/live/turns/T1/api_response.json').read_text())
    result = g.classify_turn(row['http_status'], row['response'])
    assert result['transport_completed'] and result['stop']
    assert not result['gameplay_completed']


def test_valid_but_weak_answer_continues():
    result = g.classify_turn(200, body(text='The guard says, "I do not know."'))
    assert not result['stop'] and result['gameplay_completed']


def test_recovered_host_description_is_completed():
    value = body()
    value['gm_output']['metadata']['accepted_response']['speaker_id'] = ''
    value['resolution'] = {'kind': 'conversational_answer', 'metadata': {
        'resolver_invoked': False, 'conversational_decision': {'category': 'ANSWER', 'reason': 'communication_before_execution'},
        'live_chat_interpretation': {'status': 'blocked', 'reason': 'clarification_required'}}}
    result = g.classify_turn(200, value)
    assert not result['stop'] and result['gameplay_completed']
    assert not result['action_executed']


@pytest.mark.parametrize('event', [
    {'classification': 'provider_error'}, {'classification': 'json_parse_failure'},
    {'classification': 'structured_validation_failure'}, {'event': 'rejected'},
])
def test_provider_parser_validator_failure_stops(event):
    assert g.classify_turn(200, body(), [event])['stop']


def test_partial_usable_reported_separately():
    result = g.classify_turn(200, body(partial=True))
    assert not result['stop'] and result['action_executed'] and not result['gameplay_completed']
    assert result['interaction_outcome'] == 'partial'


def test_missing_response_stops():
    assert g.classify_turn(200, {'ok': True})['stop']


def test_unauthorized_mutation_and_disclosure_stop():
    before = state()
    after = copy.deepcopy(before)
    after['character.json']['hp'] = 999
    assert g.evaluate(action(), 200, body(), before, after, [])['stop']
    before['world.json']['hidden_truth'] = 'SYNTHETIC_RESTRICTED_VALUE_23'
    row = g.evaluate(action(), 200, body(text='SYNTHETIC_RESTRICTED_VALUE_23'), before, before, [])
    assert row['stop'] and any(f['category'] == 'hidden_information_disclosure' for f in row['findings'])


@pytest.mark.parametrize('failure', ['binding', 'mutation', 'disclosure'])
def test_original_custom_controller_uses_shared_stop(failure, tmp_path):
    # Extract only its actual predicate. Importing the historical command would
    # run its top-level offline/live CLI, which this regression must never do.
    path = Path('artifacts/pr_play_22/execute_validation.py')
    module = ast.parse(path.read_text())
    definition = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'failed')
    namespace = {'read_events': lambda run: [], 'run': tmp_path, 'write': lambda *a: None,
                 'result': {'steps': [], 'ordinary_attempted': 1},
                 'scenario': runner.load_scenario('FiveTurnGameplay'),
                 'classify_turn': g.classify_turn, 'evaluate': g.evaluate}
    exec(compile(ast.Module(body=[definition], type_ignores=[]), str(path), 'exec'), namespace)
    before = state()
    after = copy.deepcopy(before)
    value = body(reason='proposal_not_eligible' if failure == 'binding' else None)
    if failure == 'mutation':
        after['character.json']['hp'] = 1000
    elif failure == 'disclosure':
        before['world.json']['hidden_truth'] = 'SYNTHETIC_HIDDEN_CUSTOM_23'
        after = copy.deepcopy(before)
        value['gm_output']['player_facing_text'] = 'SYNTHETIC_HIDDEN_CUSTOM_23'
    row = {'http_status': 200, 'response': value, 'payload': {'text': 'I ask about prices.'}}
    assert namespace['failed'](row, 0, before, after)
    assert row['evaluation']['stop']


def test_controller_failure_stops_without_followup_or_restart(monkeypatch, tmp_path):
    # Owned real worker, deterministic SDK transport, real snapshots and evaluator.
    monkeypatch.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION', '0')
    monkeypatch.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION', '0')
    request = runner.request
    submissions = []
    def observed(base, method, path, timeout, payload=None):
        if method == 'POST':
            submissions.append(path)
        if path == '/api/chat':
            return 200, body(reason='proposal_not_eligible')
        return request(base, method, path, timeout, payload)
    monkeypatch.setattr(runner, 'request', observed)
    run, result = runner.run_playtest(scenario='FiveTurnGameplay', mode='Deterministic', capture_response=True,
                                      output_root=tmp_path/'runs')
    (Path('artifacts/pr_play_23')/'harness_stop_integration.json').write_text(json.dumps({
        'result': result, 'submissions': submissions, 'live_provider_requests': 0}, indent=2), encoding='utf-8')
    assert submissions.count('/api/chat') == 1
    assert submissions.count('/api/new_campaign') == 1 and submissions.count('/api/start_campaign') == 1
    assert result['ordinary_actions_attempted'] == 1 and result['ordinary_actions_executed'] == 0
    assert result['http_requests_completed'] == 1 and result['meaningful_gameplay_turns_completed'] == 0
    assert result['decisive_failures'] == 1
    assert result['provider_usage']['dispatched_requests'] <= 6
    assert (run/'turns/T1/api_response.json').exists() and (run/'turns/T1/after/documents.json').exists()
    assert result['process_cleanup']['stopped']


def test_configured_request_ceiling_never_exceeded(monkeypatch, tmp_path):
    monkeypatch.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION', '0')
    monkeypatch.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION', '0')
    monkeypatch.setenv('ASHEN_PROVIDER_REQUEST_LIMIT', '2')
    _, result = runner.run_playtest(scenario='FiveTurnGameplay', mode='Deterministic', output_root=tmp_path/'runs')
    assert result['provider_usage']['dispatched_requests'] <= 2
    assert sum(row['action'] == 'start_campaign' for row in result['steps']) == 1
