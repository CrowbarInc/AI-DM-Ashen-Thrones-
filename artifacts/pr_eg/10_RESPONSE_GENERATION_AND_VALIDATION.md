# 10 — Response Generation and Validation

## Generation context

No new provider call was added. `authority_codes` copies the requested information, posture, improvisation flag, scope, narration-determined flag, and prohibited-claim labels onto the narration constraints and then onto the dialogue social plan. The player line is not sent. The prompt adds four instructions: answer the requested information, do not substitute another fact, allow incidental speech only when permitted and do not treat it as canon, and do not invent patrols, allegiances, rewards, quests, keys, or hidden facts. Unknown, unestablished, and withheld postures are to be said in character without naming speech authority or engine limits.

The provider cannot raise speech authority. The skip in `social_narration_unnecessary` returns true only when the authority record says narration is determined, incidental speech is not allowed, and speech authority is none. A bare `genuine_uncertainty` without that record still does not skip. That keeps `test_determined_nonresolution_skips_narration_and_characterization_does_not` on its previous expectation.

## Validation

Existing simulation checks remain: proposition authority, the resolution-decision audit, hidden-information leaks, mechanical contradiction, speaker conflicts. New dialogue reasons:

- `internal_authority_voice` for settled-here, speech authority, reply plan, canonical world, “not been established,” and information authority.
- `unauthorized_consequential_claim` for the prohibited patterns above.
- `answer_not_relevant` when a specific question is answered without the support pattern and improvisation is off.

When improvisation is permitted and the NPC’s name is in the line, a missing quotation does not by itself add `interaction_incomplete`. “The guard captain shrugs and nods.” stays valid.

## Rejected example

Probed generation for “What troubles you, standing out here?”:

> Sergeant Mara glances toward the soot-streaked lantern hanging beside the courtyard gate before meeting your gaze. “It’s this quiet watch,” they say, voice low and concerned. “The road beyond is usually calmer at night, but lately, I’ve been uneasy—like something’s lurking just beyond sight. The side gate being barred only adds to the tension. I can’t say for sure what’s coming, but I keep my eyes peeled.”

Reasons on the whole text: `ungrounded_authoritative_rule`, `unauthorized_resolution_decision_fact`. The road-is-calmer sentence is a consequential geography proposal. It was not sealed.

## Accepted examples

- “Sergeant Mara mutters, ‘Word is, the street beyond the gate is the north road.’” for the name of the street.
- “Sergeant Mara says, ‘It’s this watch, mostly.’” for what troubles her, after quote recovery, with no retry.
- “Sergeant Mara says, ‘I couldn’t tell you.’” for the lantern.
- “Sergeant Mara says, ‘I couldn’t answer that.’” for the password.
- Unit recovery: “Sergeant Mara says, ‘It’s this quiet watch.’” from a draft that also said the road is usually calmer and that something is lurking. The retry callback was not invoked.

## Not weakened

Consequential invention, hidden leaks, and unauthorized decision facts still fail the full text. Recovery only succeeds when the shorter line passes the same validator. A determined line that fails validation still falls through to the generic invalid sentence rather than being forced through.
