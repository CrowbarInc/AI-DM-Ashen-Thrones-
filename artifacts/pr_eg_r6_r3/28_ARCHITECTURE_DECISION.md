# 28 — Architecture Decision

Recommend Architecture C as the next implementation direction. Do not recommend B. Do not keep investing in a larger A schema as the way to fix binding.

C meets the pre-registered referent rule on holdout and validation, does not lose a core holdout metric by more than 3, leaks nothing, and does not classify the utterance with keywords. B improves binding somewhat and loses role fidelity and clarification discipline. A still describes roles slightly more carefully than B, and its production gate is the right authority boundary, but the provider is unreliable at emitting the full operation.

The recommendation is limited. C's composite success used a compiler that accepts interpretations A's source gate rejects. Shipping C's compiler output as a player-facing answer would skip disclosure control. The next implementation must feed a selected candidate back through existing `bind` and disclosure checks.
