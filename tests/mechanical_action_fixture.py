"""Test-only mechanical resolver.

This is not registered, not a playable ruleset, and not Pathfinder equipment,
combat, or character mechanics. Tests install it in place of the selected
authority object. Production discovery never returns it.
"""
from __future__ import annotations

from game.ruleset_contract import PolicyEvaluation, freeze


def _change(campaign_id, revision, marker):
    return {
        'state_owner': 'session_mechanical_ledger',
        'target_id': campaign_id,
        'expected_revision': revision,
        'operation': 'record_marker',
        'field': 'marker',
        'value': marker,
    }


class ContractFixtureRuleset:
    """Stands in for a campaign-selected authority during contract tests only."""

    ruleset_id = 'pf1e'
    version = '1'
    implementation = 'test_only.contract_fixture'
    supported_capabilities = frozenset({'contract_marker'})
    recognized_unsupported = frozenset({'character_statistics', 'combat_resolution', 'dice_mechanics'})
    mechanics_implemented = False

    def supports(self, capability: str) -> bool:
        return capability in self.supported_capabilities

    def capability_disposition(self, capability: str) -> str:
        if capability in self.supported_capabilities:
            return 'supported'
        if capability in self.recognized_unsupported:
            return 'unsupported'
        return 'unknown'

    def evaluate_policy(self, capability, request, context) -> PolicyEvaluation:
        del request, context
        return PolicyEvaluation(
            'unsupported', 'fixture_has_no_policy', self.ruleset_id, self.version, capability,
            self.implementation, 'unsupported', freeze({'delegated': False, 'gameplay': False}))

    def resolve_mechanical_action(self, request, context) -> dict:
        capability = request.get('action_type')
        parameters = request.get('parameters') if isinstance(request.get('parameters'), dict) else {}
        mode = parameters.get('mode', 'commit')
        revision = context.get('ledger_revision') if type(context.get('ledger_revision')) is int else 0
        campaign_id = context.get('campaign_id')
        marker = parameters.get('marker') if isinstance(parameters.get('marker'), str) else 'contract_marker'
        base = {
            'capability': capability,
            'mechanical_outcome': {'demonstration': 'contract_fixture', 'gameplay': False, 'mode': mode},
            'proposed_state_changes': [],
            'required_preconditions': [],
            'explanation': 'contract_fixture_resolution',
        }
        if capability != 'contract_marker':
            return dict(base, status='unsupported', explanation='fixture_capability_not_under_test')
        if mode == 'raise':
            raise RuntimeError('interrupted_resolution')
        if mode == 'reject':
            return dict(base, status='rejected', explanation='fixture_rejected')
        if mode == 'unresolved':
            return dict(base, status='unresolved', explanation='fixture_unresolved',
                        proposed_state_changes=[_change(campaign_id, revision, 'should_not_apply')])
        if mode == 'noop':
            return dict(base, status='authorized', explanation='authorized_no_change')
        if mode == 'bad_owner':
            change = _change(campaign_id, revision, marker)
            change['state_owner'] = 'character'
            return dict(base, status='authorized', proposed_state_changes=[change])
        if mode == 'bad_target':
            change = _change('other_campaign', revision, marker)
            return dict(base, status='authorized', proposed_state_changes=[change])
        if mode == 'bad_revision':
            return dict(base, status='authorized', proposed_state_changes=[_change(campaign_id, revision + 9, marker)])
        if mode == 'bad_field':
            change = _change(campaign_id, revision, marker)
            change['field'] = 'armor_class'
            return dict(base, status='authorized', proposed_state_changes=[change])
        if mode == 'bad_operation':
            change = _change(campaign_id, revision, marker)
            change['operation'] = 'execute'
            return dict(base, status='authorized', proposed_state_changes=[change])
        if mode == 'bad_value':
            return dict(base, status='authorized', proposed_state_changes=[_change(campaign_id, revision, 'Not A Marker')])
        if mode == 'conflict':
            return dict(base, status='authorized', proposed_state_changes=[
                _change(campaign_id, revision, 'alpha_marker'), _change(campaign_id, revision, 'beta_marker')])
        if mode == 'multi':
            return dict(base, status='authorized', proposed_state_changes=[
                _change(campaign_id, revision, marker), _change(campaign_id, revision, marker)])
        if mode == 'partial':
            bad = _change(campaign_id, revision, marker)
            bad['state_owner'] = 'world_state'
            return dict(base, status='authorized', proposed_state_changes=[_change(campaign_id, revision, marker), bad])
        return dict(base, status='authorized', proposed_state_changes=[_change(campaign_id, revision, marker)])
