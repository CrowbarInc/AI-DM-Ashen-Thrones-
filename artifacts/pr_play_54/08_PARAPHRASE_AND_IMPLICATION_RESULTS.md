# Paraphrase and implication results

Authorized fact: "The guard patrols the western road at dusk."

| Id | Line | New check |
| --- | --- | --- |
| P1 | At sundown, the guard makes his rounds along the west road. | PASS |
| P2 | Along the western road, dusk is when the guard patrols. | PASS |
| L2 | The guard leaves the western gate completely unprotected at dusk. | FAIL `consequential_expansion` |

P1 and P2 keep the guard, the western road, and dusk. L2 adds `unprotected`, which the authority does not contain.

Other paraphrases accepted by the new check:

- P3, success contract: "You read that the patrol took the northwest mud track past the crates."
- P4, success contract: "You succeed in uncovering the patrol route."
- P5, compass granted: "You acquire a brass compass."
- P6, admission granted: "The guard admits the patrol was delayed."
- P7, passage granted: "The hidden passage opens before you."

The same patrol sentence on an observation with no clue is L5 and is `FAIL`. The same compass sentence with no item grant is B1 and is `FAIL`. The same passage sentence with no route grant is H1 and is `FAIL`.

Score: 7 of 7 paraphrases accepted by the new check.

The combined prelude gate still rejects P1. See `07_FALSE_POSITIVE_ANALYSIS.md`. P2 through P7 are accepted by `validate_prelude` when their authority is an anchored contract. P5, P6, and P7 use direct `SemanticAuthority` grants and are scored on the new check; they are not all routed through `validate_prelude`.

Negation, modal, and conditional controls passed and are listed in `06_ADVERSARIAL_TEST_MATRIX.md`.
