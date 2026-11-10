"""Bounded persistent-state frames for the existing narration authority validator.

Read-side comparisons only: entities must match exactly after article/plural
normalization, and only resolved outcome text grants transitions. Observable
text can support an existing state, never a transition or permanence escalation.
No scene noun catalog, provider, mutable state, or token-similarity grant.
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class StateAssertion:
    entity: str
    property: str
    result: str
    permanent: bool
    kind: str
    text: str


def entity_key(text):
    words = re.findall(r"[a-z0-9]+", text.casefold().replace('_', ' '))
    words = [w for w in words if w not in {'the', 'a', 'an', 'your'}]
    if words and words[-1].endswith('s') and not words[-1].endswith('ss'):
        words[-1] = words[-1][:-1]
    return ' '.join(words)


# Finite result vocabulary, independent of the affected entity's noun.
_RESULTS = {
    'open': ('access', 'open'), 'opened': ('access', 'open'),
    'closed': ('access', 'closed'), 'shut': ('access', 'closed'),
    'unlocked': ('lock', 'unlocked'), 'locked': ('lock', 'locked'),
    'sealed': ('seal', 'sealed'), 'unsealed': ('seal', 'unsealed'),
    'accessible': ('accessibility', 'accessible'), 'inaccessible': ('accessibility', 'inaccessible'),
    'blocked': ('accessibility', 'blocked'), 'removed': ('existence', 'removed'),
    'destroyed': ('integrity', 'destroyed'), 'broken': ('integrity', 'broken'),
    'collapsed': ('integrity', 'collapsed'), 'dead': ('life', 'dead'),
    'unconscious': ('capacity', 'unconscious'), 'incapacitated': ('capacity', 'incapacitated'),
    'poisoned': ('condition', 'poisoned'), 'cursed': ('condition', 'cursed'),
    'flooded': ('environment', 'flooded'), 'drained': ('environment', 'drained'),
    'complete': ('progress', 'complete'), 'completed': ('progress', 'complete'),
    'advanced': ('progress', 'advanced'),
}
_RESULT = '|'.join(sorted(_RESULTS, key=len, reverse=True))
_SUBJECT = r'(?P<entity>(?:(?:the|a|an|your)\s+)?[a-z][a-z0-9-]*(?:\s+[a-z0-9-]+){0,5}?)'
_PREFIX = r'(?:(?:is|are|was|were|stands?|becomes?|became|falls?|fell|remains?|stays?)\s+|(?:has|have|had)\s+(?:been\s+)?|(?:will\s+remain)\s+)'
_STATE = re.compile(r'\b'+_SUBJECT+r'\s+'+_PREFIX+r'(?:(?:now|permanently|forever|temporarily|already|finally|fully|no longer)\s+)*(?P<result>'+_RESULT+r')\b', re.I)
_ACTIVE = re.compile(r'\b'+_SUBJECT+r'\s+(?P<verb>swings? open|slides? open|opens?|closes?|unlocks?|collapses?|gives? way|breaks?|dies|died)\b', re.I)
_VERBS = {'swing open':'open','swings open':'open','slide open':'open','slides open':'open','open':'open','opens':'open','close':'closed','closes':'closed','unlock':'unlocked','unlocks':'unlocked','collapse':'collapsed','collapses':'collapsed','give way':'collapsed','gives way':'collapsed','break':'broken','breaks':'broken','dies':'dead','died':'dead'}
_IMPOSSIBLE = re.compile(r'\b'+_SUBJECT+r'\s+can no longer be (?P<verb>closed|opened|locked|sealed)\b',re.I)
_RESULTATIVE = re.compile(r'\bleaving\s+'+_SUBJECT+r'\s+(?P<result>'+_RESULT+r')\b',re.I)
_TRANSITIVE = re.compile(r'\b(?:you|he|she|they)\s+(?P<verb>open|opened|unlock|unlocked|close|closed|destroy|destroyed|kill|killed|break|broke|incapacitate|incapacitated)\s+(?P<entity>.+?)(?=\s+(?:and|with|using|before|after)\b|[.!?;]|$)',re.I)
_ACQUIRE = re.compile(r'\byou\s+(?:pick up|picked up)\s+(?P<entity>.+?)(?=\s+(?:and|from|before|after)\b|[.!?;]|$)',re.I)
_AMBIGUOUS = re.compile(r'\b(?:seems? to have|may already be|appears? to have)\b[^.!?;]{0,40}\b(?:'+_RESULT+r')\b|\bsomething\b[^.!?;]{0,60}\bhas changed\b|\b(?:it|they|this|that)\s+(?:is|are)\s+now\s+(?:'+_RESULT+r')\b|\b(?:the\s+)?\w+\s+yields\s*[.!?]?$',re.I)


def assertions(text):
    frames = []
    # Split independent finite clauses so negation/modality cannot hide an
    # appended actual consequence. Keep noun modifiers attached to their entity.
    clauses = re.split(r'(?<=[.!?;])\s+|,\s*(?:but|and)\s+|\s+and\s+(?=(?:the|a|an|you|it)\b)', text, flags=re.I)
    for clause in clauses:
        raw = clause.strip()
        hypothetical = bool(re.match(r'(?:if|unless)\b',raw,re.I) or re.search(r'\b(?:might|could|would|should)\b|\bmay (?!already)',raw,re.I))
        attempted = bool(re.search(r'\b(?:try|tries|tried|attempt|attempts|attempted)\s+to\b',raw,re.I))
        negated = bool(re.search(r"\b(?:not|never|doesn't|don't|didn't|hasn't|haven't)\b",raw,re.I))
        if hypothetical or attempted or negated:
            continue
        if _AMBIGUOUS.search(raw):
            frames.append(StateAssertion('', '', '', False, 'ambiguous', raw))
            continue
        permanent = bool(re.search(r'\b(?:permanent\w*|forever|from now on|can no longer|never again)\b',raw,re.I))
        state_spans = [m.span() for m in _STATE.finditer(raw)]
        for pattern in (_STATE, _RESULTATIVE, _ACTIVE, _IMPOSSIBLE, _TRANSITIVE, _ACQUIRE):
            for m in pattern.finditer(raw):
                if pattern is _ACTIVE and m.group('verb').casefold() in {'open','close','unlock','collapse','break'} and not m.group('entity').casefold().endswith('s'):
                    continue
                if pattern is _ACTIVE and (any(a <= m.start() and m.end() <= b for a,b in state_spans) or re.search(r'\b(?:to|appears?|looks?|difficult)\b',m.group('entity'),re.I)):
                    continue
                entity = entity_key(m.group('entity'))
                if pattern is _TRANSITIVE:
                    verb=m.group('verb').casefold()
                    result={'open':'open','opened':'open','unlock':'unlocked','unlocked':'unlocked','close':'closed','closed':'closed','destroy':'destroyed','destroyed':'destroyed','kill':'dead','killed':'dead','break':'broken','broke':'broken','incapacitate':'incapacitated','incapacitated':'incapacitated'}[verb]
                    prop,result=_RESULTS[result]
                elif pattern is _ACQUIRE:
                    prop,result='inventory','acquired'
                elif pattern is _IMPOSSIBLE:
                    prop,result='irreversibility',m.group('verb').casefold()
                else:
                    result = m.group('result').casefold() if pattern in (_STATE, _RESULTATIVE) else _VERBS[m.group('verb').casefold()]
                    prop,result = _RESULTS[result]
                    if re.search(r'\bno longer\b',m.group(0),re.I):
                        inverse={'sealed':'unsealed','locked':'unlocked','closed':'open','blocked':'accessible','poisoned':'healthy'}
                        result = inverse.get(result, 'not '+result)
                kind = 'existing_state' if re.search(r'\b(?:remains?|stays?|stands?)\b',m.group(0),re.I) and not permanent else 'persistent_change'
                frames.append(StateAssertion(entity,prop,result,permanent,kind,raw))
    return frames


def compare(frame, authority):
    """No lexical pool: bind entity, property, result and duration in one fact."""
    if frame.kind == 'ambiguous' or frame.entity in {'it','they','this','that'}:
        return 'AMBIGUOUS'
    for source in authority.authorized_outcomes:
        for grant in assertions(source):
            if grant.kind == 'ambiguous' or frame.entity != grant.entity or frame.property != grant.property:
                continue
            if frame.result != grant.result:
                return 'CONTRADICTORY'
            if frame.permanent and not grant.permanent:
                return 'UNAUTHORIZED'
            if re.search(r'\btemporar\w*\b',source,re.I) and not re.search(r'\btemporar\w*\b',frame.text,re.I):
                return 'UNAUTHORIZED'
            return 'AUTHORIZED'
    if not frame.permanent and frame.result in {'open','unlocked','accessible'} and frame.property in {'access','lock','accessibility'} and any(frame.entity == entity_key(g) for g in authority.routes_unlocked):
        return 'AUTHORIZED'
    if not frame.permanent and frame.entity=='you' and frame.property=='condition' and any(frame.result==entity_key(g) for g in authority.conditions_applied):
        return 'AUTHORIZED'
    grants = {'inventory':authority.items_added,'condition':authority.conditions_applied,'progress':authority.objectives_completed,'accessibility':authority.routes_unlocked}
    if not frame.permanent and any(frame.entity == entity_key(g) for g in grants.get(frame.property, ())):
        # Existing adapters only carry player condition / completed objective /
        # unlocked route results. Do not reuse a grant for an opposite state.
        expected={'inventory':'acquired','condition':frame.result if frame.entity=='you' else '', 'progress':'complete','accessibility':'accessible'}
        if frame.result == expected.get(frame.property):
            return 'AUTHORIZED'
    for source in authority.observable_scene + authority.authorized_discoveries:
        for fact in assertions(source):
            if (frame.entity,frame.property)==(fact.entity,fact.property):
                if frame.result != fact.result:
                    return 'CONTRADICTORY'
                if frame.kind == 'existing_state' and not frame.permanent:
                    return 'AUTHORIZED'
    if frame.kind == 'existing_state' and re.search(r'\b(?:remains?|stays?)\s+(?:closed|locked|sealed)\b', frame.text,re.I):
        return 'AUTHORIZED'  # A denied change, unless authority above contradicts it.
    return 'UNAUTHORIZED'


def validate_persistent(text, authority):
    claims=[]
    for frame in assertions(text):
        match=compare(frame,authority)
        if match == 'AUTHORIZED':
            continue
        claims.append({'category':'persistent_consequence','reason': 'ambiguous_persistent_consequence' if match=='AMBIGUOUS' else 'persistent_contradiction' if match=='CONTRADICTORY' else 'unauthorized_persistent_consequence',
            'decision':'REVIEW_REQUIRED' if match=='AMBIGUOUS' else 'FAIL','epistemic':frame.kind,'text':frame.text,
            'subject':frame.entity,'property':frame.property,'result':frame.result,'permanent':frame.permanent,'authority_match':match})
    return claims
