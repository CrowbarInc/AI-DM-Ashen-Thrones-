"""Explicitly invoked offline preview; never a gameplay GM response.

Trusted engine callers supply completed outcomes. Offline generators are trusted
Python stubs with untrusted return values, not sandboxed executable plugins.
Free English remains subject to human review even when heuristic checks pass.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Protocol

from game.offline_investigation_projection import (
    AuthorizedInvestigation, authorize_investigation, deterministic_fallback,
)
from game.immutable_valid_response import validate_generated_response
from game.mechanical_claims import mechanical_outcome
from game.resolution_contract import contract_mapping_from_resolution

MAX_PRELUDE_BYTES = 1600
CONSTRAINTS = (
    'Write only a descriptive prelude to the examination, ending a complete sentence.',
    'Do not repeat or reinterpret discoveries; the engine appends them verbatim.',
    'Preserve uncertainty. Do not establish culprits, counts, links or destinations.',
    'No possessions, rewards, health, conditions, travel, quests or persistent changes.',
    'Compatible incidental texture is ephemeral and grants no world facts or mechanics.',
)


@dataclass(frozen=True)
class DiscoveryAnchor:
    order: int
    source: str
    status: str
    text: str


@dataclass(frozen=True)
class AnchoredInvestigation:
    outcome: AuthorizedInvestigation
    anchors: tuple[DiscoveryAnchor, ...]


def authorize_anchored_investigation(resolution: dict, payload: dict) -> AnchoredInvestigation:
    """Reuse the existing projection; support only investigations without effects.

    Failed/repeated/mundane cases are offline boundary fixtures. Resolver-selected
    text is trusted authoring; no candidate can enter this constructor.
    """
    effects = mechanical_outcome(resolution)
    if any(v for k, v in effects.items() if k != 'revealed'):
        raise ValueError('side_effects_outside_offline_slice')
    view = authorize_investigation(resolution, payload)
    records = [('resolved_action', 'newly_revealed', t) for t in view.revealed]
    records += [('player_knowledge', 'previously_known', t) for t in view.known]
    # No fabricated discovery for failures or mundane examinations. Public
    # observations and absence of a new result remain engine-owned statements.
    if not records:
        status = {
            'failed': 'The investigation establishes nothing new.',
            'known': 'The examination adds nothing new to what you already know.',
            'observed': 'No new clue is established by this examination.',
        }[view.status]
        records = [('engine_status', view.status, status)]
        records += [('public_observation', 'observed', t) for t in view.observations]
    elif view.status == 'known':
        records.insert(0, ('engine_status', 'known',
                          'The examination adds nothing new to what you already know.'))
    anchors = tuple(DiscoveryAnchor(i, *row) for i, row in enumerate(records))
    return AnchoredInvestigation(view, anchors)


class OfflinePreludeGenerator(Protocol):
    def generate(self, request: dict) -> object:
        """Return one prose string, never an envelope or mutation proposal."""


def prelude_request(contract: AnchoredInvestigation) -> dict:
    """Final allowlist: only scalar authorized strings, no planner extensions.

    JSON roundtrip detaches even nested lists from engine-owned immutable values.
    This interface trusts the engine's public/known classification, not metadata.
    """
    v = contract.outcome
    return json.loads(json.dumps({
        'authorized_investigation': {
            'target': v.target_id, 'status': v.status, 'success': v.success,
            'newly_discovered': v.revealed, 'previously_known': v.known,
        },
        'public_scene': {'observations': v.observations},
        'descriptive_constraints': CONSTRAINTS,
        'max_output_utf8_bytes': MAX_PRELUDE_BYTES,
    }))


def _resolution(contract: AnchoredInvestigation) -> dict:
    # Engine-owned validator input; never accept grants from generated prose.
    v = contract.outcome
    return {'kind': 'investigate', 'success': v.success,
            'discovered_clues': list(v.revealed), 'state_changes': {}}


def validate_prelude(contract: AnchoredInvestigation, raw: object) -> tuple[str, dict]:
    if type(raw) is not str:
        raise ValueError('prelude_shape')
    if len(raw.encode('utf-8')) > MAX_PRELUDE_BYTES:
        raise ValueError('prelude_length')
    text = raw.strip()
    if not text:
        raise ValueError('prelude_empty')
    if any(ord(c) < 32 and c not in '\n\t\r' for c in text):
        raise ValueError('prelude_control_character')
    if text[-1] not in '.!?\u201d\"':
        raise ValueError('prelude_incomplete')
    if any(a.text.casefold() in text.casefold() for a in contract.anchors):
        raise ValueError('duplicate_anchor')
    r = _resolution(contract)
    audit = validate_generated_response(text, resolution=r,
                                        contract=contract_mapping_from_resolution(r))
    from game.consequential_narration_validation import (
        apply_consequential_gate,
        authority_from_anchored,
        validate_consequential_narration,
    )

    try:
        decision = validate_consequential_narration(text, authority_from_anchored(contract))
    except Exception as exc:
        decision = {
            'decision': 'VALIDATION_ERROR',
            'reasons': ['validator_exception'],
            'error_type': type(exc).__name__,
            'claims': [],
            'provider_requests': 0,
        }
    return text, apply_consequential_gate(audit, decision)


def assemble(contract: AnchoredInvestigation, prelude: str) -> str:
    return prelude + '\n\n' + ' '.join(a.text for a in contract.anchors)


def fallback(contract: AnchoredInvestigation) -> str:
    # Existing deterministic wording, with independently preserved exact anchors.
    if any(a.source == 'engine_status' for a in contract.anchors):
        # A single engine status avoids repeating two versions of "nothing new".
        return 'You examine the evidence. ' + ' '.join(a.text for a in contract.anchors)
    text = deterministic_fallback(contract.outcome)
    for anchor in contract.anchors:
        if anchor.text not in text:
            text += ' ' + anchor.text
    return text


@dataclass(frozen=True)
class AnchoredPreview:
    preview_text: str
    anchors: tuple[DiscoveryAnchor, ...]
    diagnostic: str
    used_fallback: bool
    validation_json: str
    review_required: bool = True

    def to_json(self) -> str:
        return json.dumps(asdict(self))


def preview_anchored_investigation(contract: AnchoredInvestigation,
                                  generator: OfflinePreludeGenerator, *,
                                  enabled: bool = False) -> AnchoredPreview:
    """No transport, state handles, retries, persistence or gameplay integration.

    TimeoutError is simulated; real provider deadlines belong to a later trial.
    A passing audit is not semantic approval. Every artifact requires review.
    """
    if enabled is not True:
        raise ValueError('offline_prototype_not_enabled')
    audit = {}
    try:
        prelude, audit = validate_prelude(contract, generator.generate(prelude_request(contract)))
        if not audit['hard_valid']:
            return AnchoredPreview(fallback(contract), contract.anchors, 'semantic_rejection',
                                   True, json.dumps(audit))
        text = assemble(contract, prelude)
        if any(text.count(a.text) != 1 for a in contract.anchors):
            raise ValueError('anchor_integrity')
        return AnchoredPreview(text, contract.anchors, 'heuristic_pass_pending_review',
                               False, json.dumps(audit))
    except Exception as exc:
        diagnostic = ('simulated_timeout' if isinstance(exc, TimeoutError) else
                      'invalid_prelude' if isinstance(exc, (ValueError, UnicodeError)) else
                      'generator_or_renderer_error')
        return AnchoredPreview(fallback(contract), contract.anchors, diagnostic,
                               True, json.dumps(audit))
