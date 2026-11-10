"""Opt-in OFFLINE investigation presentation experiment, with no gameplay wiring.

Only engine callers construct the authorized view. Selectors receive JSON copies
and return enums, never prose, identifiers, or mutation proposals. The resulting
artifact is deliberately not a GM response and has no legacy adoption fields.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Protocol

from game.offline_investigation_projection import (
    AuthorizedInvestigation, authorize_investigation, deterministic_fallback,
)


CONTROLS = {
    'structure': ('action_first', 'evidence_first', 'setting_first'),
    'pace': ('clipped', 'flowing', 'measured'),
    'tone': ('spare', 'reflective', 'intent'),
    'sensory_focus': ('none', 'visual', 'texture', 'listening'),
    'detail': ('lean', 'standard', 'extended'),
    'perspective': ('second_person', 'close_observation'),
    'transition': ('direct', 'pause', 'question'),
    'information_order': ('new_first', 'known_first'),
}
PLAN_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': list(CONTROLS),
    'properties': {key: {'type': 'string', 'enum': list(values)}
                   for key, values in CONTROLS.items()},
}
DEFAULT_PLAN = {key: values[0] for key, values in CONTROLS.items()}
MAX_PLAN_BYTES = 2048


class OfflinePlanSelector(Protocol):
    def select(self, payload: dict) -> object:
        """Return a JSON plan; offline implementations only for this experiment."""


def selection_payload(view: AuthorizedInvestigation) -> dict:
    # Round trip makes a detached, JSON-only request, with no engine references.
    return json.loads(json.dumps({'authorized_investigation': asdict(view),
                                'available_controls': PLAN_SCHEMA}))


def validate_plan(raw: object) -> dict[str, str]:
    if type(raw) is str:
        if len(raw.encode('utf-8')) > MAX_PLAN_BYTES:
            raise ValueError('plan_too_large')
        def unique(pairs):
            obj = {}
            for key, value in pairs:
                if key in obj: raise ValueError('duplicate_field')
                obj[key] = value
            return obj
        raw = json.loads(raw, object_pairs_hook=unique)
    if type(raw) is not dict or set(raw) != set(CONTROLS):
        raise ValueError('exact_fields_required')
    # Type checks precede membership: nested objects, booleans, lists and
    # custom coercible objects never become narrative strings.
    if any(type(raw[k]) is not str or raw[k] not in values for k, values in CONTROLS.items()):
        raise ValueError('unsupported_control')
    return dict(raw)


def render_investigation(view: AuthorizedInvestigation, raw_plan: object) -> str:
    p = validate_plan(raw_plan)  # Also enforce the boundary for direct callers.
    opening = {
        'second_person': {
            'spare': 'You examine the evidence.',
            'reflective': 'You take a closer look, letting the details settle into place.',
            'intent': 'You narrow your attention to the evidence before you.',
        },
        'close_observation': {
            'spare': 'A closer examination follows.',
            'reflective': 'The examination moves from the whole to the smallest details.',
            'intent': 'Each detail receives close attention.',
        },
    }[p['perspective']][p['tone']]
    # These are approved, transient shifts of attention, not invented weather,
    # objects, gestures by absent NPCs, discoveries, hazards, or persistent leads.
    texture = {
        'none': '', 'visual': 'Your gaze moves slowly across what is visible.',
        'texture': 'You attend to surface and texture, as well as shape.',
        'listening': 'You listen as you look, keeping your attention on the search.',
    }[p['sensory_focus']]
    transition = {'direct': '', 'pause': 'You pause over the details.',
                  'question': 'What does the evidence actually establish?'}[p['transition']]
    status = {
        'discovered': '',
        'known': 'The examination adds nothing new to what you already know.',
        'failed': 'The attempt establishes nothing new.',
        'observed': 'No new clue is established by this examination.',
    }[view.status]
    new = ' '.join(view.revealed)
    known = ('Already established: ' + ' '.join(view.known)) if view.known else ''
    facts = [new, known] if p['information_order'] == 'new_first' else [known, new]
    # Detail only changes optional public observation and approved texture;
    # discoveries, previous knowledge, status and consequences are mandatory.
    count = {'lean': 0, 'standard': 1, 'extended': 2}[p['detail']]
    setting = ' '.join(view.observations[:count])
    action = ' '.join(filter(None, (opening, texture if count else '')))
    if p['pace'] == 'flowing' and count and texture:
        action = opening.rstrip('.') + '; ' + texture[0].lower() + texture[1:]
    evidence = ' '.join(filter(None, (transition, *facts, status, view.consequences)))
    blocks = {'action_first': [action, setting, evidence],
              'evidence_first': [evidence, action, setting],
              'setting_first': [setting, action, evidence]}[p['structure']]
    blocks = [x for x in blocks if x]
    # Source fact sentences remain intact; cadence operates only between blocks.
    separator = {'clipped': ' ', 'flowing': ' ', 'measured': '\n\n'}[p['pace']]
    return separator.join(blocks)


@dataclass(frozen=True)
class InvestigationPreview:
    text: str
    plan_json: str
    diagnostic: str
    used_fallback: bool

    def to_json(self) -> str:
        # Explicit surface: cannot serialize a selector's scene/world proposals
        # into a legacy GM response or a metadata/context-adoption field.
        return json.dumps({'preview_text': self.text, 'plan': json.loads(self.plan_json),
                           'diagnostic': self.diagnostic, 'used_fallback': self.used_fallback})


def preview_investigation(view: AuthorizedInvestigation, selector: OfflinePlanSelector,
                         *, enabled: bool = False) -> InvestigationPreview:
    """Explicitly opt in; return a review artifact, never a gameplay response.

    Selectors are trusted offline code, with untrusted output. This is not a
    sandbox for arbitrary Python providers. TimeoutError is simulated offline;
    real timeout enforcement and live adapters are intentionally not implemented.
    """
    if enabled is not True:
        raise ValueError('offline_prototype_not_enabled')
    try:
        plan = validate_plan(selector.select(selection_payload(view)))
        text = render_investigation(view, plan)
        return InvestigationPreview(text, json.dumps(plan), 'accepted', False)
    except Exception as exc:
        # Retain a safe diagnostic code, never arbitrary exception/provider prose.
        diagnostic = ('plan_timeout' if isinstance(exc, TimeoutError) else
                      'invalid_plan' if isinstance(exc, ValueError) else 'selection_or_render_error')
        return InvestigationPreview(deterministic_fallback(view), json.dumps(DEFAULT_PLAN),
                                    diagnostic, True)
