"""Internal, read-only object disclosure; never a perception or publication owner.

Only trusted Python orchestration may establish authorization. No JSON grant,
HTTP route, authentication claim, physical adjudication or persistence operation.
The caller supplies a coherent authoritative character snapshot under its existing
read lane. Inventory membership alone establishes no observation rights.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from game.object_instances import _text, _uuid, _IDENTITY_FIELDS, _identity_error

REQUEST_FIELDS = frozenset({'version', 'campaign_run_id', 'character_id',
                            'instance_id', 'observer_id', 'scope', 'categories'})


@dataclass(frozen=True)
class _ObservationAuthorization:
    campaign_run_id: str
    character_id: str
    instance_id: str
    observer_id: str
    scope: str
    categories: tuple[str, ...]
    revision: int
    state_digest: str
    decision_ref: str
    visibility_ref: str
    access_ref: str
    concealed: bool = False
    restricted_scopes: tuple[str, ...] = ()
    complete: bool = False


def _target(character, request):
    if not isinstance(character, dict) or character.get('id') != request['character_id']:
        return None
    inventory = character.get('inventory')
    if not isinstance(inventory, list):
        return None
    seen = set()
    target = None
    for row in inventory:
        if not isinstance(row, dict) or not _IDENTITY_FIELDS.intersection(row):
            continue
        # Reuse the identity owner's validation without copying inventory/history.
        if _identity_error(row, request['campaign_run_id']) or row['instance_id'] in seen:
            return None
        seen.add(row['instance_id'])
        if row['instance_id'] == request['instance_id']:
            target = row
    return target


def _state_digest(row):
    # Bind relevant state including classification; never publish this digest.
    marks = row.get('markings', [])
    if not isinstance(marks, list) or len(marks) > 16 or any(type(m) is not dict for m in marks):
        raise ValueError('invalid_active_state')
    metadata = row.get('marking_visibility')
    metadata = metadata if type(metadata) is dict else {}
    classes = metadata.get('markings')
    classes = classes if type(classes) is dict else {}
    value = dict(revision=row['revision'], visibility_version=metadata.get('version'),
        markings=[{k: m.get(k) for k in ('version', 'type', 'modification_id', 'applied_revision', 'content')}
                  for m in marks],
        visibility=[classes.get(m.get('modification_id')) for m in marks])
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _valid_request(request):
    return (type(request) is dict and set(request) == REQUEST_FIELDS
            and type(request['version']) is int and request['version'] == 1
            and all(_text(request[k]) for k in ('campaign_run_id', 'character_id', 'observer_id', 'scope'))
            and _uuid(request['instance_id']) and type(request['categories']) is list
            and 0 < len(request['categories']) <= len(_PROJECTORS)
            and all(type(c) is str and c in _PROJECTORS for c in request['categories'])
            and len(set(request['categories'])) == len(request['categories']))


def _establish_observation_authorization(character, request, *, decision_ref,
        visibility_ref, access_ref, concealed=False, restricted_scopes=(), complete=False):
    """Trusted upstream assertion, NOT callable with client-origin grants.

    The current project has no authenticated observation-decision issuer. This
    internal seam therefore requires a trusted caller to have already resolved
    visibility/access/rights and mechanics. References are private evidence, not
    independent verification of reachability. Complete grants cover concealed
    and every restricted scope (wildcard), but never guess legacy visibility.
    """
    if (not _valid_request(request) or not all(_text(v) for v in (decision_ref, visibility_ref, access_ref))
            or type(concealed) is not bool or type(complete) is not bool
            or type(restricted_scopes) is not tuple or len(restricted_scopes) > 16
            or not all(_text(v) for v in restricted_scopes)
            or len(set(restricted_scopes)) != len(restricted_scopes)
            or (complete and (not concealed or restricted_scopes != ('*',)))):
        raise ValueError('invalid_established_authorization')
    row = _target(character, request)
    if row is None:
        raise ValueError('unavailable_target')
    return _ObservationAuthorization(**{k: request[k] for k in
        ('campaign_run_id', 'character_id', 'instance_id', 'observer_id', 'scope')},
        categories=tuple(request['categories']), revision=row['revision'], state_digest=_state_digest(row),
        decision_ref=decision_ref, visibility_ref=visibility_ref, access_ref=access_ref,
        concealed=concealed, restricted_scopes=restricted_scopes, complete=complete)


def _unavailable():
    # Uniform refusal: no target existence, revisions, counts, private reasons.
    return dict(version=1, status='unresolved', target=None, properties=[],
                limitations=['observation_unavailable'], evidence=[])


def observe_object(character, request, *, authorization=None):
    """Project only authorized properties from the supplied current snapshot.

    New categories can add separate bounded projectors here; no rule execution
    or plugin framework. Unknown categories fail closed before any state read.
    Return a fresh allowlisted DTO; authorization and marking IDs never escape.
    """
    if (not _valid_request(request) or type(authorization) is not _ObservationAuthorization
            or type(authorization.revision) is not int):
        return _unavailable()
    auth = authorization
    try:
        expected = _establish_observation_authorization(character, request,
            decision_ref=auth.decision_ref, visibility_ref=auth.visibility_ref, access_ref=auth.access_ref,
            concealed=auth.concealed, restricted_scopes=auth.restricted_scopes, complete=auth.complete)
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError, OverflowError):
        return _unavailable()
    if auth != expected:
        return _unavailable()
    row = _target(character, request)
    properties = [_PROJECTORS[c](row, auth) for c in request['categories']]
    if any(p is None for p in properties):
        return _unavailable()
    complete = all(p['coverage'] == 'complete' for p in properties)
    return dict(version=1, status='observed',
        target=dict(campaign_run_id=request['campaign_run_id'], instance_id=request['instance_id']),
        properties=properties, limitations=[] if complete else ['partial_observation_scope'],
        evidence=[dict(reference=v['evidence_ref'], category=p['category'], content_sha256=v['content_sha256'])
                  for p in properties for v in p['values']])


def _project_markings(row, auth):
    """Initial concrete property adapter; reads current active state only."""
    marks = row.get('markings', [])
    if not isinstance(marks, list) or len(marks) > 16:
        return None
    metadata = row.get('marking_visibility')
    classes = (metadata.get('markings') if type(metadata) is dict
               and type(metadata.get('version')) is int and metadata['version'] == 1 else None)
    classes = classes if type(classes) is dict else {}
    values = []
    classified = True
    seen = set()
    # At most sixteen active records. No historical receipt traversal.
    for mark in marks:
        if (type(mark) is not dict or not _uuid(mark.get('modification_id'))
                or mark['modification_id'] in seen or mark.get('type') != 'add_marking'
                or type(mark.get('version')) is not int or mark['version'] != 1
                or type(mark.get('applied_revision')) is not int
                or not 0 < mark['applied_revision'] <= row['revision']):
            return None
        seen.add(mark['modification_id'])
        visibility = classes.get(mark['modification_id'])
        valid = (type(visibility) is dict and (
            (set(visibility) == {'classification'} and visibility['classification'] in ('visible', 'concealed'))
            or (set(visibility) == {'classification', 'scope'} and visibility['classification'] == 'restricted'
                and _text(visibility['scope']))))
        if not valid:
            classified = False
            continue
        kind = visibility['classification']
        permitted = (kind == 'visible' or (kind == 'concealed' and auth.concealed)
            or (kind == 'restricted' and ('*' in auth.restricted_scopes
                                        or visibility['scope'] in auth.restricted_scopes)))
        if not permitted:
            continue
        content = mark.get('content')
        if not isinstance(content, str) or not content.strip():
            return None
        try:
            encoded = content.encode('utf-8')
        except UnicodeError:
            return None
        if len(encoded) > 2048:
            return None
        values.append(dict(content=content, presentation='inscription',
            evidence_ref='observation:markings:' + str(len(values)),
            content_sha256=hashlib.sha256(encoded).hexdigest()))
    if sum(len(v['content'].encode('utf-8')) for v in values) > 8192:
        return None
    complete = auth.complete and classified
    knowledge = 'known_present' if values else ('known_absent' if complete else 'unknown')
    return dict(category='markings', knowledge=knowledge,
                coverage='complete' if complete else 'subset', values=values)


# Closed set of core projectors, extended in code; no executable ACLs/plugins.
_PROJECTORS = {'markings': _project_markings}
