"""Conservative overlay evidence reconciliation; never grants new scene authority.

The legacy gateway is shape-only. Its receipt alone cannot authorize new facts.
Exact accepted-opening and persisted authored-social projections are recognized.
Other mutations remain explicit stop conditions.
"""
import copy
import hashlib
import json


def payload(doc):
    return doc.get('payload', doc) if isinstance(doc, dict) else doc


def empty_overlay(sid):
    return dict(scene_id=sid, visible_facts_add=[], discovered_clues=[],
                state_flags={}, runtime_entities=[], mutations={})


def _valid_overlay(value, sid):
    return (isinstance(value, dict) and value.get('scene_id') == sid
            and all(isinstance(value.get(k), type(v)) for k, v in empty_overlay(sid).items()))


def _bounded(value):
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if len(raw) <= 2048:
        return value
    return {'preview': raw[:2048], 'truncated': True, 'characters': len(raw),
            'omitted_characters': len(raw)-2048,
            'sha256': hashlib.sha256(raw.encode()).hexdigest()}


def compare_overlays(before, after, *, accepted=False, opening_response=None, ordinary_action=None, turn_response=None):
    """Compare snapshots, not response session mirrors. Missing evidence fails closed.

    Existing overlays must be preserved exactly except for the proven active-scene
    projection. Missing root may initialize; malformed existing state may not heal
    silently. No overlay metadata is excluded as bookkeeping.
    """
    a = payload(before.get('session.json', {})) or {}
    b = payload(after.get('session.json', {})) or {}
    old, new = a.get('runtime_scene_overlays', {}), b.get('runtime_scene_overlays', {})
    if old == new and ('runtime_scene_overlays' in a) == ('runtime_scene_overlays' in b):
        return {'integrity': True, 'changes': [], 'omitted_entries': 0, 'total_changes': 0}
    sid = a.get('active_scene_id')
    response = opening_response or {}
    gm = response.get('gm_output') or {}
    native = (gm.get('metadata') or {}).get('accepted_response') or {}
    hard = native.get('hard_validation') or {}
    resolution = response.get('resolution') or {}
    scene_doc = payload(before.get('scenes/'+str(sid)+'.json', {})) or {}
    scene = scene_doc.get('scene') or {}
    su = gm.get('scene_update')
    reason = 'authority_evidence_unavailable'
    expected = copy.deepcopy(old)
    proven = False
    receipt = None
    if not isinstance(old, dict) or not isinstance(new, dict):
        reason = 'malformed_overlay_root'
    elif not accepted:
        reason = 'opening_not_accepted_or_ordinary_turn_authority_unavailable'
        if ordinary_action is not None and turn_response is not None:
            from tools.playtest.social_overlay_authority import social_overlay_projection
            projection = social_overlay_projection(before, after, ordinary_action, turn_response)
            if projection is not None:
                expected, receipt = projection
                proven, reason = True, 'authored_social_clue_projection'
    elif not (response.get('ok') is True and b.get('campaign_started') is True
              and a.get('campaign_started') is not True
              and sid == b.get('active_scene_id') == scene.get('id')
              and resolution.get('kind') == 'scene_opening'
              and hard.get('hard_valid') is True
              and native.get('authority_result') == 'accepted'):
        reason = 'accepted_opening_commit_evidence_missing'
    else:
        # An empty lazy overlay adds shape only. Substantive effects require the
        # structured proposal AND a new native adoption receipt in persisted state.
        traces = [t for t in b.get('debug_traces', []) if t not in a.get('debug_traces', [])
                  and isinstance(t, dict) and t.get('owner_module') == 'game.api'
                  and t.get('operation') == 'apply_gm_scene_update_layers'
                  and t.get('scene_id') == sid and t.get('adoption_status') == 'authoritative_adopted'
                  and t.get('gateway_decision') == 'allow_validated_legacy_scene_update'
                  and t.get('gateway_shape_validation_enforced') is True
                  and (t.get('resolution') or {}).get('kind') == 'scene_opening']
        expected.setdefault(sid, empty_overlay(sid))
        if not _valid_overlay(expected[sid], sid):
            reason = 'malformed_active_overlay'
        elif not su:
            proven, reason = True, 'accepted_opening_empty_initialization'
        elif not isinstance(su, dict) or set(su)-{'visible_facts_add', 'discoverable_clues_add', 'hidden_facts_add', 'mode'}:
            reason = 'unsupported_scene_update_shape'
        elif (not all(isinstance(su.get(k, []), list) and all(isinstance(v, str) for v in su.get(k, []))
                      for k in ('visible_facts_add', 'discoverable_clues_add', 'hidden_facts_add'))
              or su.get('discoverable_clues_add') or su.get('hidden_facts_add')):
            reason = 'unsupported_or_nonpublic_scene_update'
        else:
            public = {v.casefold().removesuffix('.') for k in ('visible_facts', 'opening_seed_facts')
                      for v in scene.get(k, []) if isinstance(v, str)}
            if any(v.casefold().removesuffix('.') not in public for v in su.get('visible_facts_add', [])):
                reason = 'scene_update_not_authored_public_fact'
            elif su.get('mode') and su['mode'] != scene.get('mode'):
                reason = 'scene_update_changes_authored_mode'
            elif len(traces) != 1 or any(traces[0].get(k+'_count') != len(su.get(k, []))
                                       for k in ('visible_facts_add', 'discoverable_clues_add', 'hidden_facts_add')):
                reason = 'native_adoption_receipt_missing_or_mismatched'
            elif traces[0].get('mode_present') != bool(su.get('mode')):
                reason = 'native_mode_receipt_mismatched'
            else:
                receipt = traces[0]
                overlay = expected[sid]
                for fact in su.get('visible_facts_add', []):
                    if fact not in overlay.setdefault('visible_facts_add', []):
                        overlay['visible_facts_add'].append(fact)
                mutations = overlay.setdefault('mutations', {})
                mutations.setdefault('discoverable_clues_add', [])
                mutations.setdefault('hidden_facts_add', [])
                if su.get('mode'):
                    mutations['mode'] = su['mode']
                proven, reason = True, 'accepted_opening_authored_scene_update'
    changes = []

    def walk(x, y, xp, yp, path, scene_id=None):
        if xp == yp and x == y:
            return
        if not xp and path == 'session.json:/runtime_scene_overlays' and isinstance(y, dict):
            for key in sorted(y):
                walk(None, y[key], False, True, path+'/'+key.replace('~', '~0').replace('/', '~1'), key)
            if y:
                return
        if xp and yp and isinstance(x, dict) and isinstance(y, dict):
            for key in sorted(x.keys() | y.keys()):
                walk(x.get(key), y.get(key), key in x, key in y,
                     path+'/'+key.replace('~', '~0').replace('/', '~1'), scene_id or key)
            return
        allowed = proven and scene_id == sid and isinstance(new, dict) and new.get(sid) == expected.get(sid)
        changes.append({'path': path, 'change': 'added' if not xp else 'removed' if not yp else 'modified',
                        'before': _bounded(x), 'after': _bounded(y), 'scene_id': scene_id,
                        'overlay_id': scene_id, 'classification': 'authorized_gameplay_mutation' if allowed else 'uncertain_or_unauthorized_mutation',
                        'reason': reason if allowed or not proven else 'outside_exact_authorized_projection',
                        'authority_evidence': {'source': ('game.clues.apply_socially_revealed_leads; game.clues.ensure_scene_has_minimum_actionable_lead'
                                                       if receipt and receipt.get('action_id') else 'game.api._apply_post_gm_updates; game.storage'),
                                               'native_operation': receipt.get('operation') if receipt else None,
                                               'authored_scene': 'scenes/'+str(sid)+'.json',
                                               'ordinary_turn': receipt if receipt and receipt.get('action_id') else None} if allowed else None})
    walk(old, new, 'runtime_scene_overlays' in a, 'runtime_scene_overlays' in b,
         'session.json:/runtime_scene_overlays')
    return {'integrity': all(c['classification'] == 'authorized_gameplay_mutation' for c in changes),
            'changes': changes[:100], 'omitted_entries': max(0, len(changes)-100),
            'total_changes': len(changes), 'snapshots_preserved': True}
