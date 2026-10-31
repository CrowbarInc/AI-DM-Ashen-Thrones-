# 01 — Executive Summary

PR-EG-R1 repairs conversational continuity and response ownership without replacing the PR-EF-R4 authorization contract.

## Implemented repairs

- The line actually delivered to the player is stored as a bounded exchange. Rejected narration and discarded provider candidates are not stored.
- A follow-up can ground "that," a paraphrase, a possessive ("the road's name"), or an earlier topic in that delivered statement.
- If the player is still speaking to that NPC, the reply stays in the NPC's voice. A GM question about what the NPC said quotes the earlier line and does not start a new NPC turn.
- A conversational correction updates the topic. It does not emit an undo refusal for a completed social action.
- A harmless preference that comes back as ignorance or a one-word refusal is replaced with a stable non-canonical preference. A later question reuses it.
- A request for a promise or reward is declined in the NPC's voice. No quest, payment, or inventory change is created.
- An earlier statement can be recalled after the character leaves. The absent NPC is not spoken to from the new scene.
- Scene descriptions are dropped from the exchange window before an NPC statement, so a short move-and-inspect sequence does not erase the last useful answer.
- Follow-ups that the engine can already answer do not start a narration or a retry.

## Player-facing improvement

Fresh `/api/chat` play, model route `gpt-4.1-mini`, two disposable campaigns, frozen checks written before the run:

- Fifteen-turn conversation: 0 frozen failures. 6 provider calls, 2 narration calls, 0 retries, 56,440 input tokens.
- Independent twelve-turn conversation: 0 frozen failures. 4 provider calls, 2 narration calls, 0 retries, 53,374 input tokens.

"What did you mean by that?" now repeats the north-road sentence with no provider call. The historical failure of that turn spent about 52,957 input tokens and answered "I couldn't tell you."

## Remaining limitations

- "Say that again in plainer words" repeats the sentence under "I meant this:" rather than restating it in new words.
- The first street-name question and a preference question still each send one strict-social narration of about 24,000–26,000 input tokens. There is no retry. The prompt itself was not rewritten.
- The preference the player hears is a stable "I prefer the evening," not a longer characterization.
- Nineteen inherited regression identities remain. No new failing identity was introduced.

## Recommendation

**B — PR-EG ACCEPTED WITH LIMITATIONS**

Ordinary conversation now keeps the previous delivered meaning, the speaker, and the authority boundary. The remaining gaps are phrasing stiffness and the size of the first social narration, not lost context or internal software language.
