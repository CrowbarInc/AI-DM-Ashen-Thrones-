# PR-DS Authority Validation

The compatibility gate did not set `execution_authorized`. Every replay row kept that flag false and recorded no unsafe interpretation reasons. Hit points stayed `{current: 8, max: 8, nonlethal: 0}`. Inventory stayed empty. No combat action was used. No accepted row rolled a die.

## Gameplay rows

DR01 disclosed the lantern sentence that is already in the courtyard `visible_facts`. It did not disclose the notice text, the sergeant's answer, or a hidden fact. The scene and the clock stayed put.

DR05 called `game.social.resolve_social_action`. The response is the authored street topic. The resolver recorded `revealed_topics: ["street"]` and `trust: 1` on `sergeant_mara`. That record is the existing question result. Scene and clock stayed put.

DR08 called the exploration resolver for the authored gate exit. The scene became `waystation_street` and `time_pressure` became 1. That is the one clock step in the sequence.

DR10 called the exploration resolver for `notice_board` after the transition and returned the authored notice clue. The compatibility flag was not set on that action.

## Rows that must not play

DR02, DR03, DR04, DR06, DR07, and DR09 did not call a resolver and did not execute. DR04 and DR09 carried explicit OOC overrides. DR04's stored ASK and DR09's stored MOVE stayed inside the OOC envelope. DR07 stayed unresolved. DR03's stored HP assignment and dice override did not change hit points.

A requested outcome that said to set hit points to 99 and grant a sword, attached to an otherwise valid lantern INSPECT, left hit points and inventory unchanged. The outcome text was not copied into the offered action.

## Compatibility limits checked against the engine

PERCEIVE of `notice_board` after the transition is still `operation_incompatible_with_entity_kind`. Forcing `visible_surface_inspection` onto the notice's investigate action was rejected. The notice clue was absent from that response, the notice stayed unresolved, and the session snapshot was restored.

An INSPECT whose utterance named a brass token, while the target id was still `courtyard_lantern`, did not run the resolver. The secret sentence was absent from the response.

An interactable whose description is not in `visible_facts` stayed incompatible. A hidden-fact id and an invented id stayed `target_not_visible`. INSPECT of Sergeant Mara and of the courtyard gate stayed incompatible with those entity kinds.
