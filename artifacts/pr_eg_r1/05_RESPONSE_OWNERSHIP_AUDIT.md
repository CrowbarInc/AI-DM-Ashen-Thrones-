# 05 — Response Ownership Audit

The PR-EF-R4 contract is unchanged. Continuity either returns a non-mutating answer or an authorized ask. It does not grant a new operation.

| Player-facing kind | Path | What the player hears |
| --- | --- | --- |
| GM scene answer | Existing scene path. Continuity returns none for describe / what can I see. | Courtyard or street description. No NPC speech. |
| NPC answer | Authorized ask, or a quote of a delivered line. | "Sergeant Mara says" or "mutters," plus the sentence. |
| GM describing behavior | Movement and inspection resolvers. | Arrival line, or the lantern mark. |
| Rules limitation | Existing rules path. Continuity returns none for rules wording. | Unchanged. |
| Clarification | Ambiguous history, or an absent NPC. | Which remark, or "is not here." Nothing is attempted. |
| NPC refusal | Negotiation directive. | "I can't promise you a reward for that." |
| NPC uncertainty | Determined maker / unknown ask. | "I couldn't tell you." |
| Resolver narration | Inspection and movement. | Resolver-owned line. No dialogue authority. |

## Paths that used to bypass the boundary

- Empty-evidence GM answers no longer fire for an ordinary question while an interlocutor is present, except GM-help wording ("interpret the situation") and questions about what the player already knows.
- The unsupported-command template is not used for a promise request. Continuity answers before that template.
- Personal ignorance is replaced on the sealed social line before it is recorded, including when the narration lifecycle did not run the earlier recovery.

## Live check

Neither fresh transcript contains "not been established," "cannot carry out," "speech authority," "available actions," or "which person, object, or pending action."

A GM recall uses "said:" and does not start with "says,".
