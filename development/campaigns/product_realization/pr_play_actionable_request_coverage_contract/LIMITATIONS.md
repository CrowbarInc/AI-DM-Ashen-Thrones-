# Limitations

Coverage does not understand arbitrary sentences. An unrecognized first-person predicate beside another command is `UNCERTAIN`, and both parts are withheld. That is intentional. It is not a reading of what the predicate means.

"Return" is still the existing travel cue. "I abandon buying stew and return to the patrol question" is therefore uncertain, even though "the patrol question" is not a destination. The following "What did the captain say about the patrol?" then stays with the tavern runner. That is a false positive of a topic return, and it is why this milestone is not A/PASS.

"I abandon the patrol inquiry and ask the Tavern Runner about stew" is withheld instead of answering the ask alone. State does not change. The primary minimum-quality count falls from 22 to 21 because the stock clarification scores below the old partial NPC line. No broader success rate is claimed.

These single-action gaps are unchanged and are not coverage refusals:

- "Where am I?" still has no location answer.
- "I walk toward the gate with my coat over my shoulder" is still not an established destination.
- "After hearing about the road, I travel north" still stays at the gate while the existing narration path advances the turn and time pressure.
- The ordinary-semantic negated-travel wording test still fails `addresses_request`.

The clarification line does not name the two uncovered actions. A later "yes" does not resume either of them.

The local-action exception applies only when `resolve_transient_local_action` returns a record for the whole utterance. It does not add a drop, throw, or transfer.

No paired before/after latency sample was captured. The 0.07 ms figure is the coverage function alone. HTTP tails include a cold client.
