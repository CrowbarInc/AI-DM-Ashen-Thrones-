from __future__ import annotations
from typing import Any, Dict, List, Optional

from game.models import CombatEngineResult
from game.utils import roll_die, int_mod, slugify
from game.conditions import current_ac, add_condition, remove_condition, has_condition, can_take_actions, can_attack, can_cast, cleanup_player_turn


def alive_enemies(scene: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [e for e in scene['scene'].get('enemies', []) if e['hp']['current'] > 0]


def get_enemy(scene: Dict[str, Any], enemy_id: str) -> Dict[str, Any]:
    for enemy in scene['scene'].get('enemies', []):
        if enemy['id'] == enemy_id:
            return enemy
    raise ValueError(f'Enemy not found: {enemy_id}')


def resolve_enemy_id_from_hint(scene: Dict[str, Any], hint: Optional[str]) -> Optional[str]:
    """Resolve a freeform target hint (e.g. 'orc', 'the guard') to an enemy id.
    Tries exact id match, then slug match on id and name. Returns None if no match."""
    if not hint or not isinstance(hint, str):
        return None
    h = hint.strip().lower()
    if not h:
        return None
    h_slug = slugify(h)
    for enemy in alive_enemies(scene):
        if enemy['id'] == h or enemy['id'] == hint:
            return enemy['id']
        if slugify(enemy['id']) == h_slug or h_slug in slugify(enemy['id']):
            return enemy['id']
        name = (enemy.get('name') or '').strip()
        if name and (name.lower() == h or slugify(name) == h_slug or h_slug in slugify(name)):
            return enemy['id']
    return None


def ensure_target(scene: Dict[str, Any], target_id: Optional[str]) -> str:
    if target_id:
        try:
            enemy = get_enemy(scene, target_id)
            if enemy and enemy['hp']['current'] > 0:
                return target_id
        except ValueError:
            pass
        resolved = resolve_enemy_id_from_hint(scene, target_id)
        if resolved:
            return resolved
    enemies = alive_enemies(scene)
    if not enemies:
        raise ValueError('No living enemies remain.')
    return enemies[0]['id']


def get_attack(character: Dict[str, Any], attack_id: str) -> Dict[str, Any]:
    for attack in character.get('attacks', []):
        if attack['id'] == attack_id:
            return attack
    raise ValueError(f'Attack not found: {attack_id}')


def get_spell(character: Dict[str, Any], spell_id: str) -> Dict[str, Any]:
    for spell in character.get('spells', {}).get('prepared', []):
        if spell.get('id') == spell_id:
            return spell
    raise ValueError(f'Spell not found: {spell_id}')


def risky_strike_values(bab: int) -> Dict[str, int]:
    tier = bab // 4
    return {'attack_penalty': -(1 + tier), 'damage_bonus': 2 + tier * 2}


def defensive_stance_values(bab: int) -> Dict[str, int]:
    tier = bab // 4
    return {'attack_penalty': -(1 + tier), 'ac_bonus': 1 + tier}


def player_can_act(character: Dict[str, Any], combat: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
    if combat['in_combat'] and combat['active_actor_id'] != character['id']:
        return False
    if combat['player_turn_used']:
        return False
    return can_take_actions(character, conditions)


def roll_initiative(character: Dict[str, Any], scene: Dict[str, Any], combat: Dict[str, Any], conditions: Dict[str, Any]) -> Dict[str, Any]:
    entries = []
    pr = roll_die(20) + character.get('initiative_bonus', 0)
    entries.append({'id': character['id'], 'name': character['name'], 'initiative_total': pr, 'side': 'player'})
    for enemy in alive_enemies(scene):
        er = roll_die(20) + enemy.get('initiative_bonus', 0)
        entries.append({'id': enemy['id'], 'name': enemy['name'], 'initiative_total': er, 'side': 'enemy'})
    entries.sort(key=lambda x: x['initiative_total'], reverse=True)
    combat['in_combat'] = True
    combat['round'] = 1
    combat['initiative_order'] = entries
    combat['turn_index'] = 0
    combat['active_actor_id'] = entries[0]['id'] if entries else None
    combat['player_turn_used'] = False
    cleanup_player_turn(character)
    result = CombatEngineResult(
        kind='initiative',
        action_id='initiative',
        label='Roll initiative',
        prompt='Roll initiative',
        success=None,
        hint='Combat has begun. Narrate the initiative order and the first actor to act.',
        combat={
            'combat_phase': 'initiative',
            'actor': {'id': character['id'], 'name': character['name']},
            'target': None,
            'rolls': {},
            'hit': None,
            'damage_dealt': 0,
            'healing_applied': 0,
            'conditions_applied': [],
            'conditions_removed': [],
            'turn_advanced': False,
            'combat_ended': False,
            'winner': None,
            'round': combat['round'],
            'active_actor_id': combat['active_actor_id'],
            'order': entries,
        },
    )
    return result.to_dict()


def advance_turn(combat: Dict[str, Any]) -> None:
    if not combat['initiative_order']:
        combat['active_actor_id'] = None
        return
    combat['turn_index'] += 1
    if combat['turn_index'] >= len(combat['initiative_order']):
        combat['turn_index'] = 0
        combat['round'] += 1
    combat['active_actor_id'] = combat['initiative_order'][combat['turn_index']]['id']


def prune_initiative(scene: Dict[str, Any], combat: Dict[str, Any], player_id: str) -> None:
    living = {player_id} | {e['id'] for e in alive_enemies(scene)}
    combat['initiative_order'] = [e for e in combat['initiative_order'] if e['id'] in living]
    if not combat['initiative_order']:
        combat.update({'in_combat': False, 'round': 0, 'turn_index': 0, 'active_actor_id': None, 'player_turn_used': False})
        return
    if combat['turn_index'] >= len(combat['initiative_order']):
        combat['turn_index'] = 0
    combat['active_actor_id'] = combat['initiative_order'][combat['turn_index']]['id']


def end_combat_if_done(scene: Dict[str, Any], combat: Dict[str, Any]) -> bool:
    if alive_enemies(scene):
        return False
    combat.update({'in_combat': False, 'round': 0, 'initiative_order': [], 'turn_index': 0, 'active_actor_id': None, 'player_turn_used': False})
    return True


def build_end_turn_result(combat: Dict[str, Any]) -> Dict[str, Any]:
    """Canonical engine result when player ends turn and it immediately becomes their turn again (no enemy)."""
    result = CombatEngineResult(
        kind='end_turn',
        action_id='end_turn',
        label='End turn',
        prompt='End turn',
        success=None,
        hint=f"Round {combat.get('round', 1)}. Player's turn again.",
        combat={
            'combat_phase': 'end_turn',
            'actor': None,
            'target': None,
            'rolls': {},
            'hit': None,
            'damage_dealt': 0,
            'healing_applied': 0,
            'conditions_applied': [],
            'conditions_removed': [],
            'turn_advanced': True,
            'combat_ended': False,
            'winner': None,
            'round': combat.get('round'),
            'active_actor_id': combat.get('active_actor_id'),
        },
    )
    return result.to_dict()


def resolve_attack(character: Dict[str, Any], scene: Dict[str, Any], attack_id: str, target_id: Optional[str], modifiers: List[str], conditions: Dict[str, Any]) -> Dict[str, Any]:
    if not can_attack(character, conditions):
        raise ValueError('You cannot attack in your current condition.')
    attack = get_attack(character, attack_id)
    target_id = ensure_target(scene, target_id)
    enemy = get_enemy(scene, target_id)

    attack_bonus = attack['attack_bonus']
    damage_bonus = attack['damage']['bonus']
    applied = []

    if 'risky_strike' in modifiers:
        rs = risky_strike_values(character.get('bab', 0))
        attack_bonus += rs['attack_penalty']
        damage_bonus += rs['damage_bonus']
        applied.append({'name': 'Risky Strike', **rs})
        remove_condition(character, 'risky_strike')
        add_condition(character, {'name': 'risky_strike', 'expires': 'start_of_next_player_turn'})

    if 'defensive_stance' in modifiers:
        ds = defensive_stance_values(character.get('bab', 0))
        attack_bonus += ds['attack_penalty']
        applied.append({'name': 'Defensive Stance', **ds})
        remove_condition(character, 'defensive_stance')
        add_condition(character, {'name': 'defensive_stance', 'ac_bonus': ds['ac_bonus'], 'expires': 'start_of_next_player_turn'})

    d20 = roll_die(20)
    total = d20 + attack_bonus
    target_ac = current_ac(enemy, conditions)
    hit = total >= target_ac
    damage = 0
    if hit:
        for _ in range(attack['damage']['dice_count']):
            damage += roll_die(attack['damage']['dice_sides'])
        damage += damage_bonus
        enemy['hp']['current'] = max(0, enemy['hp']['current'] - damage)
    hint = (
        f"Player hit {enemy['name']} for {damage} damage with {attack['name']}."
        if hit else f"Player missed {enemy['name']} with {attack['name']} (roll {total} vs AC {target_ac})."
    )
    result = CombatEngineResult(
        kind='attack',
        action_id=attack_id,
        label=f"Attack with {attack['name']}",
        prompt=f"Attack with {attack_id}",
        success=hit,
        hint=hint,
        combat={
            'combat_phase': 'attack',
            'actor': {'id': character['id'], 'name': character['name']},
            'target': {'id': enemy['id'], 'name': enemy['name']},
            'weapon_name': attack['name'],
            'rolls': {'attack_roll': d20, 'attack_total': total, 'target_ac': target_ac},
            'hit': hit,
            'damage_dealt': damage,
            'healing_applied': 0,
            'conditions_applied': [],
            'conditions_removed': [],
            'turn_advanced': False,
            'combat_ended': not alive_enemies(scene),
            'winner': 'player' if not alive_enemies(scene) else None,
            'round': None,
            'active_actor_id': None,
            'target_hp_remaining': enemy['hp']['current'],
            'applied_modifiers': applied,
        },
    )
    return result.to_dict()


def resolve_skill(character: Dict[str, Any], skill_id: str, intent: str) -> Dict[str, Any]:
    bonus = character.get('skills', {}).get(skill_id)
    if bonus is None:
        raise ValueError(f'Unknown skill: {skill_id}')
    d20 = roll_die(20)
    total = d20 + bonus
    result = CombatEngineResult(
        kind='skill_check',
        action_id=skill_id,
        label=f'Use {skill_id}',
        prompt=intent or f'Use {skill_id}',
        success=None,
        hint=f"Player rolled {skill_id} (d20={d20}+{bonus}={total}). Narrate the outcome.",
        combat={
            'combat_phase': 'skill_check',
            'actor': {'id': character['id'], 'name': character['name']},
            'target': None,
            'rolls': {'roll': d20, 'modifier': bonus, 'total': total},
            'hit': None,
            'damage_dealt': 0,
            'healing_applied': 0,
            'conditions_applied': [],
            'conditions_removed': [],
            'turn_advanced': False,
            'combat_ended': False,
            'winner': None,
            'round': None,
            'active_actor_id': None,
            'skill_id': skill_id,
            'intent': intent,
        },
    )
    return result.to_dict()


def resolve_spell(character: Dict[str, Any], scene: Dict[str, Any], spell_id: str, target_id: Optional[str], conditions: Dict[str, Any]) -> Dict[str, Any]:
    if not can_cast(character, conditions):
        raise ValueError('You cannot cast spells in your current condition.')
    spell = get_spell(character, spell_id)
    name = spell['name'].lower()
    if spell.get('cast'):
        raise ValueError(f"{spell['name']} is already marked cast. Reset or edit the sheet to refresh slots.")
    if name == 'magic missile':
        target_id = ensure_target(scene, target_id)
        enemy = get_enemy(scene, target_id)
        missiles = min(5, 1 + ((max(1, character['level']) - 1) // 2))
        rolls = [roll_die(4) + 1 for _ in range(missiles)]
        total_damage = sum(rolls)
        enemy['hp']['current'] = max(0, enemy['hp']['current'] - total_damage)
        spell['cast'] = True
        result = CombatEngineResult(
            kind='spell',
            action_id=spell_id,
            label=f"Cast {spell['name']}",
            prompt=f"Cast {spell_id}",
            success=True,
            hint=f"Player hit {enemy['name']} with Magic Missile for {total_damage} damage ({len(rolls)} missiles).",
            combat={
                'combat_phase': 'spell',
                'actor': {'id': character['id'], 'name': character['name']},
                'target': {'id': enemy['id'], 'name': enemy['name']},
                'weapon_name': spell['name'],
                'rolls': {'damage_rolls': rolls, 'total_damage': total_damage},
                'hit': True,
                'damage_dealt': total_damage,
                'healing_applied': 0,
                'conditions_applied': [],
                'conditions_removed': [],
                'turn_advanced': False,
                'combat_ended': not alive_enemies(scene),
                'winner': 'player' if not alive_enemies(scene) else None,
                'round': None,
                'active_actor_id': None,
                'target_hp_remaining': enemy['hp']['current'],
                'spell_name': spell['name'],
            },
        )
        return result.to_dict()
    if name == 'daze':
        target_id = ensure_target(scene, target_id)
        enemy = get_enemy(scene, target_id)
        dc = 10 + 0 + int_mod(character['ability_scores']['int'])
        roll = roll_die(20)
        total = roll + enemy.get('saves', {}).get('will', 0)
        applied = False
        if enemy.get('creature_type', '').lower() == 'humanoid' and enemy.get('hd', 99) <= 4 and total < dc:
            remove_condition(enemy, 'dazed')
            add_condition(enemy, {'name': 'dazed', 'expires': 'after_skipped_turn'})
            applied = True
        spell['cast'] = True
        success = applied
        hint = (
            f"{enemy['name']} failed the Will save and is dazed." if applied
            else f"{enemy['name']} resisted the Daze spell (save {total} vs DC {dc})."
        )
        result = CombatEngineResult(
            kind='spell',
            action_id=spell_id,
            label=f"Cast {spell['name']}",
            prompt=f"Cast {spell_id}",
            success=success,
            hint=hint,
            combat={
                'combat_phase': 'spell',
                'actor': {'id': character['id'], 'name': character['name']},
                'target': {'id': enemy['id'], 'name': enemy['name']},
                'weapon_name': spell['name'],
                'rolls': {'save_roll': roll, 'save_total': total, 'dc': dc, 'save_type': 'Will'},
                'hit': None,
                'damage_dealt': 0,
                'healing_applied': 0,
                'conditions_applied': ['dazed'] if applied else [],
                'conditions_removed': [],
                'turn_advanced': False,
                'combat_ended': False,
                'winner': None,
                'round': None,
                'active_actor_id': None,
                'spell_name': spell['name'],
                'condition_applied': 'dazed' if applied else None,
            },
        )
        return result.to_dict()
    if name == 'shield':
        remove_condition(character, 'shield')
        add_condition(character, {'name': 'shield', 'ac_bonus': 4, 'expires': 'start_of_next_player_turn'})
        spell['cast'] = True
        result = CombatEngineResult(
            kind='spell',
            action_id=spell_id,
            label=f"Cast {spell['name']}",
            prompt=f"Cast {spell_id}",
            success=True,
            hint=f"Player cast Shield. AC +4 until start of next turn.",
            combat={
                'combat_phase': 'spell',
                'actor': {'id': character['id'], 'name': character['name']},
                'target': {'id': character['id'], 'name': character['name']},
                'weapon_name': spell['name'],
                'rolls': {},
                'hit': None,
                'damage_dealt': 0,
                'healing_applied': 0,
                'conditions_applied': ['shield'],
                'conditions_removed': [],
                'turn_advanced': False,
                'combat_ended': False,
                'winner': None,
                'round': None,
                'active_actor_id': None,
                'spell_name': spell['name'],
                'effect': 'shield_applied',
            },
        )
        return result.to_dict()
    raise ValueError(f'Spell resolver not implemented for {spell["name"]}.')


def enemy_take_turn(character: Dict[str, Any], scene: Dict[str, Any], combat: Dict[str, Any], conditions: Dict[str, Any]) -> Dict[str, Any]:
    """Returns canonical CombatEngineResult dict. No wrapper; resolution is the result itself."""
    active_id = combat['active_actor_id']
    enemy = get_enemy(scene, active_id)
    if not can_take_actions(enemy, conditions):
        if has_condition(enemy, 'dazed'):
            remove_condition(enemy, 'dazed')
        result = CombatEngineResult(
            kind='enemy_turn_skipped',
            action_id='enemy_turn',
            label=f"{enemy['name']} skips turn",
            prompt=f"{enemy['name']} is unable to act",
            success=None,
            hint=f"{enemy['name']} is unable to act this round.",
            combat={
                'combat_phase': 'enemy_turn',
                'actor': {'id': enemy['id'], 'name': enemy['name']},
                'target': None,
                'rolls': {},
                'hit': None,
                'damage_dealt': 0,
                'healing_applied': 0,
                'conditions_applied': [],
                'conditions_removed': ['dazed'] if has_condition(enemy, 'dazed') else [],
                'turn_advanced': True,
                'combat_ended': False,
                'winner': None,
                'round': combat.get('round'),
                'active_actor_id': active_id,
                'reason': 'condition_prevents_actions',
            },
        )
        return result.to_dict()
    attack = enemy['attacks'][0]
    d20 = roll_die(20)
    total = d20 + attack['attack_bonus']
    target_ac = current_ac(character, conditions)
    hit = total >= target_ac
    damage = 0
    if hit:
        for _ in range(attack['damage']['dice_count']):
            damage += roll_die(attack['damage']['dice_sides'])
        damage += attack['damage']['bonus']
        character['hp']['current'] = max(0, character['hp']['current'] - damage)
    hint = (
        f"{enemy['name']} hit {character['name']} for {damage} damage with {attack['name']}."
        if hit else f"{enemy['name']} missed {character['name']} with {attack['name']} (roll {total} vs AC {target_ac})."
    )
    result = CombatEngineResult(
        kind='enemy_attack',
        action_id='enemy_attack',
        label=f"{enemy['name']} attacks",
        prompt=hint,
        success=hit,
        hint=hint,
        combat={
            'combat_phase': 'enemy_turn',
            'actor': {'id': enemy['id'], 'name': enemy['name']},
            'target': {'id': character['id'], 'name': character['name']},
            'weapon_name': attack['name'],
            'rolls': {'attack_roll': d20, 'attack_total': total, 'target_ac': target_ac},
            'hit': hit,
            'damage_dealt': damage,
            'healing_applied': 0,
            'conditions_applied': [],
            'conditions_removed': [],
            'turn_advanced': True,
            'combat_ended': False,
            'winner': None,
            'round': combat.get('round'),
            'active_actor_id': active_id,
            'target_hp_remaining': character['hp']['current'],
        },
    )
    return result.to_dict()
