"""Action-focused recovery and optional repeat bypass, without real providers."""
import json

import pytest

from game import api, storage
from game import integrated_investigation_narration as integrated
from game import quarantined_investigation_narration as q
from tests.helpers.turn_pipeline_http_fixtures import _gm_response
from tests.test_pr_play_52_quarantined_integration import _seed, _forbid_provider
from tests.test_pr_play_61_player_facing import _bind, _session, _authority, NOTICE, BARREL, REPEAT
from tests.test_pr_play_57_integrated_narration import ROUTE


def setup_session(tmp_path, monkeypatch):
    _forbid_provider(monkeypatch)
    _seed(tmp_path, monkeypatch, 'frontier_gate')
    _bind(monkeypatch, storage.load_session()['campaign_run_id'])
    monkeypatch.setattr(api, 'call_gpt', lambda *a, **k: _gm_response(
        'Provider calls are disabled for this run, so no live narration was generated.'))
    q.clear_evidence()


def test_action_specific_fallback_and_recovery(tmp_path, monkeypatch):
    actions = [NOTICE, BARREL, REPEAT, 'I look around the gate.', BARREL]
    setup_session(tmp_path / 'control', monkeypatch)
    monkeypatch.delenv(q.GATE_ENV, raising=False)
    _session(actions)
    expected = _authority()
    setup_session(tmp_path / 'experimental', monkeypatch)
    monkeypatch.setenv(q.SAMPLE_ENV, 'unsafe')
    rows = _session(actions)
    texts = [r['gm_output']['player_facing_text'] for r in rows]
    assert texts[0].startswith('You examine the notice board.')
    assert texts[1].startswith('You examine the rain barrel; no new clue is established.')
    assert texts[2].startswith('You examine the notice board again.')
    assert ROUTE in texts[2] and 'nothing new' in texts[2]
    assert texts[3].startswith('You examine the gate; no new clue is established.')
    assert all('silver key' not in t and 'census' not in t for t in texts)
    assert ROUTE in texts[0]
    assert all(ROUTE not in texts[index] for index in (1, 3, 4))
    after = _authority()
    assert after['clues'] == [ROUTE]
    assert after == expected


@pytest.mark.parametrize('fault', ['timeout', 'provider_error'])
def test_provider_fault_recovery(tmp_path, monkeypatch, fault):
    setup_session(tmp_path, monkeypatch)
    monkeypatch.setenv(q.FAULT_ENV, fault)
    rows = _session([BARREL, NOTICE, REPEAT])
    assert all(qr['used_fallback'] for qr in q.evidence_records())
    assert all('no live narration' not in r['gm_output']['player_facing_text'] for r in rows)
    assert _authority()['clues'] == [ROUTE]


def test_repeat_fast_path_is_authoritative_and_optional(tmp_path, monkeypatch):
    setup_session(tmp_path, monkeypatch)
    _session([NOTICE])
    hook = q.evidence_records()[-1]['hook_input']
    repeat = json.loads(json.dumps(hook))
    repeat['resolution'].update(kind='already_searched', success=False, discovered_clues=[], clue_text='',
                                state_changes={'already_searched': True})
    monkeypatch.setenv(q.LIVE_ENV, '1')
    monkeypatch.setenv('ASHEN_INTEGRATED_REPEAT_FAST_PATH', '1')
    result = integrated.run_integrated_hook(repeat)
    assert result['deterministic_fast_path'] is True
    assert result['provider_requests'] == result['generator_calls'] == 0
    assert result['provider_skip_reason'] == 'resolved_repeat_without_new_information'
    # Explicit replay and injected failures are never bypassed.
    replay = integrated.run_integrated_hook(repeat, generator=q._Replay(ROUTE, ''))
    assert not replay.get('deterministic_fast_path')
    monkeypatch.setenv(q.FAULT_ENV, 'timeout')
    assert integrated.run_integrated_hook(repeat)['diagnostic'] == 'provider_timeout'


def test_public_target_label_does_not_invent_an_object():
    scene = {'visible_facts': ['An amber sundial rests beside the bridge.']}
    assert q._public_target_label('I examine the amber sundial again.', scene) == 'amber sundial'
    assert q._public_target_label('I examine the silver key.', scene) is None
    assert q._public_target_label('I examine the sundial. You gain gold.', scene) is None


def test_failed_examination_keeps_failure_without_inventing_discovery():
    hook = q.build_hook_input(
        resolution={'kind': 'investigate', 'success': False, 'state_changes': {}},
        scene={'scene': {'visible_facts': ['An amber sundial rests beside the bridge.']}},
        known_clue_texts=[], player_text='I examine the amber sundial.')
    contract, request = integrated.outcome_contract(hook)
    text = integrated.action_fallback(contract, hook)
    assert text == 'You examine the amber sundial, but no new clue is established.'
    assert request['resolved_outcome'] == {'status': 'failed', 'success': False}
    assert not contract.outcome.revealed
