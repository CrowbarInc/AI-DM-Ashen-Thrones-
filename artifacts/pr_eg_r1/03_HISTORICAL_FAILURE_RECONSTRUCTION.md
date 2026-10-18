# 03 — Historical Failure Reconstruction

Traced from the PR-EG live transcript and the production decision path. The six cases do not share one root cause.

## Case A — Immediate follow-up

Player: "What did you mean by that?" after Mara named the north road.

Earliest wrong decision: dialogue authority classified the question as a general unknown about the subject "mean." Narration was not determined, so strict-social narration ran, failed validation, and retried. The delivered north-road sentence was not the answer source.

Downstream: about 52,957 input tokens, then "I couldn't tell you."

Class: lost delivered statement, then a narration retry spent to reconstruct it.

## Case B — Response ownership

Player: "Has anyone been keeping an eye on it after dark?"

Earliest wrong decision: the empty-evidence GM answer in conversational orchestration. Authorization and dialogue authority were not attached. The owner became the GM.

Downstream: "That has not been established in the information available to you."

Class: NPC question emitted as an internal information-authority line.

## Case C — Personal question

Player: "Do you prefer the morning or the evening?"

Earliest wrong decision: the model said it lacked knowledge, and validation accepted that line. Improvisation was permitted. The reply was not replaced.

Downstream: "I do not know enough to answer that." One narration, no retry.

Class: harmless preference treated as missing world knowledge.

## Case D — Correction

Player: "I meant the road, not how you feel."

Earliest wrong decision: the text matched a revision pattern and the last intention was already executed, so the pending-revision path refused an undo.

Downstream: "That action already resolved, so I cannot undo it."

Class: topic correction classified as a world-state reversal.

## Case E — Negotiation

Player: "Promise me a reward if I carry a message for you."

Earliest wrong decision: interpretation status unsupported request. The player-facing template interpolated the internal operation summary.

Downstream: "I cannot carry out Speak to Sergeant Mara and say: …" No reward was created.

Class: social request rendered as an unsupported command.

## Case F — Distant reference

Player, after leaving: "Earlier you could not tell me who watches the north road. Is that still where you stand?"

Earliest wrong decision: the earlier statement was not a recognized referent, and Mara was not in the arrived scene, so the clarifier asked which person, object, or pending action.

Downstream: the historical remark was discarded. Remote speech was correctly not invented, but the reference was lost.

Class: absent speaker with no retained delivered statement.
