# PR-CJ Authority Integrity

Live provider calls: 0. No game code was changed in this cycle.

## Checks

| Control | Result |
| --- | --- |
| `gm_resolution_decision` authority | Preserved. No edit to decision ownership. Cluster C retries through the existing decision audit. |
| Claim-only NPC speech | No new NPC claim was sealed as world fact in the traced failures. Wrong-speaker text was replaced by safe nonresolution, which drops both the unauthorized speaker and the canonical speaker. |
| Authored objective facts | Desk-clue discovery still works on `/api/action`. Chat investigation no longer applies that authored clue. That is a missed authorized mutation, not a provider fact becoming authoritative. |
| Consequential information | The place adjudication and the safe line do not add routes, orders, or evidence. |
| Narration-only envelope | Not altered. Cluster C shows the narration-only retry sentence already in use. |
| Structured realization | Not altered. |
| Retry-contract preservation | Not altered. Cluster C shows the immutable prompt and the older `Retry target:` prompt disagree. |
| Immutable-response integrity | Not altered. Rejected candidates are still replaced before seal. The replacement for several passive and speaker tests is the generic safe line. |
| C18 state and provenance | No unauthorized session write was identified. Chat investigation omits the desk clue. Provenance stamps were not reassigned. |

## Not an authority regression

Decision E was not used. The reproducible problem is mis-selection and omitted engine results. Traced provider sentences were not stored as clues, world flags, or decision facts.

Focused authority and immutable suites passed after this diagnostic. See `PR-CJ_regression_results.md`.
