"""G1–G25 instrumentation controls. Synthetic contracts are not gameplay scores."""
import copy
import json
import socket
import zipfile
from pathlib import Path

import pytest

from tools.playtest import gameplay as g, runner


@pytest.fixture(autouse=True, scope='module')
def production_pipeline_configuration():
    # conftest disables these for in-process unit tests. Owned SDK-stubbed workers
    # must exercise the normal interpretation/expression pipeline instead.
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv('ASHEN_DISABLE_LIVE_INTERPRETATION', '0')
        patch.setenv('ASHEN_DISABLE_EXPRESSION_GENERATION', '0')
        yield


def action(index=0):
    return runner.load_scenario('FiveTurnGameplay')['actions'][3+index]


def state():
    return {'session.json': {'campaign_started': True, 'active_scene_id': 'frontier_gate', 'turn_counter': 1},
            'world.json': {'world_state': {'flags': {}}}, 'character.json': {'hp': 10}, 'session_log.jsonl': []}


def response(text='Rain falls over the gate district.', *, hard_valid=True):
    return {'ok': True, 'gm_output': {'player_facing_text': text, 'metadata': {'accepted_response': {
        'provenance': 'initial_generation', 'hard_validation': {'hard_valid': hard_valid, 'reasons': []}}}}}


def evaluate(index=0, body=None, before=None, after=None, events=None, prior=()):
    before = before or state()
    return g.evaluate(action(index), 200, body if body is not None else response(), before,
                      after if after is not None else copy.deepcopy(before), events or [], prior)


def categories(row):
    return {f['category'] for f in row['findings']}


def test_G1_five_turn_successful_instrument_contract():
    """Full evaluator positive control; no assertion about model interpretation."""
    rows = [evaluate(i, response(t)) for i, t in enumerate([
        'Rain falls over the gate district.', 'The gate serjeant declines to discuss the patrol.',
        'The notice board lists taxes and curfew rules.', 'The notice board and serjeant are available patrol leads.',
        'The gate remains closed; permission to enter the city is required.'])]
    assert len(rows) == 5 and all(r['mechanical']['status'] == 'PASS' and r['semantic']['status'] == 'RECORDED' for r in rows)
    for row in rows:
        row.update(action='player_turn', ok=True)
    result = {'scenario': runner.load_scenario('FiveTurnGameplay'), 'mode': 'Deterministic',
              'steps': rows, 'opening_acceptance': True, 'verdict': 'PASS', 'provider_usage': {}, 'elapsed_seconds': 0}
    report = g.finalize(result)
    assert result['verdict'] == 'PASS' and result['completed_turns'] == 5
    assert 'REQUIRES_HUMAN_REVIEW' in report


@pytest.fixture(scope='module')
def opening_failure():
    return runner.run_playtest(scenario='FiveTurnGameplay', case='invalid_json', capture_response=True)


def test_G2_opening_failure(opening_failure):
    _, result = opening_failure
    assert result['verdict'] == 'FAIL' and result['attempted_turns'] == 0
    assert len(result['skipped_turns']) == 5


def test_G3_provider_failure_turn2():
    row = evaluate(1, events=[{'event': 'completed', 'error': 'provider_error', 'completion_status': 'failed'}])
    assert row['stop'] and 'provider_transport_failure' in categories(row)


def test_G4_invalid_structure_turn3():
    row = evaluate(2, events=[{'stage': 'provider_response', 'classification': 'structured_validation_failure'}])
    assert row['stop'] and 'structured_envelope_failure' in categories(row)


@pytest.mark.parametrize('case,turn,category', [('turn2_exception', 'T2', 'provider_transport_failure'),
                                             ('turn3_invalid_json', 'T3', 'invalid_interpretation_response')])
def test_real_http_turn_failures(case, turn, category):
    _, result = runner.run_playtest(scenario='FiveTurnGameplay', case=case, capture_response=True)
    assert result['verdict'] == 'FAIL'
    assert result['gameplay_turns'][-1]['step_id'] == turn
    assert category in categories(result['gameplay_turns'][-1])
    assert len(result['gameplay_turns']) == int(turn[1:])


def test_G5_semantic_nonresolution():
    body = response('No one here can answer that from what is settled here.')
    body['gm_output']['metadata']['accepted_response']['provenance'] = 'safe_nonresolution'
    row = evaluate(body=body)
    assert 'generic_nonresolution' in categories(row)
    assert row['semantic']['nonresolution'] == 'safe_nonresolution'
    assert row['mechanical']['status'] == 'PASS'


def test_G6_legitimate_refusal():
    row = evaluate(1, response('The serjeant refuses to discuss the patrol while managing this crowd.'))
    assert not row['stop'] and row['mechanical']['status'] == 'PASS'


def test_G7_unsupported_world_claim_native_authority():
    body = response('The patrol is dead.', hard_valid=False)
    body['gm_output']['metadata']['accepted_response']['hard_validation']['reasons'] = ['unsupported_world_claim']
    row = evaluate(body=body)
    assert row['semantic']['status'] == 'FAIL' and row['stop']
    assert row['findings'][0]['source'] == 'native accepted_response.hard_validation'


def test_G8_unauthorized_state_mutation():
    after = state(); after['character.json']['hp'] = 50
    row = evaluate(after=after)
    assert 'unauthorized_state_mutation' in categories(row) and row['stop']
    after = state(); after['world.json']['invented_persistent_structure'] = True
    assert 'unauthorized_state_mutation' in categories(evaluate(after=after))


def test_G9_legitimate_movement():
    after = state(); after['session.json']['active_scene_id'] = 'market_quarter'
    body = response('You enter the city market.'); body['resolution'] = {'kind': 'travel', 'resolved_transition': True, 'target_scene_id': 'market_quarter'}
    row = evaluate(4, body, after=after)
    assert row['mechanical']['status'] == 'PASS' and not row['stop']


def test_G10_blocked_movement():
    body = response('The gate guard blocks your entry to the city.')
    body['resolution'] = {'kind': 'travel', 'success': False, 'resolved_transition': False}
    assert not evaluate(4, body)['stop']


def test_G11_divergence(monkeypatch):
    real = runner.snapshot_files
    def diverged(run, label):
        value = real(run, label)
        if label == 'after':
            # Fault the read-side observation, never persistent gameplay state.
            value = copy.deepcopy(value)
            value['session.json']['payload']['active_scene_id'] = 'market_quarter'
        return value
    monkeypatch.setattr(runner, 'snapshot_files', diverged)
    _, result = runner.run_playtest(scenario='FiveTurnGameplay', capture_response=True)
    assert result['stop_reason'] == 'scenario_divergence' and result['verdict'] == 'PARTIAL'
    assert result['attempted_turns'] == 0 and len(result['skipped_turns']) == 5


@pytest.fixture(scope='module')
def sequence():
    return runner.run_playtest(scenario='FiveTurnGameplay', capture_response=True)


def test_G12_budget_exhaustion(sequence):
    _, result = sequence
    assert result['provider_usage']['dispatched_requests'] == 6
    assert result['stop_reason'] == 'provider_budget_exhaustion'
    assert result['attempted_turns'] == 4 and result['skipped_turns'][0]['step_id'] == 'T5'
    assert result['process_cleanup']['stopped']


def test_G13_turn_timeout(monkeypatch):
    real = runner.request
    def timeout(base, method, path, *args, **kwargs):
        if path == '/api/chat':
            raise socket.timeout()
        return real(base, method, path, *args, **kwargs)
    monkeypatch.setattr(runner, 'request', timeout)
    run, result = runner.run_playtest(scenario='FiveTurnGameplay', capture_response=True)
    assert result['stop_reason'] == 'timeout' and result['process_cleanup']['stopped']
    assert (run/'turns/T1/interruption.json').is_file()
    assert (run/'after/documents.json').is_file()


def test_G14_missing_response_evidence():
    row = evaluate(body={'ok': True})
    assert row['mechanical']['status'] == 'INCONCLUSIVE'
    assert row['semantic']['status'] == 'UNKNOWN'
    assert 'insufficient_response_evidence' in categories(row)


def test_G15_irrelevance():
    row = evaluate(1, response('Purple clouds dance over distant mountains.'))
    assert 'possibly_irrelevant_response' in categories(row)
    assert all(f['kind'] == 'heuristic_quality_concern' for f in row['findings'])


def test_G16_repetition():
    text = 'Rain falls over the gate district.'
    assert 'repetitive_narration' in categories(evaluate(body=response(text), prior=[text]))


def test_G17_state_consistent_description():
    row = evaluate()
    assert not row['state_diff'] and row['mechanical']['turn_delta'] == 0


@pytest.mark.parametrize('valid', [True, False], ids=['G18_correct_rules', 'G19_incorrect_rules'])
def test_native_rules_audit(valid):
    from game.noncombat_resolution import resolve_noncombat_action
    body = response()
    body['resolution'] = resolve_noncombat_action({'scene': {'id': 'plain_yard', 'visible_facts': ['Rain falls.']}}, {}, {},
        {'id': 'look', 'type': 'observe', 'label': 'Look around', 'prompt': 'Look around'}, raw_player_text='Look around')
    if not valid:
        # Contradict an engine-owned contract; never compute our own dice result.
        body['resolution']['success'] = False
        body['resolution']['noncombat_resolution']['success_state'] = 'success'
    row = evaluate(body=body)
    assert row['mechanical']['rules']['status'] == ('PASS' if valid else 'FAIL')
    assert ('invalid_rules_adjudication' in categories(row)) is (not valid)


def test_G20_inapplicable_dimension():
    d = evaluate()['quality']['dimensions']['Q6']
    assert d['status'] == 'N/A' and d['score'] is None


def test_G21_human_review():
    d = evaluate()['quality']['dimensions']['Q5']
    assert d['status'] == 'REQUIRES_HUMAN_REVIEW' and d['score'] is None
    assert {'evidence', 'method', 'confidence', 'explanation'} <= d.keys()


def test_G22_exact_accounting(sequence):
    run, result = sequence
    events = g.read_events(run)
    usage = g.accounting(events)
    assert usage['request_count'] == result['provider_usage']['dispatched_requests'] == 6
    assert usage['input_tokens'] == 120 and usage['output_tokens'] == 60
    assert usage['total_tokens'] == 180
    assert sum(t['provider_usage']['request_count'] for t in result['gameplay_turns']) == 5  # opening is separate


def test_G23_zero_live(sequence):
    assert sequence[1]['provider_exposure']['live_calls'] == 0
    # Existing H15 additionally proves external socket refusal in a separate worker.
    code = "from tools.playtest.worker import install_transport; import socket; install_transport('success', True); socket.socket().connect(('192.0.2.1',443))"
    proc = runner.subprocess.run([runner.sys.executable, '-c', code], capture_output=True, timeout=10)
    assert proc.returncode != 0 and b'external network access refused' in proc.stderr


def test_G24_unauthorized_live():
    _, result = runner.run_playtest(scenario='FiveTurnGameplay', mode='Live', capture_response=True)
    assert result['verdict'] == 'BLOCKED' and not result['steps'] and not result['process_cleanup']['owned']


def test_G25_complete_export(sequence):
    run, result = sequence
    with zipfile.ZipFile(result['evidence_zip']) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        for path in ['reports/GAMEPLAY_REPORT.md', 'reports/result.json', 'opening/documents.json',
                     'turns/T1/api_response.json', 'turns/T1/before/documents.json', 'turns/T1/after/documents.json',
                     'turns/T1/evaluation.json', 'diagnostics/provider_usage.jsonl']:
            assert path in names
        for item in json.loads(archive.read('evidence/manifest.json'))['files']:
            assert runner.hashlib.sha256(archive.read(item['path'])).hexdigest() == item['sha256']
    out = runner.ROOT/'artifacts/pr_play_09'
    out.mkdir(parents=True, exist_ok=True)
    runner.write(out/'example_run.json', {'run': str(run), 'verdict': result['verdict'],
                 'stop_reason': result['stop_reason'], 'scope': 'real HTTP; synthetic SDK; not live quality evidence'})


def test_live_capture_required():
    _, result = runner.run_playtest(scenario='FiveTurnGameplay', mode='Live', authorize_live=True)
    assert result['verdict'] == 'BLOCKED' and not result['process_cleanup']['owned']


def test_versioned_contract_and_bounded_turns():
    value = runner.load_scenario('FiveTurnGameplay')
    assert value['version'] == '1.0.0' and value['provider_request_ceiling'] == 6
    assert runner.verify_gameplay_grounding(value) is True
    invalid = copy.deepcopy(value); invalid['actions'][4]['required_npc'] = 'invented_person'
    with pytest.raises(ValueError):
        runner.verify_gameplay_grounding(invalid)
    value['actions'][3]['timeout'] = 91
    with pytest.raises(ValueError):
        runner.validate_scenario(value)


def test_unknown_rules_are_not_assumed_correct():
    assert evaluate()['mechanical']['rules']['status'] == 'uncertain'


def test_engine_nonmutating_contract_prevents_time_and_world_changes():
    body = response(); body['resolution'] = {'metadata': {'authoritative_mutation': False}}
    after = state(); after['world.json']['world_state']['flags']['quest_accepted'] = True
    assert 'nonmutating_contract_violation' in categories(evaluate(body=body, after=after))


def test_departed_npc_invalidates_next_action():
    assert g.prerequisite_failure(action(1), state()) == 'Required NPC no longer present'


def test_missing_object_invalidates_next_action():
    assert g.prerequisite_failure(action(2), state()) == 'Required object no longer present'
