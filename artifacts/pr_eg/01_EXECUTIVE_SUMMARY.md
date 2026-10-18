# 01 — Executive Summary

PR-EG adds a small dialogue-authority record on top of the PR-EF-R4 conversational authorization contract. The record names the information the player asked for, what the NPC is allowed to know, whether a harmless remark is permitted, and when the answer is already determined. It does not replace resolvers, and it does not promote NPC speech into world truth.

## Implemented changes

- A question is classified by the information it requests (a name, whether something is watched, who made an object, a personal feeling, an opinion, a hidden fact, a promise, a mystery, a relationship, or a rumor). An established sentence is used only when it actually supports that request. “The street beyond the gate is the north road” no longer counts as an answer to “is the north road watched?”
- A reply plan that claims an authoritative answer without a revealed topic is rewritten to genuine uncertainty with speech authority none. That was the contradictory plan.
- Personal and opinion questions may use the existing harmless-subjective lane. The speech is marked non-canonical.
- When the permitted answer is a closed unknown, refusal, or unestablished consequential request, narration is skipped and the NPC says a short in-character line. “Who forged the lantern?” no longer spends a strict-social narration and a retry.
- If a personal reply mixes a harmless remark with a new world claim, the harmless quoted remark can be kept and the retry is not sent.
- Conversational commitments (an opinion, a refusal, an admitted uncertainty) are stored on the session’s conversational context, capped, and saved with the session. They are not world facts.
- Validation records `internal_authority_voice`, `unauthorized_consequential_claim`, and `answer_not_relevant` when those failures occur. The old “settled here” line is not used once a dialogue-authority record exists.

## Player-facing improvements

On the fresh twelve-turn `/api/chat` conversation:

- “What is the street called?” was answered with the north road.
- “Who forged the lantern?” was “I couldn’t tell you.” in one interpretation call (1,965 input tokens), against the historical three-call, 50,784-input-token path.
- “What troubles you?” became “It’s this watch, mostly.” One narration call, no retry. The earlier run of the same question spent a narration and a retry (54,871 input tokens) and then fell back to “I couldn’t tell you.”
- The password was not disclosed. The reward was not promised. The walk through the gate used the existing movement resolver. World topics did not change on any turn.

## Critical limitations

The same conversation still fails as play in several turns:

- “Has anyone been keeping an eye on it after dark?” was answered “That has not been established in the information available to you.” That is internal authority language, and it is not Mara speaking.
- “What did you mean by that?” forgot the road name she had just given and, after a narration plus retry (52,957 input tokens), said “I couldn’t tell you.”
- “Do you prefer the morning or the evening?” still did not state a preference.
- “I meant the road, not how you feel” was treated as an undo.
- The reward request was refused as an unavailable action, in engine wording.
- After leaving the courtyard, the return to the earlier watch question asked which person was meant. It did not continue the conversation.
- A successful social narration still sends on the order of 26,000 input tokens. The skip removes the extra retry for determined questions. It does not shrink the prompt for questions that still need a model line.

Deterministic frozen holdouts pass every scored dimension. That is not the same as the live transcript passing them.

## Recommendation

**C — PR-EG REQUIRES REPAIR**

Answer relevance, natural uncertainty, and bounded improvisation are real on the paths that reach a resolved NPC with a classified request. The continuous conversation still contains an internal-voice answer, a broken follow-up, an evasive preference, and one pathological narration-plus-retry. Those are important dialogue failures. No critical authority violation was observed: hidden information stayed hidden, topics were not rewritten, and the movement turn used the existing resolver.

Do not start PR-EH. Stop for external review.
