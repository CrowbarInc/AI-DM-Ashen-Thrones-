"""Historical evidence and adversarial authority controls; no provider network."""
import copy
import json
from pathlib import Path

import pytest

from tools.playtest.analysis import compare
from tools.playtest.overlays import compare_overlays, empty_overlay, payload
from tests.test_pr_play_04_opening_integrity import opening_world, _start

ROOT = Path(__file__).resolve().parents[1]
HIST = ROOT/'artifacts/pr_play_10/historical'
OUT = ROOT/'artifacts/pr_play_10'


def historical():
    before = json.loads((HIST/'baseline/documents.json').read_text())
    after = json.loads((HIST/'opening/documents.json').read_text())
    result = json.loads((HIST/'reports/result.json').read_text())
    response = next(s['response'] for s in result['steps'] if s['action'] == 'start_campaign')
    return before, after, response


def test_historical_exact_classification():
    a, b, body = historical()
    result = compare(a, b, accepted=True, opening_response=body)
    assert result['integrity']
    assert len(result['overlay_comparison']['changes']) == 4
    assert not compare(a, b, accepted=True)['integrity']


@pytest.mark.parametrize('case', ['O'+str(i) for i in range(1, 16)])
def test_authority_matrix(case):
    a, b, body = historical()
    old, new = payload(a['session.json']), payload(b['session.json'])
    sid = old['active_scene_id']
    accepted = True
    expected = case in {'O1', 'O10', 'O11', 'O12', 'O13', 'O14'}
    operation = 'classify captured accepted opening'
    if case == 'O1':
        del old['runtime_scene_overlays'][sid]
        operation = 'add active overlay via accepted authored structured update'
    elif case == 'O2':
        accepted = False
    elif case == 'O3':
        body['gm_output']['scene_update'] = None
    elif case == 'O4':
        new['runtime_scene_overlays'][sid]['state_flags']['unowned'] = True
    elif case == 'O5':
        del new['runtime_scene_overlays']['market_quarter']
    elif case == 'O6':
        new['runtime_scene_overlays']['market_quarter'] = copy.deepcopy(new['runtime_scene_overlays'][sid])
    elif case in {'O7', 'O8'}:
        text = ('The gate has vanished.' if case == 'O7' else a['scenes/frontier_gate.json']['scene']['hidden_facts'][0])
        body['gm_output']['scene_update']['visible_facts_add'][0] = text
        new['runtime_scene_overlays'][sid]['visible_facts_add'][0] = text
    elif case == 'O9':
        new['runtime_scene_overlays'][sid]['last_seen'] = 'not documented bookkeeping'
    elif case in {'O10', 'O12', 'O13'}:
        a = copy.deepcopy(b)
        operation = 'unchanged subsequent snapshot; repeated/concurrent endpoint coverage in opening regression'
    elif case == 'O11':
        b = copy.deepcopy(a)
        accepted = False
    elif case == 'O14':
        assert old['runtime_scene_overlays']['market_quarter'] == new['runtime_scene_overlays']['market_quarter']
    elif case == 'O15':
        old['runtime_scene_overlays'] = []
    result = compare_overlays(a, b, accepted=accepted, opening_response=body)
    record = dict(case=case, fixture='captured PR-PLAY-09 snapshots with explicit adversarial deltas',
                  operation=operation, expected_integrity=expected, actual=result, passed=result['integrity'] == expected)
    (OUT/(case+'.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    assert result['integrity'] == expected


def documents():
    import game.storage as st
    docs = {}
    for p in st.DATA_DIR.rglob('*'):
        if p.suffix == '.json':
            docs[p.relative_to(st.DATA_DIR).as_posix()] = json.loads(p.read_text(encoding='utf-8'))
        elif p.suffix == '.jsonl':
            docs[p.relative_to(st.DATA_DIR).as_posix()] = [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
    return docs


def test_replay_production_opening(opening_world, monkeypatch):
    import game.api as api
    import game.storage as st
    # Restore only authored scene fixture content, before the operation. No
    # historical runtime session/world injection and no GM/validator stubs.
    a, historical_after, _ = historical()
    st._save_json(st.scene_path('frontier_gate'), a['scenes/frontier_gate.json'])
    capture = json.loads((HIST/'opening_response_evidence/eea42395cc4a47a6b5d6ed286f046436-1.json').read_text())
    opening_world['state']['text'] = (ROOT/'tests/fixtures/pr_play_10/historical_opening.json').read_text()
    assert json.loads(opening_world['state']['text']) == capture['parsed_response']
    # Match the harness's normal GET /api/state baseline capture, which performs
    # lazy initialization through production owners before taking snapshots.
    api.compose_state()
    before = documents()
    stages = []
    real_apply, real_accept, real_save = api._apply_post_gm_updates, api._opening_response_rejection, api.save_session

    def observe_apply(*args, **kwargs):
        stages.append(dict(stage='before_overlay_application', overlays=copy.deepcopy(args[2].get('runtime_scene_overlays'))))
        result = real_apply(*args, **kwargs)
        stages.append(dict(stage='after_overlay_application', overlays=copy.deepcopy(result[1].get('runtime_scene_overlays'))))
        return result

    def observe_accept(*args, **kwargs):
        result = real_accept(*args, **kwargs)
        stages.append(dict(stage='opening_acceptance', rejection=result))
        return result

    def observe_save(session, *args, **kwargs):
        stages.append(dict(stage='save_session', campaign_started=session.get('campaign_started'),
                           overlays=copy.deepcopy(session.get('runtime_scene_overlays'))))
        return real_save(session, *args, **kwargs)

    monkeypatch.setattr(api, '_apply_post_gm_updates', observe_apply)
    monkeypatch.setattr(api, '_opening_response_rejection', observe_accept)
    monkeypatch.setattr(api, 'save_session', observe_save)
    body, status = _start()
    after = documents()
    comparison = compare(before, after, accepted=status == 200, opening_response=body)
    record = dict(status=status, before=before, after=after, stages=stages,
                  response=body, comparison=comparison, sdk_calls=len(opening_world['calls']),
                  parsed_response_unmodified=True,
                  historical_overlay_before_equal=payload(before['session.json'])['runtime_scene_overlays'] == payload(a['session.json'])['runtime_scene_overlays'],
                  historical_overlay_after_equal=payload(after['session.json'])['runtime_scene_overlays'] == payload(historical_after['session.json'])['runtime_scene_overlays'])
    (OUT/'replay.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    assert status == 200, body.get('opening_failure_reason')
    assert comparison['integrity'], comparison['unexpected_mutations']
    assert record['historical_overlay_after_equal']
    assert record['historical_overlay_before_equal']
    assert len(opening_world['calls']) == 1
    assert [s['stage'] for s in stages].index('after_overlay_application') < [s['stage'] for s in stages].index('opening_acceptance')
    assert not _start()[0].get('ok')
    assert len(opening_world['calls']) == 1


def test_bound_diagnostics_and_missing_null_distinction():
    a = {'session.json': {'runtime_scene_overlays': {str(i): {} for i in range(120)}}}
    b = copy.deepcopy(a)
    for overlay in b['session.json']['runtime_scene_overlays'].values():
        overlay['extra'] = 'x'*5000
    result = compare_overlays(a, b)
    assert not result['integrity'] and result['omitted_entries'] == 20
    assert result['changes'][0]['after']['omitted_characters'] > 0
    assert len(result['changes']) == 100
    b = {'session.json': {'runtime_scene_overlays': {'a': None}}}
    assert not compare_overlays({'session.json': {}}, b)['integrity']


def test_ordinary_turn_overlay_stops():
    from tests.test_five_turn_gameplay import evaluate
    a, b, body = historical()
    row = evaluate(body=body, before=a, after=b)
    assert row['stop']
    assert any(f['category'] == 'unauthorized_overlay_mutation' for f in row['findings'])


def test_failed_opening_rolls_back_applied_overlays(opening_world, monkeypatch):
    import game.api as api
    import game.storage as st
    a, _, _ = historical()
    st._save_json(st.scene_path('frontier_gate'), a['scenes/frontier_gate.json'])
    api.compose_state()
    opening_world['state']['text'] = (ROOT/'tests/fixtures/pr_play_10/historical_opening.json').read_text()
    before = documents()
    # Inject a persistence failure after normal semantic and acceptance checks.
    # No mutation is injected; the normal post-GM owner has already applied it.
    def fail_save(_):
        raise OSError('synthetic commit failure')
    monkeypatch.setattr(api, 'save_world', fail_save)
    with pytest.raises(OSError):
        _start()
    after = documents()
    result = compare(before, after, accepted=False)
    assert result['integrity']
    assert payload(before['session.json'])['runtime_scene_overlays'] == payload(after['session.json'])['runtime_scene_overlays']
    (OUT/'failed_overlay_rollback.json').write_text(json.dumps(result, indent=2))


def test_concurrent_historical_overlay_commit_once(opening_world, monkeypatch):
    import threading
    import openai
    from types import SimpleNamespace as NS
    import game.api as api
    import game.storage as st
    a, historical_after, _ = historical()
    st._save_json(st.scene_path('frontier_gate'), a['scenes/frontier_gate.json'])
    api.compose_state()
    text = (ROOT/'tests/fixtures/pr_play_10/historical_opening.json').read_text()
    entered, release = threading.Event(), threading.Event()
    calls, results = [], []

    def create(**kwargs):
        calls.append(1)
        entered.set()
        assert release.wait(10)
        return NS(output_text=text, status='completed', model='offline-stub',
                  usage=NS(input_tokens=20, output_tokens=10, total_tokens=30))
    monkeypatch.setattr(openai, 'OpenAI', lambda **kw: NS(responses=NS(create=create)))
    threads = [threading.Thread(target=lambda: results.append(_start())) for _ in range(2)]
    threads[0].start()
    try:
        assert entered.wait(5)
        threads[1].start()
        threads[1].join(.1)
        assert threads[1].is_alive()
    finally:
        release.set()
        for thread in threads:
            if thread.ident:
                thread.join(15)
    assert all(not t.is_alive() for t in threads)
    assert sorted(s for _, s in results) == [200, 409]
    assert len(calls) == 1
    actual = payload(documents()['session.json'])['runtime_scene_overlays']
    assert actual == payload(historical_after['session.json'])['runtime_scene_overlays']
    (OUT/'concurrent_overlay.json').write_text(json.dumps(dict(statuses=sorted(s for _, s in results),
           sdk_calls=len(calls), overlays=actual), indent=2))


def test_unrelated_vocabulary_and_missing_overlay_root():
    sid = 'observatory'
    a = {'session.json': {'active_scene_id': sid},
         'scenes/observatory.json': {'scene': {'id': sid, 'visible_facts': ['A blue lens.'], 'mode': 'explore'}}}
    b = copy.deepcopy(a)
    b['session.json'].update(campaign_started=True, runtime_scene_overlays={sid: empty_overlay(sid)})
    body = {'ok': True, 'resolution': {'kind': 'scene_opening'}, 'gm_output': {
        'metadata': {'accepted_response': {'hard_validation': {'hard_valid': True}, 'authority_result': 'accepted'}}}}
    assert compare_overlays(a, b, accepted=True, opening_response=body)['integrity']
    b['session.json']['runtime_scene_overlays'][sid]['visible_facts_add'] = ['A secret vault opens.']
    assert not compare_overlays(a, b, accepted=True, opening_response=body)['integrity']
