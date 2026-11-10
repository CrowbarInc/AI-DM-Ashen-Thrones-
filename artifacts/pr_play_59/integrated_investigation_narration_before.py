"""Quarantined wording of completed investigations, never a state/publication owner.

Reuses PR49 authority and PR55 validation. Coverage is a conservative heuristic,
not a semantic proof; every raw candidate remains available for external review.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import time

from game import anchored_investigation_narration as anchored
from game import consequential_narration_validation as semantic
from game import quarantined_investigation_narration as quarantine
from game.mandatory_outcome_coverage import mandatory_coverage
from game.immutable_valid_response import validate_generated_response
from game.resolution_contract import contract_mapping_from_resolution

SYSTEM_PROMPT = (
    "Narrate this already completed player action in 35-65 words of natural tabletop-GM prose. "
    "The engine alone determined the outcome. Communicate every must_communicate fact naturally; "
    "preserve its full meaning, including uncertainty. No rigid template or fact IDs in prose. "
    "For a repeated examination, acknowledge what was already known and that nothing new emerged. "
    "Respond directly to the action, maintain continuity, and use concise, engaging description. "
    "May_reference facts are optional. Harmless incidental sensory texture is allowed. "
    "Do not resolve another action, invent discoveries or hints, award items, change success/failure, "
    "reveal restricted information, invent NPC motives, objectives, destinations or persistent effects. "
    "Output only complete prose sentences. The engine will not append the outcome to this candidate."
)
CONSTRAINTS = (
    "Only communicate completed engine outcomes; never establish additional facts or effects.",
    "Preserve failure, uncertainty and previously-known status; no misleading hints.",
    "No inventory, condition, NPC, quest, travel or other persistent changes are authorized.",
)


def outcome_contract(hook_input: dict):
    """Ephemeral projection of existing authority; no campaign objects or candidate input."""
    contract = anchored.authorize_anchored_investigation(
        hook_input['resolution'], hook_input['narration_payload'])
    facts = []
    for anchor in contract.anchors:
        # Ordinary scene observations are optional. Repeated knowledge is kept
        # mandatory so the candidate cannot replace the result with atmosphere.
        if anchor.source == 'public_observation':
            continue
        facts.append({'id': f'outcome:{anchor.order}', 'source': anchor.source,
                      'status': anchor.status, 'text': anchor.text})
    v = contract.outcome
    request = {
        'player_action': str(hook_input.get('player_text') or '')[:1000],
        'resolved_outcome': {'status': v.status, 'success': v.success},
        'must_communicate': facts,
        'may_reference': {'visible_scene': list(v.observations),
                          'continuity': list(v.known)},
        'authorized_consequences': [],
        'must_not_establish': list(CONSTRAINTS),
    }
    # Refuse oversized input rather than silently dropping required information.
    if len(json.dumps(request).encode('utf-8')) > 10000:
        raise ValueError('integrated_projection_too_large')
    return contract, request


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
    fault = quarantine._fault()
    live = generator is None and quarantine.live_provider_enabled() and not fault
    if generator is None:
        if live:
            generator = _LiveIntegrated(request['player_action'])
        else:
            values = {'empty': '', 'malformed': {}, 'unsafe': 'You find a silver key beneath the board.'}
            generator = quarantine._Replay(values.get(quarantine._sample(),
                'You examine the evidence carefully.'), fault)
    result = {'mode': 'quarantined_integrated', 'authorized_outcome_contract': request,
              'anchors': [asdict(a) for a in contract.anchors],
              'assembled': anchored.fallback(contract), 'raw_provider_text': None,
              'used_fallback': True, 'provider_requests': 0, 'generator_calls': 0,
              'validation_ms': None, 'validation': {}, 'review_required': True,
              'live_provider': {'enabled': False}, 'promoted': False}
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
