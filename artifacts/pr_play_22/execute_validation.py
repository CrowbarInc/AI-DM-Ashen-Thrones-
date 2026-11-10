"""One offline preflight and one bounded Player HTTP experiment; no production edits."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.playtest import runner
from tools.playtest.gameplay import diff, read_events, classify_turn, evaluate
from tools.atgb.isolation import prepare_isolated_store, player_campaign_dir_from_env

OUT = ROOT/'artifacts/pr_play_22'
mode = sys.argv[1]
assert mode in {'offline', 'live'}
os.environ['ASHEN_OPENING_RENDERER'] = '1'
os.environ['ASHEN_PROVIDER_REQUEST_LIMIT'] = '6'
run = ROOT/'artifacts/atgb/pr_play_22'/mode
run.mkdir(parents=True, exist_ok=False)
for f in ('configuration', 'diagnostics', 'baseline', 'after', 'opening', 'reports'):
    (run/f).mkdir()
write = runner.write
scenario = runner.load_scenario('FiveTurnGameplay')
env = runner.child_environment(run, scenario, 'Live' if mode == 'live' else 'Deterministic', 'success')
env['ASHEN_OPENING_RESPONSE_CAPTURE'] = '1'
if mode == 'offline':
    env['ASHEN_DISABLE_PROVIDER_CALLS'] = '1'
else:
    assert json.loads((OUT/'offline_summary.json').read_text())['passed']
    with (OUT/'live_attempt_authorized_once.json').open('x') as stream:
        json.dump({'maximum_initializations': 1, 'request_ceiling': 6, 'authorization': 'PR-PLAY-22 user mission'}, stream)
assert env.get('OPENAI_API_KEY', '').strip()
player = player_campaign_dir_from_env(ROOT)
prepare_isolated_store(run/'data', scenario_id='FiveTurnGameplay', repo=ROOT, player_campaign_dir=player)
write(run/'configuration/scenario.json', scenario)
write(run/'configuration/run.json', {'scenario_id': 'FiveTurnGameplay', 'mode': 'Live' if mode == 'live' else 'Deterministic',
      'fixture_response': 'success', 'port': 0, 'player_data': str(player), 'capture_response': True})
write(OUT/'repository_status.json', {'branch': subprocess.check_output(['git','branch','--show-current'], cwd=ROOT, text=True).strip(),
      'status': subprocess.check_output(['git','status','--short'], cwd=ROOT, text=True),
      'revision': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()})
paths = ['game/api.py','game/api_ui_mode.py','game/gm.py','game/provider_budget.py','game/opening_presentation_renderer.py',
         'scripts/run_live_playtest.ps1','tools/playtest/runner.py','tools/playtest/worker.py','tools/playtest/gameplay.py']
write(OUT/(mode+'_source_hashes.json'), {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
env['PYTHONPATH'] = os.pathsep.join([str(ROOT), *[p for p in sys.path if 'site-packages' in p]])
exe = getattr(sys, '_base_executable', sys.executable)
if mode == 'offline':
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0)); listener.listen(1)
        with socket.create_connection(listener.getsockname(), timeout=2) as client:
            accepted, _ = listener.accept()
            with accepted:
                client.sendall(b'PR-PLAY-22'); assert accepted.recv(32) == b'PR-PLAY-22'
    # Exercise production admission with synthetic invocations, never a provider client.
    test_env = dict(env, ASHEN_DISABLE_PROVIDER_CALLS='0', ASHEN_PROVIDER_USAGE_PATH=str(run/'diagnostics/offline_budget_test.jsonl'))
    code = '''from game import provider_budget as b
from types import SimpleNamespace as N
b.initialize_accounting()
for i in range(6):
 a=b.admit_request(purpose='offline_budget_test',owner='test',estimated_input=1,max_output=1,model='gpt-4.1-mini')
 assert not a.refusal
 a.dispatch(lambda **kw: N(usage=N(input_tokens=1,output_tokens=1,total_tokens=2),id='synthetic',model='gpt-4.1-mini'))
a=b.admit_request(purpose='seventh',owner='test',estimated_input=1,max_output=1,model='gpt-4.1-mini')
assert a.refusal == 'request ceiling'
try: a.dispatch(lambda **kw: (_ for _ in ()).throw(AssertionError('must not invoke')))
except b.ProviderBudgetRefused: pass
else: raise AssertionError('seventh dispatch allowed')
assert b.snapshot()['dispatched_requests']==6
print('Six synthetic dispatches; seventh refused; zero live requests')
'''
    checked = subprocess.run([exe, '-c', code], env=test_env, cwd=ROOT, capture_output=True, text=True, timeout=15)
    write(OUT/'offline_budget_verification.json', {'returncode': checked.returncode, 'stdout': checked.stdout, 'stderr': checked.stderr})
    assert checked.returncode == 0

process = None
result = {'mode': mode, 'steps': [], 'stop_reason': None, 'ordinary_attempted': 0, 'ordinary_completed': 0}
started = time.monotonic()
base = None
def call(method, path, body=None):
    assert 'debug' not in path and 'author' not in path
    assert body is None or body.get('ui_mode', 'player') == 'player'
    path += ('&' if '?' in path else '?')+'ui_mode=player'
    start = time.monotonic()
    status, response = runner.request(base, method, path, 90, body)
    row = {'method': method, 'path': path, 'payload': body, 'http_status': status,
           'response': response, 'api_latency_seconds': time.monotonic()-start}
    result['steps'].append(row)
    write(run/'reports/interactions.json', result['steps'])
    return row
def capture(label):
    folder = run/label
    folder.mkdir(parents=True, exist_ok=True)
    row = call('GET', '/api/state')
    assert row['http_status'] == 200
    write(folder/'public_state.json', row['response'])
    return runner.snapshot_files(run, label)
def text(row):
    return (row['response'].get('gm_output') or {}).get('player_facing_text') or ''
def failed(row, offset, before=None, after=None):
    events = read_events(run)[offset:]
    write(run/'reports'/f"events_{len(result['steps']):02}.json", events)
    bad = [e for e in events if e.get('classification') in {'provider_error','json_parse_failure','missing_structured_envelope','structured_validation_failure','empty_provider_content'}
           or e.get('provider_status') in {'incomplete','failed','cancelled'} or e.get('event') == 'rejected'
           or e.get('semantic_classification') == 'rejected']
    row['completion'] = classify_turn(row['http_status'], row['response'], events)
    if before is not None and after is not None:
        action = dict(next(a for a in scenario['actions'] if a['kind'] == 'player_turn'))
        action.update(step_id=f"T{result['ordinary_attempted']}", player_input=row['payload']['text'],
                      interaction_category='interaction', allowed_destinations=[])
        row['evaluation'] = evaluate(action, row['http_status'], row['response'], before, after, events)
        return row['evaluation']['stop']
    return row['completion']['stop'] or bool(bad)

try:
    process = subprocess.Popen([exe, '-u', str(OUT/'worker_capture.py'), str(run)], cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    secrets = [v for k,v in env.items() if len(v)>6 and any(s in k.lower() for s in ('key','token','secret','password','credential'))]
    logger = threading.Thread(target=runner.bounded_log, args=(process.stdout,run/'diagnostics/application.log',secrets), daemon=True)
    logger.start()
    ready, base = runner.wait_for_http_ready(process,run,30)
    assert ready['model']=='gpt-4.1-mini' and ready['opening_renderer']['selected']
    assert ready['sdk_retries']==ready['host_retries']==0 and ready['limits'][0]<=6
    assert ready['diagnostics_enabled']
    # Validate all configured routing models without changing the configured provider.
    from dotenv import dotenv_values
    config = {**dotenv_values(ROOT/'.env'), **os.environ}
    safe = {k: config.get(k) for k in ('MODEL_NAME','DEFAULT_MODEL_NAME','HIGH_PRECISION_MODEL_NAME','RETRY_ESCALATION_MODEL_NAME','ENABLE_MODEL_ROUTING')}
    write(OUT/'safe_configuration.json', {'model_configuration': safe, 'credentials_present': bool(config.get('OPENAI_API_KEY')),
        'renderer': 1, 'player_mode_only': True, 'request_ceiling': ready['limits'][0], 'sdk_retries': 0, 'host_retries': 0})
    assert all(v in (None, '', 'gpt-4.1-mini') for k,v in safe.items() if k!='ENABLE_MODEL_ROUTING'), 'Model variation outside scope'
    if mode == 'offline':
        capture('baseline')
        result['stop_reason']='offline_preflight_complete_no_initialization'
    else:
        new = call('POST','/api/new_campaign',{'ui_mode':'player'})
        assert new['http_status']==200
        before = capture('baseline')
        offset=len(read_events(run))
        opening = call('POST','/api/start_campaign',{'ui_mode':'player'})
        after = capture('opening')
        write(run/'opening/state_diff.json',diff(before,after))
        result['campaign_initialized']=not failed(opening,offset)
        result['opening']=text(opening)
        write(OUT/'live_result.json', result)
        if not result['campaign_initialized']:
            result['stop_reason']='campaign_initialization_failure'
        else:
            target=next((t for t in ('tavern runner','gate serjeant','guard') if t in text(opening).lower()),None)
            if not target:
                result['stop_reason']='no_supported_npc_in_published_opening'
            else:
                previous=text(opening)
                for turn in range(1,6):
                    budget=json.loads((run/'diagnostics/budget_snapshot.json').read_text())
                    if budget['dispatched_requests']>=ready['limits'][0]:
                        result['stop_reason']='provider_budget_exhaustion'; break
                    if turn==1:
                        action = f"I approach the {target} and ask what they're offering." if target=='tavern runner' else f'I approach the {target} and ask what I should know about the situation here.'
                    elif turn in (2,3):
                        sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+',previous) if len(s.strip())>25]
                        if not sentences:
                            result['stop_reason']='no_meaningful_followup'; break
                        quote=sentences[0][:500]
                        action=f'I ask the {target} to explain more about this: "{quote}" What can they tell me?' if turn==2 else f'I ask the {target}: "{quote}" How do they know that?'
                    elif turn==4:
                        if 'notice board' in (result['opening']+' '+previous).lower():
                            action='I decide to read the notice board and walk over to examine the posted notices.'
                        else:
                            result['stop_reason']='no_supported_meaningful_choice'; break
                    else:
                        if 'patrol' in previous.lower():
                            action='I examine the notice about the missing patrol more closely. What details are actually written there?'
                        else:
                            result['stop_reason']='no_supported_consequence_followup'; break
                    folder=f'turns/T{turn}'
                    before=capture(folder+'/before'); offset=len(read_events(run))
                    result['ordinary_attempted']+=1
                    row=call('POST','/api/chat',{'text':action,'ui_mode':'player'})
                    after=capture(folder+'/after')
                    write(run/folder/'api_response.json',row)
                    write(run/folder/'state_diff.json',diff(before,after))
                    if failed(row,offset,before,after):
                        result['stop_reason']='ordinary_turn_decisive_failure'; break
                    previous=text(row)
                    if previous == result['opening']:
                        result['stop_reason']='meaningful_continuation_unavailable'; break
                    result['ordinary_completed']+=int(row['completion']['gameplay_completed'])
                else:
                    result['stop_reason']='five_ordinary_turns_complete'
        capture('after')
except BaseException as exc:
    result['error_type']=type(exc).__name__
    result['stop_reason']=result['stop_reason'] or 'environment_or_controller_failure'
finally:
    ordinary = [row for row in result['steps'] if row.get('path', '').startswith('/api/chat')]
    result['http_requests_completed'] = sum(row['http_status'] == 200 for row in ordinary)
    result['ordinary_actions_attempted'] = result['ordinary_attempted']
    result['ordinary_actions_executed'] = sum(row.get('completion', {}).get('action_executed', False) for row in ordinary)
    result['meaningful_gameplay_turns_completed'] = sum(row.get('completion', {}).get('gameplay_completed', False) and not row.get('evaluation', {}).get('stop', False) for row in ordinary)
    result['total_http_requests_completed'] = sum(row['http_status'] == 200 for row in result['steps'])
    result['decisive_failures'] = sum(row.get('evaluation', {}).get('stop', row.get('completion', {}).get('semantic_dead_end', False)) for row in ordinary)
    result['cleanup']=runner.stop_owned(process,5)
    if process:
        logger.join(timeout=3)
    result['duration_seconds']=time.monotonic()-started
    result['provider_usage']=json.loads((run/'diagnostics/budget_snapshot.json').read_text()) if (run/'diagnostics/budget_snapshot.json').exists() else {}
    if (run/'data').exists():
        runner.snapshot_files(run,'after')
    if base:
        with socket.socket() as released:
            released.bind(('127.0.0.1',ready['port']))
        result['port_released']=True
    write(OUT/(mode+'_result.json'),result)
    write(run/'reports/result.json',result)
    if mode=='offline':
        passed=result['stop_reason']=='offline_preflight_complete_no_initialization' and result['cleanup']['stopped'] and result['provider_usage'].get('dispatched_requests')==0
        write(OUT/'offline_summary.json',{'passed':passed,'zero_live_calls':True,'run':str(run)})
    print(json.dumps({k:v for k,v in result.items() if k!='steps'}))
