"""Quarantined wording of completed investigations, never a state/publication owner.

Reuses PR49 authority and PR55 validation. Coverage is a conservative heuristic,
not a semantic proof; every raw candidate remains available for external review.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import os
import re
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

DISCLOSURE_ENV = 'ASHEN_EXPERIMENTAL_AUTHORITATIVE_DISCLOSURE'
PRESENTATION_PROMPT = (
    "Write one concise optional introductory sentence for this completed examination. "
    "Use only the supplied public scene and player action. Describe no additional object condition. "
    "The engine appends engine_disclosure verbatim immediately after your sentence. "
    "Do not repeat, paraphrase, contradict or qualify that disclosure. "
    "Do not narrate discoveries, outcomes, possessions, NPC actions, movement or persistent effects. "
    "Do not invent facts, hints or hidden information. Output only complete prose sentences."
    " The must_communicate list belongs exclusively to the engine; it is not your writing task. "
    "Write only the lead-in. You may repeat an exact visible_scene observation, or frame the player's "
    "attention naturally: You take a moment to examine [target]; You pause to inspect [target]; "
    "You turn your attention to [target]; You look more closely at [target]; "
    "You give [target] your attention. End with a period. "
    "Use the exact target from player_action. No new adjectives, metaphors or subordinate clauses."
)


def authoritative_disclosure_enabled():
    # Publication still requires the existing quarantine + integrated + session gates.
    return os.environ.get(DISCLOSURE_ENV, '').strip() == '1'


def trusted_disclosure(request):
    """Only the engine-built current-action projection enters this renderer."""
    return ' '.join(dict.fromkeys(f['text'] for f in request['must_communicate']))


def presentation_within_boundary(contract, request, raw):
    """Bounded experimental surface, additional to all existing safety gates.

    The general validators are heuristic and cannot prove arbitrary declarative
    prose safe. Admit only exact public/prior propositions and an examination
    introduction targeting the current player action. Unknown clauses are omitted
    through fallback, not repaired or inferred. No hidden content is needed here.
    """
    literals = {s.strip().casefold().rstrip('.!?') for s in (
        *contract.outcome.observations, *contract.outcome.known,
        *(f['text'] for f in request['must_communicate']))}
    action = re.fullmatch(r'(?:I|You)\s+(?:examine|inspect|study)\s+(.+?)[.!?]?',
                          request['player_action'].strip(), re.I)
    target = action.group(1).rstrip('.!?').strip() if action else None
    if target:
        target = re.sub(r'\s+again$', '', target, flags=re.I)
    intro = (rf'you (?:examine|inspect|study|focus on) {re.escape(target)}'
             rf'(?: carefully| again)?' if target else r'(?!)')
    # Finite, nonconsequential attention frames. The target is literal and the
    # whole sentence must match; suffix claims cannot ride an allowed opening.
    framing = (rf'you (?:(?:take a moment to|pause to) (?:examine|inspect|study) {re.escape(target)}'
               rf'|turn your attention to {re.escape(target)}'
               rf'|look more closely at {re.escape(target)}'
               rf'|give {re.escape(target)} your attention)' if target else r'(?!)')
    for sentence in re.split(r'(?<=[.!?])\s+', raw.strip()):
        normal = sentence.casefold().rstrip('.!?').strip()
        if normal in literals or re.fullmatch(intro, normal, re.I) or re.fullmatch(framing, normal, re.I):
            continue
        # An explicit no-new result is itself engine supplied, not an AI hint.
        if not contract.outcome.revealed and normal in {
            'nothing new is established', 'no new clue is established'}:
            continue
        return False
    return True


def compose_authoritative(contract, request, raw, trusted):
    """Validate optional prose separately, then validate the composed response.

    Coverage moves to the trusted segment; no safety obligation moves away from
    the untrusted segment. No candidate is ever used as an authority input.
    """
    if trusted != trusted_disclosure(request):
        raise ValueError('disclosure_provenance_mismatch')
    coverage = mandatory_coverage(trusted, request)
    if coverage['decision'] != 'PASS':
        raise ValueError('trusted_disclosure_coverage')
    presentation_request = {**request, 'must_communicate': []}
    presentation = validate_integrated(contract, presentation_request, raw)
    if presentation['decision'] != 'PASS':
        return presentation, None
    # Conservative omission, never rewriting: a candidate that carries a
    # mandatory fact is redundant. Discovery vocabulary in a new-disclosure
    # prelude also stays out, even when a paraphrase is not recognized.
    duplicate = bool(trusted) and (
        any(f['decision'] == 'PASS' for f in mandatory_coverage(raw, request)['facts'])
        or (contract.outcome.revealed and re.search(
            r'\b(?:patrol|route|track|trail|prints|footprints|discover\w*|learn\w*)\b', raw, re.I)))
    if duplicate:
        return {**presentation, 'decision': 'REVIEW_REQUIRED',
                'composition_reason': 'optional_disclosure_overlap', 'coverage': coverage}, None
    if not presentation_within_boundary(contract, request, raw):
        return {**presentation, 'decision': 'REVIEW_REQUIRED',
                'composition_reason': 'outside_bounded_presentation', 'coverage': coverage}, None
    composition_started = time.perf_counter()
    composed = ' '.join(filter(None, (raw.strip(), trusted)))
    composition_ms = quarantine._elapsed(composition_started)
    final = validate_integrated(contract, request, composed)
    final.update(presentation=presentation, trusted_coverage=coverage,
                 provenance='engine_current_action_plus_validated_ai', composition_ms=composition_ms)
    return final, composed if final['decision'] == 'PASS' else None


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
    # Legacy discovery assertions also need already disclosed authorization.
    # Keep this separate from resolver-selected discoveries: it grants no new
    # disclosure and does not add a mandatory outcome to the current action.
    r['previously_disclosed_information'] = list(contract.outcome.known)
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
    authoritative = authoritative_disclosure_enabled()
    render_start = time.perf_counter()
    trusted = trusted_disclosure(request) if authoritative else None
    render_ms = quarantine._elapsed(render_start)
    fault = quarantine._fault()
    live = generator is None and quarantine.live_provider_enabled() and not fault
    if generator is None:
        if live:
            generator = _LiveIntegrated(request['player_action'])
            if authoritative:
                generator.system_prompt = PRESENTATION_PROMPT
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
    if authoritative:
        result.update(disclosure_mode='authoritative', trusted_disclosure=trusted,
                      trusted_disclosure_ms=render_ms,
                      trusted_facts=json.loads(json.dumps(request['must_communicate'])))
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
        provider_request = json.loads(json.dumps(request))
        if authoritative:
            provider_request['engine_disclosure'] = trusted
            provider_request['presentation_responsibility'] = 'optional introduction only; engine supplies mandatory facts'
            # Separate writing instructions from engine-owned facts. Retain
            # disclosure as reference so contradiction/duplication is avoidable.
            provider_request.pop('must_communicate', None)
            provider_request['engine_owned_facts_do_not_narrate'] = request['must_communicate']
        raw = generator.generate(provider_request)
        result['raw_provider_text'] = raw if isinstance(raw, str) else None
        validation_start = time.perf_counter()
        try:
            if authoritative:
                audit, composed = compose_authoritative(contract, request, raw, trusted)
            else:
                audit = validate_integrated(contract, request, raw)
                composed = raw
        finally:
            result['validation_ms'] = quarantine._elapsed(validation_start)
        result['validation'] = audit
        result['diagnostic'] = audit['decision']
        if audit['decision'] == 'PASS':
            result.update(assembled=composed, used_fallback=False)
            if authoritative:
                result['validated_composition'] = composed
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
