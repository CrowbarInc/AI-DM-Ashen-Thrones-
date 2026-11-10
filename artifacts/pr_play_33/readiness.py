"""Offline controller readiness, stopped before the scenario action loop."""
import json
import os
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.playtest import runner
from investigate import processes, save


def main():
    original_start = runner.start_worker
    original_wait = runner.wait_for_http_ready
    original_env = runner.child_environment
    original_request = runner.request
    rows = []
    current = {}
    def offline_environment(*args, **kwargs):
        env = original_env(*args, **kwargs)
        # Provider admission disabled in addition to synthetic transport and
        # the existing external socket denial. Never serialize credentials.
        env['ASHEN_DISABLE_PROVIDER_CALLS'] = '1'
        env['OPENAI_API_KEY'] = 'offline-placeholder'
        env['ASHEN_OPENING_RENDERER'] = '1'
        current['provider_admission_disabled'] = True
        return env
    def start(run, env):
        script = ROOT/'artifacts/pr_play_32/worker_capture.py' if current['observer'] else None
        process = original_start(run, env, script=script)
        current['popen_pid'] = process.pid
        return process
    def request(base, method, path, *args, **kwargs):
        assert method == 'GET' and path.startswith('/api/state'), 'Campaign request forbidden'
        current.setdefault('http_requests', []).append(dict(method=method, path=path))
        return original_request(base, method, path, *args, **kwargs)
    def wait(process, run, timeout):
        ready, base = original_wait(process, run, timeout)
        table = processes()
        current.update(ready=ready, base=base, process=table[process.pid],
            children=[r for r in table.values() if r['parent_pid'] == process.pid])
        assert ready['pid'] == process.pid
        assert table[process.pid]['parent_pid'] == os.getpid()
        assert not current['children']
        assert ready['isolation_verified'] and ready['diagnostics_enabled']
        assert ready['sdk_retries'] == ready['host_retries'] == 0
        # Deliberate controlled unwind: existing controller finally performs
        # its normal bounded cleanup and evidence export before any POST.
        raise KeyboardInterrupt
    runner.start_worker, runner.wait_for_http_ready = start, wait
    runner.child_environment, runner.request = offline_environment, request
    try:
        for observer in (False, True):
            for failure in (False, True):
                current.clear()
                current.update(observer=observer, occupied_port_control=failure)
                with socket.socket() as occupied:
                    if failure:
                        occupied.bind(('127.0.0.1', 0)); occupied.listen()
                    run, result = runner.run_playtest(scenario='FiveTurnGameplay', mode='Deterministic',
                        output_root=ROOT/'artifacts/atgb/pr_play_33/readiness',
                        port=occupied.getsockname()[1] if failure else 0)
                    assert result['steps'] == [], result
                    assert result['process_cleanup']['stopped'], result
                    pid = current['popen_pid']
                    table = processes()
                    assert pid not in table and not any(r['parent_pid'] == pid for r in table.values())
                    journal = run/'diagnostics/provider_usage.jsonl'
                    events = [json.loads(s) for s in journal.read_text().splitlines()] if journal.exists() else []
                    assert not any(e.get('event') == 'dispatch_attempted' for e in events)
                    usage = result['provider_usage']
                    assert usage.get('dispatched_requests', 0) == 0
                    assert usage.get('total_tokens', 0) == 0
                    assert not (run/'data/session.json').exists()
                    if failure:
                        details = json.loads((run/'diagnostics/worker_failure.json').read_text())
                        assert details['stage'] == 'socket_binding'
                        assert details['os_error'] in {48, 98, 10048}
                        assert occupied.fileno() != -1
                        current['failure_details'] = details
                        current['original_listener_preserved'] = True
                    else:
                        port = current['ready']['port']
                        with socket.socket() as probe:
                            probe.settimeout(1)
                            assert probe.connect_ex(('127.0.0.1', port)) != 0
                        with socket.socket() as released:
                            released.bind(('127.0.0.1', port))
                        current['port_released'] = True
                        assert usage['dispatched_requests'] == usage['total_tokens'] == 0
                        assert events and all(e['event'] == 'initialized' for e in events)
                    current.update(run=str(run.relative_to(ROOT)), cleanup=result['process_cleanup'],
                        remaining_owned_processes=[], provider_requests=0, provider_tokens=0,
                        gameplay_turns=0, campaign_initializations=0,
                        accounting_events=events, usage=usage,
                        controller_verdict=result['verdict'],
                        note='Controller scenario verdict is intentionally incomplete: stopped at readiness, no actions.')
                    rows.append(dict(current))
                    save('offline_readiness.json', rows)
                    print('PASS', 'observer' if observer else 'module', 'occupied port' if failure else 'readiness', flush=True)
    finally:
        runner.start_worker, runner.wait_for_http_ready = original_start, original_wait
        runner.child_environment, runner.request = original_env, original_request
    save('readiness_verdict.json', dict(pass_all=True, cases=len(rows), provider_requests=0,
         provider_tokens=0, gameplay_turns=0, campaign_initializations=0))


if __name__ == '__main__':
    main()
