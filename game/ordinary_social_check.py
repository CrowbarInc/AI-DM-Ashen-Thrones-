"""Ordinary-language entrance for one Pathfinder social skill check.

The chat turn calls this only after admission has allowed the utterance.
Unmatched text returns None and stays on its existing owner.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from game.present_npc import match_present_npc, present_roster

_NEGATION = re.compile(r"\b(?:not|never|don't|do not|won't|cannot|can't|no longer)\b", re.I)
_CONDITIONAL = re.compile(r"^\s*(?:if|unless|when|should)\b|\bif i\b", re.I)
_COMPOUND = re.compile(r"\band\b", re.I)
_ACTION = re.compile(
    r"^\s*(?:i|we)\s+(?:(?:try|attempt)\s+to\s+)?(?P<verb>persuade|intimidate|deceive|bluff)\s+(?:the\s+)?(?P<target>.+?)\s*\.?\s*$",
    re.I,
)
_NAMED = re.compile(
    r"^\s*(?:i|we)\s+make\s+a\s+(?:diplomacy|intimidate|intimidation|bluff)\s+check\s+to\s+(?P<verb>persuade|intimidate|deceive)\s+(?:the\s+)?(?P<target>.+?)\s*\.?\s*$",
    re.I,
)
_TRUST = re.compile(r"^\s*(?:does|do)\s+(?:the\s+)?(?P<target>.+?)\s+trust\s+me\s*\??\s*$", re.I)
_REGARD = re.compile(r"^\s*how\s+does\s+(?:the\s+)?(?P<target>.+?)\s+regard\s+me\s*\??\s*$", re.I)
_DID = re.compile(r"^\s*did\s+i\s+(?P<verb>persuade|intimidate|deceive)\s+(?:the\s+)?(?P<target>.+?)\s*\??\s*$", re.I)
_VERBS = {'persuade': 'persuade', 'intimidate': 'intimidate', 'deceive': 'deceive', 'bluff': 'deceive'}


def _kind(verb: str) -> str:
    return _VERBS[verb.casefold()]


def _runtime(session: Mapping[str, Any], npc_id: str) -> Mapping[str, Any]:
    root = session.get('npc_runtime') if isinstance(session.get('npc_runtime'), Mapping) else {}
    row = root.get(npc_id) if isinstance(root, Mapping) else None
    return row if isinstance(row, Mapping) else {}


def _number(row: Mapping[str, Any], field: str) -> int:
    value = row.get(field)
    return value if type(value) is int else 0


def _read_text(kind: str, npc: Mapping[str, Any], session: Mapping[str, Any]) -> str:
    name = str(npc.get('name') or npc.get('id'))
    row = _runtime(session, str(npc.get('id')))
    check = row.get('last_social_check') if isinstance(row.get('last_social_check'), Mapping) else None
    trust = _number(row, 'trust')
    if kind == 'trust':
        if check is None:
            return f"{name}'s trust is {trust}. No social skill check against {name} has been resolved."
        verdict = 'succeeded' if check.get('success') is True else 'failed'
        return (
            f"{name}'s trust is {trust}. The last {check.get('skill')} check to {check.get('kind')} {name} {verdict} "
            f"({check.get('total')} vs DC {check.get('difficulty')})."
        )
    if kind == 'regard':
        text = (
            f"{name}'s stance is attitude {_number(row, 'attitude')}, trust {trust}, "
            f"fear {_number(row, 'fear')}, suspicion {_number(row, 'suspicion')}."
        )
        if check is None:
            return text + f" No social skill check against {name} has been resolved."
        verdict = 'succeeded' if check.get('success') is True else 'failed'
        return text + f" The last {check.get('skill')} check to {check.get('kind')} {name} {verdict}."
    if check is None or check.get('kind') != kind:
        return f"No {kind} check against {name} has been resolved."
    if check.get('success') is True:
        return (
            f"Yes. The {check.get('skill')} check to {kind} {name} succeeded "
            f"({check.get('total')} vs DC {check.get('difficulty')})."
        )
    return (
        f"No. The {check.get('skill')} check to {kind} {name} failed "
        f"({check.get('total')} vs DC {check.get('difficulty')})."
    )


def _action_request(text_kind: str, npc: Mapping[str, Any], character: Mapping[str, Any],
                    session: Mapping[str, Any]) -> dict[str, Any]:
    ledger = session.get('mechanical_action_ledger') if isinstance(session.get('mechanical_action_ledger'), Mapping) else {}
    revision = ledger.get('revision') if type(ledger.get('revision')) is int else 0
    npc_id = str(npc.get('id'))
    action_id = f'social-{text_kind}-{npc_id}'
    receipts = session.get('mechanical_action_receipts') if isinstance(session.get('mechanical_action_receipts'), Mapping) else {}
    existing = receipts.get(action_id) if isinstance(receipts, Mapping) else None
    if isinstance(existing, Mapping) and type(existing.get('ledger_revision_before')) is int:
        revision = existing['ledger_revision_before']
    return {
        'action_id': action_id,
        'action_type': 'social_skill_check',
        'actor_reference': {'kind': 'character', 'id': character.get('id')},
        'target_references': [{'kind': 'npc', 'id': npc_id}],
        'parameters': {'kind': text_kind},
        'campaign_reference': session.get('campaign_run_id'),
        'expected_state_revision': revision,
    }


def plan_ordinary_social_turn(text: str, *, character: Mapping[str, Any], session: Mapping[str, Any],
                              world: Mapping[str, Any], scene: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return a plan, or None when this is not the production social check."""
    raw = text or ''
    roster = present_roster(scene, world, session)
    for pattern, read_kind in ((_TRUST, 'trust'), (_REGARD, 'regard')):
        match = pattern.fullmatch(raw.strip())
        if match is None:
            continue
        found = match_present_npc(match.group('target'), roster)
        if found['status'] != 'unique':
            return {'disposition': 'limitation', 'reason': found['status'] + '_target',
                    'text': _target_limitation(found)}
        return {'disposition': 'read', 'category': 'ANSWER', 'text': _read_text(read_kind, found['npc'], session)}
    did = _DID.fullmatch(raw.strip())
    if did is not None:
        found = match_present_npc(did.group('target'), roster)
        if found['status'] != 'unique':
            return {'disposition': 'limitation', 'reason': found['status'] + '_target',
                    'text': _target_limitation(found)}
        return {'disposition': 'read', 'category': 'ANSWER',
                'text': _read_text(_kind(did.group('verb')), found['npc'], session)}
    match = _NAMED.fullmatch(raw.strip()) or _ACTION.fullmatch(raw.strip())
    if match is None:
        return None
    if _NEGATION.search(raw) or _CONDITIONAL.search(raw) or _COMPOUND.search(raw):
        return {'disposition': 'limitation', 'reason': 'not_admitted',
                'text': 'The check was not made. No trust, fear, attitude, or suspicion changed.'}
    kind = _kind(match.group('verb'))
    found = match_present_npc(match.group('target'), roster)
    if found['status'] != 'unique':
        return {'disposition': 'limitation', 'reason': found['status'] + '_target',
                'text': _target_limitation(found)}
    if not session.get('campaign_run_id') or not character.get('id'):
        return {'disposition': 'limitation', 'reason': 'missing_actor',
                'text': 'The check cannot be resolved because the campaign or character is not established.'}
    return {'disposition': 'action', 'request': _action_request(kind, found['npc'], character, session)}


def _target_limitation(found: Mapping[str, Any]) -> str:
    if found.get('status') == 'ambiguous':
        names = ', '.join(str(item) for item in found.get('options') or [])
        return f"More than one person matches. Say which person: {names}."
    return 'No present person matches that. The check was not made.'


def limitation_text(result: Mapping[str, Any]) -> str:
    """Player sentence for an action that did not commit. It does not report a roll as success."""
    reason = str(result.get('reason') or '')
    if reason.startswith('missing_skill:'):
        skill = reason.split(':', 1)[1].replace('_', ' ')
        return f"The check cannot be resolved. No recorded {skill} modifier is available."
    sentences = {
        'missing_binding': 'This campaign has no ruleset binding, so the check cannot be resolved.',
        'unknown_ruleset': 'This campaign\'s ruleset is unknown, so the check cannot be resolved.',
        'unsupported_version': 'This campaign\'s ruleset version cannot resolve the check.',
        'ruleset_unavailable': 'This campaign\'s ruleset cannot resolve the check.',
        'capability_not_supported': 'The campaign ruleset does not provide this check.',
        'unknown_capability': 'The campaign ruleset does not provide this check.',
        'missing_target': 'The check needs one present person. It was not made.',
        'unknown_target': 'That person is not present. The check was not made.',
        'unknown_actor': 'The acting character is not the campaign character. The check was not made.',
        'request_ruleset_conflict': 'A request cannot switch the campaign ruleset. The check was not made.',
        'stale_revision': 'The campaign state changed before the check could be recorded. It was not made.',
        'duplicate_action_id': 'That check does not match the one already recorded under the same request.',
        'commit_failed': 'The check was not saved. No trust, fear, attitude, or suspicion changed.',
        'resolution_interrupted': 'The check was interrupted before it could be recorded. Nothing changed.',
        'missing_difficulty': 'The check has no established difficulty. It was not made.',
        'invalid_social_kind': 'That is not a resolved social check.',
    }
    if reason in sentences:
        return sentences[reason]
    if result.get('status') in {'unsupported', 'unknown'}:
        return 'The campaign ruleset does not provide this check. Nothing changed.'
    return 'The check was not completed. Nothing changed.'
