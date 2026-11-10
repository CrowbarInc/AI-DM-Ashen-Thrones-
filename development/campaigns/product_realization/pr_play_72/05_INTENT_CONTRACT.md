# PR-PLAY-72 — 05 INTENT CONTRACT

The existing frozen ConversationalDecision carries category, intention, operation, target, confidence, ambiguity and missing information. Its existing operation record crosses the bridge. It is internal evidence and never returned as raw player metadata. No separate intent schema was added.

INSPECT and ASK reuse current visible-target mapping. CUSTOM extends the existing bridge for finite authored choices: the bridge recomputes a proposal from original player text and the current scene, checks the same target, enrollment and prerequisites, then passes only the server definition's id/type/label/prompt. Effects still come exclusively from authored_consequences.resolve. A narrow API exception bypasses NPC addressing only after this bridge accepts an authored choice. Provider proposals cannot grant this exception by naming an invented action.

The interpreter never saves, applies world updates, adds inventory or discovers clues.
