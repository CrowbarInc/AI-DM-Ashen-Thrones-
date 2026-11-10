import json, os, socket, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
os.environ['ASHEN_OPENING_RENDERER'] = '1'
from tools.playtest import runner
from game import config
s = runner.load_scenario('FiveTurnGameplay')
env = runner.child_environment(OUT/'config_only', s, 'Live', 'success')
save('safe_configuration.json', {'credentials_present': bool(env.get('OPENAI_API_KEY', '').strip()),
    'default_model': config.DEFAULT_MODEL_NAME, 'high_precision_model': config.HIGH_PRECISION_MODEL_NAME,
    'retry_escalation_model': config.RETRY_ESCALATION_MODEL_NAME,
    'request_limit': int(env['ASHEN_PROVIDER_REQUEST_LIMIT']),
    'token_allowances': {k: int(env[f'ASHEN_PROVIDER_{k.upper()}_TOKEN_LIMIT']) for k in runner.CAPS},
    'sdk_retries': 0, 'host_retries': 0, 'startup_probes': False})
assert config.DEFAULT_MODEL_NAME == config.HIGH_PRECISION_MODEL_NAME == config.RETRY_ESCALATION_MODEL_NAME == 'gpt-4.1-mini'
assert int(env['ASHEN_PROVIDER_REQUEST_LIMIT']) == 6
original_env, original_wait = runner.child_environment, runner.wait_for_http_ready
ready_data = {}
def offline(*args, **kwargs):
    value = original_env(*args, **kwargs)
    value['ASHEN_DISABLE_PROVIDER_CALLS'] = '1'
    return value
def stop_ready(*args):
    ready, base = original_wait(*args)
    ready_data.update(ready=ready, base=base)
    raise KeyboardInterrupt
runner.child_environment, runner.wait_for_http_ready = offline, stop_ready
try:
    run, execution = runner.run_playtest(scenario='FiveTurnGameplay', mode='Deterministic', output_root=ROOT/'artifacts/atgb/pr_play_17/offline_startup')
finally:
    runner.child_environment, runner.wait_for_http_ready = original_env, original_wait
check = {'run': str(run), 'ready': ready_data, 'cleanup': execution['process_cleanup'],
         'steps': execution['steps'], 'provider_usage': execution.get('provider_usage'), 'passed': False}
try:
    assert ready_data and not execution['steps'] and execution['process_cleanup']['stopped']
    assert execution['provider_usage']['dispatched_requests'] == 0
    http = json.loads((run/'diagnostics/http_ready.json').read_text())
    assert http['startup_seconds'] < 30
    port = ready_data['ready']['port']
    with socket.socket() as probe:
        probe.settimeout(1)
        assert probe.connect_ex(('127.0.0.1', port)) != 0
    with socket.socket() as released:
        released.bind(('127.0.0.1', port))
    assert ready_data['ready']['opening_renderer']['selected']
    check.update(http=http, port_released=True, passed=True)
except Exception as exc:
    check.update(error=repr(exc))
save('offline_readiness.json', check)
print(json.dumps(check), flush=True)
sys.exit(0 if check['passed'] else 3)

