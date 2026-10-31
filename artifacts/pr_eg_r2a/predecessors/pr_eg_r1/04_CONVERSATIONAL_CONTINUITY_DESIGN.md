# 04 — Conversational Continuity Design

Module: `game/conversational_continuity.py`.

Orchestration converts a directive into the existing `ConversationalDecision`. The continuity module does not import that type.

## What is stored

`conversational_context.delivered_exchanges` records only the sealed player-facing line, after validation. The fields are speaker, addressee, the player's question, the delivered sentence, the quoted supplied text, the subject, the requested-information kind, uncertainty, and scene.

Four layers stay distinct:

| Layer | Used as what the player heard |
| --- | --- |
| Proposed response | No |
| Generated candidate | No |
| Validated-but-replaced text | No |
| Delivered line | Yes |

An internal-voice line is forced to GM ownership and is not treated as NPC speech.

## Precedence

1. Explicit player wording. "I ask Corporal Bren," a scene question, a rules question, a hidden-information question, an undo, and a world action leave this path. A named vocative ("Sergeant Mara, …") selects that NPC.
2. The immediately preceding relevant delivered statement, for "what did you mean," "say that again," "that name," and "why that one."
3. The active topic, by overlap with the supplied sentence. A possessive such as "road's" counts as "road." An uncertain answer does not outrank a sentence that actually supplied the fact.
4. The established interlocutor, if that NPC is still in the scene. A stale interlocutor does not override a newly named person.
5. Earlier dialogue. If the speaker has left, the engine quotes the old line and says the speaker is not here.
6. Authoritative scene context, only when no delivered exchange matches. That remains the existing scene and resolver path.

If two NPC speakers are equally plausible and the player did not name one, the engine asks which remark was meant and does not execute.

## "What did you mean by that?"

When the speaker is still present, this stays an authorized ask, so the PR-EF-R4 execute-NPC holdout still advances the social turn. Dialogue authority then fills the line from the delivered statement and narration is skipped. The player hears the quote. The provider is not called.

A GM or third-person question ("what did she mean," "GM, what did she say") quotes the same statement and does not contain "says,". No new NPC dialogue is generated.
