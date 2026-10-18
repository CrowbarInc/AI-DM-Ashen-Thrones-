# 05 — Generation Path Implementation

There is one speech path. `adopt_host_speech` still calls `select_host_speech`. If the contract is eligible, `apply_expression` makes one provider call and validates the candidate. An accepted sentence is passed to the existing `seal_host_speech` with the same fallback source. A rejection seals the host fallback. Continuity answers that never enter the resolver use `maybe_reword_continuity_line` and then the same seal.

The prompt contains the speaker, the player question, the operation, and the authorized propositions. It labels AUTHORIZED FACTS separately from OPTIONAL NONCANONICAL EXPRESSION. It does not send world state, NPC histories, resolver policy, or hidden information. Prompt text is not treated as the safety boundary.

Generation is skipped when `ASHEN_DISABLE_EXPRESSION_GENERATION` is on, when provider calls are disabled, or when the operation is not eligible. `generation_attempts` on the seal stays 0 so existing narration-attempt assertions remain meaningful. Expression calls are counted separately from narration in `calls_since`. The live-model test guard blocks `game.expressive_dialogue.request_expression` unless a test stubs it.
