"""HTTP scenario controller with owned-process cleanup and bounded evidence export."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, build_opener

from tools.atgb.isolation import prepare_isolated_store, player_campaign_dir_from_env
from tools.atgb.driver import repository_revision
from tools.playtest.analysis import classify, compare
from tools.playtest.browser import observation

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT/'artifacts/atgb/automated_playtests'
CASES = ('success', 'truncation', 'invalid_json', 'envelope', 'semantic', 'safe_nonresolution',
         'exception', 'admission', 'empty', 'incomplete')
OVERLAY_CASES = ('authored_overlay',)
GAMEPLAY_CASES = ('turn2_exception', 'turn3_invalid_json')
CAPS = {'input': 200000, 'output': 20000, 'total': 220000}
TIMEOUT_CAPS = {'preflight': 30, 'startup': 30, 'request': 90, 'scenario': 180, 'evidence': 30, 'shutdown': 5}


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


def load_scenario(name):
    if name not in {'CampaignOpening', 'ScriptedObservation', 'FiveTurnGameplay'}:
        raise ValueError('Unknown scenario')
    path = ROOT/'tools/playtest/scenarios'/f'{name}.json'
    value = json.loads(path.read_text(encoding='utf-8'))
    validate_scenario(value)
    return value


def validate_scenario(s):
    required = {'id', 'version', 'description', 'fixture', 'execution_modes', 'actions',
                'expected_invariants', 'maximum_action_count', 'provider_request_ceiling',
                'token_budgets', 'timeouts', 'evidence_requirements', 'stop_conditions'}
    if not required <= s.keys() or s['fixture'] != 'frontier-gate-v1':
        raise ValueError('Missing scenario contract or unpinned fixture')
    if not 1 <= len(s['actions']) <= s['maximum_action_count'] <= 10:
        raise ValueError('Action ceiling invalid')
    kinds = [a['kind'] for a in s['actions']]
    if kinds[:3] != ['initialize_campaign', 'capture_baseline', 'start_campaign'] or kinds.count('start_campaign') != 1 or kinds.count('initialize_campaign') != 1:
        raise ValueError('One New Campaign and one Start Campaign required')
    allowed = {'initialize_campaign', 'capture_baseline', 'start_campaign', 'capture_final_state',
               'observe_scene', 'verify_state', 'npc_interaction', 'examine_object', 'rules_action', 'movement', 'player_turn'}
    if any(k not in allowed for k in kinds):
        raise ValueError('Unknown step')
    turns = [a for a in s['actions'] if a['kind'] == 'player_turn']
    if turns:
        if len(turns) != 5 or len({a.get('step_id') for a in turns}) != 5:
            raise ValueError('Five unique ordered turns required')
        for a in turns:
            if not {'step_id', 'player_input', 'interaction_category', 'expected_response_properties',
                    'allowed_state_changes', 'forbidden_state_changes', 'evaluation_criteria',
                    'timeout', 'stop_conditions', 'subject_terms', 'required_scene'} <= a.keys():
                raise ValueError('Incomplete player-turn contract')
            if not 0 < a['timeout'] <= s['timeouts']['request']:
                raise ValueError('Unbounded turn timeout')
    if not 1 <= s['provider_request_ceiling'] <= 6:
        raise ValueError('Request ceiling exceeds established controlled scope')
    for k, cap in CAPS.items():
        if not 0 < s['token_budgets'][k] <= cap:
            raise ValueError('Scenario cannot increase established aggregate ceilings')
    for k, cap in TIMEOUT_CAPS.items():
        if not 0 < s['timeouts'][k] <= cap:
            raise ValueError('Timeout must be positive and bounded')


def verify_gameplay_grounding(s):
    if s['id'] != 'FiveTurnGameplay':
        return None
    from tools.atgb.baseline import load_baseline
    source, _ = load_baseline(ROOT)
    world = json.loads((source/'world.json').read_text(encoding='utf-8'))
    for action in s['actions']:
        if action['kind'] != 'player_turn':
            continue
        scene = json.loads((source/'scenes'/f"{action['required_scene']}.json").read_text(encoding='utf-8'))['scene']
        if action.get('required_npc') and not any(n.get('id') == action['required_npc'] and n.get('location') == action['required_scene'] for n in world['npcs']):
            raise ValueError('NPC fixture grounding missing')
        if action.get('required_object') and not any(o.get('id') == action['required_object'] for o in scene['interactables']):
            raise ValueError('Object fixture grounding missing')
        if not set(action.get('allowed_destinations', [])) <= {e['target_scene_id'] for e in scene['exits']}:
            raise ValueError('Movement fixture grounding missing')
    return True


def child_environment(run, scenario, mode, case, inherited=None):
    # Configuration file values are read in memory only; never serialized as an environment dump.
    from dotenv import dotenv_values
    env = {**{k: v for k, v in dotenv_values(ROOT/'.env').items() if v is not None},
           **(dict(os.environ) if inherited is None else inherited)}
    for key in ('ASHEN_PIN_PROVIDER_MODEL',):
        if env.get(key, '').strip():
            raise ValueError('Pinned model override is outside this harness scope')
    for kind, cap in scenario['token_budgets'].items():
        key = f'ASHEN_PROVIDER_{kind.upper()}_TOKEN_LIMIT'
        current = int(env.get(key, cap))
        if current <= 0:
            raise ValueError('Invalid inherited token ceiling')
        env[key] = str(min(cap, current))
    request_limit = int(env.get('ASHEN_PROVIDER_REQUEST_LIMIT', scenario['provider_request_ceiling']))
    if request_limit <= 0:
        raise ValueError('Invalid inherited request ceiling')
    env['ASHEN_PROVIDER_REQUEST_LIMIT'] = str(min(request_limit, scenario['provider_request_ceiling']))
    if case == 'admission':
        env['ASHEN_PROVIDER_INPUT_TOKEN_LIMIT'] = '1'
    env.update(ASHEN_DATA_DIR=str(run/'data'), ASHEN_PROVIDER_USAGE_PATH=str(run/'diagnostics/provider_usage.jsonl'),
               ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1', ASHEN_PLAYTEST_DISABLE_SDK_RETRIES='1',
               ASHEN_DISABLE_PROVIDER_RETRIES='1', ASHEN_GENERATION_DIAGNOSTICS='1')
    if mode != 'Live':
        env['OPENAI_API_KEY'] = 'offline-placeholder'
    elif env.get('ASHEN_DISABLE_PROVIDER_CALLS', '').lower() in {'1', 'true', 'yes', 'on'}:
        raise ValueError('Inherited provider disabled flag blocks Live mode')
    # Synthetic responses traverse admission; the SDK is replaced and external connects are denied.
    if mode != 'Live':
        env['ASHEN_DISABLE_PROVIDER_CALLS'] = '0'
    return env


def bounded_log(pipe, path, secrets):
    size = 0
    with path.open('w', encoding='utf-8') as dest:
        while True:
            chunk = pipe.readline(4096)
            if not chunk:
                break
            text = chunk.decode('utf-8', errors='replace')
            for secret in secrets:
                text = text.replace(secret, '[REDACTED]')
            if size < 262144:
                dest.write(text[:262144-size])
                dest.flush()
                size += len(text)
    pipe.close()


def stop_owned(process, timeout):
    if process is None:
        return {'owned': False, 'stopped': True}
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=timeout)
    return {'owned': True, 'pid': process.pid, 'stopped': process.poll() is not None,
            'exit_code': process.returncode}


def request(base, method, path, timeout, body=None):
    data = json.dumps(body).encode() if body is not None else (b'{}' if method == 'POST' else None)
    req = Request(base+path, data=data, method=method, headers={'Content-Type': 'application/json'})
    # Ignore machine HTTP proxies for loopback traffic.
    try:
        response = build_opener(ProxyHandler({})).open(req, timeout=timeout)
    except HTTPError as exc:
        response = exc
    with response:
        content = response.read(2*1024*1024+1)
        if len(content) > 2*1024*1024:
            raise ValueError('API evidence exceeds bounded response size')
        return response.status, json.loads(content)


def snapshot(run, label, base, timeout):
    folder = run/label
    status, state = request(base, 'GET', '/api/state?ui_mode=debug', timeout)
    if status != 200:
        raise ValueError('State capture failed')
    write(folder/'api_state.json', state)
    return snapshot_files(run, label)


def snapshot_files(run, label):
    folder = run/label
    docs = {}
    for path in (run/'data').rglob('*'):
        if not path.is_file() or path.name.startswith('.'):
            continue
        if path.stat().st_size > 2*1024*1024:
            raise ValueError('Campaign evidence exceeds file ceiling')
        rel = path.relative_to(run/'data')
        target = folder/'persistent'/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        if path.suffix == '.json':
            docs[rel.as_posix()] = json.loads(path.read_text(encoding='utf-8'))
        elif path.suffix == '.jsonl':
            docs[rel.as_posix()] = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    write(folder/'documents.json', docs)
    return docs


def export(run, timeout=30):
    started = time.monotonic()
    selected = [p for folder in ('configuration', 'baseline', 'after', 'diagnostics', 'reports', 'screenshots', 'turns', 'opening')
                for p in (run/folder).rglob('*') if p.is_file()]
    total = sum(p.stat().st_size for p in selected)
    if total > 32*1024*1024:
        raise ValueError('Evidence exceeds 32 MiB ceiling')
    manifest = []
    for p in selected:
        if time.monotonic()-started > timeout:
            raise TimeoutError('Evidence collection timeout')
        manifest.append({'path': p.relative_to(run).as_posix(), 'bytes': p.stat().st_size,
                         'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    write(run/'evidence/manifest.json', {'files': manifest, 'manifest_self_hash': 'Excluded to avoid recursion'})
    archive = run/'evidence/evidence.zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for p in [*selected, run/'evidence/manifest.json']:
            if time.monotonic()-started > timeout:
                raise TimeoutError('Evidence compression timeout')
            z.write(p, p.relative_to(run).as_posix())
    return archive


def summarize(result):
    return '\n'.join([
        '# ASHEN THRONES — AUTOMATED PLAYTEST', '',
        f"Scenario: {result['scenario'].get('id', 'Unavailable')}", f"Mode: {result['mode']}",
        f"Repository revision: {result['repository'].get('revision')}; dirty={result['repository'].get('worktree_dirty')}",
        f"Overall: **{result['verdict']}**", f"Provider attempts: {result['provider_usage'].get('dispatched_requests', 'Unavailable')}",
        f"Usage (input/output/total): {result['provider_usage'].get('input_tokens')}/{result['provider_usage'].get('output_tokens')}/{result['provider_usage'].get('total_tokens')}",
        f"Opening: {result.get('opening_acceptance')}", f"Structural validation: {result.get('structural_validation')}",
        f"Provider completion: {result.get('provider_completion')}",
        f"Semantic validation: {result.get('semantic_validation')}", f"State integrity: {result['state_comparison'].get('integrity', 'Unavailable')}",
        f"UI: {result['ui']['status']}", f"Primary observed failure: {result.get('failure_classification')}",
        'Root cause: Not established.', '', 'Evidence: diagnostics/provider_usage.jsonl; baseline/; after/; reports/result.json.',
        f"Remaining uncertainty: {'; '.join(result['uncertainties'])}",
        'Recommended investigation: inspect the first evidenced failing stage; external review before any live invocation.',
        f"Evidence ZIP: {result['evidence_zip']}", ''])


def run_playtest(*, scenario='CampaignOpening', mode='Deterministic', authorize_live=False,
                 case='success', port=0, capture_response=False, output_root=None, startup_timeout=None):
    root = Path(output_root or OUTPUT).resolve()
    # Artifacts must never be written inside canonical/player data or pinned sources.
    player = player_campaign_dir_from_env(ROOT)
    for protected in ((ROOT/'data').resolve(), player):
        if root == protected or protected in root.parents or root in protected.parents:
            raise ValueError('Unsafe artifact root')
    root.mkdir(parents=True, exist_ok=True)
    run = root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:12])
    run.mkdir(exist_ok=False)
    for folder in ('configuration', 'baseline', 'after', 'diagnostics', 'reports', 'evidence', 'screenshots'):
        (run/folder).mkdir()
    result = {'schema_version': 1, 'run_id': run.name, 'timestamp': datetime.now(timezone.utc).isoformat(),
              'mode': mode, 'scenario': {'id': scenario}, 'repository': repository_revision(ROOT),
              'environment_verification': {}, 'provider_usage': {}, 'state_comparison': {},
              'structural_validation': None, 'semantic_validation': None, 'opening_acceptance': None,
              'ui': observation(), 'steps': [], 'uncertainties': [], 'verdict': 'BLOCKED',
              'evidence_zip': str(run/'evidence/evidence.zip')}
    process, logger, s, env = None, None, None, None
    infrastructure = None
    before, after = None, None
    base = None
    started = time.monotonic()
    try:
        s = load_scenario(scenario)
        grounded = verify_gameplay_grounding(s)
        result['scenario'] = s
        if mode not in s['execution_modes'] or case not in (*CASES, *OVERLAY_CASES, *(GAMEPLAY_CASES if scenario == 'FiveTurnGameplay' else ())):
            raise ValueError('Unsupported mode or synthetic fixture')
        if mode == 'Live' and (not authorize_live or scenario not in {'CampaignOpening', 'FiveTurnGameplay'} or case != 'success'):
            raise PermissionError('Live requires invocation authorization and reviewed scenario')
        if mode == 'Live' and scenario == 'FiveTurnGameplay' and not capture_response:
            raise PermissionError('Five-turn Live requires response capture')
        if not 0 <= port <= 65535:
            raise ValueError('Invalid port')
        env = child_environment(run, s, mode, case)
        if mode == 'Live' and scenario == 'FiveTurnGameplay' and any(env.get(k, '').lower() in {'1', 'true', 'yes', 'on'} for k in ('ASHEN_DISABLE_LIVE_INTERPRETATION', 'ASHEN_DISABLE_EXPRESSION_GENERATION')):
            raise ValueError('Five-turn Live requires normal interpretation and expression configuration')
        if mode == 'Live' and not env.get('OPENAI_API_KEY', '').strip():
            raise ValueError('Live credentials unavailable')
        env['ASHEN_OPENING_RESPONSE_CAPTURE'] = '1' if capture_response else '0'
        for dependency in ('fastapi', 'uvicorn', 'openai', 'httpx'):
            __import__(dependency)
        prepare_isolated_store(run/'data', scenario_id=s['id'], repo=ROOT, player_campaign_dir=player)
        write(run/'configuration/scenario.json', s)
        from game.opening_presentation_renderer import opening_renderer_diagnostics
        cfg = {'scenario_id': s['id'], 'mode': mode, 'fixture_response': case, 'port': port,
               'player_data': str(player), 'capture_response': capture_response,
               'opening_renderer': opening_renderer_diagnostics()}
        write(run/'configuration/run.json', cfg)
        result['environment_verification'] = {'repository_root': str(ROOT), 'python': sys.executable,
            'python_version': sys.version.split()[0], 'fixture_hash_verified': True,
            'five_actions_fixture_grounded': grounded,
            'provider_request_ceiling': int(env['ASHEN_PROVIDER_REQUEST_LIMIT']),
            'token_allowances': {k: int(env[f'ASHEN_PROVIDER_{k.upper()}_TOKEN_LIMIT']) for k in CAPS},
            'live_authorization': authorize_live and mode == 'Live', 'retry_configuration': 'SDK=0, host=0',
            'response_capture_opt_in': capture_response,
            'opening_renderer': cfg['opening_renderer']}
        print('Configured ceilings:', result['environment_verification']['provider_request_ceiling'],
              'requests;', result['environment_verification']['token_allowances'], 'tokens; retries=0', flush=True)
        if time.monotonic()-started > s['timeouts']['preflight']:
            raise TimeoutError('Preflight deadline')
        infrastructure = 'application_startup_failure'
        # Windows venv python.exe may redirect to another PID. Launch the real
        # interpreter and retain this environment's packages so the PID we own
        # is the process holding the listening socket.
        executable = getattr(sys, '_base_executable', sys.executable)
        env['PYTHONPATH'] = os.pathsep.join(dict.fromkeys([str(ROOT), *[p for p in sys.path if p and 'site-packages' in p], env.get('PYTHONPATH', '')]))
        process = subprocess.Popen([executable, '-u', '-m', 'tools.playtest.worker', str(run)],
            cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        secrets = [v for k, v in env.items() if v and len(v)>6 and any(part in k.lower() for part in ('key', 'secret', 'password', 'credential', 'token'))]
        logger = threading.Thread(target=bounded_log, args=(process.stdout, run/'diagnostics/application.log', secrets), daemon=True)
        logger.start()
        deadline = time.monotonic()+min(startup_timeout or s['timeouts']['startup'], s['timeouts']['startup'])
        ready = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError('Owned server exited during startup')
            path = run/'diagnostics/ready.json'
            if path.exists():
                try:
                    ready = json.loads(path.read_text(encoding='utf-8'))
                except (OSError, json.JSONDecodeError):
                    time.sleep(.05)
                    continue
                if ready['pid'] != process.pid or Path(ready['data_dir']).resolve() != run/'data' or not ready['isolation_verified']:
                    raise RuntimeError('Isolation attestation mismatch')
                base = f"http://127.0.0.1:{ready['port']}"
                try:
                    if request(base, 'GET', '/api/state', min(1, max(.01, deadline-time.monotonic())))[0] == 200:
                        break
                except (OSError, URLError, ValueError):
                    pass
            time.sleep(.05)
        else:
            raise TimeoutError('Application startup deadline')
        result['environment_verification']['application'] = ready
        if not ready['diagnostics_enabled'] or ready['sdk_retries'] or ready['host_retries']:
            raise RuntimeError('Worker safety attestation invalid')
        infrastructure = None
        scenario_deadline = time.monotonic()+s['timeouts']['scenario']
        for action in s['actions']:
            kind = action['kind']
            timeout = min(action.get('timeout', s['timeouts']['request']), scenario_deadline-time.monotonic())
            if timeout <= 0:
                infrastructure = 'api_transport_failure'
                raise TimeoutError('Scenario deadline')
            row = {'action': kind, 'ok': False}
            result['steps'].append(row)
            try:
                if kind == 'player_turn':
                    from tools.playtest.gameplay import execute_turn, prerequisite_failure
                    usage_path = run/'diagnostics/budget_snapshot.json'
                    current_usage = json.loads(usage_path.read_text(encoding='utf-8')) if usage_path.exists() else {}
                    if current_usage.get('dispatched_requests', 0) >= int(env['ASHEN_PROVIDER_REQUEST_LIMIT']):
                        result['steps'].pop()
                        result['stop_reason'] = 'provider_budget_exhaustion'
                        break
                    state = snapshot_files(run, 'after')
                    divergence = prerequisite_failure(action, state)
                    if divergence:
                        result['steps'].pop()
                        result['divergence'] = {'step_id': action['step_id'], 'kind': 'scenario_limitation',
                                               'reason': divergence}
                        result['stop_reason'] = 'scenario_divergence'
                        break
                    row.update(step_id=action['step_id'], player_input=action['player_input'])
                    row.update(execute_turn(run, action, base, timeout, request, snapshot,
                                            [r.get('dm_response', '') for r in result['steps'][:-1] if r['action'] == 'player_turn']))
                    if row['stop']:
                        result['stop_reason'] = row['findings'][0]['category'] if row['findings'] else 'turn_stopped'
                elif kind in {'capture_baseline', 'capture_final_state'}:
                    docs = snapshot(run, 'baseline' if kind == 'capture_baseline' else 'after', base, timeout)
                    if kind == 'capture_baseline':
                        before = docs
                    else:
                        after = docs
                    row['ok'] = True
                elif kind in {'observe_scene', 'verify_state'}:
                    status, body = request(base, 'GET', '/api/state', timeout)
                    row.update(http_status=status, response=body)
                    row['ok'] = status == 200
                    if kind == 'verify_state':
                        public = body.get('public_state', body)
                        row['ok'] = row['ok'] and all(public.get('ui', {}).get(k) == v for k, v in action.get('expect', {}).items())
                else:
                    endpoint, payload = {
                        'initialize_campaign': ('/api/new_campaign', None),
                        'start_campaign': ('/api/start_campaign', None),
                        'npc_interaction': ('/api/chat', action.get('request')),
                        'examine_object': ('/api/chat', action.get('request')),
                        'rules_action': ('/api/action', action.get('request')),
                        'movement': ('/api/action', action.get('request')),
                    }[kind]
                    status, body = request(base, 'POST', endpoint, timeout, payload)
                    row.update(http_status=status, response=body)
                    row['ok'] = status == 200 and body.get('ok', body.get('status') == 'ok') is True
                    if kind == 'start_campaign':
                        row['narration_present'] = bool((body.get('gm_output') or {}).get('player_facing_text'))
                        if scenario == 'FiveTurnGameplay':
                            (run/'opening').mkdir()
                            opening_state = snapshot(run, 'opening', base, min(timeout, 10))
                            result['opening_state_comparison'] = compare(before, opening_state, accepted=row['ok'], opening_response=body)
                            row['ok'] = row['ok'] and result['opening_state_comparison']['integrity']
                if not row['ok']:
                    break
            except (OSError, URLError, ValueError):
                infrastructure = 'api_transport_failure'
                row['ok'] = False
                raise
        # Capture after a failed opening too; never submit a second opening.
        if before is not None and after is None:
            after = snapshot(run, 'after', base, min(10, s['timeouts']['request']))
    except KeyboardInterrupt:
        infrastructure = 'interrupted_execution'
        result['verdict'] = 'INCONCLUSIVE'
    except Exception as exc:
        if infrastructure is None:
            infrastructure = 'environment_preflight_failure'
        result['failure'] = {'type': type(exc).__name__, 'stage': infrastructure}
        if scenario == 'FiveTurnGameplay':
            result['stop_reason'] = 'timeout' if isinstance(exc, (TimeoutError, socket.timeout)) else infrastructure
        # Never write exception strings, which may contain sensitive external data.
    finally:
        result['process_cleanup'] = stop_owned(process, s['timeouts']['shutdown'] if s else 5)
        if logger:
            logger.join(timeout=5)
        if before is not None and after is None:
            try:
                after = snapshot_files(run, 'after')
                result['uncertainties'].append('Final API capture unavailable; persistent state collected after owned-process shutdown')
            except (OSError, ValueError):
                result['uncertainties'].append('Final persistent snapshot unavailable')
        if scenario == 'FiveTurnGameplay' and result['steps'] and result['steps'][-1]['action'] == 'player_turn' and not result['steps'][-1]['ok'] and 'mechanical' not in result['steps'][-1]:
            row = result['steps'][-1]
            if row.get('step_id') and (run/'turns'/row['step_id']).exists():
                try:
                    snapshot_files(run, f"turns/{row['step_id']}/after")
                    row['state_after'] = f"turns/{row['step_id']}/after/documents.json"
                    row['mechanical'] = {'status': 'INCONCLUSIVE', 'completed_interaction': False}
                except (OSError, ValueError):
                    pass
        events = []
        ledger = run/'diagnostics/provider_usage.jsonl'
        if ledger.exists():
            try:
                events = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()]
            except ValueError:
                result['uncertainties'].append('Provider journal incomplete or malformed')
        snap_path = run/'diagnostics/budget_snapshot.json'
        usage = json.loads(snap_path.read_text(encoding='utf-8')) if snap_path.exists() else {}
        result['provider_usage'] = usage
        if ledger.exists() and usage:
            from tools.atgb.accounting import inspect_ledger
            result['accounting_reconciliation'] = inspect_ledger(ledger, usage)
        allowances = result['environment_verification'].get('token_allowances', {})
        usage['allowances'] = allowances
        usage['remaining_budget'] = {k: allowances[k]-usage[k+'_tokens'] if usage.get(k+'_tokens') is not None else None for k in allowances}
        usage['budget_rejections'] = [e for e in events if e.get('event') == 'rejected']
        result['correlation'] = {'harness_run_id': run.name, 'scenario_id': scenario,
            'provider_run_ids': sorted({e['run_id'] for e in events if e.get('run_id')}),
            'opening_attempt_ids': sorted({e['opening_attempt_id'] for e in events if e.get('opening_attempt_id')}),
            'provider_attempt_ids': sorted({e['attempt_id'] for e in events if e.get('attempt_id')}),
            'limitation': 'Missing native identifiers remain unavailable; harness run ID maps to isolated journal, not fabricated provider IDs.'}
        providers = [e for e in events if e.get('stage') == 'provider_response']
        outcomes = [e for e in events if e.get('stage') == 'opening_outcome']
        outcome = outcomes[-1] if outcomes else {}
        accepted = outcome.get('opening_accepted') is True
        result['structural_validation'] = providers[-1].get('structured_validation_result') if providers else None
        result['provider_completion'] = {k: providers[-1].get(k) for k in
            ('provider_status', 'provider_finish_reason', 'provider_output_limit_exhausted', 'classification')} if providers else None
        result['semantic_validation'] = outcome.get('semantic_classification')
        result['opening_acceptance'] = outcome.get('opening_accepted')
        if before is not None and after is not None:
            start_rows = [r for r in result['steps'] if r['action'] == 'start_campaign']
            api_accepted = bool(start_rows and start_rows[0].get('response', {}).get('ok') is True and
                                start_rows[0].get('response', {}).get('session', {}).get('campaign_started') is True)
            result['state_comparison'] = result.get('opening_state_comparison') or compare(
                before, after, accepted=accepted if outcomes else api_accepted,
                opening_response=start_rows[0].get('response') if start_rows else None)
        result['provider_response_evidence'] = ['diagnostics/'+p.name for p in (run/'opening_response_evidence').glob('*.json')]
        for p in (run/'opening_response_evidence').glob('*.json'):
            shutil.copy2(p, run/'diagnostics'/p.name)
        if not result['provider_response_evidence']:
            result['uncertainties'].append('Bounded provider response unavailable (disabled, capture failed, or response unparsed)')
        if not providers or not outcomes:
            result['uncertainties'].append('Required provider/acceptance diagnostic artifact unavailable')
        commits = sum(e.get('gameplay_committed') is True for e in outcomes)
        result['opening_commits_observed'] = commits
        result['provider_exposure'] = {'live_calls': 0 if mode != 'Live' or process is None else usage.get('dispatched_requests'),
                                       'transport': 'production' if mode == 'Live' else 'synthetic_sdk_with_external_socket_denial'}
        integrity = result['state_comparison'].get('integrity')
        if infrastructure:
            result['verdict'] = 'BLOCKED' if infrastructure in {'environment_preflight_failure', 'application_startup_failure'} else 'INCONCLUSIVE'
        elif integrity is False or not accepted or any(not step['ok'] for step in result['steps']):
            result['verdict'] = 'FAIL' if outcomes or integrity is False else 'INCONCLUSIVE'
        elif not providers or not outcomes or not usage or result.get('accounting_reconciliation', {}).get('status') != 'recorded':
            result['verdict'] = 'INCONCLUSIVE'
        else:
            invariants = s['expected_invariants']
            checks = {'campaign_started': result['state_comparison'].get('campaign_started'),
                      'opening_commits': commits, 'turn_delta': result['state_comparison'].get('turn_delta'),
                      'log_delta': result['state_comparison'].get('log_delta')}
            result['invariants'] = {k: {'expected': v, 'actual': checks.get(k), 'pass': checks.get(k) == v} for k, v in invariants.items()}
            result['verdict'] = 'PASS' if all(v['pass'] for v in result['invariants'].values()) else 'FAIL'
        result['failure_classification'] = None if result['verdict'] == 'PASS' else classify(events, infrastructure=infrastructure, integrity=integrity)
        result['uncertainties'].append('Rendered UI, live adequacy, and gameplay quality not established by deterministic API execution')
        result['elapsed_seconds'] = round(time.monotonic()-started, 3)
        if scenario == 'FiveTurnGameplay' and s:
            from tools.playtest.gameplay import finalize
            (run/'reports/GAMEPLAY_REPORT.md').write_text(finalize(result), encoding='utf-8')
        write(run/'reports/result.json', result)
        (run/'reports/SUMMARY.md').write_text(summarize(result), encoding='utf-8')
        write(run/'diagnostics/execution_log.json', {'steps': [{'action': r['action'], 'ok': r['ok'], 'http_status': r.get('http_status')} for r in result['steps']], 'cleanup': result['process_cleanup']})
        try:
            export(run, s['timeouts']['evidence'] if s else 30)
        except (OSError, ValueError, TimeoutError) as exc:
            result['verdict'] = 'INCONCLUSIVE'
            result['uncertainties'].append('Evidence export failed: '+type(exc).__name__)
            write(run/'reports/result.json', result)
            (run/'reports/SUMMARY.md').write_text(summarize(result), encoding='utf-8')
    return run, result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=['CampaignOpening', 'ScriptedObservation', 'FiveTurnGameplay'], default='CampaignOpening')
    parser.add_argument('--mode', choices=['Deterministic', 'Live', 'ScriptedGameplay'], default='Deterministic')
    parser.add_argument('--authorize-live-provider', action='store_true')
    parser.add_argument('--fixture-response', choices=(*CASES, *OVERLAY_CASES, *GAMEPLAY_CASES), default='success')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--capture-response', action='store_true')
    parser.add_argument('--latest', action='store_true')
    args = parser.parse_args(argv)
    if args.latest:
        paths = sorted(OUTPUT.glob('*/reports/result.json'), key=lambda p: p.stat().st_mtime)
        if not paths:
            print('No playtest results available')
            return 2
        p = paths[-1]
        result = json.loads(p.read_text(encoding='utf-8'))
        print(result['verdict'], p.parent/'SUMMARY.md', result['evidence_zip'], sep='\n')
        return 0
    run, result = run_playtest(scenario=args.scenario, mode=args.mode, authorize_live=args.authorize_live_provider,
        case=args.fixture_response, port=args.port, capture_response=args.capture_response)
    print(result['verdict'], run/'reports/SUMMARY.md', result['evidence_zip'], sep='\n')
    return 0 if result['verdict'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
