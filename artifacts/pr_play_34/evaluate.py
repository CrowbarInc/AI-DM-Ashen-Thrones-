"""Pure readiness assertions for PR-PLAY-34.

No process launches, gameplay imports, or provider calls. The diagnostic
records each condition under its own identifier. A bootstrap session file is
not a failure. A started campaign, a nonzero turn, a gameplay action, or a
provider dispatch is.
"""
from __future__ import annotations

FORBIDDEN_TRACE_MARKERS = (
    'start_campaign', 'player_turn', 'chat', 'provider', 'narration', 'dispatch',
)
INTERPRETER_IMAGES = {'python.exe', 'pythonw.exe', 'py.exe'}


def check(identifier, expected, observed, passed, evidence, *, gating=True):
    return {
        'id': identifier,
        'expected': expected,
        'observed': observed,
        'passed': bool(passed),
        'evidence': evidence,
        'gating': gating,
        'cleanup_succeeded': None,
    }


def apply_cleanup(assertions, cleanup_succeeded):
    for row in assertions:
        row['cleanup_succeeded'] = cleanup_succeeded
    return assertions


def _ready(obs):
    return (obs.get('live') or {}).get('ready') or {}


def _children(obs):
    return list((obs.get('live') or {}).get('children') or [])


def _interpreter_children(obs):
    return [row for row in _children(obs)
            if str(row.get('image') or '').lower() in INTERPRETER_IMAGES]


def historical_assertions(obs):
    """Replay the five unlabeled PR-PLAY-33 wrapper asserts as separate rows.

    H3 (no children at all) stays visible and is not a harness-ownership gate.
    An interpreter descendant remains gating elsewhere.
    """
    live = obs.get('live') or {}
    ready = _ready(obs)
    popen_pid = live.get('popen_pid')
    parent = live.get('parent_pid')
    controller = live.get('controller_pid')
    children = _children(obs)
    return [
        check('H1_ready_pid_equals_popen', 'ready.pid equals the Popen pid',
              {'ready_pid': ready.get('pid'), 'popen_pid': popen_pid},
              ready.get('pid') == popen_pid and popen_pid is not None,
              {'source': 'ready.json pid compared with Popen.pid'}),
        check('H2_parent_is_controller', 'worker parent pid equals the controller pid',
              {'parent_pid': parent, 'controller_pid': controller},
              parent == controller and controller is not None,
              {'source': 'Toolhelp32 parent of the worker pid'}),
        check('H3_worker_has_no_children',
              'worker has no child processes (original diagnostic assumption)',
              {'child_count': len(children), 'children': children},
              len(children) == 0, {'source': 'Toolhelp32 children of the worker pid'},
              gating=False),
        check('H4_isolation_and_diagnostics',
              'isolation_verified and diagnostics_enabled are true',
              {'isolation_verified': ready.get('isolation_verified'),
               'diagnostics_enabled': ready.get('diagnostics_enabled')},
              ready.get('isolation_verified') is True and ready.get('diagnostics_enabled') is True,
              {'source': 'ready.json'}),
        check('H5_retries_zero', 'sdk_retries and host_retries are both 0',
              {'sdk_retries': ready.get('sdk_retries'), 'host_retries': ready.get('host_retries')},
              ready.get('sdk_retries') == 0 and ready.get('host_retries') == 0,
              {'source': 'ready.json'}),
    ]


def _traces(session):
    return list((session or {}).get('debug_traces') or [])


def _forbidden_traces(session):
    found = []
    for row in _traces(session):
        blob = ' '.join(str(row.get(key) or '') for key in ('kind', 'domain', 'operation')).lower()
        if any(marker in blob for marker in FORBIDDEN_TRACE_MARKERS):
            found.append(row.get('operation'))
    return found


def bootstrap_assertions(obs):
    before = obs.get('session_before') or {}
    after = obs.get('session_after') or {}
    events = list(obs.get('provider_events') or [])
    dispatches = [row for row in events if row.get('event') == 'dispatch_attempted']
    requests = list(obs.get('http_requests') or [])
    posts = [row for row in requests if row.get('method') != 'GET' or not str(row.get('path') or '').startswith('/api/state')]
    usage = obs.get('usage') or {}
    steps = list(obs.get('steps') or [])
    forbidden = _forbidden_traces(after)
    isolated = after.get('exists') is False or after.get('inside_isolated_store') is True
    return [
        check('G_session_file_allowed',
              'session.json may exist after GET /api/state; absence is not required',
              {'existed_before_request': before.get('exists'), 'exists_after_request': after.get('exists')},
              True, {'note': 'load_session creates a bootstrap document when the file is missing'}),
        check('G_isolated_store', 'session file, when present, is inside the isolated run store',
              {'inside_isolated_store': after.get('inside_isolated_store'), 'exists': after.get('exists')},
              isolated, {'path': after.get('path')}),
        check('G_campaign_not_started', 'campaign_started is false',
              {'campaign_started': after.get('campaign_started')},
              after.get('exists') is not True or after.get('campaign_started') is False,
              {'source': 'session payload'}),
        check('G_turn_counter_zero', 'turn_counter remains 0',
              {'turn_counter': after.get('turn_counter')},
              after.get('exists') is not True or after.get('turn_counter') == 0,
              {'source': 'session payload'}),
        check('G_no_gameplay_action',
              'no chat history, session-log entries, last action, or scenario steps',
              {'chat_history_len': after.get('chat_history_len'),
               'log_entries': after.get('log_entries'),
               'last_action_debug': after.get('last_action_debug'),
               'steps': len(steps)},
              (after.get('exists') is not True or (
                  (after.get('chat_history_len') or 0) == 0
                  and (after.get('log_entries') or 0) == 0
                  and after.get('last_action_debug') is not True))
              and steps == [],
              {'debug_traces': _traces(after)}),
        check('G_no_gameplay_traces',
              'debug traces do not record campaign start, chat, narration, or provider dispatch',
              {'forbidden_operations': forbidden, 'operations': [row.get('operation') for row in _traces(after)]},
              not forbidden, {'debug_traces': _traces(after)}),
        check('G_no_provider_dispatch', 'no provider dispatch and zero tokens',
              {'dispatch_events': len(dispatches),
               'dispatched_requests': usage.get('dispatched_requests', 0),
               'total_tokens': usage.get('total_tokens', 0)},
              not dispatches and usage.get('dispatched_requests', 0) == 0 and usage.get('total_tokens', 0) == 0,
              {'events': [row.get('event') for row in events]}),
        check('G_no_campaign_http', 'HTTP activity is limited to GET /api/state',
              {'requests': requests}, not posts, {'forbidden': posts}),
    ]


def ownership_assertions(obs):
    live = obs.get('live') or {}
    reported = live.get('reported_pid')
    popen_pid = live.get('popen_pid')
    rows = historical_assertions(obs)
    rows.extend([
        check('A_reported_pid_matches_popen', 'worker-reported pid equals the Popen pid',
              {'reported_pid': reported, 'popen_pid': popen_pid},
              reported == popen_pid and popen_pid is not None,
              {'startup_events_pid': live.get('startup_event_pid')}),
        check('A_executable_is_base', 'worker image is the base interpreter, not a venv redirector',
              {'image': live.get('worker_executable'), 'base': live.get('base_executable')},
              _same_path(live.get('worker_executable'), live.get('base_executable')),
              {'controller_executable': live.get('controller_executable'),
               'launch_command': live.get('launch_command')}),
        check('A_no_interpreter_descendant',
              'the worker has no Python interpreter child (console hosts may exist)',
              {'interpreter_children': _interpreter_children(obs)},
              not _interpreter_children(obs),
              {'children': _children(obs)}),
    ])
    return rows


def _same_path(left, right):
    if not left or not right:
        return False
    return str(left).replace('\\', '/').lower() == str(right).replace('\\', '/').lower()


def http_assertions(obs, *, expect_ready):
    status = obs.get('http_status')
    ready_file = obs.get('http_ready_exists')
    if expect_ready:
        return [
            check('A_http_ready', 'HTTP readiness file exists and status is 200',
                  {'http_ready_exists': ready_file, 'http_status': status},
                  ready_file is True and status == 200,
                  {'startup_seconds': obs.get('startup_seconds'),
                   'timeout_seconds': obs.get('timeout_seconds')}),
            check('A_controller_not_false_pass',
                  'controller stops before actions with verdict INCONCLUSIVE',
                  {'verdict': obs.get('verdict'), 'steps': obs.get('steps')},
                  obs.get('verdict') == 'INCONCLUSIVE' and not obs.get('steps'),
                  {'failure': obs.get('failure'),
                   'note': 'KeyboardInterrupt unwind yields INCONCLUSIVE before any action'}),
        ]
    return [
        check('F_http_not_ready', 'controller does not record HTTP readiness',
              {'http_ready_exists': ready_file, 'http_status': status, 'verdict': obs.get('verdict')},
              ready_file is not True and obs.get('verdict') != 'PASS',
              {'failure': obs.get('failure'), 'poll_events': obs.get('poll_events')}),
    ]


def cleanup_assertions(obs):
    cleanup = obs.get('process_cleanup') or {}
    return [
        check('B_cleanup_stopped', 'owned worker process was stopped',
              cleanup, cleanup.get('stopped') is True and cleanup.get('owned') is True,
              {'exit_code': cleanup.get('exit_code')}),
        check('B_no_orphan', 'no remaining process whose parent or pid is the owned worker',
              {'orphans': obs.get('orphans')}, not obs.get('orphans'),
              {'popen_pid': (obs.get('live') or {}).get('popen_pid')}),
        check('B_port_released', 'the worker loopback port is closed and bindable',
              {'port_released': obs.get('port_released'), 'port': obs.get('port')},
              obs.get('port_released') is True, {'port': obs.get('port')}),
    ]


def failure_assertions(obs):
    failure = obs.get('worker_failure') or {}
    return [
        check('C_failure_detected', 'worker failure record exists and startup is not ready',
              {'worker_failure': failure, 'verdict': obs.get('verdict')},
              bool(failure) and obs.get('verdict') == 'BLOCKED' and obs.get('http_ready_exists') is not True,
              {'poll_events': obs.get('poll_events'), 'controller_failure': obs.get('failure')}),
        check('C_failure_preserved', 'failure stage and error type were written before cleanup',
              {'type': failure.get('type'), 'stage': failure.get('stage'), 'os_error': failure.get('os_error')},
              bool(failure.get('type')) and bool(failure.get('stage')),
              {'path': 'diagnostics/worker_failure.json'}),
    ]


def timeout_assertions(obs):
    events = list(obs.get('poll_events') or [])
    deadline = next((row for row in events if row.get('event') == 'readiness_deadline_expired'), None)
    limit = obs.get('timeout_seconds')
    elapsed = None if deadline is None else deadline.get('elapsed_seconds')
    return [
        check('D_timeout_enforced', 'readiness deadline expired at or below the configured timeout',
              {'elapsed_seconds': elapsed, 'timeout_seconds': limit, 'poll_events': events},
              deadline is not None and limit is not None and elapsed is not None and elapsed <= limit + 0.25,
              {'controller_failure': obs.get('failure')}),
        check('D_no_false_readiness', 'timeout does not produce HTTP readiness or verdict PASS',
              {'http_ready_exists': obs.get('http_ready_exists'), 'verdict': obs.get('verdict')},
              obs.get('http_ready_exists') is not True and obs.get('verdict') != 'PASS',
              {'stop_reason': obs.get('stop_reason')}),
    ]


def occupied_port_assertions(obs):
    failure = obs.get('worker_failure') or {}
    holder = obs.get('holder') or {}
    return [
        check('F_conflict_detected', 'worker records socket_binding address-in-use and does not become ready',
              {'stage': failure.get('stage'), 'os_error': failure.get('os_error'),
               'http_ready_exists': obs.get('http_ready_exists'), 'verdict': obs.get('verdict')},
              failure.get('stage') == 'socket_binding'
              and failure.get('os_error') in {48, 98, 10048}
              and obs.get('http_ready_exists') is not True
              and obs.get('verdict') != 'PASS',
              {'poll_events': obs.get('poll_events')}),
        check('F_holder_preserved', 'the isolated process holding the port is still alive and still bound',
              {'holder_pid': holder.get('pid'), 'alive': holder.get('alive'),
               'port_still_bound': holder.get('port_still_bound')},
              holder.get('alive') is True and holder.get('port_still_bound') is True,
              {'port': holder.get('port')}),
        check('F_cleanup_is_owned_only', 'cleanup pid is the harness worker, not the port holder',
              {'cleanup_pid': (obs.get('process_cleanup') or {}).get('pid'),
               'worker_pid': (obs.get('live') or {}).get('popen_pid'),
               'holder_pid': holder.get('pid')},
              (obs.get('process_cleanup') or {}).get('pid') == (obs.get('live') or {}).get('popen_pid')
              and (obs.get('process_cleanup') or {}).get('pid') != holder.get('pid'),
              {'orphans': obs.get('orphans')}),
    ]


def evaluate_control(control, obs):
    """Return one control verdict. Observations must already be captured."""
    selected = {
        'A': lambda: ownership_assertions(obs) + http_assertions(obs, expect_ready=True) + bootstrap_assertions(obs),
        'B': lambda: cleanup_assertions(obs),
        'C': lambda: failure_assertions(obs) + cleanup_assertions(obs)[:2] + bootstrap_assertions(obs),
        'D': lambda: timeout_assertions(obs) + cleanup_assertions(obs)[:2],
        'E': lambda: ownership_assertions(obs) + http_assertions(obs, expect_ready=True) + bootstrap_assertions(obs) + cleanup_assertions(obs),
        'F': lambda: occupied_port_assertions(obs) + cleanup_assertions(obs)[:2] + bootstrap_assertions(obs),
        'G': lambda: bootstrap_assertions(obs),
    }[control]
    assertions = apply_cleanup(selected(), obs.get('cleanup_succeeded'))
    failed = [row for row in assertions if row['gating'] and not row['passed']]
    return {
        'control': control,
        'result': 'FAIL' if failed else 'PASS',
        'failed_ids': [row['id'] for row in failed],
        'assertions': assertions,
        'cleanup_succeeded': obs.get('cleanup_succeeded'),
    }


def historical_failure_ids(obs):
    """Which original unlabeled asserts the saved evidence can decide."""
    return [row['id'] for row in historical_assertions(obs) if not row['passed']]
