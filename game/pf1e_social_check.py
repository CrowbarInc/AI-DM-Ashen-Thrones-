"""Pathfinder social skill check. The ruleset proposes; it does not save.

The difficulty, skill, die, and stance consequence come from the existing
social skill-check owner. This module does not invent a DC, a modifier, or a die.
"""
from __future__ import annotations

from typing import Any, Mapping

from game.skill_checks import resolve_skill_check, should_trigger_check

RULE_REFERENCE = 'game.skill_checks.should_trigger_check:social'
STANCE_OWNER = 'session_npc_stance'
STANCE_OPERATION = 'record_check'
STANCE_FIELD = 'stance'
KINDS = frozenset({'persuade', 'intimidate', 'deceive'})
_SUCCESS = {'persuade': ('trust', 1), 'intimidate': ('fear', 1), 'deceive': ('suspicion', 1)}
_FAILURE = {'intimidate': ('attitude', -1)}
_SKILL_LABEL = {'diplomacy': 'Diplomacy', 'intimidate': 'Intimidate', 'bluff': 'Bluff'}
_KIND_LABEL = {'persuade': 'persuade', 'intimidate': 'intimidate', 'deceive': 'deceive'}


def check_seed(campaign_id, action_id, npc_id, skill, difficulty, character_id) -> list[str]:
    """The existing deterministic die uses these parts and no other entropy."""
    return [str(campaign_id), str(action_id), str(npc_id), str(skill), str(difficulty), str(character_id)]


def _closed(status: str, explanation: str, *, preconditions: list[str] | None = None,
            outcome: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        'status': status,
        'mechanical_outcome': outcome or {},
        'proposed_state_changes': [],
        'required_preconditions': list(preconditions or []),
        'explanation': explanation,
    }


def _clamp(current: int, delta: int) -> int:
    return max(-5, min(5, current + delta))


def _sentence(name: str, skill: str, kind: str, check: Mapping[str, Any], field: str,
              current: int, resulting: int) -> str:
    label = _SKILL_LABEL.get(skill, skill)
    verdict = 'succeeds' if check['success'] else 'fails'
    numbers = f"d20={check['roll']}+{check['modifier']}={check['total']} vs DC {check['difficulty']}"
    penalty = check.get('condition_penalty')
    if penalty:
        numbers += f"; recorded {label} modifier {check.get('base_modifier')} with condition penalty {penalty}"
    if field:
        stance = f"Their {field} is now {resulting}."
    else:
        stance = f"Their trust, fear, attitude, and suspicion are unchanged."
    return (
        f"{label} check to {_KIND_LABEL[kind]} {name} {verdict} ({numbers}). {stance}"
    )


def resolve_social_skill_check(request: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve one persuade, intimidate, or deceive check against one present NPC."""
    parameters = request.get('parameters') if isinstance(request.get('parameters'), Mapping) else {}
    kind = parameters.get('kind')
    if kind not in KINDS:
        return _closed('invalid', 'invalid_social_kind')
    targets = [item for item in (request.get('target_references') or []) if isinstance(item, Mapping) and item.get('kind') == 'npc']
    if len(targets) != 1 or not targets[0].get('id'):
        return _closed('unresolved', 'missing_target', preconditions=['present_npc'])
    npc_id = targets[0]['id']
    npc = context.get('npc') if isinstance(context.get('npc'), Mapping) else {}
    if npc.get('id') != npc_id:
        return _closed('invalid', 'unknown_target')
    supplied = {}
    if type(npc.get('skill_check_modifier')) is int:
        supplied['skill_check_modifier'] = npc['skill_check_modifier']
    overrides = npc.get('skill_check_overrides')
    if isinstance(overrides, Mapping):
        clean = {key: value for key, value in overrides.items() if type(key) is str and type(value) is int}
        if clean:
            supplied['skill_check_overrides'] = clean
    decision = should_trigger_check({'type': kind}, {'engine': 'social', 'npc': supplied})
    skill = decision.get('skill')
    difficulty = decision.get('difficulty')
    if not decision.get('requires_check') or type(skill) is not str or type(difficulty) is not int:
        return _closed('unresolved', 'missing_difficulty', preconditions=['authored_social_difficulty'])
    character = context.get('character') if isinstance(context.get('character'), Mapping) else {}
    skills = character.get('skills') if isinstance(character.get('skills'), Mapping) else {}
    recorded = skills.get(skill)
    if type(recorded) is not int:
        return _closed('unresolved', f'missing_skill:{skill}', preconditions=[f'missing_skill:{skill}'],
                       outcome={'skill': skill, 'difficulty': difficulty, 'dice': 'not_rolled'})
    definitions = context.get('condition_definitions') if isinstance(context.get('condition_definitions'), Mapping) else {}
    check = resolve_skill_check(skill, difficulty, {
        'skills': {skill: recorded},
        'conditions': list(character.get('conditions') or []) if isinstance(character.get('conditions'), list) else [],
    }, {
        'condition_definitions': dict(definitions),
        'seed_parts': check_seed(context.get('campaign_id'), request.get('action_id'), npc_id, skill, difficulty, character.get('id')),
    })
    success = check['success'] is True
    field, delta = _SUCCESS[kind] if success else _FAILURE.get(kind, ('', 0))
    stance = context.get('current_stance') if isinstance(context.get('current_stance'), Mapping) else {}
    current = stance.get(field) if field and type(stance.get(field)) is int else 0
    resulting = _clamp(current, delta) if field else current
    revision = context.get('ledger_revision')
    if type(revision) is not int:
        return _closed('invalid', 'missing_revision')
    value = {
        'kind': kind,
        'skill': skill,
        'roll': check['roll'],
        'modifier': check['modifier'],
        'total': check['total'],
        'difficulty': difficulty,
        'success': success,
        'stance_field': field,
        'stance_delta': delta,
    }
    name = str(npc.get('name') or npc_id)
    outcome = {
        'ruleset': 'pf1e',
        'rule_reference': RULE_REFERENCE,
        'kind': kind,
        'skill': skill,
        'difficulty': difficulty,
        'difficulty_source': 'social_skill_map' if 'skill_check_modifier' not in supplied and 'skill_check_overrides' not in supplied else 'social_skill_map_plus_npc_modifier',
        'roll': check['roll'],
        'modifier': check['modifier'],
        'base_modifier': recorded,
        'condition_penalty': check.get('condition_penalty', 0),
        'total': check['total'],
        'success': success,
        'dice': 'game.skill_checks._deterministic_d20',
        'npc_id': npc_id,
        'stance_field': field,
        'stance_delta': delta,
        'stance_resulting': resulting if field else None,
    }
    return {
        'status': 'authorized',
        'mechanical_outcome': outcome,
        'proposed_state_changes': [{
            'state_owner': STANCE_OWNER,
            'target_id': npc_id,
            'expected_revision': revision,
            'operation': STANCE_OPERATION,
            'field': STANCE_FIELD,
            'value': value,
        }],
        'required_preconditions': [],
        'explanation': _sentence(name, skill, kind, check, field, current, resulting if field else current),
    }
