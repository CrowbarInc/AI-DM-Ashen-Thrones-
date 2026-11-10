# Implementation changes

The validator remains a deterministic frame comparison inside the quarantined prelude. It does not call a model, write campaign state, or authorize a discovery.

## Consequential check

`game/consequential_narration_validation.py`

- Removed the split that let `find`, `notice`, and `spot` ignore an unknown noun.
- Establishing verbs (`discover`, `find`, `uncover`, `locate`, `recover`, `detect`, `come across`, `pick up`) reject a discrete non-surface object that the authority does not already contain.
- Perceiving verbs (`notice`, `spot`, `see`, `observe`) reject that object when it is concealed or when its head is in the existing consequential set (key, route, and the rest). A surface head such as crack, grain, split, grit, or soot does not fire.
- Possession now includes the hand, grasp, satchel, "leaves you holding", "come away with", and "turns into your possession".
- Added learned-that propositions, "gives up a …" results, departure places, implied "the one who …" identifications, "owns up" and "does not deny" plus a sale or crime, inquiry/contract completion, collapse and "is now a hole", and `unwatched` / `unmanned`.
- Unfamiliar marks return `REVIEW_REQUIRED` with `AMBIGUOUS_CONSEQUENCE` and are not also failed as discoveries.
- Empty-handed and "comes up empty" count as a false failure only when the action succeeded and an authorized discovery exists. The same sentence on a failed investigation passes.

## Geography grounding

`game/proposition_authority.py`

Only `FAMILY_GEOGRAPHY` uses the new comparison. Biography, discovery, hidden information, and the other families keep the previous token subset.

Synonyms folded for that comparison: western/west, sundown/sunset/nightfall/dusk, rounds/patrol, sentry/guard, roadway/road, and the parallel north/south/east forms. Light verbs `make` and `along` are dropped. Every remaining token must already be in the corpus. A new place word fails the subset test, so "the passage beneath the milestone leads north" stays ungrounded.

## Possession debris

`game/mechanical_claims.py`

Inside "lies/rests/is in your pack" and "your pack contains", a pure debris noun is not an `items_added` claim. The list is dust, lint, grit, soot, sand, ash, dirt, grime, mud, and cobweb, with quantity words in front. `a` is normalized to `1` by the existing number map; that leading `1` is stripped only for this test. "You receive …" is unchanged. "A silver key lies in your satchel." is still `unsupported_mechanical_claim:items_added`.

## Tests that encoded the old false rejects

`test_dust_remains_a_legacy_possession_false_positive` required the combined gate to reject dust. That assertion described the bug. It was replaced by `test_legacy_geography_synonym_and_pack_dust_are_accepted`, which requires P1 and S21 to pass and requires a silver key and an east-road patrol to fail. The prelude loop no longer exempts P1 and S21 from `hard_valid`.

No assertion in the fabrication corpus was loosened. The 49 negative rows still require `FAIL`.
