"""Pure structured marking proposals. API owns application; storage owns bytes.

No gameplay parser, physical inference, ruleset mechanics, or implicit migration.
Only trusted internal Python callers may supply the authorization evidence.
"""
from __future__ import annotations

import copy
import hashlib
import json
from uuid import uuid4

from game.object_instances import _text, _uuid, inspect_object_identity

PRECONDITIONS = frozenset({'target_exists', 'accessible', 'rights', 'writable_surface',
                          'medium_available', 'medium_compatible', 'source_disclosed', 'capability'})
REQUEST_FIELDS = frozenset({'version', 'operation', 'campaign_run_id', 'character_id',
    'instance_id', 'request_id', 'expected_revision', 'content', 'source', 'authorization'})
RESULT_FIELDS = frozenset({'version', 'status', 'persistence', 'campaign_run_id', 'character_id',
    'instance_id', 'request_id', 'request_digest', 'modification_id', 'previous_revision', 'resulting_revision'})
MARK_FIELDS = frozenset({'version', 'type', 'modification_id', 'content', 'source', 'authorization',
                         'request_id', 'request_digest', 'applied_revision'})
LEDGER = 'object_marking_receipts'


def request_digest(request: dict) -> str:
    """SHA-256 of every meaningful input; supplied digest is never self-hashed."""
    semantic = {k: v for k, v in request.items() if k != 'request_digest'}
    raw = json.dumps(semantic, sort_keys=True, separators=(',', ':'),
                     ensure_ascii=True, allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _reject(error):
    return {'status': 'rejected', 'error': error}


def _request_error(req):
    if not isinstance(req, dict) or set(req) != REQUEST_FIELDS | {'request_digest'}:
        return 'invalid_request'
    if (type(req['version']) is not int or req['version'] != 1 or req['operation'] != 'add_marking'
            or not all(_text(req[k]) for k in ('campaign_run_id','character_id','request_id'))
            or not _uuid(req['instance_id']) or type(req['expected_revision']) is not int
            or req['expected_revision'] < 0):
        return 'invalid_request'
    content = req['content']
    try:
        if not isinstance(content, str) or not content.strip() or len(content.encode('utf-8')) > 2048:
            return 'invalid_content'
    except UnicodeError:
        return 'invalid_content'
    source = req['source']
    if (not isinstance(source, dict) or set(source) != {'kind', 'reference'}
            or source['kind'] not in ('explicit_literal', 'disclosed_copy') or not _text(source['reference'])):
        return 'invalid_source'
    auth = req['authorization']
    if (not isinstance(auth, dict) or set(auth) != {'caller_id','decision_id','content_sha256','preconditions','mechanics'}
            or not _text(auth['caller_id']) or not _text(auth['decision_id'])
            or auth['mechanics'] != 'not_applicable'
            or auth['content_sha256'] != hashlib.sha256(content.encode('utf-8')).hexdigest()
            or not isinstance(auth['preconditions'], dict) or set(auth['preconditions']) != PRECONDITIONS
            or not all(_text(v) for v in auth['preconditions'].values())):
        return 'unauthorized_content'
    if req['request_digest'] != request_digest(req):
        return 'invalid_digest'
    return None


def _result(req, marking_id):
    return dict(version=1, status='applied', persistence='committed',
        **{k:req[k] for k in ('campaign_run_id','character_id','instance_id','request_id','request_digest')},
        modification_id=marking_id, previous_revision=req['expected_revision'],
        resulting_revision=req['expected_revision']+1)


def _receipt_state_valid(character, campaign, actor):
    """Cross-check both directions; never trust an orphan/malformed cached result."""
    ledger = character.get(LEDGER, {'version':1, 'campaign_run_id':campaign, 'character_id':actor, 'entries':{}})
    if (not isinstance(ledger,dict) or set(ledger) != {'version','campaign_run_id','character_id','entries'}
            or type(ledger['version']) is not int or ledger['version'] != 1
            or ledger['campaign_run_id'] != campaign or ledger['character_id'] != actor
            or not isinstance(ledger['entries'],dict)):
        return False
    seen_requests, seen_ids = set(), set()
    for row in character['inventory']:
        if not isinstance(row, dict) or 'markings' not in row:
            continue
        marks = row['markings']
        if not _uuid(row.get('instance_id')) or not isinstance(marks,list) or len(marks)>16:
            return False
        total = 0
        last_revision = -1
        for mark in marks:
            if (not isinstance(mark,dict) or set(mark) != MARK_FIELDS
                    or type(mark['version']) is not int or mark['version'] != 1 or mark['type'] != 'add_marking'
                    or not _uuid(mark['modification_id']) or type(mark['applied_revision']) is not int
                    or not last_revision < mark['applied_revision'] <= row['revision']):
                return False
            reconstructed = dict(version=1, operation=mark['type'], campaign_run_id=campaign,
                character_id=actor, instance_id=row['instance_id'], expected_revision=mark['applied_revision']-1,
                **{k:mark[k] for k in ('content','source','authorization','request_id','request_digest')})
            if _request_error(reconstructed):
                return False
            key = mark['request_id']
            receipt = ledger['entries'].get(key)
            expected = _result(reconstructed, mark['modification_id'])
            if (key in seen_requests or mark['modification_id'] in seen_ids
                    or not isinstance(receipt,dict) or set(receipt) != RESULT_FIELDS or receipt != expected
                    or type(receipt['version']) is not int
                    or type(receipt['previous_revision']) is not int or type(receipt['resulting_revision']) is not int):
                return False
            seen_requests.add(key); seen_ids.add(mark['modification_id'])
            total += len(mark['content'].encode('utf-8'))
            last_revision = mark['applied_revision']
        if total > 8192:
            return False
    return seen_requests == set(ledger['entries'])


def prepare_marking(character: dict, request: dict) -> dict:
    """Validate fully, then stage detached state. No filesystem or authority writes."""
    error = _request_error(request)
    if error:
        return _reject(error)
    if not isinstance(character,dict) or character.get('id') != request['character_id']:
        return _reject('character_mismatch')
    inventory = character.get('inventory')
    if not isinstance(inventory,list):
        return _reject('invalid_inventory')
    indices = [i for i,row in enumerate(inventory) if isinstance(row,dict) and row.get('instance_id') == request['instance_id']]
    if len(indices) != 1:
        return _reject('missing_or_ambiguous_target')
    index = indices[0]
    identity = inspect_object_identity(character,index,campaign_run_id=request['campaign_run_id'])
    if identity.status != 'existing':
        return _reject(identity.error or 'missing_identity')
    if not _receipt_state_valid(character,request['campaign_run_id'],request['character_id']):
        return _reject('invalid_receipt_state')
    ledger = character.get(LEDGER, {}).get('entries', {})
    receipt = ledger.get(request['request_id'])
    if receipt is not None:
        if receipt['request_digest'] != request['request_digest']:
            return _reject('conflicting_request')
        return {'status':'replay', 'result':copy.deepcopy(receipt)}
    row = inventory[index]
    if row['revision'] != request['expected_revision']:
        return _reject('stale_revision')
    marks = row.get('markings',[])
    if len(marks) >= 16 or sum(len(m['content'].encode('utf-8')) for m in marks)+len(request['content'].encode('utf-8'))>8192:
        return _reject('marking_capacity')
    marking_id = str(uuid4())
    if any(m['modification_id']==marking_id for r in inventory if isinstance(r,dict) for m in r.get('markings',[])):
        return _reject('modification_id_collision')
    result = _result(request,marking_id)
    candidate = copy.deepcopy(character)
    target = copy.deepcopy(candidate['inventory'][index])
    target.setdefault('markings',[]).append(dict(version=1, type='add_marking', modification_id=marking_id,
        **{k:copy.deepcopy(request[k]) for k in ('content','source','authorization','request_id','request_digest')},
        applied_revision=result['resulting_revision']))
    target['revision'] = result['resulting_revision']
    candidate['inventory'][index] = target
    candidate.setdefault(LEDGER,dict(version=1, campaign_run_id=request['campaign_run_id'],
        character_id=request['character_id'],entries={}))['entries'][request['request_id']] = copy.deepcopy(result)
    return {'status':'validated', 'character':candidate, 'result':result}
