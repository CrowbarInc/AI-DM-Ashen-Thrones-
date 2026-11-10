"""Player HTTP DTOs. Pure, source-specific allowlists; unknown fields fail closed.

This is a publication adapter, never a persistence or gameplay authority. In
particular, discovery text comes from the existing journal/clue publication
owners, not the scene's discoverable_clues catalog. No arbitrary object leaf,
stringification of objects, or internal resolution/GM metadata crosses here.
"""
from __future__ import annotations

import math

# Schema leaves accept only their declared primitive type. Lists and dictionaries
# always have a nested schema; there is deliberately no "any JSON" escape hatch.
TEXT = str
NUMBER = float
BOOL = bool


def project(value, schema):
    if schema is TEXT:
        return value if isinstance(value, str) else ''
    if schema is BOOL:
        return value if isinstance(value, bool) else False
    if schema is NUMBER:
        return value if type(value) in (int, float) and math.isfinite(value) else 0
    if isinstance(schema, list):
        return [project(item, schema[0]) for item in value
                if (isinstance(item, dict) if isinstance(schema[0], dict) else isinstance(item, schema[0]))] if isinstance(value, list) else []
    source = value if isinstance(value, dict) else {}
    return {key: project(source[key], spec) for key, spec in schema.items() if key in source}


ITEM = dict(id=TEXT, name=TEXT, quantity=NUMBER, usable=BOOL)
EFFECT = dict(id=TEXT, name=TEXT, kind=TEXT, duration=NUMBER)
CHARACTER = dict(
    id=TEXT, name=TEXT, **{'class': TEXT}, level=NUMBER, ancestry=TEXT,
    hp=dict(current=NUMBER, max=NUMBER, nonlethal=NUMBER),
    ac=dict(normal=NUMBER, touch=NUMBER, flat_footed=NUMBER),
    initiative_bonus=NUMBER, speed=NUMBER, bab=NUMBER, cmb=NUMBER, cmd=NUMBER,
    ability_scores={k:NUMBER for k in ('str','dex','con','int','wis','cha')},
    saves={k:NUMBER for k in ('fort','ref','will')},
    attacks=[dict(id=TEXT,name=TEXT,attack_bonus=NUMBER,type=TEXT,
                  damage=dict(dice_count=NUMBER,dice_sides=NUMBER,bonus=NUMBER,type=TEXT))],
    conditions=[EFFECT], inventory=[ITEM],
    spells=dict(prepared=[dict(id=TEXT,name=TEXT,cast=BOOL,level=NUMBER)],
                slots={str(k):NUMBER for k in range(10)}),
)
SESSION = dict(session_id=TEXT, campaign_run_id=TEXT, active_scene_id=TEXT, character_name=TEXT,
               response_mode=TEXT, campaign_started=BOOL, turn_counter=NUMBER,
               visited_scene_ids=[TEXT])
SCENE = dict(scene=dict(id=TEXT, location=TEXT, summary=TEXT, mode=TEXT, visible_facts=[TEXT]))
AFFORDANCE = dict(id=TEXT,label=TEXT,type=TEXT,prompt=TEXT,
                  target_scene_id=TEXT,target_id=TEXT,target_location_id=TEXT,
                  targetSceneId=TEXT,targetEntityId=TEXT,targetLocationId=TEXT)
CLUE = dict(text=TEXT,presentation=TEXT)
LEAD = dict(id=TEXT,title=TEXT,summary=TEXT,next_step=TEXT,last_touched_turn=NUMBER)
JOURNAL = dict(known_facts=[TEXT],discovered_clues=[TEXT],unresolved_leads=[TEXT],
               status_effects=[EFFECT],suspicion_flags=[TEXT],
               **{k:[LEAD] for k in ('active_leads','pursued_leads','stale_leads','resolved_leads','obsolete_leads')},
               lead_counts={k:NUMBER for k in ('active','pursued','stale','resolved','obsolete')})
SNAPSHOT = dict(id=TEXT,created_at=TEXT,label=TEXT)
UI = dict(player_can_act=BOOL,campaign_started=BOOL,campaign_can_start=BOOL,
          living_enemies=[dict(id=TEXT,name=TEXT,hp=NUMBER,max_hp=NUMBER)],
          scene_ids=[TEXT],affordances=[AFFORDANCE],
          clues={k:[CLUE] for k in ('known','implicit','explicit','actionable')},
          # Identity/name are public for the existing active-scene roster. Private
          # role, numeric trust and attitude lack a player-knowledge contract.
          scene_npcs=[dict(id=TEXT,name=TEXT,disposition=TEXT)],
          interaction={k:TEXT for k in ('active_interaction_target_id','active_interaction_target_name','active_interaction_kind','interaction_mode')})
STATE = dict(campaign=dict(id=TEXT,title=TEXT),character=CHARACTER,session=SESSION,
             scene=SCENE,combat=dict(in_combat=BOOL,round=NUMBER,active_actor_id=TEXT,player_turn_used=BOOL),
             ui=UI,journal=JOURNAL,player_name=TEXT,campaign_run_id=TEXT,
             save_summary=dict(saved_at=TEXT,save_data_exists=BOOL,active_scene_id=TEXT,discovered_clues=NUMBER,chat_messages=NUMBER),
             snapshots=[SNAPSHOT])


def project_player_state(state):
    """Derive a fresh DTO from an authoritative composed state, without mutation."""
    source = state if isinstance(state, dict) else {}
    out = project(source, STATE)
    character = source.get('character')
    if isinstance(character, dict) and isinstance(character.get('skills'), dict):
        # Skill names are player-sheet identifiers. Only numeric ranks cross;
        # arbitrary nested sheet annotations are never serialized.
        out.setdefault('character', {})['skills'] = {
            k:v for k,v in character['skills'].items()
            if isinstance(k,str) and type(v) in (int,float) and math.isfinite(v)}
    session = source.get('session') if isinstance(source.get('session'),dict) else {}
    if isinstance(out.get('ui'),dict):
        # All authored scene IDs were previously exposed by the scene picker.
        # Restrict to already visited/current locations, never the full catalog.
        known = session.get('visited_scene_ids', [])
        known = [x for x in known if isinstance(x,str)] if isinstance(known,list) else []
        current = session.get('active_scene_id')
        if isinstance(current,str): known.append(current)
        # Retain already projected state for idempotent final response enforcement.
        out['ui']['scene_ids'] = list(dict.fromkeys(known))
    # World structures contain private plans/events without per-item publication
    # metadata. No raw world subtree is authorized. UI tolerates this empty view.
    if 'world' in source: out['world'] = {}
    return out


SAFE_ERRORS = frozenset({
    'Unknown or invalid scene ID.', 'snapshot_id required', 'Snapshot not found',
    'You cannot act right now.', 'You have no attacks available.',
    'Campaign has already started, or the transcript is not empty.',
    'privileged HTTP ui mode is not authorized',
})
SAFE_STATUSES = frozenset({'ok','blocked','already_started','opening_failed','error'})
GENERIC_ERROR = 'Unable to complete this request. Refresh your session and try again.'


def project_player_response(payload):
    """Endpoint envelope plus explicit state and narration. No execution metadata."""
    source = payload if isinstance(payload,dict) else {}
    out = project_player_state(source)
    if 'public_state' in source:
        out['public_state'] = project_player_state(source['public_state'])
    if isinstance(source.get('session_id'),str): out['session_id'] = source['session_id']
    for key in ('ok','campaign_started','gameplay_committed'):
        if isinstance(source.get(key),bool): out[key] = source[key]
    if 'ui_mode' in source: out['ui_mode'] = 'player'
    if isinstance(source.get('status'),str) and source['status'] in SAFE_STATUSES: out['status'] = source['status']
    if 'error' in source:
        error = source['error']
        out['error'] = error if isinstance(error,str) and error in SAFE_ERRORS else GENERIC_ERROR
    if 'gm_output' in source:
        out['gm_output'] = project(source['gm_output'],dict(player_facing_text=TEXT))
    # The frontend uses resolution only for an optional details panel. Do not
    # publish resolver claims, state diffs, hidden discoveries or validation data.
    if 'resolution' in source: out['resolution'] = {}
    if 'snapshot' in source: out['snapshot'] = project(source['snapshot'],SNAPSHOT)
    if 'entries' in source:
        out['entries'] = project(source['entries'],[dict(timestamp=TEXT,player_input=TEXT,gm_output=dict(player_facing_text=TEXT))])
    return out
