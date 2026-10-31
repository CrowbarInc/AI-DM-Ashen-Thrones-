from __future__ import annotations
from typing import Any, Dict


def get_template(name: str, definitions: Dict[str, Any]) -> Dict[str, Any]:
    return definitions.get(name, {})


def has_condition(entity: Dict[str, Any], name: str) -> bool:
    return any(c.get('name') == name for c in entity.get('conditions', []))


def add_condition(entity: Dict[str, Any], condition: Dict[str, Any]) -> None:
    entity.setdefault('conditions', []).append(condition)


def remove_condition(entity: Dict[str, Any], name: str) -> None:
    entity['conditions'] = [c for c in entity.get('conditions', []) if c.get('name') != name]


def get_effect_value(entity: Dict[str, Any], definitions: Dict[str, Any], key: str) -> int:
    total = 0
    for cond in entity.get('conditions', []):
        if key in cond:
            value = cond[key]
        else:
            value = get_template(cond.get('name', ''), definitions).get('default_effects', {}).get(key, 0)
        if isinstance(value, bool):
            value = int(value)
        if isinstance(value, (int, float)):
            total += int(value)
    return total


def has_effect(entity: Dict[str, Any], definitions: Dict[str, Any], key: str) -> bool:
    for cond in entity.get('conditions', []):
        if key in cond and bool(cond[key]):
            return True
        if get_template(cond.get('name', ''), definitions).get('default_effects', {}).get(key) is True:
            return True
    return False


def current_ac(entity: Dict[str, Any], definitions: Dict[str, Any]) -> int:
    ac_block = entity.get('ac', {})
    base = ac_block.get('normal', ac_block if isinstance(ac_block, int) else 10)
    if has_effect(entity, definitions, 'lose_dex_to_ac') and isinstance(ac_block, dict) and ac_block.get('flat_footed') is not None:
        base = ac_block['flat_footed']
    return base + get_effect_value(entity, definitions, 'ac_bonus') - get_effect_value(entity, definitions, 'ac_penalty')


def can_take_actions(entity: Dict[str, Any], definitions: Dict[str, Any]) -> bool:
    return not has_effect(entity, definitions, 'no_actions')


def can_attack(entity: Dict[str, Any], definitions: Dict[str, Any]) -> bool:
    return can_take_actions(entity, definitions) and not has_effect(entity, definitions, 'no_attacks') and not has_effect(entity, definitions, 'single_move_only')


def can_cast(entity: Dict[str, Any], definitions: Dict[str, Any]) -> bool:
    return can_take_actions(entity, definitions) and not has_effect(entity, definitions, 'no_spells')


def cleanup_player_turn(character: Dict[str, Any]) -> None:
    character['conditions'] = [c for c in character.get('conditions', []) if c.get('expires') != 'start_of_next_player_turn']
