from __future__ import annotations
from pathlib import Path
import json
import re
from typing import Any, Dict, List

from game.utils import slugify


def to_int(value, default=0):
    if value is None:
        return default
    if isinstance(value, int):
        return value
    s = str(value).strip().replace('+', '')
    if not s:
        return default
    m = re.search(r'-?\d+', s)
    return int(m.group()) if m else default


def parse_damage(text: str):
    if not text:
        return {'dice_count': 1, 'dice_sides': 1, 'bonus': 0, 'type': 'unknown'}
    t = text.strip().lower().replace(' ', '')
    m = re.match(r'(\d+)d(\d+)([+-]\d+)?', t)
    if not m:
        return {'dice_count': 1, 'dice_sides': 1, 'bonus': 0, 'type': 'unknown'}
    return {'dice_count': int(m.group(1)), 'dice_sides': int(m.group(2)), 'bonus': int(m.group(3) or 0), 'type': 'unknown'}


def collect_skills(raw: Dict[str, Any]):
    skills = {}
    for i in range(1, 36):
        name = raw.get(f'Skill{i:02d}')
        if not name:
            continue
        mod = raw.get(f'Skill{i:02d}Mod')
        skills[slugify(name)] = to_int(mod)
    return skills


def collect_attacks(raw: Dict[str, Any]):
    attacks = []
    for i in range(1, 9):
        name = raw.get(f'Weapon{i}')
        if not name:
            continue
        attacks.append({
            'id': slugify(name),
            'name': name,
            'attack_bonus': to_int(raw.get(f'Weapon{i}AB')),
            'damage': parse_damage(raw.get(f'Weapon{i}Damage', '')),
            'type': (raw.get(f'Weapon{i}Type', '') or '').lower()
        })
    return attacks


def collect_spells(raw: Dict[str, Any]):
    prepared = []
    for i in range(1, 80):
        key = f'Spell{i:02d}'
        name = raw.get(key)
        if not name or str(name).startswith('~~'):
            continue
        prepared.append({'id': slugify(name), 'name': name, 'cast': bool(raw.get(f'{key}Cast')), 'level': 0 if i < 10 else 1})
    return {'prepared': prepared, 'slots': {'0': 0, '1': to_int(raw.get('SpellPerDay1'), 0) + to_int(raw.get('BonusSpells1'), 0)}}


def collect_inventory(raw: Dict[str, Any]):
    items = []
    armor = raw.get('ArmorName')
    if armor:
        items.append({'id': slugify(armor), 'name': armor, 'quantity': 1, 'usable': False})
    for idx in range(1, 10):
        gear = raw.get(f'Gear{idx:02d}')
        if gear:
            items.append({'id': f'gear_{idx}', 'name': gear, 'quantity': 1, 'usable': False})
    return items


def import_sheet(path: str | Path) -> Dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    character = {
        'id': slugify(raw.get('Name', 'character')),
        'name': raw.get('Name', 'Unknown'),
        'class': raw.get('Class', 'Unknown'),
        'level': to_int(raw.get('Level'), 1),
        'ancestry': raw.get('Race', ''),
        'hp': {'current': to_int(raw.get('HP'), 1), 'max': to_int(raw.get('HP'), 1), 'nonlethal': 0},
        'ac': {'normal': to_int(raw.get('AC'), 10), 'touch': to_int(raw.get('ACTouch'), 10), 'flat_footed': to_int(raw.get('ACFlat'), 10)},
        'initiative_bonus': to_int(raw.get('Init'), 0),
        'speed': to_int(str(raw.get('Speed', '30')).split("'")[0], 30),
        'ability_scores': {
            'str': to_int(raw.get('Str'), 10), 'dex': to_int(raw.get('Dex'), 10), 'con': to_int(raw.get('Con'), 10),
            'int': to_int(raw.get('Int'), 10), 'wis': to_int(raw.get('Wis'), 10), 'cha': to_int(raw.get('Cha'), 10)
        },
        'saves': {'fort': to_int(raw.get('Fort'), 0), 'ref': to_int(raw.get('Ref'), 0), 'will': to_int(raw.get('Will'), 0)},
        'bab': to_int(raw.get('MBAB'), 0),
        'cmb': to_int(raw.get('CMB'), 0),
        'cmd': to_int(raw.get('CMD'), 10),
        'skills': collect_skills(raw),
        'attacks': collect_attacks(raw),
        'conditions': [],
        'inventory': collect_inventory(raw),
        'spells': collect_spells(raw),
        'notes': raw.get('__txt_Notes', '')
    }
    return character
