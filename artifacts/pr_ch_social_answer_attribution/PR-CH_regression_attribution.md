# PR-CH Regression Attribution

Historical evidence:
- PR-CE recorded `tests/test_social_question_relevance_answer_selection.py` as 20 passed, 4 failed.
- PR-CE recorded that the same four failures were observed before the subjective-classifier edit.
- PR-CF preserved the social relevance HTTP cluster and grouped it with response projection/fallback contract drift.

Attribution:
- Predates PR-CE: CONFIRMED.
- Introduced by PR-CE: not supported.
- Introduced by PR-CC: UNKNOWN.
- Related to broader dirty-tree final-emission/social fallback drift: SUPPORTED.

The defect is best attributed to current final-emission/fallback ordering and immutable-response behavior, not PR-CE subjective classification.

