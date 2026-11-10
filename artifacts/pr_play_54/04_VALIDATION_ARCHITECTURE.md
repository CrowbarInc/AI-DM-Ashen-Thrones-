# Validation architecture

The selected design is a hybrid, and it stays inside the quarantined prelude path.

```
Anchored investigation
        |
        v
SemanticAuthority
        |
        v
Candidate prelude
        |
        v
Existing validate_generated_response
        |
        v
Frame and relation claims
        |
        v
Comparison with the authority snapshot
        |
        v
PASS | FAIL | REVIEW_REQUIRED | VALIDATION_ERROR
```

`validate_prelude` still runs the previous checker. It then runs `validate_consequential_narration`. `apply_consequential_gate` copies that decision onto the audit.

- `PASS` leaves `hard_valid` as the previous checker set it. It never turns a previous rejection into a pass.
- `FAIL`, `REVIEW_REQUIRED`, and `VALIDATION_ERROR` set `hard_valid` false. The preview then uses the deterministic fallback (`semantic_rejection`).
- An exception becomes `VALIDATION_ERROR` with the exception type only. It is not a pass.

No model is called. The PR-PLAY-53 misses are classification failures on known sentences, so deterministic replay is sufficient. A second model call would add latency and another fabrication source, and its confidence would not be evidence.

Claim extraction is typed, not a list of forbidden sentences:

- Discovery, including presuppositions such as "the key you recovered".
- Inventory acquisition, only against `items_added`.
- NPC identity and confession.
- Mechanical success and failure, read from the authority success flag.
- Location access, hidden places, quests, conditions, and persistent gate-sealing.
- Direction contradictions and expansion predicates such as `unprotected`.
- Restricted-text overlap when a caller supplies restricted facts.

Metaphor, `wonder whether`, `as though`, conditionals, and a modal before the verb do not establish a fact. A presupposition still does. "The key you recovered should open the nearby door." is a discovery claim. "You wonder whether someone concealed a key nearby." is not.

Weak `find` / `notice` / `spot` claims fire for a consequential head (key, compass, route, culprit, and the rest of that set) that the authority does not contain. Surface words such as crack, grain, and rain do not fire. That split is why wax seals and cracks stay descriptive, and why an unlisted noun under `find` can still pass. Strong verbs (`discover`, `uncover`, `recover`, `locate`) do not use that head list.

`REVIEW_REQUIRED` is used for two scored lines: "The compartment yields." and "The lock resists your efforts." when the action succeeded and the lock was not an authorized outcome. Both block the prelude. They are not counted as passes.
