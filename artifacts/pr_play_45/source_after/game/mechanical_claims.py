"""Conservative offline consequence checks for the existing semantic validator.

This is a bounded English assertion recognizer, not a semantic proof. It never
uses authored prose, player requests, provider declarations or metadata as grants.
Unrecognized paraphrases remain a documented limitation.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from game.authorized_information import revealed_information


def _norm(value):
    value = str(value).lower().replace('_', ' ')
    numbers = {'a': '1', 'an': '1', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
               'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
               'ten': '10', 'twenty': '20', 'fifty': '50'}
    return ' '.join(numbers.get(w, w) for w in re.findall(r'\w+', value) if w not in {'the'})


def mechanical_outcome(resolution):
    """Adapt existing result fields; absence never grants a change.

    Inventory/currency adapters also support explicit synthetic resolver deltas;
    they do not create a second writable authority or infer changes from state.
    """
    r = resolution if isinstance(resolution, Mapping) else {}
    s = r.get('state_changes') or {}
    if not isinstance(s, Mapping):
        s = {}
    effects = {}
    for key in ('items_added', 'items_removed', 'currency_gained', 'currency_spent',
                'damage_taken', 'health_recovered', 'conditions_applied', 'conditions_removed',
                'routes_unlocked', 'objectives_completed', 'npc_changes', 'faction_changes',
                'encounter_triggered', 'time_advanced'):
        value = s.get(key, r.get(key))
        if value:
            effects[key] = value
    combat = r.get('combat')
    if isinstance(combat, Mapping):
        if r.get('kind') == 'enemy_attack' and combat.get('damage_dealt'):
            effects['damage_taken'] = combat['damage_dealt']
        actor, target = combat.get('actor') or {}, combat.get('target') or {}
        if isinstance(actor, Mapping) and isinstance(target, Mapping) and actor.get('id') and actor.get('id') == target.get('id'):
            for key in ('conditions_applied', 'conditions_removed'):
                if combat.get(key):
                    effects[key] = combat[key]
            if combat.get('healing_applied'):
                effects['health_recovered'] = combat['healing_applied']
    if r.get('success') is not False and r.get('resolved_transition'):
        effects['destination'] = r.get('target_scene_id')
    effects['revealed'] = [v['text'] for v in revealed_information(r)]
    return effects


def _values(value):
    if isinstance(value, Mapping):
        if 'name' in value or 'id' in value:
            return [str(value.get('name') or value.get('id'))]
        return [f'{v} {k}' for k, v in value.items()]
    if isinstance(value, list):
        return [x for row in value for x in _values(row)]
    return [str(value)] if value is not None else []


def _supported(claim, value):
    c = _norm(claim)
    return any(c.removeprefix('1 ') == _norm(v).removeprefix('1 ') for v in _values(value))


def mechanical_fallback(resolution):
    effects = mechanical_outcome(resolution)
    lines = list(effects.get('revealed') or [])
    templates = {'items_added': 'You receive {}.', 'items_removed': 'You lose {}.',
                 'currency_gained': 'You collect {}.', 'currency_spent': 'You spend {}.',
                 'damage_taken': 'You suffer {} damage.', 'health_recovered': 'You recover {} health.',
                 'destination': 'You arrive at {}.', 'conditions_applied': 'You become {}.',
                 'conditions_removed': 'You are no longer {}.',
                 'routes_unlocked': 'You unlock the {}.',
                 'objectives_completed': 'You complete the {}.',
                 'time_advanced': '{} pass.'}
    for key, template in templates.items():
        for value in _values(effects.get(key)):
            lines.append(template.format(value.replace('_', ' ')))
    return ' '.join(lines)


def audit_mechanical_claims(text, resolution):
    effects = mechanical_outcome(resolution)
    claims = []
    # Speech is attributed belief, never an engine event. Adjacent narrator
    # clauses remain checked. No blanket exemption for a hedge elsewhere.
    narrator = re.sub(r'\b(?:says|said|replies|replied|asks|asked|whispers|speculates),?\s*["“][^"”]*["”]', '', str(text or ''), flags=re.I)
    # Normalize common passive/transfer frames into the same consequence audit.
    narrator = re.sub(r'\b([^.!?;]+?)\s+is added to your (?:inventory|pack|bag)\b', r'you receive \1', narrator, flags=re.I)
    narrator = re.sub(r'\b[^.!?;]+?\s+(?:hands|gives|awards) you\s+', 'you receive ', narrator, flags=re.I)
    narrator = re.sub(r'\byou now own\s+', 'you receive ', narrator, flags=re.I)
    # Named actors are not exempt simply because the narrator uses third person.
    # A named-actor consequence needs an actor-specific grant; player-only deltas
    # cannot grant an arbitrary NPC a possession or injury.
    named = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(receives|collects|acquires|loses|spends|suffers|regains|arrives|discovers)\s+([^.!?;]+)')
    for match in named.finditer(narrator):
        if not re.search(r'\b(?:if|might|could|would)\b', match[0], re.I):
            r = resolution if isinstance(resolution, Mapping) else {}
            combat = r.get('combat') or {}
            actor = combat.get('target' if r.get('kind') == 'enemy_attack' else 'actor') or r.get('actor') or {}
            player_name = actor.get('name') if isinstance(actor, Mapping) else None
            if player_name and _norm(player_name) == _norm(match[1]):
                verbs = {'receives': 'receive', 'collects': 'collect', 'acquires': 'acquire',
                         'loses': 'lose', 'spends': 'spend', 'suffers': 'suffer',
                         'regains': 'regain', 'arrives': 'arrive', 'discovers': 'discover'}
                normalized = 'you ' + verbs[match[2]] + ' ' + match[3]
                audit = audit_mechanical_claims(normalized, resolution)
                claims.append(('named_actor_consequence', match[0], not audit['reasons']))
            else:
                claims.append(('named_actor_consequence', match[0], False))
    for sentence in re.split(r'[.!?;\n]+', narrator):
        sentence = sentence.strip()
        if not sentence:
            continue
        # Separate actual assertions from conditional/figurative clauses.
        for clause in re.split(r'\bbut\b|\band\s+(?=you\b)|,\s*(?=you\b)', sentence, flags=re.I):
            if re.search(r'\b(?:if|would|could|might|perhaps|maybe|as if|feels? like|like a|metaphorically)\b', clause, re.I):
                continue
            if re.search(r'\byou\s+(?:do not|don.t|cannot|can.t|never)\b', clause, re.I):
                continue
            m = re.search(r'\byou\s+(?:now\s+)?(receive|collect|gain|acquire|obtain|pick up|are given|lose|spend|pay|hand over)\s+(.+)', clause, re.I)
            if m:
                loss = m[1].lower() in {'lose', 'spend', 'pay', 'hand over'}
                for obj in re.split(r'\s+and\s+', m[2], flags=re.I):
                    # Incidental sensations are not material possessions.
                    if re.fullmatch(r'(?:a |an )?(?:glimpse|impression|sense|chill|breath|moment)(?:\s+of\s+.*)?', obj, re.I):
                        continue
                    currency = bool(re.search(r'\b(?:coins?|currency)\b|\b(?:gold|silver|copper)$', obj, re.I)) and bool(re.match(r'(?:\d+|one|two|three|four|five|ten|twenty|fifty)\b', obj, re.I))
                    key = ('currency_spent' if loss else 'currency_gained') if currency else ('items_removed' if loss else 'items_added')
                    claims.append((key, obj, _supported(obj, effects.get(key))))
            patterns = (
                ('damage_taken', r'\byou\s+(?:take|suffer|sustain)\s+(?:(\w+)\s+(?:points? of\s+)?)?damage\b'),
                ('health_recovered', r'\byou\s+(?:recover|regain|heal)\s+(\w+)\s+(?:health|hp|hit points?)\b'),
                ('destination', r'\byou\s+(?:arrive at|arrive in|enter|reach|travel to)\s+(.+)'),
                ('conditions_applied', r'\byou\s+(?:become|are now)\s+(.+)'),
                ('conditions_removed', r'\byou\s+are no longer\s+(.+)'),
                ('routes_unlocked', r'\byou\s+unlock\s+(.+)'),
                ('objectives_completed', r'\byou\s+complete\s+(.+)'),
                ('revealed', r'\byou\s+(?:discover|uncover|learn|find out)\s+(.+)'),
                ('time_advanced', r'\b(\w+\s+(?:minutes?|hours?|days?))\s+(?:pass|elapse)\b'),
                ('encounter_triggered', r'\b(?:combat|an encounter)\s+(begins|starts)\b'),
            )
            for key, pattern in patterns:
                for match in re.finditer(pattern, clause, re.I):
                    claim = match[1] or ''
                    value = effects.get(key)
                    ok = bool(value) if not claim else _supported(claim, value)
                    if key in {'damage_taken', 'health_recovered'} and claim:
                        ok = _norm(claim) == _norm(value)
                    claims.append((key, claim, ok))
            # Finite, explicit state assertions outside player-owned effects.
            for category, pattern in (
                ('npc_changes', r'\b(.+?)\s+(?:dies|is now dead|becomes hostile|joins your party)\b'),
                ('faction_changes', r'\b(?:the\s+)?(.+?)\s+(?:faction|guild|clan)\s+(?:is now allied|declares war|is destroyed)\b'),
            ):
                match = re.search(pattern, clause, re.I)
                if match:
                    claims.append((category, match[0], _supported(match[0], effects.get(category))))
            uncertain = [v for v in effects['revealed'] if re.search(r'\b(?:may|might|unclear|unknown|cannot|incomplete)\b', v, re.I)]
            if uncertain and re.search(r'\b(?:definitely|certainly|proves|confirmed|without doubt)\b', clause, re.I):
                if any(set(_norm(v).split()) & set(_norm(clause).split()) - {'you', 'is', 'a', 'the', 'be', 'are'} for v in uncertain):
                    claims.append(('certainty', clause, False))
    return {'claims': [{'category': k, 'claim': c, 'supported': ok} for k, c, ok in claims],
            'reasons': list(dict.fromkeys('unsupported_mechanical_claim:' + k for k, _, ok in claims if not ok))}
