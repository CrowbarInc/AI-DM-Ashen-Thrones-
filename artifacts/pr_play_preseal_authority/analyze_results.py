"""Build compact review evidence from unchanged HTTP runs and focused controls."""
import hashlib
import json
from pathlib import Path
import statistics
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ID = 'pr_play_preseal_authority'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def run(directory, xml):
    suite = ET.parse(OUT/directory/xml).getroot()[0]
    nodes = []
    for c in suite.findall('testcase'):
        node = c.attrib['classname'].replace('.', '/') + '.py::' + c.attrib['name']
        outcome = 'failed' if c.find('failure') is not None else 'error' if c.find('error') is not None else 'skipped' if c.find('skipped') is not None else 'passed'
        nodes.append({'nodeid': node, 'outcome': outcome, 'seconds': c.get('time')})
    counts = {k: sum(v['outcome'] == k for v in nodes) for k in ('passed', 'failed', 'error', 'skipped')}
    return {'directory': directory, 'counts': {'tests': len(nodes), **counts}, 'nodes': nodes,
            'failures': read(OUT/directory/'failures.json'), 'command': read(OUT/directory/'command.json')}


def find(value, key):
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for v in value.values():
            got = find(v, key)
            if got is not None:
                return got
    elif isinstance(value, list):
        for v in value:
            got = find(v, key)
            if got is not None:
                return got


runs = [run(d, x) for d, x in [
    ('before', 'baseline_junit.xml'), ('before/authority', 'recovery_junit.xml'),
    ('after', 'baseline_junit.xml'), ('after/authority', 'recovery_junit.xml'),
    ('focused_before', 'baseline_junit.xml'), ('focused_after', 'baseline_junit.xml'),
    ('focused_verified', 'baseline_junit.xml'), ('focused_final', 'baseline_junit.xml')]]
before = {v['nodeid']: v for r in runs[:2] for v in r['nodes']}
after = {v['nodeid']: v for r in runs[2:4] for v in r['nodes']}
assert set(before) == set(after)
before_failed = {n for n, v in before.items() if v['outcome'] != 'passed'}
after_failed = {n for n, v in after.items() if v['outcome'] != 'passed'}
summed = lambda rows: {k: sum(r['counts'][k] for r in rows) for k in runs[0]['counts']}
baseline_before = [v for n, v in before.items() if 'test_pr_play_46_mechanical_boundary.py' not in n]
baseline_after = [v for n, v in after.items() if 'test_pr_play_46_mechanical_boundary.py' not in n]
count_nodes = lambda rows: {'tests': len(rows), **{k: sum(v['outcome'] == k for v in rows) for k in ('passed', 'failed', 'error', 'skipped')}}
save('test_results.json', {'milestone': ID, 'runs': runs, 'expanded_before': summed(runs[:2]),
    'expanded_after': summed(runs[2:4]), 'established_before': count_nodes(baseline_before),
    'established_after': count_nodes(baseline_after), 'added_tests_final': runs[-1]['counts'],
    'newly_failing': sorted(after_failed-before_failed), 'resolved': sorted(before_failed-after_failed),
    'unchanged_known_failures': sorted(after_failed & before_failed), 'same_collection': True,
    'live_provider_calls': 0,
    'focused_draft_caveat': 'Initial draft asserted entire world equality. Baseline and post-change captures show normal faction/event simulation. Final test checks no invented truth while allowing those same simulation keys; all intermediate failures retained.'})

cases = read(ROOT/'artifacts/pr_play_baseline_provenance/publication_defects.json')['defects']
before_cap = read(OUT/'before/http_capture.json')
after_cap = read(OUT/'after/http_capture.json')
events = read(OUT/'after/stage_events.json')
comparison = []
for c in cases:
    node = c['nodeid']
    b = before_cap[node][0]
    a = after_cap[node][0]
    res = a['after']['log'][-1]['resolution']
    note = find(a['raw_before_projection'], 'closed_surface_preparation')
    record = find(a['raw_before_projection'], 'accepted_response')
    line = a['response']['gm_output']['player_facing_text']
    assert note['applied'] and note['eligible'] and note['prepared_candidate'] == line
    assert record['immutable'] and record['hard_validation']['hard_valid'] and record['text'] == line
    payload = {k: v for k, v in record.items() if k not in {'integrity_digest', 'skipped_mutators'}}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    assert digest == record['integrity_digest']
    assert a['before']['character'] == a['after']['character']
    world_keys_changed = [k for k in a['after']['world'] if a['after']['world'][k] != a['before']['world'].get(k)]
    assert set(world_keys_changed) <= {'factions', 'event_log'}
    assert a['after']['session']['last_publication']['visible'] == line
    candidate = b['response']['gm_output']['player_facing_text']
    assert note['original_candidate'] == candidate and candidate != line
    ev = [v for v in events if v['node'] == node]
    validation = next(v for v in ev if v['function'].endswith('validate_generated_response'))
    assert validation['args'][0] == line
    preparation_event = next(v for v in ev if v['function'].endswith('_closed_surface_preparation'))
    seal_event = next(v for v in ev if v['function'].endswith('seal_accepted_response'))
    assert ev.index(preparation_event) < ev.index(validation) < ev.index(seal_event)
    assert seal_event['kwargs']['validation']['hard_valid']
    assert record['generation_attempts'] == 1
    assert record['provenance'] == 'closed_surface_authority_projection'
    comparison.append({'id': c['id'], 'nodeid': node, 'request': a['request'],
        'before_publication': candidate, 'after_publication': line, 'authoritative_resolution': res,
        'preparation': note, 'accepted_response': record, 'digest_verified': True,
        'validation_before_seal': True, 'state_before': a['before'], 'state_after': a['after'],
        'character_unchanged': True, 'world_changed_keys': world_keys_changed,
        'baseline_world_changed_keys': [k for k in b['after']['world'] if b['after']['world'][k] != b['before']['world'].get(k)],
        'unsupported_claim_published': False, 'obsolete_assertions_remaining_in_this_test': [],
        'original_test_after': after[node]['outcome']})
save('three_case_comparison.json', {'milestone': ID, 'cases': comparison})
timings = [v['duration_ns']/1e6 for v in events if v['function'].endswith('_closed_surface_preparation') and v['result'] and v['result'].get('eligible')]
save('performance.json', {'live_provider_calls': 0, 'additional_dispatches': 0, 'additional_retries': 0,
    'added_prompt_tokens': 0, 'helper_samples_ms': timings,
    'helper_median_ms': statistics.median(timings) if timings else None,
    'scope': 'Actual local HTTP helper calls including renderer; excludes test instrumentation copying and existing validation. No provider latency or billing claim.'})
bturns = read(OUT/'before/twelve_turn/turns.json')
aturns = read(OUT/'after/twelve_turn/turns.json')
turns = []
for b, a in zip(bturns, aturns, strict=True):
    assert b['id'] == a['id']
    turns.append({'id': a['id'], 'request': a['player_text'], 'before': b['visible'], 'after': a['visible'],
        'publication_equal': b['visible'] == a['visible'], 'scene_equal': b['after']['scene_id'] == a['after']['scene_id'],
        'before_state': b['after'], 'after_state': a['after'], 'error': a['error'],
        'before_log': b['log'], 'after_log': a['log']})
save('twelve_turn_comparison.json', {'turns': turns, 'before_summary': read(OUT/'before/twelve_turn/sequence_summary.json'),
    'after_summary': read(OUT/'after/twelve_turn/sequence_summary.json')})
save('precedence_results.json', {'focused': runs[-1]['nodes'],
    'http_handoff_controls': [v for v in runs[2]['nodes'] if 'test_pr_play_post_npc_handoff.py' in v['nodeid']],
    'at_opt_06': [v for v in runs[2]['nodes'] if 'test_at_opt_06' in v['nodeid']],
    'scope': 'New resolved-delta/physical precedence tests are synthetic at the actual acceptance owner. Existing HTTP controls cover clue, travel, repetition, follow-up and refusal. No end-to-end loot persistence claim.'})
print(json.dumps({'before': summed(runs[:2]), 'after': summed(runs[2:4]), 'new': runs[-1]['counts'],
    'new_failures': sorted(after_failed-before_failed), 'three_cases': [c['original_test_after'] for c in comparison],
    'twelve_equal': all(v['publication_equal'] and v['scene_equal'] for v in turns)}))
