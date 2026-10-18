"""Bounded named-role proposals. These checks grant no factual authority.

Role vocabulary is open and bounded by syntax, rather than a relationship table.
Legacy binary propositions remain readable without asserting additional roles.
"""
from copy import deepcopy
import re

NAME = re.compile(r'[a-z][a-z0-9_]{0,47}')
EXTENSIONS = {'roles', 'requested_role'}


def role_schema():
    from game.semantic_correspondence import object_schema
    return object_schema({k: {'type': 'string', 'maxLength': 160, **({'minLength': 1} if k != 'entity_id' else {})} for k in
                          ('name', 'value', 'entity_id', 'evidence')})


def clean_roles(raw):
    if not isinstance(raw, list) or len(raw) > 8:
        return None
    seen = set()
    for r in raw:
        if not isinstance(r, dict) or set(r) != {'name', 'value', 'entity_id', 'evidence'}:
            return None
        if any(not isinstance(v, str) or len(v) > 160 for v in r.values()):
            return None
        if not NAME.fullmatch(r['name']) or r['name'] in seen or not r['value'] or not r['evidence']:
            return None
        seen.add(r['name'])
    return deepcopy(raw)


def roles_witnessed(prop, text, participants=(), prior_text=''):
    from game.semantic_correspondence import argument_identity, normalize
    for role in prop.get('roles', []):
        if role['evidence'].casefold() not in (text + ' ' + prior_text).casefold():
            return False
        if not argument_identity(role['value'], role['evidence'], participants):
            return False
        if role['entity_id']:
            person = next((p for p in participants if p['id'] == role['entity_id']), None)
            if not person or normalize(role['value']) not in {
                normalize(person.get('id')), normalize(person.get('name')),
                *(normalize(a) for a in person.get('aliases', []))}:
                return False
    return True


def named_coverage(request, source):
    from game.semantic_correspondence import normalize
    if request['predicate'] != source['predicate'] or request['negated'] != source['negated']:
        return 'related_but_nonanswer'
    wanted = {r['name']: r for r in request['roles']}
    supplied = {r['name']: r for r in source['roles']}
    incomplete = False
    for name, role in wanted.items():
        other = supplied.get(name)
        if not other:
            incomplete = True
        elif role['entity_id'] and other['entity_id']:
            if role['entity_id'] != other['entity_id']:
                return 'related_but_nonanswer'
        elif normalize(role['value']) != normalize(other['value']):
            return 'related_but_nonanswer'
    for key in ('temporal', 'spatial'):
        if request[key] and not source[key]:
            incomplete = True
        elif request[key] and normalize(request[key]) != normalize(source[key]):
            return 'related_but_nonanswer'
    missing = request['requested_role']
    if not missing or missing not in supplied or source['requested_role'] == missing:
        incomplete = True
    if request['epistemic'] != source['epistemic']:
        incomplete = True
    return 'partial' if incomplete else 'direct'


def apply_role_delta(old, proposed, op, utterance, participants):
    """Copy-on-write roles: no opaque replacement, no erasure of omitted roles."""
    fields = set(op['changed_fields'])
    names = op.get('changed_roles', [])
    old_roles = {r['name']: r for r in old.get('roles', [])}
    new_roles = {r['name']: r for r in proposed.get('roles', [])}
    if ('roles' in fields) != bool(names) or len(names) != len(set(names)):
        return None, 'invalid_role_delta'
    if 'roles' in fields and not old_roles:
        return None, 'legacy_role_delta_requires_explicit_question'
    if any(name not in old_roles or name not in new_roles for name in names):
        return None, 'unknown_changed_role'
    for name, role in new_roles.items():
        if name not in names and role != old_roles.get(name):
            return None, 'unlisted_role_change'
    changed = {name: new_roles[name] for name in names}
    if not roles_witnessed({'roles': list(changed.values())}, utterance, participants):
        return None, 'ungrounded_role_change'
    if names and all(old_roles[n] == changed[n] for n in names):
        return None, 'empty_role_change'
    result = deepcopy(old)
    old_roles.update(deepcopy(changed))
    result['roles'] = list(old_roles.values())
    if 'requested_role' in fields:
        result['requested_role'] = proposed.get('requested_role', '')
        if not NAME.fullmatch(result['requested_role']) or result['requested_role'] in old_roles:
            return None, 'invalid_requested_role'
    elif proposed.get('requested_role', old.get('requested_role')) != old.get('requested_role'):
        return None, 'unlisted_requested_role_change'
    return result, ''
