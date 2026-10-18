"""Bounded semantic correspondence. Interpretations never become canonical records.

The provider normalizes an open relationship vocabulary. The host checks quoted
witnesses, argument identity, qualifiers and source identity independently of
NPC knowledge/disclosure. Only the original authorized text can be delivered.
"""
from __future__ import annotations

import re
from typing import Mapping, Any

ROLES = ('speaker', 'addressee', 'mentioned_npc', 'requested_subject', 'requested_object', 'information_source', 'prior_proposition', 'correction_target')


def object_schema(properties):
    return {'type': 'object', 'additionalProperties': False, 'properties': properties, 'required': list(properties)}


def proposition_schema(named=False):
    strings = ('predicate', 'predicate_evidence', 'subject', 'subject_evidence', 'object', 'object_evidence', 'missing_argument', 'temporal', 'spatial', 'epistemic', 'prior_reference')
    properties = {**{k: {'type': 'string'} for k in strings}, 'negated': {'type': 'boolean'}}
    if named:
        from game.semantic_operations import role_schema
        for key in ('subject', 'subject_evidence', 'object', 'object_evidence', 'missing_argument'):
            properties.pop(key)
        properties.update(roles={'type': 'array', 'items': role_schema(), 'maxItems': 8},
                          requested_role={'type': 'string', 'maxLength': 48})
    return object_schema(properties)


def role_schema():
    return object_schema({'role': {'type': 'string', 'enum': list(ROLES)}, 'entity_id': {'type': 'string'}, 'reference': {'type': 'string'}, 'evidence': {'type': 'string'}})


def source_schema(named=False):
    return object_schema({'source_id': {'type': 'string'}, 'proposition': proposition_schema(named)})


def normalize(value):
    return re.sub(r'[^\w]+', ' ', str(value or '').casefold()).strip()


def clean_proposition(raw: Any):
    if not isinstance(raw, Mapping):
        return None
    # An explicitly empty requested slot and an omitted requested slot are the
    # same proposal. Normalize only this schema-equivalent representation.
    if isinstance(raw.get('roles'), list) and isinstance(raw.get('requested_role'), str):
        raw = dict(raw)
        raw['roles'] = [r for r in raw['roles'] if not (
            isinstance(r, dict) and set(r) == {'name', 'value', 'entity_id', 'evidence'}
            and r['name'] == raw['requested_role'] and all(r[k] == '' for k in ('value', 'entity_id')))]
    from game.semantic_operations import EXTENSIONS, NAME, clean_roles
    named = bool(set(raw) & EXTENSIONS)
    binary = {'subject', 'subject_evidence', 'object', 'object_evidence', 'missing_argument'}
    if named and not set(raw) & binary:
        raw = {**raw, **dict.fromkeys(binary, '')}
    keys = set(proposition_schema()['properties']) | (EXTENSIONS if named else set())
    if set(raw) != keys or not isinstance(raw.get('negated'), bool):
        return None
    if any(not isinstance(raw[k], str) or len(raw[k]) > 160 for k in keys - {'negated', 'roles'}):
        return None
    if named and (clean_roles(raw['roles']) is None or
                  raw['requested_role'] and not NAME.fullmatch(raw['requested_role'])):
        return None
    if named and raw['requested_role'] in {r['name'] for r in raw['roles']}:
        return None
    if raw['missing_argument'] not in {'', 'subject', 'object', 'temporal', 'spatial', 'predicate'}:
        return None
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,79}', raw['predicate']):
        return None
    return dict(raw)


def witnessed(prop, text, *, prior_text=''):
    """Exact text witnesses bound an interpretation to its host-owned input."""
    for field in ('predicate', 'subject', 'object'):
        evidence = prop[field + '_evidence']
        if prop[field] and field != prop['missing_argument'] and not evidence:
            return False
        if evidence and evidence.casefold() not in text.casefold():
            # Only an explicitly bound prior request may supply elided arguments.
            if not prop['prior_reference'] or evidence.casefold() not in prior_text.casefold():
                return False
    return all(not prop[k] or prop[k].casefold() in (text + ' ' + prior_text).casefold() for k in ('temporal', 'spatial'))


def argument_identity(reference, evidence, participants):
    """Only literal identity or an existing entity's aliases establish a binding."""
    ref, span = normalize(reference), normalize(evidence)
    ref = re.sub(r'^(?:the|a|an) ', '', ref)
    span = re.sub(r'^(?:the|a|an) ', '', span)
    if ref == span:
        return True
    for person in participants:
        aliases = {normalize(person.get('id')), normalize(person.get('name'))}
        aliases.update(normalize(x) for x in person.get('aliases') or [])
        if ref in aliases and span in aliases:
            return True
    return False


def coverage(request, source, *, question, source_text, participants=(), prior_text=''):
    """Host structural compatibility, never a disclosure grant.

    Unknown semantic equivalence between argument phrases fails closed; arbitrary
    relationship paraphrases are proposed by the provider, with literal witnesses.
    """
    if not witnessed(request, question, prior_text=prior_text) or not witnessed(source, source_text):
        return 'unknown'
    if 'roles' in request or 'roles' in source:
        from game.semantic_operations import roles_witnessed, named_coverage
        if 'roles' not in request or 'roles' not in source:
            return 'unknown'
        if not roles_witnessed(request, question, participants, prior_text) or not roles_witnessed(source, source_text, participants):
            return 'unknown'
        return named_coverage(request, source)
    for prop in (request, source):
        for slot in ('subject', 'object'):
            if slot != prop['missing_argument'] and prop[slot] and not argument_identity(prop[slot], prop[slot + '_evidence'], participants):
                return 'unknown'
    for slot in ('subject', 'object'):
        if slot == request['missing_argument']:
            continue
        if request[slot] and normalize(request[slot]) != normalize(source[slot]):
            return 'related_but_nonanswer' if any(normalize(request[k]) == normalize(source[k]) and request[k] for k in ('subject', 'object')) else 'unrelated'
    if request['predicate'] != source['predicate']:
        return 'related_but_nonanswer'
    if request['negated'] != source['negated']:
        return 'related_but_nonanswer'
    for qualifier in ('temporal', 'spatial'):
        if request[qualifier] and normalize(request[qualifier]) != normalize(source[qualifier]):
            return 'related_but_nonanswer'
    missing = request['missing_argument']
    if not missing or not source.get(missing):
        return 'partial'
    if source['epistemic'] != request['epistemic']:
        return 'partial'
    return 'direct'
