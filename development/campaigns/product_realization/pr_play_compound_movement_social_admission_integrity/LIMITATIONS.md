# Limitations

The inherited compound no longer travels. Three related sentences still spend a gameplay turn.

“I go to the fortress trail looking for the guard.”
“I go to the fortress trail so I can persuade the guard.”
“I go to the fortress trail because I want to persuade the guard.”

Each is one COMPLETE MOVE. `_PURPOSE_RE` does not split them. The new compound gate runs only on INCOMPLETE coverage, so it does not see them. The destination phrase keeps the participle or the reason. The exploration resolver is invoked with `leave_for_seek_the_fortress_trail`, `resolved_transition` is false, the scene stays `market_quarter`, and turn, tick, and pressure each increase by 1. Publication: “You try to move, but no reachable destination is established from here.” Social resolver is not called. No arrival and no persuasion.

That path is the existing failed scene-transition line in `game/api_turn_support.py`. This milestone did not change destination binding, because the route/destination invariant was not to be rewritten in order to fix compound admission. The sentences are not the identity `admission/compound-social`. They are the reason this milestone is not overall-integrity clean.

Other purpose wording declines with zero turns and awkward destination text, for example “the gate because I want” and “the fortress trail hoping”. Those are the same binder. They do not spend a turn.

“I head to the market to look for work.” is classified INSPECT because “look” matches the inspect cue before movement. From Market Quarter that is a zero-turn decline, not a withheld compound and not a trip.

“I persuade the guard after I arrive at the fortress trail.” is owned by the existing social checker because the sentence starts with “I persuade”. It refuses: no present person, check not made. It does not travel.

The compound clarification asks whether to do the first step. That question does not travel by itself. Confirming later is a separate request. Unsupported future steps are not stored as executable intentions after a confirmed move.

No live play was run. No provider was called. T06 and T13 scenery were not touched. Combat and exploration were not redesigned.
