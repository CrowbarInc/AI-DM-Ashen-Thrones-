"""H1–H20: real isolated HTTP orchestration, no provider connectivity."""
import copy
import json
import socket
import zipfile
from pathlib import Path

import pytest

from tools.playtest import runner
from tools.playtest.analysis import classify, compare

pytestmark = pytest.mark.integration
OUT = Path('artifacts/pr_play_08')


@pytest.fixture(scope='module')
def cases():
    results = {}
    for name in runner.CASES:
        path, result = runner.run_playtest(case=name, capture_response=True, startup_timeout=10)
        results[name] = (path, result)
    OUT.mkdir(exist_ok=True, parents=True)
    runner.write(OUT/'matrix_runs.json', {k: {'run': str(p), 'result': r} for k, (p, r) in results.items()})
    return results


def test_H1_successful_opening(cases):
    result = cases['success'][1]
    assert result['verdict'] == 'PASS'
    assert result['opening_commits_observed'] == 1
    assert result['steps'][2]['narration_present'] is True


@pytest.mark.parametrize('identifier,case,category', [
    ('H2', 'truncation', 'provider_output_limit_exhaustion'),
    ('H3', 'invalid_json', 'json_parsing_failure'),
    ('H4', 'envelope', 'structured_envelope_failure'),
    ('H5', 'semantic', 'semantic_validation_failure'),
    ('H6', 'safe_nonresolution', 'opening_acceptance_failure'),
    ('H7', 'exception', 'provider_exception'),
    ('H8', 'admission', 'provider_admission_rejection'),
])
def test_failure_matrix(cases, identifier, case, category):
    result = cases[case][1]
    assert result['verdict'] == 'FAIL', result
    assert result['failure_classification']['category'] == category
    assert result['failure_classification']['inferred'] is False
    assert result['opening_commits_observed'] == 0
    assert result['state_comparison']['integrity'] is True
    assert result['provider_usage']['dispatched_requests'] == (0 if case == 'admission' else 1)


def test_H9_failed_opening_preserves_state(cases):
    for name, (_, result) in cases.items():
        if name == 'success':
            continue
        assert result['state_comparison']['integrity'] is True
        assert not result['state_comparison']['gameplay_mutations']


def test_H10_commits_once(cases):
    result = cases['success'][1]
    assert result['state_comparison']['turn_delta'] == result['state_comparison']['log_delta'] == 1
    assert sum(step['action'] == 'start_campaign' for step in result['steps']) == 1
    assert result['provider_usage']['dispatched_requests'] == 1


def test_H11_preflight_blocked(monkeypatch):
    monkeypatch.setattr(runner, 'load_scenario', lambda _: (_ for _ in ()).throw(ValueError('Missing fixture')))
    path, result = runner.run_playtest()
    assert result['verdict'] == 'BLOCKED'
    assert not result['process_cleanup']['owned']
    assert not result['steps']
    assert (path/'evidence/evidence.zip').exists()


def test_H12_startup_timeout(monkeypatch):
    # A real owned server cannot complete readiness before this bounded deadline.
    path, result = runner.run_playtest(startup_timeout=.001)
    assert result['verdict'] == 'BLOCKED'
    assert result['failure']['type'] == 'TimeoutError'
    assert result['process_cleanup']['stopped']
    assert result['elapsed_seconds'] < 15
    assert not result['steps']


def test_H13_interruption(monkeypatch):
    real_request = runner.request
    def interrupt(base, method, path, *args, **kwargs):
        if path == '/api/start_campaign':
            raise KeyboardInterrupt
        return real_request(base, method, path, *args, **kwargs)
    monkeypatch.setattr(runner, 'request', interrupt)
    path, result = runner.run_playtest(startup_timeout=10)
    assert result['verdict'] == 'INCONCLUSIVE'
    assert result['process_cleanup']['owned'] and result['process_cleanup']['stopped']
    assert result['failure_classification']['category'] == 'interrupted_execution'
    assert (path/'evidence/evidence.zip').exists()


def test_H14_missing_diagnostic(monkeypatch):
    real_stop = runner.stop_owned
    def remove_diagnostic(process, timeout):
        value = real_stop(process, timeout)
        # Fault injection preserves the source artifact under a different name.
        if process:
            run = Path(process.args[-1])
            (run/'diagnostics/provider_usage.jsonl').rename(run/'diagnostics/unavailable_journal.jsonl')
        return value
    monkeypatch.setattr(runner, 'stop_owned', remove_diagnostic)
    _, result = runner.run_playtest(startup_timeout=10)
    assert result['verdict'] == 'INCONCLUSIVE'
    assert any('diagnostic artifact unavailable' in u for u in result['uncertainties'])


def test_H15_deterministic_transport(cases):
    for _, result in cases.values():
        assert result['mode'] == 'Deterministic'
        assert result['environment_verification']['application']['sdk_retries'] == 0
        assert result['environment_verification']['application']['host_retries'] == 0
        assert not result['environment_verification']['application']['connectivity_diagnostics']
        assert result['provider_usage']['dispatched_requests'] <= 1
    # A non-local connection is rejected before the real socket connect.
    from tools.playtest.worker import install_transport
    # Run this assertion in a bounded subprocess; never mutate pytest's sockets.
    code = "from tools.playtest.worker import install_transport; import socket; install_transport('success'); socket.socket().connect(('192.0.2.1',443))"
    proc = runner.subprocess.run([runner.sys.executable, '-c', code], capture_output=True, timeout=10)
    assert proc.returncode != 0 and b'external network access refused' in proc.stderr


def test_H16_unauthorized_live():
    _, result = runner.run_playtest(mode='Live')
    assert result['verdict'] == 'BLOCKED'
    assert result['failure']['type'] == 'PermissionError'
    assert not result['process_cleanup']['owned'] and not result['steps']


def test_H17_existing_port_preserved():
    with socket.socket() as server:
        server.bind(('127.0.0.1', 0))
        server.listen()
        port = server.getsockname()[1]
        _, result = runner.run_playtest(port=port, startup_timeout=5)
        assert result['verdict'] == 'BLOCKED'
        assert not result['steps']
        assert server.fileno() != -1
        assert server.getsockname()[1] == port


def test_H18_archive_manifest(cases):
    run, result = cases['success']
    with zipfile.ZipFile(result['evidence_zip']) as z:
        assert z.testzip() is None
        manifest = json.loads(z.read('evidence/manifest.json'))
        for record in manifest['files']:
            assert runner.hashlib.sha256(z.read(record['path'])).hexdigest() == record['sha256']
        assert {'baseline/documents.json', 'after/documents.json', 'reports/result.json', 'reports/SUMMARY.md'} <= set(z.namelist())
        assert result['provider_response_evidence'][0] in z.namelist()


def test_H19_gameplay_vs_bookkeeping(cases):
    run, _ = cases['invalid_json']
    before = json.loads((run/'baseline/documents.json').read_text())
    after = copy.deepcopy(before)
    after['session.json']['saved_at'] = 'changed'
    result = compare(before, after, accepted=False)
    assert result['integrity'] and result['bookkeeping_mutations'] == ['session.json']
    assert not result['gameplay_mutations']
    after['world.json']['test_unauthorized_mutation'] = True
    result = compare(before, after, accepted=False)
    assert not result['integrity'] and result['unexpected_mutations'] == ['world.json']


def test_H20_unknown_failure():
    result = classify([{'classification': 'unrecognized', 'observed': True}])
    assert result['category'] == 'unknown_failure'
    assert result['root_cause'] == 'Not established'
    assert result['evidence_record'] == 'reports/result.json'


def test_scripted_observation_and_no_live_multiturn():
    _, result = runner.run_playtest(scenario='ScriptedObservation', mode='ScriptedGameplay', startup_timeout=10)
    assert result['verdict'] == 'PASS'
    assert len(result['steps']) == 6
    assert result['provider_usage']['dispatched_requests'] == 1
    _, refused = runner.run_playtest(scenario='ScriptedObservation', mode='Live', authorize_live=True)
    assert refused['verdict'] == 'BLOCKED' and not refused['process_cleanup']['owned']


def test_scenario_and_inherited_limits_cannot_expand(tmp_path):
    scenario = runner.load_scenario('CampaignOpening')
    scenario['token_budgets']['total'] += 1
    with pytest.raises(ValueError):
        runner.validate_scenario(scenario)
    scenario = runner.load_scenario('CampaignOpening')
    env = runner.child_environment(tmp_path, scenario, 'Deterministic', 'success', inherited={
        'ASHEN_PROVIDER_INPUT_TOKEN_LIMIT': '300', 'ASHEN_PROVIDER_REQUEST_LIMIT': '1'})
    assert env['ASHEN_PROVIDER_INPUT_TOKEN_LIMIT'] == '300'
    assert env['ASHEN_PROVIDER_REQUEST_LIMIT'] == '1'


@pytest.mark.parametrize('events,category', [
    ([{'provider_status': 'incomplete', 'provider_finish_reason': 'max_output_tokens', 'classification': 'json_parse_failure'}], 'provider_output_limit_exhaustion'),
    ([{'provider_status': 'incomplete'}], 'provider_incomplete_response'),
    ([{'classification': 'empty_provider_content'}], 'empty_provider_response'),
])
def test_precedence_and_additional_categories(events, category):
    assert classify(events)['category'] == category


def test_secret_log_redaction(tmp_path):
    import io
    runner.bounded_log(io.BytesIO(b'authorization sentinel-secret\n'), tmp_path/'log', ['sentinel-secret'])
    assert (tmp_path/'log').read_text() == 'authorization [REDACTED]\n'
