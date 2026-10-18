# 06 — Bounded Improvisation

## Permitted

Personal-state and opinion questions open the existing harmless-subjective plan: speech authority `claim_only`, incidental subjective allowed, durable mutation false, objective world authority none. The prompt says incidental speech is allowed only when `improvisation_permitted` is true and is not canonical.

A generated reply that also contains a consequential sentence can be reduced to one quoted remark that `classify_propositions` does not class as a consequential proposal and that `dialogue_rejection_reasons` does not flag. The rebuilt line is `Name says, "…"`. If that line passes the existing hard validation, it is sealed as the first attempt and the retry is not called. This is `incidental_quote_recovery` in `run_preserve_if_valid`.

Observed recovery: a model line that said both “It’s this quiet watch” and “the road beyond is usually calmer… something’s lurking” can be reduced to the quiet-watch remark. The live turn “What troubles you, standing out here?” was accepted as “It’s this watch, mostly.”

## Prohibited

The consequential-claim check rejects, among other phrases: a patrol schedule, “usually a patrol,” secretly serves, a promised payment, ten silver, the quest, “the password is,” “we’re married,” “I forged,” a new key, a hidden passage.

Proposition authority still rejects ungrounded world-truth rules. The decision audit still rejects unauthorized resolution facts. Quote recovery does not bypass those checks. It only resubmits a shorter line. If the short line fails, the retry and the safe fallback remain.

Hidden, promise, mystery, relationship, rumor, and unanswered surveillance or maker questions do not permit improvisation.

## Authority boundary

NPC speech is not written into topics or clues. The live conversation’s topic list was unchanged after every turn, including the personal remark and the reward request.

## Examples

- Acceptable in this cycle’s live play: “It’s this watch, mostly.”
- Rejected by validation before recovery, from a probed generation: “The road beyond is usually calmer at night, but lately, I’ve been uneasy—like something’s lurking just beyond sight.” Reasons: `ungrounded_authoritative_rule`, `unauthorized_resolution_decision_fact`.
- Not accepted as a preference in live play: “I do not know enough to answer that.” Improvisation was permitted and the narration ran once. The model did not offer a preference, and no safe preference quote was recovered.

## Known limitations

- Two determined lines cover every closed gap. They are not a personality.
- A preference question can still come back as ignorance after a full narration.
- Scene color such as “Sergeant Mara looks concerned” is not turned into speech.
- Recovery depends on the model putting a harmless remark in its own quotation. A single mixed sentence is dropped whole.
