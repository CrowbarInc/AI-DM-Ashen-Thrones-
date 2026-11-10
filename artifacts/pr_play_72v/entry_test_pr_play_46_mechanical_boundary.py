"""Offline acceptance gates and a deliberately non-exhaustive adversarial census.

Corpus labels describe meaning, never the implementation's current behavior.
Residual misclassifications are recorded, not relabeled to inflate accuracy.
"""
import copy
import importlib.util
import json
import statistics
import time
import tracemalloc
from pathlib import Path

import pytest
from game.immutable_valid_response import validate_generated_response, run_preserve_if_valid
from game.mechanical_claims import audit_mechanical_claims
from game.narration_authorization import project_narration_payload

OUT = Path(__file__).resolve().parents[1] / 'artifacts/pr_play_46'
CORPUS = json.loads((OUT / 'corpus.json').read_text())


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def result(**kwargs):
    return {'kind': 'investigate', 'success': True, 'state_changes': {}, **kwargs}


@pytest.mark.parametrize('text,changes,accepted', [
    ('Your purse now holds fifty more gold coins.', {}, False),
    ('A silver key now rests among your possessions.', {}, False),
    ('Your purse now holds fifty more gold coins.', {'currency_gained': ['50 gold coins']}, True),
    ('A silver key now rests among your possessions.', {'items_added': ['silver key']}, True),
    ('Your pack contains an obsidian brooch.', {}, False),
    ('An obsidian brooch lies in your inventory.', {'items_added': ['obsidian brooch']}, True),
    ('Your bag holds 12 additional copper coins.', {'currency_gained': ['12 copper coins']}, True),
    ('Your bag holds 12 additional copper coins.', {'currency_gained': ['3 copper coins']}, False),
    ('Your purse holds fifty gold coins.', {'currency_gained': ['50 gold coins']}, False),
    ('Your pack contains a flute and a ruby.', {'items_added': ['flute']}, False),
    ('The porter says, "A silver key now rests among your possessions."', {}, True),
    ('The porter says, "Morning." A silver key now rests among your possessions.', {}, False),
    ('The room feels like a treasure vault.', {}, True),
    ('If your purse now holds fifty more gold coins, you could pay.', {}, True),
    ('Your purse does not contain fifty gold coins.', {}, True),
])
def test_bounded_possession_contract(text, changes, accepted):
    r = result(state_changes=changes)
    before = copy.deepcopy(r)
    assert validate_generated_response(text, resolution=r)['hard_valid'] is accepted
    assert r == before


def test_originals_fallback_preserves_clue_without_retry():
    clue = 'The marks may indicate a burrow; their age remains unknown.'
    r = result(kind='discover_clue', clue_text=clue, discovered_clues=[clue],
               state_changes={'clue_revealed': True})
    rows = []
    for bad in ['Your purse now holds fifty more gold coins.',
                'A silver key now rests among your possessions.']:
        state = {'inventory': [], 'currency': 0, 'hp': 12, 'active_scene_id': 'observatory'}
        before = copy.deepcopy((state, r))
        retries = []
        draft = clue + ' ' + bad
        final = run_preserve_if_valid({'player_facing_text': draft, 'metadata': {}},
            resolution=r, player_text='I examine the marks.', regenerate=lambda _: retries.append(True))
        assert retries == []
        assert (state, r) == before
        assert clue in final['player_facing_text']
        assert bad not in final['player_facing_text']
        assert draft == final['metadata']['rejected_provider_output']
        assert final['metadata']['mechanical_rejection_reasons']
        rows.append({'input': draft, 'authoritative_outcome': r, 'pre_state': before[0],
                     'post_state': state, 'validator': validate_generated_response(draft, resolution=r),
                     'final': final, 'retry_calls': retries})
    write('after_originals_with_clue.json', rows)


def test_envelope_is_read_only_and_idempotent():
    r = result(state_changes={'items_added': [{'name': 'flute', 'secret': 'CANARY'}]})
    payload = {'instructions': [], 'scene': {}, 'world': {'secret': 'CANARY'}}
    before = copy.deepcopy((r, payload))
    p = project_narration_payload(payload, r)
    assert project_narration_payload(p, r) == p
    assert (r, payload) == before
    assert 'CANARY' not in json.dumps(p)
    assert p['authorized_mechanical_outcome']['items_added'] == [{'name': 'flute'}]
    assert sum('not total balances' in line for line in p['instructions']) == 1


@pytest.mark.parametrize('scenario', ['merchant', 'wilderness', 'dungeon', 'conversation', 'failed_travel', 'quiet_exploration'])
def test_cross_scenario(scenario):
    cases = {
        'merchant': (result(state_changes={'items_added': ['linen cloak'], 'currency_spent': ['3 copper coins']}),
                     'A linen cloak now rests among your possessions. You spend 3 copper coins.',
                     'A bonus ruby lies in your inventory.'),
        'wilderness': (result(state_changes={'damage_taken': 3}), 'You suffer 3 damage.', 'You suffer 7 damage.'),
        'dungeon': (result(kind='discover_clue', clue_text='The marks may indicate a burrow; their age remains unknown.',
                           state_changes={'clue_revealed': True}),
                    'The marks may indicate a burrow; their age remains unknown.',
                    'The marks definitely prove a dragon burrow.'),
        'conversation': (result(kind='social'), 'The porter says, "Morning again, is it?"',
                         'Your pack contains a bonus ruby.'),
        'failed_travel': (result(kind='travel', success=False, resolved_transition=False),
                          'Wind whistles along the blocked trail.', 'You arrive at the watchtower.'),
        'quiet_exploration': (result(), 'Rain taps the shutters. The porter rubs his chin.',
                              'Your purse now holds fifty more gold coins.'),
    }
    r, good, bad = cases[scenario]
    before = copy.deepcopy(r)
    assert validate_generated_response(good, resolution=r)['hard_valid']
    assert not validate_generated_response(bad, resolution=r)['hard_valid']
    assert r == before


def census():
    rows = []
    for case in CORPUS:
        r = copy.deepcopy(case['resolution'])
        before = copy.deepcopy(r)
        v = validate_generated_response(case['text'], resolution=r)
        final = run_preserve_if_valid({'player_facing_text': case['text'], 'metadata': {}},
            resolution=r, player_text='I observe.', regenerate=None)
        assert r == before
        rows.append({**case, 'validation': v, 'final': final, 'state_unchanged': r == before})
    return rows


def metrics(rows):
    # Positive = clearly unsupported mechanical assertion; ambiguous excluded.
    labeled = [r for r in rows if r['group'] != 'ambiguous']
    tp = sum(r['group'] == 'unsupported' and not r['validation']['hard_valid'] for r in labeled)
    fn = sum(r['group'] == 'unsupported' and r['validation']['hard_valid'] for r in labeled)
    fp = sum(r['group'] != 'unsupported' and not r['validation']['hard_valid'] for r in labeled)
    tn = sum(r['group'] != 'unsupported' and r['validation']['hard_valid'] for r in labeled)
    return {'positive_class': 'clearly unsupported mechanical assertion', 'ambiguous_excluded': 4,
            'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn, 'precision': tp/(tp+fp) if tp+fp else None,
            'recall': tp/(tp+fn), 'false_rejection_rate': fp/(fp+tn),
            'false_acceptance_rate': fn/(fn+tp),
            'by_group': {g: {'total': sum(r['group'] == g for r in rows),
                           'accepted': sum(r['group'] == g and r['validation']['hard_valid'] for r in rows),
                           'rejected': sum(r['group'] == g and not r['validation']['hard_valid'] for r in rows)}
                         for g in sorted({r['group'] for r in rows})},
            'by_category': {c: {g: {'total': sum(r['group'] == g and r['category'] == c for r in rows),
                 'rejected': sum(r['group'] == g and r['category'] == c and not r['validation']['hard_valid'] for r in rows)}
                 for g in sorted({r['group'] for r in rows if r['category'] == c})}
                 for c in sorted({r['category'] for r in rows})},
            'false_negatives': [r['id'] for r in labeled if r['group'] == 'unsupported' and r['validation']['hard_valid']],
            'false_positives': [r['id'] for r in labeled if r['group'] != 'unsupported' and not r['validation']['hard_valid']]}


def test_record_adversarial_census(monkeypatch):
    assert len(CORPUS) >= 40
    assert len({r['id'] for r in CORPUS}) == len(CORPUS)
    spec = importlib.util.spec_from_file_location('pr46_baseline', OUT/'source_before/game/mechanical_claims.py')
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    with monkeypatch.context() as m:
        m.setattr('game.mechanical_claims.audit_mechanical_claims', old.audit_mechanical_claims)
        baseline = census()
    current = census()
    write('corpus_before.json', baseline)
    write('corpus_after.json', current)
    write('metrics.json', {'before': metrics(baseline), 'after': metrics(current),
          'method': 'Full validator decisions on hand-labeled controlled cases; not a random sample or production accuracy estimate.'})
    # Acceptance gates stay independent of the census, which must expose misses.
    for id in ('original_item', 'original_currency', 'other_item', 'other_currency', 'container_item'):
        assert not next(r for r in current if r['id'] == id)['validation']['hard_valid']


def test_record_offline_performance(monkeypatch):
    from tests.test_pr_play_45_narration_authority import messages
    ms = messages(monkeypatch)
    payload = json.loads(ms[-1]['content'])
    baseline = copy.deepcopy(ms)
    old_payload = copy.deepcopy(payload)
    old_payload['instructions'] = [s for s in old_payload['instructions'] if 'not total balances' not in s]
    baseline[-1]['content'] = json.dumps(old_payload, ensure_ascii=False)
    size = lambda v: len(json.dumps(v, ensure_ascii=False).encode())
    def timing(fn, iterations=300):
        samples=[]
        for _ in range(iterations):
            start=time.perf_counter_ns(); fn(); samples.append(time.perf_counter_ns()-start)
        return {'iterations': iterations, 'median_us': statistics.median(samples)/1000,
                'p95_us': sorted(samples)[int(.95*len(samples))]/1000}
    r = result()
    text = 'Your purse now holds fifty more gold coins.'
    def fallback():
        return run_preserve_if_valid({'player_facing_text': text, 'metadata': {}},
                                    resolution=r, player_text='I observe.', regenerate=None)
    tracemalloc.start()
    fallback()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    write('performance.json', {'messages_before_utf8_bytes': size(baseline),
          'messages_after_utf8_bytes': size(ms), 'additional_utf8_bytes': size(ms)-size(baseline),
          'existing_envelope_utf8_bytes': size(payload['authorized_mechanical_outcome']),
          'additional_envelope_bytes': 0, 'audit': timing(lambda: audit_mechanical_claims(text, r)),
          'full_validation': timing(lambda: validate_generated_response(text, resolution=r)),
          'rejection_and_fallback': timing(fallback, 100),
          'traced_fallback_current_bytes': current, 'traced_fallback_peak_bytes': peak,
          'serialization': 'Same existing payload serialization; one fixed instruction, no new envelope or roundtrip.',
          'cost_estimate': 'Additional prompt text only; token count and live cost unmeasured. No budget changes.',
          'provider_requests': 0, 'provider_tokens': 0})
