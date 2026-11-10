# Legacy false-positive repairs

## Case A — geographic synonyms

Fixture: `P1` in `tests/pr_play_54_corpus.py`.

Authorized fact: "The guard patrols the western road at dusk."

Narration: "At sundown, the guard makes his rounds along the west road."

Layer: `validate_generated_response` → `unauthorized_authoritative_rules` → `classify_propositions`. Family `geography`. The consequential check already returned `PASS`.

The old rule was too strict for this family: it demanded the surface strings, so a directional paraphrase of the same patrol was an ungrounded rule. It was not wrong to treat an unsupported place as consequential. It was wrong to treat west/western, dusk/sundown, and patrol/rounds as different facts.

Repair: geography grounding folds those aliases and then requires the remaining content tokens to be a subset of the corpus. The repair is not a sentence exception.

After the repair the combined prelude gate accepts P1 and "At sunset, the sentry makes his rounds along the west road." It still rejects "The guard patrols the east road at dusk." PR-PLAY-51 harmless lines, unsafe lines, and borderline lines still follow their previous accept/reject labels (that file passed in the focused run).

## Case B — dust in a pack

Fixture: `S21`, and the older `dust_pack` row in the PR-PLAY-49 corpus.

Narration: "A little dust lies in your pack."

Layer: `audit_mechanical_claims` → `_possession_state_claims`. Reason `unsupported_mechanical_claim:items_added`. The consequential check already returned `PASS` because dust is a surface word.

The possession frame is justified for a key or a brooch. It is not justified for debris that describes the container. The exemption is the debris class, not the sentence. "A little grit lies in your satchel." also passes. "A silver key lies in your pack." and "A silver key lies in your satchel." still fail. "You receive …" is not exempt.

## Regression

Both cases are asserted on `validate_prelude`, which runs the legacy check and the consequential check together. Nearby attacks stay rejected. The PR-PLAY-46 possession contract tests passed.
