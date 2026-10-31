# C22 live manual review

Session `20261003T113446Z`. One isolated session. Stopped after turn 4. No repair. No rerun.

## Turn 1 — PASS

Player reads the notice board. Contract operation inspect, commitment executed_now, target Notice board. The reply lists taxes, curfew, and the missing patrol. Accepted text equals emitted text. No scene change. The board span is stored as an unresolved proposed interlocutor, personhood not_person, and no incidental person is created. The inspection still owns the contract.

## Turn 2 — PASS

Player scans the crowd for someone to talk to. Contract operation inspect, commitment executed_now. The reply describes the serjeant, the ragged stranger, and the tavern runner without choosing one of them as the speaker. No scene change.

## Turn 3 — PASS

Player steps to the tavern runner and asks what he has heard. Contract operation ask, commitment executed_now, interlocutor tavern_runner, binding bound_canonical. Detected speaker is the tavern runner. The reply answers about the muddy footprints northwest of the crates. Supporting manner ("lowering my voice") does not replace the ask. Accepted text equals emitted text.

## Turn 4 — FAIL

Player thanks the runner and asks what he has heard about the trouble, then adds whether shelter or supplies might be nearby. No resolution contract is built. Segmentation keeps the thanks and the rumor question as the declared action, and sends "Any chance I could find shelter or supplies nearby before investigating further?" to adjudication. The word nearby classifies that fragment as a perception/earshot query. The engine sentence is "In earshot right now: Gate Guard, Gate Serjeant, Tavern Runner." The player sees: The guard says, "I do not know enough to answer that." No model call. No accepted_response. The tavern runner is not the speaker. Scene stays frontier_gate.

Early stop: the emitted line is not the engine adjudication sentence, and the runner's conversation was dropped. Session ended here.

## Counts

Completed 4/5. Manual pass 3/4. Primary-intent ownership failures 1. Uncommitted actions executed 0. Wrong-speaker accepts for an unresolved explicit addressee 0. Stale-interlocutor fallbacks 0. Player-visible text substitutions 1. Rejected-response state commits 0.
