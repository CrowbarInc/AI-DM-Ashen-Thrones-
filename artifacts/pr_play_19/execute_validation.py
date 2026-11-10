"""One offline readiness cycle or one authorized opening-only live attempt."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.playtest import runner
OUT = ROOT/'artifacts/pr_play_19'
mode = sys.argv[1]
assert mode in {'offline', 'live'}
os.environ['ASHEN_OPENING_RENDERER'] = '1'
os.environ['ASHEN_PROVIDER_REQUEST_LIMIT'] = '1'
original_env = runner.child_environment
original_wait = runner.wait_for_http_ready
original_popen = subprocess.Popen
original_request = runner.request
timings = []

def request(*args, **kwargs):
    start = time.perf_counter()
    result = original_request(*args, **kwargs)
    timings.append({'method': args[1], 'path': args[2], 'seconds': time.perf_counter()-start,
                    'http_status': result[0]})
    return result
runner.request = request

if mode == 'offline':
    # Real TCP connection with no external networking or provider access.
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        with socket.create_connection(listener.getsockname(), timeout=2) as client:
            accepted, _ = listener.accept()
            with accepted:
                client.sendall(b'PR-PLAY-19')
                assert accepted.recv(32) == b'PR-PLAY-19'
    runner.write(OUT/'loopback.json', {'passed': True, 'offline': True})
    def environment(*args, **kwargs):
        env = original_env(*args, **kwargs)
        env['ASHEN_DISABLE_PROVIDER_CALLS'] = '1'
        return env
    runner.child_environment = environment
    def ready(*args):
        result = original_wait(*args)
        raise KeyboardInterrupt
    runner.wait_for_http_ready = ready
else:
    offline = json.loads((OUT/'offline_summary.json').read_text())
    assert offline['passed']
    # Durable exclusive marker prohibits a repeat attempt through this script.
    marker = OUT/'live_attempt_authorized_once.json'
    if marker.exists():
        # A controller bootstrap error before worker creation is not an opening attempt.
        assert not list((ROOT/'artifacts/atgb/pr_play_19/live').rglob('ready.json'))
        assert not list((ROOT/'artifacts/atgb/pr_play_19/live').rglob('actual_assembled_request.json'))
    else:
        with marker.open('x') as f:
            json.dump({'authorization': 'User PR-PLAY-19 request', 'maximum_attempts': 1}, f)
    class ObservedPopen(original_popen):
        def __init__(self, command, *args, **kwargs):
            if command[2:4] == ['-m', 'tools.playtest.worker']:
                command = [command[0], '-u', str(OUT/'worker_capture.py'), command[4]]
            super().__init__(command, *args, **kwargs)
    runner.subprocess.Popen = ObservedPopen
    def ready(*args):
        attestation, base = original_wait(*args)
        assert attestation['model'] == 'gpt-4.1-mini'
        assert attestation['opening_renderer']['selected']
        assert attestation['limits'][0] == 1
        assert attestation['sdk_retries'] == attestation['host_retries'] == 0
        return attestation, base
    runner.wait_for_http_ready = ready

run, result = runner.run_playtest(scenario='CampaignOpening', mode='Live' if mode == 'live' else 'Deterministic',
    authorize_live=mode == 'live', capture_response=True, output_root=ROOT/'artifacts/atgb/pr_play_19'/mode)
runner.write(OUT/(mode+'_timings.json'), timings)
runner.write(OUT/(mode+'_run.json'), {'run': str(run), 'verdict': result['verdict']})
if mode == 'offline':
    ready = json.loads((run/'diagnostics/ready.json').read_text())
    with socket.socket() as released:
        released.bind(('127.0.0.1', ready['port']))
    passed = ((run/'diagnostics/http_ready.json').exists() and not result['steps'] and
              result['process_cleanup']['stopped'] and result['provider_usage']['dispatched_requests'] == 0)
    runner.write(OUT/'offline_summary.json', {'passed': passed, 'port_released': True, 'run': str(run),
                 'provider_requests': result['provider_usage']['dispatched_requests']})
    assert passed
print(json.dumps({'run': str(run), 'verdict': result['verdict'], 'failure': result.get('failure'),
                  'requests': result['provider_usage'].get('dispatched_requests')}))
