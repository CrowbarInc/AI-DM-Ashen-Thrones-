"""Bounded continuation using the reviewed harness unchanged; never retries a live trial."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from tools.atgb.driver import RunConfig, run_benchmark
from tools.atgb.budget import Budget
from tools.atgb.accounting import live_accounting_readiness, inspect_ledger

def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def unchanged():
    before = json.loads((OUT / 'provenance_before.json').read_text())
    changed = [p for p, h in before['source_sha256'].items() if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
    assert not changed, f'Protected source/evidence drift: {changed}'
    assert live_accounting_readiness(ROOT)['ok']

assert not (OUT / 'campaign_clock.json').exists(), 'No automatic live restart'
unchanged()
preflight = json.loads((OUT / 'preflight_final/result.json').read_text())
assert not preflight['stop_reason'] and len(preflight['scenario_records']) == 10
assert all(r['preflight']['ok'] for r in preflight['scenario_records']) and not preflight['turns']
for name in ('reset_retry.xml',):
    suite = ET.parse(OUT / name).getroot()
    assert all(int(s.get('failures', 0)) == 0 and int(s.get('errors', 0)) == 0 for s in suite.iter('testsuite'))
# The one failure in the broad check is preserved and resolved by the targeted reset check.
suite = ET.parse(OUT / 'focused_unsandboxed.xml').getroot()
failures = [t.get('name') for t in suite.iter('testcase') if t.find('failure') is not None or t.find('error') is not None]
assert failures == ['test_all_scenarios_reset_reproducibly_without_chat_or_canonical_changes']

started = time.time()
write(OUT / 'campaign_clock.json', {'start_epoch': started, 'deadline_epoch': started + 900})
admissions = incoming = outgoing = 0
for number in range(4, 11):
    unchanged()
    sid = f'S{number:02}'
    seconds = min(180, started + 900 - time.time())
    calls, tokens = 48 - admissions, 120000 - incoming - outgoing
    if seconds <= 0 or calls <= 0 or tokens <= 0:
        write(OUT / 'campaign_stop.json', {'reason': 'campaign_budget', 'next_scenario': sid})
        break
    target = OUT / sid
    assert not target.exists(), 'Never overwrite any live attempt'
    target.mkdir()
    os.environ['ASHEN_PROVIDER_USAGE_PATH'] = str((target / 'provider_usage.jsonl').resolve())
    os.environ['ASHEN_PROVIDER_REQUEST_LIMIT'] = str(calls)
    os.environ['ASHEN_PROVIDER_INPUT_TOKEN_LIMIT'] = str(100000 - incoming)
    os.environ['ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT'] = str(20000 - outgoing)
    os.environ['ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT'] = str(tokens)
    began = time.time()
    result = run_benchmark(RunConfig(mode='live_provider', scenario_ids=(sid,), output_dir=target,
        trial_number=2 if sid == 'S04' else 1, confirm_live_provider=True, keep_stores=True,
        worker_timeout_seconds=seconds, budget=Budget(max_provider_calls=calls,
            max_elapsed_seconds=seconds, max_tokens=tokens)), root=ROOT)
    write(target / 'wall_clock.json', {'start_epoch': began, 'end_epoch': time.time(), 'elapsed_seconds': time.time() - began})
    workers = list((target / 'stores').glob('*/atgb-worker.json'))
    worker = json.loads(workers[0].read_text()) if len(workers) == 1 else {}
    turns = result['turns']
    expected = 2 if sid in ('S09', 'S10') else 4
    snapshot = turns[-1]['provider_accounting']['process_snapshot'] if turns else None
    accounting = inspect_ledger(target / 'provider_usage.jsonl', snapshot) if snapshot else {'status': 'unavailable'}
    accepted = (not result['stop_reason'] and len(turns) == expected and worker.get('ok')
        and all(t['capture_status'] == 'captured' and t['response_text'] for t in turns)
        and all(r['preflight']['ok'] for r in result['scenario_records'])
        and accounting['status'] == 'recorded' and not accounting.get('pending_requests')
        and snapshot['total_tokens'] is not None and not snapshot['stopped'])
    if snapshot:
        admissions += snapshot['requests']
        if snapshot['input_tokens'] is not None and snapshot['output_tokens'] is not None:
            incoming += snapshot['input_tokens']
            outgoing += snapshot['output_tokens']
    status = {'scenario_id': sid, 'trial': 2 if sid == 'S04' else 1,
        'infrastructure_accepted': bool(accepted), 'turns_captured': len(turns),
        'stop_reason': result['stop_reason'], 'accounting': accounting,
        'campaign_admissions': admissions, 'campaign_input_tokens': incoming, 'campaign_output_tokens': outgoing,
        'human_review': 'pending'}
    write(target / 'execution_status.json', status)
    print(json.dumps(status), flush=True)
    if not accepted:
        write(OUT / 'campaign_stop.json', {'scenario': sid, 'reason': result['stop_reason'] or 'infrastructure_or_usage_uncertainty', 'automatic_retry': False})
        break
write(OUT / 'campaign_usage.json', {'admissions': admissions, 'input_tokens': incoming, 'output_tokens': outgoing,
    'elapsed_seconds': time.time() - started, 'historical_usage_included': False})
