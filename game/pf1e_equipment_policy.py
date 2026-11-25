"""Bounded PF1e-inspired definition eligibility; never character/equipment state.

Callers must supply an explicit ruleset identity: there is no runtime loader or
implicit default. A catalog reference is rules data, not evidence of possession.
No result from this foundation authorizes an equipment mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from game.ruleset_contract import PolicyEvaluation, freeze

RULESET_ID = 'pf1e@1'
POLICY_ID = 'pf1e.equipment.light_armor'
POLICY_VERSION = 1
CATEGORY = 'light_armor'
SLOT = 'body_armor'
PADDED_ARMOR_ID = 'pf1e.core.padded_armor'
SOURCE = 'https://legacy.aonprd.com/coreRulebook/equipment.html'


class MechanicalConsequence(str, Enum):
    NONE_ESTABLISHED = 'NONE_ESTABLISHED'
    KNOWN = 'KNOWN'
    UNRESOLVED = 'UNRESOLVED'
    UNSUPPORTED = 'UNSUPPORTED'


@dataclass(frozen=True)
class EquipmentEligibility:
    decision: str
    reason: str
    ruleset: str | None
    category: str | None
    slot: str | None
    compatibility: str = 'UNKNOWN'
    mechanical_consequence: MechanicalConsequence = MechanicalConsequence.UNSUPPORTED
    mechanical_reason: str = 'consequence_policy_unavailable'
    missing_contribution_data: tuple[str, ...] = ()
    execution_readiness: str = 'BLOCKED_POLICY'
    policy_id: str = POLICY_ID
    policy_version: int = POLICY_VERSION
    definition_id: str | None = None
    ruleset_applicable: bool = False
    category_recognized: bool = False
    slot_recognized: bool = False
    item_authorized: bool = False
    mechanically_complete: bool = False
    transition_authorized: bool = False


def padded_armor_definition() -> dict[str, Any]:
    """Return detached rules data, without inventory identity or equipped state.

    Numeric armor effects are intentionally not supplied as executable modifiers.
    Even padded armor has AC, Dex-cap and spell-failure implications. Imported
    totals cannot be decomposed from this definition.
    """
    return {
        'name': 'Padded armor',
        'equipment_policy': {'ruleset': RULESET_ID, 'policy_version': POLICY_VERSION,
                             'definition_id': PADDED_ARMOR_ID, 'category': CATEGORY},
    }


def evaluate_equipment_eligibility(item: Any, slot: Any, ruleset: Any, *,
                                   policy_version: Any = POLICY_VERSION) -> EquipmentEligibility:
    """Validate an explicit catalog binding without reading or changing state.

    ELIGIBLE means definition/slot eligibility only. Execution remains blocked
    by unresolved contribution attribution and the absent mutation lifecycle.
    main_hand is an exclusion-only identifier, not a supported wielding slot.
    shield/simple_melee_weapon are recognized for body-armor exclusion only.
    Unrecognized categories are UNKNOWN; recognized unimplemented armor
    categories are UNSUPPORTED. Malformed/conflicting metadata fails closed.
    """
    context: dict[str, Any] = {
        'ruleset': ruleset if isinstance(ruleset, str) else None,
        'slot': slot if isinstance(slot, str) else None, 'category': None,
    }

    def result(decision: str, reason: str, **fields: Any) -> EquipmentEligibility:
        return EquipmentEligibility(decision, reason, **(context | fields))

    if ruleset is None or ruleset == '':
        return result('UNKNOWN', 'missing_ruleset')
    if not isinstance(ruleset, str):
        return result('UNKNOWN', 'malformed_ruleset')
    if ruleset != RULESET_ID:
        return result('UNSUPPORTED', 'unsupported_ruleset')
    context['ruleset_applicable'] = True
    if type(policy_version) is not int:
        return result('UNKNOWN', 'malformed_policy_version')
    if policy_version != POLICY_VERSION:
        return result('UNSUPPORTED', 'policy_version_mismatch')
    if slot is None or slot == '':
        return result('UNKNOWN', 'missing_slot')
    if not isinstance(slot, str):
        return result('UNKNOWN', 'malformed_slot')
    if slot not in (SLOT, 'main_hand'):
        return result('UNSUPPORTED', 'unsupported_slot', compatibility='UNSUPPORTED')
    context['slot_recognized'] = True
    if item is None:
        return result('UNKNOWN', 'missing_item')
    if not isinstance(item, dict):
        return result('UNKNOWN', 'malformed_item')
    metadata = item.get('equipment_policy')
    if metadata is None:
        return result('UNKNOWN', 'missing_equipment_metadata')
    if not isinstance(metadata, dict):
        return result('UNKNOWN', 'malformed_equipment_metadata')
    allowed = {'ruleset', 'policy_version', 'definition_id', 'category'}
    if set(metadata) - allowed:
        return result('UNKNOWN', 'unrecognized_equipment_metadata')
    category = metadata.get('category')
    if category is None or category == '':
        return result('UNKNOWN', 'missing_category')
    if not isinstance(category, str):
        return result('UNKNOWN', 'malformed_category')
    context['category'] = category
    if category not in (CATEGORY, 'shield', 'simple_melee_weapon', 'medium_armor', 'heavy_armor'):
        return result('UNKNOWN', 'unknown_category')
    context['category_recognized'] = True
    if category in ('medium_armor', 'heavy_armor'):
        return result('UNSUPPORTED', 'unsupported_category', compatibility='UNSUPPORTED')
    if any(metadata.get(k) is None for k in allowed):
        return result('UNKNOWN', 'incomplete_equipment_metadata')
    if not isinstance(metadata['ruleset'], str) or type(metadata['policy_version']) is not int:
        return result('UNKNOWN', 'malformed_item_policy_identity')
    if metadata['ruleset'] != RULESET_ID:
        return result('UNSUPPORTED', 'item_ruleset_mismatch')
    if metadata['policy_version'] != POLICY_VERSION:
        return result('UNSUPPORTED', 'item_policy_version_mismatch')
    definition_id = metadata['definition_id']
    if not isinstance(definition_id, str) or not definition_id:
        return result('UNKNOWN', 'malformed_definition_id')
    context['definition_id'] = definition_id
    # A reference to our known definition may not contradict its category.
    if definition_id == PADDED_ARMOR_ID and category != CATEGORY:
        return result('UNKNOWN', 'conflicting_definition_category')
    if definition_id == PADDED_ARMOR_ID:
        context.update(item_authorized=True,
                       mechanical_consequence=MechanicalConsequence.UNRESOLVED,
                       mechanical_reason='imported_contribution_attribution_missing',
                       missing_contribution_data=('aggregate_contribution_attribution',
                                                  'character_equipment_effect_context'))
    if slot == 'main_hand' or category in ('shield', 'simple_melee_weapon'):
        return result('INELIGIBLE', 'category_slot_incompatible', compatibility='INCOMPATIBLE')
    context['compatibility'] = 'COMPATIBLE'
    if definition_id != PADDED_ARMOR_ID:
        return result('UNSUPPORTED', 'unsupported_item_definition')
    return result('ELIGIBLE', 'definition_slot_authorized_mechanics_unresolved',
                  item_authorized=True, mechanical_consequence=MechanicalConsequence.UNRESOLVED,
                  execution_readiness='BLOCKED_MECHANICAL_RECONCILIATION')


# Adapter for the generic ruleset boundary. Callers that already hold this
# authority have selected pf1e version 1; the request cannot retarget it.
_SUPPORTED_CAPABILITIES = frozenset({'equipment_policy', 'social_skill_check'})
_RECOGNIZED_UNSUPPORTED = frozenset({'character_statistics', 'combat_resolution', 'dice_mechanics'})


def _eligibility_status(result: EquipmentEligibility) -> str:
    if result.reason.startswith('malformed_'):
        return 'invalid'
    if result.mechanical_consequence is MechanicalConsequence.UNRESOLVED:
        return 'mechanically_unresolved'
    if result.decision == 'INELIGIBLE':
        return 'supported'
    if result.decision == 'UNSUPPORTED':
        return 'unsupported'
    if result.decision == 'UNKNOWN':
        return 'unknown'
    return 'mechanically_unresolved'


def _eligibility_payload(result: EquipmentEligibility) -> dict[str, Any]:
    return {
        'decision': result.decision,
        'reason': result.reason,
        'ruleset': result.ruleset,
        'category': result.category,
        'slot': result.slot,
        'compatibility': result.compatibility,
        'mechanical_consequence': result.mechanical_consequence.value,
        'mechanical_reason': result.mechanical_reason,
        'missing_contribution_data': list(result.missing_contribution_data),
        'execution_readiness': result.execution_readiness,
        'policy_id': result.policy_id,
        'policy_version': result.policy_version,
        'definition_id': result.definition_id,
        'ruleset_applicable': result.ruleset_applicable,
        'category_recognized': result.category_recognized,
        'slot_recognized': result.slot_recognized,
        'item_authorized': result.item_authorized,
        'mechanically_complete': result.mechanically_complete,
        'transition_authorized': result.transition_authorized,
    }


class Pf1eRulesetAuthority:
    """pf1e version 1 authority. Equipment policy and one social skill check are delegated."""

    ruleset_id = 'pf1e'
    version = '1'
    implementation = 'game.pf1e_equipment_policy'
    canonical = RULESET_ID
    mechanics_implemented = True
    supported_capabilities = _SUPPORTED_CAPABILITIES
    recognized_unsupported = _RECOGNIZED_UNSUPPORTED

    def supports(self, capability: str) -> bool:
        return isinstance(capability, str) and capability in self.supported_capabilities

    def capability_disposition(self, capability: str) -> str:
        if capability in self.supported_capabilities:
            return 'supported'
        if capability in self.recognized_unsupported:
            return 'unsupported'
        return 'unknown'

    def resolve_mechanical_action(self, request, context):
        """Resolve a declared action. Equipment policy still proposes nothing."""
        capability = request.get('action_type') if isinstance(request, dict) else None
        if capability == 'social_skill_check':
            from game.pf1e_social_check import resolve_social_skill_check
            return resolve_social_skill_check(request, context if isinstance(context, dict) else {})
        disposition = self.capability_disposition(capability if isinstance(capability, str) else '')
        if disposition != 'supported':
            reason = {'unsupported': 'capability_not_supported', 'unknown': 'unknown_capability',
                      'invalid': 'malformed_capability'}.get(disposition, 'unknown_capability')
            status = disposition if disposition in ('unsupported', 'unknown', 'invalid') else 'unknown'
            return {'status': status, 'mechanical_outcome': {'delegated': False},
                    'proposed_state_changes': [], 'required_preconditions': [], 'explanation': reason}
        parameters = request.get('parameters') if isinstance(request, dict) and isinstance(request.get('parameters'), dict) else {}
        evaluation = self.evaluate_policy(capability, parameters, context if isinstance(context, dict) else {})
        from game.ruleset_contract import to_plain
        payload = to_plain(evaluation.ruleset_result)
        if not isinstance(payload, dict):
            payload = {}
        if evaluation.status == 'mechanically_unresolved':
            status = 'unresolved'
        elif evaluation.status == 'supported':
            status = 'rejected'
        elif evaluation.status in ('rejected', 'unresolved', 'unsupported', 'invalid', 'unknown'):
            status = evaluation.status
        else:
            status = 'invalid'
        preconditions = payload.get('missing_contribution_data')
        if not isinstance(preconditions, list):
            preconditions = []
        return {'status': status, 'mechanical_outcome': payload, 'proposed_state_changes': [],
                'required_preconditions': [item for item in preconditions if type(item) is str],
                'explanation': evaluation.reason}

    def evaluate_policy(self, capability, request, context) -> PolicyEvaluation:
        del context
        if capability == 'social_skill_check':
            return PolicyEvaluation(
                'mechanically_unresolved', 'social_check_requires_action_resolution',
                self.ruleset_id, self.version, capability, self.implementation, 'supported',
                freeze({'delegated': False, 'executed': False}))
        if capability in self.recognized_unsupported:
            return PolicyEvaluation(
                'unsupported', 'capability_not_delegated', self.ruleset_id, self.version,
                capability, self.implementation, 'unsupported',
                freeze({'delegated': False, 'legacy_pathway': 'not_on_this_boundary'}))
        if capability not in self.supported_capabilities:
            return PolicyEvaluation(
                'unknown', 'unknown_capability', self.ruleset_id, self.version,
                capability, self.implementation, 'unknown', freeze({'delegated': False}))
        item = request['item'] if 'item' in request else None
        slot = request['slot'] if 'slot' in request else None
        policy_version = request['policy_version'] if 'policy_version' in request else POLICY_VERSION
        eligibility = evaluate_equipment_eligibility(
            item, slot, RULESET_ID, policy_version=policy_version)
        return PolicyEvaluation(
            _eligibility_status(eligibility), eligibility.reason, self.ruleset_id, self.version,
            capability, self.implementation, 'supported', freeze(_eligibility_payload(eligibility)))


PF1E_RULESET_AUTHORITY = Pf1eRulesetAuthority()
