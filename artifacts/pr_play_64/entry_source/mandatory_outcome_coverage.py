"""Bounded read-only coverage relationships for completed investigation facts.

This is a leaf of integrated narration validation, not an authority store or a
general natural-language inference engine. Unsupported grammar stays in review.
"""
from __future__ import annotations

import re

from game import consequential_narration_validation as semantic


def _has(pattern, text):
    return re.search(pattern, text, re.I) is not None


def _normal(text):
    text = text.casefold().replace('\u2019', "'")
    # Morphology and tightly scoped surface variants, not world synonyms.
    for pattern, value in (
        (r'\bfootprints?\b', 'prints'), (r'\bprint\b', 'prints'),
        (r'\bmuddy\b', 'mud'), (r'\b(?:track|trail|path)\b', 'track'),
        (r'\b(?:spotted|observed)\b', 'seen'),
        (r'\b(?:heading|following|taking)\b', 'taking'),
        (r'\b(?:beyond)\b', 'past'),
        (r'\b(?:weathered)\s+(?:stone\s+)?milestone\b', 'old milestone'),
    ):
        text = re.sub(pattern, value, text)
    return re.sub(r'\s+', ' ', text).strip()


_DOUBT = r'\b(?:perhaps|maybe|might|may|could|supposedly|allegedly|if|whether|seems?|suggests?)\b|\?'
_NEGATION = r"\b(?:not|never|isn't|wasn't|didn't|cannot|can't)\b"
_CONTINUITY = r'\b(?:again|already|previously|still|remains?|recall|remember|revisit\w*|return|once more|familiar)\b'
_NEW = r'\b(?:first time|newly discover\w*|new discovery|fresh discovery)\b'
_NO_NEW = (
    r'\b(?:nothing (?:new|further)|no (?:new|fresh|further|additional) '
    r'(?:clues?|information|discover\w*|evidence)|'
    r'(?:find|learn|reveal|uncover)\w* nothing (?:new|further)|'
    r'without (?:finding|learning|uncovering) (?:anything|something) new|'
    r'nothing beyond what you already know)\b'
)


def _route_shape(text):
    """Parse a finite reported movement relation, retaining subject and path.

    Requiring the whole relation prevents a list of matching words or movement
    by another actor from proving coverage. No action synonym crosses domains.
    """
    match = re.search(
        r'\bthe (?P<subject>[a-z ]{1,60}?) was last seen taking '
        r'(?:along )?the (?P<path>[a-z ]{1,80}?) past the (?P<landmark>[a-z ]{1,40})[.!?,;:]?$', text)
    return match.groupdict() if match else None


def _route(text, fact):
    shape = _route_shape(_normal(fact))
    if not shape:
        return None
    subject, path, landmark = (re.escape(shape[k]) for k in ('subject', 'path', 'landmark'))
    # Northwest mud / mud northwest are equivalent adjective order only.
    parts = shape['path'].split()
    paths = [path]
    if len(parts) == 3 and parts[-1] == 'track' and parts[1] == 'mud':
        paths.append(re.escape(' '.join([parts[1], parts[0], parts[2]])))
    path = '(?:' + '|'.join(paths) + ')'
    movement = rf'the {subject} was last seen taking (?:along )?the {path} past the {landmark}\b'
    reordered = rf'past the {landmark},? the {subject} was last seen taking (?:along )?the {path}\b'
    record = rf'(?:notices?|records?|reports?) place the {subject} on the {path},? past the {landmark}\b'
    directional = r'(?!)'
    if len(parts) == 3 and parts[1:] == ['mud','track']:
        directional = (rf'the {subject} was last seen taking {re.escape(parts[0])} '
                       rf'along the mud track past the {landmark}\b')
    candidates = re.split(r'(?<=[.!?])\s+', _normal(text))
    evidence = next((s for s in candidates if _has(movement+'|'+reordered+'|'+record+'|'+directional, s)
                     and not _has(_NEGATION+'|'+_DOUBT, s)), None)
    # Contradictory restatements do not disappear just because one sentence fits.
    relevant = [s for s in candidates if _has(rf'\b{subject}\b', s)]
    directions = set(re.findall(r'\b(?:northwest|northeast|southwest|southeast|north|south|east|west)\b', shape['path']))
    wrong = any((set(re.findall(r'\b(?:northwest|northeast|southwest|southeast|north|south|east|west)\b', s)) - directions)
                or _has(r'\b(?:was not last seen|will be seen|before the '+landmark+r')\b', s)
                for s in relevant)
    if wrong:
        return 'contradicted', None, {'relation':shape}
    if evidence:
        return 'covered', evidence, {'relation':shape}
    return 'ambiguous' if any(_has(_DOUBT, s) for s in relevant) else 'partial' if relevant else 'missing', None, {'relation':shape}


_FACETS = {
    'number': r'\bnumber\b|\bhow many (?:people|persons|travelers|prints)',
    'origin': r'\b(?:origin|source)\b|\bwhere they came from\b',
    'direction': r'\bdirection\b|\bwhich way they (?:went|go)\b',
}
_UNCERTAIN = (r'\b(?:unclear|uncertain|unknown|indistinct|unresolved|doubtful|ambiguous)\b|'
              r"\b(?:cannot|can't|unable to) (?:tell|determine|discern|establish)\b|"
              r'\bno evidence of\b')


def _uncertainty(text, fact):
    required = _normal(fact)
    # Only parse coordinated uncertainty when all facets are explicitly required.
    if not all(_has(p, required) for p in _FACETS.values()) or not _has(_UNCERTAIN, required):
        return None
    observation, sep, _ = required.partition(', but ')
    if not sep or 'prints' not in observation:
        return None
    # Preserve every observation detail using finite observation predicates.
    observation = re.sub(r'\bprints mark\b', 'prints', observation)
    required_terms = set(semantic._tokens(observation)) - {'mark'}
    sentences = re.split(r'(?<=[.!?])\s+', _normal(text))
    evidence = None
    facets = []
    for i, sentence in enumerate(sentences):
        # Adjacent anaphora only: "Their number..." must follow the observation.
        window = sentence + (' ' + sentences[i+1] if i+1 < len(sentences)
                             and _has(r'^(?:their|the prints|though|but)\b', sentences[i+1]) else '')
        terms = set(semantic._tokens(window))
        visible = required_terms <= terms and _has(r'\bprints\b', sentence)
        if _has(r'\b(?:no prints|prints (?:are|were) not|not visible|might be prints|absent|imaginary)\b', window):
            continue
        if not visible:
            continue
        # Each facet needs the same uncertainty predicate in its own clause.
        for clause in re.split(r'[.!?;]|\bbut\b|\bthough\b', window):
            if _has(_UNCERTAIN, clause) and not _has(r'\b(?:not unclear|not uncertain|no longer|not unknown)\b', clause):
                facets.extend(k for k,p in _FACETS.items() if _has(p, clause))
        evidence = window
        if set(facets) == set(_FACETS):
            break
    certain = _has(r'\bprints (?:lead|go|head) (?:toward|to|north|south|east|west)|'
                   r'\b(?:three|two|four|five|\d+) (?:travelers|people|persons)\b|'
                   r'\b(?:number|origin|source|direction) (?:is|are|remains?) (?:known|clear|certain|resolved)\b', _normal(text))
    if certain:
        return 'contradicted', None, {'uncertainty_facets':sorted(set(facets))}
    covered = set(facets) == set(_FACETS) and not _has(_DOUBT, _normal(text))
    return ('covered' if covered else 'partial' if evidence else 'ambiguous'), evidence, {'uncertainty_facets':sorted(set(facets))}


def mandatory_coverage(text: str, request: dict) -> dict:
    rows = []
    normalized = _normal(text)
    for fact in request['must_communicate']:
        result = None
        if fact['source'] == 'inventory_effect':
            from game.mechanical_claims import audit_mechanical_claims, _values, _supported
            effects = request.get('authorized_consequences') or {}
            audit = audit_mechanical_claims(text, {'state_changes': effects})
            claims = audit['claims']
            expected = [(k, v) for k in ('items_added', 'items_removed') for v in _values(effects.get(k))]
            covered = bool(expected) and not audit['reasons'] and all(
                any(c['category'] == k and c['supported'] and
                    _supported(c['claim'], [v])
                    for c in claims) for k, v in expected)
            result = ('covered' if covered else 'missing', text if covered else None, {})
        elif fact['source'] == 'engine_status':
            no_new = any(_has(_NO_NEW,s) and not _has(_DOUBT+'|'+r'\bnot (?:true|nothing|no new)\b',s)
                         for s in re.split(r'(?<=[.!?])\s+',normalized))
            repeat = fact['status'] != 'known' or _has(_CONTINUITY, normalized)
            result = ('covered' if no_new and repeat else 'partial' if no_new else 'missing',
                      text if no_new and repeat else None, {})
        else:
            result = _route(text, fact['text']) or _uncertainty(text, fact['text'])
        if result is None:
            # Unknown fact types require a literal proposition, not a bag of words.
            literal = _normal(fact['text']).rstrip('.!?')
            covered = any(literal in s and not _has(_NEGATION+'|'+_DOUBT, s)
                          for s in re.split(r'(?<=[.!?])\s+', normalized))
            result = ('covered' if covered else 'ambiguous', text if covered else None, {})
        classification, evidence, details = result
        if (fact['status'] in ('known', 'previously_known') and _has(_NEW, normalized)):
            classification, evidence = 'contradicted', None
        rows.append({**fact, 'decision':'PASS' if classification == 'covered' else 'REVIEW_REQUIRED',
                     'classification':classification, 'evidence':evidence, **details})
    return {'decision':'PASS' if all(r['decision']=='PASS' for r in rows) else 'REVIEW_REQUIRED',
            'facts':rows, 'scope':'bounded_deterministic_coverage_not_semantic_proof'}
