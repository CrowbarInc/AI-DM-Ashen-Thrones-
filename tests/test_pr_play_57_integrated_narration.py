"""Integrated outcome safety and conservative coverage; no real provider calls."""
import copy
import json

import pytest

from game import integrated_investigation_narration as integrated
from game import quarantined_investigation_narration as q

ROUTE = 'The missing patrol was last seen taking the northwest mud track past the crates.'


def hook(kind='discover_clue', success=True, clues=None, known=()):
    return q.build_hook_input(resolution={'kind': kind, 'success': success,
        'discovered_clues': [ROUTE] if clues is None else clues, 'state_changes': {}},
        scene={'scene': {'visible_facts': ['Rain falls around the notice board.'],
                         'hidden_facts': ['SECRET']}},
        known_clue_texts=known, player_text='I examine the notice board.')


def run(text, **kwargs):
    return integrated.run_integrated_hook(hook(**kwargs), generator=q._Replay(text, ''))


def test_outcome_and_natural_reordering():
    row = run('Past the crates, the missing patrol was last seen taking the northwest mud track.')
    assert row['validation']['coverage']['decision'] == 'PASS'
    assert 'SECRET' not in json.dumps(row)
    assert row['promoted'] is False


@pytest.mark.parametrize('text', [
    'Rain falls while you study the notice board.',
    'The patrol followed a muddy path.',
    'The missing patrol was not last seen taking the northwest mud track past the crates.',
])
def test_omission_or_uncertain_paraphrase_blocks(text):
    row = run(text)
    assert row['validation']['coverage']['decision'] == 'REVIEW_REQUIRED'
    assert row['used_fallback']


@pytest.mark.parametrize('text', [
    'You find a silver key beneath the board.',
    'The patrol took the southeast road.',
])
def test_existing_semantic_protections(text):
    row = run(text)
    assert row['validation']['semantic']['decision'] == 'FAIL'
    assert row['used_fallback']


def test_legacy_inventory_gate_remains_required():
    # PR55 alone misses this wording; the unchanged legacy mechanical gate
    # must reject it. Preserve that limitation rather than repair PR55 here.
    row = run('You gain 10 gold coins.')
    assert row['validation']['legacy']['hard_valid'] is False
    assert row['validation']['decision'] == 'FAIL'
    assert row['used_fallback']


@pytest.mark.parametrize('success,text', [
    (False, 'Your investigation succeeds.'),
    (True, 'Your investigation fails.'),
])
def test_contradictory_mechanical_success_or_failure(success, text):
    row = run(text, success=success, clues=[ROUTE] if success else [])
    assert row['validation']['semantic']['decision'] == 'FAIL'
    assert any(reason.startswith('false_mechanical_')
               for reason in row['validation']['semantic']['reasons'])
    assert row['used_fallback']


@pytest.mark.parametrize('text', ['', {}, None, 'unfinished'])
def test_invalid_provider_return(text):
    row = run(text)
    assert row['diagnostic'] == 'VALIDATION_ERROR'
    assert row['used_fallback']


@pytest.mark.parametrize('error', [TimeoutError, RuntimeError])
def test_provider_failure(error):
    class Broken:
        def generate(self, request):
            raise error('simulated')
    row = integrated.run_integrated_hook(hook(), generator=Broken())
    assert row['used_fallback'] and row['promoted'] is False


@pytest.mark.parametrize('decision', ['FAIL', 'REVIEW_REQUIRED', 'VALIDATION_ERROR'])
def test_validator_failure_is_closed(monkeypatch, decision):
    monkeypatch.setattr(integrated.semantic, 'validate_consequential_narration',
        lambda *a: {'decision': decision, 'reasons': ['injected'], 'claims': []})
    row = run(ROUTE)
    assert row['used_fallback'] and row['validation']['decision'] == decision


def test_validator_exception_is_closed(monkeypatch):
    def broken(*args):
        raise RuntimeError('simulated validator error')
    monkeypatch.setattr(integrated.semantic, 'validate_consequential_narration', broken)
    assert run(ROUTE)['diagnostic'] == 'VALIDATION_ERROR'


def test_repeat_requires_continuity_and_no_new_result():
    row = run('You examine the board again; nothing new is established. ' + ROUTE,
              kind='already_searched', success=False, clues=[], known=[ROUTE])
    assert row['validation']['coverage']['decision'] == 'PASS'
    row = run(ROUTE, kind='already_searched', success=False, clues=[], known=[ROUTE])
    assert row['validation']['coverage']['decision'] == 'REVIEW_REQUIRED'


def test_no_new_discovery_status():
    row = run('You examine the barrel, but no new clue is established.', clues=[])
    assert row['validation']['coverage']['decision'] == 'PASS'


def test_source_unchanged_and_effects_rejected(monkeypatch):
    value = hook()
    before = copy.deepcopy(value)
    integrated.run_integrated_hook(value, generator=q._Replay(ROUTE, ''))
    assert value == before
    monkeypatch.setenv(q.MODE_ENV, 'integrated')
    with pytest.raises(ValueError, match='side_effects'):
        q.build_hook_input(resolution={'kind': 'investigate', 'success': True,
            'state_changes': {'items_added': ['key']}}, scene={}, known_clue_texts=[], player_text='Look')


def test_usage_accounting_required(monkeypatch):
    monkeypatch.setattr('game.provider_budget.accounting_active', lambda: False)
    with pytest.raises(RuntimeError, match='accounting'):
        integrated._LiveIntegrated('Look').generate({})


@pytest.mark.parametrize('certain', [False, True])
def test_uncertain_observation_preserves_all_facets(certain):
    prints = ('Faint overlapping prints mark the mud around the old milestone, '
              'but their number, origin, and direction stay unclear.')
    text = prints if not certain else 'Three prints lead north from the old milestone.'
    row = run(text, clues=[prints])
    assert row['validation']['coverage']['decision'] == ('REVIEW_REQUIRED' if certain else 'PASS')
    if certain:
        assert row['used_fallback']


def test_mode_specific_budget_does_not_raise_prelude_ceiling(monkeypatch):
    monkeypatch.setattr(q, '_LIVE_SENT', 6)
    monkeypatch.setattr(q, '_LIVE_STOP', '')
    monkeypatch.setattr(q, '_LIVE_TOKENS', 1000)
    monkeypatch.setattr('game.provider_budget.accounting_active', lambda: False)
    assert not q._live_budget(100)['admit']
    assert q._live_budget(100, (8, 700, 12000))['admit']
    monkeypatch.setattr(q, '_LIVE_SENT', 8)
    assert not q._live_budget(100, (8, 700, 12000))['admit']


@pytest.mark.parametrize('accepted', [False, True])
def test_http_quarantine_and_fallback(tmp_path, monkeypatch, accepted):
    from fastapi.testclient import TestClient
    from game import api
    from tests.test_pr_play_52_quarantined_integration import (
        _seed, _forbid_provider, _guard_writers, _snapshot, _scrub, _facing)
    _forbid_provider(monkeypatch)
    _seed(tmp_path / 'baseline', monkeypatch, 'frontier_gate')
    monkeypatch.delenv(q.GATE_ENV, raising=False)
    with TestClient(api.app) as client:
        baseline = client.post('/api/chat?ui_mode=player', json={'text': 'I examine the notice board.'}).json()
    baseline_state = _scrub(_snapshot())
    _seed(tmp_path / 'integrated', monkeypatch, 'frontier_gate')
    hits = _guard_writers(monkeypatch)
    monkeypatch.setenv(q.GATE_ENV, '1')
    monkeypatch.setenv(q.MODE_ENV, 'integrated')
    monkeypatch.setenv(q.SAMPLE_ENV, 'unsafe')
    monkeypatch.delenv(q.LIVE_ENV, raising=False)
    if accepted:
        original = integrated.run_integrated_hook
        monkeypatch.setattr(integrated, 'run_integrated_hook',
            lambda value: original(value, generator=q._Replay(ROUTE, '')))
    q.clear_evidence()
    with TestClient(api.app) as client:
        candidate = client.post('/api/chat?ui_mode=player', json={'text': 'I examine the notice board.'}).json()
    assert _facing({'body': candidate}) == _facing({'body': baseline})
    assert _scrub(_snapshot()) == baseline_state
    assert not hits
    assert q.evidence_records()[-1]['used_fallback'] is (not accepted)
