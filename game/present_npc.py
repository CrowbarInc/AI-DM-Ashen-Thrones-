"""Resolve one present person from the existing scene roster.

This is reference binding. It does not roll dice, apply a ruleset, or write state.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

_STOP = frozenset({'the', 'a', 'an', 'my', 'our', 'this', 'that'})


def present_roster(scene: Mapping[str, Any] | None, world: Mapping[str, Any] | None,
                   session: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """People the existing addressable roster already places in the active scene."""
    from game.interaction_context import canonical_scene_addressable_roster

    envelope = scene if isinstance(scene, Mapping) else {}
    inner = envelope.get('scene') if isinstance(envelope.get('scene'), Mapping) else envelope
    scene_id = str((inner or {}).get('id') or (session or {}).get('active_scene_id') or '').strip()
    if not scene_id:
        return []
    rows = canonical_scene_addressable_roster(
        world if isinstance(world, Mapping) else {},
        scene_id,
        scene_envelope=envelope if isinstance(envelope.get('scene'), Mapping) else {'scene': inner},
        session=session if isinstance(session, Mapping) else None,
    )
    return [dict(row) for row in rows if isinstance(row, Mapping) and str(row.get('id') or '').strip()]


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r'[a-z0-9]+', (text or '').casefold()) if token not in _STOP]


def _surfaces(npc: Mapping[str, Any]) -> list[str]:
    parts = [str(npc.get('name') or ''), str(npc.get('id') or '').replace('_', ' ')]
    parts.extend(str(item) for item in (npc.get('address_roles') or []) if isinstance(item, str))
    parts.extend(str(item) for item in (npc.get('aliases') or []) if isinstance(item, str))
    return [' '.join(_tokens(part)) for part in parts if _tokens(part)]


def npc_check_facts(scene: Mapping[str, Any] | None, npc_id: str, roster_row: Mapping[str, Any]) -> dict[str, Any]:
    """Copy authored social-check fields. Missing fields are omitted, not defaulted."""
    facts: dict[str, Any] = {'id': npc_id, 'name': str(roster_row.get('name') or npc_id)}
    sources = [roster_row]
    inner = scene.get('scene') if isinstance(scene, Mapping) and isinstance(scene.get('scene'), Mapping) else {}
    for item in inner.get('addressables') or []:
        if isinstance(item, Mapping) and str(item.get('id') or '') == npc_id:
            sources.append(item)
    for source in sources:
        if type(source.get('skill_check_modifier')) is int:
            facts['skill_check_modifier'] = source['skill_check_modifier']
        overrides = source.get('skill_check_overrides')
        if isinstance(overrides, Mapping):
            clean = {key: value for key, value in overrides.items() if type(key) is str and type(value) is int}
            if clean:
                facts['skill_check_overrides'] = clean
    return facts


def match_present_npc(phrase: str, roster: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Match a player phrase to one present person, or report why it does not."""
    candidates = [phrase]
    if re.search(r'\s+to\s+', phrase or '', flags=re.I):
        candidates.insert(0, re.split(r'\s+to\s+', phrase, maxsplit=1, flags=re.I)[0])
    best = {'status': 'missing', 'options': []}
    for candidate in candidates:
        phrase_norm = ' '.join(_tokens(candidate))
        phrase_tokens = set(_tokens(candidate))
        if not phrase_norm:
            continue
        matched: list[Mapping[str, Any]] = []
        seen: set[str] = set()
        for npc in roster:
            npc_id = str(npc.get('id') or '').strip()
            if not npc_id or npc_id in seen:
                continue
            surfaces = _surfaces(npc)
            name_tokens = set(_tokens(str(npc.get('name') or ''))) | set(_tokens(str(npc_id).replace('_', ' ')))
            exact = phrase_norm in surfaces
            named = bool(phrase_tokens) and phrase_tokens <= name_tokens
            if exact or named:
                seen.add(npc_id)
                matched.append(npc)
        if len(matched) == 1:
            return {'status': 'unique', 'npc': dict(matched[0]), 'options': [str(matched[0].get('name') or matched[0].get('id'))]}
        if len(matched) > 1:
            best = {'status': 'ambiguous', 'options': [str(npc.get('name') or npc.get('id')) for npc in matched]}
    return best
