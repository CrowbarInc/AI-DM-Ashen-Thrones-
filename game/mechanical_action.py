"""Campaign-selected mechanical actions. The ruleset proposes; the core commits.

Ordinary chat calls this module for one social skill check. A ruleset cannot
reach storage from here: this module loads the campaign binding, asks that
ruleset to resolve, and is the only writer of the session ledger and the NPC
stance record that check owns.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from game.campaign_ruleset import resolve_campaign_ruleset
from game.mechanical_action_contract import (
    parse_request, request_digest, validate_proposed_changes,
)
from game.ruleset_contract import PolicyEvaluation, to_plain
from game import ruleset_registry as registry

_RESOLUTION_STATUS = frozenset({
    'authorized', 'rejected', 'unresolved', 'unsupported', 'invalid', 'unknown',
})
_JSON_SCALARS = (str, int, bool, type(None))


def _publication(committed: bool, explanation: str) -> dict[str, Any]:
    if committed:
        return {'published': True, 'reason': 'committed_outcome', 'text': explanation}
    return {'published': False, 'reason': 'outcome_not_committed', 'text': ''}


def _result(request, *, status, reason, campaign_id=None, ruleset_id=None, ruleset_version=None,
            capability=None, capability_status='not_applicable', validation_status='not_applicable',
            authorization_status='not_applicable', commit_status='not_attempted',
            mechanical_outcome=None, proposed=None, preconditions=None, explanation='',
            committed_marker=None, implementation=None, discarded=0, retry='none') -> dict[str, Any]:
    committed = commit_status == 'committed'
    return {
        'status': status,
        'reason': reason,
        'action_id': None if request is None else request.get('action_id'),
        'campaign_id': campaign_id,
        'ruleset_id': ruleset_id,
        'ruleset_version': ruleset_version,
        'capability': capability if capability is not None else (None if request is None else request.get('action_type')),
        'capability_status': capability_status,
        'validation_status': validation_status,
        'authorization_status': authorization_status,
        'commit_status': commit_status,
        'mechanical_outcome': mechanical_outcome or {},
        'proposed_state_changes': list(proposed or []),
        'required_preconditions': list(preconditions or []),
        'explanation': explanation,
        'publication': _publication(committed, explanation if committed else ''),
        'retry': retry,
        'committed_marker': committed_marker if committed else None,
        'implementation': implementation,
        'discarded_proposal_count': discarded,
    }


def _binding_failure(request, found: Mapping[str, Any]) -> dict[str, Any]:
    status = found.get('status')
    reason = found.get('reason') or 'invalid_binding'
    if status == 'missing':
        status, reason = 'invalid', 'missing_binding'
    elif status == 'unknown':
        status = 'unknown'
    elif status == 'unsupported':
        status = 'unsupported'
    elif status != 'invalid':
        status, reason = 'invalid', reason
    binding = found.get('binding') if isinstance(found.get('binding'), dict) else {}
    return _result(
        request, status=status, reason=reason, campaign_id=found.get('campaign_id') or request.get('campaign_reference'),
        ruleset_id=binding.get('ruleset_id'), ruleset_version=binding.get('ruleset_version'),
        capability_status='not_applicable', validation_status='valid', explanation=reason)


def _ledger(session: Mapping[str, Any]):
    if 'mechanical_action_ledger' not in session:
        return {'revision': 0, 'markers': {}}
    raw = session.get('mechanical_action_ledger')
    if (not isinstance(raw, dict) or type(raw.get('revision')) is not int or raw['revision'] < 0
            or not isinstance(raw.get('markers'), dict)):
        return None
    if any(type(value) is not str for value in raw['markers'].values()):
        return None
    return {'revision': raw['revision'], 'markers': dict(raw['markers'])}


def _receipts(session: Mapping[str, Any]):
    if 'mechanical_action_receipts' not in session:
        return {}
    raw = session.get('mechanical_action_receipts')
    if not isinstance(raw, dict):
        return None
    return raw


def _json_outcome(value: Any, depth: int = 0) -> bool:
    if depth > 8:
        return False
    if type(value) in _JSON_SCALARS:
        return True
    if type(value) is str:
        return len(value) <= 4000
    if type(value) is list:
        return all(_json_outcome(item, depth + 1) for item in value)
    if type(value) is dict:
        return all(type(key) is str and _json_outcome(item, depth + 1) for key, item in value.items())
    return False


def _from_policy(authority, request, context) -> dict[str, Any]:
    """Policy evaluation cannot authorize a commit or propose a mutation."""
    del context
    capability = request['action_type']
    disposition = authority.capability_disposition(capability)
    if disposition != 'supported':
        reason = {'unsupported': 'capability_not_supported', 'unknown': 'unknown_capability',
                  'invalid': 'malformed_capability'}.get(disposition, 'unknown_capability')
        return {'status': disposition if disposition in _RESOLUTION_STATUS else 'unknown',
                'mechanical_outcome': {'delegated': False}, 'proposed_state_changes': [],
                'required_preconditions': [], 'explanation': reason}
    evaluation = authority.evaluate_policy(capability, request.get('parameters') or {}, {})
    if not isinstance(evaluation, PolicyEvaluation):
        return {'status': 'invalid', 'mechanical_outcome': {}, 'proposed_state_changes': [],
                'required_preconditions': [], 'explanation': 'authority_result_malformed'}
    payload = to_plain(evaluation.ruleset_result)
    if evaluation.status == 'mechanically_unresolved':
        status = 'unresolved'
    elif evaluation.status == 'supported':
        # Recognized policy is not permission to mutate or publish success.
        status = 'rejected'
    elif evaluation.status in _RESOLUTION_STATUS:
        status = evaluation.status
    else:
        status = 'invalid'
    preconditions = payload.get('missing_contribution_data') if isinstance(payload, dict) else []
    if not isinstance(preconditions, list):
        preconditions = []
    return {'status': status, 'mechanical_outcome': payload if isinstance(payload, dict) else {},
            'proposed_state_changes': [], 'required_preconditions': [item for item in preconditions if type(item) is str],
            'explanation': evaluation.reason}


def _normalize(produced, *, allow_proposals: bool) -> dict[str, Any] | None:
    if not isinstance(produced, dict) or produced.get('status') not in _RESOLUTION_STATUS:
        return None
    changes = produced.get('proposed_state_changes', [])
    outcome = produced.get('mechanical_outcome', {})
    preconditions = produced.get('required_preconditions', [])
    if not isinstance(changes, list) or not isinstance(outcome, dict) or not _json_outcome(outcome):
        return None
    if not isinstance(preconditions, list) or any(type(item) is not str for item in preconditions):
        return None
    explanation = produced.get('explanation') if type(produced.get('explanation')) is str else ''
    visible = copy.deepcopy(changes)
    if produced['status'] != 'authorized' or not allow_proposals:
        discarded = len(visible)
        applicable = []
    else:
        discarded = 0
        applicable = visible
    return {'status': produced['status'], 'changes': applicable, 'visible_proposals': visible,
            'outcome': copy.deepcopy(outcome), 'preconditions': list(preconditions),
            'explanation': explanation, 'discarded': discarded}


def _resolve(authority, request, context) -> dict[str, Any] | None:
    method = getattr(authority, 'resolve_mechanical_action', None)
    if callable(method):
        return _normalize(method(request, context), allow_proposals=True)
    return _normalize(_from_policy(authority, request, context), allow_proposals=False)


def _actor_problem(character: Mapping[str, Any], actor: Mapping[str, str]) -> str | None:
    if actor.get('kind') != 'character' or character.get('id') != actor.get('id'):
        return 'unknown_actor'
    return None


def _target_problem(character: Mapping[str, Any], session: Mapping[str, Any], targets) -> str | None:
    inventory = {item.get('id') for item in character.get('inventory') or [] if isinstance(item, dict)}
    for target in targets:
        if target['kind'] == 'character' and target['id'] != character.get('id'):
            return 'unknown_target'
        if target['kind'] == 'inventory_item' and target['id'] not in inventory:
            return 'unknown_target'
        if target['kind'] == 'scene' and target['id'] != session.get('active_scene_id'):
            return 'unknown_target'
    return None


def _replay(request, receipt, binding, implementation) -> dict[str, Any]:
    marker = receipt.get('marker') if type(receipt.get('marker')) is str else None
    explanation = receipt.get('explanation') if type(receipt.get('explanation')) is str else ''
    outcome = receipt.get('mechanical_outcome') if isinstance(receipt.get('mechanical_outcome'), dict) else {}
    return _result(
        request, status='committed', reason='durable_replay', campaign_id=request['campaign_reference'],
        ruleset_id=binding['ruleset_id'], ruleset_version=binding['ruleset_version'],
        capability=request['action_type'], capability_status='supported', validation_status='valid',
        authorization_status='authorized', commit_status='committed', mechanical_outcome=outcome,
        explanation=explanation, committed_marker=marker, implementation=implementation, retry='replay')


def _apply_npc_check(session: dict[str, Any], change: Mapping[str, Any]) -> None:
    """Apply one validated stance check on the session copy. The caller saves once."""
    value = change['value']
    root = session.get('npc_runtime')
    if not isinstance(root, dict):
        root = {}
        session['npc_runtime'] = root
    current = root.get(change['target_id'])
    row = dict(current) if isinstance(current, dict) else {}
    for field_name in ('attitude', 'trust', 'fear', 'suspicion'):
        if type(row.get(field_name)) is not int:
            row[field_name] = 0
    stance_field = value['stance_field']
    if stance_field:
        row[stance_field] = max(-5, min(5, row[stance_field] + value['stance_delta']))
    recorded = {key: value[key] for key in (
        'kind', 'skill', 'roll', 'modifier', 'total', 'difficulty', 'success', 'stance_field', 'stance_delta')}
    recorded['stance_after'] = row.get(stance_field) if stance_field else None
    row['last_social_check'] = recorded
    row['last_interaction_turn'] = session.get('turn_counter')
    root[change['target_id']] = row


def _commit(request, session_binding, authority, resolution, marker, stance_change=None) -> dict[str, Any]:
    from game import storage
    from game.integrated_play import ordered_turn
    digest = request_digest(request)
    try:
        with ordered_turn(str(storage.DATA_DIR), mutating=True):
            session = storage.load_session()
            receipts = _receipts(session)
            ledger = _ledger(session)
            if receipts is None or ledger is None:
                return _result(request, status='invalid', reason='ledger_unreadable',
                               campaign_id=request['campaign_reference'], validation_status='invalid',
                               ruleset_id=session_binding['ruleset_id'], ruleset_version=session_binding['ruleset_version'],
                               implementation=getattr(authority, 'implementation', None),
                               explanation='ledger_unreadable')
            existing = receipts.get(request['action_id'])
            if isinstance(existing, dict):
                if existing.get('request_digest') == digest:
                    return _replay(request, existing, session_binding, getattr(authority, 'implementation', None))
                return _result(request, status='conflict', reason='duplicate_action_id',
                               campaign_id=request['campaign_reference'], ruleset_id=session_binding['ruleset_id'],
                               ruleset_version=session_binding['ruleset_version'], capability_status='supported',
                               validation_status='valid', authorization_status='authorized', commit_status='conflict',
                               implementation=getattr(authority, 'implementation', None), explanation='duplicate_action_id')
            if request['expected_state_revision'] is not None and request['expected_state_revision'] != ledger['revision']:
                return _result(request, status='conflict', reason='stale_revision',
                               campaign_id=request['campaign_reference'], ruleset_id=session_binding['ruleset_id'],
                               ruleset_version=session_binding['ruleset_version'], capability_status='supported',
                               validation_status='conflict', authorization_status='authorized', commit_status='conflict',
                               proposed=resolution['changes'], implementation=getattr(authority, 'implementation', None),
                               explanation='stale_revision')
            updated = copy.deepcopy(session)
            before = ledger['revision']
            markers = dict(ledger['markers'])
            if stance_change is not None:
                _apply_npc_check(updated, stance_change)
                marker = 'social_check'
            markers[request['action_id']] = marker
            receipt = {
                'version': 1, 'action_id': request['action_id'], 'request_digest': digest,
                'ruleset_id': session_binding['ruleset_id'], 'ruleset_version': session_binding['ruleset_version'],
                'capability': request['action_type'], 'implementation': getattr(authority, 'implementation', None),
                'status': 'committed', 'ledger_revision_before': before, 'ledger_revision_after': before + 1,
                'marker': marker, 'explanation': resolution['explanation'],
                'mechanical_outcome': resolution['outcome'],
            }
            updated['mechanical_action_ledger'] = {'revision': before + 1, 'markers': markers}
            updated_receipts = dict(receipts)
            updated_receipts[request['action_id']] = receipt
            updated['mechanical_action_receipts'] = updated_receipts
            storage.save_session(updated)
    except (OSError, RuntimeError):
        return _result(request, status='rejected', reason='commit_failed', campaign_id=request['campaign_reference'],
                       ruleset_id=session_binding['ruleset_id'], ruleset_version=session_binding['ruleset_version'],
                       capability_status='supported', validation_status='valid', authorization_status='authorized',
                       commit_status='failed', mechanical_outcome=resolution['outcome'], proposed=resolution['changes'],
                       explanation=resolution['explanation'], implementation=getattr(authority, 'implementation', None))
    return _result(request, status='committed', reason='committed', campaign_id=request['campaign_reference'],
                   ruleset_id=session_binding['ruleset_id'], ruleset_version=session_binding['ruleset_version'],
                   capability_status='supported', validation_status='valid', authorization_status='authorized',
                   commit_status='committed', mechanical_outcome=resolution['outcome'], proposed=[resolution['change']] if resolution.get('change') else resolution['changes'],
                   preconditions=resolution['preconditions'], explanation=resolution['explanation'],
                   committed_marker=marker, implementation=getattr(authority, 'implementation', None))


def public_action(result: Mapping[str, Any]) -> dict[str, Any]:
    """Player-visible action fields. Ruleset payloads and resolver paths stay internal."""
    publication = result.get('publication') if isinstance(result.get('publication'), dict) else {}
    body = {
        'status': result.get('status') if type(result.get('status')) is str else '',
        'reason': result.get('reason') if type(result.get('reason')) is str else '',
        'action_id': result.get('action_id') if type(result.get('action_id')) is str else '',
        'campaign_id': result.get('campaign_id') if type(result.get('campaign_id')) is str else '',
        'ruleset_id': result.get('ruleset_id') if type(result.get('ruleset_id')) is str else '',
        'ruleset_version': result.get('ruleset_version') if type(result.get('ruleset_version')) is str else '',
        'capability': result.get('capability') if type(result.get('capability')) is str else '',
        'capability_status': result.get('capability_status') if type(result.get('capability_status')) is str else '',
        'validation_status': result.get('validation_status') if type(result.get('validation_status')) is str else '',
        'authorization_status': result.get('authorization_status') if type(result.get('authorization_status')) is str else '',
        'commit_status': result.get('commit_status') if type(result.get('commit_status')) is str else '',
        'explanation': result.get('explanation') if type(result.get('explanation')) is str else '',
        'retry': result.get('retry') if type(result.get('retry')) is str else '',
        'publication': {
            'published': publication.get('published') is True,
            'reason': publication.get('reason') if type(publication.get('reason')) is str else '',
            'text': publication.get('text') if type(publication.get('text')) is str else '',
        },
    }
    if type(result.get('committed_marker')) is str:
        body['committed_marker'] = result['committed_marker']
    return body


def http_status_for(result: Mapping[str, Any]) -> int:
    if result.get('status') == 'invalid':
        return 422
    if result.get('status') == 'conflict' or result.get('commit_status') == 'failed':
        return 409
    return 200


def execute_mechanical_action(payload: Any) -> dict[str, Any]:
    """Run one campaign-scoped mechanical action. Unsupported work does not commit."""
    request, problem = parse_request(payload)
    if problem is not None:
        return _result(request, status='conflict' if problem == 'request_ruleset_conflict' else 'invalid',
                       reason=problem, validation_status='invalid', explanation=problem)
    found = resolve_campaign_ruleset(request['campaign_reference'])
    if found.get('status') != 'valid':
        return _binding_failure(request, found)
    binding = found['binding']
    if request['ruleset_echo'] and (request['ruleset_id'] != binding['ruleset_id']
                                    or request['ruleset_version'] != binding['ruleset_version']):
        return _result(request, status='conflict', reason='request_ruleset_conflict',
                       campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                       ruleset_version=binding['ruleset_version'], validation_status='valid',
                       explanation='request_ruleset_conflict')
    selection = registry.get_ruleset(binding['ruleset_id'], binding['ruleset_version'])
    authority = selection.authority
    implementation = None if authority is None else getattr(authority, 'implementation', None)
    if authority is None:
        return _result(request, status='unsupported', reason=selection.reason or 'ruleset_unavailable',
                       campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                       ruleset_version=binding['ruleset_version'], explanation=selection.reason or 'ruleset_unavailable')
    from game import storage
    try:
        session = storage.load_session()
        character = storage.load_character()
    except (OSError, ValueError):
        return _result(request, status='invalid', reason='persisted_campaign_unreadable',
                       campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                       ruleset_version=binding['ruleset_version'], validation_status='invalid',
                       implementation=implementation, explanation='persisted_campaign_unreadable')
    if session.get('campaign_run_id') != request['campaign_reference']:
        return _result(request, status='invalid', reason='campaign_mismatch',
                       campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                       ruleset_version=binding['ruleset_version'], validation_status='invalid',
                       implementation=implementation, explanation='campaign_mismatch')
    ledger = _ledger(session)
    receipts = _receipts(session)
    if ledger is None or receipts is None:
        return _result(request, status='invalid', reason='ledger_unreadable',
                       campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                       ruleset_version=binding['ruleset_version'], validation_status='invalid',
                       implementation=implementation, explanation='ledger_unreadable')
    # A committed receipt is authoritative. Restart does not re-resolve it.
    existing = receipts.get(request['action_id'])
    if isinstance(existing, dict):
        if existing.get('request_digest') == request_digest(request):
            return _replay(request, existing, binding, existing.get('implementation') or implementation)
        return _result(request, status='conflict', reason='duplicate_action_id',
                       campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                       ruleset_version=binding['ruleset_version'], validation_status='valid',
                       commit_status='conflict', implementation=implementation, explanation='duplicate_action_id')
    discovery = registry.discover_capability(binding['ruleset_id'], binding['ruleset_version'], request['action_type'])
    if discovery.status != 'supported':
        return _result(request, status=discovery.status, reason=discovery.reason,
                       campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                       ruleset_version=binding['ruleset_version'], capability_status=discovery.status,
                       validation_status='valid', implementation=implementation, explanation=discovery.reason)
    actor_problem = _actor_problem(character, request['actor_reference'])
    if actor_problem is not None:
        return _result(request, status='invalid', reason=actor_problem, campaign_id=request['campaign_reference'],
                       ruleset_id=binding['ruleset_id'], ruleset_version=binding['ruleset_version'],
                       capability_status='supported', validation_status='invalid', implementation=implementation,
                       explanation=actor_problem)
    target_problem = _target_problem(character, session, request['target_references'])
    npc_targets = [item for item in request['target_references'] if item['kind'] == 'npc']
    roster = []
    scene = None
    if npc_targets or request['action_type'] == 'social_skill_check':
        try:
            world = storage.load_world()
            scene = storage.load_active_scene()
        except (OSError, ValueError):
            return _result(request, status='invalid', reason='persisted_campaign_unreadable',
                           campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                           ruleset_version=binding['ruleset_version'], validation_status='invalid',
                           implementation=implementation, explanation='persisted_campaign_unreadable')
        from game.present_npc import present_roster
        roster = present_roster(scene, world, session)
    npc_ids = {str(row.get('id')) for row in roster if row.get('id')}
    if any(item['id'] not in npc_ids for item in npc_targets):
        target_problem = 'unknown_target'
    if target_problem is not None:
        return _result(request, status='invalid', reason=target_problem, campaign_id=request['campaign_reference'],
                       ruleset_id=binding['ruleset_id'], ruleset_version=binding['ruleset_version'],
                       capability_status='supported', validation_status='invalid', implementation=implementation,
                       explanation=target_problem)
    if request['expected_state_revision'] is not None and request['expected_state_revision'] != ledger['revision']:
        return _result(request, status='conflict', reason='stale_revision', campaign_id=request['campaign_reference'],
                       ruleset_id=binding['ruleset_id'], ruleset_version=binding['ruleset_version'],
                       capability_status='supported', validation_status='conflict', commit_status='conflict',
                       implementation=implementation, explanation='stale_revision')
    npc_facts = {}
    current_stance = {}
    if len(npc_targets) == 1:
        from game.present_npc import npc_check_facts
        matched = next(row for row in roster if str(row.get('id')) == npc_targets[0]['id'])
        npc_facts = npc_check_facts(scene, npc_targets[0]['id'], matched)
        runtime_root = session.get('npc_runtime') if isinstance(session.get('npc_runtime'), dict) else {}
        runtime = runtime_root.get(npc_targets[0]['id']) if isinstance(runtime_root, dict) else {}
        if isinstance(runtime, dict):
            current_stance = {key: runtime.get(key) if type(runtime.get(key)) is int else 0
                              for key in ('attitude', 'trust', 'fear', 'suspicion')}
    condition_definitions = {}
    if request['action_type'] == 'social_skill_check':
        try:
            loaded = storage.load_conditions()
        except (OSError, ValueError):
            loaded = {}
        condition_definitions = loaded if isinstance(loaded, dict) else {}
    skills = character.get('skills') if isinstance(character.get('skills'), dict) else {}
    context = {'campaign_id': request['campaign_reference'], 'actor_reference': request['actor_reference'],
               'target_references': request['target_references'], 'ledger_revision': ledger['revision'],
               'character': {'id': character.get('id'), 'skills': dict(skills),
                             'conditions': list(character.get('conditions') or []) if isinstance(character.get('conditions'), list) else []},
               'condition_definitions': condition_definitions, 'npc': npc_facts,
               'current_stance': current_stance, 'scene_id': session.get('active_scene_id')}
    try:
        resolution = _resolve(authority, request, context)
    except RuntimeError:
        return _result(request, status='rejected', reason='resolution_interrupted',
                       campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                       ruleset_version=binding['ruleset_version'], capability_status='supported',
                       validation_status='valid', authorization_status='rejected', implementation=implementation,
                       explanation='resolution_interrupted')
    if resolution is None:
        return _result(request, status='invalid', reason='authority_result_malformed',
                       campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                       ruleset_version=binding['ruleset_version'], capability_status='supported',
                       validation_status='invalid', implementation=implementation,
                       explanation='authority_result_malformed')
    if resolution['status'] != 'authorized':
        return _result(request, status=resolution['status'], reason=resolution['explanation'] or resolution['status'],
                       campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                       ruleset_version=binding['ruleset_version'], capability_status='supported',
                       validation_status='valid', authorization_status=resolution['status'],
                       mechanical_outcome=resolution['outcome'], proposed=resolution['visible_proposals'],
                       preconditions=resolution['preconditions'], explanation=resolution['explanation'],
                       implementation=implementation, discarded=resolution['discarded'])
    checked = validate_proposed_changes(resolution['changes'], campaign_id=request['campaign_reference'],
                                        revision=ledger['revision'], npc_ids=npc_ids)
    if checked['outcome'] == 'empty':
        return _result(request, status='authorized', reason='authorized_no_change',
                       campaign_id=request['campaign_reference'], ruleset_id=binding['ruleset_id'],
                       ruleset_version=binding['ruleset_version'], capability_status='supported',
                       validation_status='valid', authorization_status='authorized',
                       mechanical_outcome=resolution['outcome'], explanation=resolution['explanation'],
                       implementation=implementation)
    if checked['outcome'] != 'valid':
        terminal = {'invalid': 'invalid', 'rejected': 'rejected', 'conflict': 'conflict'}[checked['outcome']]
        return _result(request, status=terminal, reason=checked['reason'], campaign_id=request['campaign_reference'],
                       ruleset_id=binding['ruleset_id'], ruleset_version=binding['ruleset_version'],
                       capability_status='supported', validation_status=checked['outcome'],
                       authorization_status='authorized', commit_status='conflict' if terminal == 'conflict' else 'not_attempted',
                       mechanical_outcome=resolution['outcome'], proposed=resolution['changes'],
                       explanation=checked['reason'], implementation=implementation)
    resolution['change'] = checked['change']
    return _commit(request, binding, authority, resolution, checked['marker'],
                   stance_change=checked['change'] if checked.get('kind') == 'stance' else None)
