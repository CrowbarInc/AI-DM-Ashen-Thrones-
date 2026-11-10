"""Five bounded offline startup-only cycles and one occupied-port control.

Uses the existing controller/worker. Stops immediately after HTTP readiness;
no campaign requests are sent. Synthetic transport, external socket denial,
placeholder credentials and the provider admission prohibition all remain on.
"""
from __future__ import annotations

import json
import os
import socket
from pathlib import Path

from tools.playtest import runner


def main():
    output = runner.ROOT/'artifacts/pr_play_15'
    output.mkdir(exist_ok=True)
    original_wait = runner.wait_for_http_ready
    original_environment = runner.child_environment
    starts = {}

    def offline_environment(*args, **kwargs):
        env = original_environment(*args, **kwargs)
        env['ASHEN_DISABLE_PROVIDER_CALLS'] = '1'
        return env

    def record_creation(process):
        # Popen returns the actual listener-owning interpreter in this harness.
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            creation, exit_time, kernel, user = (wintypes.FILETIME() for _ in range(4))
            if not ctypes.windll.kernel32.GetProcessTimes(wintypes.HANDLE(int(process._handle)),
                    ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel), ctypes.byref(user)):
                raise ctypes.WinError()
            timestamp = ((creation.dwHighDateTime << 32) + creation.dwLowDateTime)/10000000-11644473600
            starts[process.pid] = runner.datetime.fromtimestamp(timestamp, runner.timezone.utc).isoformat()

    ready_result = {}

    def stop_at_readiness(*args):
        record_creation(args[0])
        ready, base = original_wait(*args)
        ready_result.update(ready=ready, base=base)
        # Controlled unwind invokes the controller's normal cleanup/export path.
        raise KeyboardInterrupt

    def check(run, result, expected_ready):
        journal = run/'diagnostics/provider_usage.jsonl'
        entries = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
        dispatches = sum(e.get('event') == 'dispatch_attempted' for e in entries)
        assert dispatches == 0 and not result['steps'], result
        assert result['process_cleanup']['stopped']
        if expected_ready:
            assert entries and all(e['event'] == 'initialized' for e in entries)
            usage = json.loads((run/'diagnostics/budget_snapshot.json').read_text())
            assert usage['dispatched_requests'] == 0
            ready = ready_result['ready']
            with socket.socket() as probe:
                probe.settimeout(1)
                assert probe.connect_ex(('127.0.0.1', ready['port'])) != 0
            with socket.socket() as released:
                released.bind(('127.0.0.1', ready['port']))
            http = json.loads((run/'diagnostics/http_ready.json').read_text())
            assert http['startup_seconds'] < 30
            assert ready['opening_renderer']['selected']
            with runner.zipfile.ZipFile(result['evidence_zip']) as archive:
                assert archive.testzip() is None
            return {'run': str(run), 'pid': ready['pid'], 'process_created_utc': starts.get(ready['pid']),
                    'port': ready['port'], 'http': http, 'cleanup': result['process_cleanup'],
                    'port_released': True, 'no_orphan': True, 'provider_dispatches': dispatches,
                    'renderer': ready['opening_renderer'], 'limits': ready['limits']}
        failure = json.loads((run/'diagnostics/worker_failure.json').read_text())
        assert failure['stage'] == 'socket_binding' and failure['os_error'] in {48, 98, 10048}
        polls = [json.loads(line) for line in (run/'diagnostics/readiness_poll.jsonl').read_text().splitlines()]
        assert polls[-1]['event'] == 'worker_exited'
        assert result['elapsed_seconds'] < 30
        return {'run': str(run), 'failure': failure, 'cleanup': result['process_cleanup'],
                'elapsed_seconds': result['elapsed_seconds'], 'provider_dispatches': dispatches}

    runner.child_environment = offline_environment
    runner.wait_for_http_ready = stop_at_readiness
    measurements = {'cycles': [], 'failure_control': None}
    try:
        for index in range(5):
            ready_result.clear()
            run, result = runner.run_playtest(scenario='FiveTurnGameplay', mode='Deterministic',
                output_root=runner.ROOT/'artifacts/atgb/pr_play_15/cycles')
            measurements['cycles'].append(check(run, result, True))
            runner.write(output/'startup_cycles.json', measurements)
            print('Cycle', index+1, 'passed', flush=True)
        with socket.socket() as occupied:
            occupied.bind(('127.0.0.1', 0))
            occupied.listen()
            run, result = runner.run_playtest(scenario='FiveTurnGameplay', mode='Deterministic',
                port=occupied.getsockname()[1], output_root=runner.ROOT/'artifacts/atgb/pr_play_15/failure')
            measurements['failure_control'] = check(run, result, False)
            assert occupied.fileno() != -1
            measurements['failure_control']['original_listener_preserved'] = True
        runner.write(output/'startup_cycles.json', measurements)
        print('Occupied-port control passed', flush=True)
    finally:
        runner.child_environment = original_environment
        runner.wait_for_http_ready = original_wait


if __name__ == '__main__':
    main()
