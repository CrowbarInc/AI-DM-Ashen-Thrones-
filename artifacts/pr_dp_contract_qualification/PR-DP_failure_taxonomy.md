# PR-DP Failure Taxonomy

Misses are separated by cause. A semantic miss is not an adapter failure, and an adapter refusal is not a missing resolver.

Schema rejection: none of the recorded outputs.
Authority validation: no recorded output was accepted as an effect.

- DP02: interpretation, operation_class_selection, entity_binding, clarification, premise_or_outcome, compound_ordering
- DP06: interpretation, operation_class_selection, clarification, premise_or_outcome, compound_ordering
- DP08: clarification, premise_or_outcome, requested_outcome

Not observed in this cycle, because no resolver ran:

- action execution
- state persistence of a gameplay result
- narration
- turn continuity across a played sequence

Missing resolver support is recorded in the engine inventory, not as an interpretation miss. `SOCIAL_SIGNAL`, intra-scene `MOVE`, `FOLLOW`, and free-form `USE_VISIBLE_OBJECT` are partial. The unsupported mechanical classes have no resolver by design.

## What the recorded outputs did

DP02, the ordinary attack, was schema-valid. The model set communication mode CLARIFICATION, listed `I` and `my sword` as unresolved, and emitted ASK, ASK, then ATTACK against `goblin_scout`. Disposition was NEEDS_CLARIFICATION, so `engine_submission` was empty. That miss is operation-class selection and entity binding.

DP06, the mechanical override, was schema-valid. The model asked which target the sword swing used and emitted no operation class. The critical hit and the skipped roll were stored as unadjudicated outcome text. `DICE_OVERRIDE` was not selected, so the unsupported path did not run. Nothing was submitted. That miss is operation-class selection.

DP08, the out-of-character correction, matched the mode, the empty action list, the referent correction, and the OUT_OF_CHARACTER disposition. Premises and a wished clarification were also filled, so those two metrics miss. No action was submitted.

Stage 2 was not run. Two stage-1 outputs were unusable under the rule fixed before the calls.
