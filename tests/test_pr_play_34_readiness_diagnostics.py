"""Regression coverage for the PR-PLAY-34 readiness assertions.

These tests do not launch a worker or contact a provider. They lock the
corrected bootstrap expectation and the individually identified assertions.
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'pr_play_34_evaluate', ROOT / 'artifacts' / 'pr_play_34' / 'evaluate.py')
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)

HISTORICAL_SESSION = (ROOT / 'artifacts' / 'atgb' / 'pr_play_33' / 'readiness'
                      / '20261102T004939Z-7d36523024d3' / 'data' / 'session.json')
HISTORICAL_TRACE = ROOT / 'artifacts' / 'pr_play_33' / 'readiness_output.txt'


def _ownership(**overrides):
    live = {
        'controller_pid': 10, 'popen_pid': 20, 'parent_pid': 10, 'reported_pid': 20,
        'worker_executable': r'C:\Python312\python.exe',
        'base_executable': r'C:\Python312\python.exe',
        'children': [],
        'ready': {'pid': 20, 'isolation_verified': True, 'diagnostics_enabled': True,
                  'sdk_retries': 0, 'host_retries': 0},
    }
    live.update(overrides.pop('live', {}))
    obs = {
        'live': live, 'http_status': 200, 'http_ready_exists': True, 'startup_seconds': 2.0,
        'timeout_seconds': 30, 'verdict': 'INCONCLUSIVE', 'steps': [], 'failure': None,
        'process_cleanup': {'owned': True, 'stopped': True, 'pid': 20, 'exit_code': 1},
        'orphans': [], 'port_released': True, 'port': 9, 'cleanup_succeeded': True,
        'provider_events': [{'event': 'initialized'}],
        'usage': {'dispatched_requests': 0, 'total_tokens': 0},
        'http_requests': [{'method': 'GET', 'path': '/api/state'}],
        'session_before': {'exists': False},
        'session_after': {'exists': True, 'inside_isolated_store': True, 'campaign_started': False,
                          'turn_counter': 0, 'chat_history_len': 0, 'log_entries': 0,
                          'last_action_debug': False, 'debug_traces': []},
    }
    obs.update(overrides)
    return obs


def _ids(result, *, failed_only=False):
    rows = result['assertions']
    if failed_only:
        rows = [row for row in rows if not row['passed']]
    return [row['id'] for row in rows]


def test_historical_outer_assertion_required_session_absence():
    text = HISTORICAL_TRACE.read_text(encoding='utf-8')
    assert "assert not (run/'data/session.json').exists()" in text


def test_historical_bootstrap_session_is_not_a_failure():
    payload = json.loads(HISTORICAL_SESSION.read_text(encoding='utf-8'))['payload']
    obs = _ownership(session_after={
        'exists': True, 'inside_isolated_store': True,
        'campaign_started': payload['campaign_started'],
        'turn_counter': payload['turn_counter'],
        'chat_history_len': len(payload.get('chat_history') or []),
        'log_entries': 0, 'last_action_debug': payload.get('last_action_debug') is not None,
        'debug_traces': payload.get('debug_traces') or [],
        'path': str(HISTORICAL_SESSION),
    })
    result = evaluate.evaluate_control('G', obs)
    assert result['result'] == 'PASS', result['failed_ids']
    assert 'G_session_file_allowed' in _ids(result)
    assert payload['campaign_started'] is False and payload['turn_counter'] == 0


def test_started_campaign_turn_and_dispatch_fail_separately():
    started = _ownership(session_after={
        'exists': True, 'inside_isolated_store': True, 'campaign_started': True,
        'turn_counter': 2, 'chat_history_len': 1, 'log_entries': 1,
        'last_action_debug': True,
        'debug_traces': [{'operation': 'start_campaign'}],
    }, provider_events=[{'event': 'dispatch_attempted'}],
        usage={'dispatched_requests': 1, 'total_tokens': 30},
        http_requests=[{'method': 'POST', 'path': '/api/chat'}], cleanup_succeeded=False)
    result = evaluate.evaluate_control('G', started)
    assert result['result'] == 'FAIL'
    assert set(result['failed_ids']) >= {
        'G_campaign_not_started', 'G_turn_counter_zero', 'G_no_gameplay_action',
        'G_no_gameplay_traces', 'G_no_provider_dispatch', 'G_no_campaign_http'}
    assert 'G_session_file_allowed' not in result['failed_ids']
    failed = next(row for row in result['assertions'] if row['id'] == 'G_campaign_not_started')
    assert failed['expected'] and failed['observed']['campaign_started'] is True
    assert failed['evidence'] and failed['cleanup_succeeded'] is False


def test_non_interpreter_child_is_visible_but_not_an_ownership_failure():
    obs = _ownership(live={
        'children': [{'pid': 30, 'parent_pid': 20, 'image': 'conhost.exe'}],
    })
    result = evaluate.evaluate_control('A', obs)
    assert result['result'] == 'PASS', result['failed_ids']
    historical = next(row for row in result['assertions'] if row['id'] == 'H3_worker_has_no_children')
    assert historical['passed'] is False and historical['gating'] is False
    assert 'H3_worker_has_no_children' not in result['failed_ids']


def test_interpreter_descendant_and_parent_mismatch_are_gating():
    child = _ownership(live={'children': [{'pid': 31, 'parent_pid': 20, 'image': 'python.exe'}]})
    child_result = evaluate.evaluate_control('A', child)
    assert 'A_no_interpreter_descendant' in child_result['failed_ids']
    parent = _ownership(live={'parent_pid': 99})
    parent_result = evaluate.evaluate_control('A', parent)
    assert 'H2_parent_is_controller' in parent_result['failed_ids']
    assert evaluate.historical_failure_ids(parent) == ['H2_parent_is_controller']


def test_timeout_and_occupied_port_controls_reject_false_readiness():
    timeout = _ownership(
        http_ready_exists=False, http_status=None, verdict='BLOCKED', port_released=None,
        timeout_seconds=0.4, stop_reason='timeout',
        failure={'type': 'TimeoutError', 'stage': 'application_startup_failure'},
        poll_events=[{'event': 'worker_spawned', 'elapsed_seconds': 0.0},
                     {'event': 'readiness_deadline_expired', 'elapsed_seconds': 0.41}])
    assert evaluate.evaluate_control('D', timeout)['result'] == 'PASS'
    late = dict(timeout)
    late['poll_events'] = [{'event': 'readiness_deadline_expired', 'elapsed_seconds': 30}]
    assert 'D_timeout_enforced' in evaluate.evaluate_control('D', late)['failed_ids']
    occupied = _ownership(
        http_ready_exists=False, verdict='BLOCKED', port_released=None,
        worker_failure={'type': 'OSError', 'stage': 'socket_binding', 'os_error': 10048},
        holder={'pid': 77, 'alive': True, 'port_still_bound': True, 'port': 9},
        process_cleanup={'owned': True, 'stopped': True, 'pid': 20})
    assert evaluate.evaluate_control('F', occupied)['result'] == 'PASS', evaluate.evaluate_control('F', occupied)['failed_ids']
    killed = dict(occupied, holder={'pid': 77, 'alive': False, 'port_still_bound': False, 'port': 9})
    assert 'F_holder_preserved' in evaluate.evaluate_control('F', killed)['failed_ids']
