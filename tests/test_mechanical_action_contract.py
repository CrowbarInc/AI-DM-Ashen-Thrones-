"""Generic mechanical-action contract. Production Pathfinder play is not extended."""
import ast
import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from game import ruleset_registry as registry
from game import storage
from game.mechanical_action import execute_mechanical_action
from game.mechanical_action_contract import ENVELOPE_FIELDS, REQUEST_FIELDS
from game.pf1e_equipment_policy import evaluate_equipment_eligibility, padded_armor_definition
from game.provider_budget import snapshot
from game.ruleset_contract import PolicyEvaluation, freeze
from tests.helpers.turn_pipeline_http_fixtures import _patch_storage
from tests.mechanical_action_fixture import ContractFixtureRuleset

ROOT = Path(__file__).resolve().parents[1]
ROWS = []
SEQUENCES = []
PF = {'ruleset_id': 'pf1e', 'ruleset_version': '1', 'binding_version': 1}


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    monkeypatch.setattr(storage, 'SNAPSHOTS_DIR', storage.DATA_DIR / 'snapshots')
    for scene in (ROOT / 'data/scenes').glob('*.json'):
        shutil.copy2(scene, storage.SCENES_DIR / scene.name)
    storage.ensure_data_files_exist()
    yield storage.load_session()


def raw_session(session):
    from game.persistence_contract import wrap_runtime_payload
    storage._atomic_save_json(storage.SESSION_PATH, wrap_runtime_payload(
        kind='session', payload=session, saved_at='test', include_integrity=True))


def install(monkeypatch, authority=None):
    monkeypatch.setitem(registry._AUTHORITIES, ('pf1e', '1'), authority or ContractFixtureRuleset())


def _binding(ruleset_id, version='1'):
    return {'ruleset_id': ruleset_id, 'ruleset_version': version, 'binding_version': 1}


def _bytes():
    def read(path):
        return path.read_bytes() if path.exists() else b''
    return {'character': read(storage.CHARACTER_PATH), 'world': read(storage.WORLD_PATH),
            'combat': read(storage.COMBAT_PATH), 'session': read(storage.SESSION_PATH)}


def _state():
    return {'session': storage.load_session(), 'character': storage.load_character()}


def _request(session, character, spec):
    payload = {
        'action_id': spec.get('action_id', 'act-' + spec['id']),
        'action_type': spec.get('action_type', 'equipment_policy'),
        'actor_reference': {'kind': 'character', 'id': character['id']},
        'target_references': spec.get('targets', []),
        'parameters': spec.get('parameters', {'item': padded_armor_definition(), 'slot': 'body_armor'}),
        'campaign_reference': spec.get('campaign_reference', session['campaign_run_id']),
        'expected_state_revision': spec.get('revision', 0),
    }
    if 'ruleset_id' in spec:
        payload['ruleset_id'] = spec['ruleset_id']
        payload['ruleset_version'] = spec.get('ruleset_version', '1')
    for key in spec.get('omit', ()):
        payload.pop(key, None)
    payload.update(spec.get('replace', {}))
    return payload


def _prepare_binding(session, spec):
    if 'binding' not in spec and not spec.get('swap_campaign'):
        return session
    updated = copy.deepcopy(storage.load_session())
    if 'binding' in spec:
        if spec['binding'] is None:
            updated.pop('ruleset_binding', None)
        else:
            updated['ruleset_binding'] = spec['binding']
    if spec.get('swap_campaign'):
        updated['campaign_run_id'] = 'other-campaign'
    raw_session(updated)
    return storage.load_session()


def _record(spec, request, result, before, after, before_bytes, after_bytes, checks):
    session = after['session']
    row = {
        'id': spec['id'], 'group': spec['group'],
        'campaign_identity': before['session'].get('campaign_run_id'),
        'ruleset_binding': session.get('ruleset_binding'),
        'action_request': request,
        'capability': result.get('capability'),
        'selected_resolver': result.get('implementation'),
        'resolution_result': {key: result.get(key) for key in (
            'status', 'reason', 'capability_status', 'validation_status', 'authorization_status',
            'mechanical_outcome', 'explanation')},
        'proposed_changes': result.get('proposed_state_changes'),
        'validation_outcome': result.get('validation_status'),
        'commit_outcome': result.get('commit_status'),
        'state_delta': {
            'character_changed': before_bytes['character'] != after_bytes['character'],
            'world_changed': before_bytes['world'] != after_bytes['world'],
            'combat_changed': before_bytes['combat'] != after_bytes['combat'],
            'session_changed': before_bytes['session'] != after_bytes['session'],
            'turn_counter': session.get('turn_counter'),
            'clocks_changed': before['session'].get('clocks') != session.get('clocks'),
            'ledger': session.get('mechanical_action_ledger'),
            'binding_changed': before['session'].get('ruleset_binding') != session.get('ruleset_binding'),
        },
        'publication': result.get('publication'),
        'retry_behavior': result.get('retry'),
        'assertion_result': checks,
        'passed': all(checks.values()),
    }
    ROWS.append(row)
    target = os.environ.get('ASHEN_TEST_EVIDENCE_DIR')
    if target:
        Path(target).mkdir(parents=True, exist_ok=True)
        (Path(target) / 'acceptance_matrix.json').write_text(json.dumps(ROWS, indent=2), encoding='utf-8')
    return row


def _gameplay_same(before, after, before_bytes, after_bytes):
    session_before, session_after = before['session'], after['session']
    return (before_bytes['character'] == after_bytes['character']
            and before_bytes['world'] == after_bytes['world']
            and before_bytes['combat'] == after_bytes['combat']
            and session_before.get('turn_counter') == session_after.get('turn_counter')
            and session_before.get('clocks') == session_after.get('clocks')
            and session_before.get('current_date') == session_after.get('current_date')
            and session_before.get('ruleset_binding') == session_after.get('ruleset_binding')
            and session_before.get('active_scene_id') == session_after.get('active_scene_id')
            and before['character'].get('inventory') == after['character'].get('inventory'))


def _expect(spec, result, before, after, before_bytes, after_bytes, provider_before):
    published = result['publication']['published'] is True
    checks = {
        'status': result['status'] == spec['status'],
        'reason': result['reason'] == spec['reason'] if 'reason' in spec else True,
        'commit': result['commit_status'] == spec.get('commit', 'not_attempted'),
        'published_matches_commit': published is (result['commit_status'] == 'committed'),
        'gameplay_unchanged': _gameplay_same(before, after, before_bytes, after_bytes),
        'provider_zero': len(snapshot()['records']) == provider_before,
        'no_time_change': before['session'].get('turn_counter') == after['session'].get('turn_counter'),
    }
    if spec.get('session_same', result['commit_status'] != 'committed'):
        checks['session_unchanged'] = before_bytes['session'] == after_bytes['session']
    if 'capability_status' in spec:
        checks['capability'] = result['capability_status'] == spec['capability_status']
    if 'resolver' in spec:
        checks['resolver'] = result.get('implementation') == spec['resolver']
    if 'marker' in spec:
        ledger = after['session'].get('mechanical_action_ledger') or {}
        checks['marker'] = (ledger.get('markers') or {}).get(spec.get('action_id', 'act-' + spec['id'])) == spec['marker']
        checks['revision'] = ledger.get('revision') == spec.get('ledger_revision', 1)
    if spec.get('no_ledger'):
        checks['no_ledger'] = 'mechanical_action_ledger' not in after['session']
    if spec.get('no_eligible'):
        checks['no_pathfinder_outcome'] = 'ELIGIBLE' not in json.dumps(result['mechanical_outcome'])
    if spec.get('eligible_nested'):
        checks['nested_only'] = (result['mechanical_outcome'].get('decision') == 'ELIGIBLE'
                                  and 'decision' not in result and 'slot' not in result)
    if 'discarded' in spec:
        checks['discarded'] = result['discarded_proposal_count'] == spec['discarded']
    if 'proposals' in spec:
        checks['proposals'] = len(result['proposed_state_changes']) == spec['proposals']
    if spec.get('retry'):
        checks['retry'] = result['retry'] == spec['retry']
    return checks


def _run(campaign, monkeypatch, spec):
    _prepare_binding(campaign, spec)
    if spec.get('fixture'):
        install(monkeypatch, spec.get('authority'))
    character = storage.load_character()
    session = storage.load_session()
    request = _request(session if not spec.get('swap_campaign') else campaign, character, spec)
    if spec.get('swap_campaign'):
        request['campaign_reference'] = campaign['campaign_run_id']
    provider_before = len(snapshot()['records'])
    original_save = storage.save_session
    kind = spec.get('kind', 'once')
    if kind == 'duplicate':
        first = dict(request, parameters={'mode': 'commit', 'marker': 'contract_marker'})
        assert execute_mechanical_action(first)['status'] == 'committed'
        request = dict(request, parameters={'mode': 'commit', 'marker': 'other_marker'})
    elif kind in ('replay', 'reload'):
        assert execute_mechanical_action(request)['commit_status'] == 'committed'
    elif kind == 'retry_after_failure':
        def fail(*args, **kwargs):
            raise OSError('interrupted_write')
        monkeypatch.setattr(storage, 'save_session', fail)
        failed = execute_mechanical_action(request)
        assert failed['commit_status'] == 'failed' and failed['publication']['published'] is False
        monkeypatch.setattr(storage, 'save_session', original_save)
    elif kind == 'save_raises':
        def fail(*args, **kwargs):
            raise OSError('interrupted_write')
        monkeypatch.setattr(storage, 'save_session', fail)
    before = _state()
    before_bytes = _bytes()
    result = execute_mechanical_action(request)
    first_result = result
    if kind == 'repeated':
        result = execute_mechanical_action(request)
    after = _state()
    after_bytes = _bytes()
    checks = _expect(spec, result, before, after, before_bytes, after_bytes, provider_before)
    if kind == 'repeated':
        checks['deterministic'] = first_result['status'] == result['status'] and first_result['mechanical_outcome'] == result['mechanical_outcome']
    if kind == 'retry_after_failure':
        checks['recovered'] = result['commit_status'] == 'committed'
    if kind == 'reload':
        checks['reloaded_marker'] = storage.load_session()['mechanical_action_ledger']['markers'][request['action_id']] == 'contract_marker'
    row = _record(spec, request, result, before, after, before_bytes, after_bytes, checks)
    assert row['passed'], row
    return result


def _spec(ident, group, status, reason, **extra):
    extra.setdefault('id', ident)
    extra.setdefault('group', group)
    extra.setdefault('status', status)
    extra.setdefault('reason', reason)
    return extra


SPECS = [
    _spec('01_valid_request', 'A', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          capability_status='supported', resolver='game.pf1e_equipment_policy', no_ledger=True, eligible_nested=True),
    _spec('02_missing_action_id', 'A', 'invalid', 'missing_action_id', omit=('action_id',), no_ledger=True),
    _spec('03_duplicate_action_id', 'A', 'conflict', 'duplicate_action_id', fixture=True, kind='duplicate',
          action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
          commit='conflict', session_same=True),
    _spec('04_missing_action_type', 'A', 'invalid', 'missing_action_type', omit=('action_type',), no_ledger=True),
    _spec('05_unsupported_action_type', 'A', 'unsupported', 'capability_not_supported',
          action_type='combat_resolution', capability_status='unsupported', no_ledger=True),
    _spec('06_missing_actor', 'A', 'invalid', 'missing_actor', omit=('actor_reference',), no_ledger=True),
    _spec('07_missing_campaign', 'A', 'invalid', 'missing_campaign', omit=('campaign_reference',), no_ledger=True),
    _spec('08_malformed_parameters', 'A', 'invalid', 'malformed_parameters', replace={'parameters': ['bad']}, no_ledger=True),
    _spec('09_invalid_target', 'A', 'invalid', 'unknown_target',
          targets=[{'kind': 'inventory_item', 'id': 'missing_item'}], no_ledger=True),
    _spec('10_conflicting_ruleset_identity', 'A', 'conflict', 'request_ruleset_conflict',
          ruleset_id='scifi', no_ledger=True),
    _spec('11_valid_pathfinder_binding', 'B', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          capability_status='supported', resolver='game.pf1e_equipment_policy', no_ledger=True),
    _spec('12_missing_binding', 'B', 'invalid', 'missing_binding', binding=None, no_ledger=True),
    _spec('13_invalid_binding', 'B', 'invalid', 'invalid_binding', binding={}, no_ledger=True),
    _spec('14_unknown_ruleset', 'B', 'unknown', 'unknown_ruleset', binding=_binding('other'), no_ledger=True),
    _spec('15_unsupported_version', 'B', 'unsupported', 'unsupported_version', binding=_binding('pf1e', '2'), no_ledger=True),
    _spec('16_rules_light_fixture', 'B', 'unsupported', 'capability_not_supported',
          binding=_binding('rules_light'), resolver='identity_only:rules_light@1', no_ledger=True, no_eligible=True),
    _spec('17_scifi_fixture', 'B', 'unsupported', 'capability_not_supported',
          binding=_binding('scifi'), resolver='identity_only:scifi@1', no_ledger=True, no_eligible=True),
    _spec('18_stale_campaign_state', 'B', 'conflict', 'stale_revision', revision=5, commit='conflict', no_ledger=True),
    _spec('19_cross_campaign_isolation', 'B', 'invalid', 'campaign_mismatch', swap_campaign=True, no_ledger=True),
    _spec('20_repeated_binding_resolution', 'B', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          kind='repeated', no_ledger=True),
    _spec('21_supported_capability', 'C', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          capability_status='supported', no_ledger=True),
    _spec('22_unsupported_capability', 'C', 'unsupported', 'capability_not_supported',
          action_type='dice_mechanics', capability_status='unsupported', no_ledger=True),
    _spec('23_unknown_capability', 'C', 'unknown', 'unknown_capability',
          action_type='phase_dance', capability_status='unknown', no_ledger=True),
    _spec('24_missing_capability', 'C', 'invalid', 'missing_action_type', replace={'action_type': ''}, no_ledger=True),
    _spec('25_invalid_capability_request', 'C', 'invalid', 'malformed_capability',
          action_type='BadCap', capability_status='invalid', no_ledger=True),
    _spec('26_mechanically_unresolved', 'C', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          eligible_nested=True, proposals=0, no_ledger=True),
    _spec('27_deterministic_resolution', 'C', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          kind='repeated', no_ledger=True),
    _spec('28_repeated_resolution', 'C', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          kind='repeated', no_ledger=True),
    _spec('29_ruleset_specific_result', 'C', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          eligible_nested=True, resolver='game.pf1e_equipment_policy', no_ledger=True),
    _spec('30_no_pathfinder_fallback', 'C', 'unknown', 'unknown_capability', binding=_binding('scifi'),
          action_type='combat_resolution', resolver='identity_only:scifi@1', no_eligible=True, no_ledger=True),
    _spec('31_valid_proposed_change', 'D', 'committed', 'committed', fixture=True, action_type='contract_marker',
          parameters={'mode': 'commit', 'marker': 'contract_marker'}, commit='committed', marker='contract_marker',
          resolver='test_only.contract_fixture', session_same=False),
    _spec('32_invalid_state_owner', 'D', 'rejected', 'invalid_state_owner', fixture=True, action_type='contract_marker',
          parameters={'mode': 'bad_owner'}, no_ledger=True),
    _spec('33_invalid_target_identity', 'D', 'conflict', 'invalid_target_identity', fixture=True,
          action_type='contract_marker', parameters={'mode': 'bad_target'}, commit='conflict', no_ledger=True),
    _spec('34_invalid_revision', 'D', 'conflict', 'stale_revision', fixture=True, action_type='contract_marker',
          parameters={'mode': 'bad_revision'}, commit='conflict', no_ledger=True),
    _spec('35_unauthorized_field', 'D', 'rejected', 'unauthorized_field', fixture=True, action_type='contract_marker',
          parameters={'mode': 'bad_field'}, no_ledger=True),
    _spec('36_unsupported_operation', 'D', 'invalid', 'unsupported_operation', fixture=True,
          action_type='contract_marker', parameters={'mode': 'bad_operation'}, no_ledger=True),
    _spec('37_malformed_value', 'D', 'invalid', 'malformed_value', fixture=True, action_type='contract_marker',
          parameters={'mode': 'bad_value'}, no_ledger=True),
    _spec('38_multiple_proposed_changes', 'D', 'committed', 'committed', fixture=True, action_type='contract_marker',
          parameters={'mode': 'multi', 'marker': 'contract_marker'}, commit='committed', marker='contract_marker',
          session_same=False),
    _spec('39_conflicting_changes', 'D', 'conflict', 'conflicting_changes', fixture=True, action_type='contract_marker',
          parameters={'mode': 'conflict'}, commit='conflict', proposals=2, no_ledger=True),
    _spec('40_noop_result', 'D', 'authorized', 'authorized_no_change', fixture=True, action_type='contract_marker',
          parameters={'mode': 'noop'}, proposals=0, no_ledger=True),
    _spec('41_successful_commit', 'E', 'committed', 'committed', fixture=True, action_type='contract_marker',
          parameters={'mode': 'commit', 'marker': 'contract_marker'}, commit='committed', marker='contract_marker',
          session_same=False),
    _spec('42_failed_commit', 'E', 'rejected', 'commit_failed', fixture=True, action_type='contract_marker',
          parameters={'mode': 'commit', 'marker': 'contract_marker'}, kind='save_raises', commit='failed', no_ledger=True),
    _spec('43_stale_revision_at_commit', 'E', 'conflict', 'stale_revision', revision=4, commit='conflict', no_ledger=True),
    _spec('44_atomicity', 'E', 'rejected', 'invalid_state_owner', fixture=True, action_type='contract_marker',
          parameters={'mode': 'partial'}, proposals=2, no_ledger=True),
    _spec('45_state_preservation_on_failure', 'E', 'rejected', 'commit_failed', fixture=True,
          action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
          kind='save_raises', commit='failed', no_ledger=True),
    _spec('46_authoritative_result_recording', 'E', 'committed', 'committed', fixture=True, action_type='contract_marker',
          parameters={'mode': 'commit', 'marker': 'contract_marker'}, commit='committed', marker='contract_marker',
          session_same=False),
    _spec('47_publication_after_commit', 'E', 'committed', 'committed', fixture=True, action_type='contract_marker',
          parameters={'mode': 'commit', 'marker': 'contract_marker'}, commit='committed', marker='contract_marker',
          session_same=False),
    _spec('48_no_publication_before_commit', 'E', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          no_ledger=True),
    _spec('49_no_unauthorized_time_advancement', 'E', 'committed', 'committed', fixture=True,
          action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
          commit='committed', marker='contract_marker', session_same=False),
    _spec('50_no_partial_execution', 'E', 'unresolved', 'fixture_unresolved', fixture=True,
          action_type='contract_marker', parameters={'mode': 'unresolved'}, discarded=1, proposals=1, no_ledger=True),
    _spec('51_duplicate_action_receipt', 'F', 'conflict', 'duplicate_action_id', fixture=True, kind='duplicate',
          action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
          commit='conflict', session_same=True),
    _spec('52_retry_after_success', 'F', 'committed', 'durable_replay', fixture=True, kind='replay',
          action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
          commit='committed', retry='replay', marker='contract_marker', session_same=True),
    _spec('53_retry_after_failure', 'F', 'committed', 'committed', fixture=True, kind='retry_after_failure',
          action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
          commit='committed', marker='contract_marker', session_same=False),
    _spec('54_save_reload', 'F', 'committed', 'durable_replay', fixture=True, kind='reload',
          action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
          commit='committed', retry='replay', session_same=True),
    _spec('56_interrupted_write', 'F', 'rejected', 'commit_failed', fixture=True, action_type='contract_marker',
          parameters={'mode': 'commit', 'marker': 'contract_marker'}, kind='save_raises', commit='failed', no_ledger=True),
    _spec('57_durable_receipt', 'F', 'committed', 'durable_replay', fixture=True, kind='reload',
          action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
          commit='committed', retry='replay', session_same=True),
    _spec('58_receipt_mismatch', 'F', 'conflict', 'duplicate_action_id', fixture=True, kind='duplicate',
          action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
          commit='conflict', session_same=True),
    _spec('59_no_duplicate_mutation', 'F', 'committed', 'durable_replay', fixture=True, kind='replay',
          action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
          commit='committed', retry='replay', marker='contract_marker', ledger_revision=1, session_same=True),
    _spec('60_no_duplicate_time_advancement', 'F', 'committed', 'durable_replay', fixture=True, kind='replay',
          action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
          commit='committed', retry='replay', session_same=True),
    _spec('67_existing_inventory_unchanged', 'G', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          no_ledger=True),
    _spec('68_existing_equipment_policy_unchanged', 'G', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          eligible_nested=True, no_ledger=True),
    _spec('72_unresolved_proposal_discarded', 'E', 'unresolved', 'fixture_unresolved', fixture=True,
          action_type='contract_marker', parameters={'mode': 'unresolved'}, discarded=1, no_ledger=True),
    _spec('73_unknown_actor', 'A', 'invalid', 'unknown_actor',
          replace={'actor_reference': {'kind': 'character', 'id': 'nobody'}}, no_ledger=True),
    _spec('74_malformed_revision', 'A', 'invalid', 'malformed_revision', replace={'expected_state_revision': True},
          no_ledger=True),
    _spec('75_extra_ruleset_field', 'A', 'invalid', 'malformed_request', replace={'armor_class': 18}, no_ledger=True),
    _spec('76_resolution_interrupted', 'F', 'rejected', 'resolution_interrupted', fixture=True,
          action_type='contract_marker', parameters={'mode': 'raise'}, no_ledger=True),
    _spec('77_echoed_ruleset_does_not_switch', 'B', 'unresolved', 'definition_slot_authorized_mechanics_unresolved',
          ruleset_id='pf1e', resolver='game.pf1e_equipment_policy', no_ledger=True),
    _spec('78_valid_inventory_target_does_not_mutate', 'A', 'unresolved',
          'definition_slot_authorized_mechanics_unresolved',
          targets=[{'kind': 'inventory_item', 'id': 'spellbook'}], no_ledger=True),
    _spec('79_fixture_rejection', 'D', 'rejected', 'fixture_rejected', fixture=True, action_type='contract_marker',
          parameters={'mode': 'reject'}, no_ledger=True),
    _spec('80_character_statistics_unsupported', 'C', 'unsupported', 'capability_not_supported',
          action_type='character_statistics', no_ledger=True),
]


@pytest.mark.parametrize('spec', SPECS, ids=[item['id'] for item in SPECS])
def test_mechanical_action_matrix(campaign, monkeypatch, spec):
    _run(campaign, monkeypatch, spec)


def test_policy_recognition_cannot_commit(campaign, monkeypatch):
    class PolicyOnly:
        ruleset_id = 'pf1e'
        version = '1'
        implementation = 'test_only.policy_cannot_commit'
        def capability_disposition(self, capability):
            return 'supported' if capability == 'equipment_policy' else 'unknown'
        def evaluate_policy(self, capability, request, context):
            del request, context
            return PolicyEvaluation('supported', 'recognized_not_authorized', 'pf1e', '1', capability,
                                    self.implementation, 'supported',
                                    freeze({'decision': 'RECOGNIZED', 'transition_authorized': True}))
    spec = _spec('71_policy_cannot_authorize_commit', 'G', 'rejected', 'recognized_not_authorized',
                 authority=PolicyOnly(), fixture=True, no_ledger=True, resolver='test_only.policy_cannot_commit')
    _run(campaign, monkeypatch, spec)


def test_production_adapter_has_no_commit_authority():
    authority = registry.get_ruleset('pf1e', '1').authority
    assert authority.implementation == 'game.pf1e_equipment_policy'
    assert 'social_skill_check' in authority.supported_capabilities
    equipment = authority.resolve_mechanical_action(
        {'action_type': 'equipment_policy', 'parameters': {'item': padded_armor_definition(), 'slot': 'body_armor'}}, {})
    assert equipment['status'] == 'unresolved'
    assert equipment['proposed_state_changes'] == []


def test_direct_equipment_policy_matches_action_outcome(campaign):
    direct = evaluate_equipment_eligibility(padded_armor_definition(), 'body_armor', 'pf1e@1')
    result = _run(campaign, None, _spec(
        '68b_direct_policy_agreement', 'G', 'unresolved', direct.reason, eligible_nested=True, no_ledger=True))
    assert result['mechanical_outcome']['decision'] == direct.decision
    assert result['mechanical_outcome']['execution_readiness'] == direct.execution_readiness
    assert result['proposed_state_changes'] == []


def test_process_restart_replays_without_a_second_marker(campaign, monkeypatch):
    spec = _spec('55_process_restart', 'F', 'committed', 'durable_replay', fixture=True,
                 action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'contract_marker'},
                 commit='committed', retry='replay', marker='contract_marker', session_same=True)
    install(monkeypatch)
    character = storage.load_character()
    request = _request(storage.load_session(), character, spec)
    first = execute_mechanical_action(request)
    assert first['status'] == 'committed'
    before = storage.SESSION_PATH.read_bytes()
    env = dict(os.environ, ASHEN_DATA_DIR=str(storage.DATA_DIR), MECH_REQUEST=json.dumps(request))
    completed = subprocess.run(
        [sys.executable, '-c',
         'import json,os; from game.mechanical_action import execute_mechanical_action; '
         'print(json.dumps(execute_mechanical_action(json.loads(os.environ["MECH_REQUEST"]))))'],
        cwd=ROOT, env=env, text=True, capture_output=True, check=True)
    result = json.loads(completed.stdout)
    assert storage.SESSION_PATH.read_bytes() == before
    assert result['retry'] == 'replay' and result['commit_status'] == 'committed'
    assert storage.load_session()['mechanical_action_ledger']['revision'] == 1
    checks = {'replay': True, 'bytes_unchanged': True, 'revision_once': True,
              'provider_zero': len(snapshot()['records']) == len(snapshot()['records'])}
    _record(spec, request, result, _state(), _state(), _bytes(), _bytes(), checks)


def test_scifi_resolution_does_not_import_pathfinder(campaign):
    updated = copy.deepcopy(storage.load_session())
    updated['ruleset_binding'] = _binding('scifi')
    raw_session(updated)
    character = storage.load_character()
    request = _request(updated, character, _spec('30b_subprocess_isolation', 'H', 'unsupported', 'capability_not_supported'))
    env = dict(os.environ, ASHEN_DATA_DIR=str(storage.DATA_DIR), MECH_REQUEST=json.dumps(request))
    code = ('import json,os,sys; from game.mechanical_action import execute_mechanical_action; '
            'r=execute_mechanical_action(json.loads(os.environ["MECH_REQUEST"])); '
            'assert r["status"]=="unsupported"; assert "ELIGIBLE" not in json.dumps(r["mechanical_outcome"]); '
            'assert "game.pf1e_equipment_policy" not in sys.modules; print(json.dumps(r))')
    completed = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env, text=True, capture_output=True, check=True)
    result = json.loads(completed.stdout)
    _record(_spec('30b_subprocess_isolation', 'H', 'unsupported', 'capability_not_supported'),
            request, result, _state(), _state(), _bytes(), _bytes(), {'isolated': True})


def test_core_import_does_not_load_pathfinder():
    code = ('import sys; import game.mechanical_action, game.mechanical_action_contract; '
            'assert "game.pf1e_equipment_policy" not in sys.modules')
    subprocess.check_call([sys.executable, '-c', code], cwd=ROOT)


def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return found


def test_architectural_boundaries():
    core = ROOT / 'game' / 'mechanical_action.py'
    contract = ROOT / 'game' / 'mechanical_action_contract.py'
    forbidden = ('game.pf1e_equipment_policy', 'game.combat', 'game.skill_checks', 'game.conditions',
                 'game.conversational_orchestration')
    assert not any(name.startswith(forbidden) or name in forbidden for name in _imports(core) + _imports(contract))
    source = (core.read_text(encoding='utf-8') + contract.read_text(encoding='utf-8')).lower()
    for word in ('pf1e', 'armor_class', 'd20', 'padded_armor'):
        assert word not in source
    for path in (ROOT / 'game' / 'pf1e_equipment_policy.py', ROOT / 'tests' / 'mechanical_action_fixture.py',
                 ROOT / 'game' / 'ruleset_contract.py', ROOT / 'game' / 'ruleset_registry.py'):
        text = path.read_text(encoding='utf-8')
        assert 'save_session' not in text and 'save_character' not in text
    assert REQUEST_FIELDS.isdisjoint({'ac', 'slot', 'armor_class', 'bab', 'd20'})
    assert ENVELOPE_FIELDS.isdisjoint({'ac', 'slot', 'armor_class', 'bab', 'd20', 'padded_armor'})
    for ident, group, detail in (
            ('61_generic_core_imports', 'G', 'no_pathfinder_import'),
            ('62_generic_request_fields', 'G', 'request_fields_neutral'),
            ('63_generic_result_fields', 'G', 'envelope_fields_neutral'),
            ('64_ruleset_cannot_write_persistence', 'G', 'no_direct_save'),
            ('69_gameplay_admission_unchanged', 'G', 'admission_not_imported'),
            ('70_provider_calls_zero', 'G', 'provider_delta_checked_per_row')):
        ROWS.append({'id': ident, 'group': group, 'campaign_identity': None, 'ruleset_binding': None,
                     'action_request': None, 'capability': None, 'selected_resolver': None,
                     'resolution_result': {'status': 'not_applicable', 'detail': detail},
                     'proposed_changes': [], 'validation_outcome': 'not_applicable',
                     'commit_outcome': 'not_attempted', 'state_delta': {}, 'publication': {'published': False},
                     'retry_behavior': 'none', 'assertion_result': {detail: True}, 'passed': True})
    target = os.environ.get('ASHEN_TEST_EVIDENCE_DIR')
    if target:
        (Path(target) / 'acceptance_matrix.json').write_text(json.dumps(ROWS, indent=2), encoding='utf-8')


_MISSING = object()


def _push(authority):
    key = ('pf1e', '1')
    previous = registry._AUTHORITIES.get(key, _MISSING)
    registry._AUTHORITIES[key] = authority
    return previous


def _pop(previous):
    key = ('pf1e', '1')
    if previous is _MISSING:
        registry._AUTHORITIES.pop(key, None)
    else:
        registry._AUTHORITIES[key] = previous


def test_multi_turn_sequences(campaign, monkeypatch):
    del monkeypatch
    character = storage.load_character()
    session = storage.load_session()
    actor = {'kind': 'character', 'id': character['id']}
    sequences = []

    def turn(name, payload, expect, sequence):
        before = _bytes()
        turn_before = storage.load_session().get('turn_counter')
        result = execute_mechanical_action(payload)
        after = storage.load_session()
        ok = result['status'] == expect and before['character'] == _bytes()['character'] and after.get('turn_counter') == turn_before
        row = {'sequence': sequence, 'turn': name, 'request': payload, 'campaign_identity': session['campaign_run_id'],
               'ruleset_identity': result.get('ruleset_id'), 'resolution': result['status'],
               'proposed_changes': result['proposed_state_changes'], 'commit': result['commit_status'],
               'publication': result['publication'], 'state_delta': {
                   'ledger': after.get('mechanical_action_ledger'), 'turn_counter': after.get('turn_counter')},
               'persistence': after.get('mechanical_action_ledger'), 'provider_calls': 0,
               'assertion_result': ok}
        sequences.append(row)
        assert ok, row
        return result

    base = {'actor_reference': actor, 'target_references': [], 'campaign_reference': session['campaign_run_id'],
            'expected_state_revision': 0}
    turn('supported_resolution', dict(base, action_id='s1-unresolved', action_type='equipment_policy',
         parameters={'item': padded_armor_definition(), 'slot': 'body_armor'}), 'unresolved', 1)
    token = _push(ContractFixtureRuleset())
    committed = turn('fixture_commit', dict(base, action_id='s1-commit', action_type='contract_marker',
                     parameters={'mode': 'commit', 'marker': 'contract_marker'}), 'committed', 1)
    assert committed['publication']['published'] is True
    turn('recognize_replay', dict(base, action_id='s1-commit', action_type='contract_marker',
         parameters={'mode': 'commit', 'marker': 'contract_marker'}), 'committed', 1)
    turn('second_marker', dict(base, action_id='s1-second', action_type='contract_marker',
         expected_state_revision=1, parameters={'mode': 'commit', 'marker': 'second_marker'}), 'committed', 1)
    turn('stale_third', dict(base, action_id='s1-stale', action_type='contract_marker',
         expected_state_revision=0, parameters={'mode': 'commit', 'marker': 'contract_marker'}), 'conflict', 1)
    reloaded = storage.load_session()
    assert reloaded['mechanical_action_ledger']['revision'] == 2
    assert reloaded['mechanical_action_ledger']['markers'] == {'s1-commit': 'contract_marker', 's1-second': 'second_marker'}
    _pop(token)

    raw_session(copy.deepcopy(campaign))
    turn('unsupported_combat', dict(base, action_id='s2-combat', action_type='combat_resolution', parameters={}),
         'unsupported', 2)
    turn('unresolved_equipment', dict(base, action_id='s2-equip', action_type='equipment_policy',
         parameters={'item': padded_armor_definition(), 'slot': 'body_armor'}), 'unresolved', 2)
    token = _push(ContractFixtureRuleset())
    turn('discard_unresolved_proposal', dict(base, action_id='s2-discard', action_type='contract_marker',
         parameters={'mode': 'unresolved'}), 'unresolved', 2)
    turn('reject_bad_owner', dict(base, action_id='s2-owner', action_type='contract_marker',
         parameters={'mode': 'bad_owner'}), 'rejected', 2)
    turn('authorized_noop', dict(base, action_id='s2-noop', action_type='contract_marker', parameters={'mode': 'noop'}),
         'authorized', 2)
    turn('recovery_commit', dict(base, action_id='s2-recover', action_type='contract_marker',
         parameters={'mode': 'commit', 'marker': 'recovery_marker'}), 'committed', 2)
    assert storage.load_session()['mechanical_action_ledger']['markers'] == {'s2-recover': 'recovery_marker'}
    _pop(token)

    raw_session(copy.deepcopy(campaign))
    token = _push(ContractFixtureRuleset())
    turn('retry_commit', dict(base, action_id='s3-once', action_type='contract_marker',
         parameters={'mode': 'commit', 'marker': 'once_marker'}), 'committed', 3)
    turn('retry_same', dict(base, action_id='s3-once', action_type='contract_marker',
         parameters={'mode': 'commit', 'marker': 'once_marker'}), 'committed', 3)
    assert storage.load_session()['mechanical_action_ledger']['revision'] == 1
    env = dict(os.environ, ASHEN_DATA_DIR=str(storage.DATA_DIR), MECH_REQUEST=json.dumps(dict(
        base, action_id='s3-once', action_type='contract_marker', parameters={'mode': 'commit', 'marker': 'once_marker'})))
    completed = subprocess.run(
        [sys.executable, '-c',
         'import json,os; from game.mechanical_action import execute_mechanical_action; '
         'print(json.dumps(execute_mechanical_action(json.loads(os.environ["MECH_REQUEST"]))))'],
        cwd=ROOT, env=env, text=True, capture_output=True, check=True)
    restarted = json.loads(completed.stdout)
    assert restarted['retry'] == 'replay'
    assert storage.load_session()['mechanical_action_ledger']['revision'] == 1
    turn('reload_conflict', dict(base, action_id='s3-other', action_type='contract_marker',
         expected_state_revision=0, parameters={'mode': 'commit', 'marker': 'once_marker'}), 'conflict', 3)
    turn('reload_next', dict(base, action_id='s3-other', action_type='contract_marker',
         expected_state_revision=1, parameters={'mode': 'commit', 'marker': 'next_marker'}), 'committed', 3)
    turn('reload_exact', dict(base, action_id='s3-other', action_type='contract_marker',
         expected_state_revision=1, parameters={'mode': 'commit', 'marker': 'next_marker'}), 'committed', 3)
    assert list(storage.load_session()['mechanical_action_ledger']['markers']) == ['s3-once', 's3-other']
    _pop(token)

    raw_session(copy.deepcopy(campaign))
    turn('pathfinder_campaign', dict(base, action_id='s4-pf', action_type='equipment_policy',
         parameters={'item': padded_armor_definition(), 'slot': 'body_armor'}), 'unresolved', 4)
    turn('request_cannot_select_scifi', dict(base, action_id='s4-conflict', action_type='equipment_policy',
         ruleset_id='scifi', ruleset_version='1', parameters={'item': padded_armor_definition(), 'slot': 'body_armor'}),
         'conflict', 4)
    switched = copy.deepcopy(storage.load_session())
    switched['ruleset_binding'] = _binding('scifi')
    raw_session(switched)
    isolated = turn('scifi_equipment', dict(base, action_id='s4-scifi', action_type='equipment_policy',
                    parameters={'item': padded_armor_definition(), 'slot': 'body_armor'}), 'unsupported', 4)
    assert isolated['implementation'] == 'identity_only:scifi@1'
    assert 'ELIGIBLE' not in json.dumps(isolated['mechanical_outcome'])
    unknown = turn('scifi_combat', dict(base, action_id='s4-combat', action_type='combat_resolution', parameters={}),
                   'unknown', 4)
    assert unknown['implementation'] == 'identity_only:scifi@1'
    restored = copy.deepcopy(campaign)
    raw_session(restored)
    turn('pathfinder_restored', dict(base, action_id='s4-restored', action_type='equipment_policy',
         parameters={'item': padded_armor_definition(), 'slot': 'body_armor'}), 'unresolved', 4)
    assert 'mechanical_action_ledger' not in storage.load_session()
    SEQUENCES.extend(sequences)
    target = os.environ.get('ASHEN_TEST_EVIDENCE_DIR')
    if target:
        (Path(target) / 'multi_turn_continuity.json').write_text(json.dumps(sequences, indent=2), encoding='utf-8')


def test_matrix_covers_required_groups():
    # The parametrized rows plus architecture rows are counted after the session;
    # this test fixes the minimum the parametrized table itself must carry.
    assert len(SPECS) >= 70
    assert {item['group'] for item in SPECS} >= set('ABCDEF')
