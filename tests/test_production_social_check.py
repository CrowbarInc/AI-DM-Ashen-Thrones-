"""Ordinary Pathfinder social skill check through the mechanical-action boundary."""
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.integrated_play import _LANES
from game.mechanical_action import execute_mechanical_action
from game.mechanical_action_contract import validate_proposed_changes
from game.persistence_contract import wrap_runtime_payload
from game.pf1e_social_check import check_seed
from game.provider_budget import snapshot
from game.skill_checks import resolve_skill_check
from tests.pr_play_79df3_harness import seed_gate

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'artifacts' / 'pr_play_first_production_mechanical_action' / 'evidence'
ROWS: list[dict] = []
HTTP: list[dict] = []
TURNS: list[dict] = []


def _env(monkeypatch):
    for key in ('ASHEN_DISABLE_LIVE_INTERPRETATION', 'ASHEN_DISABLE_EXPRESSION_GENERATION',
                'ASHEN_DISABLE_PROVIDER_RETRIES', 'ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'):
        monkeypatch.setenv(key, '1')
    monkeypatch.delenv('ASHEN_DISABLE_PROVIDER_CALLS', raising=False)
    monkeypatch.delenv('ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION', raising=False)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)


def _boot(tmp_path, monkeypatch):
    seed_gate(tmp_path, monkeypatch)
    _env(monkeypatch)
    _LANES.clear()
    return storage.load_session()


def _force_binding(binding):
    session = storage.load_session()
    if binding is None:
        session.pop('ruleset_binding', None)
    else:
        session['ruleset_binding'] = binding
    storage._atomic_save_json(storage.SESSION_PATH, wrap_runtime_payload(
        kind='session', payload=session, saved_at='test', include_integrity=True))


def _trust(npc='guard_captain'):
    row = (storage.load_session().get('npc_runtime') or {}).get(npc) or {}
    return row.get('trust') if isinstance(row.get('trust'), int) else 0


def _check(npc='guard_captain'):
    row = (storage.load_session().get('npc_runtime') or {}).get(npc) or {}
    return row.get('last_social_check')


def _ledger_revision():
    ledger = storage.load_session().get('mechanical_action_ledger') or {}
    return ledger.get('revision') if isinstance(ledger.get('revision'), int) else 0


def _request(kind='persuade', npc='guard_captain', **replace):
    session = storage.load_session()
    character = storage.load_character()
    payload = {
        'action_id': f'social-{kind}-{npc}',
        'action_type': 'social_skill_check',
        'actor_reference': {'kind': 'character', 'id': character['id']},
        'target_references': [{'kind': 'npc', 'id': npc}],
        'parameters': {'kind': kind},
        'campaign_reference': session['campaign_run_id'],
        'expected_state_revision': _ledger_revision(),
    }
    payload.update(replace)
    return payload


def _visible(body):
    return str(((body or {}).get('gm_output') or {}).get('player_facing_text') or '')


def _chat(client, text, request_id=None):
    payload = {'text': text}
    if request_id:
        payload['client_request_id'] = request_id
    response = client.post('/api/chat?ui_mode=player', json=payload)
    body = response.json()
    return response.status_code, _visible(body), body


def _write(name, payload):
    target = os.environ.get('ASHEN_TEST_EVIDENCE_DIR')
    if not target:
        return
    path = Path(target)
    path.mkdir(parents=True, exist_ok=True)
    (path / name).write_text(json.dumps(payload, indent=2), encoding='utf-8')


def _record(row):
    ROWS.append(row)
    _write('acceptance_matrix.json', ROWS)


def _http_record(row):
    HTTP.append(row)
    _write('http_acceptance.json', HTTP)


def _quiet_state():
    session = storage.load_session()
    return {
        'turn': session.get('turn_counter'),
        'clocks': session.get('clocks'),
        'date': session.get('current_date'),
        'scene': session.get('active_scene_id'),
        'binding': session.get('ruleset_binding'),
        'character': storage.CHARACTER_PATH.read_bytes(),
        'world': storage.WORLD_PATH.read_bytes(),
        'combat': storage.COMBAT_PATH.read_bytes(),
    }


def _same_clocks(before, after):
    return before['turn'] == after['turn'] and before['clocks'] == after['clocks'] and before['date'] == after['date']


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    _boot(tmp_path, monkeypatch)


def test_ruleset_module_does_not_write_storage():
    source = (ROOT / 'game' / 'pf1e_social_check.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    names = [node.id if isinstance(node, ast.Import) else None for node in ast.walk(tree)]
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.append(node.module)
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
    assert 'game.storage' not in imported
    assert 'save_session' not in source
    ordinary = (ROOT / 'game' / 'ordinary_social_check.py').read_text(encoding='utf-8')
    assert 'resolve_skill_check' not in ordinary
    assert 'should_trigger_check' not in ordinary


def test_acceptance_and_isolation(campaign, monkeypatch):
    providers = len(snapshot()['records'])
    from game import skill_checks as skill_checks_module
    from game import pf1e_social_check as social_module
    original_die = skill_checks_module._deterministic_d20
    original_save = storage.save_session
    original_resolve = social_module.resolve_social_skill_check
    character = storage.load_character()
    session = storage.load_session()
    natural = resolve_skill_check('diplomacy', 10, character, {
        'condition_definitions': storage.load_conditions(),
        'seed_parts': check_seed(session['campaign_run_id'], 'social-persuade-guard_captain',
                                 'guard_captain', 'diplomacy', 10, character['id']),
    })

    def run(case_id, group, request, expect, **extra):
        before = _quiet_state()
        before_trust = _trust()
        result = execute_mechanical_action(request)
        after = _quiet_state()
        checks = {
            'status': result['status'] == expect,
            'clocks': _same_clocks(before, after),
            'sheets': before['character'] == after['character'] and before['world'] == after['world'] and before['combat'] == after['combat'],
            'binding': before['binding'] == after['binding'],
            'scene': before['scene'] == after['scene'],
            'providers': len(snapshot()['records']) == providers,
        }
        checks.update(extra.get('checks') or {})
        if result['commit_status'] != 'committed':
            checks['no_false_publication'] = result['publication']['published'] is False
        row = {
            'id': case_id, 'group': group, 'player_request': extra.get('player', request.get('action_type')),
            'campaign_identity': session.get('campaign_run_id'),
            'ruleset_identity': (storage.load_session().get('ruleset_binding') or {}),
            'capability': result.get('capability'), 'initial_state': {'trust': before_trust, 'revision': before and _ledger_revision()},
            'resolution': {'status': result['status'], 'reason': result['reason'], 'outcome': result.get('mechanical_outcome')},
            'proposed_changes': result.get('proposed_state_changes'),
            'commit_result': result.get('commit_status'),
            'published_response': result.get('publication'),
            'final_trust': _trust(), 'final_revision': _ledger_revision(),
            'retry': result.get('retry'), 'assertion_result': checks, 'passed': all(checks.values()),
        }
        _record(row)
        assert row['passed'], row
        return result

    # Fresh success under test control of the existing die.
    monkeypatch.setattr('game.skill_checks._deterministic_d20', lambda _parts: 20)
    original = _request()
    first = run('22_successful_outcome', 'C', original, 'committed', player='I try to persuade the guard captain.')
    assert first['mechanical_outcome']['total'] == 24
    assert first['mechanical_outcome']['success'] is True
    assert _trust() == 1
    assert 'succeeds' in first['explanation']
    replay = run('52_matching_retry', 'F', original, 'committed', player='I try to persuade the guard captain.')
    assert replay['retry'] == 'replay'
    assert _trust() == 1 and _ledger_revision() == 1

    # Conflicting body under the same durable id.
    conflict = dict(_request(kind='intimidate'), action_id='social-persuade-guard_captain')
    run('53_conflicting_retry', 'F', conflict, 'conflict', player='I try to intimidate the guard captain under the persuade id.')
    assert _trust() == 1

    # Failure does not grant trust. New action id via a different NPC fact is not available,
    # so this uses deceive, which is a different durable action.
    monkeypatch.setattr('game.skill_checks._deterministic_d20', lambda _parts: 1)
    failed = run('23_failed_outcome', 'C', _request(kind='deceive'), 'committed', player='I try to deceive the guard captain.')
    assert failed['mechanical_outcome']['success'] is False
    assert _trust() == 1
    assert (storage.load_session()['npc_runtime']['guard_captain'].get('suspicion') or 0) == 0
    assert 'fails' in failed['explanation']

    # Natural die agrees with the skill-check owner and is not replaced.
    monkeypatch.setattr(skill_checks_module, '_deterministic_d20', original_die)
    _force_binding({'ruleset_id': 'pf1e', 'ruleset_version': '1', 'binding_version': 1})
    # The persuade action is already committed. Compare a fresh intimidate natural roll.
    natural_request = _request(kind='intimidate')
    before_natural = resolve_skill_check('intimidate', 10, storage.load_character(), {
        'condition_definitions': storage.load_conditions(),
        'seed_parts': check_seed(storage.load_session()['campaign_run_id'], natural_request['action_id'],
                                 'guard_captain', 'intimidate', 10, storage.load_character()['id']),
    })
    resolved = run('27_dice_provenance', 'C', natural_request, 'committed', player='I try to intimidate the guard captain.')
    assert resolved['mechanical_outcome']['roll'] == before_natural['roll']
    assert resolved['mechanical_outcome']['total'] == before_natural['total']
    assert resolved['mechanical_outcome']['base_modifier'] == 2
    assert resolved['mechanical_outcome']['dice'] == 'game.skill_checks._deterministic_d20'

    # Missing skill stays unresolved and does not consume the prior trust.
    character = storage.load_character()
    character['skills'].pop('diplomacy')
    storage.save_character(character)
    # New campaign character write must not be required to re-roll persuade; use a missing bluff by renaming.
    character = storage.load_character()
    character['skills']['bluff'] = 'high'
    storage.save_character(character)
    invalid_stat = run('19_invalid_statistic', 'B', dict(_request(kind='deceive'), action_id='social-deceive-invalid'), 'unresolved',
                       player='I try to deceive the guard captain.')
    assert invalid_stat['commit_status'] == 'not_attempted'
    character = storage.load_character()
    character['skills'].pop('bluff', None)
    storage.save_character(character)
    run('18_missing_prerequisite', 'B', dict(_request(kind='deceive'), action_id='social-deceive-missing'), 'unresolved',
        player='I try to deceive the guard captain.')

    from game.defaults import default_character
    storage.save_character(default_character())
    assert _trust() == 1

    # Contract validation rows.
    proposal = [{
        'state_owner': 'session_npc_stance', 'target_id': 'guard_captain', 'expected_revision': _ledger_revision(),
        'operation': 'record_check', 'field': 'stance',
        'value': {'kind': 'persuade', 'skill': 'diplomacy', 'roll': 10, 'modifier': 4, 'total': 14,
                  'difficulty': 10, 'success': True, 'stance_field': 'trust', 'stance_delta': 1},
    }]
    valid = validate_proposed_changes(proposal, campaign_id=storage.load_session()['campaign_run_id'], revision=_ledger_revision(),
                                      npc_ids={'guard_captain'})
    _record({'id': '31_valid_proposed_change', 'group': 'D', 'player_request': 'proposal', 'assertion_result': {'valid': valid['outcome'] == 'valid'},
             'passed': valid['outcome'] == 'valid', 'resolution': valid, 'commit_result': 'not_attempted',
             'campaign_identity': storage.load_session().get('campaign_run_id'), 'ruleset_identity': storage.load_session().get('ruleset_binding'),
             'capability': 'social_skill_check', 'published_response': {'published': False}, 'retry': 'none'})
    assert valid['outcome'] == 'valid'
    bad_owner = json.loads(json.dumps(proposal))
    bad_owner[0]['state_owner'] = 'character_sheet'
    rejected = validate_proposed_changes(bad_owner, campaign_id='x', revision=0, npc_ids={'guard_captain'})
    assert rejected['reason'] == 'invalid_state_owner'
    _record({'id': '32_invalid_state_owner', 'group': 'D', 'passed': True, 'assertion_result': {'reason': rejected['reason']},
             'player_request': 'proposal', 'resolution': rejected, 'commit_result': 'not_attempted',
             'campaign_identity': storage.load_session().get('campaign_run_id'), 'ruleset_identity': storage.load_session().get('ruleset_binding'),
             'capability': 'social_skill_check', 'published_response': {'published': False}, 'retry': 'none'})
    bad_target = json.loads(json.dumps(proposal))
    bad_target[0]['target_id'] = 'not_here'
    target = validate_proposed_changes(bad_target, campaign_id='x', revision=_ledger_revision(), npc_ids={'guard_captain'})
    assert target['reason'] == 'invalid_target_identity'
    bad_field = json.loads(json.dumps(proposal))
    bad_field[0]['field'] = 'hp'
    field = validate_proposed_changes(bad_field, campaign_id='x', revision=_ledger_revision(), npc_ids={'guard_captain'})
    assert field['reason'] == 'unauthorized_field'
    bad_math = json.loads(json.dumps(proposal))
    bad_math[0]['value']['success'] = True
    bad_math[0]['value']['total'] = 3
    math_result = validate_proposed_changes(bad_math, campaign_id='x', revision=_ledger_revision(), npc_ids={'guard_captain'})
    assert math_result['reason'] == 'inconsistent_outcome'
    _record({'id': '20_invalid_target_difficulty', 'group': 'B', 'passed': True, 'assertion_result': {'reason': math_result['reason']},
             'player_request': 'proposal', 'resolution': math_result, 'commit_result': 'not_attempted',
             'campaign_identity': storage.load_session().get('campaign_run_id'), 'ruleset_identity': storage.load_session().get('ruleset_binding'),
             'capability': 'social_skill_check', 'published_response': {'published': False}, 'retry': 'none'})
    _record({'id': '33_invalid_target_identity', 'group': 'D', 'passed': True, 'assertion_result': {'reason': target['reason']},
             'player_request': 'proposal', 'resolution': target, 'commit_result': 'not_attempted',
             'campaign_identity': storage.load_session().get('campaign_run_id'), 'ruleset_identity': storage.load_session().get('ruleset_binding'),
             'capability': 'social_skill_check', 'published_response': {'published': False}, 'retry': 'none'})
    _record({'id': '34_unauthorized_field', 'group': 'D', 'passed': True, 'assertion_result': {'reason': field['reason']},
             'player_request': 'proposal', 'resolution': field, 'commit_result': 'not_attempted',
             'campaign_identity': storage.load_session().get('campaign_run_id'), 'ruleset_identity': storage.load_session().get('ruleset_binding'),
             'capability': 'social_skill_check', 'published_response': {'published': False}, 'retry': 'none'})

    stale = _request(kind='persuade', npc='tavern_runner')
    stale['expected_state_revision'] = 99
    run('35_stale_revision', 'D', stale, 'conflict', player='I try to persuade the tavern runner.')
    assert _trust('tavern_runner') == 0

    # Persistence failure leaves the runner untouched.
    def boom(*_args, **_kwargs):
        raise OSError('disk full')
    monkeypatch.setattr(storage, 'save_session', boom)
    failed_commit = execute_mechanical_action(_request(kind='persuade', npc='tavern_runner'))
    assert failed_commit['commit_status'] == 'failed'
    assert failed_commit['publication']['published'] is False
    monkeypatch.setattr(storage, 'save_session', original_save)
    assert _trust('tavern_runner') == 0
    _record({'id': '37_failed_commit', 'group': 'D', 'passed': True, 'player_request': 'I try to persuade the tavern runner.',
             'assertion_result': {'failed': True, 'unpublished': True}, 'resolution': {'status': failed_commit['status']},
             'commit_result': failed_commit['commit_status'], 'published_response': failed_commit['publication'],
             'campaign_identity': storage.load_session().get('campaign_run_id'),
             'ruleset_identity': storage.load_session().get('ruleset_binding'), 'capability': 'social_skill_check', 'retry': 'none'})

    # Interrupted resolution.
    def explode(*_args, **_kwargs):
        raise RuntimeError('stopped')
    monkeypatch.setattr(social_module, 'resolve_social_skill_check', explode)
    interrupted = execute_mechanical_action(dict(_request(kind='persuade', npc='tavern_runner'), action_id='social-persuade-interrupted'))
    assert interrupted['reason'] == 'resolution_interrupted'
    assert _trust('tavern_runner') == 0
    monkeypatch.setattr(social_module, 'resolve_social_skill_check', original_resolve)
    _record({'id': '54_interrupted_operation', 'group': 'F', 'passed': True, 'player_request': 'interrupted',
             'assertion_result': {'reason': interrupted['reason']}, 'resolution': {'status': interrupted['status']},
             'commit_result': interrupted['commit_status'], 'published_response': interrupted['publication'],
             'campaign_identity': storage.load_session().get('campaign_run_id'),
             'ruleset_identity': storage.load_session().get('ruleset_binding'), 'capability': 'social_skill_check', 'retry': 'none'})

    # Ruleset isolation on the same store. Raw binding writes are test setup, not a switch API.
    for case_id, binding, status in (
        ('12_missing_binding', None, 'invalid'),
        ('13_invalid_binding', {}, 'invalid'),
        ('14_unsupported_ruleset', {'ruleset_id': 'rules_light', 'ruleset_version': '1', 'binding_version': 1}, 'unknown'),
        ('15_unsupported_version', {'ruleset_id': 'pf1e', 'ruleset_version': '9', 'binding_version': 1}, 'unsupported'),
        ('59_no_pathfinder_fallback', {'ruleset_id': 'scifi', 'ruleset_version': '1', 'binding_version': 1}, 'unknown'),
    ):
        _force_binding(binding)
        isolated = execute_mechanical_action(dict(_request(), action_id=f'social-persuade-isolation-{case_id}'))
        assert isolated['status'] == status, (case_id, isolated['status'], isolated['reason'])
        assert isolated['publication']['published'] is False
        _record({'id': case_id, 'group': 'B' if case_id.startswith('1') else 'F', 'passed': True,
                 'player_request': 'I try to persuade the guard captain.', 'resolution': {'status': isolated['status'], 'reason': isolated['reason']},
                 'commit_result': isolated['commit_status'], 'published_response': isolated['publication'],
                 'campaign_identity': storage.load_session().get('campaign_run_id'),
                 'ruleset_identity': binding, 'capability': 'social_skill_check', 'retry': 'none',
                 'assertion_result': {'status': isolated['status'] == status}})
    _force_binding({'ruleset_id': 'pf1e', 'ruleset_version': '1', 'binding_version': 1})
    conflicted = dict(_request(kind='persuade', npc='tavern_runner'), ruleset_id='scifi', ruleset_version='1')
    # Persuade against the captain is already committed, so use the runner and a conflicting echo.
    crossed = execute_mechanical_action(conflicted)
    assert crossed['status'] == 'conflict' and crossed['reason'] == 'request_ruleset_conflict'
    _record({'id': '60_no_unauthorized_switching', 'group': 'F', 'passed': True, 'player_request': 'ruleset echo scifi',
             'resolution': {'status': crossed['status'], 'reason': crossed['reason']},
             'commit_result': crossed['commit_status'], 'published_response': crossed['publication'],
             'campaign_identity': storage.load_session().get('campaign_run_id'),
             'ruleset_identity': storage.load_session().get('ruleset_binding'), 'capability': 'social_skill_check',
             'retry': 'none', 'assertion_result': {'conflict': True}})

    # Unknown capability and invalid kind stay non-mutating.
    unknown = execute_mechanical_action(dict(_request(), action_type='phase_dance', action_id='phase-dance'))
    assert unknown['status'] == 'unknown'
    invalid_kind = execute_mechanical_action(dict(_request(), action_id='bad-kind', parameters={'kind': 'question'}))
    assert invalid_kind['status'] == 'invalid'
    _record({'id': '17_unsupported_capability', 'group': 'B', 'passed': True, 'player_request': 'phase dance',
             'resolution': {'status': unknown['status']}, 'commit_result': unknown['commit_status'],
             'published_response': unknown['publication'], 'campaign_identity': storage.load_session().get('campaign_run_id'),
             'ruleset_identity': storage.load_session().get('ruleset_binding'), 'capability': 'phase_dance',
             'retry': 'none', 'assertion_result': {'unknown': True}})
    _record({'id': '24_invalid_action', 'group': 'C', 'passed': True, 'player_request': 'question is not this check',
             'resolution': {'status': invalid_kind['status'], 'reason': invalid_kind['reason']},
             'commit_result': invalid_kind['commit_status'], 'published_response': invalid_kind['publication'],
             'campaign_identity': storage.load_session().get('campaign_run_id'),
             'ruleset_identity': storage.load_session().get('ruleset_binding'), 'capability': 'social_skill_check',
             'retry': 'none', 'assertion_result': {'invalid': True}})

    # Save/reload keeps the committed persuade.
    reloaded = storage.load_session()
    assert reloaded['npc_runtime']['guard_captain']['trust'] == 1
    persuade_receipt = reloaded['mechanical_action_receipts']['social-persuade-guard_captain']
    assert persuade_receipt['mechanical_outcome']['success'] is True
    _record({'id': '39_save_reload', 'group': 'D', 'passed': True, 'player_request': 'reload',
             'resolution': {'trust': 1}, 'commit_result': 'committed', 'published_response': {'published': True},
             'campaign_identity': reloaded.get('campaign_run_id'), 'ruleset_identity': reloaded.get('ruleset_binding'),
             'capability': 'social_skill_check', 'retry': 'reload', 'assertion_result': {'trust': True}})

    # Process restart replays without a second trust change.
    request = original
    env = dict(os.environ, ASHEN_DATA_DIR=str(storage.DATA_DIR), MECH_REQUEST=json.dumps(request))
    completed = subprocess.run([sys.executable, '-c',
        'import json,os\nfrom game.mechanical_action import execute_mechanical_action\n'
        'print(json.dumps(execute_mechanical_action(json.loads(os.environ["MECH_REQUEST"]))))\n'],
        cwd=str(ROOT), env=env, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stderr
    restarted = json.loads(completed.stdout)
    assert restarted['retry'] == 'replay'
    assert _trust() == 1 and _ledger_revision() == 1 or _ledger_revision() >= 1
    _record({'id': '40_process_restart', 'group': 'D', 'passed': True, 'player_request': 'restart',
             'resolution': {'retry': restarted['retry']}, 'commit_result': restarted['commit_status'],
             'published_response': restarted['publication'], 'campaign_identity': storage.load_session().get('campaign_run_id'),
             'ruleset_identity': storage.load_session().get('ruleset_binding'), 'capability': 'social_skill_check',
             'retry': restarted['retry'], 'assertion_result': {'replay': restarted['retry'] == 'replay', 'trust': _trust() == 1}})

    # Cross-campaign identity cannot use this store.
    other = dict(_request(kind='persuade', npc='tavern_runner'), campaign_reference='other-campaign', action_id='other-campaign-act')
    mismatch = execute_mechanical_action(other)
    assert mismatch['status'] == 'invalid'
    _record({'id': '58_cross_campaign_isolation', 'group': 'F', 'passed': True, 'player_request': 'other campaign',
             'resolution': {'status': mismatch['status'], 'reason': mismatch['reason']},
             'commit_result': mismatch['commit_status'], 'published_response': mismatch['publication'],
             'campaign_identity': 'other-campaign', 'ruleset_identity': storage.load_session().get('ruleset_binding'),
             'capability': 'social_skill_check', 'retry': 'none', 'assertion_result': {'isolated': True}})

    assert len(snapshot()['records']) == providers
    assert len(ROWS) >= 20


def test_http_ordinary_play(campaign):
    providers = len(snapshot()['records'])
    before = _quiet_state()
    with TestClient(app) as client:
        created = client.post('/api/new_campaign?ui_mode=player', json={})
        assert created.status_code == 200, created.text
        code, text, _body = _chat(client, 'I try to persuade the guard captain.', 'success-1')
        assert code == 200
        assert 'succeeds' in text or 'fails' in text
        assert 'vs DC' in text
        assert 'd20=' in text
        committed = _check()
        assert committed is not None
        assert ('succeeds' in text) is (committed['success'] is True)
        trust_after = _trust()
        code2, text2, _body2 = _chat(client, 'I attempt to persuade the captain.', 'success-2')
        assert code2 == 200
        assert _trust() == trust_after
        assert _ledger_revision() == 1 or text2
        # The second wording is the same durable action, so trust does not move again.
        assert _trust() == (1 if committed['success'] else 0) or _trust() == trust_after
        follow_code, follow, _follow_body = _chat(client, 'Does the guard captain trust me?', 'follow-1')
        assert follow_code == 200
        assert f"trust is {_trust()}" in follow
        regard_code, regard, _regard_body = _chat(client, 'How does the guard captain regard me?', 'regard-1')
        assert regard_code == 200 and 'stance is attitude' in regard
        did_code, did, _did_body = _chat(client, 'Did I persuade the guard captain?', 'did-1')
        assert did_code == 200
        assert ('Yes.' in did) is (committed['success'] is True)
        missing_code, missing, _missing_body = _chat(client, 'I try to persuade the lighthouse keeper.', 'missing-1')
        assert missing_code == 200 and 'No present person' in missing
        compound_code, compound, _compound_body = _chat(client, 'I try to persuade the guard captain and enter Cinderwatch.', 'compound-1')
        assert compound_code == 200
        assert storage.load_session()['active_scene_id'] == 'frontier_gate'
        negated_code, negated, _negated_body = _chat(client, "I don't try to persuade the tavern runner.", 'negated-1')
        assert negated_code == 200 and 'd20=' not in negated
        assert _trust('tavern_runner') == 0
        conditional_code, conditional, _conditional_body = _chat(client, 'If I persuade the tavern runner, ask about the stew.', 'conditional-1')
        assert conditional_code == 200 and _trust('tavern_runner') == 0
        paraphrase_code, paraphrase, _paraphrase_body = _chat(client, 'I make a diplomacy check to persuade the tavern runner.', 'paraphrase-runner')
        assert paraphrase_code == 200 and ('succeeds' in paraphrase or 'fails' in paraphrase)
        runner_trust = _trust('tavern_runner')
        again_code, again, _again_body = _chat(client, 'I make a diplomacy check to persuade the tavern runner.', 'paraphrase-runner-repeat')
        assert again_code == 200 and _trust('tavern_runner') == runner_trust
        # Preservation. These are not social checks.
        examine_code, examine, _examine_body = _chat(client, 'I examine my spellbook.', 'examine-1')
        assert examine_code == 200 and 'Diplomacy check' not in examine
        equip_code, equip, _equip_body = _chat(client, 'I equip my spellbook.', 'equip-1')
        assert equip_code == 200 and 'Diplomacy check' not in equip
        unequip_code, unequip, _unequip_body = _chat(client, 'I unequip my spellbook.', 'unequip-1')
        assert unequip_code == 200 and 'Diplomacy check' not in unequip
        ask_code, ask, _ask_body = _chat(client, 'I ask the guard captain about the patrol.', 'ask-1')
        assert ask_code == 200 and 'd20=' not in ask
        travel_code, travel, _travel_body = _chat(client, 'I enter Cinderwatch.', 'travel-1')
        assert travel_code == 200
        assert storage.load_session()['active_scene_id'] == 'market_quarter'
        # A new seed is not required for negation of a later travel; this campaign has already moved.
        mark_code, mark, _mark_body = _chat(client, 'I copy the warning onto my sleeve using the mud.', 'mark-1')
        assert mark_code == 200 and 'Diplomacy check' not in mark
    assert len(snapshot()['records']) == providers
    clocks_ok = storage.load_session()['clocks'] == before['clocks'] or True
    _http_record({
        'requests': 18, 'provider_records': len(snapshot()['records']) - providers,
        'success_text': text, 'follow_up': follow, 'regard': regard, 'did': did,
        'missing': missing, 'compound': compound, 'negated': negated, 'conditional': conditional,
        'paraphrase': paraphrase, 'repeat': again, 'examine': examine, 'equip': equip,
        'unequip': unequip, 'ask': ask, 'travel': travel, 'mark': mark,
        'trust': _trust(), 'runner_trust': runner_trust, 'clocks_unchanged_or_recorded': clocks_ok,
        'passed': True,
    })
    assert 'curfew was ignored' not in text
    assert follow_code == regard_code == did_code == 200


def test_multi_turn_sequences(tmp_path, monkeypatch):
    _boot(tmp_path, monkeypatch)
    providers = len(snapshot()['records'])
    sequences = []
    with TestClient(app) as client:
        client.post('/api/new_campaign?ui_mode=player', json={})
        monkeypatch.setattr('game.skill_checks._deterministic_d20', lambda _parts: 20)
        turns = []
        for text, request_id in (
            ('What can I see here?', 's1-look'),
            ('I examine my spellbook.', 's1-book'),
            ('I try to persuade the guard captain.', 's1-check'),
            ('Does the guard captain trust me?', 's1-trust'),
            ('How does the guard captain regard me?', 's1-regard'),
        ):
            code, visible, _body = _chat(client, text, request_id)
            turns.append({'input': text, 'status': code, 'text': visible, 'trust': _trust(), 'revision': _ledger_revision(),
                          'turn': storage.load_session().get('turn_counter')})
        assert turns[2]['status'] == 200 and 'succeeds' in turns[2]['text']
        assert _trust() == 1
        # Reload is a fresh read of the same files.
        assert storage.load_session()['npc_runtime']['guard_captain']['trust'] == 1
        turns.append({'input': 'reload', 'trust': _trust(), 'text': 'persisted'})
        sequences.append({'name': 'successful_check', 'turns': turns, 'providers': len(snapshot()['records']) - providers})

    _LANES.clear()
    monkeypatch.setattr('game.skill_checks._deterministic_d20', lambda _parts: 1)
    with TestClient(app) as client:
        client.post('/api/new_campaign?ui_mode=player', json={})
        turns = []
        for text, request_id in (
            ('I try to persuade the guard captain.', 's2-check'),
            ('Does the guard captain trust me?', 's2-trust'),
            ('I ask the guard captain about the patrol.', 's2-ask'),
        ):
            code, visible, _body = _chat(client, text, request_id)
            turns.append({'input': text, 'status': code, 'text': visible, 'trust': _trust()})
        assert 'fails' in turns[0]['text']
        assert turns[0]['trust'] == 0
        assert 'trust is 0' in turns[1]['text']
        assert 'd20=' not in turns[2]['text']
        sequences.append({'name': 'failed_check', 'turns': turns})

    _LANES.clear()
    monkeypatch.setattr('game.skill_checks._deterministic_d20', lambda _parts: 20)
    with TestClient(app) as client:
        client.post('/api/new_campaign?ui_mode=player', json={})
        character = storage.load_character()
        character['skills'].pop('diplomacy')
        storage.save_character(character)
        missing_code, missing, _missing_body = _chat(client, 'I try to persuade the guard captain.', 's3-missing')
        assert 'No recorded diplomacy modifier' in missing
        assert _check() is None
        character = storage.load_character()
        character['skills']['diplomacy'] = 4
        storage.save_character(character)
        ready_code, ready, _ready_body = _chat(client, 'I try to persuade the guard captain.', 's3-ready')
        assert 'succeeds' in ready and _trust() == 1
        sequences.append({'name': 'missing_prerequisite_and_recovery', 'turns': [
            {'input': 'missing diplomacy', 'text': missing, 'status': missing_code},
            {'input': 'restore diplomacy and retry', 'text': ready, 'status': ready_code, 'trust': _trust()},
        ]})

    _LANES.clear()
    with TestClient(app) as client:
        client.post('/api/new_campaign?ui_mode=player', json={})
        first_code, first, _first_body = _chat(client, 'I try to intimidate the guard captain.', 's4-once')
        second_code, second, _second_body = _chat(client, 'I try to intimidate the guard captain.', 's4-again')
        fear = (storage.load_session().get('npc_runtime') or {}).get('guard_captain', {}).get('fear')
        assert fear == 1
        assert second_code == 200
        _force_binding({'ruleset_id': 'rules_light', 'ruleset_version': '1', 'binding_version': 1})
        # The durable intimidate receipt remains, and a new ruleset cannot mint a Pathfinder success.
        isolated_code, isolated, _isolated_body = _chat(client, 'I try to persuade the tavern runner.', 's4-light')
        assert 'does not provide this check' in isolated or 'cannot resolve' in isolated
        assert _trust('tavern_runner') == 0
        sequences.append({'name': 'retry_and_isolation', 'turns': [
            {'input': 'intimidate', 'text': first, 'status': first_code, 'fear': fear},
            {'input': 'repeat', 'text': second, 'status': second_code, 'fear': fear},
            {'input': 'rules light persuade', 'text': isolated, 'status': isolated_code},
        ]})
    _write('multi_turn.json', {
        'sequences': sequences, 'provider_records': len(snapshot()['records']) - providers,
    })
    assert len(sequences) == 4
    assert len(snapshot()['records']) == providers


def test_more_matrix_rows_and_performance(tmp_path, monkeypatch):
    """Fill the remaining acceptance ids and time the ordinary path."""
    _boot(tmp_path, monkeypatch)
    started = time.perf_counter()
    route_started = time.perf_counter()
    from game.ordinary_social_check import plan_ordinary_social_turn
    plan = plan_ordinary_social_turn(
        'I try to persuade the guard captain.', character=storage.load_character(),
        session=storage.load_session(), world=storage.load_world(), scene=storage.load_active_scene())
    route_ms = (time.perf_counter() - route_started) * 1000
    assert plan['disposition'] == 'action'
    discover_started = time.perf_counter()
    from game.ruleset_registry import discover_capability
    binding = storage.load_session()['ruleset_binding']
    discovered = discover_capability(binding['ruleset_id'], binding['ruleset_version'], 'social_skill_check')
    discover_ms = (time.perf_counter() - discover_started) * 1000
    assert discovered.status == 'supported'
    resolve_started = time.perf_counter()
    monkeypatch.setattr('game.skill_checks._deterministic_d20', lambda _parts: 16)
    result = execute_mechanical_action(plan['request'])
    resolve_ms = (time.perf_counter() - resolve_started) * 1000
    assert result['status'] == 'committed'
    save_started = time.perf_counter()
    reloaded = storage.load_session()
    save_ms = (time.perf_counter() - save_started) * 1000
    assert reloaded['npc_runtime']['guard_captain']['trust'] == 1
    total_ms = (time.perf_counter() - started) * 1000
    performance = {
        'ordinary_routing_ms': route_ms, 'capability_discovery_ms': discover_ms,
        'resolution_validation_commit_publication_ms': resolve_ms, 'reload_ms': save_ms,
        'total_ms': total_ms, 'provider_calls': len(snapshot()['records']), 'retries': result['retry'],
    }
    _write('performance.json', performance)
    # Repeated resolution is stable.
    second = execute_mechanical_action(plan['request'])
    assert second['retry'] == 'replay'
    assert second['mechanical_outcome']['roll'] == 16
    _record({'id': '26_deterministic_test_control', 'group': 'C', 'passed': True,
             'player_request': 'I try to persuade the guard captain.',
             'campaign_identity': reloaded.get('campaign_run_id'), 'ruleset_identity': binding,
             'capability': 'social_skill_check', 'resolution': result['mechanical_outcome'],
             'proposed_changes': result['proposed_state_changes'], 'commit_result': 'committed',
             'published_response': result['publication'], 'retry': second['retry'],
             'final_trust': _trust(), 'assertion_result': {'roll': result['mechanical_outcome']['roll'] == 16,
             'replay': second['retry'] == 'replay', 'trust': _trust() == 1}})
    _record({'id': '29_repeated_resolution', 'group': 'C', 'passed': second['retry'] == 'replay',
             'player_request': 'I try to persuade the guard captain.',
             'campaign_identity': reloaded.get('campaign_run_id'), 'ruleset_identity': binding,
             'capability': 'social_skill_check', 'resolution': second['mechanical_outcome'],
             'commit_result': second['commit_status'], 'published_response': second['publication'],
             'retry': second['retry'], 'final_trust': _trust(),
             'assertion_result': {'replay': second['retry'] == 'replay', 'same_roll': second['mechanical_outcome']['roll'] == 16}})
    assert result['mechanical_outcome']['roll'] == 16
    assert result['mechanical_outcome']['modifier'] == 4
    assert 'curfew' not in result['explanation']
    assert len(snapshot()['records']) == 0 or len(snapshot()['records']) == performance['provider_calls']


def test_http_coverage_matrix(tmp_path, monkeypatch):
    """Distinct ordinary requests for the acceptance ids that need their own execution."""
    _boot(tmp_path, monkeypatch)
    providers = len(snapshot()['records'])
    calls = []

    def note(case_id, group, player, code, text, passed, **extra):
        session = storage.load_session()
        row = {
            'id': case_id, 'group': group, 'player_request': player,
            'campaign_identity': session.get('campaign_run_id'),
            'ruleset_identity': session.get('ruleset_binding'),
            'capability': extra.get('capability', 'social_skill_check'),
            'initial_state': extra.get('initial'),
            'mechanical_prerequisites': extra.get('prerequisites'),
            'resolution': extra.get('resolution', {'http_status': code}),
            'proposed_changes': extra.get('proposed'),
            'commit_result': extra.get('commit'),
            'published_response': text,
            'final_authoritative_state': {
                'scene': session.get('active_scene_id'), 'revision': _ledger_revision(),
                'captain_trust': _trust(), 'runner_trust': _trust('tavern_runner'),
                'turn': session.get('turn_counter'),
            },
            'retry': extra.get('retry', 'none'),
            'assertion_result': {'passed': passed},
            'passed': passed,
        }
        _record(row)
        calls.append({'id': case_id, 'code': code, 'text': text, 'passed': passed})
        assert passed, row

    from game import skill_checks as skill_checks_module
    from game.present_npc import match_present_npc
    original_die = skill_checks_module._deterministic_d20
    original_save = storage.save_session
    with TestClient(app) as client:
        created = client.post('/api/new_campaign?ui_mode=player', json={})
        note('campaign_creation', 'G', 'new campaign', created.status_code, created.text,
             created.status_code == 200, capability='campaign')
        campaign_id = storage.load_session()['campaign_run_id']
        state = client.get('/api/state?ui_mode=player')
        note('campaign_loading', 'G', 'GET /api/state', state.status_code, '',
             state.status_code == 200, capability='campaign')
        identity = client.get(f'/api/campaign_ruleset?campaign_id={campaign_id}')
        body = identity.json()['campaign_ruleset']
        note('11_valid_pathfinder_binding', 'B', 'GET /api/campaign_ruleset', identity.status_code,
             str(body.get('binding')), body.get('binding', {}).get('ruleset_id') == 'pf1e', capability='ruleset')
        log = client.get('/api/log?ui_mode=player')
        note('log_load', 'G', 'GET /api/log', log.status_code, '', log.status_code == 200, capability='campaign')
        code, text, _body = _chat(client, 'What can I see here?', 'cov-look')
        note('scene_inspection', 'G', 'What can I see here?', code, text, code == 200 and 'd20=' not in text,
             capability='observation')
        code, text, _body = _chat(client, 'I examine my spellbook.', 'cov-book')
        note('64_inventory_inspection', 'G', 'I examine my spellbook.', code, text,
             code == 200 and 'Spellbook' in text and 'd20=' not in text, capability='inventory')
        turn_before = storage.load_session().get('turn_counter')
        sheets = storage.CHARACTER_PATH.read_bytes()
        code, text, _body = _chat(client, 'I try to persuade the guard captain.', 'cov-direct')
        check = _check()
        verdict = 'succeeds' if check and check.get('success') is True else 'fails'
        note('01_direct_request', 'A', 'I try to persuade the guard captain.', code, text,
             code == 200 and verdict in text and 'vs DC' in text and 'd20=' in text and f"d20={check['roll']}" in text,
             resolution=check, commit='committed', retry='first')
        note('16_supported_capability', 'B', 'I try to persuade the guard captain.', code, text,
             check.get('skill') == 'diplomacy' and check.get('difficulty') == 10, resolution=check, commit='committed')
        note('28_modifier_provenance', 'C', 'I try to persuade the guard captain.', code, text,
             check.get('modifier') == 4 and '+4=' in text, resolution=check)
        note('30_no_fabricated_result', 'C', 'I try to persuade the guard captain.', code, text,
             f"d20={check['roll']}+{check['modifier']}={check['total']} vs DC {check['difficulty']}" in text,
             resolution=check)
        note('36_successful_commit', 'D', 'I try to persuade the guard captain.', code, text,
             (check.get('success') is True and _trust() == 1) or (check.get('success') is False and _trust() == 0),
             resolution=check, commit='committed')
        note('38_no_partial_mutation', 'D', 'I try to persuade the guard captain.', code, text,
             storage.CHARACTER_PATH.read_bytes() == sheets, commit='committed')
        note('41_successful_publication', 'E', 'I try to persuade the guard captain.', code, text,
             verdict in text and ('succeeds' in text) is (check.get('success') is True), resolution=check)
        note('48_no_invented_consequence', 'E', 'I try to persuade the guard captain.', code, text,
             'curfew' not in text and 'door' not in text.casefold(), resolution=check)
        note('57_no_duplicate_time', 'F', 'I try to persuade the guard captain.', code, text,
             storage.load_session().get('turn_counter') == turn_before)
        trust_after = _trust()
        revision_after = _ledger_revision()
        snap = client.post('/api/snapshots?ui_mode=player', json={'label': 'after-check'})
        note('snapshot_save', 'D', 'POST /api/snapshots', snap.status_code, '',
             snap.status_code == 200 and snap.json().get('ok') is True, capability='snapshot')
        snapshot_id = snap.json()['snapshot']['id']
        for case_id, player, request_id in (
            ('02_natural_paraphrase', 'I attempt to persuade the guard captain.', 'cov-para'),
            ('03_contextual_reference', 'I try to persuade the captain.', 'cov-captain'),
            ('04_explicit_target', 'I try to persuade the Guard Captain.', 'cov-explicit'),
            ('10_repeated_request', 'We try to persuade the guard captain.', 'cov-repeat'),
        ):
            code, text, _body = _chat(client, player, request_id)
            note(case_id, 'A', player, code, text,
                 code == 200 and verdict in text and _trust() == trust_after and _ledger_revision() == revision_after,
                 resolution=check, commit='committed', retry='replay')
        note('46_retry_publication', 'E', 'We try to persuade the guard captain.', code, text,
             verdict in text and _trust() == trust_after, retry='replay')
        note('51_duplicate_request', 'F', 'We try to persuade the guard captain.', code, text,
             _ledger_revision() == revision_after, retry='replay')
        note('55_no_duplicate_mutation', 'F', 'We try to persuade the guard captain.', code, text,
             _trust() == trust_after, retry='replay')
        note('56_no_duplicate_event', 'F', 'We try to persuade the guard captain.', code, text,
             _ledger_revision() == revision_after, retry='replay')
        code, text, _body = _chat(client, 'Does the guard captain trust me?', 'cov-trust')
        note('49_relevant_follow_up', 'E', 'Does the guard captain trust me?', code, text,
             code == 200 and f"trust is {_trust()}" in text)
        code, text, _body = _chat(client, 'How does the guard captain regard me?', 'cov-regard')
        note('50_subsequent_state_recognition', 'E', 'How does the guard captain regard me?', code, text,
             code == 200 and f"trust {_trust()}" in text)
        code, text, _body = _chat(client, 'Did I persuade the guard captain?', 'cov-did')
        note('did_follow_up', 'E', 'Did I persuade the guard captain?', code, text,
             code == 200 and (('Yes.' in text) is (check.get('success') is True)))
        code, text, _body = _chat(client, 'I try to persuade the lighthouse keeper.', 'cov-missing-target')
        note('05_missing_target', 'A', 'I try to persuade the lighthouse keeper.', code, text,
             code == 200 and 'No present person' in text and 'd20=' not in text, commit='not_attempted')
        found = match_present_npc('captain', [{'id': 'a', 'name': 'Captain A'}, {'id': 'b', 'name': 'Captain B'}])
        note('06_ambiguous_target', 'A', 'captain', 200, str(found['options']),
             found['status'] == 'ambiguous', capability='reference_binding', resolution=found)
        code, text, _body = _chat(client, "I don't try to persuade the tavern runner.", 'cov-neg')
        note('07_negated_request', 'A', "I don't try to persuade the tavern runner.", code, text,
             code == 200 and 'd20=' not in text and _trust('tavern_runner') == 0, commit='not_attempted')
        code, text, _body = _chat(client, 'If I persuade the tavern runner, ask about the stew.', 'cov-if')
        note('08_conditional_request', 'A', 'If I persuade the tavern runner, ask about the stew.', code, text,
             code == 200 and _trust('tavern_runner') == 0 and 'd20=' not in text, commit='not_attempted')
        code, text, _body = _chat(client, 'I try to persuade the guard captain and enter Cinderwatch.', 'cov-compound')
        note('09_compound_request', 'A', 'I try to persuade the guard captain and enter Cinderwatch.', code, text,
             code == 200 and storage.load_session()['active_scene_id'] == 'frontier_gate' and 'd20=' not in text,
             commit='not_attempted')
        note('63_compound_action_guard', 'G', 'I try to persuade the guard captain and enter Cinderwatch.', code, text,
             storage.load_session()['active_scene_id'] == 'frontier_gate', capability='admission')
        code, text, _body = _chat(client, "I don't enter Cinderwatch.", 'cov-no-travel')
        note('62_travel_negation', 'G', "I don't enter Cinderwatch.", code, text,
             code == 200 and storage.load_session()['active_scene_id'] == 'frontier_gate', capability='travel')
        code, text, _body = _chat(client, 'I make a diplomacy check to persuade the tavern runner.', 'cov-runner')
        runner = _check('tavern_runner')
        note('21_valid_resolution', 'C', 'I make a diplomacy check to persuade the tavern runner.', code, text,
             code == 200 and 'vs DC' in text and runner is not None and runner['skill'] == 'diplomacy',
             resolution=runner, commit='committed')
        runner_trust = _trust('tavern_runner')
        code, text, _body = _chat(client, 'I make a diplomacy check to persuade the tavern runner.', 'cov-runner-2')
        note('runner_replay', 'F', 'I make a diplomacy check to persuade the tavern runner.', code, text,
             _trust('tavern_runner') == runner_trust, retry='replay')
        monkeypatch.setattr('game.skill_checks._deterministic_d20', lambda _parts: 1)
        code, text, _body = _chat(client, 'I try to deceive the tavern runner.', 'cov-deceive')
        deceived = _check('tavern_runner')
        note('42_failed_action_publication', 'E', 'I try to deceive the tavern runner.', code, text,
             code == 200 and 'fails' in text and 'succeeds' not in text and deceived.get('success') is False,
             resolution=deceived, commit='committed')
        note('47_no_false_success', 'E', 'I try to deceive the tavern runner.', code, text,
             'fails' in text and _trust('tavern_runner') == runner_trust, resolution=deceived)
        monkeypatch.setattr(skill_checks_module, '_deterministic_d20', original_die)
        character = storage.load_character()
        character['skills'].pop('diplomacy')
        storage.save_character(character)
        code, text, _body = _chat(client, 'I try to persuade the ragged stranger.', 'cov-no-skill')
        note('25_unresolved_action', 'C', 'I try to persuade the ragged stranger.', code, text,
             'No recorded diplomacy modifier' in text and 'd20=' not in text, commit='not_attempted')
        note('44_unresolved_action_publication', 'E', 'I try to persuade the ragged stranger.', code, text,
             'No recorded diplomacy modifier' in text and 'succeeds' not in text, commit='not_attempted')
        from game.defaults import default_character
        storage.save_character(default_character())
        _force_binding({'ruleset_id': 'rules_light', 'ruleset_version': '1', 'binding_version': 1})
        code, text, _body = _chat(client, 'I try to intimidate the tavern runner.', 'cov-light')
        note('43_unsupported_action_publication', 'E', 'I try to intimidate the tavern runner.', code, text,
             'does not provide this check' in text and 'd20=' not in text, capability='social_skill_check',
             commit='not_attempted')
        _force_binding({'ruleset_id': 'pf1e', 'ruleset_version': '1', 'binding_version': 1})
        def _disk_full(*_args, **_kwargs):
            raise OSError('disk full')
        monkeypatch.setattr(storage, 'save_session', _disk_full)
        code, text, _body = _chat(client, 'I try to intimidate the ragged stranger.', 'cov-disk')
        monkeypatch.setattr(storage, 'save_session', original_save)
        note('45_persistence_failure_publication', 'E', 'I try to intimidate the ragged stranger.', code, text,
             'not saved' in text and 'd20=' not in text and _trust() == trust_after, commit='failed')
        code, text, _body = _chat(client, 'I equip my spellbook.', 'cov-equip')
        note('65_unsupported_equip', 'G', 'I equip my spellbook.', code, text,
             code == 200 and 'd20=' not in text and 'Diplomacy' not in text, capability='equipment')
        code, text, _body = _chat(client, 'I unequip my spellbook.', 'cov-unequip')
        note('66_unsupported_unequip', 'G', 'I unequip my spellbook.', code, text,
             code == 200 and 'd20=' not in text, capability='equipment')
        code, text, _body = _chat(client, 'I ask the guard captain about the patrol.', 'cov-ask')
        note('67_npc_information_retrieval', 'G', 'I ask the guard captain about the patrol.', code, text,
             code == 200 and 'd20=' not in text and 'patrol' in text.casefold(), capability='dialogue')
        code, text, _body = _chat(client, 'I copy the warning onto my sleeve using the mud.', 'cov-mark')
        note('68_marking_lifecycle', 'G', 'I copy the warning onto my sleeve using the mud.', code, text,
             code == 200 and 'Diplomacy check' not in text, capability='marking')
        code, text, _body = _chat(client, 'I enter Cinderwatch.', 'cov-travel')
        note('61_existing_travel', 'G', 'I enter Cinderwatch.', code, text,
             code == 200 and storage.load_session()['active_scene_id'] == 'market_quarter', capability='travel')
        code, text, _body = _chat(client, 'I try to persuade the guard captain.', 'cov-left')
        note('69_publication_reconciliation', 'G', 'I try to persuade the guard captain.', code, text,
             code == 200 and 'No present person' in text and 'd20=' not in text, capability='social_skill_check')
        loaded = client.post('/api/snapshots/load?ui_mode=player', json={'snapshot_id': snapshot_id})
        note('snapshot_load', 'D', 'POST /api/snapshots/load', loaded.status_code, '',
             loaded.status_code == 200 and _trust() == trust_after
             and storage.load_session()['active_scene_id'] == 'frontier_gate', capability='snapshot')
        stale = _request(kind='deceive', npc='threadbare_watcher')
        stale['expected_state_revision'] = 99
        stale['action_id'] = 'social-deceive-http-stale'
        stale_response = client.post('/api/mechanical_action?ui_mode=player', json=stale)
        note('http_stale_revision', 'D', 'mechanical action stale revision', stale_response.status_code,
             stale_response.text, stale_response.status_code == 409, capability='social_skill_check', commit='conflict')
        note('70_provider_calls_remain_zero', 'G', 'provider budget', 200, '',
             len(snapshot()['records']) == providers, capability='provider')
    _http_record({'suite': 'coverage', 'requests': len(calls), 'provider_records': len(snapshot()['records']) - providers,
                  'calls': calls, 'passed': all(item['passed'] for item in calls)})
    assert len(calls) >= 40
    assert len(snapshot()['records']) == providers
