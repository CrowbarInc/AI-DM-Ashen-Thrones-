"""Offline harness readiness for PR-PLAY-34.

Stops before scenario actions. Uses the existing controller, isolated stores,
and the PR-PLAY-33 process-launch repair. Does not change gameplay or provider
routing. Assertion evidence is written before the controller cleanup runs.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('pr_play_34_evaluate', OUT / 'evaluate.py')
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)

from tools.playtest import runner

OUTPUT = ROOT / 'artifacts' / 'atgb' / 'pr_play_34' / 'readiness'
CURRENT = {}
HOLDERS = []
K = ctypes.WinDLL('kernel32', use_last_error=True)
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class Entry(ctypes.Structure):
    _fields_ = [('dwSize', w.DWORD), ('cntUsage', w.DWORD), ('th32ProcessID', w.DWORD),
                ('th32DefaultHeapID', ctypes.c_size_t), ('th32ModuleID', w.DWORD),
                ('cntThreads', w.DWORD), ('th32ParentProcessID', w.DWORD),
                ('pcPriClassBase', w.LONG), ('dwFlags', w.DWORD), ('szExeFile', w.WCHAR * 260)]


K.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
K.CreateToolhelp32Snapshot.restype = w.HANDLE
K.Process32FirstW.argtypes = K.Process32NextW.argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
K.CloseHandle.argtypes = [w.HANDLE]
K.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
K.OpenProcess.restype = w.HANDLE
K.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]
K.GetProcessTimes.argtypes = [w.HANDLE, ctypes.POINTER(w.FILETIME), ctypes.POINTER(w.FILETIME),
                              ctypes.POINTER(w.FILETIME), ctypes.POINTER(w.FILETIME)]
K.GetCurrentProcess.restype = w.HANDLE


def secrets():
    from dotenv import dotenv_values
    env = {**dotenv_values(ROOT / '.env'), **os.environ}
    return [value for key, value in env.items() if isinstance(value, str) and len(value) > 8
            and any(part in key.lower() for part in ('key', 'token', 'secret', 'password', 'credential'))]


def redact(text, hidden):
    for value in hidden:
        text = text.replace(value, '[REDACTED]')
    return text


def dump(path, value, hidden):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(json.dumps(value, indent=2, default=str), hidden) + '\n', encoding='utf-8')


def process_table():
    handle = K.CreateToolhelp32Snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    result = {}
    try:
        entry = Entry()
        entry.dwSize = ctypes.sizeof(entry)
        more = K.Process32FirstW(handle, ctypes.byref(entry))
        if not more:
            raise ctypes.WinError(ctypes.get_last_error())
        while more:
            result[entry.th32ProcessID] = {
                'pid': entry.th32ProcessID, 'parent_pid': entry.th32ParentProcessID, 'image': entry.szExeFile}
            more = K.Process32NextW(handle, ctypes.byref(entry))
    finally:
        K.CloseHandle(handle)
    return result


def _filetime_iso(value):
    ticks = (value.dwHighDateTime << 32) + value.dwLowDateTime
    if not ticks:
        return None
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(ticks / 10000000 - 11644473600))


def describe_handle(handle):
    image = ctypes.create_unicode_buffer(32768)
    size = w.DWORD(len(image))
    created, exited, kernel_time, user_time = (w.FILETIME() for _ in range(4))
    info = {}
    if K.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)):
        info['executable'] = image.value
    else:
        info['executable_error'] = ctypes.get_last_error()
    if K.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                         ctypes.byref(kernel_time), ctypes.byref(user_time)):
        info['created_utc'] = _filetime_iso(created)
    else:
        info['created_error'] = ctypes.get_last_error()
    return info


def describe_pid(pid):
    handle = K.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return {'query_error': ctypes.get_last_error()}
    try:
        return describe_handle(handle)
    finally:
        K.CloseHandle(handle)


def ownership_view(process, hidden):
    table = process_table()
    pid = process.pid
    row = table.get(pid, {})
    children = [dict(item) for item in table.values() if item['parent_pid'] == pid]
    chain, cursor, seen = [], pid, set()
    while cursor and cursor not in seen and cursor in table:
        seen.add(cursor)
        item = dict(table[cursor])
        item.update(describe_pid(cursor))
        chain.append(item)
        cursor = item.get('parent_pid')
    for child in children:
        child.update(describe_pid(child['pid']))
    command = list(process.args) if isinstance(process.args, (list, tuple)) else [str(process.args)]
    worker = describe_handle(w.HANDLE(int(process._handle))) if getattr(process, '_handle', None) else {}
    controller = describe_handle(K.GetCurrentProcess())
    return {
        'controller_pid': os.getpid(),
        'controller_executable': controller.get('executable'),
        'controller_created_utc': controller.get('created_utc'),
        'popen_pid': pid,
        'parent_pid': row.get('parent_pid'),
        'reported_image': row.get('image'),
        'worker_executable': worker.get('executable'),
        'worker_created_utc': worker.get('created_utc'),
        'worker_query_error': worker.get('executable_error') or worker.get('created_error'),
        'base_executable': getattr(sys, '_base_executable', None),
        'launch_command': [redact(str(part), hidden) for part in command],
        'children': children,
        'parent_chain': chain,
        'process_alive': process.poll() is None,
        'exit_code': process.poll(),
    }


def session_view(run):
    path = run / 'data' / 'session.json'
    log_path = run / 'data' / 'session_log.jsonl'
    log_text = log_path.read_text(encoding='utf-8') if log_path.exists() else ''
    view = {
        'exists': path.exists(), 'path': str(path), 'debug_traces': [],
        'inside_isolated_store': path.resolve().is_relative_to((run / 'data').resolve()) if path.exists() else None,
        'log_entries': len([line for line in log_text.splitlines() if line.strip()]),
    }
    if path.exists():
        payload = json.loads(path.read_text(encoding='utf-8')).get('payload') or {}
        view.update({
            'campaign_started': payload.get('campaign_started'),
            'turn_counter': payload.get('turn_counter'),
            'chat_history_len': len(payload.get('chat_history') or []),
            'last_action_debug': payload.get('last_action_debug') is not None,
            'debug_traces': payload.get('debug_traces') or [],
            'active_scene_id': payload.get('active_scene_id'),
        })
    return view


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None


def json_lines(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def fingerprint(path):
    names = ('session.json', 'session_log.jsonl', 'campaign.json', 'character.json', 'world.json', 'combat.json')
    files = {}
    if path.exists():
        for name in names:
            file = path / name
            if file.is_file():
                stat = file.stat()
                files[name] = {'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns}
    return {'path': str(path), 'exists': path.exists(), 'files': files}


def port_released(port):
    if not port:
        return None
    with socket.socket() as probe:
        probe.settimeout(1)
        if probe.connect_ex(('127.0.0.1', port)) == 0:
            return False
    try:
        with socket.socket() as released:
            released.bind(('127.0.0.1', port))
    except OSError:
        return False
    return True


def orphans(pid):
    if not pid:
        return []
    table = process_table()
    return [row for row in table.values() if row['pid'] == pid or row['parent_pid'] == pid]


def persist_live(run, hidden):
    events = json_lines(run / 'diagnostics' / 'startup_events.jsonl')
    live = CURRENT.get('live') or {}
    if events:
        live['startup_event_pid'] = events[-1].get('pid')
        if live.get('reported_pid') is None:
            live['reported_pid'] = events[-1].get('pid')
    CURRENT['live'] = live
    dump(run / 'diagnostics' / 'readiness_snapshot.json', {
        'case': CURRENT.get('case'), 'captured_before_cleanup': True,
        'timeout_seconds': CURRENT.get('timeout_seconds'),
        'session_before': CURRENT.get('session_before'), 'live': live,
        'live_after_wait': CURRENT.get('live_after_wait'),
        'wait_exception': CURRENT.get('wait_exception'),
        'http_requests': CURRENT.get('http_requests', []),
        'http_status': CURRENT.get('http_status'),
    }, hidden)


def install_hooks(hidden):
    original = {name: getattr(runner, name) for name in ('start_worker', 'wait_for_http_ready', 'child_environment', 'request')}

    def offline_environment(*args, **kwargs):
        env = original['child_environment'](*args, **kwargs)
        env['ASHEN_DISABLE_PROVIDER_CALLS'] = '1'
        env['OPENAI_API_KEY'] = 'offline-placeholder'
        env['ASHEN_OPENING_RENDERER'] = '1'
        if CURRENT.get('case') == 'C':
            env.pop('ASHEN_PLAYTEST_DISABLE_SDK_RETRIES', None)
            env.pop('ASHEN_DISABLE_PROVIDER_RETRIES', None)
        return env

    def start(run, env):
        script = ROOT / 'artifacts' / 'pr_play_32' / 'worker_capture.py' if CURRENT.get('case') == 'E' else None
        process = original['start_worker'](run, env, script=script)
        CURRENT['process'] = process
        CURRENT['live'] = ownership_view(process, hidden)
        return process

    def request(base, method, path, *args, **kwargs):
        CURRENT.setdefault('http_requests', []).append({'method': method, 'path': path})
        if method != 'GET' or not str(path).startswith('/api/state'):
            raise RuntimeError('Campaign request forbidden')
        status, body = original['request'](base, method, path, *args, **kwargs)
        CURRENT['http_status'] = status
        return status, body

    def wait(process, run, timeout):
        CURRENT['timeout_seconds'] = timeout
        CURRENT['session_before'] = session_view(run)
        CURRENT['live'] = ownership_view(process, hidden)
        try:
            ready, base = original['wait_for_http_ready'](process, run, timeout)
        except BaseException as exc:
            CURRENT['wait_exception'] = type(exc).__name__
            CURRENT['live_after_wait'] = ownership_view(process, hidden)
            persist_live(run, hidden)
            raise
        CURRENT['ready'] = ready
        CURRENT['base'] = base
        live = ownership_view(process, hidden)
        live['ready'] = {key: ready.get(key) for key in (
            'pid', 'port', 'isolation_verified', 'diagnostics_enabled', 'sdk_retries', 'host_retries', 'data_dir')}
        live['reported_pid'] = ready.get('pid')
        CURRENT['live'] = live
        persist_live(run, hidden)
        raise KeyboardInterrupt

    runner.start_worker = start
    runner.wait_for_http_ready = wait
    runner.child_environment = offline_environment
    runner.request = request
    return original


def restore_hooks(original):
    runner.start_worker = original['start_worker']
    runner.wait_for_http_ready = original['wait_for_http_ready']
    runner.child_environment = original['child_environment']
    runner.request = original['request']


def start_holder():
    executable = getattr(sys, '_base_executable', None) or sys.executable
    process = subprocess.Popen(
        [executable, '-u', '-c',
         'import socket,sys; s=socket.socket(); s.bind(("127.0.0.1",0)); s.listen(); '
         'print(s.getsockname()[1], flush=True); sys.stdin.readline()'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    HOLDERS.append(process)
    line = process.stdout.readline().strip()
    if process.poll() is not None or not line:
        raise RuntimeError('Port holder exited before binding')
    return process, int(line)


def stop_holders():
    for process in HOLDERS:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def holder_state(process, port):
    alive = process.poll() is None
    bound = False
    if alive:
        with socket.socket() as probe:
            probe.settimeout(1)
            bound = probe.connect_ex(('127.0.0.1', port)) == 0
    return {'pid': process.pid, 'port': port, 'alive': alive, 'port_still_bound': bound}


def run_case(case, options, hidden):
    CURRENT.clear()
    CURRENT['case'] = case
    CURRENT['http_requests'] = []
    holder, port = (None, 0)
    if options.get('occupy'):
        holder, port = start_holder()
    started = time.monotonic()
    run, result = runner.run_playtest(
        scenario='FiveTurnGameplay', mode='Deterministic', port=port,
        output_root=OUTPUT / case, startup_timeout=options.get('startup_timeout'))
    live_doc = load_json(run / 'diagnostics' / 'readiness_snapshot.json') or {}
    live = live_doc.get('live') or {}
    ready_doc = load_json(run / 'diagnostics' / 'ready.json') or {}
    http_doc = load_json(run / 'diagnostics' / 'http_ready.json') or {}
    if ready_doc and not live.get('ready'):
        live['ready'] = {key: ready_doc.get(key) for key in (
            'pid', 'port', 'isolation_verified', 'diagnostics_enabled', 'sdk_retries', 'host_retries', 'data_dir')}
        live['reported_pid'] = ready_doc.get('pid')
    events = json_lines(run / 'diagnostics' / 'provider_usage.jsonl')
    popen_pid = live.get('popen_pid') or (result.get('process_cleanup') or {}).get('pid')
    worker_port = (live.get('ready') or {}).get('port') or ready_doc.get('port')
    obs = {
        'live': live,
        'session_before': live_doc.get('session_before') or {'exists': None},
        'session_after': session_view(run),
        'provider_events': events,
        'usage': load_json(run / 'diagnostics' / 'budget_snapshot.json') or {},
        'http_requests': live_doc.get('http_requests') or [],
        'http_status': http_doc.get('status', live_doc.get('http_status')),
        'http_ready_exists': http_doc != {},
        'startup_seconds': http_doc.get('startup_seconds'),
        'timeout_seconds': live_doc.get('timeout_seconds'),
        'verdict': result.get('verdict'),
        'failure': result.get('failure'),
        'stop_reason': result.get('stop_reason'),
        'steps': result.get('steps') or [],
        'process_cleanup': result.get('process_cleanup') or {},
        'orphans': orphans(popen_pid),
        'port': worker_port,
        'port_released': port_released(worker_port) if case in {'A', 'E'} else None,
        'poll_events': json_lines(run / 'diagnostics' / 'readiness_poll.jsonl'),
        'worker_failure': load_json(run / 'diagnostics' / 'worker_failure.json'),
        'holder': holder_state(holder, port) if holder is not None else None,
        'elapsed_seconds': round(time.monotonic() - started, 3),
    }
    obs['cleanup_succeeded'] = obs['process_cleanup'].get('stopped') is True and not obs['orphans']
    if case == 'F':
        obs['cleanup_succeeded'] = obs['cleanup_succeeded'] and obs['holder']['alive'] is True
    controls = ['A', 'B', 'G'] if case == 'A' else [case]
    verdicts = []
    for item in controls:
        verdict = evaluate.evaluate_control(item, obs)
        verdict['run'] = str(run.relative_to(ROOT)).replace('\\', '/')
        verdict['elapsed_seconds'] = obs['elapsed_seconds']
        verdicts.append(verdict)
    report = {
        'case': case, 'run': str(run.relative_to(ROOT)).replace('\\', '/'),
        'observation': obs, 'controls': verdicts,
        'provider_dispatches': sum(row.get('event') == 'dispatch_attempted' for row in events),
        'gameplay_turns': obs['session_after'].get('turn_counter') or 0,
    }
    dump(OUT / 'controls' / f'{case}.json', report, hidden)
    print(case, ','.join(f"{row['control']}={row['result']}" for row in verdicts), flush=True)
    return report


def user_dirs():
    paths = [ROOT / 'data']
    player = runner.player_campaign_dir_from_env(ROOT)
    if player not in paths:
        paths.append(player)
    return paths


def main():
    hidden = secrets()
    original = install_hooks(hidden)
    paths = user_dirs()
    before_user = [fingerprint(path) for path in paths]
    cases = []
    try:
        plan = [
            ('A', {'startup_timeout': None}),
            ('C', {'startup_timeout': None}),
            ('D', {'startup_timeout': 0.4}),
            ('E', {'startup_timeout': None}),
            ('F', {'startup_timeout': None, 'occupy': True}),
        ]
        for case, options in plan:
            if any(row.get('provider_dispatches') for row in cases):
                print('STOP provider dispatch observed', flush=True)
                break
            try:
                cases.append(run_case(case, options, hidden))
            except Exception as exc:
                dump(OUT / 'controls' / f'{case}_exception.json', {
                    'case': case, 'exception_type': type(exc).__name__, 'controls': [],
                    'provider_dispatches': 0, 'gameplay_turns': 0,
                }, hidden)
                print(case, 'EXCEPTION', type(exc).__name__, flush=True)
                cases.append({'case': case, 'controls': [], 'provider_dispatches': 0, 'gameplay_turns': 0,
                              'exception_type': type(exc).__name__})
    finally:
        restore_hooks(original)
        stop_holders()
    after_user = [fingerprint(path) for path in paths]
    controls = [row for case in cases for row in case['controls']]
    summary = {
        'controls': controls,
        'control_results': {row['control']: row['result'] for row in controls},
        'provider_requests': sum(case['provider_dispatches'] for case in cases),
        'provider_tokens': 0,
        'gameplay_turns': sum(case['gameplay_turns'] or 0 for case in cases),
        'user_campaign_changed': before_user != after_user,
        'user_campaign_before': before_user,
        'user_campaign_after': after_user,
        'cases': [{key: case.get(key) for key in ('case', 'run', 'provider_dispatches', 'gameplay_turns', 'exception_type')}
                  for case in cases],
    }
    dump(OUT / 'readiness_summary.json', summary, hidden)
    print(json.dumps({'controls': summary['control_results'], 'provider_requests': summary['provider_requests'],
                      'gameplay_turns': summary['gameplay_turns'],
                      'user_campaign_changed': summary['user_campaign_changed']}), flush=True)
    return summary


if __name__ == '__main__':
    main()
