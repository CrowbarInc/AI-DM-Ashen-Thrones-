"""Quarantined wording of completed investigations, never a state/publication owner.

Reuses PR49 authority and PR55 validation. Coverage is a conservative heuristic,
not a semantic proof; every raw candidate remains available for external review.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import os
import time

from game import anchored_investigation_narration as anchored
from game import consequential_narration_validation as semantic
from game import quarantined_investigation_narration as quarantine
from game.mandatory_outcome_coverage import mandatory_coverage
from game.immutable_valid_response import validate_generated_response
from game.resolution_contract import contract_mapping_from_resolution

SYSTEM_PROMPT = (
    "Narrate this already completed player action in natural tabletop-GM prose. "
    "Use one or two concise sentences for routine observations and repeats; a discovery may need more. "
    "The engine alone determined the outcome. Communicate every must_communicate fact naturally; "
    "preserve its full meaning, including uncertainty. No rigid template or fact IDs in prose. "
    "For a repeated examination, acknowledge the repeat and that nothing new emerged; "
    "do not present prior information as a new discovery. "
    "Respond directly to the action, maintain continuity, and use concise, engaging description. "
    "May_reference facts are optional; omit unrelated scene details and prior information. "
    "For no-new-information outcomes, explicitly say no new clue was established. "
    "Describe only supplied observations; do not embellish object condition or environmental state. "
    "Do not resolve another action, invent discoveries or hints, award additional items, change success/failure, "
    "reveal restricted information, invent NPC motives, objectives, destinations or persistent effects. "
    "Output only complete prose sentences. The engine will not append the outcome to this candidate."
)
CONSTRAINTS = (
    "Only communicate completed engine outcomes; never establish additional facts or effects.",
    "Preserve failure, uncertainty and previously-known status; no misleading hints.",
    "Only explicitly supplied inventory deltas are authorized; no additional persistent changes.",
)


def outcome_contract(hook_input: dict):
    """Ephemeral projection of existing authority; no campaign objects or candidate input."""
    contract = anchored.authorize_anchored_investigation(
        hook_input['resolution'], hook_input['narration_payload'], inventory=True)
    facts = []
    for anchor in contract.anchors:
        # Current resolver disclosures remain mandatory even when already in
        # post-resolution state. Accumulated knowledge is authorization, not a
        # requirement to repeat it. Keep all anchors for safety validation.
        if anchor.source in {'public_observation', 'player_knowledge'}:
            continue
        facts.append({'id': f'outcome:{anchor.order}', 'source': anchor.source,
                      'status': anchor.status, 'text': anchor.text})
    v = contract.outcome
    if v.status in {'observed', 'failed'} and not any(f['source'] == 'engine_status' for f in facts):
        facts.insert(0, {'id': 'outcome:status', 'source': 'engine_status',
                         'status': v.status, 'text': 'No new clue is established by this examination.'})
    effects = json.loads(v.inventory_effects_json)
    if effects:
        facts.append({'id': 'outcome:inventory', 'source': 'inventory_effect',
                      'status': 'resolved', 'text': v.consequences})
    request = {
        'player_action': str(hook_input.get('player_text') or '')[:1000],
        'resolved_outcome': {'status': v.status, 'success': v.success},
        'must_communicate': facts,
        'may_reference': {'visible_scene': list(v.observations),
                          'continuity': list(v.known)},
        'authorized_consequences': effects if effects else [],
        'must_not_establish': list(CONSTRAINTS),
    }
    # Refuse oversized input rather than silently dropping required information.
    if len(json.dumps(request).encode('utf-8')) > 10000:
        raise ValueError('integrated_projection_too_large')
    return contract, request


def action_fallback(contract, hook_input: dict) -> str:
    """Existing integrated fallback, ordered by action then mandatory authority.

    Public scene catalogues are optional context, not the action's outcome.
    Current resolver disclosures remain verbatim; prior knowledge is optional.
    """
    view = contract.outcome
    label = hook_input.get('target_label')
    target = 'the ' + label if isinstance(label, str) and label else 'what is visible'
    opening = {
        'discovered': f'You examine {target}.',
        'known': f'You examine {target} again; nothing new is established.',
        'failed': f'You examine {target}, but no new clue is established.',
        'observed': f'You examine {target}; no new clue is established.',
    }[view.status]
    facts = [a.text for a in contract.anchors
             if a.source not in {'engine_status', 'public_observation', 'player_knowledge'}]
    return ' '.join(filter(None, [opening, *facts, view.consequences]))


def validate_integrated(contract, request, raw):
    if type(raw) is not str or not raw.strip() or len(raw.encode('utf-8')) > 3000:
        raise ValueError('integrated_response_shape_or_length')
    if any(ord(c) < 32 and c not in '\n\t\r' for c in raw) or raw.rstrip()[-1] not in '.!?\u201d"':
        raise ValueError('integrated_response_incomplete_or_control_character')
    r = anchored._resolution(contract)
    audit = validate_generated_response(raw, resolution=r, contract=contract_mapping_from_resolution(r))
    decision = semantic.validate_consequential_narration(raw, semantic.authority_from_anchored(contract))
    audit = semantic.apply_consequential_gate(audit, decision)
    coverage = mandatory_coverage(raw, request)
    final = decision['decision']
    if final == 'PASS' and not audit.get('hard_valid'):
        final = 'FAIL'
    if final == 'PASS' and coverage['decision'] != 'PASS':
        final = 'REVIEW_REQUIRED'
    return {'decision': final, 'semantic': decision, 'legacy': audit, 'coverage': coverage}


class _LiveIntegrated(quarantine._LivePrelude):
    system_prompt = SYSTEM_PROMPT
    limits = (8, 700, 12000)

    def user_payload(self):
        return self.request

    def generate(self, request):
        from game.provider_budget import accounting_active
        if not accounting_active():
            self.diagnostic = 'integrated_requires_usage_accounting'
            raise RuntimeError(self.diagnostic)
        return super().generate(request)


def run_integrated_hook(hook_input: dict, *, generator=None) -> dict:
    start = time.perf_counter()
    contract, request = outcome_contract(hook_input)
    context_build_ms = quarantine._elapsed(start)
    fault = quarantine._fault()
    live = generator is None and quarantine.live_provider_enabled() and not fault
    if generator is None:
        if live:
            generator = _LiveIntegrated(request['player_action'])
        else:
            values = {'empty': '', 'malformed': {}, 'unsafe': 'You find a silver key beneath the board.'}
            generator = quarantine._Replay(values.get(quarantine._sample(),
                'You examine the evidence carefully.'), fault)
    assembly_start = time.perf_counter()
    fallback_text = (action_fallback(contract, hook_input)
                     if os.environ.get(quarantine.PUBLICATION_ENV, '').strip() == '1'
                     else anchored.fallback(contract))
    assembly_ms = quarantine._elapsed(assembly_start)
    result = {'mode': 'quarantined_integrated', 'authorized_outcome_contract': request,
              'anchors': [asdict(a) for a in contract.anchors],
              'assembled': fallback_text, 'raw_provider_text': None,
              'used_fallback': True, 'provider_requests': 0, 'generator_calls': 0,
              'validation_ms': None, 'validation': {}, 'review_required': True,
              'live_provider': {'enabled': False}, 'promoted': False}
    result['context_build_ms'] = context_build_ms
    result['assembly_ms'] = assembly_ms
    # Separate opt-in preserves live repeat exercise and saved-text regression.
    # Fault injection must still reach the failing generator/validation path.
    if (live and os.environ.get('ASHEN_INTEGRATED_REPEAT_FAST_PATH', '').strip() == '1'
            and contract.outcome.status == 'known' and not contract.outcome.revealed
            and not json.loads(contract.outcome.inventory_effects_json)):
        result.update(provider_skip_reason='resolved_repeat_without_new_information',
                      deterministic_fast_path=True, diagnostic='deterministic_fast_path',
                      review_required=False, total_integrated_ms=quarantine._elapsed(start))
        return result
    try:
        raw = generator.generate(json.loads(json.dumps(request)))
        result['raw_provider_text'] = raw if isinstance(raw, str) else None
        validation_start = time.perf_counter()
        try:
            audit = validate_integrated(contract, request, raw)
        finally:
            result['validation_ms'] = quarantine._elapsed(validation_start)
        result['validation'] = audit
        result['diagnostic'] = audit['decision']
        if audit['decision'] == 'PASS':
            result.update(assembled=raw, used_fallback=False)
    except Exception as exc:
        result['diagnostic'] = 'provider_timeout' if isinstance(exc, TimeoutError) else 'VALIDATION_ERROR'
        result['error_type'] = type(exc).__name__
    finally:
        result['generator_calls'] = getattr(generator, 'calls', 0)
        if isinstance(generator, _LiveIntegrated):
            result['raw_provider_text'] = generator.raw_text
            result['provider_requests'] = int(generator.sent)
            result['live_provider'] = quarantine._live_metadata(generator)
        result['total_integrated_ms'] = quarantine._elapsed(start)
    return result
