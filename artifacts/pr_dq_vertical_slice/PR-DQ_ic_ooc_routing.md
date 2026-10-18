# PR-DQ IC/OOC Routing

Classification chooses a destination. The destination chooses which function may run. It does not grant a world change.

| Mode and intent | Destination | Execution |
| --- | --- | --- |
| IC + ACTION | IC_ACTION | May call the experimental gameplay adapter when a hand-authored action is attached. |
| IC + DIALOGUE or QUESTION | IC_DIALOGUE | Same adapter, social question path when the action is hand-authored. |
| IC + any other intent | CLARIFICATION_REQUIRED | Not executed. |
| OOC + QUESTION | OOC_QUESTION | Deterministic non-mutating deferral. |
| OOC + CORRECTION | OOC_CORRECTION | Noted, or held for adjudication when the subject is COMMITTED_ACTION. |
| OOC + RULES_QUERY | OOC_RULES_QUERY | Deterministic non-mutating deferral. |
| OOC + any other intent | CLARIFICATION_REQUIRED | Not executed. An OOC override on an action sentence does not become an IC action. |
| MIXED | MIXED_MESSAGE | Deferred. Not passed to an IC resolver. |
| UNRESOLVED | CLARIFICATION_REQUIRED | Not executed. |

The four gameplay turns carry explicit IC metadata and a hand-authored action spec. The spec names an existing operation class and an existing resolver type: observe, question, scene_transition, or investigate. The adapter checks entity kind against the disposable scene, then calls `game.exploration.resolve_exploration_action` or `game.social.resolve_social_action`. An accepted scene transition updates the in-memory session and calls `advance_clock` once. It does not call `storage.activate_scene`.

There is no mixed-message segmenter. A mixed envelope is one history entry and one deferral.

Reclassification before `committed` is true updates the mode and destination. Reclassification after commit records POST_EXECUTION_CORRECTION, sets adjudication_required, and leaves the original text, mode, destination, and session in place.
