# 08 — Resolver Handoff

Authorized operations are the existing bridged actions. The bridge keeps the grounded canonical id, including when that id disagrees with the provider. Resolvers are unchanged and still own success, failure, time, and faction updates.

## Social

Live and scripted explicit asks of Mara reach `resolution.social` with `npc_id=sergeant_mara` and `target_resolved=true`. The taller-guard holdout reaches `corporal_bren` when the world states the height. Unresolved addresses do not call the social resolver: the live ambiguous turn has no social payload.

A follow-up whose interpretation is malformed never reaches the resolver. That is the isolated `npc_followup` holdout. The in-conversation follow-up did reach it.

## Exploration

“I inspect the courtyard lantern.” Live turn 8: kind `discover_clue`, action the lantern, text “A small maker’s mark is stamped beneath the lantern.” Turn 3 → 4. Interpretation only; the clue line is resolver-owned, so narration was not called. Performance case D matches.

## Movement

“I walk through the courtyard gate.” Live turn 10: kind `scene_transition`, scene `waystation_street`, no provider call. The deterministic move path still owns the destination.

## Compound and conditional

“I ask Mara about the road, then leave.” Scripted and live-holdout: no social execution, scene unchanged, both ask and leave remain named. The existing compound confirmation is required.

“Does the gate look safe? If so, I go through.” Live turn 9: kind `conversational_clarify`, zero provider calls, scene unchanged, “No part of the action has been attempted.” The condition was not established, so the move did not run. The next explicit move did.

## Preservation

The pre-tick gate does not replace an authorized move or inspect with an addressee clarification. “I thank the guard and head toward the docks.” still resolves the docks exit. “Where can I find them?” with an active interlocutor still routes to the social exchange. Those regressions were checked after the speech-act nominal was narrowed so that `toward` and `find` are not person addresses.
