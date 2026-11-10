"""Eight-attempt integrated narration experiment. Refuses reuse of its ledger.

Reuses PR56 isolated API fixtures/capture helpers, never its archived results.
All no-provider controls run before dispatch, avoiding the prior exhausted-budget
baseline artifact. Zero automatic retries. No canonical campaign edits.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'artifacts/pr_play_57'
spec = importlib.util.spec_from_file_location('pr56_helpers', ROOT / 'artifacts/pr_play_56/run_experiment.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
h.OUT = OUT
h.EVIDENCE = OUT / 'hook_evidence'
h.LEDGER = OUT / 'provider_usage.jsonl'
h.EXPERIMENT_REQUEST_CEILING = 8
os.environ['ASHEN_PROVIDER_REQUEST_LIMIT'] = '8'
os.environ['ASHEN_QUARANTINE_NARRATION_MODE'] = 'integrated'

PLAN = [
    {'id': 'A', 'category': 'successful_discovery', 'scene': 'frontier_gate',
     'turns': [{'text': 'I examine the notice board.'}], 'limitation': None},
    {'id': 'B', 'category': 'unsuccessful_investigation', 'scene': 'frontier_gate',
     'turns': [{'text': 'I examine the rain barrel.'}],
     'limitation': 'Mundane successful examination with no new clue; no deterministic failed skill-check fixture exists. This does not evaluate dice failure.'},
    {'id': 'C', 'category': 'repeated_investigation', 'scene': 'frontier_gate',
     'turns': [{'text': 'I examine the notice board.'}, {'text': 'I examine the notice board.'}],
     'limitation': None},
    {'id': 'D', 'category': 'uncertain_observation', 'scene': 'old_milestone',
     'turns': [{'text': 'I examine the footprints.'}], 'limitation': None},
]


def full_state():
    from game import storage
    return {p.relative_to(storage.DATA_DIR).as_posix():
            json.loads(p.read_text(encoding='utf-8'))
            if p.suffix == '.json' else p.read_text(encoding='utf-8')
            for p in sorted(storage.DATA_DIR.rglob('*'))
            if p.is_file() and p.suffix in {'.json', '.jsonl'}}


def execute(label, scenario, live):
    turns = [dict(t, live=bool(live and i == len(scenario['turns']) - 1))
             for i, t in enumerate(scenario['turns'])]
    # h.play_sequence seeds the store. Capture exact state just after seed and
    # immediately before/after the hook as well as after the complete API turn.
    snapshots = []
    from game import quarantined_investigation_narration as q
    original = q.run_quarantined_hook
    def observed(detached):
        before = full_state()
        result = original(detached)
        after = full_state()
        snapshots.append({'before': before, 'after': after,
                          'differences': h.diff(before, after)})
        return result
    q.run_quarantined_hook = observed
    try:
        row = h.play_sequence(OUT / 'tmp_runs' / label, scenario['scene'], turns, label)
        row['full_state_after'] = full_state()
        row['hook_state_snapshots'] = snapshots
        return row
    finally:
        q.run_quarantined_hook = original


def main():
    from game import provider_budget as budget
    from game.config import get_openai_api_key, DEFAULT_MODEL_NAME
    from game.expressive_dialogue import _OUTPUT_CAP
    from game import integrated_investigation_narration as integrated
    from game import quarantined_investigation_narration as q
    if h.LEDGER.exists():
        raise RuntimeError('existing experiment ledger; do not rerun')
    OUT.mkdir(parents=True, exist_ok=True)
    h.write_json('scenario_manifest.json', {'scenarios': PLAN, 'generations_per_scenario': 2,
        'input_classification': 'representative_player_behavior', 'automatic_retries': 0})
    before = h.campaign_hashes()
    h.write_json('campaign_hashes_before.json', before)
    validator_before = h.sha(ROOT / h.PRIMARY_VALIDATOR)
    h.write_json('preflight.json', {'provider': 'openai', 'model': DEFAULT_MODEL_NAME,
        'credentials_present': bool(get_openai_api_key()), 'configured_output_cap': _OUTPUT_CAP,
        'limits': [8, 700, 12000], 'mode': 'quarantined_integrated'})
    assert _OUTPUT_CAP <= 700
    h.write_json('generation_parameters.json', {'system_prompt': integrated.SYSTEM_PROMPT,
        'limits': [8, 700, 12000], 'configured_output_cap': _OUTPUT_CAP,
        'automatic_retries': 0, 'sdk_max_retries': 0})
    baselines = {s['id']: execute(s['id'] + '_baseline', s, False) for s in PLAN}
    h.write_json('deterministic_baselines.json', baselines)
    os.environ['ASHEN_PROVIDER_USAGE_PATH'] = str(h.LEDGER)
    budget.initialize_accounting()
    h.install_capture()
    q.reset_live_budget()
    rows, pairs = [], []
    halted = ''
    try:
        for scenario in PLAN:
            for generation in (1, 2):
                if halted:
                    break
                label = f"{scenario['id']}{generation}"
                row = execute(label, scenario, True)
                baseline = baselines[scenario['id']]
                pair = h.pair(row, baseline)
                # Full persisted JSON state, including scene/campaign domains.
                # Only the existing volatile timestamp/ID scrub is applied.
                left = h.scrub(row['full_state_after'])
                right = h.scrub(baseline['full_state_after'])
                # JSONL logs are parsed before applying the same field scrub.
                for value in (left, right):
                    for key in list(value):
                        if key.endswith('.jsonl'):
                            value[key] = [h.scrub(json.loads(line)) for line in value[key].splitlines() if line]
                pair['full_persisted_differences'] = h.diff(left, right)
                pair['hook_state_differences'] = [d for snap in row['hook_state_snapshots'] for d in snap['differences']]
                record = row['turns'][-1]['quarantine'] or {}
                raw = record.get('raw_provider_text') or ''
                # Exact candidate storage scan; no vague authority-slice proxy.
                pair['raw_candidate_in_persisted_state'] = bool(raw and raw in json.dumps(row['full_state_after']))
                rows.append(row)
                pairs.append(pair)
                h.write_json('scenario_results.json', {'results': rows, 'pairs': pairs,
                    'usage': budget.snapshot(), 'raw_provider_responses': h.RAW, 'halted': halted})
                if (not all(pair['player_facing_identical']) or not all(pair['mechanical_identical'])
                    or pair['full_persisted_differences'] or pair['hook_state_differences']
                    or pair['raw_candidate_in_persisted_state'] or pair['context_leaks']):
                    halted = 'integrity_divergence:' + label
                if any(secret in raw for secret in list(h.CANARIES) + h.hidden_facts()):
                    halted = 'restricted_output:' + label
                provider = record.get('live_provider') or {}
                if not provider.get('sent') or provider.get('provider_error'):
                    halted = 'provider_failure:' + label
                if budget.snapshot().get('stopped') or q._LIVE_STOP:
                    halted = 'provider_budget_stop:' + (q._LIVE_STOP or budget.snapshot().get('stop_reason', ''))
    except Exception:
        halted = 'experiment_exception'
        h.write_json('experiment_exception.json', {'traceback': traceback.format_exc()})
    finally:
        after = h.campaign_hashes()
        h.write_json('state_integrity.json', {'canonical_campaign_unchanged': before == after,
            'validator_unchanged': validator_before == h.sha(ROOT / h.PRIMARY_VALIDATOR),
            'validator_sha256': validator_before, 'pairs': pairs})
        h.write_json('scenario_results.json', {'results': rows, 'pairs': pairs,
            'usage': budget.snapshot(), 'raw_provider_responses': h.RAW, 'halted': halted})
    print(json.dumps({'samples': len(rows), 'halted': halted,
        'total_tokens': budget.snapshot().get('total_tokens'),
        'decisions': [(r['label'], r['turns'][-1]['quarantine'].get('diagnostic')) for r in rows]}, indent=2))
    return int(bool(halted))


if __name__ == '__main__':
    raise SystemExit(main())
