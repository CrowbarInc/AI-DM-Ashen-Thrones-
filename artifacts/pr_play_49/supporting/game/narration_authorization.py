"""Read-only disclosure projection at the narration boundary.

Engine/planner inputs remain private. This projection is applied both by the
context renderer and after GM convenience fields, immediately before transport.
"""
from __future__ import annotations

import copy
from collections.abc import Mapping

from game.authorized_information import revealed_information


def fields(value, keys):
    return {k: copy.deepcopy(value[k]) for k in keys if isinstance(value, Mapping) and k in value}


def project_narration_payload(payload, resolution=None):
    out = copy.deepcopy(payload)
    # These are engine-wide, mixed-authority summaries, not observed events.
    for key in ('world', 'world_state', 'world_progression_summary'):
        out.pop(key, None)
    out['campaign'] = fields(out.get('campaign'), ('title', 'tone', 'character_role', 'magic_style'))
    out['active_interlocutor'] = fields(out.get('active_interlocutor'), ('npc_id', 'display_name'))
    # An NPC's knowledge scope, reliability, affiliation and agenda are engine
    # facts, not facts the player necessarily knows. Selected dialogue remains
    # available via the established decision/answer authority contract.
    out.pop('social_context', None)
    out['instructions'] = [line for line in out.get('instructions', [])
                           if not str(line).startswith(('Engine knowledge_scope tokens', 'Discoverable facts may be hinted'))]
    disclosure_rule = 'Only supplied public, known and newly revealed facts may be described; undiscovered facts are unavailable.'
    if disclosure_rule not in out['instructions']:
        out['instructions'].append(disclosure_rule)
    outcome_rule = (
        'authorized_mechanical_outcome contains engine-authorized changes, not total balances. '
        'Realize those outcomes and authorized information faithfully; add atmosphere, sensory detail, '
        'gestures and personality without establishing further possessions, rewards, injuries, '
        'travel, discoveries or persistent status. Descriptive prose and dialogue grant no mechanics.'
    )
    if outcome_rule not in out['instructions']:
        out['instructions'].append(outcome_rule)
    scene = out.get('scene') or {}
    public = fields(scene.get('public'), ('id', 'location', 'summary', 'mode', 'visible_facts'))
    public['exits'] = [fields(row, ('label', 'direction')) for row in (scene.get('public') or {}).get('exits', [])
                       if isinstance(row, Mapping) and not any(row.get(k) for k in
                           ('hidden', 'requires', 'reveal_requires', 'locked')) and row.get('visible') is not False]
    known = [fields(c, ('id', 'text', 'presentation', 'actionable'))
             for c in scene.get('discovered_clues', []) if isinstance(c, Mapping)]
    out['scene'] = {'public': public, 'discovered_clues': known,
                    'visible_clues': known, 'clue_records': {'discovered': known}}
    out['scene']['intent'] = copy.deepcopy(scene.get('intent') or {})
    out['scene']['pending_leads'] = [fields(row, ('surface',)) for row in scene.get('pending_leads', [])
                                     if isinstance(row, Mapping) and row.get('surface')]
    runtime = scene.get('runtime') or {}
    out['scene']['runtime'] = {'pending_leads': [fields(row, ('surface',)) for row in runtime.get('pending_leads', [])
                                               if isinstance(row, Mapping) and row.get('surface')]}
    out['discoverable_hinting'] = False
    out['authorized_information'] = revealed_information(resolution)
    from game.mechanical_claims import mechanical_outcome

    effects = mechanical_outcome(resolution)
    # NPC/faction mutations can be private even when mechanically real. They
    # remain validator inputs; only separately authorized dialogue/facts ship.
    effects.pop('npc_changes', None)
    effects.pop('faction_changes', None)
    for key in ('items_added', 'items_removed', 'conditions_applied', 'conditions_removed',
                'routes_unlocked', 'objectives_completed'):
        rows = effects.get(key)
        if isinstance(rows, list):
            effects[key] = [fields(row, ('id', 'name', 'quantity', 'label')) if isinstance(row, Mapping) else row
                            for row in rows]
        elif isinstance(rows, Mapping):
            effects[key] = fields(rows, ('id', 'name', 'quantity', 'label'))
    out['authorized_mechanical_outcome'] = effects
    social = (resolution or {}).get('social') or {}
    if isinstance(social, Mapping) and social.get('target_resolved') is True:
        out['authorized_dialogue'] = fields(social.get('topic_revealed'), ('id', 'text'))
    # Raw resolver metadata, hints, checks, world updates and combat internals
    # must not become convenience channels for private prose or thresholds.
    mech = out.get('mechanical_resolution')
    if isinstance(mech, Mapping):
        out['mechanical_resolution'] = fields(mech, (
            'kind', 'success', 'resolved_transition', 'target_scene_id',
            'originating_scene_id', 'action_id', 'interactable_id', 'action_outcome'))
    if isinstance(out.get('skill_check'), Mapping):
        out['skill_check'] = fields(out['skill_check'], ('skill', 'success'))
    out.pop('resolved_combat_action', None)
    # Only player-owned observable combat status, never enemy statistics/checks.
    out['combat'] = fields(out.get('combat'), ('in_combat', 'active', 'round', 'is_player_turn'))
    if isinstance(out.get('clues'), Mapping):
        out['clues'] = {key: [fields(c, ('id', 'text', 'presentation', 'actionable'))
                              for c in rows if isinstance(c, Mapping)]
                        for key, rows in out['clues'].items() if isinstance(rows, list)}
    # All remaining structures are existing public planner contracts. Strip
    # private extension fields recursively; unknown resolver fields above fail closed.
    private = {'gm_only', 'gm_notes', 'gm_guidance', 'hidden_facts', 'hidden_clocks',
               'secret', 'secrets', 'hidden_motivation', 'private_history', 'metadata',
               'undiscovered', 'undiscovered_clues', 'discoverable_clues_locked',
               'reveal_requires', 'dc', 'difficulty', 'roll', 'rolls', 'ambient_pressure_topics',
               'compressed_world_pressures', 'world_pressures', 'ambient_pressures',
               'world_pressure', 'clock_summaries', 'clocks_summary', 'clocks',
               'world_progression_summary', 'current_agenda', 'agenda', 'knowledge_scope',
               'information_reliability'}
    memo = {}
    def clean(value):
        if isinstance(value, Mapping):
            if id(value) in memo:
                return memo[id(value)]
            cleaned = {}
            memo[id(value)] = cleaned
            cleaned.update({k: clean(v) for k, v in value.items()
                            if k not in private and not k.startswith(('_', 'private_', 'hidden_', 'secret_'))})
            # Preserve neutral planner shape without transporting clock/pressure content.
            if 'world_pressure' in value:
                cleaned['world_pressure'] = None
            if 'clock_summaries' in value:
                cleaned['clock_summaries'] = []
            return cleaned
        if isinstance(value, list):
            return [clean(v) for v in value]
        # Same instruction, without colliding with the unchanged SECRET canary probe.
        if isinstance(value, str) and value == 'DO NOT LEAK HIDDEN FACTS / SECRETS':
            return 'DO NOT LEAK HIDDEN FACTS'
        return value
    return clean(out)
