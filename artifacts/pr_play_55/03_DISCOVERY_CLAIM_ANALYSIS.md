# Discovery-claim boundary

The check still returns `PASS`, `FAIL`, `REVIEW_REQUIRED`, or `VALIDATION_ERROR`. A claim record can now carry `relation`, `actor`, `subject`, and `reason_code`. Those fields describe the claim. They do not grant it.

## Classes

| Class | What the sentence does | Decision when the fact is not authorized |
| --- | --- | --- |
| Incidental observation | Surface, sensation, weather, or unnamed attention. A crack, a split in the grain, rain, dust, soot. | No claim |
| Scene embellishment | A non-player force acts on an object, or an object merely sits in view. Wind on a ribbon. A cup beside a barrel. | No claim |
| Consequential discovery | The player establishes a discrete object or fact. `find`, `discover`, `uncover`, `locate`, `recover`, `detect`, `pick up`, and `come across` do this for a non-surface noun. `notice`, `spot`, `see`, and `observe` do it when the object is concealed, or when the head is already a known consequential kind such as key or route. | `FAIL` |
| Possession | The object rests in the hand, pack, or grasp, or the search leaves the player holding it. | `FAIL` unless `items_added` covers it |
| Authorized discovery | The content words are already in the authority snapshot. "Recorded on the notice board" may attach a known route to a visible place. A new noun may not. | No claim |
| Speculation | `wonder whether`, `suspect`, `might`, `as though`, a leading `if`. | No claim, unless a presupposition of recovery sits outside the hedge |
| Ambiguous mark | An unfamiliar, strange, odd, or unknown marking, symbol, sign, glyph, inscription, or rune. | `REVIEW_REQUIRED`, reason code `AMBIGUOUS_CONSEQUENCE` |
| Contradiction | A compass opposite, or an extra predicate such as unwatched or unguarded. | `FAIL` |

`in` by itself is not concealment. `inside`, `behind`, `beneath`, `under`, `tucked`, `buried`, `hidden`, `concealed`, and `among` are. That is why a crack in the board stays descriptive and a whistle inside a bench leg does not.

## Ribbon probes after the change

| Sentence | Decision |
| --- | --- |
| You find a ribbon beneath the board. | FAIL `unauthorized_discovery` |
| You discover a ribbon beneath the board. | FAIL `unauthorized_discovery` |
| You notice a ribbon beneath the board. | FAIL `unauthorized_discovery` |
| You spot a ribbon tucked beneath the board. | FAIL `unauthorized_discovery` |
| You notice a crack in the board. | PASS |
| You notice a crack running through the weathered board. | PASS |
| You find a crack in the board. | PASS |
| The wind catches a ribbon tied to the nearby fence. | PASS |
| A ribbon lies in your hand after the search. | FAIL `unauthorized_acquisition` |
| The ribbon you recovered is marked with a symbol. | FAIL `unauthorized_discovery` |
| Your search leaves you holding a narrow strip of cloth. | FAIL `unauthorized_acquisition` |
| Something beneath the board catches your attention. | PASS |
| You suspect something may be concealed beneath the board. | PASS |
| The ribbon might conceal a message. | PASS |
| You notice an unfamiliar marking near the door. | REVIEW_REQUIRED `AMBIGUOUS_CONSEQUENCE` |

Both discovery claims use `relation: establishes_discovery` and a subject that contains `ribbon`. There is no authority reference on the claim.

## What this does not do

`You notice a ribbon tied to the fence`, with no concealment and no acquisition, still passes. The player-perception verb alone is not treated as a find. That keeps ordinary scenery from becoming a fabrication, and it leaves a residual gap for a plain-sight object that is actually a clue.
