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


def proposition_schema():
    strings = ('predicate', 'predicate_evidence', 'subject', 'subject_evidence', 'object', 'object_evidence', 'missing_argument', 'temporal', 'spatial', 'epistemic', 'prior_reference')
    return object_schema({**{k: {'type': 'string'} for k in strings}, 'negated': {'type': 'boolean'}})


def role_schema():
    return object_schema({'role': {'type': 'string', 'enum': list(ROLES)}, 'entity_id': {'type': 'string'}, 'reference': {'type': 'string'}, 'evidence': {'type': 'string'}})


def source_schema():
    return object_schema({'source_id': {'type': 'string'}, 'proposition': proposition_schema()})


def normalize(value):
    return re.sub(r'[^\w]+', ' ', str(value or '').casefold()).strip()


def clean_proposition(raw: Any):
    if not isinstance(raw, Mapping):
        return None
    keys = set(proposition_schema()['properties'])
    if set(raw) != keys or not isinstance(raw.get('negated'), bool):
        return None
    if any(not isinstance(raw[k], str) or len(raw[k]) > 160 for k in keys - {'negated'}):
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
