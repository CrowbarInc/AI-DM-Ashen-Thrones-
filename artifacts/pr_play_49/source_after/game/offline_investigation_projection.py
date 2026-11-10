"""Existing PR47 read-only investigation projection and deterministic fallback.

Shared only by the two opt-in offline investigation previews. No state owners,
provider interface, new resolution logic or generalized narration policy.
"""
from __future__ import annotations
from dataclasses import dataclass
from game.authorized_information import revealed_information
from game.mechanical_claims import mechanical_fallback
from game.narration_authorization import project_narration_payload


@dataclass(frozen=True)
class AuthorizedInvestigation:
    """Ephemeral read model, derived from the existing authority, not state.

    Text slots are trusted engine projections. Never construct this type from a
    selector response. Failure excludes stale resolution clues. Known clues must
    come from the established player-knowledge projection, never a clue catalog.
    """
    status: str
    success: bool | None
    target_id: str | None
    revealed: tuple[str, ...]
    known: tuple[str, ...]
    observations: tuple[str, ...]
    consequences: str


def _strings(rows):
    return tuple(dict.fromkeys(x.strip() for x in rows
                              if type(x) is str and x.strip()))


def authorize_investigation(resolution: dict, narration_payload: dict) -> AuthorizedInvestigation:
    """Engine-side adapter; no scene catalog, world, hints or private metadata escapes."""
    if resolution.get('kind') not in {'investigate', 'observe', 'discover_clue', 'already_searched'}:
        raise ValueError('Only resolved investigations are supported')
    projected = project_narration_payload(narration_payload, resolution)
    scene = projected['scene']
    new = tuple(item['text'] for item in revealed_information(resolution))
    known = _strings([row.get('text') for row in scene['discovered_clues']])
    known = tuple(x for x in known if x not in new)
    changes = resolution.get('state_changes') or {}
    status = ('known' if resolution.get('kind') == 'already_searched' or changes.get('already_searched')
              else 'failed' if resolution.get('success') is False
              else 'discovered' if new else 'observed')
    # Reuse the existing consequence adapter. Private NPC/faction updates are
    # excluded by the existing projection. Disclosure has its own exact slot.
    effects = dict(projected['authorized_mechanical_outcome'])
    effects.pop('revealed', None)
    unsupported = set(effects) - {
        'items_added', 'items_removed', 'currency_gained', 'currency_spent',
        'damage_taken', 'health_recovered', 'conditions_applied', 'conditions_removed',
        'routes_unlocked', 'objectives_completed', 'time_advanced', 'destination'}
    if unsupported:
        raise ValueError('Unsupported investigation consequence')
    # Effects remain engine text, with no second writable consequence store.
    effect_resolution = {'kind': 'investigate', 'state_changes': effects}
    if effects.get('destination'):
        effect_resolution.update(resolved_transition=True, target_scene_id=effects['destination'])
    consequences = mechanical_fallback(effect_resolution)
    target = resolution.get('interactable_id') or resolution.get('action_id')
    target = target if type(target) is str else None
    success = resolution.get('success')
    success = success if type(success) is bool else None
    return AuthorizedInvestigation(status, success, target, new, known,
        _strings(scene['public'].get('visible_facts') or []), consequences)


def deterministic_fallback(view: AuthorizedInvestigation) -> str:
    status = {
        'discovered': 'You examine the evidence.',
        'known': 'You examine the evidence again; nothing new is established.',
        'failed': 'You inspect the target, but nothing new is established.',
        'observed': 'You examine what is visible; no new clue is established.',
    }[view.status]
    return ' '.join(filter(None, (status, *view.revealed, *view.known,
                                *view.observations, view.consequences)))


