# Authority comparison

`SemanticAuthority` is unchanged as a container: observable scene, authorized discoveries and outcomes, restricted strings, a success flag, and structured grants (`items_added`, routes, objectives, conditions, dialogue). `authority_from_anchored` still copies only the public anchored view. It does not copy hidden fixture fields.

For a candidate object the check asks, in order:

1. Is every content token already in the authority pool? Locative participles such as `recorded` and `written` are ignored so a known route can be described as recorded on a visible board.
2. If the object is new, the claim fails. An authorized route does not license a new noun such as a cipher or a paymaster.
3. A departure (`leaves from`, `departs from`, `sails from`) fails when the place is not in the pool. "The night barge leaves from the lower jetty." passes when that sentence is the authorized fact. "The night barge leaves from the upper quarry." fails.
4. `unwatched`, `unmanned`, `unguarded`, and `unprotected` fail unless that predicate is itself authorized. "The western gate is completely unguarded at dusk." still fails against a patrol fact.
5. Compass opposites on a shared topic still fail. East against an authorized west road is `discovery_contradiction`, reason code `CONTRADICTORY_AUTHORITY`.
6. Restricted overlap and frames such as `secretly reports` still fail. Reason code `POTENTIAL_HIDDEN_DISCLOSURE` is attached to restricted-text hits.
7. If the sentence is only an unfamiliar mark, the decision is `REVIEW_REQUIRED`. Uncertainty is not converted to `PASS`.

Paraphrase examples that pass:

- "At sunset, the sentry makes his rounds along the west road." against "The guard patrols the western road at dusk."
- "You uncover the patrol route recorded on the notice board." against the northwest-track clue.
- "You learn that the night barge leaves from the lower jetty." against that same sentence in the holdout authority.
- "You acquire the oilskin pouch." when `items_added` contains `oilskin pouch`.

`You learn that the western gate is unwatched at dusk.` fails. The jetty fact does not make the jetty unwatched.

`VALIDATION_ERROR` is still the result for a non-string or a non-authority input, and for an exception inside the check. `apply_consequential_gate` cannot turn that into a pass.
