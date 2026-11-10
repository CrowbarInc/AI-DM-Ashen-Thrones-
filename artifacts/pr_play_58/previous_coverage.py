import re
from game import consequential_narration_validation as semantic
def mandatory_coverage(text: str, request: dict) -> dict:
    """Reuse PR55 normalization without a new synonym ontology.

    Match content within one sentence, preserving negative polarity and explicit
    uncertainty. Unrecognized paraphrases are REVIEW_REQUIRED, never inferred safe.
    The semantic gate independently checks contradictions and unauthorized claims.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    negative = re.compile(r"\b(?:nothing (?:new|further)|no (?:new|further|additional) (?:clue|information|discovery)|adds? nothing new|establish\w* nothing new)\b", re.I)
    repeated = re.compile(r'\b(?:again|already|previously|still|remains?|remember|recall|before|revisit\w*)\b', re.I)
    rows = []
    for fact in request['must_communicate']:
        needed = set(semantic._tokens(fact['text']))
        matched = None
        if fact['source'] == 'engine_status':
            matched = next((s for s in sentences if negative.search(s)), None)
            if fact['status'] == 'known' and not repeated.search(text):
                matched = None
        else:
            for sentence in sentences:
                # Negating a matching fact is not coverage. Ambiguous negation
                # is intentionally sent for review even if semantically harmless.
                if re.search(r"\b(?:not|never|isn't|wasn't|didn't)\b", sentence, re.I):
                    continue
                if needed and needed <= set(semantic._tokens(sentence)):
                    matched = sentence
                    break
        overlap = max((len(needed & set(semantic._tokens(s))) / max(1, len(needed))
                       for s in sentences), default=0)
        rows.append({**fact, 'decision': 'PASS' if matched else 'REVIEW_REQUIRED',
                     'classification': 'covered' if matched else
                     'ambiguous_paraphrase' if overlap >= .4 else 'missing_mandatory_outcome',
                     'evidence': matched, 'content_overlap': round(overlap, 3)})
    return {'decision': 'PASS' if all(r['decision'] == 'PASS' for r in rows) else 'REVIEW_REQUIRED',
            'facts': rows, 'scope': 'provisional_conservative_coverage_not_semantic_proof'}
