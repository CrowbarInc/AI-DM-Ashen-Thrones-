# Object Manipulation

Push, pull, and move require mobility `movable`. An immovable target is category E. Unknown mobility is category D. Weight other than `light` is category B and is not lifted, because the character has no strength-check owner.

A successful push updates position. "Away from the doorway" clears an obstruction only when the object already obstructs a doorway or its position says it is blocking one. Otherwise the engine says no doorway obstruction is established and does not claim the doorway is clear.

"Farther" extends the current aside position and then stays idempotent. Pronouns use the physical focus set by the last committed object action.

Lift of an explicitly light movable object sets position to "raised in place". It does not enter inventory. Place works only from that raised position. Take and drop are deferred because ordinary carrying has no safe owner.
