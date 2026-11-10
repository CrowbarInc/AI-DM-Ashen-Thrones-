"""Recovery evidence only: run unchanged tests with fail-closed network/storage guards."""
import copy
import time
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent/sys.argv[1]
sys.path.insert(0, str(ROOT))
OUT.mkdir(parents=True,exist_ok=True)
os.chdir(ROOT)
os.environ['ASHEN_TEST_EVIDENCE_DIR'] = str(OUT)
for key in ('ASHEN_DISABLE_PROVIDER_CALLS', 'ASHEN_DISABLE_LIVE_INTERPRETATION',
            'ASHEN_DISABLE_EXPRESSION_GENERATION', 'ASHEN_DISABLE_PROVIDER_RETRIES',
            'ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'):
    os.environ[key] = '1'

def hashes():
    paths = []
    for folder in ('game', 'tests', 'data', 'static', 'prompts'):
        if (ROOT/folder).exists():
            paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file()
                         and '__pycache__' not in p.parts and p.suffix != '.pyc')
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

before = hashes()
(OUT/'entry_hashes.json').write_text(json.dumps(before, indent=2))
(OUT/'entry_git_status.txt').write_bytes(subprocess.check_output(['git', 'status', '--short']))
blocked = []
def network_guard(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo'):
        destination = args[1] if event == 'socket.connect' else args[0]
        host = destination[0] if isinstance(destination, tuple) else destination
        # Windows asyncio implements its wakeup pipe using a loopback socketpair.
        if host in ('127.0.0.1', '::1', 'localhost'):
            return
        blocked.append({'event': event, 'destination': str(args[1] if event == 'socket.connect' else args[0])})
        raise RuntimeError('Recovery audit forbids network access')
sys.addaudithook(network_guard)

import pytest
from tests.helpers.storage_isolation import install
install(ROOT/'development/tmp/t05_composition_main_storage')

class Capture:
    def __init__(self):
        self.node = None
        self.turns = {}
        self.failures = []
        self.decisions = []

    def pytest_collection_finish(self, session):
        (OUT/'collected_nodes.json').write_text(json.dumps([i.nodeid for i in session.items], indent=2))
        import game.api as api
        from game import storage
        from fastapi.testclient import TestClient
        original_post = TestClient.post
        original_projection = api.project_player_response
        original_decision = api.deterministic_conversational_decision
        capture = self
        def snap():
            try:
                return copy.deepcopy({'session': storage.load_session(), 'character': storage.load_character(),
                                      'world': storage.load_world(), 'log': storage.load_log()})
            except Exception as exc:
                return {'unavailable': str(exc)}
        def project(payload):
            if capture.active:
                capture.raw.append(copy.deepcopy(payload))
            return original_projection(payload)
        def decision(*args, **kwargs):
            result = original_decision(*args, **kwargs)
            if capture.active:
                capture.decisions.append({'player_text': kwargs.get('player_text'),
                    'reason': getattr(result, 'reason', None), 'decision': str(result) if result else None})
            return result
        def post(client, url, *args, **kwargs):
            selected = capture.node and (capture.node in wanted or 'test_pr_play_post_npc_handoff.py' in capture.node)
            if not selected:
                return original_post(client, url, *args, **kwargs)
            capture.active = True
            capture.raw = []
            capture.decisions = []
            pre = snap()
            try:
                response = original_post(client, url, *args, **kwargs)
                capture.turns.setdefault(capture.node, []).append({'url': str(url), 'request': kwargs.get('json'),
                    'http_status': response.status_code, 'response': response.json(), 'raw_before_projection': capture.raw,
                    'routing': capture.decisions, 'before': pre, 'after': snap()})
                return response
            finally:
                capture.active = False
        import game.immutable_valid_response as ivr
        import game.gm_resolution_decision as grd
        import game.perception_grounding as pg
        capture.stage_events = []
        def wrap(module, name):
            original = getattr(module, name)
            def traced(*args, **kwargs):
                started_ns = time.perf_counter_ns()
                value = original(*args, **kwargs)
                duration_ns = time.perf_counter_ns() - started_ns
                if capture.active:
                    event = {'node': capture.node, 'function': module.__name__+'.'+name,
                             'args': copy.deepcopy(args), 'kwargs': copy.deepcopy(kwargs), 'result': copy.deepcopy(value), 'duration_ns': duration_ns}
                    capture.stage_events.append(event)
                return value
            setattr(module, name, traced)
        for module, names in [(ivr, ['validate_generated_response','_unsupported_perception','seal_accepted_response']),
                              (grd, ['audit_narration_against_decision','audit_narrated_claims']),
                              (pg, ['classify_perception_invention'])]:
            for name in names: wrap(module, name)
        if hasattr(ivr, '_closed_surface_preparation'): wrap(ivr, '_closed_surface_preparation')
        self.active = False
        api.project_player_response = project
        api.deterministic_conversational_decision = decision
        TestClient.post = post

    def pytest_runtest_setup(self, item):
        self.node = item.nodeid

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        if report.failed:
            self.failures.append({'nodeid': item.nodeid, 'phase': report.when, 'traceback': report.longreprtext,
                                  'fixtures': item.fixturenames})

old = json.loads((ROOT/'artifacts/pr_play_adjacent_regression/classification_matrix.json').read_text())
wanted = {f['test'] for f in old['failures']}
modules = old['selection']['modules']
modules += ['tests/test_pr_br_continuation18_immutable_boundary.py', 'tests/test_perception_narration_authority_audible_non_invention.py']
capture = Capture()
args = modules + ['tests/test_pr_play_post_npc_handoff.py', '-q', '--tb=long',
                  '--junitxml='+str(OUT/'baseline_junit.xml'),
                  '--basetemp='+str(ROOT/'development/tmp/t05_composition_main_pytest'), '-p', 'no:cacheprovider']
(OUT/'command.json').write_text(json.dumps({'executable': sys.executable, 'args': args}, indent=2))
code = pytest.main(args, plugins=[capture])
(OUT/'http_capture.json').write_text(json.dumps(capture.turns, indent=2, default=str))
(OUT/'stage_events.json').write_text(json.dumps(capture.stage_events, indent=2, default=str))
(OUT/'failures.json').write_text(json.dumps(capture.failures, indent=2))
after = hashes()
integrity = {'protected_files': len(before), 'changed': [p for p in before if before[p] != after.get(p)],
             'added': sorted(set(after)-set(before)), 'network_attempts_blocked': blocked,
             'live_provider_calls': 0, 'pytest_exit_code': code}
(OUT/'execution_integrity.json').write_text(json.dumps(integrity, indent=2))
print(json.dumps(integrity))
