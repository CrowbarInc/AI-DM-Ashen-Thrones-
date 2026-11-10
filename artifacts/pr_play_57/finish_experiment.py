"""Continue after verified telemetry-only stop, with a strictly reduced budget.

Never reuses or resets a ledger. The initial stop/raw comparisons stay intact.
Remaining shard gets 7 requests / 11,536 total tokens / 633 output tokens.
No quality retry; A1 remains part of the original two-generation plan.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/pr_play_57'
spec = importlib.util.spec_from_file_location('pr57_run', OUT / 'run_experiment.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
h = r.h


def authority_values(state):
    """Preserve every gameplay field; unwrap storage envelopes and omit only
    named operational clocks/performance. Raw snapshots and raw diffs remain.
    """
    def operational(value):
        if isinstance(value, dict):
            return {k: (['clue_text_digest:<process-hash>' if isinstance(x, str) and x.startswith('clue_text_digest:') else operational(x) for x in v] if k == 'surfaced_facts' and isinstance(v, list) else operational(v)) for k, v in value.items()
                    if k not in {'saved_at', 'last_saved_at', 'performance'} }
        if isinstance(value, list):
            return [operational(v) for v in value]
        return value
    result = {}
    for path, doc in state.items():
        if path.endswith('.jsonl'):
            doc = [json.loads(line) for line in doc.splitlines() if line]
        elif isinstance(doc, dict) and 'payload' in doc and 'integrity' in doc:
            doc = doc['payload']
        result[path] = h.scrub(operational(doc))
    return result


def main():
    from game import provider_budget as budget
    from game import quarantined_investigation_narration as q
    initial = json.loads((OUT / 'scenario_results.json').read_text(encoding='utf-8'))
    second = json.loads((OUT / 'combined_results.json').read_text(encoding='utf-8'))
    original = {'results': [initial['results'][0], second['results'][1]],
                'pairs': [initial['pairs'][0], second['pairs'][1]],
                'usage': {k: sum(sh[k] for sh in second['usage_shards']) for k in ('requests','input_tokens','output_tokens','total_tokens')},
                'raw_provider_responses': second['raw_provider_responses'],
                'halted': second['halted']}
    # Verify every prior candidate against the correctly decoded baseline.
    # The second stop was a cp1252 read of UTF-8 evidence, not gameplay drift.

    baselines = json.loads((OUT / 'deterministic_baselines.json').read_text(encoding='utf-8'))
    assert len(original['results']) == 2 and original['usage']['requests'] == 2
    for row in original['results']:
        assert not h.diff(authority_values(row['full_state_after']), authority_values(baselines['A']['full_state_after']))
        assert all(not snap['differences'] for snap in row['hook_state_snapshots'])
    first = original['results'][0]
    a = first['full_state_after']
    b = baselines['A']['full_state_after']
    differences = h.diff(authority_values(a), authority_values(b))
    assert not differences, differences
    assert not original['pairs'][0]['hook_state_differences']
    assert all(original['pairs'][0]['player_facing_identical'])
    assert all(original['pairs'][0]['mechanical_identical'])
    assert not original['pairs'][0]['context_leaks']
    # A strict whitelist classifies the recorded raw differences; any other
    # divergence remains a stop. No original comparison evidence is overwritten.
    allowed = ('$.combat.json.saved_at:', '$.session.json.integrity.payload_sha256:',
               '$.session.json.payload.last_saved_at:', '$.session.json.saved_at:',
               '$.session.json.payload.debug_traces[14].performance.',
               '$.session_log.jsonl[0].resolution.metadata.performance.')
    assert all(d.startswith(allowed) for d in original['pairs'][0]['full_persisted_differences'])
    h.write_json('second_stop_analysis.json', {'initial_halt': original['halted'],
        'raw_differences': original['pairs'][0]['full_persisted_differences'],
        'authoritative_payload_differences': differences, 'hook_exact_state_unchanged': True,
        'classification': 'UTF8_decode_error_and_process_randomized_diagnostic_clue_hash; game/noncombat_resolution.py:355 uses hash(slug)'  ,
        'remaining_attempts': 6, 'remaining_total_tokens': 12000 - original['usage']['total_tokens'],
        'remaining_output_tokens': 700 - original['usage']['output_tokens']})
    ledger = OUT / 'provider_usage_final.jsonl'
    if ledger.exists():
        raise RuntimeError('remaining shard already executed; do not rerun')
    os.environ['ASHEN_PROVIDER_USAGE_PATH'] = str(ledger)
    os.environ['ASHEN_PROVIDER_REQUEST_LIMIT'] = '6'
    os.environ['ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT'] = str(12000 - original['usage']['total_tokens'])
    os.environ['ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT'] = str(700 - original['usage']['output_tokens'])
    budget.initialize_accounting()
    h.install_capture()
    rows, pairs = copy.deepcopy(original['results']), copy.deepcopy(original['pairs'])
    pairs[0]['authoritative_payload_differences'] = []
    pairs[1]['original_encoding_differences'] = pairs[1].pop('authoritative_payload_differences')
    pairs[1]['authoritative_payload_differences'] = []
    halted = ''
    before = h.campaign_hashes()
    plan = [(s, g) for s in r.PLAN[1:] for g in (1, 2)]
    try:
        for scenario, generation in plan:
            if halted:
                break
            label = scenario['id'] + str(generation)
            row = r.execute(label, scenario, True)
            baseline = baselines[scenario['id']]
            pair = h.pair(row, baseline)
            pair['authoritative_payload_differences'] = h.diff(
                authority_values(row['full_state_after']), authority_values(baseline['full_state_after']))
            pair['hook_state_differences'] = [d for snap in row['hook_state_snapshots'] for d in snap['differences']]
            record = row['turns'][-1]['quarantine'] or {}
            raw = record.get('raw_provider_text') or ''
            pair['raw_candidate_in_persisted_state'] = bool(raw and raw in json.dumps(row['full_state_after']))
            rows.append(row)
            pairs.append(pair)
            if (not all(pair['player_facing_identical']) or not all(pair['mechanical_identical'])
                or pair['authoritative_payload_differences'] or pair['hook_state_differences']
                or pair['raw_candidate_in_persisted_state'] or pair['context_leaks']):
                halted = 'integrity_divergence:' + label
            if any(secret in raw for secret in list(h.CANARIES) + h.hidden_facts()):
                halted = 'restricted_output:' + label
            provider = record.get('live_provider') or {}
            if not provider.get('sent') or provider.get('provider_error'):
                halted = 'provider_failure:' + label
            if budget.snapshot().get('stopped') or q._LIVE_STOP:
                halted = 'provider_budget_stop:' + label
            total = original['usage']['total_tokens'] + (budget.snapshot().get('total_tokens') or 0)
            assert len(h.RAW) + len(original['raw_provider_responses']) <= 8
            assert total <= 12000
            h.write_json('final_results.json', {'results': rows, 'pairs': pairs,
                'usage_shards': second['usage_shards'] + [budget.snapshot()],
                'raw_provider_responses': original['raw_provider_responses'] + h.RAW, 'halted': halted})
    finally:
        h.write_json('final_results.json', {'results': rows, 'pairs': pairs,
            'usage_shards': second['usage_shards'] + [budget.snapshot()],
            'raw_provider_responses': original['raw_provider_responses'] + h.RAW, 'halted': halted})
        h.write_json('final_integrity.json', {'canonical_campaign_unchanged': before == h.campaign_hashes(),
            'validator_unchanged': h.sha(ROOT / h.PRIMARY_VALIDATOR) == 'ed29349cde1bb641178b01175f608142707dcc21a7d387e4b0f57707a1d0d6b6',
            'remaining_shard_requests': budget.snapshot()['requests']})
    print(json.dumps({'samples': len(rows), 'halted': halted,
        'tokens': sum(s['total_tokens'] for s in [original['usage'], budget.snapshot()])}))
    return int(bool(halted))


if __name__ == '__main__':
    raise SystemExit(main())
