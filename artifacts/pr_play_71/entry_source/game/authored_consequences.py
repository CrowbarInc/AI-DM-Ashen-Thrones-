"""Finite server-authored consequences, using existing conditions and world flags."""
import copy
import json
import os
from pathlib import Path

GATE = 'ASHEN_EXPERIMENTAL_BRANCHING'
SESSION = 'ASHEN_EXPERIMENTAL_BRANCHING_SESSION'
FIXTURE = Path(__file__).resolve().parents[1] / 'experiments/pr_play_70/scene_actions.json'


def overlay(scene, session):
    sid = str(session.get('campaign_run_id') or session.get('session_id') or '')
    if os.environ.get(GATE) != '1' or not sid or os.environ.get(SESSION) != sid:
        return scene
    actions = json.loads(FIXTURE.read_text(encoding='utf-8')).get(scene.get('scene', {}).get('id'), [])
    result = copy.deepcopy(scene)
    result['scene'].setdefault('actions', []).extend(actions)
    return result


def resolve(scene, session, world, action):
    """No mutations: only current server scene definitions can supply effects."""
    from game.affordances import _affordance_passes_conditions
    from game.models import ExplorationEngineResult
    aid = str(action.get('id') or '')
    definitions = [a for a in scene.get('actions', []) if isinstance(a, dict) and a.get('id') == aid]
    authored = definitions[0] if len(definitions) == 1 else None
    if not authored or 'consequence' not in authored:
        return None
    effect = authored['consequence']
    conditions = authored.get('conditions', {})
    allowed_conditions = {'requires_flags', 'excludes_flags', 'requires_clues', 'excludes_clues'}
    valid = (isinstance(effect, dict) and set(effect) == {'set_flags', 'text'}
             and isinstance(effect.get('text'), str) and bool(effect['text'].strip())
             and isinstance(effect.get('set_flags'), dict) and bool(effect['set_flags'])
             and all(isinstance(k, str) and k and not k.startswith('_') and v is True
                     for k, v in effect['set_flags'].items())
             and authored.get('type') == 'custom'
             and isinstance(conditions, dict) and set(conditions) <= allowed_conditions
             and all(isinstance(v, list) and all(isinstance(k, str) and k for k in v)
                     for v in conditions.values())
             and set(effect['set_flags']) <= set(conditions.get('excludes_flags', [])))
    available = valid and _affordance_passes_conditions(authored, scene.get('id', ''), session, world)
    text = effect['text'] if available else 'That choice is not available here. No consequence was applied.'
    return ExplorationEngineResult(
        kind='custom', action_id=aid, label=authored['label'], prompt=authored.get('prompt') or authored['label'],
        success=bool(available), resolved_transition=False, target_scene_id=None, clue_id=None,
        world_updates={'set_flags': copy.deepcopy(effect['set_flags'])} if available else None,
        hint=text, metadata={'authored_consequence': True, 'trusted_text': text}).to_dict()


def trusted_text(resolution):
    meta = (resolution or {}).get('metadata') or {}
    return meta.get('trusted_text') if (resolution or {}).get('kind') == 'custom' and meta.get('authored_consequence') is True else None
