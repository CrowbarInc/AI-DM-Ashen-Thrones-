"""Exact offline evidence check for an authored physical-clue overlay projection."""
import copy
from tools.playtest.overlays import payload, empty_overlay


def investigation_overlay_projection(before, after, action, response):
    a, b = (payload(d.get('session.json', {})) or {} for d in (before, after))
    sid = a.get('active_scene_id')
    logs_a, logs_b = (d.get('session_log.jsonl') or [] for d in (before, after))
    if (not action or action.get('interaction_category') != 'investigate'
            or a.get('campaign_started') is not True or b.get('campaign_started') is not True
            or b.get('active_scene_id') != sid
            or b.get('turn_counter') != a.get('turn_counter', 0) + 1
            or len(logs_b) != len(logs_a) + 1 or logs_b[:-1] != logs_a):
        return None
    turn = logs_b[-1]
    res = turn.get('resolution') or {}
    public_res = response.get('resolution') or {}
    native = ((turn.get('gm_output') or {}).get('metadata') or {}).get('accepted_response') or {}
    if (turn.get('player_input') != action.get('player_input')
            or res.get('kind') != 'discover_clue' or res.get('success') is not True
            or res.get('resolved_transition') or res.get('target_scene_id')
            or (res.get('skill_check') or {}).get('success') is False
            or (native.get('hard_validation') or {}).get('hard_valid') is not True
            or any(public_res.get(k) != res.get(k) for k in ('action_id', 'clue_id', 'clue_text', 'discovered_clues', 'success'))):
        return None
    scene = (payload(before.get('scenes/'+str(sid)+'.json', {})) or {}).get('scene') or {}
    target = next((r for r in scene.get('interactables', []) if isinstance(r, dict)
                   and r.get('id') == res.get('interactable_id') == res.get('action_id')), None)
    if (scene.get('id') != sid or not target or target.get('hidden')
            or target.get('visible') is False or target.get('accessible') is False
            or target.get('reveals_clue') != res.get('clue_id')):
        return None
    clue = next((c for c in scene.get('discoverable_clues', []) if isinstance(c, dict)
                 and c.get('id') == target['reveals_clue']), None)
    if not clue or not clue.get('text') or res.get('clue_text') != clue['text'] or res.get('discovered_clues') != [clue['text']]:
        return None
    knowledge = (b.get('clue_knowledge') or {}).get(clue['id']) or {}
    rt = (b.get('scene_runtime') or {}).get(sid) or {}
    if (knowledge.get('state') != 'discovered' or knowledge.get('text') != clue['text']
            or clue['id'] not in rt.get('discovered_clue_ids', [])
            or target['id'] not in rt.get('resolved_interactables', [])):
        return None
    expected = copy.deepcopy(a.get('runtime_scene_overlays') or {})
    overlay = expected.setdefault(sid, empty_overlay(sid))
    if clue['text'] not in overlay['discovered_clues']:
        overlay['discovered_clues'].append(clue['text'])
    return expected, dict(operation='authored_investigation_clue_projection', action_id=res['action_id'],
                          clue_id=clue['id'], source_id=f'scene:{sid}:interactable:{target["id"]}')
