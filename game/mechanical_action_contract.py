"""Ruleset-neutral mechanical-action request, proposal, and result shapes.

This module does not select a ruleset, import a ruleset, read campaign
persistence, or apply a mutation. It names the fields the core is allowed to
understand: identity, capability, references, and the authority of a proposal.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping

_ACTION_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,80}$')
_MARKER = re.compile(r'^[a-z][a-z0-9_]{0,63}$')
_REFERENCE_KINDS = frozenset({'character', 'inventory_item', 'scene', 'npc'})

# Closed generic request. Parameters are an opaque JSON object for the ruleset.
REQUEST_FIELDS = frozenset({
    'action_id', 'action_type', 'actor_reference', 'target_references',
    'parameters', 'campaign_reference', 'expected_state_revision',
    'ruleset_id', 'ruleset_version',
})

# Closed proposal. One owner, one operation, one field. Not a patch language.
CHANGE_FIELDS = frozenset({
    'state_owner', 'target_id', 'expected_revision', 'operation', 'field', 'value',
})
LEDGER_OWNER = 'session_mechanical_ledger'
LEDGER_OPERATION = 'record_marker'
LEDGER_FIELD = 'marker'
STANCE_OWNER = 'session_npc_stance'
STANCE_OPERATION = 'record_check'
STANCE_FIELD_NAME = 'stance'
_STANCE_FIELDS = frozenset({'', 'trust', 'fear', 'attitude', 'suspicion'})
_STANCE_KINDS = frozenset({'persuade', 'intimidate', 'deceive'})
_STANCE_VALUE_KEYS = frozenset({
    'kind', 'skill', 'roll', 'modifier', 'total', 'difficulty', 'success',
    'stance_field', 'stance_delta',
})

# Envelope field names are generic. A ruleset payload may exist only inside
# mechanical_outcome, which this module does not interpret.
ENVELOPE_FIELDS = frozenset({
    'status', 'reason', 'action_id', 'campaign_id', 'ruleset_id', 'ruleset_version',
    'capability', 'capability_status', 'validation_status', 'authorization_status',
    'commit_status', 'mechanical_outcome', 'proposed_state_changes',
    'required_preconditions', 'explanation', 'publication', 'retry',
    'committed_marker', 'implementation', 'discarded_proposal_count',
})

TERMINAL_STATUSES = frozenset({
    'supported', 'unsupported', 'unknown', 'invalid', 'unresolved',
    'authorized', 'rejected', 'conflict', 'committed',
})


def request_digest(request: Mapping[str, Any]) -> str:
    """Stable identity of one action request. Replay matches this digest."""
    body = {key: request.get(key) for key in (
        'action_id', 'action_type', 'actor_reference', 'target_references',
        'parameters', 'campaign_reference', 'expected_state_revision')}
    raw = json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return sha256(raw.encode('utf-8')).hexdigest()


def _json_safe(value: Any, depth: int = 0) -> bool:
    if depth > 8:
        return False
    if value is None or type(value) is bool or type(value) is int:
        return True
    if type(value) is str:
        return len(value) <= 4000
    if type(value) is list:
        return len(value) <= 64 and all(_json_safe(item, depth + 1) for item in value)
    if type(value) is dict:
        return len(value) <= 64 and all(
            type(key) is str and len(key) <= 80 and _json_safe(item, depth + 1)
            for key, item in value.items())
    return False


def _reference(value: Any) -> str | None:
    if not isinstance(value, dict) or set(value) != {'kind', 'id'}:
        return 'malformed'
    if value.get('kind') not in _REFERENCE_KINDS or type(value.get('id')) is not str:
        return 'malformed'
    if not value['id'] or len(value['id']) > 80:
        return 'malformed'
    return None


def parse_request(payload: Any) -> tuple[dict[str, Any] | None, str | None]:
    """Validate shape only. Campaign truth and ruleset authority are not decided here."""
    if not isinstance(payload, dict):
        return None, 'malformed_request'
    if set(payload) - REQUEST_FIELDS:
        return None, 'malformed_request'
    if 'action_id' not in payload or payload['action_id'] in (None, ''):
        return None, 'missing_action_id'
    if type(payload['action_id']) is not str or _ACTION_ID.fullmatch(payload['action_id']) is None:
        return None, 'malformed_action_id'
    if 'action_type' not in payload or payload['action_type'] in (None, ''):
        return None, 'missing_action_type'
    if type(payload['action_type']) is not str or len(payload['action_type']) > 80:
        return None, 'malformed_action_type'
    if 'actor_reference' not in payload or payload['actor_reference'] in (None, ''):
        return None, 'missing_actor'
    if _reference(payload['actor_reference']) is not None:
        return None, 'malformed_actor'
    if 'campaign_reference' not in payload or payload['campaign_reference'] in (None, ''):
        return None, 'missing_campaign'
    if type(payload['campaign_reference']) is not str or len(payload['campaign_reference']) > 80:
        return None, 'malformed_campaign'
    if 'parameters' in payload and payload['parameters'] is not None:
        if type(payload['parameters']) is not dict or not _json_safe(payload['parameters']):
            return None, 'malformed_parameters'
        parameters = payload['parameters']
    else:
        parameters = {}
    if 'target_references' in payload and payload['target_references'] is not None:
        targets = payload['target_references']
        if type(targets) is not list or len(targets) > 8:
            return None, 'malformed_targets'
        if any(_reference(item) is not None for item in targets):
            return None, 'invalid_target'
    else:
        targets = []
    if 'expected_state_revision' in payload and payload['expected_state_revision'] is not None:
        revision = payload['expected_state_revision']
        if type(revision) is not int or revision < 0:
            return None, 'malformed_revision'
    else:
        revision = None
    named = 'ruleset_id' in payload or 'ruleset_version' in payload
    if named and (type(payload.get('ruleset_id')) is not str or type(payload.get('ruleset_version')) is not str):
        return None, 'request_ruleset_conflict'
    return {
        'action_id': payload['action_id'],
        'action_type': payload['action_type'],
        'actor_reference': {'kind': payload['actor_reference']['kind'], 'id': payload['actor_reference']['id']},
        'target_references': [{'kind': item['kind'], 'id': item['id']} for item in targets],
        'parameters': parameters,
        'campaign_reference': payload['campaign_reference'],
        'expected_state_revision': revision,
        'ruleset_id': payload.get('ruleset_id') if named else None,
        'ruleset_version': payload.get('ruleset_version') if named else None,
        'ruleset_echo': named,
    }, None


def _stance_problem(value: Any) -> str | None:
    if not isinstance(value, dict) or set(value) != _STANCE_VALUE_KEYS:
        return 'malformed_value'
    if value.get('kind') not in _STANCE_KINDS or type(value.get('skill')) is not str:
        return 'malformed_value'
    roll, modifier, total, difficulty = (value.get('roll'), value.get('modifier'),
                                          value.get('total'), value.get('difficulty'))
    if type(roll) is not int or roll < 1 or roll > 20:
        return 'malformed_value'
    if type(modifier) is not int or type(total) is not int or type(difficulty) is not int:
        return 'malformed_value'
    if total != roll + modifier or type(value.get('success')) is not bool:
        return 'inconsistent_outcome'
    if value['success'] is not (total >= difficulty):
        return 'inconsistent_outcome'
    field, delta = value.get('stance_field'), value.get('stance_delta')
    if field not in _STANCE_FIELDS or delta not in (-1, 0, 1):
        return 'malformed_value'
    if (field == '') != (delta == 0):
        return 'malformed_value'
    return None


def validate_proposed_changes(changes: Any, *, campaign_id: str, revision: int,
                              npc_ids: set[str] | None = None) -> dict[str, Any]:
    """Accept one ledger marker or one NPC stance check, or reject the whole proposal."""
    if not isinstance(changes, list):
        return {'outcome': 'invalid', 'reason': 'malformed_value', 'marker': None}
    if not changes:
        return {'outcome': 'empty', 'reason': 'authorized_no_change', 'marker': None}
    normalized = []
    kinds = []
    for change in changes:
        if not isinstance(change, dict) or set(change) != CHANGE_FIELDS:
            return {'outcome': 'invalid', 'reason': 'malformed_value', 'marker': None}
        owner = change.get('state_owner')
        if owner == LEDGER_OWNER:
            if change.get('target_id') != campaign_id:
                return {'outcome': 'conflict', 'reason': 'invalid_target_identity', 'marker': None}
            if type(change.get('expected_revision')) is not int or change['expected_revision'] != revision:
                return {'outcome': 'conflict', 'reason': 'stale_revision', 'marker': None}
            if change.get('operation') != LEDGER_OPERATION:
                return {'outcome': 'invalid', 'reason': 'unsupported_operation', 'marker': None}
            if change.get('field') != LEDGER_FIELD:
                return {'outcome': 'rejected', 'reason': 'unauthorized_field', 'marker': None}
            if type(change.get('value')) is not str or _MARKER.fullmatch(change['value']) is None:
                return {'outcome': 'invalid', 'reason': 'malformed_value', 'marker': None}
            kinds.append('ledger')
        elif owner == STANCE_OWNER:
            if npc_ids is None or change.get('target_id') not in npc_ids:
                return {'outcome': 'conflict', 'reason': 'invalid_target_identity', 'marker': None}
            if type(change.get('expected_revision')) is not int or change['expected_revision'] != revision:
                return {'outcome': 'conflict', 'reason': 'stale_revision', 'marker': None}
            if change.get('operation') != STANCE_OPERATION:
                return {'outcome': 'invalid', 'reason': 'unsupported_operation', 'marker': None}
            if change.get('field') != STANCE_FIELD_NAME:
                return {'outcome': 'rejected', 'reason': 'unauthorized_field', 'marker': None}
            problem = _stance_problem(change.get('value'))
            if problem is not None:
                return {'outcome': 'invalid', 'reason': problem, 'marker': None}
            kinds.append('stance')
        else:
            return {'outcome': 'rejected', 'reason': 'invalid_state_owner', 'marker': None}
        normalized.append({key: change[key] for key in CHANGE_FIELDS})
    if any(item != normalized[0] for item in normalized) or len(set(kinds)) != 1:
        return {'outcome': 'conflict', 'reason': 'conflicting_changes', 'marker': None}
    if kinds[0] == 'stance':
        return {'outcome': 'valid', 'reason': 'valid_proposed_change', 'marker': 'social_check',
                'change': normalized[0], 'kind': 'stance'}
    return {'outcome': 'valid', 'reason': 'valid_proposed_change', 'marker': normalized[0]['value'],
            'change': normalized[0], 'kind': 'ledger'}
