"""Campaign wrapper: use approved harness unchanged, with a separate smoke gate."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
from tools.atgb.driver import RunConfig, run_benchmark
from tools.atgb.budget import Budget

OUT = Path(__file__).parent
def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def unchanged():
    provenance = json.loads((OUT / 'configuration_and_provenance.json').read_text())
    drift = [p for p, digest in provenance['source_sha256'].items() if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != digest]
    assert not drift, f'Execution source drift: {drift}'

def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

stage = sys.argv[1]
unchanged()
if stage == 'A':
    started = time.time()
    write(OUT / 'campaign_clock.json', {'start_epoch': started, 'deadline_epoch': started + 1800})
    ids = ['S01']
else:
    gate = json.loads((OUT / 'stage_a_acceptance.json').read_text())
    assert gate['accepted'], 'Stage A infrastructure gate failed'
    ids = [f'S{i:02}' for i in range(2, 11)]
clock = json.loads((OUT / 'campaign_clock.json').read_text())
for sid in ids:
    unchanged()
    prior = [r for p in OUT.glob('S*/provider_usage.jsonl') for r in records(p)]
    used = sum(bool(r.get('sent')) for r in prior)
    remaining = min(300, clock['deadline_epoch'] - time.time())
    calls = min(12 if sid == 'S01' else 80, 80 - used)
    if remaining <= 0 or calls <= 0:
        write(OUT / 'campaign_stop.json', {'reason': 'campaign_budget', 'provider_calls': used})
        break
    target = OUT / sid
    assert not target.exists(), 'Never overwrite a live attempt'
    target.mkdir()
    # Existing provider accounting is an observation/safety surface, not a model change.
    os.environ['ASHEN_PROVIDER_USAGE_PATH'] = str((target / 'provider_usage.jsonl').resolve())
    os.environ['ASHEN_PROVIDER_REQUEST_LIMIT'] = str(calls)
    for key in ['INPUT', 'OUTPUT', 'TOTAL']:
        os.environ[f'ASHEN_PROVIDER_{key}_TOKEN_LIMIT'] = '10000000'
    began = time.time()
    result = run_benchmark(RunConfig(mode='live_provider', scenario_ids=(sid,), output_dir=target,
        confirm_live_provider=True, keep_stores=True, worker_timeout_seconds=remaining,
        budget=Budget(max_provider_calls=calls, max_elapsed_seconds=remaining)), root=ROOT)
    write(target / 'wall_clock.json', {'start_epoch': began, 'end_epoch': time.time(), 'elapsed_seconds': time.time() - began})
    usage = records(target / 'provider_usage.jsonl')
    workers = list((target / 'stores').glob('*/atgb-worker.json'))
    worker = json.loads(workers[0].read_text()) if workers else {}
    expected = 4 if sid == 'S01' else len(json.loads(next((ROOT / 'data/validation/atgb').glob(f'*/{sid}.json')).read_text())['turns'])
    accepted = (not result.get('stop_reason') and len(result['turns']) == expected
        and all(t['capture_status'] == 'captured' and t['response_text'] for t in result['turns'])
        and all(s.get('preflight', {}).get('ok') and s['isolation']['accepted'] for s in result['scenario_records'])
        and any(r.get('sent') and r.get('request_id') for r in usage)
        and not any(r.get('refusal') or r.get('model_mismatch') for r in usage))
    status = {'scenario': sid, 'accepted': accepted, 'turns_captured': len(result['turns']),
        'provider_requests_recorded': sum(bool(r.get('sent')) for r in usage),
        'stop_reason': result.get('stop_reason'), 'human_review': 'pending', 'worker_ok': worker.get('ok')}
    write(OUT / ('stage_a_acceptance.json' if sid == 'S01' else f'{sid}/execution_status.json'), status)
    print(json.dumps(status), flush=True)
    if not accepted:
        write(OUT / 'campaign_stop.json', {'reason': 'infrastructure_or_provider_evidence_failure', 'scenario': sid})
        break
