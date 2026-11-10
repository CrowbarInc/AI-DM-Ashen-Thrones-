# Mandatory outcome coverage

Counts: {'REVIEW_REQUIRED': 4, 'PASS': 4}

The narrow checker reuses PR55 content normalization and requires content within a sentence; it adds no synonym dictionary. Engine no-new status uses bounded negative-result patterns; repeats additionally require continuity wording. Unrecognized or potentially negated paraphrases return REVIEW_REQUIRED, with each fact classified as covered, ambiguous paraphrase or missing mandatory outcome. Never exact sentence matching. It is conservative and incomplete: token presence is not a proof of relation binding or semantic equivalence, and sentence splitting can cause false reviews. Independent raw-text review is pending. Coverage_decisions.json preserves evidence spans and overlap, which never substitute for semantic validation.
